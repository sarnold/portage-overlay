### BITPIM
###
### Copyright (C) 2006 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$

"""Talk to the Sanyo VI-2300 cell phone"""

# my modules
import common
import p_sanyo200
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import com_sanyonewer
import prototypes

# Order is like the PM-8200
numbertypetab=( 'cell', 'home', 'office', 'pager',
                    'fax', 'data', 'none' )

class Phone(com_sanyonewer.Phone):
    "Talk to the Sanyo SCP-200 cell phone"

    desc="SCP-200"

    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=1

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        )    

    protocolclass=p_sanyo200
    serialsname='scp200'

    builtinringtones=( 'None', 'Vibrate', 'Ringer & Voice', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8', '', '', '', '', '',
                       '', '', '', '', '', '', '',
                       'Gymnopedie', 'Hungarian Dance No. 5',
                       'Dies Irae from Requiem', 'The Moment', 'Asian Jingle',
                       'Habanera', 'Ska Big Band', 'Asian Melody',
                       'Clair de Lune', 'Kung-fu')

    calendar_defaultringtone=4

    def __init__(self, logtarget, commport):
        com_sanyonewer.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE
        self.numbertypetab=numbertypetab

class Profile(com_sanyonewer.Profile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SANYO'
    phone_model='SCP-200/US'

    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=112
    OVERSIZE_PERCENTAGE=100

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None), # Read sms messages
        ('todo', 'read', None), # Read todos
    )

    def __init__(self):
        com_sanyonewer.Profile.__init__(self)
        self.numbertypetab=numbertypetab
