### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2004 John O'Shaughnessy <oshinfo@comcast.net>
### Copyright (C) 2007 Fiz Stein <fzzz62@yahoo.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgux5000.p 4096 2007-03-13 21:27:19Z djpham $

%{

"""Various descriptions of data specific to LG UX5000"""

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
FIRSTSPEEDDIAL=2
LASTSPEEDDIAL=99
NUMPHONEBOOKENTRIES=500
MAXCALENDARDESCRIPTION=38

NUMEMAILS=3
NUMPHONENUMBERS=5

MEMOLENGTH=65

PHONE_ENCODING='iso8859_1'

CAL_NO_VOICE=0xffff
CAL_REPEAT_DATE=(2999, 12, 31)

cal_has_voice_id=True
cal_voice_id_ofs=0x11
cal_voice_ext='.qcp'      # full name='sche000.qcp'
%}

PACKET speeddial:
    2 UINT {'default': 0xffff} +entry
    1 UINT {'default': 0xff} +number

PACKET speeddials:
    * LIST {'length': NUMSPEEDDIALS, 'elementclass': speeddial} +speeddials
    
PACKET indexentry:
    2 UINT {'default': 0xffff} +index
    50 USTRING {'default': ""} +name

PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    # A bit of a silly design again.  Entries with an index of 0xffff are
    # 'blank'.  Thus it is possible for numactiveitems and the actual
    # number of valid entries to be mismatched.
    2 UINT numactiveitems
    * LIST {'elementclass': indexentry, 'createdefault': True} +items

PACKET pbgroup:
    "A single group"
    1 UINT icon
    23 USTRING {'encoding': PHONE_ENCODING} name

PACKET pbgroups:
    "Phonebook groups"
    * LIST {'elementclass': pbgroup} +groups

# All STRINGS have raiseonterminatedread as False since the phone does
# occassionally leave out the terminator byte
# Note if you change the length of any of these fields, you also
# need to modify com_lgvx4500 to give a different truncateat parameter
# in the convertphonebooktophone method

PACKET pbentry:

    4  UINT serial1
    2  UINT entrysize
    4  UINT serial2
    2  UINT entrynumber 
    23 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    2  UINT group
    *  LIST {'length': NUMEMAILS} +emails:
        49 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} email
    49 USTRING {'raiseonunterminatedread': False} url
    1  UINT ringtone                                     "ringtone index for a call"
    1  UINT msgringtone                                  "ringtone index for a text message"
    1  BOOL secret
    *  USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'sizeinbytes': MEMOLENGTH} memo
    1  UINT wallpaper
    9  UINT { 'default': 0 } +unknown1
    * LIST {'length': NUMPHONENUMBERS} +numbertypes:
        1 UINT numbertype
    * LIST {'length': NUMPHONENUMBERS} +numbers:
        49 USTRING {'raiseonunterminatedread': False} number
    * UNKNOWN +unknown20c

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
    4 UINT pos "position within file, used as an event id"
    4 LGCALDATE start
    4 LGCALDATE end
    1 UINT repeat        "Repeat?"
    3 UINT daybitmap     "which days a weekly repeat event happens on?"
    1 UINT alarmminutes  "a value of 100 indicates not set"
    1 UINT alarmhours    "a value of 100 indicates not set"
    1 UINT alarmtype     "preset alarm reminder type"
    1 UINT { 'default': 0 } +snoozedelay   "in minutes?"
    1 UINT ringtone
    35 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } description
    2 UINT { 'default': 0 } +unknown1     "This seems to always be two zeros"
    2 UINT hasvoice     "This event has an associated voice memo if 1"
    2 UINT voiceid   "sch/schexxx.qcp is the voice memo (xxx = voiceid - 0x0f)"
    2 UINT { 'default': 0 } +unknown2     "This seems to always be yet two more zeros"

PACKET schedulefile:
    2 UINT numactiveitems
    * LIST {'elementclass': scheduleevent} +events

PACKET camindexentry:
    1 UINT {'default': 0} +index
    11 USTRING {'default': ""} +name
    4 LGCALDATE +taken
    4 UINT {'default': 0x00ff0100} +dunno

PACKET campicsdat:
    "the cam/pics.dat file"
    * LIST {'length': 60, 'elementclass': camindexentry, 'createdefault': True} +items

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
    9 UINT unknown9

PACKET callhistory:
    4 UINT numcalls
    1 UINT unknown1
    * LIST {'elementclass': call} +calls

PACKET firmwareresponse:
    1 UINT command
    11 USTRING {'terminator': None}  date1
    8 USTRING {'terminator': None}  time1
    11 USTRING {'terminator': None}  date2
    8 USTRING {'terminator': None}  time2
    8 USTRING {'terminator': None}  firmware

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
#   The vx8100 supports SMS contatination, this allows you to send text messages that are
#   longer than 160 characters. The format is different for these type of messages, but
#   it is supported by this implementation.
#   The vx8100 also allows you to put small graphics, sounds and animations in a message.
#   This implementation does not support these, if they are contained in a message they
#   will be ignored and just the text will be shown when you view the message in bitpim.
#   The text in the the messages is stored in 7-bit characters, so they have
#   to be unpacked, in concatinated messages and messages with embeded graphics etc. the
#   format uses the GSM 03.38 specified format, a good example of this can be found at
#   "http://www.dreamfabric.com/sms/hello.html".
#   For simple messages less than 161 characters with no graphics the format is simpler, 
#   the 7-bit characters are just packed into memory in the order they appear in the
#   message.

PACKET recipient_record:
    14 UINT unknown1
    49 USTRING number
    1 UINT status   # 1 when sent, 5 when received, 2 failed to send
    4 LGCALDATE timesent
    4 LGCALDATE timereceived
    40 DATA unknown2

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
    21 USTRING {'encoding': PHONE_ENCODING} subject
    1 DATA unknown2
    1 UINT num_msg_elements # up to 7
    * LIST {'elementclass': msg_record, 'length': 7} +messages
    2 UINT unknown6
    1 UINT priority # 0=normal, 1=high
    13 DATA unknown7
    3 DATA unknown8 # set to 01,00,00 
    23 USTRING callback 
    * LIST {'elementclass': recipient_record, 'length': 10} +recipients 

PACKET SMSINBOXMSGFRAGMENT:
    * LIST {'length': 181} +msg: # this size could be wrong
        1 UINT byte "individual byte of message"

PACKET sms_in:
    4 UINT msg_index1
    4 UINT msg_index2 
    2 UINT unknown2 # set to 0 
    4 UINT unknown3 # set to 0
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
    2 UINT unknown5 # zero
    1 UINT read # 1 if message has been read, 0 otherwise
    1 UINT locked # 1 if the message is locked, 0 otherwise
    2 UINT unknown8 
    1 UINT priority # 1 if the message is high priority, 0 otherwise
    6 DATA flags # message flags
    21 USTRING {'encoding': PHONE_ENCODING} subject
    1 UINT bin_header1 # 0 in simple message 1 if the message contains a binary header
    1 UINT bin_header2 # 0 in simple message 9 if the message contains a binary header
    1 UINT multipartID # multi-part message ID, used for concatinated messages only
    3 UINT unknown6 # zeros
    1 UINT bin_header3 # 0 in simple message 2 if the message contains a binary header
    1 UINT num_msg_elements # max 20 elements (guessing on max here)
    * LIST {'length': 20} +msglengths:
        1 UINT msglength "lengths of individual messages in septets"
    * LIST {'length': 20, 'elementclass': SMSINBOXMSGFRAGMENT} +msgs 
                # 181 bytes per message, 
                # 20 messages, 7-bit ascii for simple text. for binary header 
                # first byte is header length not including the length byte
                # rest depends on content of header, not known at this time.
                # text alway follows the header although the format it different
                # than a simple SMS
    68 DATA unknown5
    33 USTRING senders_name
    169 DATA unknown6   # ?? inlcudes senders phone number in ascii

PACKET sms_quick_text:
# the vx4400 has variable length NULL terminated strings null terminated in it's canned messages
# file sms/mediacan000.dat, not sure about the max
    * LIST {} +msgs:
        * USTRING {'encoding': PHONE_ENCODING} msg #

# Text Memos. LG memo support is weak, it only supports the raw text and none of 
# the features that other phones support, when you run bitpim you see loads of
# options that do not work in the vx8100 on the memo page
PACKET textmemo:
    151 USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text

PACKET textmemofile:
    4 UINT itemcount
    * LIST { 'elementclass': textmemo } +items
