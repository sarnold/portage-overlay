#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx8600.py 4305 2007-07-16 04:05:25Z djpham $

"""
Communicate with the LG VX8600 cell phone, which I was told is VERY similar to
the VX-8500
"""

# BitPim modules
import common
import com_lgvx8500
import p_lgvx8600
import helpids

#-------------------------------------------------------------------------------
parentphone=com_lgvx8500.Phone
class Phone(parentphone):
    desc="LG-VX8600"
    helpid=helpids.ID_PHONE_LGVX8600
    protocolclass=p_lgvx8600
    serialsname='lgvx8600'

    my_model='VX8600'

    def setDMversion(self):
        _fw_version=self.get_firmware_version()[-1]
        # T86VZV03 uses DMv5
        self._DMv5=self.my_model=='VX8600' and _fw_version>'2'
        if self._DMv5:
            # takes about 30 seconds for T86VZV03 to kick out of DM
            self._timeout = 30

    # Fundamentals:
    #  - get_esn             - same as LG VX-8300
    #  - getgroups           - same as LG VX-8100
    #  - getwallpaperindices - LGUncountedIndexedMedia
    #  - getrintoneindices   - LGUncountedIndexedMedia
    #  - DM Version          - T86VZV01 - T86VZV02: 4, T86VZV03: 5

#-------------------------------------------------------------------------------
parentprofile=com_lgvx8500.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX8600'
    # inside screen resoluation
    WALLPAPER_WIDTH=176
    WALLPAPER_HEIGHT=220

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 184, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 128, 'height': 160, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 128, 'height': 142, 'format': "JPEG"}))

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
