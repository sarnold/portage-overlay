### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo7200.py 2321 2005-04-23 01:12:49Z sawecw $

"""Talk to the Sanyo SCP-7200 (RL2000) cell phone"""

# my modules
import common
import p_sanyo7200
import com_brew
import com_phone
import com_sanyo
import prototypes


class Phone(com_sanyo.Phone):
    "Talk to the Sanyo SCP-7200 cell phone"

    desc="SCP-7200"

    protocolclass=p_sanyo7200
    serialsname='scp7200'

    builtinringtones=( 'None', 'Vibrate', 'Ringer & Voice')
                      
    calendar_defaultringtone=0

    def __init__(self, logtarget, commport):
        com_sanyo.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE

    def savecalendar(self, dict, merge):
        req=self.protocolclass.beginendupdaterequest()
        req.beginend=1 # Start update
        res=self.sendpbcommand(req, self.protocolclass.beginendupdateresponse, writemode=True)

        self.writewait()
        result = com_sanyo.Phone.savecalendar(self, dict, merge)

class Profile(com_sanyo.Profile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SANYO'
    phone_model='SCP-7200/US'

    WALLPAPER_WIDTH=120
    WALLPAPER_HEIGHT=128
    OVERSIZE_PERCENTAGE=100

    def __init__(self):
        com_sanyo.Profile.__init__(self)
