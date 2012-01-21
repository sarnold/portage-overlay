### BITPIM
###
### Copyright (C) 2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo7300.py 2321 2005-04-23 01:12:49Z sawecw $

"""Talk to the Sanyo SCP-7300 (RL2000) cell phone"""

# my modules
import common
import p_sanyo7300
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import com_sanyonewer
import prototypes


class Phone(com_sanyonewer.Phone):
    "Talk to the Sanyo SCP-7300 cell phone"

    desc="SCP-7300"

    FIRST_MEDIA_DIRECTORY=2
    LAST_MEDIA_DIRECTORY=3

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        )    

    protocolclass=p_sanyo7300
    serialsname='scp7300'

    calendar_defaultringtone=4

    def __init__(self, logtarget, commport):
        com_sanyonewer.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE

class Profile(com_sanyonewer.Profile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SANYO'
    phone_model='SCP-7300/US'

    WALLPAPER_WIDTH=132
    WALLPAPER_HEIGHT=176
    OVERSIZE_PERCENTAGE=100

    def __init__(self):
        com_sanyonewer.Profile.__init__(self)
