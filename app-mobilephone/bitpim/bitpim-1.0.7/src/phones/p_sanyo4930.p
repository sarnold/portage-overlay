### BITPIM
###
### Copyright (C) 2005 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sanyo4930.p 4075 2007-03-03 04:55:07Z sawecw $

%{

"""Various descriptions of data specific to Sanyo RL-4930"""

from prototypes import *

# Make all sanyo stuff available in this module as well
from p_sanyo import *
from p_sanyomedia import *
from p_sanyonewer import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb
_NUMPBSLOTS=500
_NUMSPEEDDIALS=8
_NUMLONGNUMBERS=5
_LONGPHONENUMBERLEN=30
_NUMEVENTSLOTS=100
_NUMCALLALARMSLOTS=15
_NUMCALLHISTORY=20
_MAXNUMBERLEN=32
_MAXEMAILLEN=96
HASRINGPICBUF=0
 
%}

PACKET {'readwrite': 0x26} qcpheader:
    1 UINT readwrite
    1 UINT command
    1 UINT packettype

PACKET {'readwrite': 0x27} qcpwriteheader:
    1 UINT readwrite
    1 UINT command
    1 UINT packettype

# How can I override bufsize without repeating the whole thing?
PACKET pbsortbuffer:
    "Various arrays for sorting the phone book, speed dial, determining which"
    # slots are in use, etc.
    # This 7168 byte buffer is formed from the concatenation of 1024 bytes of
    # payload from commands 0X 3c 0F through 0X 43 0F
    P UINT {'constant': 0x3c} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 7168} bufsize
    P USTRING {'default': "sort buffer"} +comment
    * LIST {'length': _NUMPBSLOTS, 'createdefault': True} +usedflags:
        1 UINT used "1 if slot in use"
    2 UINT slotsused
    2 UINT slotsused2  "Always seems to be the same.  Why duplicated?"
    2 UINT numemail "Num of slots with email"
    2 UINT numurl "Num of slots with URL"
    * LIST {'length': _NUMPBSLOTS} +firsttypes:
        1 UINT firsttype "First phone number type in each slot"
    * LIST {'length': _NUMPBSLOTS} +sortorder:
        2 UINT {'default': 0xffff} pbslot
    * USTRING {'terminator': None, 'sizeinbytes': _NUMPBSLOTS} pbfirstletters
    * LIST {'length': _NUMPBSLOTS} +sortorder2: "Is this the same"
        2 UINT {'default': 0xffff} pbslot
    * LIST {'length': _NUMSPEEDDIALS} +speeddialindex:
        2 UINT {'default': 0xffff} pbslotandtype
    * LIST {'length': _NUMLONGNUMBERS} +longnumbersindex:
        2 UINT {'default': 0xffff} pbslotandtype
    * LIST {'length': _NUMPBSLOTS} +emails: "Sorted list of slots with Email"
        2 UINT {'default': 0xffff} pbslot
    * USTRING {'terminator': None, 'sizeinbytes': _NUMPBSLOTS} emailfirstletters "First letters in sort order"
    * LIST {'length': _NUMPBSLOTS} +urls: "Sorted list of slots with a URL"
        2 UINT {'default': 0xffff} pbslot
    * USTRING {'terminator': None, 'sizeinbytes': _NUMPBSLOTS} urlfirstletters "First letters in sort order"
    * UNKNOWN +pad

PACKET calleridbuffer:
    "Index so that phone can show a name instead of number"
    # This 7000 byte buffer is formed from the concatenation of 500 bytes of
    # payload from commands 0X 50 0F through 0X 5D 0F
    P UINT {'constant': 700} maxentries
    P UINT {'constant': 0x46} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 9216} bufsize
    P USTRING {'default': "callerid"} +comment
    2 UINT numentries "Number phone numbers"
    * LIST {'length': self.maxentries, 'elementclass': calleridentry, 'createdefault': True} +items
    * UNKNOWN +pad

PACKET evententry:
    1 UINT slot
    14 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} eventname
    7 UNKNOWN +pad1
    1 UINT eventname_len
    4 UINT start "# seconds since Jan 1, 1980 approximately"
    4 UINT end
    14 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} location
    7 UNKNOWN +pad2
    1 UINT location_len
    4 UINT alarmdiff "Displayed alarm time"
    1 UINT period "No, Daily, Weekly, Monthly, Yearly"
    1 UINT dom "Day of month for the event"
    4 UINT alarm
    1 UNKNOWN +pad3
    1 UINT {'default': 0} +serial "Some kind of serial number"
    3 UNKNOWN +pad4
    2 UINT ringtone
    
PACKET eventrequest:
    * qcpheader {'packettype': 0x0c, 'command': 0x23} +header
    1 UINT slot
    129 UNKNOWN +pad

PACKET eventresponse:
    * qcpheader header
    * evententry entry
    * UNKNOWN pad

PACKET eventslotinuserequest:
    * qcpheader {'readwrite': 0x26, 'packettype': 0x0d, 'command': 0x74} +header
    1 UINT slot
    129 UNKNOWN +pad
    
PACKET eventslotinuseresponse:
    * qcpheader header
    1 UINT slot
    1 UINT flag
    * UNKNOWN pad

PACKET eventslotinuseupdaterequest:
    * qcpwriteheader {'packettype': 0x0d, 'command': 0x74} +header
    1 UINT slot
    1 UINT flag
    124 UNKNOWN +pad
    
PACKET eventupdaterequest:
    * qcpwriteheader {'packettype': 0x0c, 'command':0x23} +header
    * evententry entry
    56 UNKNOWN +pad

PACKET callalarmrequest:
    * qcpheader {'packettype': 0x0c, 'command': 0x24} +header
    1 UINT slot
    129 UNKNOWN +pad

PACKET callalarmresponse:
    * qcpheader header
    * callalarmentry entry
    * UNKNOWN pad

PACKET callalarmupdaterequest:
    * qcpwriteheader {'packettype': 0x0c, 'command':0x24} +header
    * callalarmentry entry
    40 UNKNOWN +pad

PACKET callalarmslotinuserequest:
    * qcpheader {'packettype': 0x0d, 'command': 0x76} +header
    1 UINT slot
    129 UNKNOWN +pad

PACKET callalarmslotinuseresponse:
    * qcpheader header
    1 UINT slot
    1 UINT flag
    * UNKNOWN pad

PACKET callalarmentry:
    1 UINT slot
    1 UNKNOWN +pad0 "Not the flag?"
    49 USTRING {'raiseonunterminatedread': False} phonenum
    1 UINT phonenum_len
    4 UINT date "# seconds since Jan 1, 1980 approximately"
    1 UINT period "No, Daily, Weekly, Monthly, Yearly"
    1 UINT dom "Day of month for the event"
    4 UINT datedup "Copy of the date.  Always the same???"
    16 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} name
    1 UNKNOWN +pad1
    1 UINT name_len
    1 UINT phonenumbertype "1: Home, 2: Work, ..." 
    2 UINT phonenumberslot
    1 UNKNOWN +pad2
    1 UINT {'default': 0} +serial
    2 UNKNOWN +pad3
    1 UINT {'default': 0xfc} +ringtone
    1 UNKNOWN +pad4 " This may be the ringtone.  Need to understand "
    1 UINT +flag

