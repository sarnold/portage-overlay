### BITPIM
###
### Copyright (C) 2007 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_motov325.py 4541 2008-01-04 03:41:51Z djpham $

"""Communicate with Motorola phones using AT commands"""

import time

import common
import com_motov3m as v3m
import helpids
import p_motov325

parentphone=v3m.Phone
class Phone(parentphone):
    desc='Moto-V325'
    helpid=helpids.ID_PHONE_MOTOV325
    protocolclass=p_motov325
    serialsname='motov325'

    builtinringtones=(
        (0, ('Silent',)),
        (5, ('Vibe Dot', 'Vibe Dash', 'Vibe Dot Dot', 'Vibe Dot Dash',
             'Vibe Pulse')),
        (11, ('Alert', 'Standard', 'Bells', 'Triads', 'Up and Down')),
        (30, ('Moonlit Haze', 'Nightlife', 'Wind Chime', 'Random',
              'Bit & Bytes', 'Door Bell', 'Ding', 'One Moment', 'Provincial',
              'Harmonics', 'Interlude', 'Snaggle', 'Cosmic')),
        )

    def getwallpapers(self, fundamentals):
        """Retrieve wallpaper data"""
        # The V325 needs some time to switch from BREW back to MODEM mode
        # without this sleep, the switch will always come back with ERROR
        self.log('Waiting for the phone to switch back to mode modem')
        time.sleep(2)
        return parentphone.getwallpapers(self, fundamentals)

#------------------------------------------------------------------------------
parentprofile=v3m.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname

    # use for auto-detection
    phone_manufacturer='Motorola'
    phone_model='V325 '
    common_model_name='V325'
    generic_phone_model='Motorola V325 Phone'

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 184, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 96, 'height': 72, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))

