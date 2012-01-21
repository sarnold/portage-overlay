### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx8500.p 4395 2007-09-11 21:11:45Z djpham $
###
%{

"""Various descriptions of data specific to LG VX8500"""

from common import PhoneBookBusyException

from prototypes import *
from prototypeslg import *

# Make all lg stuff available in this module as well
from p_lg import *

# we are the same as lgvx8300 except as noted below
from p_brew import *
from p_lgvx8300 import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

# Phonebook stuff
RTPathIndexFile='pim/pbRingIdSetAsPath.dat'
MsgRTIndexFile='pim/pbMsgRingIdSetAsPath.dat'
WPPathIndexFile='pim/pbPictureIdSetAsPath.dat'
pb_file_name='pim/pbentry.dat'

# Calendar stuff
##NUMCALENDARENTRIES=??

#Play List stuff
PLIndexFileName='dload/aodplaylist.lgpl'
PLFilePath='dload'
PLExt='.clgpl'
PLMaxSize=50    # Max number of items per playlist

# T9 User Database, how do we handle the Spanish DB?
T9USERDBFILENAME='t9udb/t9udb_eng.dat'
Default_Header='\x36\x00' \
               '\x00\x00\x00\x00\x00\x00\x00\x00'
Default_Header2=        '\xFB\x07\xF6\x0F\xF1\x17' \
                '\xEC\x1F\xE7\x27\xE2\x2F\xDD\x37' \
                '\xD8\x3F\xD3\x47'
%}

# Phonebook stuff
PACKET pbfileentry:
    4   UINT    serial1
    2   UINT    entrynumber
    123 DATA    data1
    2   UINT    ringtone
    2   UINT    msgringtone
    2   UINT    wallpaper
    250 DATA    data2

PACKET pbfile:
    * LIST { 'elementclass': pbfileentry } items

PACKET PathIndexEntry:
    255 USTRING { 'encoding': PHONE_ENCODING,
                  'default': '' } +pathname
PACKET PathIndexFile:
    * LIST { 'elementclass': PathIndexEntry,
             'createdefault': True,
             'length': NUMPHONEBOOKENTRIES } +items

# Playlist stuff
PACKET PLIndexEntry:
    255 USTRING { 'encoding': PHONE_ENCODING } pathname

PACKET PLIndexFile:
    * LIST { 'elementclass': PLIndexEntry,
             'createdefault': True } +items

PACKET PLSongEntry:
    255 USTRING { 'encoding': PHONE_ENCODING } pathname
    255 USTRING { 'encoding': PHONE_ENCODING,
                  'default': self.pathname } +tunename
    100 USTRING { 'encoding': PHONE_ENCODING,
                  'default': 'Unknown' } +artistname
    100 USTRING { 'encoding': PHONE_ENCODING,
                  'default': 'Unknown' } +albumname
    102 USTRING { 'encoding': PHONE_ENCODING,
                  'default': 'Unknown' } +genre
    4 UINT { 'default': 2 } +dunno1
    4 GPSDATE { 'default': GPSDATE.now() } +date
    4 UINT size
    4 UINT { 'default': 0 } +zero

PACKET PLPlayListFile:
    * LIST { 'elementclass': PLSongEntry,
             'createdefault': True } +items

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
    * LIST {'length': 219} +msg:
        1 UINT byte "individual byte of message"

PACKET recipient_record:
    33 DATA unknown1 # contains recipient name from phonebook on this phone
    50 USTRING number
    1 UINT status   # 1 when sent, 5 when received
    3 UNKNOWN dunno1
    4 LGCALDATE timesent
    4 LGCALDATE timereceived
    1 UINT unknown2 # 0 when not received, set to 1 when received
    57 DATA unknown3

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
    8 UNKNOWN unknown1
    1 UINT priority # 0=normal, 1=high
    16 UNKNOWN unknown5
    73 USTRING callback
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
    1 UINT read
    1 UINT locked
    1 UINT priority
    6 UNKNOWN dunno1
    23 USTRING {'encoding': PHONE_ENCODING,
                'raiseonunterminatedread': False } subject
    47 UNKNOWN dunno2
    1 UINT num_msg_elements # max 10 elements (guessing on max here)
    * LIST {'length': 10} +msglengths:
        1 UINT msglength "lengths of individual messages in septets"
    10 UNKNOWN unknown9
    * LIST {'length': 10, 'elementclass': SMSINBOXMSGFRAGMENT} +msgs
    2594 UNKNOWN dunno3
    1 UINT sender_length
    * LIST {'length': 49} +sender:
        1 UINT byte "individual byte of senders phone number"
    3 UNKNOWN dunno4
    1 UINT callback_length # 0 for no callback number
    55 USTRING callback
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

# Misc stuff
PACKET LockKeyReq:
    1 UINT { 'default': 0x21 } +cmd
    2 UINT { 'default': 0 } +lock "0=Lock, 1=Unlock"

PACKET KeyPressReq:
     1 UINT { 'default': 0x20 } +cmd
     1 UINT { 'default': 0 } +hold
     1 STRING { 'terminator': None,
                'sizeinbytes': 1 } key

# T9 User Database
    
PACKET t9udbfile:
    2 UINT { 'default': 0x5000 } +file_length
    6 DATA { 'default': '\x7B\x1B\x00\x00\x01\x00' } +unknown1
    2 UINT word_count
    2 UINT { 'default': 0x00 } +unknown2
    2 UINT free_space
    10 DATA { 'default': Default_Header } +unknown3
    2 UINT { 'default': 0 } +extra_cnt
    18 DATA { 'default': Default_Header2 } +unknown4
    if self.extra_cnt:
        * LIST { 'length': self.extra_cnt } +extras:
            1 UINT { 'default': 0 } +extra
    1 UINT { 'constant': 0xA0 } +A0
    * LIST { 'createdefault': True } +blocks:
        * T9USERDBBLOCK block

# DM stuff
PACKET DMKeyReq:
    1 UINT { 'default': 0xFE } +cmd
    6 STRING { 'terminator': None,
               'default': '\x00\x00\x00\x00\x00\x00' } +body
PACKET DMKeyResp:
    1 UINT cmd
    1 UINT code
    4 UINT key
    1 UINT one

PACKET DMReq:
    1 UINT { 'default': 0xFE } +cmd
    1 UINT { 'default': 1 } +one
    4 UINT key
    1 UINT { 'default': 0 } +zero
PACKET DMResp:
    1 UINT cmd
    1 UINT one
    4 UINT key
    1 UINT zero2one
