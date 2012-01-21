### BITPIM
###
### Copyright (C) 2006 Simon Capper <skyjunky@sbcglobal.net.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

%{

"""Various descriptions of data specific to LG PM225 (Sprint)"""

import re

from prototypes import *
from prototypeslg import *

# Make all lg stuff available in this module as well
from p_lg import *


# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

NUMSPEEDDIALS=99
FIRSTSPEEDDIAL=1
LASTSPEEDDIAL=99
NUMPHONEBOOKENTRIES=200
MEMOLENGTH=33

NORINGTONE=0
NOMSGRINGTONE=0
NOWALLPAPER=0

NUMEMAILS=3
NUMPHONENUMBERS=5

SMS_CANNED_MAX_ITEMS=40
SMS_CANNED_MAX_LENGTH=104
SMS_CANNED_FILENAME="sms/canned_msg.dat"
SMS_PATTERNS={'Inbox': re.compile(r"^.*/inbox[0-9][0-9][0-9]\.dat$"),
             'Sent': re.compile(r"^.*/outbox[0-9][0-9][0-9]\.dat$"),
             'Saved': re.compile(r"^.*/sf[0-9][0-9]\.dat$"),
             }

numbertypetab=( 'cell', 'home', 'office', 'fax', 'pager' )

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
CAL_REPEAT_DATE=(2100, 12, 31)

cal_dir='sch'
cal_data_file_name='sch/schedule.dat'
cal_exception_file_name='sch/schexception.dat'
cal_has_voice_id=False

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

# All STRINGS have raiseonterminatedread as False since the phone does
# occassionally leave out the terminator byte
# Note if you change the length of any of these fields, you also
# need to modify com_lgpm225 to give a different truncateat parameter
# in the convertphonebooktophone method
PACKET pbentry:
    4  UINT serial1
    2  UINT {'constant': 0x0270} +entrysize
    4  UINT entrynumber                 
    33 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    2  UINT group
    2  UINT {'default': 0} +unknown2 #ringtone ??
    1  BOOL secret
    *  USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'sizeinbytes': MEMOLENGTH} memo
    *  LIST {'length': NUMEMAILS} +emails:
        73 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} email
    75 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} url
    * LIST {'length': NUMPHONENUMBERS} +numberspeeds:
        1 UINT numberspeed
    * LIST {'length': NUMPHONENUMBERS} +numbertypes:
        1 UINT numbertype
    *  LIST {'length': NUMPHONENUMBERS} +numbers:
        49 USTRING {'raiseonunterminatedread': False} number
    1  UINT {'constant': 0x7A} +EndOfRecord
    P  UINT {'default': 0x600} +ringtone
    P  UINT {'default': 0x100} +wallpaper

PACKET pbgroup:
    "A single group"
    1 UINT group_id
    1 UINT rectype 	# 0x30 or 0xFF if deleted
    3 UNKNOWN +unknown2
    3 UNKNOWN +unknown3
    33 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name

PACKET pbgroups:
    "Phonebook groups"
    * LIST {'elementclass': pbgroup} +groups

PACKET pb_contact_media_entry:
    """Reads the wallpaper/ringer info for each 
    contact on the phone"""
    2 UINT index # matches serial1 in pbentry despite being a different size
    18 DATA dont_care1
    2 UINT ringer
    33 USTRING {'encoding': PHONE_ENCODING} name # this is null terminated
    182 DATA dont_care2
    2 UINT wallpaper
    4 DATA dont_care3

PACKET pb_contact_media_file:
    * LIST {'elementclass': pb_contact_media_entry} +contacts

###
### The calendar
###
#
#   The calendar consists of one file listing events and an exception
#   file that lists exceptions.  These exceptions suppress a particular
#   instance of a repeated event.  For example, if you setup something
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
    1 UINT { 'default': 0 } +pad3
    42 USTRING {'encoding': PHONE_ENCODING, 'raiseontruncate': False,
               'raiseonunterminatedread': False } description

PACKET schedulefile:
    2 UINT numactiveitems
    * LIST {'elementclass': scheduleevent} +events

###
### Call History
###

PACKET call:
    4 GPSDATE GPStime #no. of seconds since 0h 1-6-80, based off local time.
    4 UINT unknown1 # different for each call
    4 UINT duration #seconds, not certain about length of this field
    49 USTRING {'raiseonunterminatedread': False} number
    36 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    1 UINT numberlength # length of phone number
    1 UINT unknown2 # set to 1 on some calls
    1 UINT pbnumbertype # 0=, 1=, 2=, 3=, 4=, 5=, 0xFF=not in phone book
    5 UINT unknown3 # probably contains some kind of index into the phonebook

PACKET callhistory:
    4 UINT numcalls
    1 UINT unknown1
    * LIST {'elementclass': call} +calls

###
### Media indexes
###
#
#   The pm225 has 2 index files for media and for ringtones and wallpaper uses
#   both of them. The "indexfile" packet is the same as the other versizon LG
#   phones, but the "content_file" packet is different. One index file contains
#   all downloaded content including games, images and ringtone. The two
#   index files need to be synchronised for things to work correctly.

PACKET indexentry:
    1 UINT index
    1 UINT const
    40 USTRING {'default': ""} +name

PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    # A bit of a silly design again.  Entries with an index of 0xffff are
    # 'blank'.  Thus it is possible for numactiveitems and the actual
    # number of valid entries to be mismatched.
    2 UINT numactiveitems
    * LIST {'elementclass': indexentry, 'createdefault': True} +items

PACKET content_entry:
    3 USTRING {'terminator': 0xA} type
    if self.type=='!C':
        * USTRING {'terminator': 0xA} index1
        * USTRING {'terminator': 0xA} name1
        * USTRING {'terminator': 0xA, 'default': '-1'} +unknown1 
        8 UINT {'default' :0} +unknown2
        * USTRING {'terminator': 0xA} mime_type
        * USTRING {'terminator': 0xA} content_type # 'Games', 'Screen Savers', 'Ringers'
        * USTRING {'terminator': 0xA, 'default':'bitpim.org'} +url
        1 UINT {'default':0x14} + unknown_int1
        * USTRING {'terminator': 0xA, 'default':''} +unknown3 
        1 UINT {'default':0x14} + unknown_int2
        * USTRING {'terminator': 0xA, 'default':''} +unknown4
        * USTRING {'terminator': 0xA, 'default':'0'} +unknown5 
        * USTRING {'terminator': 0xA} size
    if self.type=='!E':
        * USTRING {'terminator': 0xA, 'default':'ams:'} +location_maybe
        * USTRING {'terminator': 0xA} index2
        * USTRING {'terminator': 0xA} name2
        * USTRING {'terminator': 0xA, 'default':''} +unknown6

PACKET content_file:
    "Used to store all content on the phone, apps, ringers and images (with the exception of the camera)"
    * LIST {'elementclass': content_entry, 'createdefault': True} +items

PACKET content_count:
    "Stores the number of items in the content file"
    * USTRING {'terminator': None} count

PACKET qcp_media_header:
    "Start of a qcp format file, used to determine if a file is qcp or mp3 format"
    4 USTRING {'constant': 'RIFF', 'terminator': None} riff
    4 UINT riff_size
    8 USTRING {'constant': 'QLCMfmt ', 'terminator': None} qcp_format
    # rest of the header is not interesting 
    * DATA stuff

###
### Text Memos
###

PACKET textmemo:
    151 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text

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
    49 USTRING number
    24 UINT unknown2
    1 UINT status   # 1 when sent, 2 when received
    1 UINT unknown3 
    4 LGCALDATE time # sent if status=1, received when status=2
    12 DATA unknown2

PACKET sms_out:
    4 UINT index # starting from 1, unique
    1 UINT locked # 1=locked
    3 UINT unknown1 # zero
    4 LGCALDATE timesent # time the message was sent
    1 UINT saved # 0 for outbox, 1 for draft
    178 USTRING {'encoding': PHONE_ENCODING} msg
    1 UINT unknown3
    16 USTRING callback 
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
    38 USTRING callback
    1 UINT sender_length
    * LIST {'length': 38} +sender:
        1 UINT byte "individual byte of senders phone number"
    15 DATA unknown4 # set to zeros
    4 LGCALDATE lg_time # time the message was sent
    4 GPSDATE GPStime # num seconds since 0h 1-6-80, time message received by phone
    2 UINT read # 1 if message has been read, 0 otherwise (kind of a guess, not enough data to be sure)
    1 UINT locked # 1 if the message is locked, 0 otherwise
    8 UINT unknown5 # these are flags, not enough data to decode
    #1 UINT priority # 1 if the message is high priority, 0 otherwise
    73 USTRING {'encoding': PHONE_ENCODING} subject 
    2 UINT msglength
    200 USTRING {'encoding': PHONE_ENCODING} msg
    * DATA unknown8   # ?? inlcudes senders phone number and name in ascii

PACKET sms_quick_text:
    4 UINT {'default': 0} +dunno
    104 USTRING {'encoding': PHONE_ENCODING, 'default': ""} +msg # include terminating NULL

PACKET sms_canned_file:
    4 UINT num_active
    * LIST {'length': SMS_CANNED_MAX_ITEMS, 'createdefault': True, 'elementclass': sms_quick_text} +msgs
