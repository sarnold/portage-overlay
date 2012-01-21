### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo5300.py 2321 2005-04-23 01:12:49Z sawecw $

"""Talk to the Sanyo SCP-5300 cell phone"""

# my modules
import common
import p_sanyo5300
import com_brew
import com_phone
import com_sanyo
import prototypes


class Phone(com_sanyo.Phone):
    "Talk to the Sanyo SCP-5300 cell phone"

    desc="SCP-5300"

    protocolclass=p_sanyo5300
    serialsname='scp5300'
    
    builtinringtones=( 'None', 'Vibrate', 'Ringer & Voice', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8', '', '', '', '', '',
                       '', '', '', '', '', '', '',
                       'HallelujahSamba', 'Amazing Grace',
                       'The Entertainer', 'Mozart Eine..', 'Canon',
                       'Chopin Waltz', 'Brahms Hungar..', 'Asian Jingle',
                       'Rodeo', 'Call Delivery', 'Toy Box' )

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
    phone_model='SCP-5300/US'

    WALLPAPER_WIDTH=132
    WALLPAPER_HEIGHT=144
    OVERSIZE_PERCENTAGE=100
        
    def __init__(self):
        com_sanyo.Profile.__init__(self)
