### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
### Copyright (C) 2006 Caesar Naples <caesarnaples@yahoo.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx9900.p 4647 2008-07-26 04:17:24Z djpham $

%{

"""Various descriptions of data specific to LG VX9900"""

from prototypes import *
from prototypeslg import *

# Make all lg stuff available in this module as well
from p_lg import *

# we are the same as lgvx9800 except as noted
# below
from p_lgvx9800 import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

CALENDAR_HAS_SEPARATE_END_TIME_AND_DATE=1

from p_lgvx8300 import scheduleexception
from p_lgvx8300 import scheduleevent
from p_lgvx8300 import scheduleexceptionfile
from p_lgvx8300 import schedulefile
from p_lgvx8300 import indexentry
from p_lgvx8300 import indexfile
from p_lgvx8300 import call
from p_lgvx8300 import callhistory
##from p_lgvx8500 import msg_record
##from p_lgvx8500 import recipient_record
##from p_lgvx8500 import sms_saved
##from p_lgvx8500 import sms_out
##from p_lgvx8500 import SMSINBOXMSGFRAGMENT
##from p_lgvx8500 import sms_in
##from p_lgvx8500 import sms_quick_text

%}

PACKET textmemo:
    304 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text
    4 UINT {'default' : 0x1000000} +dunno
    4 LGCALDATE memotime # time the memo was writen LG time

PACKET textmemofile:
    4 UINT itemcount
    * LIST { 'elementclass': textmemo } +items

# SMS stuff

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
    33 DATA unknown1 # contains name if available
    53 USTRING number
    1 UINT status   # 1 when sent, 5 when received
    4 LGCALDATE timesent
    4 LGCALDATE timereceived
    1 UINT unknown2 # 0 when not received, set to 1 when received
    54 DATA unknown3

PACKET sms_saved:
    P BOOL { 'default': True } +outboxmsg
    4 GPSDATE GPStime   # num seconds since 0h 1-6-80, time message received by phone
    * sms_out outbox

PACKET sms_out:
    4 UINT index # starting from 1, unique
    1 UINT locked # 1=locked
    4 LGCALDATE timesent # time the message was sent
    7 UNKNOWN unknown2 # zero
    61 USTRING {'encoding': PHONE_ENCODING} subject
    1 UINT num_msg_elements # up to 7
    * LIST {'elementclass': msg_record, 'length': 7} +messages
    18 UNKNOWN unknown1
    # Don't know where the priority field is
    P UINT { 'default': 0 } +priority # 0=normal, 1=high
##    16 UNKNOWN unknown5
    73 USTRING callback
    # Can't figure out the recipient record, so set just 1 for now
    * LIST {'elementclass': recipient_record,'length': 9} +recipients

PACKET SMSINBOXMSGFRAGMENT:
    * LIST {'length': 220} +msg: # this size could be wrong
        1 UINT byte "individual byte of message"

PACKET sms_in:
    7 UNKNOWN unknown1
    4 LGCALDATE lg_time # time the message was sent
    1 UINT unknown2
    4 GPSDATE GPStime # num seconds since 0h 1-6-80, time message received by phone
    6 SMSDATE timesent
    1 UINT read
    1 UINT locked
    1 UINT priority
    6 UNKNOWN dunno1
    23 USTRING {'encoding': PHONE_ENCODING,
                'raiseonunterminatedread': False } subject
    47 UNKNOWN dunno2
    1 UINT num_msg_elements # max 20 elements (guessing on max here)
    * LIST {'length': 20} +msglengths:
        1 UINT msglength "lengths of individual messages in septets"
    * LIST {'length': 20, 'elementclass': SMSINBOXMSGFRAGMENT} +msgs
    4 UNKNOWN dunno3
    1 UINT sender_length
    * LIST {'length': 49} +sender:
        1 UINT byte "individual byte of senders phone number"
    3 UNKNOWN dunno4
    1 UINT callback_length # 0 for no callback number
    22 USTRING callback
    # this stuff is required by the code, but couldn't figure it out,
    # so just fake it
    P UINT { 'default': 0 } +bin_header1
    P UINT { 'default': 0 } +bin_header2
    P UINT { 'default': 0 } +multipartID
    P UINT { 'default': 0 } +bin_header3

PACKET sms_quick_text:
    * LIST { 'length': SMS_CANNED_MAX_ITEMS, 'createdefault': True} +msgs:
        101 USTRING {'encoding': PHONE_ENCODING, 'default': ""} +msg # include terminating NULL


