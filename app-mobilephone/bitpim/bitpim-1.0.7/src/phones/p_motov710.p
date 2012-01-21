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
from p_moto import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

PB_TOTAL_GROUP=30
PB_GROUP_RANGE=xrange(1, PB_TOTAL_GROUP+1)
PB_GROUP_NAME_LEN=24

RT_BUILTIN=0x0C
RT_CUSTOM=0x0D
RT_INDEX_FILE='/MyToneDB.db'
RT_PATH='motorola/shared/audio'

WP_PATH='motorola/shared/picture'
WP_EXCLUDED_FILES=frozenset([])

# Calendar const
CAL_TOTAL_ENTRIES=500
CAL_MAX_ENTRY=499
CAL_TOTAL_ENTRY_EXCEPTIONS=8
CAL_TITLE_LEN=64

CAL_REP_NONE=0
CAL_REP_DAILY=1
CAL_REP_WEEKLY=2
CAL_REP_MONTHLY=3
CAL_REP_MONTHLY_NTH=4
CAL_REP_YEARLY=5

CAL_ALARM_NOTIME='00:00'
CAL_ALARM_NODATE='00-00-2000'

%}

PACKET group_count_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+MPGR=?' } +command

PACKET group_count_resp:
    * CSVSTRING { 'quotechar': None, 'terminator': ord(' '),
                  'default': '+MPGR:' } command
    * CSVSTRING { 'quotechar': None } countstring
    * DATA dontcare

PACKET read_group_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+MPGR=' } +command
    * CSVINT { 'default': 1 } +start_index
    * CSVINT { 'terminator': None,
               'default': PB_TOTAL_GROUP } +end_index
PACKET read_group_resp:
    * CSVSTRING { 'quotechar': None, 'terminator': ord(' '),
                  'default': '+MPGR:' } command
    * CSVINT index
    * CSVSTRING name
    * CSVINT ringtone
    * DATA dunno
PACKET del_group_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+MPGW=' } +command
    * CSVINT { 'terminator': None } index
PACKET write_group_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+MPGW=' } +command
    * CSVINT index
    * CSVSTRING { 'maxsizeinbytes': PB_GROUP_NAME_LEN,
                  'raiseontruncate': False } name
    * CSVINT { 'terminator': None, 'default': 255 } +ringtone

PACKET ringtone_index_entry:
    P BOOL { 'default': True } +read_mode
    if self.read_mode:
        508 DATA { 'pad': None } name
    if not self.read_mode:
        508 DATA name
    1 UINT index
    1 UINT ringtone_type
    6 DATA { 'default': '' } +dunno

PACKET ringtone_index_file:
    * LIST { 'elementclass': ringtone_index_entry,
             'createdefault': True} +items

# Calendar stuff
PACKET calendar_lock_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None,
                  'default': '+MDBL=' } +command
    * CSVINT { 'terminator': None } lock

PACKET calendar_read_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None,
                  'default': '+MDBR=' } +command
    * CSVINT { 'default': 0 } +start_index
    * CSVINT { 'terminator': None,
               'default': CAL_MAX_ENTRY } +end_index

PACKET calendar_req_resp:
    * CSVSTRING { 'quotechar': None,
                  'terminator': ord(' '),
                  'default': '+MDBR:' } command
    * CSVINT index
    if self.command=='+MDBR:':
        * CSVSTRING title
        * CSVINT alarm_timed
        * CSVINT alarm_enabled
        * CAL_TIME start_time
        * CAL_DATE start_date
        * CSVINT duration
        * CAL_TIME alarm_time
        * CAL_DATE alarm_date
        * CSVINT { 'terminator': None } repeat_type
    if self.command=='+MDBRE:':
        * CSVINT ex_event
        * CSVINT { 'terminator': None } ex_event_flag

PACKET calendar_write_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None,
                  'default': '+MDBW=' } +command
    * CSVINT index
    * CSVSTRING {'maxsizeinbytes': CAL_TITLE_LEN } title
    * CSVINT { 'default': 0 } +alarm_timed
    * CSVINT { 'default': 0 } +alarm_enabled
    * CAL_TIME start_time
    * CAL_DATE start_date
    * CSVINT duration
    * CAL_TIME alarm_time
    * CAL_DATE alarm_date
    * CSVINT { 'terminator': None,
               'default': 0 } +repeat_type
    
PACKET calendar_write_ex_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None,
                  'default': '+MDBWE=' }  +command
    * CSVINT index
    * CSVINT nth_event
    * CSVINT { 'terminator': None,
               'default': 1 } +ex_event_flag
