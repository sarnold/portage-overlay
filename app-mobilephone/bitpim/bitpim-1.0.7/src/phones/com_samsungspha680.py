### BITPIM
###
### Copyright (C)  Stephen Wood <saw@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungspha680.py 3460 2006-07-08 23:55:09Z djpham $

"""Communicate with a Samsung SPH-A680"""

import sha
import re
import struct

import common
import commport
import p_brew
import p_samsungspha620
import p_samsungspha680
import com_brew
import com_phone
import com_samsung_packet
import com_samsungspha620
import prototypes

numbertypetab=('home','office','cell','pager','fax','none')

class Phone(com_samsungspha620.Phone):
    "Talk to a Samsung SPH-A680 phone"

    desc="SPH-A680"

    protocolclass=p_samsungspha680
    serialsname='spha680'

    # jpeg Remove first 124 characters

    imagelocations=(
        # offset, index file, files location, origin, maximumentries, header offset
        # Offset is arbitrary.  100 is reserved for amsRegistry indexed files
        (300, "cam/jpeg", "camera", 100, 124),
        (400, "cam/dldJpeg", "camera", 100, 124),
        (500, "cam/mjpeg", "camera", 100, 124),
        (600, "cam/dldMjpeg", "camera", 100, 124),
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries, header offset
        )
        

    def __init__(self, logtarget, commport):
        com_samsungspha620.Phone.__init__(self, logtarget, commport)
        self.numbertypetab=numbertypetab
        self.mode=self.MODENONE

parentprofile=com_samsungspha620.Profile
class Profile(parentprofile):
    deviceclasses=("modem",)

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SAMSUNG'
    phone_model='SPH-A680/152'

    def __init__(self):
        parentprofile.__init__(self)
        self.numbertypetab=numbertypetab


