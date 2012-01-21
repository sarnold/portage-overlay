### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sanyo8100_bell.p 3753 2006-12-07 04:03:00Z sawecw $

%{

"""Various descriptions of data specific to Sanyo SCP-8100"""

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
_NUMCALLHISTORY=20
_MAXNUMBERLEN=48
_MAXEMAILLEN=48

%}

PACKET phonenumber:
    1 UINT {'default': 0} +number_len
    49 USTRING {'default': ""} +number

PACKET phonebookentry:
    2 UINT slot
    2 UINT slotdup
    16 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} name
    * LIST {'length': 7, 'createdefault': True, 'elementclass': phonenumber} +numbers
    1 UINT +email_len
    49 USTRING {'default': ""} +email
    1 UINT +url_len
    49 USTRING {'default': ""} +url
    1 BOOL +secret
    1 UINT name_len
     
PACKET phonebookslotresponse:
    * sanyoheader header
    * phonebookentry entry
    * UNKNOWN pad

PACKET phonebookslotupdaterequest:
    * sanyowriteheader {'packettype': 0x0c, 'command': 0x28} +header
    * phonebookentry entry
    500 UNKNOWN +pad

PACKET evententry:
    1 UINT slot
    1 UINT flag "0: Not used, 1: Scheduled, 2: Already Happened"
    14 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} eventname
    7 UNKNOWN +pad1
    1 UINT eventname_len
    4 UINT start "# seconds since Jan 1, 1980 approximately"
    4 UINT end
    14 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} location
    7 UNKNOWN +pad2
    1 UINT location_len
    1 UNKNOWN +pad3
    4 UINT alarmdiff "Displayed alarm time"
    1 UINT period "No, Daily, Weekly, Monthly, Yearly"
    1 UINT dom "Day of month for the event"
    4 UINT alarm
    1 UINT {'default': 0} +serial "Some kind of serial number"
    3 UNKNOWN +pad4
    1 UINT ringtone "0: Beep, 1: Voice, 2: Silent"

PACKET eventresponse:
    * sanyoheader header
    * evententry entry
    * UNKNOWN pad

PACKET eventupdaterequest:
    * sanyowriteheader {'packettype': 0x0c, 'command':0x23} +header
    * evententry entry
    400 UNKNOWN +pad

PACKET callalarmentry:
    P UINT {'constant': 0} ringtone
    1 UINT slot
    1 UINT flag "0: Not used, 1: Scheduled, 2: Already Happened"
    1 UINT {'default': 0} +dunno1 "Related to Snooze?"
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
    1 UINT {'default': 0} +serial

PACKET callalarmresponse:
    * sanyoheader header
    * callalarmentry entry
    * UNKNOWN pad

PACKET callalarmupdaterequest:
    * sanyowriteheader {'packettype': 0x0c, 'command':0x24} +header
    * callalarmentry entry
    400 UNKNOWN +pad
