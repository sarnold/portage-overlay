### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
### Copyright (C) 2006 Simon Capper <scapper@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgc2000.py 3927 2007-01-22 03:15:22Z rogerb $

"""Communicate with the LG C2000 cell phone. This is crappy phone if you want to connect it to
your PC, I would not recommend it.
The serial interface is buggy, the phone crashes with the slightest reasons and sometimes this
requires battery removal to fix . eg. AT+CPBS="LD" followed by AT+CPBR for call history retrieval.
and refuses to accept file uploads although the commands are reported as supported.
"""

# standard modules
import base64
import sha
import time

# BitPim modules
import bpcalendar
import common
import commport
import com_lgg4015
import guihelper
import helpids
import memo
import nameparser
import p_lgc2000
import prototypes
import sms

class Phone(com_lgg4015.Phone):
    """ Talk to the LG C2000 Phone"""

    desc='LG-C2000'
    helpid=helpids.ID_PHONE_LGC2000
    protocolclass=p_lgc2000
    serialsname='lgc2000'

    def __init__(self, logtarget, commport):
        super(Phone,self).__init__(logtarget, commport)
        self.mode=self.MODENONE

    def getfundamentals(self, results):

        """Gets information fundamental to interoperating with the phone and UI.

        Currently this is:

          - 'uniqueserial'     a unique serial number representing the phone
          - 'groups'           the phonebook groups

        This method is called before we read the phonebook data or before we
        write phonebook data.
        """
        # use a hash of ESN and other stuff (being paranoid)
        self.setmode(self.MODEMODEM)
        self.log("Retrieving fundamental phone information")
        self.log("Reading phone serial number")
        results['uniqueserial']=sha.new(self.get_sim_id()).hexdigest()
        # now read groups
        self.log("Reading group information")
        results['groups']=self._get_groups()
        # All done
        self.log("Fundamentals retrieved")
        return results

    # this function does not work !!!!
    def getwallpapers(self, result):
        self.log('Reading wallpaper index')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        self._wallpaper_mode()
        media={}
        media_index=self._get_wallpaper_index()

        # Set the media type to be pic (wallpaper)
        self.charset_ascii()
        self._wallpaper_mode()
        # and read the list
        res={}
        self._get_image_index(self.protocolclass.MIN_WALLPAPER_INDEX, self.protocolclass.MAX_WALLPAPER_INDEX,
                         res, 0, 'wallpaper')

        # dummy data for wallpaper        
        _dummy_data=file(guihelper.getresourcefile('wallpaper.png'),'rb').read()
        for e in res.values():
            media[e['name']]=_dummy_data

        # Set the media type to be photo
        self.charset_ascii()
        self._photo_mode()
        # and read the list
        res={}
        self._get_image_index(self.protocolclass.MIN_PHOTO_INDEX, self.protocolclass.MAX_PHOTO_INDEX,
                         res, 0, 'camera')
        # read the files out of the phone
        for e in res.values():
            data=self._get_media_file(e['name'])
            if data != False:
                print "get OK"
                media[e['name']]=data
            else:
                print "get failed"
                media[e['name']]=_dummy_data
                
        result['wallpapers']=media
        result['wallpaper-index']=media_index
        return result

    def _photo_mode(self):
        _req=self.protocolclass.media_selector_set()
        _req.media_type=self.protocolclass.MEDIA_PHOTO
        self.sendATcommand(_req, None)

    def _get_image_index(self, min, max, res, res_offset, origin):
        _req=self.protocolclass.media_list_req()
        _req.start_index=min
        _req.end_index=max
        _res=self.sendATcommand(_req, self.protocolclass.media_list_resp)
        for i,e in enumerate(_res):
            res[i+res_offset]={ 'name': e.file_name, 'origin': origin, 'size':e.size }
    
    def _get_wallpaper_index(self):
        """ Return the wallpaper index"""
        res={}
        # Set the media type to be pic (wallpaper)
        self.charset_ascii()
        self._wallpaper_mode()
        # and read the list
        self._get_image_index(self.protocolclass.MIN_WALLPAPER_INDEX, self.protocolclass.MAX_WALLPAPER_INDEX,
                         res, 0, 'wallpaper')
        # Set the media type to be photo
        self.charset_ascii()
        self._photo_mode()
        # and read the list
# this command only seems to retrieve the first photo in the phone, so it is kindof useless
        self._get_image_index(self.protocolclass.MIN_PHOTO_INDEX, self.protocolclass.MAX_PHOTO_INDEX,
                         res, self.protocolclass.MAX_WALLPAPER_INDEX, 'camera')
        return res

    # this function only retrieves the beginning of the file
    # the phone sends a chunk of data follow by the '@' sign.
    # I have not found a way to make it send the rest of the file
    # the data that is sent is valid after being decoded
    def _get_media_file(self, file_name):
        """ Read a media file
        """
        if not file_name:
            return False
        self.log('Writing media %s'%file_name)
        _cmd='AT+DDLU=0,"%s"\r' % file_name
        self.comm.write(str(_cmd))
        # strip for the start of the response
        self.comm.readuntil('>')
        self.comm.read(1)
        # read the raw file data
        _data64=self.comm.readuntil('@')
        # convert to binary
        data=base64.decodestring(_data64[:-1])
        if self.comm.read(10)!='\n\r\r\n\r\nOK\r\n':
            return False
        # need to figure out how to make phone send rest of file	
        return data

#-------------------------------------------------------------------------------
parent_profile=com_lgg4015.Profile
class Profile(parent_profile):

    serialsname=Phone.serialsname

    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=128
    MAX_WALLPAPER_BASENAME_LENGTH=19
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_ ."
    WALLPAPER_CONVERT_FORMAT="jpg"
    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_ ."
    RINGTONE_LIMITS= {
        'MAXSIZE': 20480
    }
    # use for auto-detection
    phone_manufacturer='LGE'
    phone_model='C2000'

    usbids=( ( 0x10AB, 0x10C5, 1),
             ( 0x067b, 0x2303, None), # VID=Prolific, PID=USB to serial
        )
    deviceclasses=("serial",)

    def __init__(self):
        parent_profile.__init__(self)

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        # these features appear to be crippled, they seem to work from looking at the 
        # responses from the phone, but the phone crashes and none of the transfered 
        # data appears on the phone
        #('ringtone', 'read', None),   # all ringtone reading
        #('ringtone', 'write', 'OVERWRITE'),
        #('wallpaper', 'read', None),  # all wallpaper reading
        #('wallpaper', 'write', 'OVERWRITE'),
        ('memo', 'read', None),     # all memo list reading
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing
        ('sms', 'read', None),     # all SMS list reading
        # this phone hangs when you try to read the call history, even though it "claims" to 
        # support the commands when you query it using AT+CLAC, I only tested with the call history
        # empty.
        # ('call_history', 'read', None),
        )

    def convertphonebooktophone(self, helper, data):
        return data
