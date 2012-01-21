### BITPIM
###
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx8000.p 3352 2006-06-10 15:20:39Z skyjunky $

%{

"""Various descriptions of data specific to LG VX8000"""

from prototypes import *

# Make all lg stuff available in this module as well
from p_lg import *

# we are the same as lgvx7000 except as noted
# below
from p_lgvx7000 import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

%}
    
PACKET indexentry:
    2 UINT index
    2 UINT type
    # they shortened this from 84 chars in the vx7000
    64 USTRING filename  "includes full pathname"
    4 UINT {'default': 0} +date "i think this is bitfield of the date"
    4 UINT dunno

PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    * LIST {'elementclass': indexentry, 'createdefault': True} +items

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
    33 DATA unknown1 # contains recipient name from phonebook on this phone
    49 USTRING number
    1 UINT status   # 1 when sent, 5 when received
    4 LGCALDATE timesent
    4 LGCALDATE timereceived
    1 UINT unknown2 # 0 when not received, set to 1 when received
    40 DATA unknown3

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
   1 UNKNOWN unknown2
   4 LGCALDATE timesent # time the message was sent
   6 UNKNOWN unknown2
   21 USTRING subject
   1 UNKNOWN unknown4
   2 UINT num_msg_elements # up to 10
   * LIST {'elementclass': msg_record, 'length': 7} +messages
   14 UNKNOWN unknown1
   1 UINT priority # 0=normal, 1=high
   1 UNKNOWN unknown5
   35 USTRING callback
   * LIST {'elementclass': recipient_record,'length': 9} +recipients
   * UNKNOWN pad

PACKET SMSINBOXMSGFRAGMENT:
   * LIST {'length': 181} +msg: # this size could be wrong
       1 UINT byte "individual byte of message"

PACKET sms_in:
   10 UNKNOWN unknown1
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
   4 UINT unknown5 # zero
   1 UINT read # 1 if message has been read, 0 otherwise
   1 UINT locked # 1 if the message is locked, 0 otherwise
   8 UINT unknown6 # zero
   1 UINT priority # 1 if the message is high priority, 0 otherwise
   21 USTRING subject
   1 UINT bin_header1 # 0 in simple message 1 if the message contains a binary header
   1 UINT bin_header2 # 0 in simple message 9 if the message contains a binary header
   4 UINT unknown7 # zeros
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
