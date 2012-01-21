#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx5400.py 4472 2007-11-29 03:58:54Z djpham $

"""
Communicate with the LG VX5400 cell phone
"""

import common
import com_lgvx8550
import p_lgvx8550

p_lgvx5400=p_lgvx8550
parentphone=com_lgvx8550.Phone
class Phone(parentphone):
    desc="LG-VX5400"
    helpid=None
    protocolclass=p_lgvx5400
    serialsname='lgvx5400'

    my_model='VX5400'

    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'Door Bell', 'VZW Default Ringtone') + \
                      tuple(['Ringtone '+`n` for n in range(1,13)]) + \
                      ('No Ring',)

    ringtonelocations= (
        # type           index file             default dir                 external dir  max  type   index
        ('ringers',     'dload/myringtone.dat','brew/mod/10889/ringtones', '',            100, 0x01,  100),
	( 'sounds',     'dload/mysound.dat',   'brew/mod/18067',           '',            100, 0x02,  None),
        )

    wallpaperlocations= (
        #  type          index file            default dir     external dir  max  type Index
        ( 'images',     'dload/image.dat',    'brew/mod/10888', '',          100, 0x00, 100),
        )

parentprofile=com_lgvx8550.Profile
class Profile(parentprofile):
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX5400'
    # inside screen resoluation
    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=160

    ringtoneorigins=('ringers', 'sounds')

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 128, 'height': 160, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 96, 'height': 64, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 96, 'height': 64, 'format': "JPEG"}))

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
        ('t9_udb', 'write', 'OVERWRITE'),
        )
    if __debug__:
        _supportedsyncs+=(
        ('t9_udb', 'read', 'OVERWRITE'),
        )
