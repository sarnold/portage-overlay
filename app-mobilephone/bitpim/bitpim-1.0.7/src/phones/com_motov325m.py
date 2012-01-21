### BITPIM
###
### Copyright (C) 2007 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_motov325m.py 4563 2008-01-11 21:49:45Z djpham $

"""Communicate with Motorola phones using AT commands"""
import time

import common
import com_motov3mm as v3mm
import com_motov325 as v325
import prototypes
import p_motov325
import helpids

parentphone=v3mm.Phone
class Phone(parentphone):
    """ Talk to a Motorola V3mM phone"""
    desc='Moto-V325M'
    helpid=helpids.ID_PHONE_MOTOV325M
    protocolclass=p_motov325
    serialsname='motov325m'
    MODEOBEX='modeobex'

    builtinringtones=(
        (0, ('Silent',)),
        (5, ('Vibe Dot', 'Vibe Dash', 'Vibe Dot Dot', 'Vibe Dot Dash',
             'Vibe Pulse')),
        (11, ('Alert', 'Standard', 'Bells', 'Triads', 'Up and Down')),
        (30, ('Moonlit Haze', 'Nightlife', 'Wind Chime', 'Random',
              'Bit & Bytes', 'Door Bell', 'Ding', 'One Moment', 'Provincial',
              'Harmonics', 'Interlude', 'Snaggle', 'Cosmic')),
        )

    def _get_del_new_list(self, index_key, media_key, merge, fundamentals,
                          origins):
        """Return a list of media being deleted and being added"""
        _index=fundamentals.get(index_key, {})
        _media=fundamentals.get(media_key, {})
        _index_file_list=[_entry['name'] for _entry in _index.values() \
                          if _entry.has_key('filename') and \
                          _entry['filename'].startswith(self.protocolclass.MOTO_SHARED_PATH) and \
                          _entry.get('origin', None) in origins ]
        _bp_file_list=[_entry['name'] for _entry in _media.values() \
                       if _entry.get('origin', None) in origins ]
        if merge:
            # just add the new files, don't delete anything
            _del_list=[]
            _new_list=_bp_file_list
        else:
            # Delete specified files and add everything
            _del_list=[x for x in _index_file_list if x not in _bp_file_list]
            _new_list=_bp_file_list
        return _del_list, _new_list

    def _add_files(self, index_key, media_key, media_path,
                   new_list, fundamentals):
        """Add new file using OBEX"""
        _index=fundamentals.get(index_key, {})
        _media=fundamentals.get(media_key, {})
        _adding_ringtones=index_key=='ringtone-index'
        for _file in new_list:
            _data=self._item_from_index(_file, 'data', _media)
            if not _data:
                self.log('Failed to write file %s due to no data'%_file)
                continue
            if self._item_from_index(_file, None, _index) is None:
                # new file
                _name=_file
                if _adding_ringtones and \
                   common.getext(_name).lower()=='mp3':
                    # need to adjust the file name since this model only
                    # accepts qcp and mid files (AFAIK).
                    _name='%s.mid'%common.stripext(_name)
                _file_name='%(pathname)s/%(filename)s'% \
                            { 'pathname': media_path,
                              'filename': _name }
                try:
                    self.obex.writefile(_file_name, _data)
                except:
                    self.log('Failed to write OBEX file '+_file_name)
                    if __debug__:
                        raise
        
    def getwallpapers(self, fundamentals):
        """Retrieve wallpaper data"""
        # The V325 needs some time to switch from BREW back to MODEM mode
        # without this sleep, the switch will always come back with ERROR
        self.log('Waiting for the phone to switch back to mode modem')
        time.sleep(2)
        self.setmode(self.MODEPHONEBOOK)
        return parentphone.getwallpapers(self, fundamentals)

    def getringtones(self, fundamentals):
        """Retrieve ringtones data"""
        self.log('Waiting for the phone to switch to MODEM')
        time.sleep(2)
        self.setmode(self.MODEPHONEBOOK)
        self.log('Reading ringtones')
        _res={}
        _rt_index=fundamentals.get('ringtone-index', {})
        # This model has ringtone files on both the normal dir (shared/audio)
        # as well as other dirs
        # 1st, get the BREW files
        self.setmode(self.MODEBREW)
        for _entry in _rt_index.values():
            if _entry.has_key('filename') and \
               not _entry['filename'].startswith(self.protocolclass.RT_PATH):
                try:
                    _res[_entry['name']]=self.getfilecontents(_entry['filename'])
                except:
                    self.log('Failed to read media file %s'%_entry['filename'])
        # Now, get the OBEX One        
        self.setmode(self.MODEOBEX)
        for _entry in _rt_index.values():
            if _entry.has_key('filename') and \
               _entry['filename'].startswith(self.protocolclass.RT_PATH):
                try:
                    _res[_entry['name']]=self.obex.getfilecontents(
                        self.protocolclass.OBEXName(_entry['filename']))
                except:
                    self.log('Failed to read media file %s'%_entry['filename'])
        fundamentals['ringtone']=_res
        self.setmode(self.MODEMODEM)
        # The phone will need to be reset (unplugged & replug) after this!
        fundamentals['clearcomm']=True
        return fundamentals

    def saveringtones(self, fundamentals, merge):
        """Save ringtones to the phone"""
        self.log('Waiting for the phone to switch back to mode modem')
        time.sleep(2)
        parentphone.saveringtones(self, fundamentals, merge)
        fundamentals['clearcomm']=True
        return fundamentals

    def savewallpapers(self, fundamentals, merge):
        """Save wallpapers to the phone"""
        self.log('Waiting for the phone to switch back to mode modem')
        time.sleep(2)
        self.log('Writing wallpapers to the phone')
        self.setmode(self.MODEBREW)
        try: 
            _del_list, _new_list=self._get_del_new_list('wallpaper-index',
                                                        'wallpapers',
                                                        merge,
                                                        fundamentals,
                                                        frozenset(['images']))
            # replace files
            self._replace_files('wallpaper-index', 'wallpapers',
                                _new_list, fundamentals)
        except:
            if __debug__:
                self.setmode(self.MODEMODEM)
                raise
        self.setmode(self.MODEMODEM)
        return fundamentals


#-------------------------------------------------------------------------------
parentprofile=v325.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    phone_model='V325M'
    generic_phone_model='Motorola V325M Phone'

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('ringtone', 'read', None),   # all ringtone reading
        ('ringtone', 'read', 'EXCLUSIVE'),   # all ringtone reading
        ('ringtone', 'write', 'EXCLUSIVE'),
        ('ringtone', 'write', None),
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', 'OVERWRITE'),
        ('sms', 'read', None),
        )
