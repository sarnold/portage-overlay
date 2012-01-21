### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2004 John O'Shaughnessy <oshinfo@comcast.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx6100.py 3918 2007-01-19 05:15:12Z djpham $

"""Communicate with the LG VX6100 cell phone

The VX6100 is substantially similar to the VX4400 except that it supports more
image formats, has wallpapers in no less than 5 locations and puts things in
slightly different directories.

The code in this file mainly inherits from VX4400 code and then extends where
the 6100 has extra functionality

"""

# standard modules
import time
import cStringIO
import sha

# my modules
import common
import commport
import copy
import p_brew
import p_lgvx6100
import com_lgvx4400
import com_brew
import com_phone
import com_lg
import prototypes
import call_history
import helpids

class Phone(com_lgvx4400.Phone):
    "Talk to the LG VX6100 cell phone"

    desc="LG-VX6100"
    helpid=helpids.ID_PHONE_LGVX6100
    protocolclass=p_lgvx6100
    serialsname='lgvx6100'

    # more VX6100 indices
    imagelocations=(
        # offset, index file, files location, type, maximumentries
        ( 16, "download/dloadindex/brewImageIndex.map", "brew/shared", "images", 60) ,
        ( 200, "download/dloadindex/mmsImageIndex.map", "brew/shared/mms", "mms", 30),
        ( 240, "download/dloadindex/mmsDrmImageIndex.map", "brew/shared/mms/d", "drm", 20), 
        ( 130, None, None, "camera", 60) # nb camera must be last
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries
        ( 50, "download/dloadindex/brewRingerIndex.map", "user/sound/ringer", "ringers", 60),
        ( 150, "download/dloadindex/mmsRingerIndex.map", "mms/sound", "mms", 20),
        ( 180, "download/dloadindex/mmsDrmRingerIndex.map", "mms/sound/drm", "drm", 20)
        )

    builtinimages= ('Sport', 'Butterfly', 'Cake', 'Niagara Falls', 'Rockefeller', 
    				'Statue of Liberty', 'The Capital', 'Scenary','White Bear', 'Yacht' ) 
    
    builtinringtones= ('Ring 1', 'Ring 2', 'Ring 3', 'Ring 4', 'Ring 5', 'VZW Default Tone',
                       'Farewell', 'Arabesque',
                       'Piano Sonata', 'Latin', 'When The Saints', 'Bach Cello Suite',
                       'Speedy Way', 'Cancan', 'Sting', 'Toccata and Fugue',
                       'Mozart Symphony 40', 'Nutcracker March', 'Funiculi', 'Polka', 	
                       'Hallelujah', 'Mozart Aria',
                       'Leichte', 'Spring', 'Slavonic', 'Fantasy', 'Chimes High',
                       'Chimes Low', 'Ding', 'Tada', 'Notify', 'Drum', 'Claps', 'Fanfare', 
                       'Chord High', 'Chord Low')
                       
    
    def __init__(self, logtarget, commport):
        com_lgvx4400.Phone.__init__(self,logtarget,commport)
        self.mode=self.MODENONE
        
    def makeentry(self, counter, entry, dict):
        e=com_lgvx4400.Phone.makeentry(self, counter, entry, dict)
        e.entrysize=0x202
        return e

    def getcameraindex(self):
        index={}
        try:
            buf=prototypes.buffer(self.getfilecontents("cam/pics.dat"))
            g=self.protocolclass.campicsdat()
            g.readfrombuffer(buf, logtitle="Read camera index")
            for i in g.items:
                if len(i.name):
                    # index[i.index]={'name': i.name, 'date': i.taken, 'origin': 'camera' }
                    # we currently use the filesystem name rather than rename in camera
                    # since the latter doesn't include the file extension which then makes
                    # life less pleasant once the file ends up on the computer
                    index[i.index]={'name': "pic%02d.jpg"%(i.index,), 'date': i.taken, 'origin': 'camera' }
        except com_brew.BrewNoSuchFileException:
            # if the phone has no pictures it may not have a a cam/pics.dat file
            pass
        return index

    my_model='VX6100'

    def getphoneinfo(self, phone_info):
        self.log('Getting Phone Info')
        try:
            s=self.getfilecontents('brew/version.txt')
            if s[:6]=='VX6100':
                phone_info.append('Model:', "VX6100")
                req=p_brew.firmwarerequest()
                res=self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
                phone_info.append('Firmware Version:', res.firmware)
                s=self.getfilecontents("nvm/$SYS.ESN")[85:89]
                txt='%02X%02X%02X%02X'%(ord(s[3]), ord(s[2]), ord(s[1]), ord(s[0]))
                phone_info.append('ESN:', txt)
                txt=self.getfilecontents("nvm/nvm/nvm_0000")[577:587]
                phone_info.append('Phone Number:', txt)
        except:
            pass
        return

parentprofile=com_lgvx4400.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX6100'

    WALLPAPER_WIDTH=132
    WALLPAPER_HEIGHT=148
    MAX_WALLPAPER_BASENAME_LENGTH=24
    WALLPAPER_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_ ."
    WALLPAPER_CONVERT_FORMAT="jpg"
   
    MAX_RINGTONE_BASENAME_LENGTH=24
    RINGTONE_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_ ."

    ringtoneorigins=('ringers', 'mms', 'drm')
    excluded_ringtone_origins=('mms', 'drm')

    # nb we don't allow save to camera so it isn't listed here
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "mms"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "drm"))
    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 132, 'height': 148, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 132, 'height': 148, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 128, 'height': 160, 'format': "JPEG"}))
    # can the outside lcd display images?
    #imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
    #                                  {'width': 96, 'height': 64, 'format': "JPEG"}))
    
    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None),         # all SMS list reading
        ('memo', 'read', None),        # all memo list reading
        ('calendar', 'write', 'OVERWRITE'),  # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),     # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
        ('ringtone', 'write', 'OVERWRITE'),
        ('sms', 'write', 'OVERWRITE'),       # all SMS list writing
        ('memo', 'write', 'OVERWRITE'),      # all memo list writing
        )
 
    def __init__(self):
        parentprofile.__init__(self)

