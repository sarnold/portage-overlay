### BITPIM
###
### Copyright (C) 2006 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$

%{

"""Various descriptions of data specific to Sanyo Katana (SCP-6600)"""

from prototypes import *

# Make all sanyo stuff available in this module as well
from p_sanyo import *
from p_sanyomedia import *
from p_sanyonewer import *
from p_sanyo4930 import *

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

PACKET historyresponse:
    * sanyoheader header
    * historyentry entry
    428 UNKNOWN pad

PACKET historyentry:
    2 UINT slot
    4 GPSDATE date
    1 UINT phonenumlen
    48 USTRING {'raiseonunterminatedread': False} phonenum
    16 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} name
    1 UNKNOWN dunno2
    1 UNKNOWN dunno3

# Phonebook sort buffer. No longer compatible with older Sanyo phones.  Will
# need new getphonebook and savephonebook methods
PACKET pbsortbuffer:
    "Various arrays for sorting the phone book, speed dial, determining which"
    # slots are in use, etc.
    # This 4000 byte buffer is formed from the concatenation of 500 bytes of
    # payload from commands 0X 3c 0F through 0X 43 0F
    P UINT {'constant': 0x76} startcommand "Starting command for R/W buf parts"
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

# No group assignments in pbsortbuffer

PACKET cannedmessagerequest:
    * sanyoheader {'packettype': 0x0e,
                   'command': 0x5b} +header

PACKET pbinfo:
    2 UINT {'constant': 0x00fa} +fa
    1 UINT {'default': 0x02} +faset
    #1 UINT command
    1 UINT byte1
    1 UINT byte2
    2 UINT byte3

PACKET contactindexrequest:
    * sanyoheader {'packettype': 0x16,
                   'command': 0x88} +header
    2 UINT slot

# Pointers to the name, phone numbers, memo, emails, url, address
# One name, 7 phone numbers, 2 email, 1 url, one group, 1 ringer, 1 address
# 1 memo, 1 picture
PACKET contactindexentry:
    1 UINT groupid
    2 UINT slot
    2 UINT {'default': 0xffff} +namep
    * LIST {'length': NUMPHONENUMBERS} +numberps:
        2 UINT {'default': 0xffff} slot
    * LIST {'length': NUMEMAILS} +emailps:
        2 UINT {'default': 0xffff} slot
    2 UINT {'default': 0xffff} +urlp
    2 UINT {'default': 0xffff} +addressp
    2 UINT {'default': 0xffff} +memop
    2 UINT {'default': 0xfff0} +ringerid
    2 UINT {'default': 0xfffe} +pictureid
    2 UINT {'default': 0} +defaultnum
    1 UINT {'default': 0} +secret
    
PACKET contactindexresponse:
    * sanyoheader header
    2 UINT slot
    * contactindexentry entry
    * UNKNOWN pad

PACKET contactindexupdaterequest:
    * sanyowriteheader {'packettype': 0x16,
                   'command': 0x88} +header
    2 UINT slot
    * contactindexentry +entry
    
PACKET numberrequest:
    * sanyoheader {'packettype': 0x16,
                   'command': 0x8f} +header
    2 UINT slot

PACKET numberentry:
    2 UINT contactp "Pointer to contact number belongs"
    1 UINT numberlen
    48 USTRING {'default': "", 'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} +number
    1 UNKNOWN +pad
    1 UINT numbertype
    
PACKET numberresponse:
    * sanyoheader header
    2 UINT slot
    * numberentry entry
    * UNKNOWN pad

PACKET numberupdaterequest:
    * sanyowriteheader {'packettype': 0x16,
                   'command': 0x8f} +header
    2 UINT slot
    * numberentry +entry
    
PACKET namerequest:
    * sanyoheader {'packettype': 0x16,
                   'command': 0x8c} +header
    2 UINT slot
                  
PACKET nameentry:
    2 UINT contactp
    1 UINT name_len
    1 UINT name_len2
    32 USTRING {'default': "", 'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} name

PACKET nameresponse:
    * sanyoheader header
    2 UINT slot
    * nameentry entry
    * UNKNOWN pad
                  
PACKET nameupdaterequest:
    * sanyowriteheader {'packettype': 0x16,
                   'command': 0x8c} +header
    2 UINT slot
    * nameentry +entry
                  
PACKET urlrequest:
    * sanyoheader {'packettype': 0x16,
                   'command': 0x98} +header
    2 UINT slot

PACKET urlentry:
    2 UINT contactp "Pointer to contact number belongs"
    1 UINT url_len
    96 USTRING {'default': "", 'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} +url
    1 UNKNOWN +pad
    1 UINT {'default': 9} +type "Always 9 for World Icon"

PACKET urlresponse:
    * sanyoheader header
    2 UINT slot
    * urlentry entry
    * UNKNOWN pad

PACKET urlupdaterequest:
    * sanyowriteheader {'packettype': 0x16,
                   'command': 0x98} +header
    2 UINT slot
    * urlentry +entry
                  
PACKET addressrequest:
    * sanyoheader {'packettype': 0x16,
                   'command': 0x9b} +header
    2 UINT slot
                  
PACKET addressentry:
    2 UINT contactp "Pointer to contact number belongs"
    2 UINT address_len
    256 USTRING {'default': "", 'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} +address

PACKET addressresponse:
    * sanyoheader header
    2 UINT slot
    * addressentry entry
    * UNKNOWN pad
                  
PACKET addressupdaterequest:
    * sanyowriteheader {'packettype': 0x16,
                   'command': 0x9b} +header
    2 UINT slot
    * addressentry +entry

PACKET memorequest:
    * sanyoheader {'packettype': 0x16,
                   'command': 0x9e} +header
    2 UINT slot

PACKET memoentry:
    2 UINT contactp "Pointer to contact number belongs"
    2 UINT memo_len
    256 USTRING {'default': "", 'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} +memo

PACKET memoresponse:
    * sanyoheader header
    2 UINT slot
    * memoentry entry
    * UNKNOWN pad

PACKET memoupdaterequest:
    * sanyowriteheader {'packettype': 0x16,
                   'command': 0x9e} +header
    2 UINT slot
    * memoentry +entry

PACKET emailrequest:
    * sanyoheader {'packettype': 0x16,
                   'command': 0x93} +header
    2 UINT slot

PACKET emailentry:
    2 UINT contactp "Pointer to contact number belongs"
    1 UINT email_len
    96 USTRING {'default': "", 'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} +email
    1 UNKNOWN +pad
    1 UINT {'default': 8} +type "7: Mobile, 8: Internet"
    
PACKET emailresponse:
    * sanyoheader header
    2 UINT slot
    * emailentry entry

PACKET emailupdaterequest:
    * sanyowriteheader {'packettype': 0x16,
                   'command': 0x93} +header
    2 UINT slot
    * emailentry +entry
                  
PACKET grouprequest:
    * sanyoheader {'packettype': 0x16,
                   'command': 0x87} +header
    1 UINT slot

PACKET groupentry:
    1 UINT slot
    1 UINT groupname_len
    16 USTRING {'default': ""} +groupname
    2 UINT {'default': 0xfff0} +ringer
    2 UINT {'default': 0xfffe} +picture
    

PACKET groupresponse:
    * sanyoheader header
    1 UINT slot
    * groupentry entry
    * UNKNOWN pad

PACKET groupupdaterequest:
    * sanyowriteheader {'packettype': 0x16,
                   'command': 0x87} +header
    1 UINT slot
    * groupentry entry
    * UNKNOWN pad

PACKET evententry:
    P UINT {'default': 0xffffffff} +alarm
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
    4 UINT {'default': 0} +timestamp
    1 UNKNOWN +pad3
    1 UINT {'default': 0} +serial "Some kind of serial number"
    3 UNKNOWN +pad4
    2 UINT ringtone

PACKET eventresponse:
    * qcpheader header
    * evententry entry
    * UNKNOWN pad
    
PACKET eventupdaterequest:
    * qcpwriteheader {'packettype': 0x0c, 'command':0x23} +header
    * evententry entry
    56 UNKNOWN +pad

PACKET messagesententry:
    1 UINT slot
    1 UINT read
    1 UINT counter
    3 UNKNOWN pad1
    1 UINT dunno1
    1 UINT dunno2
    1 UINT dunno3
    1 UNKNOWN pad2
    1 UINT dunno4
    1 UINT dunno5
    1 UNKNOWN pad3
    1 UINT message_len
    255 USTRING message "Text of the notification"
    1 UNKNOWN pad4
    1 UINT pad5
    1 UINT year
    1 UINT month
    1 UINT day
    1 UINT hour
    1 UINT minute
    1 UINT second
    1 UINT callback_len
    34 USTRING callback
    1 UINT phonenum_len
    36 USTRING phonenum
    1 UINT dunno6
    1 UINT priority
    3 UNKNOWN pad6
    1 UINT dunno7
    1 UINT dunno8

PACKET messagesentresponse:
    * sanyoheader header
    * messagesententry entry
    * UNKNOWN pad

