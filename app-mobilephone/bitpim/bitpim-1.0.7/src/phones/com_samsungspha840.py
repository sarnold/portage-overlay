### BITPIM
###
### Copyright (C) 2006 Stephen Wood <saw@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungspha840.py 3918 2007-01-19 05:15:12Z djpham $

"""Communicate with a Samsung SPH-A840"""

import sha
import re
import struct

import common
import commport
import p_brew
import p_samsungspha620
import p_samsungspha840
import com_brew
import com_phone
import com_samsung_packet
import com_samsungspha620
import prototypes
import helpids

numbertypetab=('cell','home','office','pager','fax','none')

class Phone(com_samsungspha620.Phone):
    "Talk to a Samsung SPH-A840 phone"

    desc="SPH-A840"
    helpid=helpids.ID_PHONE_SAMSUNGOTHERS
    protocolclass=p_samsungspha840
    serialsname='spha840'

    # jpeg Remove first 124 characters

    imagelocations=(
        # offset, index file, files location, origin, maximumentries, header offset
        # Offset is arbitrary.  100 is reserved for amsRegistry indexed files
        (400, "cam/dldJpeg", "camera", 100, 124),
        (300, "cam/jpeg", "camera", 100, 124),
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
    phone_model='SPH-A840/152'

    def __init__(self):
        parentprofile.__init__(self)
        self.numbertypetab=numbertypetab


