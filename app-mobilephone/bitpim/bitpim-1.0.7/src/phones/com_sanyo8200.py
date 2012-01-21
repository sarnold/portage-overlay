### BITPIM
###
### Copyright (C) 2004-2006 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo8200.py 3565 2006-09-03 03:17:42Z sawecw $

"""Talk to the Sanyo SCP-8200 cell phone"""

# my modules
import common
import p_sanyo8200
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import com_sanyonewer
import prototypes

numbertypetab=( 'cell', 'home', 'office', 'pager',
                    'fax', 'data', 'none' )

class Phone(com_sanyonewer.Phone):
    "Talk to the Sanyo PM8200 cell phone"

    desc="PM8200"

    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=3

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        )    

    protocolclass=p_sanyo8200
    serialsname='pm8200'

    builtinringtones=( 'None', 'Vibrate', '', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8', '', '', '', '', '',
                       '', '', '', '', '', '', '',
                       'Tschaik.Swanlake', 'Satie Gymnop.#1',
                       'Hungarian Dance', 'Beethoven Sym.5', 'Greensleeves',
                       'Foster Ky. Home', 'The Moment', 'Asian Jingle',
                       'Disco','','','','','','','','','','','','','','','','','',
                       'Voice Alarm')

    def __init__(self, logtarget, commport):
        com_sanyonewer.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE
        self.numbertypetab=numbertypetab

class Profile(com_sanyonewer.Profile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SANYO'
    phone_model='SCP-8200/US'
    # GMR: 1.115SP   ,10019

    WALLPAPER_WIDTH=132
    WALLPAPER_HEIGHT=160

    def __init__(self):
        com_sanyonewer.Profile.__init__(self)
        self.numbertypetab=numbertypetab

        # NOTE: Calendar alarm 35 is Foster Ky. Home.
