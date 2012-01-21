### BITPIM
###
### Copyright (C) 2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sanyo7400.p 3352 2006-06-10 15:20:39Z skyjunky $

%{

"""Various descriptions of data specific to Sanyo MM-7400"""

from prototypes import *

# Make all sanyo stuff available in this module as well
from p_sanyo import *
from p_sanyomedia import *
from p_sanyonewer import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb
_NUMPBSLOTS=300
_NUMSPEEDDIALS=8
_NUMLONGNUMBERS=5
_LONGPHONENUMBERLEN=30
_NUMEVENTSLOTS=100
_NUMCALLALARMSLOTS=15
 # Need to check.  Is max phone will hold 32/96 or 33/97
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

PACKET eventrequest:
    * qcpheader {'packettype': 0x0c, 'command': 0x23} +header
    1 UINT slot
    129 UNKNOWN +pad

PACKET eventslotinuserequest:
    * qcpheader {'readwrite': 0x26, 'packettype': 0x0d, 'command': 0x74} +header
    1 UINT slot
    129 UNKNOWN +pad
    
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
    
PACKET eventresponse:
    * qcpheader header
    * evententry entry
    * UNKNOWN pad

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

PACKET todorequest:
    * qcpheader {'packettype': 0x0c, 'command': 0x25} +header
    1 UINT slot
    129 UNKNOWN +pad

PACKET todoentry:
    1 UINT slot
    1 UINT flag "0: Not used, 1: Used"
    14 USTRING {'raiseonunterminatedread': False} todo
    7 UNKNOWN +pad1
    1 UINT todo_len
    1 UINT priority "0: Normal, 1: Urgent, 2: Done"
    1 UINT +dunno "Maybe always zero"
    1 UINT order "Gets sorted on screen in this order"

PACKET todoresponse:
    * qcpheader header
    * todoentry entry
    * UNKNOWN pad

PACKET sanyomediafilenameresponse:
    * sanyomediaheader header
    1 UINT pad1
    154 USTRING filename
    1 UINT num1
    1 UNKNOWN pad2
    1 UINT num2
    1 UNKNOWN pad3
    1 UINT num5
    1 UNKNOWN pad4
    1 UINT num4
    1 UNKNOWN pad5
    1 UINT num3
    8 UNKNOWN pad5
