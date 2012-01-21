### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_motov3m.p 4537 2007-12-30 03:32:13Z djpham $

%{

"""Various descriptions of data specific to Motorola V3m phones"""

from prototypes import *
from prototypes_moto import *
from p_etsi import *
from p_moto import *
from p_motov710 import *
from p_motov3m import *

import fnmatch

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

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
NUMBER_TYPE_WWW=11
NUMBER_TYPE_MEMO=11
NUMBER_TYPE=frozenset([NUMBER_TYPE_WORK, NUMBER_TYPE_HOME, NUMBER_TYPE_MAIN,
                       NUMBER_TYPE_MOBILE, NUMBER_TYPE_FAX, NUMBER_TYPE_PAGER])
EMAIL_TYPE=frozenset([NUMBER_TYPE_EMAIL])
WWW_TYPE=frozenset([NUMBER_TYPE_WWW])
MEMO_TYPE=frozenset([NUMBER_TYPE_MEMO])
NUMBER_TYPE_NAME={
    NUMBER_TYPE_WORK: 'office',
    NUMBER_TYPE_HOME: 'home',
    NUMBER_TYPE_MAIN: 'main',
    NUMBER_TYPE_MOBILE: 'cell',
    NUMBER_TYPE_FAX: 'fax',
    NUMBER_TYPE_PAGER: 'pager',
    }
NUMBER_TYPE_CODE={
    'office': NUMBER_TYPE_WORK,
    'home': NUMBER_TYPE_HOME,
    'main': NUMBER_TYPE_MAIN,
    'cell': NUMBER_TYPE_MOBILE,
    'fax': NUMBER_TYPE_FAX,
    'pager': NUMBER_TYPE_PAGER }

PB_TOTAL_GROUP=14
PB_GROUP_RANGE=xrange(1, PB_TOTAL_GROUP+1)
PB_GROUP_NAME_LEN=24

PB_MAX_NUMBER_LEN=32
PB_MAX_NAME_LEN=24
PB_MAX_EMAIL_LEN=48

PB_FIRST_ENTRY=2
PB_TOTAL_ENTRIES=1430
# Slot 1 is voice mail
PB_RANGE=xrange(PB_FIRST_ENTRY,PB_TOTAL_ENTRIES+1)


%}

# Should fix _save_groups in com_motov710.py to query to get the group count
PACKET read_group_req:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None, 'default': '+MPGR=' } +command
    * CSVINT { 'default': 1 } +start_index
    * CSVINT { 'terminator': None,
               'default': PB_TOTAL_GROUP } +end_index

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
        * CSVINT repeat_type
    if self.command=='+MDBRE:':
        * CSVINT ex_event
        * CSVINT { 'terminator': None } ex_event_flag
