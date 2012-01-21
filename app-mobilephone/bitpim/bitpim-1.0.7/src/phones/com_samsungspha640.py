### BITPIM
###
### Copyright (C) 2004-2005 Stephen Wood <saw@bitpim.org>
### Copyright (C) 2005 Todd Imboden
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### By Allan Slawik; based on code from com_samsungspha620.py, and 
### com_samsungspha460.py by sawecw and djpham
###
### $Id:$

"""Communicate with a Samsung SPH-A640"""

import sha
import re
import struct

import common
import commport
import p_samsungspha640
import p_brew
import com_brew
import com_phone
import com_samsung_packet
import com_samsungspha620
import prototypes
import fileinfo
import helpids

numbertypetab=('home','cell','office','other','pager','none')

class Phone(com_samsungspha620.Phone):
    "Talk to a Samsung SPH-A640 phone"

    desc="SPH-A640"
    helpid=helpids.ID_PHONE_SAMSUNGOTHERS
    protocolclass=p_samsungspha640
    serialsname='spha640'

    # digital_cam/jpeg Remove first 128 characters

    imagelocations=(
        # offset, index file, files location, origin, maximumentries, header offset
        # Offset is arbitrary.  100 is reserved for amsRegistry indexed files
        (400, "cam/dldJpeg", "camera", 100, 128),
        (300, "cam/jpeg", "camera", 100, 128),
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries, header offset
        )
        
    __audio_mimetype={ 'mid': 'audio/midi', 'qcp': 'audio/vnd.qcelp', 'pmd': 'application/x-pmd'}
    __image_mimetype={ 'jpg': 'image/jpg', 'jpeg': 'image/jpeg', 'gif': 'image/gif', 'bmp': 'image/bmp', 'png': 'image/png'}

    def __init__(self, logtarget, commport):
        com_samsungspha620.Phone.__init__(self, logtarget, commport)
        self.numbertypetab=numbertypetab
        self.mode=self.MODENONE
        
parentprofile=com_samsungspha620.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_ ."
    RINGTONE_LIMITS= {
        'MAXSIZE': 500000
    }
    phone_manufacturer='SAMSUNG'
    phone_model='SPH-A640/152'

    def __init__(self):
        parentprofile.__init__(self)
        self.numbertypetab=numbertypetab

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
       # ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', None), # Image conversion needs work
        ('ringtone', 'read', None),   # all ringtone reading
        ('ringtone', 'write', None),
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('todo', 'read', None),     # all todo list reading
        ('todo', 'write', 'OVERWRITE'),  # all todo list writing
        ('memo', 'read', None),     # all memo list reading
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing
        )

