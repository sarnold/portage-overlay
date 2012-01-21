### BITPIM
###
### Copyright (C) 2005 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo2300.py 3635 2006-10-29 22:24:19Z sawecw $

"""Talk to the Sanyo VI-2300 cell phone"""

# my modules
import common
import p_sanyo2300
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
    "Talk to the Sanyo VI-2300 cell phone"

    desc="SCP-2300"

    FIRST_MEDIA_DIRECTORY=2
    LAST_MEDIA_DIRECTORY=3

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        )    

    protocolclass=p_sanyo2300
    serialsname='vi2300'

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
    phone_model='SCP-2300/US'

    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=112
    OVERSIZE_PERCENTAGE=100

    def __init__(self):
        com_sanyonewer.Profile.__init__(self)
        self.numbertypetab=numbertypetab
