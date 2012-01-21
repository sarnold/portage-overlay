### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo8100_bell.py 3753 2006-12-07 04:03:00Z sawecw $

"""Talk to the Sanyo SCP-8100 Bell Mobility (Canada) cell phone"""

# my modules
import common
import p_sanyo8100_bell
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import com_sanyonewer
import prototypes

import os

class Phone(com_sanyonewer.Phone):
    "Talk to the Sanyo SCP-8100 Bell Mobility (Canada) cell phone"

    desc="SCP-8100-Bell"

    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=3

    protocolclass=p_sanyo8100_bell
    serialsname='scp8100bell'
    
# Need to check these from Bell.  

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
        com_sanyonewer.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE

class Profile(com_sanyonewer.Profile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SANYO'
    phone_model='SCP-8100CA'

    WALLPAPER_WIDTH=132
    WALLPAPER_HEIGHT=144
    OVERSIZE_PERCENTAGE=100

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        # ('wallpaper', 'write', 'MERGE'),
        # ('ringtone', 'write', 'MERGE'),
    )

    def __init__(self):
        com_sanyonewer.Profile.__init__(self)
