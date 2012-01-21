### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sanyo.p 4618 2008-06-19 03:55:00Z sawecw $

%{

"""Various descriptions of data specific to Sanyo phones"""

from prototypes import *
from prototypeslg import *

# We use LSB for all integer like fields

UINT=UINTlsb
BOOL=BOOLlsb
_NUMPBSLOTS=300
_NUMSPEEDDIALS=8
_NUMLONGNUMBERS=5
_LONGPHONENUMBERLEN=30
_NUMEVENTSLOTS=100
_NUMCALLALARMSLOTS=15
NUMCALLHISTORY=20
NUMPHONENUMBERS=7
NUMMESSAGESLOTS=128
NUMTODOSLOTS=20
HASRINGPICBUF=1
FIRSTSPEEDDIAL=2
LASTSPEEDDIAL=9

OUTGOING=0
INCOMING=1
MISSED=2

 %}

PACKET sanyoerror:
    1 UINT errorcode
    * UNKNOWN unknown

PACKET firmwarerequest:
    1 UINT {'constant': 0x00} +command

PACKET firmwareresponse:
    1 UINT command
    * UNKNOWN unknown
#    11 USTRING {'terminator': None}  date1
#    8 USTRING {'terminator': None}  time1
#    11 USTRING {'terminator': None}  date2
#    8 USTRING {'terminator': None}  time2
#    8 USTRING {'terminator': None}  string1
#    1 UNKNOWN dunno1
#    11 USTRING {'terminator': None}  date3
#    1 UNKNOWN dunno2
#    8 USTRING {'terminator': None}  time3
#    11 UNKNOWN dunno3
#    10 USTRING {'terminator': None}  firmware
#    7 UNKNOWN dunno4
#    16 USTRING {'terminator': None}  phonemodel
#    5 USTRING {'terminator': None}  prl

PACKET beginendupdaterequest:
    1 UINT {'constant': 0x29} +command
    2 UINT beginend

PACKET beginendupdateresponse:
    1 UINT command
    2 UINT beginend

PACKET statusrequest:
    1 UINT {'constant': 0x0c} +command

PACKET statusresponse:
    P UINT {'constant': 0x0} readyvalue
    1 UINT command
    3 UNKNOWN dunno1
    4 UINT esn
    1 UINT flag0
    14 UNKNOWN dunno2
    1 UINT ready
    1 UINT dunno3
    1 UINT flag2
    6 UNKNOWN dunno4
    1 UINT flag3
    * UNKNOWN unknown
    
PACKET lockcoderequest:
    1 UINT {'constant': 0x26} +command1
    2 UINT {'constant': 0x52} +command2
    130 UNKNOWN +pad
    
PACKET lockcoderesponse:
    1 UINT {'constant': 0x26} +command1
    2 UINT {'constant': 0x52} +command2
    4 USTRING {'raiseonunterminatedread': False} lockcode
    * UNKNOWN pad

PACKET sanyofirmwarerequest:
    1 UINT {'constant': 0x00} +command

PACKET sanyofirmwareresponse:
    1 UINT command
    11 USTRING {'terminator': None} date1
    8 USTRING {'terminator': None} time1
    11 USTRING {'terminator': None} date2
    8 USTRING {'terminator': None} time2
    8 USTRING {'terminator': None} string1
    1 UNKNOWN dunno1
    11 USTRING {'terminator': None} date3
    1 UNKNOWN dunno2
    8 USTRING {'terminator': None} time3
    11 UNKNOWN dunno3
    10 USTRING {'terminator': None} firmware
    7 UNKNOWN pad
    16 USTRING {'terminator': None} phonemodel
    5 USTRING {'terminator': None} prl

PACKET reconditionedrequest:
    1 UINT {'constant': 0x26} +command1
    2 UINT {'constant': 0x0c1b} +command2
    130 UNKNOWN +pad
    
PACKET reconditionedresponse:
    1 UINT {'constant': 0x26} command1
    2 UINT {'constant': 0x0c1b} command2
    1 UINT reconditioned
    * UNKNOWN pad

PACKET phonenumberrequest:
    1 UINT {'constant': 0x26} +command1
    1 UINT {'constant': 0xb2} +command2
    1 UINT {'constant': 0} +zero
    130 UNKNOWN +pad

PACKET phonenumberresponse:
    1 UINT {'constant': 0x26} command1
    1 UINT {'constant': 0xb2} command2
    2 UNKNOWN pad1
    10 USTRING {'raiseonunterminatedread': False}  myphonenumber
    119 UNKNOWN pad2

PACKET {'readwrite': 0x0d} sanyoheader:
    1 UINT readwrite
    1 UINT command
    1 UINT packettype

PACKET esnrequest:
    1 UINT {'constant': 0x01} +command

PACKET esnresponse:
    1 UINT {'constant': 0x01} command
    4 UINT esn

PACKET ownerinforequest:
    * sanyoheader {'packettype': 0x0c,
		'command': 0x3b} +header
    502 UNKNOWN +pad

PACKET ownerentry:
    16 USTRING {'raiseonunterminatedread': False} ownername
    2 UINT birthyear
    1 UINT birthmonth
    1 UINT birthday
    1 UINT bloodtype "0: ?, 1: A, 2: B, 3: O, 4: AB"
    96 USTRING {'raiseonunterminatedread': False} address
    14 UNKNOWN +pad
    48 USTRING {'raiseonunterminatedread': False} homeemail
    48 USTRING {'raiseonunterminatedread': False} workemail
    48 USTRING {'raiseonunterminatedread': False} homephone
    48 USTRING {'raiseonunterminatedread': False} workphone
    
PACKET ownerinforesponse:
    * sanyoheader header
    * ownerentry entry
    178 UNKNOWN pad
    
PACKET eventrequest:
    * sanyoheader {'packettype': 0x0c,
		'command': 0x23} +header
    1 UINT slot
    501 UNKNOWN +pad

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
    1 UINT ringtone "0: Beep, 1: Voice, 2: Silent"
    4 UINT alarmdiff "Displayed alarm time"
    1 UINT period "No, Daily, Weekly, Monthly, Yearly"
    1 UINT dom "Day of month for the event"
    4 UINT alarm
    1 UINT {'default': 0} +serial "Some kind of serial number"

PACKET eventresponse:
    * sanyoheader header
    * evententry entry
    436 UNKNOWN pad

PACKET eventupdaterequest:
    * sanyoheader {'readwrite': 0x0e,
                   'packettype': 0x0c, 'command':0x23} +header
    * evententry entry
    436 UNKNOWN +pad
        
PACKET callalarmrequest:
    * sanyoheader {'packettype': 0x0c,
		'command': 0x24} +header
    1 UINT slot
    501 UNKNOWN +pad

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
    417 UNKNOWN pad

PACKET callalarmupdaterequest:
    * sanyoheader {'readwrite': 0x0e,
                   'packettype': 0x0c, 'command':0x24} +header
    * callalarmentry entry
    417 UNKNOWN +pad

PACKET todorequest:
    * sanyoheader {'packettype': 0x0c,
		'command': 0x25} +header
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

PACKET holidaybitsrequest:
    * UNKNOWN unknown

PACKET holidaybitsresponse:
    * UNKNOWN unknown

PACKET weeklyholidaybitsrequest:
    * UNKNOWN unknown

PACKET weeklyholidaybitsresponse:
    * UNKNOWN unknown

PACKET foldernamerequest:
    * sanyoheader {'packettype': 0x0b,
                   'command': 0xef} +header
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

PACKET messagerequest:
    * sanyoheader {'packettype': 0x0c,
                   'command': 0xe1} +header
    1 UINT slot
    501 UNKNOWN +pad

PACKET messageentry:
    1 UINT slot
    1 UINT messagetype
    1 UINT dunno1
    1 UINT dunno2
    1 UINT dunno3
    1 UINT dunno4
    1 UINT dunno5
    1 UINT dunno6
    1 UINT dunno7
    1 UINT dunno8
    1 UINT dunno9
    1 UINT dunno10
    1 UINT dunno11
    1 UINT message_len
    255 USTRING message "Text of the notification"
    1 UNKNOWN pad1
    1 UINT year
    1 UINT month
    1 UINT day
    1 UINT hour
    1 UINT minute
    1 UINT second
    1 UINT phonenum_len
    33 USTRING phonenum
    1 UINT dunno12
    38 UNKNOWN pad2
    1 UINT dunno13
    1 UINT folder
    
PACKET messageresponse:
    * sanyoheader header
    * messageentry entry
    151 UNKNOWN pad

# Call History
# 0x3d Outgoing
# 0x3e Incoming
# 0x3f Missed

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

# Call History
# 0x60 Outgoing
# 0x61 Incoming
# 0x62 Missed

PACKET historymiscrequest:
    P UINT type "0: Outgoing, 1: Incoming, 2: Missed"
    if self.type==OUTGOING:
        * sanyoheader {'packettype': 0x0c, 'command': 0x60} +header
    if self.type==INCOMING:
        * sanyoheader {'packettype': 0x0c, 'command': 0x61} +header
    if self.type==MISSED:
        * sanyoheader {'packettype': 0x0c, 'command': 0x62} +header
    1 UINT slot
    501 UNKNOWN +pad

PACKET historyentry:
    2 UINT slot
    1 UNKNOWN dunno1
    4 GPSDATE date
    1 UINT phonenumlen
    48 USTRING {'raiseonunterminatedread': False} phonenum
    16 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False, 'terminator': None} name
    1 UNKNOWN dunno2
    1 UNKNOWN dunno3

PACKET historyresponse:
    * sanyoheader header
    * historyentry entry
    428 UNKNOWN pad

PACKET historymiscentry:
    2 UINT slot
    2 UINT pbslotandtype
    2 UINT dunno1
    1 UINT dunno2
    1 UINT dunno3
    1 UINT dunno4

PACKET historymiscresponse:
    * sanyoheader header
    * historymiscentry entry
    493 UNKNOWN pad

PACKET bufferpartrequest:
    P UINT {'constant': 500} bufpartsize
    * sanyoheader {'packettype': 0x0f} +header
    502 UNKNOWN +pad

PACKET bufferpartresponse:
    P UINT {'constant': 500} bufpartsize
    * sanyoheader header
    * DATA {'sizeinbytes': self.bufpartsize} data
    2 UNKNOWN pad

PACKET bufferpartupdaterequest:
    P UINT {'constant': 500} bufpartsize
    * sanyoheader {'readwrite': 0x0e, 'packettype': 0x0f} +header
    * DATA {'sizeinbytes': self.bufpartsize} data
    2 UNKNOWN +pad
        
PACKET phonebookslotrequest:
    * sanyoheader {'packettype': 0x0c,
                   'command': 0x28} +header
    2 UINT slot
    500 UNKNOWN +pad

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
    30 UNKNOWN pad

PACKET phonebookslotupdaterequest:
    * sanyoheader {'packettype': 0x0c, 'readwrite': 0x0e,
                   'command': 0x28} +header
    * phonebookentry entry
    30 UNKNOWN +pad

PACKET voicedialrequest:
    * sanyoheader {'packettype': 0x0b,
                   'command': 0xed} +header
    1 UINT slot
    501 UNKNOWN +pad

PACKET voicedialentry:
    1 UINT slot
    1 UINT flag "1 if voice dial slot in use"
    2 UNKNOWN pad1
    2 UINT phonenumberslot
    1 UINT phonenumbertype "1: Home, 2: Work, ..." 

PACKET voicedialresponse:
    * sanyoheader header
    * voicedialentry entry
    495 UNKNOWN pad2

PACKET t9request:
    * UNKNOWN unknown

PACKET t9response:
    * UNKNOWN unknown

PACKET calleridentry:
    2 UINT {'default': 0xffff} +pbslotandtype "Low 12 bits, slotnum, top 4 bits, type"
    1 UINT {'default': 0} +actualnumberlen "Length of the actual phone number"
    10 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': "", 'terminator': None} +numberfragment

PACKET calleridbuffer:
    "Index so that phone can show a name instead of number"
    # This 7000 byte buffer is formed from the concatenation of 500 bytes of
    # payload from commands 0X 50 0F through 0X 5D 0F
    P UINT {'constant': 500} maxentries
    P UINT {'constant': 0x50} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 7000} bufsize
    P USTRING {'default': "callerid"} +comment
    2 UINT numentries "Number phone numbers"
    * LIST {'length': self.maxentries, 'elementclass': calleridentry, 'createdefault': True} +items
    498 UNKNOWN +pad

PACKET ringerpicbuffer:
    "Index of ringer and picture assignments"
    # This 1000 byte buffer is formed from the concatenation of 500 bytes of
    # payload from commands 0X 46 0F through 0X 47 0F
    P UINT {'constant': _NUMPBSLOTS} numpbslots "Number of phone book slots"
    P UINT {'constant': 0x46} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 1000} bufsize
    P USTRING {'default': "ringer/picture assignments"} +comment
    * LIST {'length': _NUMPBSLOTS} +ringtones:
        1 UINT ringtone "ringtone index"
    * LIST {'length': _NUMPBSLOTS} +wallpapers:
        1 UINT wallpaper "wallpaper index"
    400 UNKNOWN +pad

PACKET wallpaperbuffer:
    "Addition buffer of wallpaper assignment info"
    # 1500 byte buffer
    P UINT {'constant': _NUMPBSLOTS} numpbslots "Number of phone book slots"
    P UINT {'constant': 0x69} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 1500} bufsize
    P USTRING {'default': "wallpaper assignment info"} +comment
    * LIST {'length': _NUMPBSLOTS, 'elementclass': wallpaperinfo} +wallpapers
    
PACKET wallpaperinfo:
    "5 byte structure with info about wallpaper assignments"
    1 UINT flag
    2 UINT word1
    2 UINT word2
    
PACKET pbsortbuffer:
    "Various arrays for sorting the phone book, speed dial, determining which"
    # slots are in use, etc.
    # This 4000 byte buffer is formed from the concatenation of 500 bytes of
    # payload from commands 0X 3c 0F through 0X 43 0F
    P UINT {'constant': 0x3c} startcommand "Starting command for R/W buf parts"
    P UINT {'constant': 4000} bufsize
    P USTRING {'default': "sort buffer"} +comment
    * LIST {'length': _NUMPBSLOTS, 'createdefault': True} +usedflags:
        1 UINT used "1 if slot in use"
    2 UINT slotsused
    2 UINT slotsused2  "# slots containing a phone number"
    2 UINT numemail "Num of slots with email"
    2 UINT numurl "Num of slots with URL"
    * LIST {'length': _NUMPBSLOTS} +firsttypes:
        1 UINT firsttype "First phone number type in each slot"
    * LIST {'length': _NUMPBSLOTS} +sortorder:
        2 UINT {'default': 0xffff} pbslot
    * USTRING {'terminator': None, 'sizeinbytes': _NUMPBSLOTS} pbfirstletters
    * LIST {'length': _NUMPBSLOTS} +sortorder2: "Sort order for entries with phone numbers"
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
    66 UNKNOWN +pad

PACKET sanyomediaheader:
    2 UINT {'constant': 0xfa} +fa
    1 UINT {'default': 0x05} +faset
    2 UINT command
    2 UNKNOWN +pad

PACKET sanyosendfilename:
    * sanyomediaheader {'command': 0xffa1} +header
    1 UINT {'constant': 0x20} +payloadsize
    32 USTRING {'default': ""} +filename

PACKET sanyosendfilesize:
    * sanyomediaheader {'command': 0xffc1} +header
    1 UINT {'constant': 0x20} +payloadsize
    1 UNKNOWN +pad1
    2 UINT filesize
    29 UNKNOWN +pad2 

PACKET sanyosendfilefragment:
    * sanyomediaheader +header
    1 UINT {'constant': 0x20} +payloadsize
    32 DATA data

PACKET sanyosendfileterminator:
    * sanyomediaheader {'command': 0xffe1} +header
    1 UINT {'constant': 0x20} +payloadsize
    32 UNKNOWN +pad

PACKET sanyosendfileresponse:
    * sanyomediaheader +header
    1 UINT payloadsize
    32 UNKNOWN pad

PACKET study:
    * sanyoheader +header
    2 UINT slot
    500 UNKNOWN +pad

PACKET studyresponse:
    * sanyoheader header
    * UNKNOWN data
