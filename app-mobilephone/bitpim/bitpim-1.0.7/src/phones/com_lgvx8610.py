### BITPIM
###
### Copyright (C) 2008 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx8610.py 4641 2008-07-23 18:32:47Z djpham $

"""
Communicate with the LG VX8610 (Decoy) cell phone.  This is based on the enV2 model
"""

import common
import com_lgvx9100
import p_lgvx9100
import helpids

#-------------------------------------------------------------------------------
parentphone=com_lgvx9100.Phone
class Phone(parentphone):
    "Talk to the LG VX8610 (Decoy) cell phone"

    desc="LG-VX8610"
    helpid=helpids.ID_PHONE_LGVX8610
    protocolclass=p_lgvx9100
    serialsname='lgvx8610'
    my_model='VX8610'

    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)

#-------------------------------------------------------------------------------
parentprofile=com_lgvx9100.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX8610'

    WALLPAPER_WIDTH=240
    WALLPAPER_HEIGHT=320

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))
    def GetImageOrigins(self):
        return self.imageorigins


##    ringtoneorigins=('ringers', 'sounds', 'sounds(sd)',' music', 'music(sd)')
##    excluded_ringtone_origins=('sounds', 'sounds(sd)', 'music', 'music(sd)')
    ringtoneorigins=('ringers', 'sounds', 'sounds(sd)')
    excluded_ringtone_origins=('sounds', 'sounds(sd)')

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 240, 'height': 320, 'format': "JPEG"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets
