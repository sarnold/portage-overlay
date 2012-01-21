### BITPIM
###
### Copyright (C) 2008 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$

"""Talk to the Sanyo SCP-7050 cell phone"""
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
import p_sanyo7050
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
    "Talk to the Sanyo Katana-II (SCP-7050) cell phone"

    desc="SCP-7050"

    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=2

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        )
    wallpaperexts=(".jpg", ".png", ".mp4", ".3g2",".JPG")


    protocolclass=p_sanyo7050
    serialsname='scp7050'

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

    def getfundamentals(self, results):
        """Gets information fundamental to interopating with the phone and UI."""
        req=self.protocolclass.sanyoreset()
        res=self.sendpbcommand(req, p_brew.testing0cresponse)

        results['uniqueserial']=sha.new(self.get_esn()).hexdigest()
        self.getmediaindices(results)

        results['groups']=self.read_groups()

        self.log("Fundamentals retrieved")

        return results
        
    my_model='SCP7050'
    detected_model='SCP-7050/US'
    my_manufacturer='SANYO'

parentprofile=com_sanyo6600.Profile
class Profile(parentprofile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer=Phone.my_manufacturer
    phone_model=Phone.my_model

    usbids=( ( 0x0474, 0x0743, 2),)  # VID=Sanyo,
    deviceclasses=("serial",)

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        #('calendar', 'read', None),   # all calendar reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        #('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None), # Read sms messages
        ('todo', 'read', None), # Read todos
    )

    def __init__(self):
        parentprofile.__init__(self)
        com_sanyonewer.Profile.__init__(self)
        self.numbertypetab=numbertypetab

