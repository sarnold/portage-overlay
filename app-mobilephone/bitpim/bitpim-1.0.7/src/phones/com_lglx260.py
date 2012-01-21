### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2005 Simon Capper <skyjunky@sbcglobal.net>
### Copyright (C) 2008 Joe Siegrist <joesigrist@gmail.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

"""Communicate with the LG LX260 cell phone

The LX260 is like other LG phones, I got this to import and export phonebook data 
which is all I care about at the moment, extending should be straightforward


"""

# standard modules
import time
import cStringIO
import sha

# my modules
import common
import copy
import p_brew
import p_lglx260
import com_lgvx4400
import com_brew
import com_phone
import com_lg
import prototypes

class Phone(com_lgvx4400.Phone):
    "Talk to the LG LX260 cell phone"

    desc="LG-LX260"
    helpid=None
    protocolclass=p_lglx260
    serialsname='lglx260'

    # more LX260 indices
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
        index={}
        return index

    # this phone lacks groups
    def getgroups(self, results):
	g=self.protocolclass.pbgroups()
	groups={}
        #for i in range(len(g.groups)):
            #if len(g.groups[i].name): # sometimes have zero length names
                #groups[i]={ 'icon': g.groups[i].icon, 'name': g.groups[i].name }
        	#self.log('Getting group: ' +i)
        results['groups']=groups
	return groups

    def getphoneinfo(self, phone_info):
        self.log('Getting Phone Info')
        phone_info.model=self.my_model
        phone_info.manufacturer=Profile.phone_manufacturer
	phone_info.append('ESN:', self.get_brew_esn())
        req=p_brew.firmwarerequest()
        res=self.sendbrewcommand(req, p_lglx260.firmwareresponse)
        phone_info.append('Firmware Version:', res.firmware)
        s=self.getfilecontents('pim/MyInformation.dat')
        phone_info.append('Phone Number:', s[363:373])
        try:
            dirlisting=self.getfilesystem('', 1)
	    keys = dirlisting.keys()
	    keys.sort()
            #dirlisting=self.getfilesystem('nvm/')
            for i in keys:
	      self.log('file: '+ i)
	      #s=self.getfilecontents(i)
        except com_brew.BrewNoSuchDirectoryException:
	    self.log('no such directory pim/')
  	#self.log(self.getfilecontents('pim/sp_num.dat'))

    def eval_detect_data(self, res):
	found=False
        try:
            s=self.getfilecontents('brew/version.txt')
            if s[:5]==self.my_model:
                found=True
                res['model']=self.my_model
                res['manufacturer']='LG Electronics Inc'
                res['esn'] = self.get_brew_esn()
        except:
            pass
        return

    my_model='LX260'

parentprofile=com_lgvx4400.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='LG Electronics Inc'
    phone_model='LX260'

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

