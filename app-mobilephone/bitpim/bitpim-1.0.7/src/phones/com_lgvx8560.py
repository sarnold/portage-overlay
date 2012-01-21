#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2008 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx8560.py 4678 2008-08-13 23:46:56Z djpham $


"""
Communicate with the LG VX8560 cell phone. (aka VX8610)
"""

# BitPim modules
import common
import com_brew
import prototypes
import com_lgvx9700
import p_lgvx8560
import helpids

#-------------------------------------------------------------------------------
parentphone=com_lgvx9700.Phone
class Phone(parentphone):
    desc="LG-VX8560 (Chocolate 3)"
    protocolclass=p_lgvx8560
    serialsname='lgvx8560'
    helpid=helpids.ID_PHONE_LGVX8560
    
    my_model='VX8560'

    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'Door Bell', 'VZW Default Ringtone') + \
                      tuple(['Ringtone '+`n` for n in range(1,21)]) + \
                      ('No Ring',)

    def setDMversion(self):
        self._DMv5 = False
        self._DMv6 = True
        self._timeout=5 # Assume a quick timeout

    # Fundamentals:
    #  - get_esn             - same as LG VX-8300
    #  - getgroups           - same as LG VX-8700
    #  - getwallpaperindices - LGUncountedIndexedMedia
    #  - getringtoneindices  - LGUncountedIndexedMedia
    #  - DM Version          - 6
    #  - phonebook           - same as LG VX-8550 with HPE entry VX8610
    #  - sms                 - same as LG VX-9700

    # Calendar stuff------------------------------------------------------------
    def _scheduleextras(self, data, fwversion):
        data.serial_number = '000000ca-00000000-00000000-' + fwversion
        data.unknown3 = 0x01fa

#-------------------------------------------------------------------------------
parentprofile=com_lgvx9700.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX8560'
    # inside screen resoluation
    WALLPAPER_WIDTH  = 240
    WALLPAPER_HEIGHT = 320

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 240, 'height': 320, 'format': "JPEG"}))
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
