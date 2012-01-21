### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_motov3c.py 4255 2007-05-28 02:12:29Z djpham $

"""Communicate with Motorola V3c phones using AT commands"""

# system modules

# BitPim modules
import com_motov710
import p_motov3c
import helpids

parentphone=com_motov710.Phone
class Phone(parentphone):
    desc='Moto-V3c'
    helpid=helpids.ID_PHONE_MOTOV3C
    serialsname='motov3c'
    protocolclass=p_motov3c

    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)

#------------------------------------------------------------------------------
parentprofile=com_motov710.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    # use for auto-detection
    phone_manufacturer='Motorola'
    phone_model='V3c '
    common_model_name='V3c'
    generic_phone_model='Motorola CDMA V3c Phone'
