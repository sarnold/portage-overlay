### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo5500.py 2313 2005-04-21 03:28:25Z sawecw $

"""Talk to the Sanyo SCP-5500 cell phone"""

# standard modules
import time
import cStringIO

# my modules
import common
import p_sanyo5500
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import com_sanyonewer
import prototypes

class Phone(com_sanyonewer.Phone):
    "Talk to the Sanyo SCP-5500 cell phone"

    desc="SCP-5500"

    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=3

    protocolclass=p_sanyo5500
    serialsname='scp5500'
    
    builtinringtones=( 'None', 'Vibrate', 'Ringer & Voice', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8', '', '', '', '', '',
                       '', '', '', '', '', '', '',
                       'Tschaik.Swanlake', 'Satie Gymnop.#1',
                       'Bach Air on the G', 'Beethoven Sym.5', 'Greensleeves',
                       'Johnny Comes..', 'Foster Ky. Home', 'Asian Jingle',
                       'Disco', 'Toy Box', 'Rodeo' )

    calendar_defaultringtone=4

    def __init__(self, logtarget, commport):
        com_sanyonewer.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE

class Profile(com_sanyonewer.Profile):

    protocolclass=p_sanyo5500
    serialsname='scp5500'
    phone_manufacturer='SANYO'
    phone_model='SCP-5500/US'
    # GMR: 1.010SP   ,10024

    def __init__(self):
        com_sanyonewer.Profile.__init__(self)
