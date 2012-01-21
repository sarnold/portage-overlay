### BITPIM
###
### Copyright (C) 2006 Simon Capper <skyjunky@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

"""Communicate with the LG LX5550 cell phone

The LX5550 is substantially similar to the VX4400

"""

# standard modules
import time
import cStringIO
import sha

# my modules
import common
import copy
import p_lglx5550
import com_lgvx4400
import com_brew
import com_phone
import com_lg
import prototypes
import sms

class Phone(com_lgvx4400.Phone):
    "Talk to the LG LX5550 cell phone"

    desc="LG-LX5550"
    helpid=None
    protocolclass=p_lglx5550
    serialsname='lglx5550'

    # more LX5550 indices
    imagelocations=(
        # offset, index file, files location, type, maximumentries
        ( 10, "download/dloadindex/brewImageIndex.map", "brew/shared", "images", 30) ,
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries
        ( 50, "download/dloadindex/brewRingerIndex.map", "user/sound/ringer", "ringers", 30),
        )

    builtinimages= ('Foliage', 'Castle', 'Dandelion', 'Golf course', 'Icicles', 
                    'Orangutan', 'Lake')

    builtinringtones= ('Ring 1', 'Ring 2', 'Ring 3', 'Ring 4', 'Ring 5', 'Ring 6',
                       'Ring 7', 'Ring 8', 'Annen Polka', 'Pachelbel Canon', 
                       'Hallelujah', 'La Traviata', 'Leichte Kavallerie Overture', 
                       'Mozart Symphony No.40', 'Bach Minuet', 'Farewell', 
                       'Mozart Piano Sonata', 'Sting', 'O Solemio', 
                       'Pizzicato Polka', 'Stars and Stripes Forever', 
                       'Pineapple Rag', 'When the Saints Go Marching In', 'Latin', 
                       'Carol 1', 'Carol 2') 
                       
    
    def __init__(self, logtarget, commport):
        com_lgvx4400.Phone.__init__(self,logtarget,commport)
        self.mode=self.MODENONE

    def _getquicktext(self):
        quicks=[]
        quicks=com_lgvx4400.Phone._getquicktext(self)
        built_in=['Yes', 'No', 'Call Me', 'Need Directions', 'Where are you?',
                  'Will Call you later', 'Busy', 'On My way', 'Will arive in 15 minutes',
                  'Thank you', 'Love you']
        for s in built_in:
            quicks.append({ 'text': s, 'type': sms.CannedMsgEntry.builtin_type })
        return quicks

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

    my_version_txt='AX5550'
    my_model='LX5550'

    def getphoneinfo(self, phone_info):
        self.log('Getting Phone Info')
        try:
            s=self.getfilecontents('brew/version.txt')
            if s[:6]=='AX5550':
                phone_info.model=self.my_model
                phone_info.manufacturer=Profile.phone_manufacturer
                req=p_brew.firmwarerequest()
                res=self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
                phone_info.append('Firmware Version:', res.firmware)
                s=self.getfilecontents("nvm/$SYS.ESN")[85:89]
                txt='%02X%02X%02X%02X'%(ord(s[3]), ord(s[2]), ord(s[1]), ord(s[0]))
                phone_info.append('ESN:', txt)
                txt=self.getfilecontents("nvm/nvm/nvm_0000")[577:587]
                phone_info.append('Phone Number:', txt)
        except:
            if __debug__:
                raise


parentprofile=com_lgvx4400.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='LG Electronics Inc'
    phone_model='LX5550'

    # no direct usb interface
    usbids=com_lgvx4400.Profile.usbids_usbtoserial

    # delay in rebooting the phone after a send data and delay between offline and reboot in seconds.
    reboot_delay=3

    WALLPAPER_WIDTH=120
    WALLPAPER_HEIGHT=131
    MAX_WALLPAPER_BASENAME_LENGTH=19
    WALLPAPER_FILENAME_CHARS="_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ."
    WALLPAPER_CONVERT_FORMAT="jpg"

    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ."

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
        # some uncertainty over wallpaper write, more testing required
        #('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        #('wallpaper', 'write', 'OVERWRITE'),
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
