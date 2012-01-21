### BITPIM
###
### Copyright (C) 2003-2006 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2005-2006 Simon Capper <skyjunky@sbcglobal.net>
### Copyright (C) 2006 Michael Cohen <mikepublic@nc.rr.com>
### Copyright (C) 2006 Bart Massey <bitpim@po8.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx5300.p 3917 2007-01-19 05:13:24Z djpham $

%{

"""Various descriptions of data specific to LG VX5300"""

from common import PhoneBookBusyException

from prototypes import *

# Make all lg stuff available in this module as well
from p_lg import *

# we are the same as lgvx8100 except as noted
# below
from p_lgvx8100 import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

BREW_FILE_SYSTEM=0

PHONE_ENCODING='iso-8859-1'

NUMSPEEDDIALS=100
FIRSTSPEEDDIAL=2
LASTSPEEDDIAL=99
NUMPHONEBOOKENTRIES=500
MAXCALENDARDESCRIPTION=32
CALENDAR_HAS_SEPARATE_END_TIME_AND_DATE=1

NUMEMAILS=2
NUMPHONENUMBERS=5

# need to call stat to get the file time/data
broken_filelist_date=True
%}

PACKET indexentry:
    256 USTRING {'encoding': PHONE_ENCODING,
                 'raiseonunterminatedread': False,
                 'raiseontruncate': False } filename  "full pathname"
    4 UINT size
    4 UINT {'default': 0} +date
    4 UINT type

PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    * LIST {'elementclass': indexentry, 'createdefault': True} +items

# All STRINGS have raiseonterminatedread as False since the phone does
# occassionally leave out the terminator byte
# Note if you change the length of any of these fields, you also
# need to modify com_lgvx7000 to give a different truncateat parameter
# in the convertphonebooktophone method
PACKET pbentry:
   4  UINT serial1
   2  UINT {'constant': 0x181, 'constantexception': PhoneBookBusyException} +entrysize
   4  UINT serial2
   2  UINT entrynumber
   23 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
   2  UINT group
   *  LIST {'length': NUMEMAILS} +emails:
       49 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} email
   2  UINT {'default': 0xFFFF} +ringtone       "ringtone index for a call"
   2  UINT {'default': 0xFFFF} +msgringtone    "ringtone index for a text message"
   2  UINT {'default': 0} +wallpaper
   * LIST {'length': NUMPHONENUMBERS} +numbertypes:
       1 UINT numbertype
   * LIST {'length': NUMPHONENUMBERS} +numbers:
       49 USTRING {'raiseonunterminatedread': False} number
   * UNKNOWN +unknown

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

# 314 bytes per record, maybe they plan to add a memo field at some point??
PACKET scheduleevent:
    4 UINT pos "position within file, used as an event id"
    33 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } description
    4 LGCALDATE start
    4 LGCALDATE end_time
    4 LGCALDATE end_date
    4 LGCALREPEAT repeat # complicated bit mapped field
    1 UINT alarmindex_vibrate #LSBit of this set vibrate ON(0)/OFF(1), the 7 MSBits are the alarm index
                              #the alarmindex is the index into the amount of time in advance of the
                              #event to notify the user. It is directly related to the alarmminutes
                              #and alarmhours below, valid values are
                              # 8=2days, 7=1day, 6=2hours, 5=1hour, 4=15mins, 3=10mins, 2=5mins, 1=0mins, 0=NoAlarm
    1 UINT ringtone
    1 UINT { 'default': 0 } +unknown1
    1 UINT alarmminutes  "a value of 0xFF indicates not set"
    1 UINT alarmhours    "a value of 0xFF indicates not set"
    256 USTRING {'encoding': PHONE_ENCODING,
                 'raiseonunterminatedread': False,
                 'raiseontruncate': False,
                 'default': '' } +ringpath
                              # MIC If ringtone = 0x64 (decimal 100), this field is used to specify
                              # the full path of the ringer, either on the phone or on the microSD card

PACKET schedulefile:
    2 UINT numactiveitems
    * LIST {'elementclass': scheduleevent} +events

PACKET call:
    4 GPSDATE GPStime #no. of seconds since 0h 1-6-80, based off local time.
    4 UINT unknown2 # different for each call
    4 UINT duration #seconds, not certain about length of this field
    49 USTRING {'raiseonunterminatedread': False} number
    36 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    1 UINT numberlength # length of phone number
    1 UINT pbnumbertype # 1=cell, 2=home, 3=office, 4=cell2, 5=fax, 6=vmail, 0xFF=not in phone book
    5 UINT unknown2 #
    2 UINT pbentrynum #entry number in phonebook

PACKET callhistory:
    4 UINT numcalls
    1 UINT unknown1
    * LIST {'elementclass': call} +calls

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
    1 UINT unknown1 # 0
    1 UINT binary   # 0=simple text, 1=binary/concatinated
    1 UINT unknown3 # 0=simple text, 1=binary/concatinated
    1 UINT unknown4 # 0
    1 UINT unknown6 # 2=simple text, 9=binary/concatinated
    1 UINT length
    * LIST {'length': 219} +msg:
        1 UINT byte "individual byte of message"

PACKET recipient_record:
    34 DATA unknown1 # contains recipient name from phonebook on this phone
    49 USTRING number
    1 UINT status   # 1 when sent, 5 when received
    4 LGCALDATE timesent
    4 LGCALDATE timereceived
    1 UINT unknown2 # 0 when not received, set to 1 when received
    53 DATA unknown3

PACKET sms_saved:
    4 UINT outboxmsg
    4 GPSDATE GPStime   # num seconds since 0h 1-6-80, time message received by phone
    if self.outboxmsg:
        * sms_out outbox
    if not self.outboxmsg:
        * sms_in inbox

PACKET sms_out:
    4 UINT index # starting from 1, unique
    1 UINT unknown1 # zero
    1 UINT locked # 1=locked
    4 LGCALDATE timesent # time the message was sent
    2 UINT unknown2 # zero
    4 GPSDATE GPStime  # num seconds since 0h 1-6-80, time message received by phone
    24 USTRING {'encoding': PHONE_ENCODING} subject
    1 UINT num_msg_elements # up to 7
    * LIST {'elementclass': msg_record, 'length': 7} +messages
    15 UNKNOWN unknown1
    1 UINT priority # 0=normal, 1=high
    1 UNKNOWN unknown5
    35 USTRING callback
    * LIST {'elementclass': recipient_record,'length': 9} +recipients
    * UNKNOWN pad

PACKET SMSINBOXMSGFRAGMENT:
    * LIST {'length': 181} +msg: # this size could be wrong
        1 UINT byte "individual byte of message"

PACKET sms_in:
    7 UNKNOWN unknown1
    4 LGCALDATE lg_time # time the message was sent
    1 UINT unknown2
    4 GPSDATE GPStime # num seconds since 0h 1-6-80, time message received by phone
    6 SMSDATE timesent
    1 UINT callback_length # 0 for no callback number
    39 USTRING callback
    1 UINT sender_length
    * LIST {'length': 38} +sender:
        1 UINT byte "individual byte of senders phone number"
    12 DATA unknown3 # set to zeros
    6 UNKNOWN unknown4
    1 UINT read # 1 if message has been read, 0 otherwise
    1 UINT locked # 1 if the message is locked, 0 otherwise
    1 UINT priority # 1 if the message is high priority, 0 otherwise
    24 USTRING {'encoding': PHONE_ENCODING} subject
    1 UINT bin_header1 # 0 in simple message 1 if the message contains a binary header
    1 UINT bin_header2 # 0 in simple message 9 if the message contains a binary header
    1 UINT unknown7 # zeros
    2 UINT multipartID # multi-part message ID, used for concatinated messages only
    1 UINT bin_header3 # 0 in simple message 2 if the message contains a binary header
    5 UINT unknown8 # zeros
    1 UINT num_msg_elements # max 10 elements (guessing on max here)
    * LIST {'length': 10} +msglengths:
        1 UINT msglength "lengths of individual messages in septets"
    10 UNKNOWN unknown9
    * LIST {'length': 10, 'elementclass': SMSINBOXMSGFRAGMENT} +msgs
               # 181 bytes per message, uncertain on this, no multipart message available
               # 20 messages, 7-bit ascii for simple text. for binary header
               # first byte is header length not including the length byte
               # rest depends on content of header, not known at this time.
               # text alway follows the header although the format it different
               # than a simple SMS
    * UNKNOWN unknown10

PACKET sms_quick_text:
    * LIST { 'length': SMS_CANNED_MAX_ITEMS, 'createdefault': True} +msgs:
        101 USTRING {'encoding': PHONE_ENCODING, 'default': ""} +msg # include terminating NULL

# Text Memos. LG memo support is weak, it only supports the raw text and none of
# the features that other phones support, when you run bitpim you see loads of
# options that do not work in the vx8100 on the memo page
PACKET textmemo:
    152 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text
    4 UINT {'default' : 0x1000000} +dunno
    4 LGCALDATE memotime # time the memo was writen LG time

PACKET textmemofile:
    4 UINT itemcount
    * LIST { 'elementclass': textmemo } +items
