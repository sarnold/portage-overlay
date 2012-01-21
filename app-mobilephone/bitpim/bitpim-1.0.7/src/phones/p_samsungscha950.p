### BITPIM
###
### Copyright (C) 2006 Joe Pham<djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsungscha950.p 4776 2010-01-05 02:11:15Z djpham $

%{

"""Various descriptions of data specific to the Samsung SCH-A950 Phone"""

from prototypes import *
from prototypes_samsung import *
from p_brew import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

ENCODING='latin_1'

RT_PATH='brew/16452/mr'
RT_PATH2='brew/16452/lk/mr'
RT_INDEX_FILE_NAME=RT_PATH+'/MrInfo.db'
RT_EXCLUDED_FILES=('MrInfo.db',)
SND_PATH='brew/16452/ms'
SND_PATH2='brew/16452/lk/ms'
SND_INDEX_FILE_NAME=SND_PATH+'/MsInfo.db'
SND_EXCLUDED_FILES=('MsInfo.db', 'ExInfo.db')
PIC_PATH='brew/16452/mp'
PIC_PATH2='brew/16452/lk/mp'
PIC_INDEX_FILE_NAME=PIC_PATH+'/Default Album.alb'
PIC_EXCLUDED_FILES=('Default Album.alb', 'Graphics.alb')
PREF_DB_FILE_NAME='current_prefs.db'

GROUP_INDEX_FILE_NAME='pb/pbgroups_'

# Calendar stuff
CAL_PATH='sch_event'
CAL_INDEX_FILE_NAME=CAL_PATH+'/usr_tsk'
CAL_FILE_NAME_PREFIX=CAL_PATH+'/usr_tsk_'
CAL_MAX_EVENTS=100

NP_MAX_ENTRIES=30
NP_MAX_LEN=130
NP_PATH=CAL_PATH
NP_FILE_NAME_PREFIX=CAL_FILE_NAME_PREFIX

# Phonebook stuff
PB_PATH='pb'
PB_JRNL_FILE_PREFIX=PB_PATH+'/jrnl_'
PB_ENTRY_FILE_PREFIX=PB_PATH+'/recs_'
PB_MAIN_FILE_PREFIX=PB_PATH+'/main_'
PB_WP_CACHE_PATH='cache/pb'
PB_WP_CACHE_WIDTH=128
PB_WP_CACHE_HEIGHT=96
PB_MAX_NAME_LEN=32
PB_MAX_EMAIL_LEN=48
PB_MAX_NUMBER_LEN=48

PB_FLG_NONE=0x0000
PB_FLG_NAME=0x0001
PB_FLG_DATE=0x0400
PB_FLG_FAX=0x0080
PB_FLG_CELL=0x0020
PB_FLG_WORK=0x0010
PB_FLG_HOME=0X0008
PB_FLG_EMAIL2=0X0004
PB_FLG_EMAIL=0X0002
PB_FLG_WP=0X8000
PB_FLG_GROUP=0X0800
PB_FLG_CELL2=0X0100
PB_FLG_SPEEDDIAL=0x01
PB_FLG_RINGTONE=0x10
PB_FLG_PRIMARY=0x02

# Samsung command code
SS_CMD_SW_VERSION=0
SS_CMD_HW_VERSION=1
SS_CMD_PB_COUNT=2
SS_CMD_PB_VOICEMAIL_READ=5
SS_CMD_PB_VOICEMAIL_WRITE=6
SS_CMD_PB_READ=0x14
SS_CMD_PB_WRITE=0x15
SS_CMD_PB_CLEAR=0x1D
SS_CMD_PB_VOICEMAIL_PARAM=0x19
PB_DEFAULT_VOICEMAIL_NUMBER='*86'

# Call log/history
CL_PATH='clog'
CL_PREFIX=CL_PATH+'/clog_'
CL_INDEX_FILE=CL_PATH+'/clog_master'
CL_MAX_ENTRIES=20
CL_TYPE_INCOMING=1
CL_TYPE_OUTGOING=2
CL_TYPE_MISSED=3
CL_TYPE_DELETED=5
CL_VALID_TYPE=frozenset((CL_TYPE_INCOMING, CL_TYPE_OUTGOING, CL_TYPE_MISSED))

# SMS stuff
SMS_PATH='nvm/sms_wp_os'

SMS_TXT_TYPE=0x0200
SMS_TYPE_IN=1
SMS_TYPE_SENT=3
SMS_TYPE_DRAFT=4
SMS_VALID_TYPE=(SMS_TYPE_IN, SMS_TYPE_SENT, SMS_TYPE_DRAFT)
SMS_FLG1_DEFERREDDEL=0x40
SMS_FLG1_VALIDPERIOD=0x10
SMS_FLG1_HAS40=SMS_FLG1_DEFERREDDEL | SMS_FLG1_VALIDPERIOD
SMS_FLG2_CALLBACK=0x40
SMS_FLG2_MSG=0x04
SMS_FLG2_PRIORITY=0x01
SMS_FLG2_SOMETHING=0x08
SMS_STATUS_SENT=0x10
SMS_STATUS_DELIVERED=0x11
SMS_STATUS_READ=0x05
SMS_STATUS_NOTREAD=0x01
SMS_STATUS_LOCKED=0x100

broken_filelist_date=True
%}

PACKET DefaultResponse:
    * DATA data

PACKET WRingtoneIndexEntry:
    P STRING name
    * STRING { 'terminator': None,
               'default': '/ff/' } +path_prefix
    * STRING { 'terminator': None } pathname
    * STRING { 'terminator': None,
               'default': '|2\x0A' } +eor
PACKET WRingtoneIndexFile:
    * LIST { 'elementclass': WRingtoneIndexEntry } +items

PACKET RRingtoneIndexEntry:
    * STRING { 'terminator': 0x7C } pathname
    * STRING { 'terminator': 0x0A } misc
PACKET RRingtoneIndexFile:
    * LIST { 'elementclass': RRingtoneIndexEntry } +items

PACKET WSoundsIndexEntry:
    P STRING name
    * STRING { 'terminator': None,
               'default': '/ff/' } +path_prefix
    * STRING { 'terminator': None } pathname
    * STRING { 'terminator': None,
               'default': '|0|7\x0A' } +eor
PACKET WSoundsIndexFile:
    * LIST { 'elementclass': WSoundsIndexEntry } +items
PACKET RSoundIndexEntry:
    * STRING { 'terminator': 0x7C } pathname
    * STRING { 'terminator': 0x0A } misc
PACKET RSoundsIndexFile:
    * LIST { 'elementclass': RSoundIndexEntry } +items

PACKET WPictureIndexEntry:
    * STRING { 'terminator': None } name
    * STRING { 'terminator': None,
               'default': '|/ff/' } +path_prefix
    * STRING { 'terminator': None } pathname
    * STRING { 'terminator': None,
               'default': '|0|0|3|>\x0A\xF4' } +eor
PACKET WPictureIndexFile:
    * STRING { 'terminator': None,
               'default': '0|/ff/brew/16452/mp/Default Album|\x0A\x0A\xF4' } +header
    * LIST { 'elementclass': WPictureIndexEntry } +items
PACKET RPictureIndexEntry:
    * STRING { 'terminator': 0x7C } name
    * STRING { 'terminator': 0x7C } pathname
    * STRING { 'terminator': 0xF4,
               'raiseonunterminatedread': False } misc
PACKET RPictureIndexFile:
    * LIST { 'elementclass': RPictureIndexEntry } +items

PACKET -GroupEntry:
    1 UINT index
    4 DONTCARE
    4 DateTime datetime
    68 USTRING { 'encoding': ENCODING,
                 'terminator': 0 } name
    2 UINT numofmembers
    if self.numofmembers:
        * LIST { 'length': self.numofmembers } members:
            2 UINT index
    
PACKET -GroupIndexFile:
    1 UINT num_of_entries
    * LIST { 'elementclass': GroupEntry } +items

PACKET CalIndexEntry:
    2 UINT { 'default': 0 } +index
PACKET CalIndexFile:
    2 UINT next_index
    12 UNKNOWN { 'pad': 0 } +zero1
    2 UINT numofevents
    6 UNKNOWN { 'pad': 0 } +zero2
    2 UINT numofnotes
    2 UNKNOWN { 'pad': 0 } +zero3
    2 UINT numofactiveevents
    112 UNKNOWN { 'pad': 0 } +zero4
    * LIST { 'elementclass': CalIndexEntry,
             'length': 103,
             'createdefault': True } +events
    * LIST { 'elementclass': CalIndexEntry,
             'length': 30,
             'createdefault': True } +notes
    * LIST { 'elementclass': CalIndexEntry,
             'length': 324,
             'createdefault': True } +activeevents

PACKET CalEntry:
    2 UINT titlelen
    * USTRING { 'sizeinbytes': self.titlelen,
                'encoding': ENCODING,
                'terminator': None } title
    4 DateTime start
    4 UNKNOWN { 'pad': 0 } +zero1
    4 DateTime { 'default': self.start } +start2
    4 UNKNOWN { 'pad': 0 } +zero2
    4 ExpiringTime exptime
    4 UNKNOWN { 'pad': 0 } +zero3
    1 UINT { 'default': 1 } +one
    1 UINT repeat
    1 UINT { 'default': 3 } +three
    1 UINT alarm
    1 UINT alert
    6 UNKNOWN { 'pad': 0 } +zero4
    4 UINT duration
    1 UINT timezone
    4 DateTime creationtime
    4 UNKNOWN { 'pad': 0 } +zero5
    4 DateTime modifiedtime
    4 UNKNOWN { 'pad': 0 } +zero6
    2 UINT ringtonelen
    * STRING { 'sizeinbytes': self.ringtonelen,
               'terminator': None } ringtone
    2 UNKNOWN { 'pad': 0 } +zero7

PACKET NotePadEntry:
    2 UINT textlen
    * USTRING { 'terminator': None,
                'encoding': ENCODING,
                'sizeinbytes': self.textlen } text
    4 DateTime creation
    4 UNKNOWN { 'pad': 0 } +zero1
    4 DateTime { 'default': self.creation } +creation2
    14 UNKNOWN { 'pad': 0 } +zero2
    1 UINT { 'default': 5 } +five
    13 UNKNOWN { 'pad': 0 } +zero3
    4 DateTime { 'default': self.creation } +modified
    4 UNKNOWN { 'pad': 0 } +zero4
    4 DateTime { 'default': self.modified } +modified2
    8 UNKNOWN { 'pad': 0 } +zero5

PACKET JournalNumber:
    2 UINT index
    2 UINT bitmap
PACKET JournalSpeeddial:
    2 UINT index
    2 UINT speeddial
    2 UINT bitmap
PACKET JournalEntry:
    P UINT { 'default': 0 } +number_info
    P UINT { 'default': 0 } +speeddial_info
    2 UINT index
    1 DATA { 'default': '\x00' } +data1
    2 UINT { 'default': self.index-1 } +previndex
    if self.number_info & PB_FLG_HOME:
        * JournalNumber home
    else:
        2 UINT { 'default': 0xffff } +nohome
    if self.number_info & PB_FLG_WORK:
        * JournalNumber work
    else:
        2 UINT { 'default': 0xffff } +nowork
    if self.number_info & PB_FLG_CELL:
        * JournalNumber cell
    else:
        2 UINT { 'default': 0xffff } +nocell
    2 UINT { 'default': 0xffff } +data2
    if self.number_info & PB_FLG_FAX:
        * JournalNumber fax
    else:
        2 UINT { 'default': 0xffff } +nofax
    if self.number_info&PB_FLG_CELL2:
        * JournalNumber cell2
    else:
        2 UINT { 'default': 0xffff } +nocell2
    if self.speeddial_info & PB_FLG_HOME:
        * JournalSpeeddial homesd
    else:
        2 UINT { 'default': 0xffff } +nohomesd
    if self.speeddial_info & PB_FLG_WORK:
        * JournalSpeeddial worksd
    else:
        2 UINT { 'default': 0xffff } +noworksd
    if self.speeddial_info&PB_FLG_CELL:
        * JournalSpeeddial cellsd
    else:
        2 UINT { 'default': 0xffff } +nocellsd
    2 UINT { 'default': 0xffff } +data3
    if self.speeddial_info&PB_FLG_FAX:
        * JournalSpeeddial faxsd
    else:
        2 UINT { 'default': 0xffff } +nofaxsd
    if self.speeddial_info&PB_FLG_CELL2:
        * JournalSpeeddial cell2sd
    else:
        2 UINT { 'default': 0xffff } +nocell2sd
    2 UINT { 'default': self.previndex } +previndex2
    2 UINT { 'default': self.previndex } +previndex3
    4 DATA { 'default': '\x10\x00\x0C\x04' } +data4
    2 UINT { 'default': 0xffff } +email
    2 UINT { 'default': 0xffff } +email2
    2 UINT { 'default': 0xffff } +wallpaper

PACKET JournalRec:
    1 UINT { 'default': 1 } +command
    2 UINT { 'default': 0 } +blocklen
    * JournalEntry entry

PACKET JournalFile:
    * LIST { 'elementclass': JournalRec } +items

PACKET -NumberEntry:
    * STRING { 'terminator': None,
               'pascal': True } number
    1 UINT option
    if self.has_speeddial:
        2 UINT speeddial
    if self.has_ringtone:
        * STRING { 'terminator': None,
                   'pascal': True } ringtone
    %{
    @property
    def has_speeddial(self):
        return bool(self.option & PB_FLG_SPEEDDIAL)
    @property
    def has_ringtone(self):
        return bool(self.option & PB_FLG_RINGTONE)
    @property
    def is_primary(self):
        return bool(self.option & PB_FLG_PRIMARY)
    %}

PACKET -PBEntry:
    2 UINT info
    2 DONTCARE
    if self.has_name:
        * USTRING { 'terminator': None,
                    'encoding': ENCODING,
                    'pascal': True } name
    if self.has_mail:
        * USTRING { 'terminator': None,
                    'encoding': ENCODING,
                    'pascal': True } email
    if self.has_email2:
        * USTRING { 'terminator': None,
                    'encoding': ENCODING,
                   'pascal': True } email2
    if self.has_home:
        * NumberEntry home
    if self.ihas_work:
        * NumberEntry work
    if self.has_cell:
        * NumberEntry cell
    if self.has_fax:
        * NumberEntry fax
    if self.has_cell2:
        * NumberEntry cell2
    if self.has_date:
        4 DateTime datetime
    if self.has_group:
        1 UINT group
    if self.has_wallpaper:
        * STRING { 'terminator': None,
                   'pascal': True } wallpaper
        4 UINT wallpaper_range
    %{
    @property
    def has_name(self):
        return bool(self.info & PB_FLG_NAME)
    @property
    def has_email(self):
        return bool(self.info & PB_FLG_EMAIL)
    @property
    def has_email2(self):
        return bool(self.info & PB_FLG_EMAIL2)
    @property
    def has_home(self):
        return bool(self.info & PB_FLG_HOME)
    @property
    def has_work(self):
        return bool(self.info & PB_FLG_WORK)
    @property
    def has_cell(self):
        return bool(self.info & PB_FLG_CELL)
    @property
    def has_fax(self):
        return bool(self.info & PB_FLG_FAX)
    @property
    def has_cell2(self):
        return bool(self.info & PB_FLG_CELL2)
    @property
    def has_date(self):
        return bool(self.info & PB_FLG_DATE)
    @property
    def has_group(self):
        return bool(self.info & PB_FLG_GROUP)
    @property
    def has_wallpaper(self):
        return bool(self.info & PB_FLG_WP)
    %}

PACKET -LenEntry:
    2 UINT { 'default': 0 } +itemlen

PACKET -PBFile:
    * LIST { 'elementclass': LenEntry,
             'length': 8,
             'createdefault': True } +lens
    * LIST { 'elementclass': PBEntry } +items

PACKET -PBFileHeader:
    * LIST { 'elementclass': LenEntry,
             'length': 8,
             'createdefault': True } +lens

PACKET ss_cmd_hdr:
    4 UINT { 'default': 0xfa4b } +commandcode
    1 UINT command

PACKET -ss_cmd_resp:
    * ss_cmd_hdr cmd_hdr
    * DATA data

PACKET ss_sw_req:
    * ss_cmd_hdr { 'command': SS_CMD_SW_VERSION } +hdr
PACKET -ss_sw_resp:
    * ss_cmd_hdr hdr
    * STRING { 'terminator': 0 } sw_version
PACKET ss_hw_req:
    * ss_cmd_hdr { 'command': SS_CMD_HW_VERSION } +hdr
PACKET -ss_hw_resp:
    * ss_cmd_hdr hdr
    * STRING { 'terminator': 0 } hw_version

PACKET ss_pb_count_req:
    * ss_cmd_hdr { 'command': SS_CMD_PB_COUNT } +hdr
PACKET -ss_pb_count_resp:
    * ss_cmd_hdr hdr
    1 DONTCARE
    2 UINT count
PACKET ss_pb_read_req:
    * ss_cmd_hdr { 'command': SS_CMD_PB_READ } +hdr
    1 DONTCARE +
    2 UINT index
PACKET -ss_pb_read_resp:
    * ss_cmd_hdr hdr
    1 DONTCARE
    2 UINT index
    1 DONTCARE
    * DATA data
PACKET ss_pb_voicemail_read_req:
    * ss_cmd_hdr { 'command': SS_CMD_PB_VOICEMAIL_READ } +hdr
    1 UINT { 'constant': SS_CMD_PB_VOICEMAIL_PARAM } +param
PACKET -ss_pb_voicemail_resp:
    * ss_cmd_hdr hdr
    1 UINT param
    * STRING { 'terminator': 0 } number
PACKET ss_pb_voicemail_write_req:
    * ss_cmd_hdr { 'command': SS_CMD_PB_VOICEMAIL_WRITE } +hdr
    1 UINT { 'constant': SS_CMD_PB_VOICEMAIL_PARAM } +param
    * STRING { 'terminator': 0,
               'default': PB_DEFAULT_VOICEMAIL_NUMBER } +number
PACKET ss_pb_clear_req:
    * ss_cmd_hdr { 'command': SS_CMD_PB_CLEAR } +hdr
PACKET -ss_pb_clear_resp:
    * ss_cmd_hdr hdr
    2 UINT flg

PACKET ss_number_entry:
    * STRING { 'terminator': 0,
               'default': '',
               'maxsizeinbytes': PB_MAX_NUMBER_LEN,
               'raiseontruncate': False } +number
    2 UINT { 'default': 0 } +speeddial
    1 UINT { 'default': 0 } +primary
    8 DONTCARE +
    * STRING { 'terminator': 0,
               'default': '' } +ringtone

PACKET ss_pb_entry:
    * USTRING { 'terminator': 0,
                'maxsizeinbytes': PB_MAX_NAME_LEN,
                'encoding': ENCODING,
                'raiseontruncate': False } name
    * USTRING { 'terminator': 0,
                'encoding': ENCODING,
                'default': '',
                'maxsizeinbytes': PB_MAX_EMAIL_LEN,
                'raiseontruncate': False } +email
    * USTRING { 'terminator': 0,
                'encoding': ENCODING,
                'default': '',
                'maxsizeinbytes': PB_MAX_EMAIL_LEN,
                'raiseontruncate': False } +email2
    4 DONTCARE +
    * STRING { 'terminator': 0,
               'default': '' } +wallpaper
    1 DONTCARE +
    * ss_number_entry +home
    * ss_number_entry +work
    * ss_number_entry +cell
    * ss_number_entry +dummy
    * ss_number_entry +fax
    * ss_number_entry +cell2
    4 DONTCARE +
    1 UINT { 'default': 0 } +group
    2 DONTCARE +
    
PACKET ss_pb_write_req:
    * ss_cmd_hdr { 'command': SS_CMD_PB_WRITE } +hdr
    1 UINT { 'default': 0 } +zero
    * ss_pb_entry entry

PACKET ss_pb_write_resp:
    * ss_cmd_hdr hdr
    1 DONTCARE
    2 UINT index

# Call History
PACKET -cl_list:
    1 UINT index

PACKET -cl_index_file:
    * LIST { 'length': CL_MAX_ENTRIES,
             'elementclass': cl_list } incoming
    * LIST { 'length': CL_MAX_ENTRIES,
             'elementclass': cl_list } outgoing
    * LIST { 'length': CL_MAX_ENTRIES,
             'elementclass': cl_list } missed
    111 DONTCARE
    4 UINT incoming_count
    4 UINT outgoing_count
    4 UINT missed_count

PACKET -cl_file:
    1 UINT cl_type
    51 STRING { 'terminator': 0 } number
    4 DateTime1 datetime
    4 DONTCARE
    4 UINT duration
    %{
    @property
    def valid(self):
        global CL_VALID_TYPE
        return bool(self.cl_type in CL_VALID_TYPE and self.number)
    %}

# SMS Stuff
PACKET pBOOL:
    P BOOL value

PACKET -sms_header:
    2 UINT index
    1 UINT msg_len
    1 UINT callback_len
    1 UINT bitmap1
    1 UINT bitmap2
    6 DONTCARE
    2 UINT body_len
    2 UINT file_type
    1 UINT msg_type
    1 UINT enhance_delivery
    * pBOOL { 'value': self.file_type==SMS_TXT_TYPE and self.msg_type in SMS_VALID_TYPE } is_txt_msg
    * pBOOL { 'value': self.msg_type==SMS_TYPE_IN } in_msg
    * pBOOL { 'value': self.msg_type==SMS_TYPE_SENT } sent_msg
    * pBOOL { 'value': self.msg_type==SMS_TYPE_DRAFT } draft_msg
    if self.is_txt_msg.value:
        * sms_body {
            'msg_len': self.msg_len,
            'has_callback': self.bitmap2 & SMS_FLG2_CALLBACK,
            'has_priority': self.bitmap2 & SMS_FLG2_PRIORITY,
            'has_1byte': self.bitmap2 & SMS_FLG2_SOMETHING,
            'has_1byte2': self.bitmap2 & SMS_FLG2_MSG,
            'has_40bytes': self.bitmap1 & SMS_FLG1_HAS40 } body

PACKET -sms_msg_stat_list:
    1 UINT status
PACKET -sms_datetime_list:
    4 DateTime1 datetime
    4 DONTCARE
PACKET -sms_delivered_datetime:
    * LIST { 'elementclass': sms_datetime_list,
             'length': 10 } datetime
    20 DONTCARE
PACKET -sms_body:
    P UINT msg_len
    P BOOL { 'default': True } +has_callback
    P BOOL { 'default': False } +has_priority
    P BOOL { 'default': False } +has_1byte
    P BOOL { 'default': True } +has_1byte2
    P BOOL { 'default': False } +has_40bytes
    50 DONTCARE
    * USTRING { 'sizeinbytes': self.msg_len,
                'encoding': ENCODING,
                'terminator': None } msg
    if self.has_callback:
        3 UNKNOWN dunno2
        1 UINT callback_len
        * STRING { 'sizeinbytes': self.callback_len,
                   'terminator': None } callback
    if self.has_priority:
        1 UINT priority
    if self.has_1byte:
        1 DONTCARE
    40 DONTCARE
    4 DateTime1 datetime
    17 DONTCARE
    1 UINT addr_len0
    1 UINT addr_len1
    1 UINT addr_len2
    1 UINT addr_len3
    1 UINT addr_len4
    1 UINT addr_len5
    1 UINT addr_len6
    1 UINT addr_len7
    1 UINT addr_len8
    1 UINT addr_len9
    if self.addr_len0:
        * STRING { 'sizeinbytes': self.addr_len0,
                   'terminator': None } addr0
    if self.addr_len1:
        * STRING { 'sizeinbytes': self.addr_len1,
                   'terminator': None } addr1
    if self.addr_len2:
        * STRING { 'sizeinbytes': self.addr_len2,
                   'terminator': None } addr2
    if self.addr_len3:
        * STRING { 'sizeinbytes': self.addr_len3,
                   'terminator': None } addr3
    if self.addr_len4:
        * STRING { 'sizeinbytes': self.addr_len4,
                   'terminator': None } addr4
    if self.addr_len5:
        * STRING { 'sizeinbytes': self.addr_len5,
                   'terminator': None } addr5
    if self.addr_len6:
        * STRING { 'sizeinbytes': self.addr_len6,
                   'terminator': None } addr6
    if self.addr_len7:
        * STRING { 'sizeinbytes': self.addr_len7,
                   'terminator': None } addr7
    if self.addr_len8:
        * STRING { 'sizeinbytes': self.addr_len8,
                   'terminator': None } addr8
    if self.addr_len9:
        * STRING { 'sizeinbytes': self.addr_len9,
                   'terminator': None } addr9
    if not self.has_1byte and self.has_1byte2:
        1 DONTCARE
    if self.has_1byte2:
        1 DONTCARE
    21 DONTCARE
    if self.has_40bytes:
        40 DONTCARE
    * LIST { 'elementclass': sms_msg_stat_list,
             'length': 10 } msg_stat
    # too hard to do it here.  Will be handled by the phone code
##    if self.msg_stat[0].status==SMS_STATUS_DELIVERED:
##        4 DateTime1 delivered_datetime
##        96 UNKNOWN dunno10
##    4 UINT locked
