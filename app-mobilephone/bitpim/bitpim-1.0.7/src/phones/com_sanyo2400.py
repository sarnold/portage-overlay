### BITPIM
###
### Copyright (C) 2006 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$

"""Talk to the Sanyo SCP-2400 cell phone"""
# standard modules
import re
import time
import sha

# my modules
import common
import p_brew
import p_sanyo8300
import p_sanyo2400
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import com_sanyonewer
import com_sanyo3100
import prototypes
import bpcalendar

numbertypetab=( 'cell', 'home', 'office', 'pager',
                    'fax', 'data', 'none' )

class Phone(com_sanyo3100.Phone):
    "Talk to the Sanyo SCP-2400 cell phone"

    desc="SCP-2400"

    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=2

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        )    

    protocolclass=p_sanyo2400
    serialsname='scp2400'

    builtinringtones=( 'None', 'Vibrate', 'Ringer & Voice', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8', '', '', '', '', '',
                       '', '', '', '', '', '', '',
                       'Tschaik.Swanlake', 'Satie Gymnop.#1',
                       'Hungarian Dance', 'Beethoven Sym.5', 'Greensleeves',
                       'Foster Ky. Home', 'The Moment', 'Asian Jingle',
                       'Disco')

    calendar_defaultringtone=0
    calendar_defaultcaringtone=0

    def __init__(self, logtarget, commport):
        com_sanyo3100.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE
        self.numbertypetab=numbertypetab

    my_model='SCP-2400/US'
    my_manufacturer='SANYO'

parentprofile=com_sanyo3100.Profile
class Profile(parentprofile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer=Phone.my_manufacturer
    phone_model=Phone.my_model

    WALLPAPER_WIDTH=176
    WALLPAPER_HEIGHT=220

    # which usb ids correspond to us
    
    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
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

