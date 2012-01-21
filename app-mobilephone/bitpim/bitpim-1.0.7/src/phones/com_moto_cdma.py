### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_moto.py 3641 2006-11-08 02:43:05Z sawecw $

"""Communicate with Motorola CDMA phones using AT commands"""

import commport
import com_moto
import com_brew

class Phone(com_moto.Phone, com_brew.BrewProtocol):
    _switch_mode_cmd='\x44\x58\xf4\x7e'

    def __init__(self, logtarget, commport):
        com_moto.Phone.__init__(self, logtarget, commport)
        com_brew.BrewProtocol.__init__(self)
        
    def _setmodephonebooktobrew(self):
        self.setmode(self.MODEMODEM)
        self.setmode(self.MODEBREW)
        return True

    def _setmodemodemtobrew(self):
        self.log('Switching from modem to BREW')
        try:
            self.comm.sendatcommand('$QCDMG')
            return True
        except:
            pass
        # give it another try
        self.log('Retry switching from modem to BREW')
        try:
            self.comm.sendatcommand('$QCDMG')
            return True
        except commport.ATError:
	    return False
	except:
            if __debug__:
                self.log('Got an excepetion')
            return False

    def _setmodebrew(self):
        # switch from None to BREW
        self.log('Switching from None to BREW')
        # do it the long, but sure, way: 1st try to switch to modem
        if not self._setmodemodem():
            # can't switch to modem, give up
            return False
        # then switch from modem to BREW
        return self._setmodemodemtobrew()

    def _setmodebrewtomodem(self):
        self.log('Switching from BREW to modem')
        try:
            self.comm.write(self._switch_mode_cmd, False)
            self.comm.readsome(numchars=5, log=False)
            return True
        except:
            pass
        # give it a 2nd try
        try:
            self.comm.write(self._switch_mode_cmd, False)
            self.comm.readsome(numchars=5, log=False)
            return True
        except:
            return False

    def _setmodemodem(self):
        # ask parent to do it
        if super(Phone,self)._setmodemodem():
            return True
        # could be in BREW mode, try switch over
        self.log('trying to switch from BREW mode')
        if not self._setmodebrewtomodem():
            return False
        try:
            self.comm.sendatcommand('E0V1')
            self.set_mode(self.protocolclass.MODE_MODEM)
            return True
        except:
            return False

    # Ringtones & wallpaper sutff------------------------------------------------------------
    def _read_media(self, index_key, fundamentals):
        """Read the contents of media files and return"""
        _media={}
        for _key,_entry in fundamentals.get(index_key, {}).items():
            if _entry.get('filename', None):
                # this one associates with a file, try to read it
                try:
                    _media[_entry['name']]=self.getfilecontents(_entry['filename'],
                                                                True)
                except (com_brew.BrewNoSuchFileException,
                        com_brew.BrewBadPathnameException,
                        com_brew.BrewNameTooLongException,
                        com_brew.BrewAccessDeniedException):
                    self.log("Failed to read media file: %s"%_entry['name'])
                except:
                    self.log('Failed to read media file.')
                    if __debug__:
                        raise
        return _media

    def getringtones(self, fundamentals):
        """Retrieve ringtones data"""
        self.log('Reading ringtones')
        self.setmode(self.MODEPHONEBOOK)
        self.setmode(self.MODEBREW)
        try:
            fundamentals['ringtone']=self._read_media('ringtone-index',
                                                      fundamentals)
        except:
            if __debug__:
                raise
        self.setmode(self.MODEMODEM)
        return fundamentals

    def getwallpapers(self, fundamentals):
        """Retrieve wallpaper data"""
        self.log('Reading wallpapers')
        self.setmode(self.MODEPHONEBOOK)
        self.setmode(self.MODEBREW)
        try:
            fundamentals['wallpapers']=self._read_media('wallpaper-index',
                                                        fundamentals)
        except:
            if __debug__:
                raise
        self.setmode(self.MODEMODEM)
        return fundamentals

class Profile(com_moto.Profile):
    pass
