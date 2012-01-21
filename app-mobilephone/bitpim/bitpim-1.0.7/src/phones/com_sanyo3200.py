### BITPIM
###
### Copyright (C) 2005 Stephen Wood <sawecw@users.sf.net>
### Copyright (C) 2007 Yan Ke <yke@cmu.edu>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo3200.py 4086 2007-03-11 04:49:43Z yke $

"""Talk to the Sanyo SCP-3200 cell phone"""
# standard modules
import re
import time
import sha

# my modules
import common
import p_brew
import p_sanyo8300
import p_sanyo3200
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import com_sanyonewer
import com_sanyo3100
import com_sanyo8300
import prototypes
import bpcalendar
import call_history

numbertypetab=( 'cell', 'home', 'office', 'pager',
                    'fax', 'data', 'none' )

class Phone(com_sanyo3100.Phone):
    "Talk to the Sanyo SCP-3200 cell phone"

    desc="SCP-3200"
# WOrking directories 1,2,4
    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=2

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        )    

    protocolclass=p_sanyo3200
    serialsname='scp3200'

    builtinringtones=( 'None', 'Vibrate', '', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8',
                       '', '', '', '', '',
                       '', '', '',
                       '', '', '', '',
                       'Hungarian Dance No.5', 'Asian Jingle',
                       'Ska Big Band', 'Habanera', 'Clair de Lune',
                       'Nocturne', 'Techno Beat', 'Jazz Melody','','','','','','','','','','','','','','','','','','','Ringer & Voice')

    calendar_defaultringtone=4
    calendar_defaultcaringtone=4

    def __init__(self, logtarget, commport):
        com_sanyo8300.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE
        self.numbertypetab=numbertypetab

    # Phone Detection-----------------------------------------------------------
    my_model='SCP3200'
    detected_model='SCP-3200/US'
    my_manufacturer='SANYO'

parentprofile=com_sanyo3100.Profile
class Profile(parentprofile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer=Phone.my_manufacturer
    phone_model=Phone.my_model

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
#        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
#        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'read', None),  # all wallpaper reading
#        ('ringtone', 'read', None),   # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
#        ('sms', 'read', None), # Read sms messages
        ('todo', 'read', None), # Read todos
    )

    def __init__(self):
        parentprofile.__init__(self)
        com_sanyonewer.Profile.__init__(self)
        self.numbertypetab=numbertypetab
