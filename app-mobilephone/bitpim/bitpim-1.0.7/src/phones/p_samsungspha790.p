### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: $
 
%{

from prototypes import *
from p_samsung_packet import *

# We use LSB for all integer like fields in diagnostic mode
UINT=UINTlsb
BOOL=BOOLlsb
#

# Phonebook constants
NUMPHONEBOOKENTRIES=500
NUMEMAILS=1
NUMPHONENUMBERS=5
MAXNUMBERLEN=32
NUMGROUPS=7
MAXNAMELEN=32
NUMSPEEDDIALS=100

# Wallpaper
WP_CAMERA_PATH='digital_cam/jpeg'

NUMTODOENTRIES=9


%}

PACKET pbentry:
    * CSVINT slot "Internal Slot"
    * CSVINT uslot "User Slot, Speed dial"
    * CSVSTRING name
    * CSVINT wallpaper
    * CSVINT primary    # Which one is the primary one?
    * LIST {'length': NUMPHONENUMBERS, 'createdefault': True, 'elementclass': phonenumber} numbers
    * CSVSTRING email
    * CSVSTRING url
    * CSVSTRING nick
    * CSVSTRING memo
    * CSVINT group
    * CSVINT ringtone
    * CSVTIME {'terminator': None } timestamp

PACKET phonebookslotresponse:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'constant': '#PBOKR:'} command
    * pbentry entry

PACKET speeddial_entry:
    1 UINT on_flg1
    1 UINT on_flg2
    2 UINT uslot
    1 UINT which

PACKET speeddial_file: 
    * LIST { 'elementclass': speeddial_entry } items

PACKET groupnameresponse:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'constant': '#PBGRR:'} command
    * groupnameentry entry

PACKET groupnameentry:
    * CSVINT gid
    * CSVSTRING groupname
    * CSVINT ringtone "Ringtone assignment?"
    * CSVSTRING {'quotechar': None} dunno2 "A single character C or S"
    * CSVTIME {'terminator': None} timestamp

PACKET groupnamesetrequest:
    * CSVSTRING {'quotechar': None, 'terminator': None,
                 'default': '#PBGRW='} +command
    * CSVINT gid "Group #"
    * CSVSTRING groupname
    * CSVINT { 'default': 0 } +ringtone     # Default Tone for now
    * CSVTIME {'terminator': None,
               'default': (1980,1,1,12,0,0) } +timestamp
