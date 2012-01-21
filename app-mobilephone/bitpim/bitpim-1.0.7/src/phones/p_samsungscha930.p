## BITPIM
###
### Copyright (C) 2006 Joe Pham<djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id:  $

%{

"""Various descriptions of data specific to the Samsung SCH-A950 Phone"""

from prototypes import *
from prototypes_samsung import *
from p_brew import *
from p_samsungscha950 import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

# Calendar stuff
CAL_PATH='sch_event'
CAL_INDEX_FILE_NAME=CAL_PATH+'/usr_tsk'
CAL_FILE_NAME_PREFIX=CAL_PATH+'/usr_tsk_'
CAL_MAX_EVENTS=100

CAL_REMINDER_OFF=3
CAL_REMINDER_ONCE=0
CAL_REMINDER_2MIN=1
CAL_REMINDER_15MIN=2

# vide stuff
FLIX_PATH='brew/16452/mf'

# Call log/history
CL_MAX_ENTRIES=90

%}

PACKET WRingtoneIndexEntry:
    * STRING { 'terminator': None,
               'default': '/ff/' } +path_prefix
    * STRING { 'terminator': None } pathname
    * STRING { 'terminator': None,
               'default': '|0|2\x0A' } +eor
PACKET WRingtoneIndexFile:
    * LIST { 'elementclass': WRingtoneIndexEntry } +items

PACKET RRingtoneIndexEntry:
    * STRING { 'terminator': 0x7C } pathname
    * STRING { 'terminator': 0x0A } misc
PACKET RRingtoneIndexFile:
    * LIST { 'elementclass': RRingtoneIndexEntry } +items

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
    1 UINT { 'default': CAL_REMINDER_ONCE } +reminder
    5 UNKNOWN { 'pad': 0 } +zero4
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

# Call History
PACKET cl_list:
    2 UINT index

PACKET cl_index_file:
    * LIST { 'length': CL_MAX_ENTRIES,
             'elementclass': cl_list } incoming
    * LIST { 'length': CL_MAX_ENTRIES,
             'elementclass': cl_list } outgoing
    * LIST { 'length': CL_MAX_ENTRIES,
             'elementclass': cl_list } missed
    992 UNKNOWN dunno1
    4 UINT incoming_count
    4 UINT outgoing_count
    4 UINT missed_count

PACKET cl_file:
    1 UINT cl_type
    51 STRING { 'terminator': 0 } number
    4 DateTime1 datetime
    4 UNKNOWN dunno1
    4 UINT duration

