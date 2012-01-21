### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgc2000.p 3927 2007-01-22 03:15:22Z rogerb $

%{

"""Various descriptions of data specific to LG C2000"""

from prototypes import *
from prototypeslg import *

# Make all lg stuff available in this module as well
from p_etsi import *
from p_lg import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

# general constants
MEDIA_RINGTONE=0
MEDIA_WALLPAPER=1
MEDIA_PHOTO=6
GROUP_INDEX_RANGE=xrange(8)
MIN_RINGTONE_INDEX=0
MAX_RINGTONE_INDEX=19
MIN_WALLPAPER_INDEX=0
MAX_WALLPAPER_INDEX=19
MIN_PHOTO_INDEX=0
MAX_PHOTO_INDEX=19
CHARSET_IRA='IRA'
CHARSET_BASE64='Base64'
CHARSET_GSM='GSM'
CHARSET_HEX='HEX'
CHARSET_PCCP437='PCCP437'
CHARSET_PCDN='PCDN'
CHARSET_8859_1='8859-1'
CHARSET_UCS2='UCS2'

# Calendar constants
CAL_TOTAL_ENTRIES=30
CAL_MIN_INDEX=0
CAL_MAX_INDEX=29
CAL_DESC_LEN=30

CAL_REP_NONE=0
CAL_REP_DAILY=1
CAL_REP_WEEKLY=2
CAL_REP_MONTHLY=3
CAL_REP_YEARLY=4

CAL_ALARM_NONE=0
CAL_ALARM_ONTIME=1
CAL_ALARM_15MIN=2
CAL_ALARM_30MIN=3
CAL_ALARM_1HR=4
CAL_ALARM_1DAY=5
CAL_ALARM_VALUE={
    CAL_ALARM_NONE: -1,
    CAL_ALARM_ONTIME: 0,
    CAL_ALARM_15MIN: 15,
    CAL_ALARM_30MIN: 30,
    CAL_ALARM_1HR: 60,
    CAL_ALARM_1DAY: 1440 }
CAL_ALARM_LIST=((1440, CAL_ALARM_1DAY), (60, CAL_ALARM_1HR),
                (30, CAL_ALARM_30MIN), (15, CAL_ALARM_15MIN),
                (0, CAL_ALARM_ONTIME), (-1, CAL_ALARM_NONE))

# Phonebook constans
PB_MEMORY_SIM='AD'
PB_MEMORY_MAIN='ME'
PB_MEMORY_LAST_DIALED='LD'
PB_MEMORY_LAST_RECEIVED='LR'
PB_MEMORY_LAST_MISSED='LM'
PB_MAIN_TOTAL_ENTRIES=255
PB_MAIN_MIN_INDEX=1
PB_MAIN_MAX_INDEX=254
PB_SIM_TOTAL_ENTRIES=250
PB_SIM_MIN_INDEX=1
PB_SIM_MAX_INDEX=250
PB_NUMBER_LEN=40    # max size of a number string
PB_NAME_LEN=20      # max size of a contact name
PB_EMAIL_LEN=40
PB_MEMO_LEN=50
PB_SIM_NAME_LEN=16
PB_LD_MIN_INDEX=1
PB_LD_MAX_INDEX=10
PB_LR_MIN_INDEX=1
PB_LR_MAX_INDEX=20
PB_LM_MIN_INDEX=1
PB_LM_MAX_INDEX=10
PB_CALL_HISTORY_INFO=(
    ('Getting Last Dialed Calls', PB_MEMORY_LAST_DIALED,
     PB_LD_MIN_INDEX, PB_LD_MAX_INDEX),
    ('Getting Last Received Calls', PB_MEMORY_LAST_RECEIVED,
     PB_LR_MIN_INDEX, PB_LR_MAX_INDEX),
    ('Getting Missed Calls', PB_MEMORY_LAST_MISSED,
     PB_LM_MIN_INDEX, PB_LM_MAX_INDEX))

# Memo constants
MEMO_MIN_INDEX=0
MEMO_MAX_INDEX=19
MEMO_READ_CMD='+CMDR'
MEMO_WRITE_CMD='+CMDW'

# SMS Constants
SMS_MEMORY_PHONE='ME'
SMS_MEMORY_SIM='SM'
SMS_MEMORY_SELECT_CMD='+CPMS'
SMS_FORMAT_TEXT=1
SMS_FORMAT_PDU=0
SMS_FORMAT_CMD='+CMGF'
SMS_MSG_REC_UNREAD='REC UNREAD'
SMS_MSG_REC_READ='REC READ'
SMS_MSG_STO_UNSENT='STO UNSENT'
SMS_MSG_STO_SENT='STO SENT'
SMS_MSG_ALL='ALL'
SMS_MSG_LIST_CMD='+CMGL'

%}

# calendar packets
PACKET calendar_read_req:
    * USTRING { 'terminator': None, 'default': '+CXDR=' } +command
    * CSVINT +start_index
    * CSVINT { 'terminator': None } +end_index

PACKET calendar_read_resp:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'constant': '+CXDR:'} command
    * CSVINT index
    * CSVINT repeat
    * CSVINT alarm
    * GSMCALDATE date
    * GSMCALTIME time
    * CSVSTRING { 'terminator': None } description

PACKET calendar_write_check_req:
    * USTRING { 'terminator': None, 'default': '+CXDW' } +command
PACKET calendar_write_check_resp:
    * USTRING { 'terminator': ord(' '), 'constant': '+CXDW:' } command
    * CSVINT { 'terminator': None } index

PACKET calendar_write_req:
    * USTRING { 'terminator': None, 'default': '+CXDW=' } +command
    * CSVINT +index
    * CSVINT +repeat
    * CSVINT +alarm
    * GSMCALDATE +date
    * GSMCALTIME +time
    * CSVSTRING { 'terminator': None,
                  'maxsizeinbytes': CAL_DESC_LEN,
                  'raiseontruncate': False } +description
PACKET calendar_del_req:
    * USTRING { 'terminator': None, 'default': '+CXDW=' } +command
    * CSVINT { 'terminator': None } +index

# Media packets
PACKET media_selector_req:
    * USTRING { 'terminator': None, 'default': '+DDLS?' } +command
PACKET media_selector_resp:
    * USTRING { 'terminator': ord(' '), 'constant': '+DDLS:' } command
    * CSVINT { 'terminator': None } media_type

PACKET media_selector_set:
    * USTRING { 'terminator': None, 'default': '+DDLS=' } +command
    * CSVINT { 'terminator': None } +media_type

PACKET media_list_req:
    * USTRING { 'terminator': None, 'default': '+DDLR=' } +command
    * CSVINT +start_index
    * CSVINT { 'terminator': None } +end_index

PACKET media_list_resp:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'constant': '+DDLR:'} command
    * CSVINT index
    * CSVSTRING file_name
    * CSVSTRING media_name
    * CSVINT size

PACKET del_media_req:
    * USTRING { 'terminator': None, 'default': '+DDLD=0,' } +command
    * CSVSTRING { 'terminator': None } +file_name

PACKET write_media_req:
    * USTRING { 'terminator': None, 'default': '+DDLW=' } +command
    * CSVINT +index
    * CSVSTRING +file_name
    * CSVSTRING +media_name
    * CSVINT data_len
    * CSVINT media_type
    * CSVINT { 'default': 0 } +dunno1    # width?
    * CSVINT { 'default': 0 } +dunno2    # height?
    * CSVINT { 'default': 0 } +dunno3    # #of colors?
    * CSVINT { 'default': 0, 'terminator': ord('\r') } +dunno4
#    * USTRING { 'terminator': None } +data

# Phonebook packets
PACKET list_group_req:
    * USTRING { 'terminator': None, 'default': '+CPGR=' } +command
    * CSVINT +start_index
    * CSVINT { 'terminator': None } +end_index

PACKET list_group_resp:
    * USTRING { 'terminator': ord(' '), 'constant': '+CPGR:' } command
    * CSVINT index
    * CSVSTRING { 'terminator': None } group_name

PACKET charset_set_req:
    * USTRING { 'terminator': None, 'default': '+CSCS=' } +command
    * CSVSTRING { 'terminator': None } +charset

PACKET select_storage_req:
    * USTRING { 'terminator': None, 'default': '+CPBS=' } +command
    * CSVSTRING { 'terminator': None } +storage

PACKET select_storage_resp:
    * USTRING { 'terminator': ord(' '), 'constant': '+CPBS:' } command
    * CSVSTRING storage
    * CSVINT used_slots_count
    * CSVINT total_slots_count
    * CSVINT { 'terminator': None } dunno

PACKET read_phonebook_req:
    * USTRING { 'terminator': None, 'default': '+CPBR=' } +command
    * CSVINT +start_index
    * CSVINT { 'terminator': None } +end_index
    
PACKET read_phonebook_resp:
    P BOOL { 'default': False } +sim
    * USTRING { 'terminator': ord(' '), 'constant': '+CPBR:' } command
    * CSVINT index
    * CSVINT group
    * CSVSTRING mobile
    * CSVINT mobile_type
    * CSVSTRING home
    * CSVINT home_type
    * CSVSTRING office
    * CSVINT office_type
    * CSVSTRING name
    * CSVSTRING email
    * CSVSTRING memo

PACKET read_sim_phonebook_resp:
    * USTRING { 'terminator': ord(' '), 'constant': '+CPBR:' } command
    * CSVINT index
    * CSVINT group
    * CSVSTRING mobile
    * CSVINT mobile_type
    * CSVSTRING name
    P USTRING { 'terminator': None, 'default': '' } +home
    P USTRING { 'terminator': None, 'default': '' } +office
    P USTRING { 'terminator': None, 'default': '' } +email
    P USTRING { 'terminator': None, 'default': '' } +memo
    P BOOL { 'default': True } +sim

PACKET del_phonebook_req:
    * USTRING { 'terminator': None, 'default': '+CPBW=' } +command
    * CSVINT { 'terminator': None } +index

PACKET update_phonebook_resp:
    * USTRING { 'terminator': ord(' '), 'constant': '+CPBW:' } command
    * CSVINT { 'terminator': None } index

PACKET write_phonebook_req:
    * USTRING { 'terminator': None, 'default': '+CPBW=,' } +command
    * CSVINT +group
    * CSVSTRING { 'default': '',
                  'maxsizeinbytes': PB_NUMBER_LEN,
                  'raiseontruncate': False } +mobile
    * CSVINT { 'default': 255 } +mobile_type
    * CSVSTRING { 'default': '',
                  'maxsizeinbytes': PB_NUMBER_LEN,
                  'raiseontruncate': False } +home
    * CSVINT { 'default': 255 } +home_type
    * CSVSTRING { 'default': '',
                  'maxsizeinbytes': PB_NUMBER_LEN,
                  'raiseontruncate': False } +office
    * CSVINT { 'default': 255 } +office_type
    * CSVSTRING { 'maxsizeinbytes': PB_NAME_LEN,
                  'raiseontruncate': False } +name
    * CSVSTRING { 'default': '',
                  'maxsizeinbytes': PB_EMAIL_LEN,
                  'raiseontruncate': False } +email
    * CSVSTRING { 'terminator': None, 'default': '',
                  'maxsizeinbytes': PB_MEMO_LEN,
                  'raiseontruncate': False } +memo

PACKET write_sim_phonebook_req:
    * USTRING { 'terminator': None, 'default': '+CPBW=,' } +command
    * CSVINT { 'default': 0 } +group
    * CSVSTRING { 'default': '',
                  'maxsizeinbytes': PB_NUMBER_LEN,
                  'raiseontruncate': False } +number
    * CSVINT { 'default': 255 } +number_type
    * CSVSTRING { 'terminator': None,
                  'maxsizeinbytes': PB_SIM_NAME_LEN,
                  'raiseontruncate': False } +name

# Memo packets
PACKET memo_read_req:
    * USTRING { 'terminator': None,
               'default': MEMO_READ_CMD+'=' } +command
    * CSVINT { 'default': MEMO_MIN_INDEX } +start_index
    * CSVINT { 'terminator': None,
               'default': MEMO_MAX_INDEX } +end_index

PACKET memo_read_resp:
    * USTRING { 'terminator': ord(' '),
               'constant': MEMO_READ_CMD+':' } command
    * CSVINT index
    * CSVSTRING { 'terminator': None } text

PACKET memo_write_req:
    * USTRING { 'terminator': None,
               'default': MEMO_WRITE_CMD+'=,' } +command
    * CSVSTRING { 'terminator': None } +text

PACKET memo_del_req:
    * USTRING { 'terminator': None,
               'default': MEMO_WRITE_CMD+'=' } +command
    * CSVINT { 'terminator': None } +index

# SMS packets
PACKET sms_format_req:
    * USTRING { 'terminator': None,
               'default': SMS_FORMAT_CMD+'=' } +command
    * CSVINT { 'terminator': None,
               'default': SMS_FORMAT_TEXT } +format

PACKET sms_memory_select_req:
    * USTRING { 'terminator': None,
               'default': SMS_MEMORY_SELECT_CMD+'=' } +command
    * CSVSTRING { 'terminator': None } +list_memory

PACKET sms_msg_list_req:
    * USTRING { 'terminator': None,
               'default': SMS_MSG_LIST_CMD+'=' } +command
    * CSVSTRING { 'terminator': None,
                  'default': SMS_MSG_ALL } +msg_type

PACKET sms_msg_list_header:
    * USTRING { 'terminator': ord(' '),
               'constant': SMS_MSG_LIST_CMD+':' } command
    * CSVINT index
    * CSVSTRING msg_type
    * CSVSTRING address
    * CSVSTRING address_name
    * SMSDATETIME timestamp
    * CSVINT address_type
    * CSVINT { 'terminator': None } data_len
