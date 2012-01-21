### BITPIM ( -*- Python -*- )
###
### Copyright (C) 2007-2008 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx8800.p 4639 2008-07-22 19:50:21Z djpham $

%{

"""Various descriptions of data specific to LG VX8800"""

from p_lgvx8550 import *

# SMS index files
inbox_index     = "dload/inbox.dat"
outbox_index    = "dload/outbox.dat"
drafts_index    = "dload/drafts.dat"

%}

# Index files

PACKET indexentry:
    256 USTRING {'encoding': PHONE_ENCODING,
                 'raiseonunterminatedread': False,
                 'raiseontruncate': False } filename  "full pathname"
    4 UINT size
    4 UINT {'default': 0} +date
    4 UINT type
    4 UINT {'default': 0} +unknown

PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    * LIST {'elementclass': indexentry, 'createdefault': True} +items

# Memos

PACKET textmemo:
    4 GPSDATE { 'default': GPSDATE.now(),
                'unique': True } +cdate
    304 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text
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
    33 DATA unknown1 # contains recipient name from phonebook on this phone
    50 USTRING number
    3 UNKNOWN dunno1
    1 UINT status   # 1 when sent, 5 when received
    4 LGCALDATE timesent
    4 LGCALDATE timereceived
    1 UINT unknown2 # 0 when not received, set to 1 when received
    54 DATA unknown3

PACKET sms_saved:
    4 GPSDATE GPStime   # num seconds since 0h 1-6-80, time message received by phone
    * sms_out outbox

PACKET sms_out:
    4 UINT index            # starting from 1, unique
    1 UINT locked           # 1=locked
    4 LGCALDATE timesent    # time the message was sent (possibly composed)
    3 UNKNOWN unknown2      # zero
    4 GPSDATE GPStimesent   # zero in drafts
    61 USTRING {'encoding': PHONE_ENCODING} subject
    1 UINT num_msg_elements # up to 7
    * LIST {'elementclass': msg_record, 'length': 7} +messages
    1 UNKNOWN unknown1
    1 UINT priority         # 0=normal, 2=high
    16 UNKNOWN unknown5
    73 USTRING callback
    * LIST {'elementclass': recipient_record,'length': 9} +recipients
    * UNKNOWN pad           # contains 10th recipient

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
    1 UINT num_msg_elements # max 10 elements (guessing on max here)
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
    33 USTRING callback_name
    49 USTRING callback2
    * UNKNOWN PAD
    # this stuff is required by the code, but couldn't figure it out,
    # so just fake it
    P UINT { 'default': 0 } +bin_header1
    P UINT { 'default': 0 } +bin_header2
    P UINT { 'default': 0 } +multipartID
    P UINT { 'default': 0 } +bin_header3

PACKET sms_quick_text:
    * LIST { 'length': SMS_CANNED_MAX_ITEMS, 'createdefault': True} +msgs:
        101 USTRING {'encoding': PHONE_ENCODING, 'default': ""} +msg # include terminating NULL
