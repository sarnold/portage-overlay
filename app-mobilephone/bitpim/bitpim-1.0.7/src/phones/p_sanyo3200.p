### BITPIM
###
### Copyright (C) 2005 Stephen Wood <sawecw@users.sf.net>
### Copyright (C) 2007 Yan Ke <yke@cmu.edu>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sanyo3200.p 2766 2006-01-24 05:22:04Z yke $

%{

"""Various descriptions of data specific to Sanyo SCP-3200"""

from prototypes import *

# Make all sanyo stuff available in this module as well
from p_sanyo import *
from p_sanyomedia import *
from p_sanyonewer import *
from p_brew import *

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

#BREW_FILE_SYSTEM=2

%}

PACKET req41:
    1 UINT {'default': 0x41} +fortyone
    6 USTRING {'terminator': None} msl

PACKET res41:
    1 UINT {'default': 0x41} fortyone
    1 UINT ans


PACKET fastatusrequest:
    * sanyofaheader {'faset': 0x13} +preamble
    1 UINT {'default': 0} +command
    1 UINT {'default': 0} +packettype

PACKET fastatusresponse:
    * sanyofaheader +preamble
    1 UINT {'default': 0} status
    1 UINT {'default': 0} packettype

PACKET response:
    * UNKNOWN pad
    
PACKET {'readwrite': 0x26} qcpheader:
    1 UINT readwrite
    1 UINT command
    1 UINT packettype

PACKET {'readwrite': 0x27} qcpwriteheader:
    1 UINT readwrite
    1 UINT command
    1 UINT packettype

    * UNKNOWN pad

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
    * sanyoheader {'packettype': 0x0c,
		'command': 0x24} +header
    1 UINT slot
    501 UNKNOWN +pad

PACKET callalarmentry:
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
    3 UNKNOWN +pad2
    1 UINT ringtone

PACKET callalarmresponse:
    * sanyoheader header
    * callalarmentry entry
    417 UNKNOWN pad

PACKET callalarmupdaterequest:
    * sanyowriteheader {'packettype': 0x0c, 'command':0x24} +header
    * callalarmentry entry
    417 UNKNOWN +pad

PACKET bufferpartrequest:
    P UINT {'constant': 1024} bufpartsize
    * sanyoheader {'packettype': 0x0f} +header
    1026 UNKNOWN +pad

PACKET bufferpartresponse:
    P UINT {'constant': 1024} bufpartsize
    * sanyoheader header
    * DATA {'sizeinbytes': self.bufpartsize} data
    2 UNKNOWN pad

PACKET bufferpartupdaterequest:
    P UINT {'constant': 1024} bufpartsize
    * sanyowriteheader {'packettype': 0x0f} +header
    * DATA {'sizeinbytes': self.bufpartsize} data
    2 UNKNOWN +pad

PACKET calleridbuffer:
    "Index so that phone can show a name instead of number"
    # This 7000 byte buffer is formed from the concatenation of 500 bytes of
    # payload from commands 0X 50 0F through 0X 5D 0F
    P UINT {'constant': 500} maxentries
    P UINT {'constant': 0x46} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 7168} bufsize
    P USTRING {'default': "callerid"} +comment
    2 UINT numentries "Number phone numbers"
    * LIST {'length': self.maxentries, 'elementclass': calleridentry, 'createdefault': True} +items
    666 UNKNOWN +pad

PACKET ringerpicbuffer:
    "Index of ringer and picture assignments"
    # This 1000 byte buffer is formed from the concatenation of 500 bytes of
    # payload from commands 0X 46 0F through 0X 47 0F
    P UINT {'constant': _NUMPBSLOTS} numpbslots "Number of phone book slots"
    P UINT {'constant': 0xd7} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 0x0f} packettype "Non standard packet type"
    P UINT {'constant': 1024} bufsize
    P USTRING {'default': "ringer/picture assignments"} +comment
    * LIST {'length': _NUMPBSLOTS} +ringtones:
        1 UINT ringtone "ringtone index"
    * LIST {'length': _NUMPBSLOTS} +wallpapers:
        1 UINT wallpaper "wallpaper index"
    424 UNKNOWN +pad

#PACKET ringerpicbufferrequest:
#    "Packet to get ringer picture buffer"
#    * sanyoheader {'packettype': 0x0c, 'command': 0xd7} +header
#    1026 UNKNOWN +pad
    
#PACKET ringerpicbufferresponse:
#    * sanyoheader +header
#    * ringerpicbuffer +buffer
    
PACKET pbsortbuffer:
    "Various arrays for sorting the phone book, speed dial, determining which"
    # slots are in use, etc.
    # This 4000 byte buffer is formed from the concatenation of 500 bytes of
    # payload from commands 0X 3c 0F through 0X 43 0F
    P UINT {'constant': 0x3c} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 4096} bufsize
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
    162 UNKNOWN +pad

PACKET wallpaperbuffer:
    "Addition buffer of wallpaper assignment info"
    # 1500 byte buffer
    P UINT {'constant': _NUMPBSLOTS} numpbslots "Number of phone book slots"
    P UINT {'constant': 0x69} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 2048} bufsize
    P USTRING {'default': "wallpaper assignment info"} +comment
    * LIST {'length': _NUMPBSLOTS, 'elementclass': wallpaperinfo} +wallpapers
    548 UNKNOWN +pad

PACKET messagerequest:
    * sanyoheader {'packettype': 0x0c,
                   'command': 0xe1} +header
    1 UINT slot
    501 UNKNOWN +pad

PACKET messagesentrequest:
    * sanyoheader {'packettype': 0x0d,
                   'command': 0x55} +header
    1 UINT slot
    501 UNKNOWN +pad

PACKET messageentry:
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
    1 UINT year
    1 UINT month
    1 UINT day
    1 UINT hour
    1 UINT minute
    1 UINT second
    1 UINT callback_len
    34 USTRING callback
    1 UINT phonenum_len
    37 USTRING phonenum
    1 UINT dunno6
    1 UINT priority
    3 UNKNOWN pad6
    1 UINT dunno7
    1 UINT dunno8

PACKET messageresponse:
    * sanyoheader header
    * messageentry entry
    * UNKNOWN pad

PACKET messagesentresponse:
    * sanyoheader header
    * messageentry entry
    * UNKNOWN pad

PACKET foldernamerequest:
    * sanyoheader {'packettype': 0x0b, 'command': 0xef} +header
    1 UINT index
    501 UNKNOWN +pad

PACKET foldernameentry:
    1 UINT index
    1 UINT flag "0 if empty, 1 in use"
    1 UINT autofile "If 1, autofile messages with keyword"
    1 UINT notify
    1 UINT icon
    13 USTRING {'raiseonunterminatedread': False} name "Name of the folder"
    3 UNKNOWN +pad
    14 USTRING {'raiseonunterminatedread': False} keyword

PACKET foldernameresponse:
    * sanyoheader header
    * foldernameentry entry
    467 UNKNOWN pad

PACKET todorequest:
    * sanyoheader {'packettype': 0x0c,'command': 0x25} +header
    1 UINT slot
    501 UNKNOWN +pad

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
    * sanyoheader header
    * todoentry entry
    472 UNKNOWN pad

PACKET historyrequest:
    P UINT type "0: Outgoing, 1: Incoming, 2: Missed"
    if self.type==OUTGOING:
        * sanyoheader {'packettype': 0x0c, 'command': 0x3d} +header
    if self.type==INCOMING:
        * sanyoheader {'packettype': 0x0c, 'command': 0x3e} +header
    if self.type==MISSED:
        * sanyoheader {'packettype': 0x0c, 'command': 0x3f} +header
    1 UINT slot
    501 UNKNOWN +pad

PACKET historyentry:
    2 UINT slot
    4 GPSDATE date
    1 UINT phonenumlen
    48 USTRING {'raiseonunterminatedread': False} phonenum
    16 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} name

PACKET historyresponse:
    * sanyoheader header
    * historyentry entry
