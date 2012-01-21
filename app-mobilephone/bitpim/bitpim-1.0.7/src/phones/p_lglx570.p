### BITPIM
###
### Copyright (C) 2008 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lglx570.p 4707 2008-09-04 02:05:45Z djpham $

%{

"""Various descriptions of data specific to LG LX570 (Musiq)"""

import re

from prototypes import *
from prototypeslg import *

# Make all lg stuff available in this module as well
from p_lgvx4400 import *


# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

MEMOLENGTH=33
NUMEMAILS=3
NUMPHONENUMBERS=5
NUMSPEEDDIALS=100
FIRSTSPEEDDIAL=1
LASTSPEEDDIAL=99
SPEEDDIALINDEX=0

numbertypetab=( 'cell', 'home', 'office', 'fax', 'pager', 'none' )

PB_FILENAME='DB/SysDB/vCardSchema.vol'
RT_MC_INDEX_FILENAME='setas/mcRingerIndex.map'
RT_VM_INDEX_FILENAME='setas/voicememoRingerIndex.map'
RT_MC_PATH='melodyComposer'
RT_VM_PATH='VoiceDB/All/Memos'

SMS_CANNED_MAX_ITEMS=40
SMS_CANNED_MAX_LENGTH=101
SMS_CANNED_FILENAME="sms/canned_msg.dat"
SMS_PATTERNS={'Inbox': re.compile(r"^.*/inbox[0-9][0-9][0-9]\.dat$"),
             'Sent': re.compile(r"^.*/outbox[0-9][0-9][0-9]\.dat$"),
             }

%}

# Media stuff
PACKET indexentry:
    1 UINT index
    1 UINT mediatype
    40 USTRING {'default': ""} +name

PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    # A bit of a silly design again.  Entries with an index of 0xffff are
    # 'blank'.  Thus it is possible for numactiveitems and the actual
    # number of valid entries to be mismatched.
    2 UINT numactiveitems
    * LIST {'elementclass': indexentry, 'createdefault': True} +items


# phonebook stuff

PACKET pbreadentryresponse:
    "Results of reading one entry"
    *  pbheader header
    *  pbentry  entry

PACKET pbupdateentryrequest:
    * pbheader {'command': 0x04, 'flag': 0x01} +header
    * pbentry entry

PACKET pbappendentryrequest:
    * pbheader {'command': 0x03, 'flag': 0x01} +header
    * pbentry entry

# All STRINGS have raiseonterminatedread as False since the phone does
# occassionally leave out the terminator byte'
# Note if you change the length of any of these fields, you also
# need to modify com_lgvx4400 to give a different truncateat parameter
# in the convertphonebooktophone method
# This phone model does not contain any wallpaper data
PACKET pbentry:
    4  UINT serial1
    2  UINT {'constant': 0x029E} +entrysize
    4  UINT serial2
    4  UINT entrynumber 
    73 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    2  UINT group
    1 UINT { 'default': 0 } +dunno1
    2 UINT ringtone     # for built-in "single tone" only
    2 UINT { 'default': 0 } +dunno2
    * USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'sizeinbytes': MEMOLENGTH} memo
    *  LIST {'length': NUMEMAILS} +emails:
        73 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} email
    73 USTRING {'raiseonunterminatedread': False} url
    * LIST { 'length': NUMPHONENUMBERS } +speeddials:
        1 UINT { 'default': 0xff } +speeddial
    * LIST {'length': NUMPHONENUMBERS} +numbertypes:
        1 UINT numbertype
    * LIST {'length': NUMPHONENUMBERS} +numbers:
        49 USTRING {'raiseonunterminatedread': False} number
    2 UINT { 'default': 0 } +dunno3
    P UINT { 'default': 0 } +wallpaper

PACKET pbgroup:
    "A single group"
    2 UINT header
    if self.valid:
        2 UINT blocksize
        9 DATA dunno2
        2 UINT groupid
        16 DATA dunno3
        * USTRING { 'encoding': PHONE_ENCODING,
                    'sizeinbytes': self.namesize } name
    %{
    def _getnamesize(self):
        # Return the length of the name, the size of data block must be on a
        # 4-byte word boundary
        _rem4=self.blocksize%4
        if _rem4:
            return self.blocksize+4-_rem4-27
        else:
            return self.blocksize-27
    namesize=property(fget=_getnamesize)
    def _getvalid(self):
        return self.header!=0xffff
    valid=property(fget=_getvalid)
    %}

PACKET pbgroups:
    "Phonebook groups"
    * LIST {'elementclass': pbgroup} +groups

### Text Memos
###
PACKET textmemo:
    1001 USTRING { 'encoding': PHONE_ENCODING,
                   'raiseonunterminatedread': False,
                   'raiseontruncate': False } text

PACKET textmemofile:
    4 UINT itemcount
    * LIST { 'elementclass': textmemo } +items

###
### SMS 
###
#
#   There are 3 types of SMS records, The inbox, outbox and unsent (pending)
#   Unlike other records in the phone each message is stored in a separate file
#   All messages are in the 'sms' directory in the root of the phone
#   Inbox messages are in files called 'inbox000.dat', the number 000 varies for
#   each message, typically there are no gaps in the numbering, but gaps can appear
#   if a message is deleted.
#   Outbox and draft message are named 'outbox000.dat'.
#   Messages in the outbox get updated when the message is received by the recipient,
#   they contain a delivery flag and a delivery time for all the possible 10 recipients.
#   The pm225 stores SMS in plain text (unlike some other LG phones)

PACKET recipient_record:
    8 UINT unknown1
    33 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    73 USTRING number
    1 UINT status   # 1 when sent, 2 when received
    1 UINT unknown3 
    4 LGCALDATE time # sent if status=1, received when status=2
    12 DATA unknown2

PACKET sms_out:
    4 UINT index # starting from 1, unique
    1 UINT locked # 1=locked
    3 UINT unknown1 # zero
    4 LGCALDATE timesent # time the message was sent
    2 DATA dunno1
    1 UINT saved # 0 for outbox, 1 for draft
    5 DATA dunno2
    1 UINT priority "0=normal, 1=urgent"
    15 DATA dunno2
    20 USTRING callback 
    160 USTRING {'encoding': PHONE_ENCODING} msg
    * LIST {'elementclass': recipient_record, 'length': 10} +recipients 

PACKET SMSINBOXMSGFRAGMENT:
    * LIST {'length': 181} +msg: # this size could be wrong
        1 UINT byte "individual byte of message"

PACKET sms_in:
    4 UINT unknown1 # all zeros
    4 UINT msg_index2 
    2 UINT unknown2 # set to 0 
    6 SMSDATE timesent
    3 UINT unknown
    1 UINT callback_length # 0 for no callback number
    42 USTRING callback
    1 UINT sender_length
    * LIST {'length': 38} +sender:
        1 UINT byte "individual byte of senders phone number"
    15 DATA unknown4 # set to zeros
    4 LGCALDATE lg_time # time the message was sent
    4 GPSDATE GPStime # num seconds since 0h 1-6-80, time message received by phone
    5 DATA dunno1
    1 UINT read # 1 if message has been read, 0 otherwise (kind of a guess, not enough data to be sure)
    1 UINT locked # 1 if the message is locked, 0 otherwise
    7 DATA unknown5 # these are flags, not enough data to decode
    #1 UINT priority # 1 if the message is high priority, 0 otherwise
    74 USTRING {'encoding': PHONE_ENCODING} subject 
    2 UINT msglength
    1030 USTRING {'encoding': PHONE_ENCODING} msg


PACKET sms_quick_text:
    101 USTRING {'encoding': PHONE_ENCODING,
                 'default': ""} +msg # include terminating NULL

PACKET sms_canned_file:
    2 UINT { 'default': len(self.msgs) } +num_active
    * LIST {'length': SMS_CANNED_MAX_ITEMS,
            'createdefault': True,
            'elementclass': sms_quick_text} +msgs
