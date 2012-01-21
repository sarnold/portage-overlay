### BITPIM
###
### Copyright (C) 2008 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$

%{

"""Various descriptions of data specific to Sanyo SCP-7050"""

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
NUMPHONEBOOKENTRIES=500
MAXNUMBERS=700
MAXEMAILS=1000
MAXURLS=500
MAXMEMOS=500
MAXADDRESSES=500
_NUMSPEEDDIALS=8
_NUMLONGNUMBERS=5
_LONGPHONENUMBERLEN=30
_NUMEVENTSLOTS=100
_NUMCALLALARMSLOTS=15
 # Need to check.  Is max phone will hold 32/96 or 33/97
MAXNUMBERLEN=48
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


PACKET bufferpartrequest:
    P UINT {'constant': 1024} bufpartsize
    * sanyoheader {'packettype': 0xc7} +header
    1026 UNKNOWN +pad

PACKET bufferpartupdaterequest:
    P UINT {'constant': 1024} bufpartsize
    * sanyowriteheader {'packettype': 0xc7} +header
    * DATA {'sizeinbytes': self.bufpartsize} data
    2 UNKNOWN +pad


# Phonebook sort buffer. No longer compatible with older Sanyo phones.  Will
# need new getphonebook and savephonebook methods
PACKET pbsortbuffer:
    "Various arrays for sorting the phone book, speed dial, determining which"
    # slots are in use, etc.
    # This 4000 byte buffer is formed from the concatenation of 500 bytes of
    # payload from commands 0X 3c 0F through 0X 43 0F
    P UINT {'constant': 0x0e} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 6144} bufsize
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
    391 UNKNOWN +junk

PACKET contactindexrequest:
    * sanyoheader {'packettype': 0xca,
                   'command': 0x38} +header
    2 UINT slot

PACKET contactindexupdaterequest:
    * sanyowriteheader {'packettype': 0xca,
                   'command': 0x38} +header
    2 UINT slot
    * contactindexentry +entry

PACKET numberrequest:
    * sanyoheader {'packettype': 0xca,
                   'command': 0x3f} +header
    2 UINT slot

PACKET numberupdaterequest:
    * sanyowriteheader {'packettype': 0xca,
                   'command': 0x3f} +header
    2 UINT slot
    * numberentry +entry
    
PACKET namerequest:
    * sanyoheader {'packettype': 0xca,
                   'command': 0x3c} +header
    2 UINT slot
                  
PACKET nameupdaterequest:
    * sanyowriteheader {'packettype': 0xca,
                   'command': 0x3c} +header
    2 UINT slot
    * nameentry +entry
                  
PACKET emailrequest:
    * sanyoheader {'packettype': 0xca,
                   'command': 0x43} +header
    2 UINT slot

PACKET emailupdaterequest:
    * sanyowriteheader {'packettype': 0xca,
                   'command': 0x43} +header
    2 UINT slot
    * emailentry +entry
                  
PACKET memorequest:
    * sanyoheader {'packettype': 0xca,
                   'command': 0x4e} +header
    2 UINT slot

PACKET memoupdaterequest:
    * sanyowriteheader {'packettype': 0xca,
                   'command': 0x4e} +header
    2 UINT slot
    * memoentry +entry

PACKET addressrequest:
    * sanyoheader {'packettype': 0xca,
                   'command': 0x4b} +header
    2 UINT slot
                  
PACKET addressupdaterequest:
    * sanyowriteheader {'packettype': 0xca,
                   'command': 0x4b} +header
    2 UINT slot
    * addressentry +entry

PACKET urlrequest:
    * sanyoheader {'packettype': 0xca,
                   'command': 0x48} +header
    2 UINT slot

PACKET urlupdaterequest:
    * sanyowriteheader {'packettype': 0xca,
                   'command': 0x48} +header
    2 UINT slot
    * urlentry +entry
                  
PACKET grouprequest:
    * sanyoheader {'packettype': 0xca,
                   'command': 0x37} +header
    1 UINT slot

PACKET groupupdaterequest:
    * sanyowriteheader {'packettype': 0xca,
                   'command': 0x37} +header
    1 UINT slot
    * groupentry entry
    * UNKNOWN pad

PACKET sanyoreset:
    * sanyofaheader {'faset': 0x37} +preamble
    1 UINT {'constant': 0} +command
    1 UINT {'constant': 0} +packettype


