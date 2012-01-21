### BITPIM
###
### Copyright (C) 2006 Joe Pham<djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsungschu740.p 4772 2010-01-02 06:10:24Z djpham $

%{

"""Various descriptions of data specific to the Samsung SCH-A950 Phone"""

from prototypes import *
from prototypes_samsung import *
from p_brew import *
from p_samsungscha950 import *

RT_PATH='brew/mod/mr'
RT_INDEX_FILE_NAME=RT_PATH+'/MrInfo.db'
RT_EXCLUDED_FILES=('MrInfo.db',)

SND_PATH='brew/mod/18067'
SND_INDEX_FILE_NAME=SND_PATH+'/MsInfo.db'
SND_EXCLUDED_FILES=('MsInfo.db', 'ExInfo.db')

PIC_PATH='brew/mod/10888'
PIC_INDEX_FILE_NAME=PIC_PATH+'/Default Album.alb'
PIC_EXCLUDED_FILES=('Default Album.alb',)
PIC_TYPE_HEADER=0
PIC_TYPE_BUILTIN=4
PIC_TYPE_USERS=3

VIDEO_PATH='brew/mod/10890'
VIDEO_INDEX_FILE_NAME=VIDEO_PATH+'/Default Album.alb'

PB_FLG_NOTE=0x0200
PB_MAX_NOTE_LEN=64

CL_MAX_ENTRIES=90
CL_TYPE_INCOMING=2
CL_TYPE_OUTGOING=1
CL_TYPE_MISSED=3
CL_TYPE_DELETED=5
CL_VALID_TYPE=frozenset((CL_TYPE_INCOMING, CL_TYPE_OUTGOING, CL_TYPE_MISSED))

%}

# Ringtone stuff
PACKET WRingtoneIndexEntry:
    P STRING name
    * STRING { 'terminator': None,
               'default': '/ff/' } +path_prefix
    * STRING { 'terminator': None } pathname
    * STRING { 'terminator': None,
               'default': '|0|3\x0A' } +eor
PACKET WRingtoneIndexFile:
    * LIST { 'elementclass': WRingtoneIndexEntry } +items

PACKET RRingtoneIndexEntry:
    * STRING { 'terminator': 0x7C } pathname
    * STRING { 'terminator': 0x0A } misc
PACKET RRingtoneIndexFile:
    * LIST { 'elementclass': RRingtoneIndexEntry } +items

# Sounds stuff
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

# Wallpaper stuff
PACKET WPictureIndexEntry:
    P STRING { 'default': '/ff/' } +path_prefix
    P STRING { 'terminator': None } pathname
    258 STRING { 'terminator': 0,
                 'default': self.path_prefix+self.pathname } +path_name
    2 UINT { 'default': PIC_TYPE_USERS } +pictype "0= invalid, 4=builtin, 3=users"
PACKET WPictureIndexFile:
    * WPictureIndexEntry { 'pathname': '0|/ff/brew/mod/10888/Default Album|\x0A',
                           'path_prefix': '',
                           'pictype': PIC_TYPE_HEADER } +header
    * WPictureIndexEntry { 'pathname': 'Preloaded1',
                           'path_prefix': '',
                           'pictype': PIC_TYPE_BUILTIN } +preloaded1
    * WPictureIndexEntry { 'pathname': 'Preloaded2',
                           'path_prefix': '',
                           'pictype': PIC_TYPE_BUILTIN } +preloaded2
    * WPictureIndexEntry { 'pathname': 'Preloaded3',
                           'path_prefix': '',
                           'pictype': PIC_TYPE_BUILTIN } +preloaded3
    * WPictureIndexEntry { 'pathname': 'Preloaded4',
                           'path_prefix': '',
                           'pictype': PIC_TYPE_BUILTIN } +preloaded4
    * WPictureIndexEntry { 'pathname': 'Preloaded5',
                           'path_prefix': '',
                           'pictype': PIC_TYPE_BUILTIN } +preloaded5
    * WPictureIndexEntry { 'pathname': 'Preloaded6',
                           'path_prefix': '',
                           'pictype': PIC_TYPE_BUILTIN } +preloaded6
    * WPictureIndexEntry { 'pathname': 'Preloaded7',
                           'path_prefix': '',
                           'pictype': PIC_TYPE_BUILTIN } +preloaded7
    * WPictureIndexEntry { 'pathname': 'Preloaded8',
                           'path_prefix': '',
                           'pictype': PIC_TYPE_BUILTIN } +preloaded8
    * LIST { 'elementclass': WPictureIndexEntry } +items

PACKET RPictureIndexEntry:
    258 STRING { 'terminator': 0,
                 'raiseonunterminatedread': False } pathname
    2 UINT pictype "0= invalid, 4=builtin, 3=users"
PACKET RPictureIndexFile:
    * LIST { 'elementclass': RPictureIndexEntry } +items

# Phonebook stuff
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
    if self.has_email:
        * USTRING { 'terminator': None,
                    'encoding': ENCODING,
                    'pascal': True } email
    if self.has_email2:
        * USTRING { 'terminator': None,
                    'encoding': ENCODING,
                   'pascal': True } email2
    if self.has_home:
        * NumberEntry home
    if self.has_work:
        * NumberEntry work
    if self.has_cell:
        * NumberEntry cell
    if self.has_fax:
        * NumberEntry fax
    if self.has_cell2:
        * NumberEntry cell2
    if self.has_note:
        * STRING { 'terminator': None,
                   'pascal': True } note
    if self.has_date:
        4 DateTime datetime
    if self.hsa_group:
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
    def has_note(self):
        return bool(self.info & PB_FLG_NOTE)
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
    2 DONTCARE +
    * USTRING { 'terminator': 0,
                'encoding': ENCODING,
                'maxsizeinbytes': PB_MAX_NOTE_LEN,
                'raiseontruncate': False,
                'default': '' } +note
    1 DONTCARE +
    * STRING { 'terminator': 0,
               'default': '' } +wallpaper
    4 UINT { 'default': 0 } +wallpaper_range
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
    1 DONTCARE +
    * ss_pb_entry entry

PACKET -ss_pb_write_resp:
    * ss_cmd_hdr hdr
    1 DONTCARE
    2 UINT index

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
    53 DONTCARE
    * USTRING { 'sizeinbytes': self.msg_len,
                'encoding': ENCODING,
                'terminator': None } msg
    if self.has_callback:
        3 DONTCARE
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
    81 DONTCARE
    if self.has_40bytes:
        40 DONTCARE
    * LIST { 'elementclass': sms_msg_stat_list,
             'length': 10 } msg_stat
    # too hard to do it here.  Will be handled by the phone code
##    if self.msg_stat[0].status==SMS_STATUS_DELIVERED:
##        4 DateTime1 delivered_datetime
##        96 UNKNOWN dunno10
##    4 UINT locked

# Call History
PACKET -cl_list:
    2 UINT index

PACKET -cl_index_file:
    * LIST { 'length': CL_MAX_ENTRIES,
             'elementclass': cl_list } incoming
    * LIST { 'length': CL_MAX_ENTRIES,
             'elementclass': cl_list } outgoing
    * LIST { 'length': CL_MAX_ENTRIES,
             'elementclass': cl_list } missed
    992 DONTCARE
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
