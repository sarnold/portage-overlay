### BITPIM
###
### Copyright (C) 2006 Simon Capper <skyjunky@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

%{

"""Various descriptions of data specific to LG 6190 (Sprint)"""

import re

from prototypes import *
from prototypeslg import *

# Make all lg stuff available in this module as well
from p_lg import *

# we are the same as lgvx4400 except as noted
# below
from p_lgvx4400 import *


# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

NUMSPEEDDIALS=100
FIRSTSPEEDDIAL=1
LASTSPEEDDIAL=99
NUMPHONEBOOKENTRIES=500
MEMOLENGTH=65

NORINGTONE=0
NOMSGRINGTONE=0
NOWALLPAPER=0

NUMEMAILS=3
NUMPHONENUMBERS=5

SMS_CANNED_MAX_ITEMS=18
SMS_CANNED_MAX_LENGTH=101
SMS_CANNED_FILENAME="sms/mediacan000.dat"
SMS_PATTERNS={'Inbox': re.compile(r"^.*/inbox[0-9][0-9][0-9]\.dat$"),
             'Sent': re.compile(r"^.*/outbox[0-9][0-9][0-9]\.dat$"),
             'Saved': re.compile(r"^.*/sf[0-9][0-9]\.dat$"),
             }

# Text Memo const
text_memo_file='sch/memo.dat'
content_file_name='ams/contentInfo'
content_count_file_name='ams/realContent'

media_directory='ams'
ringerindex='setas/amsRingerIndex.map'
imageindex='setas/amsImageIndex.map'
ringerconst=2
imageconst=3
max_ringers=100
max_images=100

phonebook_media='pim/pbookcontact.dat'

# Calendar parameters
NUMCALENDARENTRIES=300  # ?? for VX4400
CAL_REP_NONE=0x10
CAL_REP_DAILY=0x11
CAL_REP_MONFRI=0x12
CAL_REP_WEEKLY=0x13
CAL_REP_MONTHLY=0x14
CAL_REP_YEARLY=0x15
CAL_DOW_SUN=0x0800
CAL_DOW_MON=0x0400
CAL_DOW_TUE=0x0200
CAL_DOW_WED=0x0100
CAL_DOW_THU=0x0080
CAL_DOW_FRI=0x0040
CAL_DOW_SAT=0x0020
CAL_DOW_EXCEPTIONS=0x0010
CAL_REMINDER_NONE=0
CAL_REMINDER_ONTIME=1
CAL_REMINDER_5MIN=2
CAL_REMINDER_10MIN=3
CAL_REMINDER_1HOUR=4
CAL_REMINDER_1DAY=5
CAL_REMINDER_2DAYS=6
CAL_NO_VOICE=0xffff
CAL_REPEAT_DATE=(2999, 12, 31)

cal_has_voice_id=True
cal_voice_id_ofs=0x11
cal_voice_ext='.qcp'      # full name='sche000.qcp'

cal_dir='sch'
cal_data_file_name='sch/schedule.dat'
cal_exception_file_name='sch/schexception.dat'

PHONE_ENCODING='iso8859_1'

%}

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

PACKET speeddial:
    2 UINT {'default': 0xffff} +entry
    1 UINT {'default': 0xff} +number

PACKET speeddials:
    * LIST {'length': NUMSPEEDDIALS, 'elementclass': speeddial} +speeddials

# All STRINGS have raiseonterminatedread as False since the phone does
# occassionally leave out the terminator byte
# Note if you change the length of any of these fields, you also
# need to modify com_lg6190 to give a different truncateat parameter
# in the convertphonebooktophone method
PACKET pbentry:
    4  UINT serial1
    2  UINT {'constant': 0x0222}  +entrysize
    4  UINT serial2
    2  UINT entrynumber 
    23 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    2  UINT group
    *  LIST {'length': NUMEMAILS} +emails:
        49 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} email
    49 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} url
    1  UINT ringtone                                     "ringtone index for a call"
    1  UINT msgringtone                                  "ringtone index for a text message"
    1  BOOL secret
    *  USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'sizeinbytes': MEMOLENGTH} memo
    1  UINT wallpaper
    * LIST {'length': NUMPHONENUMBERS} +numbertypes:
        1 UINT numbertype
    * LIST {'length': NUMPHONENUMBERS} +numbers:
        49 USTRING {'raiseonunterminatedread': False} number
    * UNKNOWN +unknown20c


PACKET pbgroup:
    "A single group"
    1 UINT icon
    23 USTRING {'encoding': PHONE_ENCODING} name

PACKET pbgroups:
    "Phonebook groups"
    * LIST {'elementclass': pbgroup} +groups

PACKET call:
    4 GPSDATE GPStime #no. of seconds since 0h 1-6-80, based off local time.
    4 UINT unknown1 # different for each call
    4 UINT duration #seconds, not certain about length of this field
    49 USTRING {'raiseonunterminatedread': False} number
    36 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    1 UINT numberlength # length of phone number
    1 UINT unknown2 # set to 1 on some calls
    1 UINT pbnumbertype # 1=cell, 2=home, 3=office, 4=cell2, 5=fax, 6=vmail, 0xFF=not in phone book
    2 UINT unknown3 # always seems to be 0
    2 UINT pbentrynum #entry number in phonebook

PACKET callhistory:
    4 UINT numcalls
    1 UINT unknown1
    * LIST {'elementclass': call} +calls

###
### Media indexes
###

PACKET indexentry:
    2 UINT {'default': 0xffff} +index
    50 USTRING {'default': ""} +name

PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    # A bit of a silly design again.  Entries with an index of 0xffff are
    # 'blank'.  Thus it is possible for numactiveitems and the actual
    # number of valid entries to be mismatched.
    P UINT {'constant': 30} maxitems
    2 UINT numactiveitems
    * LIST {'length': self.maxitems, 'elementclass': indexentry, 'createdefault': True} +items

PACKET camindexentry:
    1 UINT index
    1 UINT {'default' : 80} +unknown1
    10 USTRING {'default': ""} +name
    4 LGCALDATE taken
    4 UINT unkown2

PACKET camindexfile:
    "Used for tracking wallpaper and ringtones"
    P UINT {'constant': 60} maxitems
    * LIST {'length': self.maxitems, 'elementclass': camindexentry, 'createdefault': True} +items

# desc file used for wallpaper and ringtone files 
# you have to create a directory with the filename, but the media (renamed to "body")
# and this .desc file (why couldn't they use regular filename, stupid way of storing files, grrr.)
PACKET mediadesc:
    4 UINT totalsize  "media file size with size of this file (152 bytes) added"
    4 UINT {'constant': 0} +dunno1
    4 UINT {'default': 0x7824c97a} +magic1 "probably the file date (created)"
    4 UINT {'default': 0x7824c97a} +magic2 "probably the file date (accessed)"
    4 UINT {'default': 0x7824c97a} +magic3 "probably the file date (modified)"
    4 UINT {'constant': 0} +dunno2
    32 USTRING {'default': 'body'} +filename
    32 USTRING {'default': 'identity'} +whoknows "set to iso8859_1 in some cases??"
    32 USTRING mimetype
    32 USTRING {'default': ""} +whoknows2

###
### Text Memos
###

PACKET textmemo:
    151 USTRING { 'raiseonunterminatedread': False, 'raiseontruncate': False } text

PACKET textmemofile:
    4 UINT itemcount
    * LIST {'elementclass': textmemo } +items

###
### The calendar
###
#
#   The calendar consists of one file listing events and an exception
#   file that lists exceptions.  These exceptions suppress a particular
#   instance of a repeatedw event.  For example, if you setup something
#   to happen monthly, but changed the 1st february event, then the
#   schedule will contain the repeating event, and the 1st feb one,
#   and the suppresions/exceptions file will point to the repeating
#   event and suppress the 1st feb.
#   The phone uses the position within the file to give an event an id

PACKET scheduleexception:
    4 UINT pos "Refers to event id (position in schedule file) that this suppresses"
    1 UINT day
    1 UINT month
    2 UINT year

PACKET scheduleexceptionfile:
    * LIST {'elementclass': scheduleexception} +items

PACKET scheduleevent:
    P UINT { 'constant': 64 } packet_size "Faster than packetsize()"
    4 UINT pos "position within file, used as an event id"
    4 LGCALDATE start
    4 LGCALDATE end
    1 UINT repeat
    2 UINT daybitmap  "which days a weekly repeat event happens on"
    1 UINT { 'default': 0 } +pad2
    1 UINT alarmminutes  "a value of 100 indicates not set"
    1 UINT alarmhours    "a value of 100 indicates not set"
    1 UINT alarmtype    "preset alarm reminder type"
    1 UINT { 'default': 0 } +snoozedelay   "in minutes, not for this phone"
    1 UINT ringtone
    35 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } description
    2 UINT { 'default': 0 } +unknown1     "This seems to always be two zeros"
    2 UINT hasvoice     "This event has an associated voice memo if 1"
    2 UINT voiceid   "sch/schexxx.qcp is the voice memo (xxx = voiceid - 0x0f)"
    2 UINT { 'default': 0 } +unknown2     "This seems to always be yet two more zeros"

PACKET schedulefile:
    2 UINT numactiveitems
    * LIST {'elementclass': scheduleevent} +events

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
#   Outbox message are named 'outbox000.dat', unsent messages are named 'sf00.dat',
#   only two digit file name that suggests a max of 100 message for this type.
#   Messages in the outbox get updated when the message is received by the recipient,
#   they contain a delivery flag and a delivery time for all the possible 10 recipients.
#   The pm225 stores SMS in plain text (unlike some other LG phones)

PACKET recipient_record:
    20 UINT unknown1
    P USTRING {'encoding': PHONE_ENCODING, 'default':'', 'raiseonunterminatedread': False} name
    49 USTRING number
    24 UINT unknown2
    1 UINT status   # 1 when sent, 2 when received
    4 LGCALDATE time # sent if status=1, received when status=2

PACKET sms_saved:
    4 UINT outboxmsg
    4 GPSDATE GPStime   # num seconds since 0h 1-6-80
    if self.outboxmsg:
        * sms_out outbox
    if not self.outboxmsg:
        * sms_in inbox

PACKET sms_out:
    4 UINT index # starting from 1, unique
    1 UINT locked # 1=locked
    3 UINT unknown1 # zero
    4 LGCALDATE timesent # time the message was sent
    500 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} msg # uncertain about max length
    1250 DATA unknown2
    16 USTRING callback 
    * LIST {'elementclass': recipient_record, 'length': 10} +recipients 

PACKET SMSINBOXMSGFRAGMENT:
    * LIST {'length': 181} +msg: # this size could be wrong
        1 UINT byte "individual byte of message"

PACKET sms_in:
    4 UINT unknown1 #
    4 UINT msg_index2 
    6 UINT unknown2 # set to 0 
    6 SMSDATE timesent
    3 UINT unknown
    1 UINT callback_length # 0 for no callback number
    38 USTRING callback
    1 UINT sender_length
    * LIST {'length': 38} +sender:
        1 UINT byte "individual byte of senders phone number"
    15 DATA unknown4 # set to zeros
    4 LGCALDATE lg_time # time the message was sent
    4 GPSDATE GPStime # num seconds since 0h 1-6-80, time message received by phone
    2 UINT unknown41
    2 UINT read # 1 if message has been read, 0 otherwise (kind of a guess, not enough data to be sure)
    9 UINT unknown5 # these are flags, not enough data to decode
    #1 UINT locked # 1 if the message is locked, 0 otherwise
    #1 UINT priority # 1 if the message is high priority, 0 otherwise
    21 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} subject 
    8 UINT unknown6 # these are flags, not enough data to decode
    2 UINT msglength
    18 UINT unknown7 # these are flags, not enough data to decode
    200 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} msg
    * DATA unknown8   # ?? inlcudes senders phone number and name in ascii


PACKET sms_quick_text:
# the 6190 has variable length NULL terminated strings null terminated in it's canned messages
# file sms/mediacan000.dat, max length 101 including terminator 
    * LIST {} +msgs:
        * USTRING {'encoding': PHONE_ENCODING} msg #

