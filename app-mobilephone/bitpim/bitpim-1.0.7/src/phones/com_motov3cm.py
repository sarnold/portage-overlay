### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_motov3cm.py 4255 2007-05-28 02:12:29Z djpham $

"""Communicate with Motorola V3cm phones using AT commands"""

# BitPim modules
import com_motov710m
import p_motov3c
import helpids

parentphone=com_motov710m.Phone
class Phone(parentphone):
    desc='Moto-V3cm'
    helpid=helpids.ID_PHONE_MOTOV3CM
    serialsname='motov3cm'
    protocolclass=p_motov3c

    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)

#------------------------------------------------------------------------------
parentprofile=com_motov710m.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    # use for auto-detection
    phone_manufacturer='Motorola'
    phone_model='V3cm'
    common_model_name='V3c'
    generic_phone_model='Motorola CDMA V3c Phone'
