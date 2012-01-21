#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2009 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx9600.py 4725 2009-03-04 03:37:48Z djpham $


"""
Communicate with the LG VX9600 cell phone.
"""

# BitPim modules
import common
import com_brew
import prototypes
import com_lgvx9700
import p_lgvx9600
import helpids
import sms

#-------------------------------------------------------------------------------
parentphone=com_lgvx9700.Phone
class Phone(parentphone):
    desc="LG-VX9600 (Versa)"
    helpid=helpids.ID_PHONE_LGVX9600
    protocolclass=p_lgvx9600
    serialsname='lgvx9600'

    my_model='VX9600'

    # built-in ringtones are represented by mp3 files that don't appear in /dload/myringtone.dat
    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'Door Bell', 'VZW Default Ringtone',
                       'Telephone Ring', 'Simple Alert', 'Business Ring', 'Low Bell', 'Move Bell', 'Bubble Ring',
                       'Timeless', 'Voice of the Nature', 'Calling Trip', 'Latin Fever', 'Ride a Tiger', 'Allure',
                       'Limousine Blues', 'Surf the Groove', 'This Time', 'Under Cover of Darkness', 'Morning Call', 'Bee',
                       'Deep Blue Calling', 'East of Rain', 'No Ring',)

    ringtonelocations= (
        #  type          index file            default dir        external dir    max  type Index
        ( 'ringers',    'dload/myringtone.dat','brew/mod/10889/ringtones','mmc1/ringers', 100, 0x01,  100),
        ( 'sounds',     'dload/mysound.dat',   'brew/mod/18067',          '',             100, 0x02,  None),
        ( 'sounds(sd)', 'dload/sd_sound.dat',  'mmc1/my_sounds',          '',             100, 0x02,  None),
        ( 'music',      'dload/efs_music.dat', 'my_music',                '',             100, 0x104, None),
        ( 'music(sd)',  'dload/sd_music.dat',  'mmc1/my_music',           '',             100, 0x14,  None),
        )

    def setDMversion(self):
        self._DMv5=False
        self._DMv6=True
        self._timeout=5 # Assume a quick timeout on newer phones

    # Fundamentals:
    #  - get_esn             - same as LG VX-8300
    #  - getgroups           - same as LG VX-8700
    #  - getwallpaperindices - LGUncountedIndexedMedia
    #  - getringtoneindices  - LGUncountedIndexedMedia
    #  - DM Version          - 6
    #  - phonebook           - same as LG VX-8550
    #  - SMS                 - same as LG VX-9700

#-------------------------------------------------------------------------------
parentprofile=com_lgvx9700.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX9600'
    # inside screen resoluation
    WALLPAPER_WIDTH  = 480
    WALLPAPER_HEIGHT = 240

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 240, 'height': 480, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 480, 'height': 240, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 120, 'height': 100, 'format': "JPEG"}))

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None),         # all SMS list reading
        ('memo', 'read', None),        # all memo list reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
        ('ringtone', 'write', 'OVERWRITE'),
        ('sms', 'write', 'OVERWRITE'),        # all SMS list writing
        ('memo', 'write', 'OVERWRITE'),       # all memo list writing
##        ('playlist', 'read', 'OVERWRITE'),
##        ('playlist', 'write', 'OVERWRITE'),
        ('t9_udb', 'write', 'OVERWRITE'),
        )
    if __debug__:
        _supportedsyncs+=(
        ('t9_udb', 'read', 'OVERWRITE'),
        )
