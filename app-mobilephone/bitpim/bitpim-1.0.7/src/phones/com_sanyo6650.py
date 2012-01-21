### BITPIM
###
### Copyright (C) 2007 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$

"""Talk to the Sanyo Katana-II (SCP-6650) cell phone"""
# standard modules
import re
import time
import sha

# my modules
import common
import p_brew
import p_sanyo8300
import p_sanyo4930
import p_sanyo6600
import p_sanyo6650
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import com_sanyonewer
import com_sanyo3100
import com_sanyo6600
import prototypes
import bpcalendar

numbertypetab=( 'cell', 'home', 'office', 'pager',
                    'fax', 'none')

class Phone(com_sanyo6600.Phone):
    "Talk to the Sanyo Katana-II (SCP-6650) cell phone"

    desc="SCP-6650"

    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=2

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        )
    wallpaperexts=(".jpg", ".png", ".mp4", ".3g2",".JPG")


    protocolclass=p_sanyo6650
    serialsname='scp6650'

    builtinringtones=( 'None', 'Vibrate', '', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8', '', '', '', '', '',
                       '', '', '', '', 
                       'Requiem:Dies Irae', 'Minute Waltz', 'Hungarian Dance',
                       'Military March', 'Ten Little Indians',
                       'Head,Shoulders,Knees&Toes', 'The Moment', 'Asian Jingle',
                       'Kung-fu','','','','','','','','','','','','','','','','','',
                       '','','','','','',
                       'Voice Alarm')


    calendar_defaultringtone=0
    calendar_defaultcaringtone=0
    calendar_toneoffset=33
    calendar_tonerange=xrange(4,100)

    def __init__(self, logtarget, commport):
        com_sanyo6600.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE
        self.numbertypetab=numbertypetab

    my_model='SCP6650'
    detected_model='SCP-6650/US'
    my_manufacturer='SANYO'

parentprofile=com_sanyo6600.Profile
class Profile(parentprofile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer=Phone.my_manufacturer
    phone_model=Phone.my_model

    usbids=( ( 0x0474, 0x0745, 2),)  # VID=Sanyo,
    deviceclasses=("serial",)

    def __init__(self):
        parentprofile.__init__(self)
        com_sanyonewer.Profile.__init__(self)
        self.numbertypetab=numbertypetab

