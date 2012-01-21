### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id:  $

%{

"""Various descriptions of data specific to Motorola phones"""

from prototypes import *
from prototypes_moto import *
from p_etsi import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

# charset constant
CHARSET_8859_1="8859-1"
CHARSET_8859_A="8859-A"
CHARSET_8859_C="8859-C"
CHARSET_8859_H="8859-H"
CHARSET_ASCII="ASCII"
CHARSET_GSM="GSM"
CHARSET_KSC5601="KSC5601"
CHARSET_UCS2="UCS2"
CHARSET_UTF8="UTF8"

# phone mode constant
MODE_MODEM=0
MODE_PHONEBOOK=2
MODE_OBEX=22

# phonebook constant
PB_DIALED='DC'
PB_MISSED='MC'
PB_MAIN='AD'
PB_INCOMING='RC'
PB_QUICKDIAL='QD'

LOCAL_TYPE_LOCAL=129
LOCAL_TYPE_INTERNATIONAL=145
LOCAL_TYPE_UNKNOWN=128

NUMBER_TYPE_WORK=0
NUMBER_TYPE_HOME=1
NUMBER_TYPE_MAIN=2
NUMBER_TYPE_MOBILE=3
NUMBER_TYPE_FAX=4
NUMBER_TYPE_PAGER=5
NUMBER_TYPE_EMAIL=6
NUMBER_TYPE_MAILING_LIST=7
NUMBER_TYPE_MOBILE2=8
NUMBER_TYPE_EMAIL2=9
NUMBER_TYPE=frozenset([NUMBER_TYPE_WORK, NUMBER_TYPE_HOME, NUMBER_TYPE_MAIN,
                       NUMBER_TYPE_MOBILE, NUMBER_TYPE_FAX, NUMBER_TYPE_PAGER,
                       NUMBER_TYPE_MOBILE2])
EMAIL_TYPE=frozenset([NUMBER_TYPE_EMAIL, NUMBER_TYPE_EMAIL2])
NUMBER_TYPE_NAME={
    NUMBER_TYPE_WORK: 'office',
    NUMBER_TYPE_HOME: 'home',
    NUMBER_TYPE_MAIN: 'main',
    NUMBER_TYPE_MOBILE: 'cell',
    NUMBER_TYPE_FAX: 'fax',
    NUMBER_TYPE_PAGER: 'pager',
    NUMBER_TYPE_MOBILE2: 'cell',
    }
NUMBER_TYPE_CODE={
    'office': NUMBER_TYPE_WORK,
    'home': NUMBER_TYPE_HOME,
    'main': NUMBER_TYPE_MAIN,
    'cell': NUMBER_TYPE_MOBILE,
    'fax': NUMBER_TYPE_FAX,
    'pager': NUMBER_TYPE_PAGER }

PB_MAX_NUMBER_LEN=32
PB_MAX_NAME_LEN=24
PB_MAX_EMAIL_LEN=48

PB_TOTAL_ENTRIES=500
PB_RANGE=xrange(1,PB_TOTAL_ENTRIES+1)
PB_TOTAL_MISSED_CALLS=60
PB_TOTAL_DIALED_CALLS=60
PB_TOTAL_RECEIVED_CALLS=60

PB_TOTAL_GROUP=30
PB_GROUP_RANGE=xrange(1, PB_TOTAL_GROUP+1)
PB_GROUP_NAME_LEN=24

RT_BUILTIN=0x0C
RT_CUSTOM=0x0D
RT_INDEX_FILE='/MyToneDB.db'

# SMS Stuff
SMS_INBOX="IM"
SMS_OUTBOX="OM"
SMS_INFO="BM"
SMS_DRAFTS="DM"
SMS_COMBINE="MT"

SMS_REC_UNREAD="REC UNREAD"
SMS_REC_READ="REC READ"
SMS_STO_UNSENT="STO UNSENT"
SMS_STO_SENT="STO SENT"
SMS_ALL="ALL"
SMS_HEADER_ONLY="HEADER ONLY"

SMS_INDEX_RANGE=xrange(1, 353)

%}

# Misc Phone Info stuff
PACKET esnrequest:
    * CSVSTRING { 'quotechar': None, 'terminator': None,
                  'default': '+CGSN' } +command

PACKET esnresponse:
    * CSVSTRING { 'quotechar': None, 'terminator': ord(' '),
                  'default': '+CGSN:' } command
    3 DATA esnlabel
    * CSVSTRING { 'quotechar': None, 'terminator': None } esn

PACKET string_resp:
    * CSVSTRING { 'quotechar': None,
                  'terminator': ord(' ') } command
    * CSVSTRING { 'quotechar': None,
                  'terminator': None } value

PACKET manufacturer_req:
    * CSVSTRING { 'quotechar': None, 'terminator': None,
                  'default': '+GMI' } +command
PACKET model_req:
    * CSVSTRING { 'quotechar': None, 'terminator': None,
                  'default': '+GMM' } +command
PACKET number_req:
    * CSVSTRING { 'quotechar': None, 'terminator': None,
                  'default': '+CNUM' } +command
PACKET firmware_req:
    * CSVSTRING { 'quotechar': None, 'terminator': None,
                  'default': '+GMR' } +command
PACKET signal_req:
    * CSVSTRING { 'quotechar': None, 'terminator': None,
                  'default': '+CSQ?' } +command
PACKET signal_resp:
    * CSVSTRING { 'quotechar': None,
                  'terminator': ord(' ') } command
    * CSVINT rssi
    * CSVINT { 'terminator': None } ber
PACKET battery_req:
    * CSVSTRING { 'quotechar': None, 'terminator': None,
                  'default': '+CBC' } +command
PACKET battery_resp:
    * CSVSTRING { 'quotechar': None,
                  'terminator': ord(' ') } command
    * CSVINT status
    * CSVINT { 'terminator': None } level

PACKET modereq:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+MODE?' } +command
PACKET moderesp:
    * CSVSTRING { 'quotechar': None, 'terminator': ord(' '),
                  'default': '+MODE:' } command
    * CSVINT { 'terminator': None } mode
PACKET modeset:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+MODE=' } +command
    * CSVINT { 'terminator': None, 'default': 0 } +mode

PACKET charset_set_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+CSCS=' } +command
    * CSVSTRING { 'terminator': None } +charset

PACKET featurereq:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+MAID?' } +command
PACKET featureresp:
    * CSVSTRING { 'quotechar': None, 'terminator': ord(' '),
                  'default': '+MAID:' } command
    * CSVINT has_phonebook
    * CSVINT has_datebook
    * CSVINT has_sms
    * CSVINT has_mo_sms
    * CSVINT has_email
    * CSVINT has_multi_phonebooks
    * CSVINT has_sim
    * CSVINT has_shared_phonebook
    * CSVINT has_multi_dest_addr
    * CSVINT has_ringtone_id
    * CSVINT has_voicetag
    * CSVSTRING { 'quotechar': None,
                  'terminator': None } +dunno

# Phonebook stuff

PACKET select_phonebook_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+CPBS=' } +command
    * CSVSTRING { 'terminator': None,
                  'default': PB_MAIN } +pb_type

PACKET read_pb_simple_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+CPBR=' } +command
    * CSVINT { 'default': 1 } +start_index
    * CSVINT { 'terminator': None,
               'default': self.start_index } +end_index
PACKET read_pb_simple_resp:
    * CSVSTRING { 'quotechar': None, 'terminator': ord(' '),
                  'default': '+CPBR:' } +command
    * CSVINT index
    * CSVSTRING number
    * CSVINT local_type
    * CSVSTRING { 'terminator': None } name

PACKET read_pb_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+MPBR=' } +command
    * CSVINT { 'default': 1 } +start_index
    * CSVINT { 'terminator': None,
               'default': self.start_index } +end_index
PACKET read_pb_resp:
    * CSVSTRING { 'quotechar': None, 'terminator': ord(' '),
                  'default': '+MPBR:' } command
    * CSVINT index
    * CSVSTRING number
    * CSVINT local_type
    * CSVSTRING name
    * CSVINT number_type
    * CSVINT voice_tag
    * CSVINT ringtone
    * CSVINT backlight
    * CSVINT is_primary
    * CSVINT group
    * CSVINT icon
    * CSVINT first_last_enabled
    * CSVINT subfield_index
    * CSVSTRING picture_name
    * CSVSTRING { 'quotechar': None, 'terminator': None } dunno

PACKET write_pb_req:
    * CSVSTRING { 'quotechar': None, 'terminator': None,
                  'default': '+MPBW=' } +command
    * CSVINT index
    * CSVSTRING { 'maxsizeinbytes': PB_MAX_NUMBER_LEN,
                  'raiseontruncate': False } number
    * CSVINT { 'default': LOCAL_TYPE_LOCAL } +local_type
    * CSVSTRING { 'maxsizeinbytes': PB_MAX_NAME_LEN,
                  'raiseontruncate': False } name
    * CSVINT number_type
    * CSVINT { 'default': 0 } +voice_tag
    * CSVINT { 'default': 255 } +ringtone
    * CSVINT { 'default': 0 } +backlight
    * CSVINT { 'default': 0 } +is_primary
    * CSVINT { 'default': 1 } +group
    * CSVINT { 'default': 255 } +icon
    * CSVINT { 'default': 255 } +first_last_enabled
    * CSVINT { 'default': 0 } +subfield_index
    * CSVSTRING { 'terminator': None,
                  'default': "" } +picture_name

PACKET del_pb_req:
    * CSVSTRING { 'quotechar': None, 'terminator': None,
                  'default': '+MPBW=' } +command
    * CSVINT { 'terminator': None } index

# SMS Stuff
PACKET sms_sel_req:
    * CSVSTRING { 'quotechar': None, 'terminator': None,
                  'default': '+CPMS=' } +command
    * CSVSTRING { 'default': SMS_COMBINE } +mem1
    * CSVSTRING { 'default': SMS_OUTBOX } +mem2
    * CSVSTRING { 'terminator': None,
                  'default': SMS_INBOX } +mem3

PACKET sms_m_read_resp:
    * CSVSTRING { 'quotechar': None,
                  'terminator': ord(' '),
                  'default': '+MMGR:' } command
    P BOOL { 'default': True } +has_date
    P BOOL { 'default': False } +date_terminated
    * CSVSTRING sms_type
    if self.has_date:
        * CSVSTRING { 'quotechar': None } sms_addr
        if self.date_terminated:
            * M_SMSDATETIME sms_date
        else:
            * M_SMSDATETIME { 'quotechar': None,
                              'terminator': None } sms_date
    else:
        * CSVSTRING { 'terminator': None,
                      'quotechar': None } sms_addr

PACKET sms_list_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None,
                  'default': '+MMGL=' } +command
    * CSVSTRING { 'terminator': None,
                  'default': SMS_HEADER_ONLY } +listtype

PACKET sms_list_resp:
    * CSVSTRING { 'quotechar': None,
                  'terminator': ord(' '),
                  'default': '+MMGL:' } command
    * CSVINT index
    * DATA dontcare
