### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo4900.py 2319 2005-04-22 03:50:56Z sawecw $

"""Talk to the Sanyo SCP-4900 cell phone"""

# my modules
import time
import common
import p_sanyo4900
import com_brew
import com_phone
import com_sanyo
import prototypes


class Phone(com_sanyo.Phone):
    "Talk to the Sanyo SCP-4900 cell phone"

    desc="SCP-4900"

    protocolclass=p_sanyo4900
    serialsname='scp4900'

    builtinringtones=( 'None', 'Vibrate', 'Ringer & Voice', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       '', '', '', '', '', '', '', '', '', '', '', '', '', '',
                       '', 'La Bamba', 'Foster Dreamer', 'Schubert March',
                       'Mozart Eine Kleine', 'Debussey Arabesq', 'Nedelka',
                       'Brahms Hungarian', 'Star Spangled Banner', 'Rodeo',
                       'Birds', 'Toy Box' )
                      
    calendar_defaultringtone=0
    calendar_tonerange=xrange(100,100)
    calendar_toneoffset=0

    def __init__(self, logtarget, commport):
        com_sanyo.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE



class Profile(com_sanyo.Profile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SANYO'
    phone_model='SCP-4900/US'
    # GMR: 1.057SP   ,10018

    WALLPAPER_WIDTH=120
    WALLPAPER_HEIGHT=128
    OVERSIZE_PERCENTAGE=100
    
    def __init__(self):
        com_sanyo.Profile.__init__(self)
