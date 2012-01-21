### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_motoe815.py 3918 2007-01-19 05:15:12Z djpham $

"""Communicate with Motorola E815 phones using AT commands"""

# BitPim modules
import com_motov710
import helpids

parentphone=com_motov710.Phone
class Phone(parentphone):
    desc='Moto-E815'
    helpid=helpids.ID_PHONE_MOTOE815
    serialsname='motoe815'

#------------------------------------------------------------------------------
parentprofile=com_motov710.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    # use for auto-detection
    phone_manufacturer='Motorola'
    phone_model='E815 '
    common_model_name='E815'
    generic_phone_model='Motorola CDMA e815 Phone'
