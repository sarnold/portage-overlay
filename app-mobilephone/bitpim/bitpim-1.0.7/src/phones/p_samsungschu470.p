### BITPIM
###
### Copyright (C) 2006 Joe Pham<djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsungschu470.p 4777 2010-01-07 03:24:27Z djpham $

%{

"""Various descriptions of data specific to the Samsung SCH-U470 (Juke) Phone"""

from prototypes import *
from prototypes_samsung import *
from p_brew import *
from p_samsungschu740 import *

PB_FLG2_RINGTONE=0x0001
PB_FLG2_WP=0x0002

CL_MAX_ENTRIES=90

%}

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
    2 UINT info2
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
    if self.has_group:
        1 UINT group
    if self.has_wallpaper:
        * STRING { 'terminator': None,
                   'pascal': True } wallpaper
        4 UINT wallpaper_range
    if self.has_ringtone:
        * STRING { 'terminator': None,
                   'pascal': True } ringtone
    if self.has_wallpaper2:
        * STRING { 'terminator': None,
                   'pascal': True } wallpaper2
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
    @property
    def has_ringtone(self):
        return bool(self.info2 & PB_FLG2_RINGTONE)
    @property
    def has_wallpaper2(self):
        return bool(self.info2 & PB_FLG2_WP)
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

# Calendar and notes stuff
PACKET CalIndexEntry:
    2 UINT { 'default': 0 } +index
PACKET CalIndexFile:
    2 UINT next_index
    12 DONTCARE +
    2 UINT numofevents
    6 DONTCARE +
    2 UINT numofnotes
    6 DONTCARE +
    2 UINT numofactiveevents
    112 DONTCARE +
    * LIST { 'elementclass': CalIndexEntry,
             'length': 103,
             'createdefault': True } +events
    * LIST { 'elementclass': CalIndexEntry,
             'length': 35,
             'createdefault': True } +notes
    * LIST { 'elementclass': CalIndexEntry,
             'length': 319,
             'createdefault': True } +activeevents

PACKET CalEntry:
    2 UINT titlelen
    * USTRING { 'sizeinbytes': self.titlelen,
                'encoding': ENCODING,
                'terminator': None } title
    4 DateTime start
    4 DONTCARE +
    4 DateTime { 'default': self.start } +start2
    4 DONTCARE +
    4 ExpiringTime exptime
    4 DONTCARE +
    1 DONTCARE { 'default': '\x01' } +
    1 UINT repeat
    1 DONTCARE { 'default': '\x03' } +
    1 UINT alarm
    1 UINT alert
    6 DONTCARE +
    4 UINT duration
    1 UINT timezone
    4 DateTime creationtime
    4 DONTCARE +
    4 DateTime modifiedtime
    4 DONTCARE +
    2 UINT ringtonelen
    * STRING { 'sizeinbytes': self.ringtonelen,
               'terminator': None } ringtone
    2 DONTCARE +

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
    1352 DONTCARE
    4 UINT incoming_count
    4 UINT outgoing_count
    4 UINT missed_count

PACKET -cl_file:
    1 UINT cl_type
    51 STRING { 'terminator': 0 } number
    4 DateTime2 datetime
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
    4 DateTime2 datetime
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
    54 DONTCARE
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
