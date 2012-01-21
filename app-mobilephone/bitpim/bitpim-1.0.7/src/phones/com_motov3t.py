### BITPIM
###
### Copyright (C) 2007 Roger Binns <rogerb@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_motov3c.py 3460 2006-07-08 23:55:09Z djpham $

"""Motorola V3t GSM phone"""

import common
import com_moto_gsm

class Phone(com_moto_gsm.Phone):
    """Talk to a Motorola RAZR V3t GSM phone"""
    desc="Moto-RAZR-V3t"
    serialsname="motov3t"

    def __init__(self, logtarget, commport):
        com_moto_gsm.Phone.__init__(self, logtarget, commport)

parentprofile=com_moto_gsm.Profile
class Profile(parentprofile):

    serialsname=Phone.serialsname

    WALLPAPER_WIDTH=176
    WALLPAPER_HEIGHT=220
    MAX_WALLPAPER_BASENAME_LENGTH=37
    WALLPAPER_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()_ .-"
    WALLPAPER_CONVERT_FORMAT="jpg"

    # Motorola USB device
    usbids=( ( 0x22B8, 0x4902, 1),
             )
    deviceclasses=("modem",)

    # use for auto-detection
    phone_manufacturer='Motorola'
    phone_model='V3t '
    common_model_name='V710'
    generic_phone_model='Motorola CDMA v710 Phone'

    def __init__(self):
        super(Profile, self).__init__()

    # all dumped in "images"
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 200, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))
    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets
