### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo8100.py 2717 2006-01-01 04:22:29Z sawecw $

"""Talk to the Sanyo SCP-8100 cell phone"""

# my modules
import common
import p_sanyo8100
import com_sanyomedia
import com_sanyo
import com_brew
import com_phone
import prototypes

import os

class Phone(com_sanyomedia.SanyoMedia,com_sanyo.Phone):
    "Talk to the Sanyo SCP-8100 cell phone"

    desc="SCP-8100"

    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=3

    protocolclass=p_sanyo8100
    serialsname='scp8100'
    
    builtinringtones=( 'None', 'Vibrate', 'Ringer & Voice', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8', '', '', '', '', '',
                       '', '', '', '', '', '', '',
                       'Tschaik.Swanlake', 'Satie Gymnop.#1',
                       'Bach Air on the G', 'Beethoven Sym.5', 'Greensleeves',
                       'Johnny Comes..', 'Foster Ky. Home', 'Asian Jingle',
                       'Disco' )

    calendar_defaultringtone=4
    calendar_defaultcaringtone=4
    calendar_tonerange=xrange(18,26)
    calendar_toneoffset=8

    def __init__(self, logtarget, commport):
        com_sanyo.Phone.__init__(self, logtarget, commport)
        com_sanyomedia.SanyoMedia.__init__(self)
        self.mode=self.MODENONE

class Profile(com_sanyo.Profile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SANYO'
    phone_model='SCP-8100/US'
    # GMR: 1.115SP   ,10019

    WALLPAPER_WIDTH=132
    WALLPAPER_HEIGHT=144
    OVERSIZE_PERCENTAGE=100

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),
        ('ringtone', 'write', 'MERGE'),
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None),
    )

    def __init__(self):
        com_sanyo.Profile.__init__(self)
