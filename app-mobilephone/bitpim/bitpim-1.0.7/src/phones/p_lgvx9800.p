### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx9800.p 3788 2006-12-20 23:15:29Z djpham $

%{

"""Various descriptions of data specific to LG VX9800"""

from prototypes import *
from prototypeslg import *

# Make all lg stuff available in this module as well
from p_lg import *

# we are the same as lgvx8100 except as noted
# below
from p_lgvx8100 import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

# phonebooks constants
NUMPHONEBOOKENTRIES=1000
NUMEMAILS=2
NUMPHONENUMBERS=5
pb_file_name='pim/pbentry.dat'
wallpaper_id_file_name='pim/pbPictureIdSetAsPath.dat'
WALLPAPER_ID_PATH_MAX_LEN=80

# Media type
MEDIA_TYPE_RINGTONE=0x0201
MEDIA_TYPE_IMAGE=0x0100
MEDIA_TYPE_SOUND=0x0402
MEDIA_TYPE_SDIMAGE=0x0008
MEDIA_TYPE_SDSOUND=0x000C
MEDIA_TYPE_VIDEO=0x0304
MEDIA_RINGTONE_DEFAULT_ICON=1
MEDIA_IMAGE_DEFAULT_ICON=0
MEDIA_VIDEO_DEFAULT_ICON=0

# Calendar parameters
NUMCALENDARENTRIES=300


# vx8100 uses a type based index for speed dials instead of positional like the vx4400
SPEEDDIALINDEX=1 
MAXCALENDARDESCRIPTION=32

SMS_CANNED_MAX_ITEMS=18
SMS_CANNED_MAX_LENGTH=101

BREW_FILE_SYSTEM=1

PHONE_ENCODING='iso-8859-1'

# playlist constants
pl_dir='mmc1/my_mp3_playlist'
pl_dir_len=len(pl_dir)+1
pl_extension='.pl'
pl_extension_len=len(pl_extension)
mp3_dir='mmc1/my_mp3'
mp3_dir_len=len(mp3_dir)+1  # account for the last '/'
mp3_index_file='dload/my_mp3.dat'

# need to call stat to get the file time/data
broken_filelist_date=True


%}

PACKET indexentry:
    2 UINT index
    2 UINT type
    80 USTRING {'encoding': PHONE_ENCODING,
                'raiseonunterminatedread': False,
                'raiseontruncate': False } filename  "includes full pathname"
    4 UINT {'default':0} +icon
    4 UINT {'default': 0} +date "i think this is bitfield of the date"
    4 UINT dunno
    4 UINT {'default': 0} +size "size of the file, can be set to zero"

PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    * LIST {'elementclass': indexentry, 'createdefault': True} +items

PACKET playlistentry:
    84 USTRING { 'encoding': PHONE_ENCODING,
                 'raiseonunterminatedread': False,
                 'raiseontruncate': False } name
    4 UINT { 'default': 0 } +date
    4 UINT { 'default': 0 } +dunno1
    4 UINT { 'default': 0 } +dunno2
    4 UINT { 'default': 1 } +dunno3

PACKET playlistfile:
    * LIST { 'elementclass': playlistentry } +items

PACKET pbgroup:
    "A single group"
    23 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } name

PACKET pbgroups:
    "Phonebook groups"
    * LIST {'elementclass': pbgroup} +groups

PACKET pbinforequest:
    "Random information about the phone"
    * pbheader {'command': 0x15, 'flag': 0x01} +header
    6 UNKNOWN +pad

PACKET pbinforesponse:
    * pbheader header
    10 UNKNOWN dunno1
    4 UINT firstentry
    2 UINT numentries  # fields from this point on differ by model and are not decoded correctly
    * UNKNOWN dunno2

PACKET pbentry:
   4  UINT serial1
   2  UINT {'constant': 0x01BE, 'constantexception': PhoneBookBusyException} +entrysize
   4  UINT serial2
   2  UINT entrynumber
   23 USTRING {'encoding': PHONE_ENCODING,'raiseonunterminatedread': False} name
   2  UINT { 'default': 0 } +group
   *  LIST {'length': NUMEMAILS} +emails:
       49 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} email
   2  UINT { 'default': 0xffff } +ringtone           "ringtone index for a call"
   2  UINT { 'default': 0xffff } +msgringtone   "ringtone index for a text message"
   2  UINT { 'default': 0 } +wallpaper
   * LIST {'length': NUMPHONENUMBERS} +numbertypes:
       1 UINT numbertype
   * LIST {'length': NUMPHONENUMBERS} +numbers:
       49 USTRING {'raiseonunterminatedread': False} number
   61 USTRING {'default': '', 'raiseonunterminatedread': False} +memo
   * UNKNOWN +unknown

PACKET pbfileentry:
    4   UINT    serial1
    2   UINT    entrynumber
    127 UNKNOWN data1
    2   UINT    wallpaper
    76  UNKNOWN data2

PACKET pbfile:
    * LIST { 'elementclass': pbfileentry } items

PACKET wallpaper_id:
    80 USTRING { 'terminator': None, 'pad': 0xFF, 'default': "" } +path
PACKET wallpaper_id_file:
    * LIST { 'length': NUMPHONEBOOKENTRIES,
             'elementclass': wallpaper_id,
             'createdefault': True } +items

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
    33 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } description
    4 LGCALDATE start
    4 LGCALDATE end
    4 LGCALREPEAT repeat # complicated bit mapped field
    1 UINT alarmindex_vibrate #LSBit of this set vibrate ON(0)/OFF(1), the 7 MSBits are the alarm index
                              #the alarmindex is the index into the amount of time in advance of the 
                              #event to notify the user. It is directly related to the alarmminutes 
                              #and alarmhours below, valid values are
                              # 8=2days, 7=1day, 6=2hours, 5=1hour, 4=15mins, 3=10mins, 2=5mins, 1=0mins, 0=NoAlarm
    1 UINT ringtone
    1 UINT unknown1
    1 UINT alarmminutes  "a value of 0xFF indicates not set"
    1 UINT alarmhours    "a value of 0xFF indicates not set"
    1 UINT unknown2


PACKET schedulefile:
    2 UINT numactiveitems
    * LIST {'elementclass': scheduleevent} +events

PACKET call:
    4 GPSDATE GPStime #no. of seconds since 0h 1-6-80, based off local time.
    4 UINT unknown2 # different for each call
    4 UINT duration #seconds, not certain about length of this field
    49 USTRING {'raiseonunterminatedread': False} number
    36 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    2 UINT numberlength # length of phone number
    1 UINT pbnumbertype # 1=cell, 2=home, 3=office, 4=cell2, 5=fax, 6=vmail, 0xFF=not in phone book
    3 UINT unknown2 # always seems to be 0
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

PACKET recipient_record:
    45 DATA unknown1
    49 USTRING number
    1 UINT status   # 1 when sent, 5 when received
    4 LGCALDATE timesent
    4 LGCALDATE timereceived
    1 UINT unknown2 # 0 when not received, set to 1 when received
    40 DATA unknown3

PACKET sms_saved:
    4 UINT inboxmsg
    4 GPSDATE GPStime   # num seconds since 0h 1-6-80, time message received by phone
    if not self.inboxmsg:
        * sms_out outbox
    if self.inboxmsg:
        * sms_in inbox

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

PACKET sms_out:
    4 UINT index # starting from 1, unique
    1 UINT unknown1 # zero
    1 UINT locked # zero
    4 LGCALDATE timesent # time the message was sent
    2 UINT unknown2 # zero
    4 GPSDATE GPStime  # num seconds since 0h 1-6-80, time message received by phone
    21 USTRING {'encoding': PHONE_ENCODING} subject
    1 UINT unknown4
    1 UINT num_msg_elements # up to 7
    1 UINT unknown6
    * LIST {'elementclass': msg_record, 'length': 7} +messages
    1 UINT priority # 0=normal, 1=high
    12 DATA unknown7
    3 DATA unknown8 # set to 01,00,01 
    23 USTRING callback
    * LIST {'elementclass': recipient_record,'length': 10} +recipients
    * UNKNOWN unknown8

PACKET SMSINBOXMSGFRAGMENT:
    * LIST {'length': 181} +msg:
        1 UINT byte "individual byte of message"

PACKET sms_in:
    4 UINT msg_index1
    4 UINT msg_index2 # equal to the numerical part of the filename eg inbox002.dat
    2 UINT unknown2 # set to 0 for simple message and 3 for binary
    6 SMSDATE timesent
    3 UINT unknown
    1 UINT callback_length
    38 USTRING callback
    1 UINT sender_length
    * LIST {'length': 38} +sender:
        1 UINT byte "individual byte of senders phone number"
    12 DATA unknown3 # set to zeros
    4 LGCALDATE lg_time # time the message was sent
    3 UINT unknown4 # set to zeros
    4 GPSDATE GPStime # num seconds since 0h 1-6-80, time message received by phone
    4 UINT unknown5 # zero
    1 UINT read # 1 if message has been read, 0 otherwise
    1 UINT locked # 1 if the message is locked, 0 otherwise
    2 UINT unknown8 # zero
    1 UINT priority # 1 if the message is high priority, 0 otherwise
    6 DATA unknown11 # zero
    21 USTRING {'encoding': PHONE_ENCODING} subject
    1 UINT bin_header1 # 0 in simple message 1 if the message contains a binary header
    1 UINT bin_header2 # 0 in simple message 9 if the message contains a binary header
    2 UINT unknown6 # zeros
    2 UINT multipartID # multi-part message ID, used for concatinated messages only
    2 UINT unknown14 
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
    101 DATA unknown12
    59 USTRING {'encoding': PHONE_ENCODING} senders_name
    * DATA unknown9   # ?? inlcudes senders phone number in ascii

PACKET sms_quick_text:
    * LIST {'length': SMS_CANNED_MAX_ITEMS, 'createdefault': True} +msgs:
        101 USTRING {'encoding': PHONE_ENCODING, 'default': ""} +msg # include terminating NULL

# Text Memos. LG memo support is weak, it only supports the raw text and none of 
# the features that other phones support, when you run bitpim you see loads of
# options that do not work in the vx8100 on the memo page
PACKET textmemo:
    301 USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text
    4 LGCALDATE memotime # time the memo was writen

PACKET textmemofile:
    4 UINT itemcount
    * LIST { 'elementclass': textmemo } +items

PACKET firmwareresponse:
    1 UINT command
    11 USTRING {'terminator': None}  date1
    8 USTRING {'terminator': None}  time1
    11 USTRING {'terminator': None}  date2
    8 USTRING {'terminator': None}  time2
    8 USTRING {'terminator': None}  firmware
