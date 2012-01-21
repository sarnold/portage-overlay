### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx4500.py 3918 2007-01-19 05:15:12Z djpham $

"""Communicate with the LG VX4500 cell phone

The VX4500 is substantially similar to the VX4400

"""

# standard modules
import time
import cStringIO
import sha

# my modules
import common
import copy
import p_lgvx4500
import com_lgvx4400
import com_brew
import com_phone
import com_lg
import helpids
import prototypes

class Phone(com_lgvx4400.Phone):
    "Talk to the LG VX4500 cell phone"

    desc="LG-VX4500"
    helpid=helpids.ID_PHONE_LGVX4500
    protocolclass=p_lgvx4500
    serialsname='lgvx4500'

    # more VX4500 indices
    imagelocations=(
        # offset, index file, files location, type, maximumentries
        ( 10, "download/dloadindex/brewImageIndex.map", "brew/shared", "images", 30) ,
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries
        ( 50, "download/dloadindex/brewRingerIndex.map", "user/sound/ringer", "ringers", 30),
        )

    builtinimages= ('Foliage', 'Castle', 'Dandelion', 'Golf course', 'Icicles', 
                    'Orangutan', 'Lake', 'Golden Gate', 'Desert')

    builtinringtones= ('Ring 1', 'Ring 2', 'Ring 3', 'Ring 4', 'Ring 5', 'Ring 6',
                       'Ring 7', 'Ring 8', 'Annen Polka', 'Pachelbel Canon', 
                       'Hallelujah', 'La Traviata', 'Leichte Kavallerie Overture', 
                       'Mozart Symphony No.40', 'Bach Minuet', 'Farewell', 
                       'Mozart Piano Sonata', 'Sting', 'O solemio', 
                       'Pizzicata Polka', 'Stars and Stripes Forever', 
                       'Pineapple Rag', 'When the Saints Go Marching In', 'Latin', 
                       'Carol 1', 'Carol 2', 'Chimes high', 'Chimes low', 'Ding', 
                       'TaDa', 'Notify', 'Drum', 'Claps', 'Fanfare', 'Chord high', 
                       'Chord low') 
                       
    
    def __init__(self, logtarget, commport):
        com_lgvx4400.Phone.__init__(self,logtarget,commport)
        self.mode=self.MODENONE

    def makeentry(self, counter, entry, dict):
        e=com_lgvx4400.Phone.makeentry(self, counter, entry, dict)
        e.entrysize=0x202
        #e.unknown20c="\x00\x00\x00\x00\x00\x31\x02"
        return e

    my_model='VX4500'

    def getphoneinfo(self, phone_info):
        self.log('Getting Phone Info')
        try:
            s=self.getfilecontents('brew/version.txt')
            if s[:6]=='VX4500':
                phone_info.model=self.my_model
                phone_info.manufacturer=Profile.phone_manufacturer
                req=p_brew.firmwarerequest()
                res=self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
                phone_info.append('Firmware Version:', res.firmware)
                s=self.getfilecontents("nvm/$SYS.ESN")[85:89]
                txt='%02X%02X%02X%02X'%(ord(s[3]), ord(s[2]), ord(s[1]), ord(s[0]))
                phone_info.append('ESN:', txt)
                txt=self.getfilecontents("nvm/nvm/nvm_0000")[457:467]
                phone_info.append('Phone Number:', txt)
        except:
            if __debug__:
                raise


parentprofile=com_lgvx4400.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX4500'

    # no direct usb interface
    usbids=com_lgvx4400.Profile.usbids_usbtoserial

    WALLPAPER_WIDTH=120
    WALLPAPER_HEIGHT=131
    MAX_WALLPAPER_BASENAME_LENGTH=19
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ."
    WALLPAPER_CONVERT_FORMAT="bmp"

    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvxwyz0123456789 ."

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 120, 'height': 131, 'format': "BMP"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 120, 'height': 131, 'format': "BMP"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 120, 'height': 160, 'format': "BMP"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets
    
    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
        ('ringtone', 'write', 'OVERWRITE'),
        ('memo', 'read', None),     # all memo list reading DJP
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing DJP
        ('call_history', 'read', None),
        ('sms', 'read', None),
        ('sms', 'write', 'OVERWRITE'),
       )

    def __init__(self):
        parentprofile.__init__(self)
