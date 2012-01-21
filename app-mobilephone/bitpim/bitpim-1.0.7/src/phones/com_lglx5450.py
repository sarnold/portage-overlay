### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2005 Simon Capper <skyjunky@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lglx5450.py 3918 2007-01-19 05:15:12Z djpham $

"""Communicate with the LG LX5450 cell phone

The LX5450 is substantially similar to the VX4400 except that it supports more
image formats, has wallpapers in no less than 4 locations and puts things in
slightly different directories. It is almost identical to the vx6000.

The code in this file mainly inherits from VX4400 code and then extends where
the 5450 has extra functionality

"""

# standard modules
import time
import cStringIO
import sha

# my modules
import common
import copy
import p_lglx5450
import com_lgvx4400
import com_brew
import com_phone
import com_lg
import prototypes

class Phone(com_lgvx4400.Phone):
    "Talk to the LG LX5450 cell phone"

    desc="LG-LX5450"
    helpid=None
    protocolclass=p_lglx5450
    serialsname='lglx5450'

    # more LX5450 indices
    imagelocations=(
        # offset, index file, files location, type, maximumentries
        ( 10, "download/dloadindex/brewImageIndex.map", "brew/shared", "images", 30) ,
        ( 0xc8, "download/dloadindex/mmsImageIndex.map", "brew/shared/mms", "mms", 20),
        ( 0xdc, "download/dloadindex/mmsDrmImageIndex.map", "brew/shared/mms/d", "drm", 20), 
        ( 0x82, None, None, "camera", 20) # nb camera must be last
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries
        ( 50, "download/dloadindex/brewRingerIndex.map", "user/sound/ringer", "ringers", 30),
        ( 150, "download/dloadindex/mmsRingerIndex.map", "mms/sound", "mms", 20),
        ( 180, "download/dloadindex/mmsDrmRingerIndex.map", "mms/sound/drm", "drm", 20)
        )

    builtinimages= ('Beach Ball', 'Towerbridge', 'Sunflower', 'Beach', 'Fish', 
                    'Sea', 'Snowman')

    builtinringtones= ('Ring 1', 'Ring 2', 'Ring 3', 'Ring 4', 'Ring 5', 'Ring 6',
                       'Annen Polka', 'Beethoven Symphony No. 9', 'Pachelbel Canon', 
                       'Hallelujah', 'La Traviata', 'Leichte Kavallerie Overture', 
                       'Mozart Symphony No.40', 'Bach Minuet', 'Farewell', 
                       'Mozart Piano Sonata', 'Sting', 'Trout', 'O solemio', 
                       'Pizzicata Polka', 'Stars and Stripes Forever', 
                       'Pineapple Rag', 'When the Saints Go Marching In', 'Latin', 
                       'Carol 1', 'Carol 2') 
                       
    
    def __init__(self, logtarget, commport):
        com_lgvx4400.Phone.__init__(self,logtarget,commport)
        self.mode=self.MODENONE

    def getcameraindex(self):
        buf=prototypes.buffer(self.getfilecontents("cam/pics.dat"))
        index={}
        g=self.protocolclass.campicsdat()
        g.readfrombuffer(buf, logtitle="Camera index")
        for i in g.items:
            if len(i.name):
                # index[i.index]={'name': i.name, 'date': i.taken, 'origin': 'camera' }
                # we currently use the filesystem name rather than rename in camera
                # since the latter doesn't include the file extension which then makes
                # life less pleasant once the file ends up on the computer
                index[i.index]={'name': "pic%02d.jpg"%(i.index,), 'date': i.taken, 'origin': 'camera' }
        return index

    def eval_detect_data(self, res):
        found=False
        if res.get(self.brew_version_txt_key, None) is not None:
            found=res[self.brew_version_txt_key][:len(self.my_version_txt)]==self.my_version_txt
        if found:
            res['model']=self.my_model
            res['manufacturer']='LG Electronics Inc'
            s=res.get(self.esn_file_key, None)
            if s:
                res['esn']=self.get_esn(s)


    my_version_txt='AX545V'
    my_model='LX5450'

parentprofile=com_lgvx4400.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='LG Electronics Inc'
    phone_model='LX5450'

    WALLPAPER_WIDTH=120
    WALLPAPER_HEIGHT=131
    MAX_WALLPAPER_BASENAME_LENGTH=32
    WALLPAPER_FILENAME_CHARS="_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ."
    WALLPAPER_CONVERT_FORMAT="bmp"
   
    MAX_RINGTONE_BASENAME_LENGTH=32
    RINGTONE_FILENAME_CHARS="_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ."

    # nb we don't allow save to camera so it isn't listed here
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "mms"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "drm"))
    def GetImageOrigins(self):
        return self.imageorigins

    ringtoneorigins=('ringers', 'mms', 'drm')
    excluded_ringtone_origins=('mms', 'drm')
    excluded_wallpaper_origins=('mms', 'drm')

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 120, 'height': 131, 'format': "BMP"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets
    
    _supportedsyncs=(
        ('sms', 'read', None),
        ('sms', 'write', 'OVERWRITE'),
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('calendar', 'read', None),   # all calendar reading
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'read', None),   # all ringtone reading
        ('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
        ('ringtone', 'write', 'OVERWRITE'),
        ('memo', 'read', None),     # all memo list reading DJP
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing DJP
        ('call_history', 'read', None),
       )
 
    def __init__(self):
        parentprofile.__init__(self)

