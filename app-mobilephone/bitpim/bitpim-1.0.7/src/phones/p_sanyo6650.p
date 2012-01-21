### BITPIM
###
### Copyright (C) 2007 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$

%{

"""Various descriptions of data specific to Sanyo Katana-II (SCP-6650)"""

from prototypes import *

# Make all sanyo stuff available in this module as well
from p_sanyo import *
from p_sanyomedia import *
from p_sanyonewer import *
from p_sanyo4930 import *
from p_sanyo6600 import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb
NUMPHONEBOOKENTRIES=300
MAXNUMBERS=500
MAXEMAILS=600
MAXURLS=300
MAXMEMOS=300
MAXADDRESSES=300
_NUMSPEEDDIALS=8
_NUMLONGNUMBERS=5
_LONGPHONENUMBERLEN=30
_NUMEVENTSLOTS=100
_NUMCALLALARMSLOTS=15

MAXNUMBERLEN=32
MAXEMAILLEN=96
MAXURLLEN=96
MAXMEMOLEN=96
HASRINGPICBUF=0
NUMGROUPS=20
NUMPHONENUMBERS=7
NUMEMAILS=2
FIRSTSPEEDDIAL=2
LASTSPEEDDIAL=9


%}


# Phonebook sort buffer. No longer compatible with older Sanyo phones.  Will
# need new getphonebook and savephonebook methods
PACKET pbsortbuffer:
    "Various arrays for sorting the phone book, speed dial, determining which"
    # slots are in use, etc.
    # This 4000 byte buffer is formed from the concatenation of 500 bytes of
    # payload from commands 0X 3c 0F through 0X 43 0F
    P UINT {'constant': 0x76} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 4096} bufsize
    P USTRING {'default': "sort buffer"} +comment
    # Don't know what it is.  A count and list of flags
    1 UINT groupslotsused
    2 UNKNOWN +pad
    * LIST {'length': NUMGROUPS, 'createdefault': True} +groupslotusedflags:
        1 UINT used "1 if slot in use"
    # Contact slots
    2 UINT slotsused
    * LIST {'length': NUMPHONEBOOKENTRIES, 'createdefault': True} +usedflags:
        1 UINT used "1 if slot in use"
    * LIST {'length': _NUMSPEEDDIALS} +speeddialindex:
        2 UINT {'default': 0xffff} numslot
    # Name slots used
    2 UINT nameslotsused  "Always seems to be the same.  Why duplicated?"
    * LIST {'length': NUMPHONEBOOKENTRIES, 'createdefault': True} +nameusedflags:
        1 UINT used "1 if slot in use"
    * LIST {'length': NUMPHONEBOOKENTRIES} +sortorder:
        2 UINT {'default': 0xffff} pbslot
    * USTRING {'terminator': None, 'sizeinbytes': NUMPHONEBOOKENTRIES} pbfirstletters
    # Phone number slots
    2 UINT numslotsused "Number of phone number slots used"
    * LIST {'length': MAXNUMBERS, 'createdefault': True} +numusedflags:
        1 UINT used "1 if slot in use"
    # Email address slots
    2 UINT emailslotsused
    * LIST {'length': MAXEMAILS, 'createdefault': True} +emailusedflags:
        1 UINT used "1 if slot in use"
    2 UINT urlslotsused
    * LIST {'length': MAXURLS, 'createdefault': True} +urlusedflags:
        1 UINT used "1 if slot in use"
    2 UINT num_address
    # Slots with an address
    * LIST {'length': NUMPHONEBOOKENTRIES, 'createdefault': True} +addressusedflags:
        1 UINT used "1 if slot in use"
    # Slots with a memo Needs to be checked.
    2 UINT num_memo
    * LIST {'length': NUMPHONEBOOKENTRIES, 'createdefault': True} +memousedflags:
        1 UINT used "1 if slot in use"
    # We see stuff repeating here, so 6*1024 must be enough.
    # Pad out the rest of the buffer
    543 UNKNOWN +junk
