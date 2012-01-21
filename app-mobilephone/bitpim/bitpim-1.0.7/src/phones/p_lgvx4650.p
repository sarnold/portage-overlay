### BITPIM
###
### Copyright (C) 2004 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx4650.p 3434 2006-06-28 03:24:32Z skyjunky $

%{

"""Various descriptions of data specific to LG VX4650"""

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

NUMPHONEBOOKENTRIES=500
pb_file_name='pim/pbentry.dat'

# Calendar parameters
NUMCALENDARENTRIES=300
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
CAL_REPEAT_DATE=(2100, 12, 31)

cal_dir='sch'
cal_voice_ext='.qcp'      # full name='sche000.qcp'
cal_data_file_name='sch/schedule.dat'
cal_exception_file_name='sch/schexception.dat'
cal_voice_id_ofs=0x0f
cal_has_voice_id=True

# Text Memo const
text_memo_file='sch/memo.dat'

# Call History const
incoming_call_file='pim/incoming_log.dat'
outgoing_call_file='pim/outgoing_log.dat'
missed_call_file='pim/missed_log.dat'

# SMS const
sms_dir='sms'
sms_ext='.dat'
sms_inbox_prefix='sms/inbox'
sms_inbox_name_len=len(sms_inbox_prefix)+3+len(sms_ext)
sms_saved_prefix='sms/sf'
sms_saved_name_len=len(sms_saved_prefix)+2+len(sms_ext)
sms_outbox_prefix='sms/outbox'
sms_outbox_name_len=len(sms_outbox_prefix)+3+len(sms_ext)
sms_canned_file='sms/mediacan000.dat'
SMS_CANNED_MAX_ITEMS=18

PHONE_ENCODING='iso8859_1'
%}

PACKET firmwarerequest:
    1 UINT {'constant': 0x00} +command

PACKET firmwareresponse:
    1 UINT command
    11 USTRING {'terminator': None}  date1
    8 USTRING {'terminator': None}  time1
    11 USTRING {'terminator': None}  date2
    8 USTRING {'terminator': None}  time2
    8 USTRING {'terminator': None}  firmwareversion
    * DATA dunno

PACKET speeddial:
    2 UINT {'default': 0xff} +entry
    1 UINT {'default': 0xff} +number

PACKET speeddials:
    * LIST {'length': NUMSPEEDDIALS, 'elementclass': speeddial} +speeddials

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
# need to modify com_lgvx4400 to give a different truncateat parameter
# in the convertphonebooktophone method
PACKET pbentry:
    4  UINT serial1
    2  UINT {'constant': 0x0202} +entrysize
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
    * USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'sizeinbytes': MEMOLENGTH} memo
    1 UINT wallpaper
    * LIST {'length': NUMPHONENUMBERS} +numbertypes:
        1 UINT numbertype
    * LIST {'length': NUMPHONENUMBERS} +numbers:
        49 USTRING {'raiseonunterminatedread': False} number
    * UNKNOWN +unknown20c

PACKET pbfileentry:
    4   UINT    serial1
    25  UNKNOWN data1
    2   UINT group
    232 UNKNOWN data2
    1   UINT    wallpaper
    15  UNKNOWN data3

PACKET pbfile:
    * LIST { 'elementclass': pbfileentry } items

PACKET indexentry:
    2 UINT {'default': 0xffff} +index
    45 USTRING {'default': ""} +name


PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    # A bit of a silly design again.  Entries with an index of 0xffff are
    # 'blank'.  Thus it is possible for numactiveitems and the actual
    # number of valid entries to be mismatched.
    P UINT {'constant': 30} maxitems
    2 UINT numactiveitems
    * LIST {'length': self.maxitems, 'elementclass': indexentry, 'createdefault': True} +items

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


## The VX4650 has the 4 bytes (unknown) below
PACKET scheduleevent:
##    P UINT { 'constant': 64 } packet_size "Faster than packetsize()"
    4 UINT pos "position within file, used as an event id"
    4 UINT { 'default': 0 } +pad1
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
    36 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } description
    1 UINT hasvoice
    2 UINT voiceid


PACKET schedulefile:
    2 UINT numactiveitems
    * LIST {'elementclass': scheduleevent} +events

# Text Memos
PACKET textmemo:
    151 USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text

PACKET textmemofile:
    4 UINT itemcount
    * LIST { 'elementclass': textmemo } +items

# calling history file
PACKET callentry:
    4 GPSDATE datetime
    4 UNKNOWN pad1
    4 UINT duration
    49 USTRING { 'raiseonunterminatedread': False } number
    36 USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False } name
    60 UNKNOWN pad2

PACKET callhistoryfile:
    4 UINT itemcount
    1 UNKNOWN pad1
    * LIST { 'elementclass': callentry } +items


PACKET SMSCannedMsg:
    101 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '' } +text

PACKET SMSCannedFile:
    * LIST { 'length': SMS_CANNED_MAX_ITEMS, 'elementclass': SMSCannedMsg } +items
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

PACKET msg_record:
    # the first few fields in this packet have something to do with the type of SMS
    # message contained. EMS and concatinated text are coded differently than a
    # simple text message
    1 UINT binary   # 0=simple text, 1=binary/concatinated
    1 UINT unknown3 # 0=simple text, 1=binary/concatinated
    1 UINT unknown4 # 0
    1 UINT unknown6 # 2=simple text, 9=binary/concatinated
    1 UINT length
    * LIST {'length': 220} +msg:
        1 UINT byte "individual byte of message"

PACKET recipient_record:
    49 USTRING number
    2 UINT status   # 1 when sent, 5 when received, 2 failed to send
    4 LGCALDATE timesent
    4 LGCALDATE timereceived
    49 UNKNOWN unknown2

PACKET sms_saved:
    4 UINT outboxmsg
    4 UNKNOWN pad
    if self.outboxmsg:
        * sms_out outbox
    if not self.outboxmsg:
        * sms_in inbox

PACKET sms_out:
    4 UINT index # starting from 1, unique
    1 UINT locked # 1=locked
    4 LGCALDATE timesent # time the message was sent
    21 USTRING subject
    2 UINT num_msg_elements # up to 10
    * LIST {'elementclass': msg_record, 'length': 7} +messages
    15 UNKNOWN unknown1
    1 UINT priority # 0=normal, 1=high
    35 USTRING callback 
    * LIST {'elementclass': recipient_record,'length': 9} +recipients
    * UNKNOWN pad

PACKET SMSINBOXMSGFRAGMENT:
    * LIST {'length': 181} +msg: # this size could be wrong
        1 UINT byte "individual byte of message"

PACKET sms_in:
    14 UNKNOWN unknown1
    6 SMSDATE timesent
    3 UINT unknown2
    1 UINT callback_length # 0 for no callback number
    38 USTRING callback
    1 UINT sender_length
    * LIST {'length': 38} +sender:
        1 UINT byte "individual byte of senders phone number"
    12 DATA unknown3 # set to zeros
    4 LGCALDATE lg_time # time the message was sent
    3 UNKNOWN unknown4
    4 GPSDATE GPStime # num seconds since 0h 1-6-80, time message received by phone
    2 UINT unknown5 # zero
    1 UINT read # 1 if message has been read, 0 otherwise
    1 UINT locked # 1 if the message is locked, 0 otherwise
    8 UINT unknown6 # zero
    1 UINT priority # 1 if the message is high priority, 0 otherwise
    21 USTRING {'encoding': PHONE_ENCODING} subject
    1 UINT bin_header1 # 0 in simple message 1 if the message contains a binary header
    1 UINT bin_header2 # 0 in simple message 9 if the message contains a binary header
    2 UINT unknown7 # zeros
    2 UINT multipartID # multi-part message ID, used for concatinated messages only
    1 UINT bin_header3 # 0 in simple message 2 if the message contains a binary header
    1 UINT num_msg_elements # max 10 elements (guessing on max here)
    * LIST {'length': 10} +msglengths:
        1 UINT msglength "lengths of individual messages in septets"
    10 UNKNOWN unknown8
    * LIST {'length': 10, 'elementclass': SMSINBOXMSGFRAGMENT} +msgs 
                # 181 bytes per message, uncertain on this, no multipart message available
                # 20 messages, 7-bit ascii for simple text. for binary header 
                # first byte is header length not including the length byte
                # rest depends on content of header, not known at this time.
                # text alway follows the header although the format it different
                # than a simple SMS
    * UNKNOWN unknown9
