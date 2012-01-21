### BITPIM
###
### Copyright (C) 2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyonewer.py 3918 2007-01-19 05:15:12Z djpham $

"""Common code for newer SCP-5500 style phones"""

# standard modules
import time
import cStringIO

# my modules
import common
import p_sanyonewer
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import prototypes
import helpids

class Phone(com_sanyomedia.SanyoMedia,com_sanyo.Phone):
    "Talk to a Sanyo SCP-5500 style cell phone"
    helpid=helpids.ID_PHONE_SANYOOTHERS
    builtinringtones=( 'None', 'Vibrate', 'Ringer & Voice', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8', '', '', '', '', '',
                       '', '', '', '', '', '', '',
                       'Tschaik.Swanlake', 'Satie Gymnop.#1',
                       'Bach Air on the G', 'Beethoven Sym.5', 'Greensleeves',
                       'Johnny Comes..', 'Foster Ky. Home', 'Asian Jingle',
                       'Disco', 'Toy Box', 'Rodeo' )

    calendar_defaultringtone=4
    calendar_defaultcaringtone=4
    calendar_tonerange=xrange(18,26)
    calendar_toneoffset=8

    def __init__(self, logtarget, commport):
        com_sanyo.Phone.__init__(self, logtarget, commport)
        com_sanyomedia.SanyoMedia.__init__(self)
        self.mode=self.MODENONE

    def sendpbcommand(self, request, responseclass, callsetmode=True, writemode=False, numsendretry=2, returnerror=False):
         
        # writemode seems not to be needed for this phone
        res=com_sanyo.Phone.sendpbcommand(self, request, responseclass, callsetmode=callsetmode, writemode=False, numsendretry=numsendretry, returnerror=returnerror)
        return res
 

    def savecalendar(self, dict, merge):
        req=self.protocolclass.beginendupdaterequest()
        req.beginend=1 # Start update
        res=self.sendpbcommand(req, self.protocolclass.beginendupdateresponse, writemode=True)

        self.writewait()
        result = com_sanyo.Phone.savecalendar(self, dict, merge)
    
class Profile(com_sanyo.Profile):

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
        ('sms', 'read', None), # Read sms messages
        ('todo', 'read', None), # Read todos
    )

    def __init__(self):
        com_sanyo.Profile.__init__(self)
