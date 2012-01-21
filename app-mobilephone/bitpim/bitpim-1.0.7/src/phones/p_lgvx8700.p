### BITPIM -*- Python -*-
###
### Copyright (C) 2007-2008 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

%{

from prototypes import *

# Make all lg stuff available in this module as well
from p_lg import *

# we are the same as lgvx9900 except as noted below
from p_lgvx9900 import *
from p_lgvx8500 import t9udbfile

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

BREW_FILE_SYSTEM = 2
BREW_READ_SIZE = 0x400
BREW_WRITE_SIZE = 0x1A00

MAX_PHONEBOOK_GROUPS=30

# Phonebook stuff
RTPathIndexFile='pim/pbRingIdSetAsPath.dat'
WPPathIndexFile='pim/pbPictureIdSetAsPath.dat'

pb_file_name='pim/pbentry.dat'
pb_group_filename='pim/pbgroup.dat'

T9USERDBFILENAME='t9udb/t9udb_eng.dat'

%}

# phonebook stuff
# pbgroup.dat
# The VX8700 and newer phones have a fixed size pbgroup.dat, hence the need to fill up with
# unused slots.
PACKET pbgroup:
    33 USTRING {'encoding': PHONE_ENCODING,
                'raiseonunterminatedread': False,
                'raiseontruncate': False,
                'default': '' } +name
    2  UINT { 'default': 0 } +groupid
    1  UINT {'default': 0} +user_added "=1 when was added by user"

PACKET pbgroups:
    "Phonebook groups"
    * LIST {'elementclass': pbgroup,
            'raiseonincompleteread': False,
            'length': MAX_PHONEBOOK_GROUPS,
            'createdefault': True} +groups

PACKET pbfileentry:
    4   UINT    serial1
    2   UINT    entrynumber
    133 DATA    data1
    2   UINT    ringtone
    2   UINT    wallpaper
    15  DATA    data2

PACKET pbfile:
    * LIST { 'elementclass': pbfileentry } items

PACKET PathIndexEntry:
    255 USTRING { 'encoding': PHONE_ENCODING,
                  'default': '' } +pathname
PACKET PathIndexFile:
    * LIST { 'elementclass': PathIndexEntry,
             'createdefault': True,
             'length': NUMPHONEBOOKENTRIES } +items

# calendar
PACKET scheduleevent:
    4  UINT pos "position within file, used as an event id"
    33 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } description
    4  GPSDATE { 'default': GPSDATE.now() } +cdate      # creation date
    4  GPSDATE { 'default': GPSDATE.now() } +mdate      # modification date
    4  LGCALDATE start
    4  LGCALDATE end_time
    4  LGCALDATE end_date
    4  LGCALREPEAT repeat # complicated bit mapped field
    1  UINT alarmindex_vibrate #LSBit of this set vibrate ON(0)/OFF(1), the 7 MSBits are the alarm index
                              #the alarmindex is the index into the amount of time in advance of the 
                              #event to notify the user. It is directly related to the alarmminutes 
                              #and alarmhours below, valid values are
                              # 8=2days, 7=1day, 6=2hours, 5=1hour, 4=15mins, 3=10mins, 2=5mins, 1=0mins, 0=NoAlarm
    1  UINT ringtone
    1  UINT unknown1
    1  UINT alarmminutes  "a value of 0xFF indicates not set"
    1  UINT alarmhours    "a value of 0xFF indicates not set"
    1  UINT { 'default': 0 } +unknown2
    2  UINT { 'default': 0x01FA } +unknown3
    69 USTRING { 'default': '', 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } +unknown4

PACKET schedulefile:
    2 UINT numactiveitems
    * LIST {'elementclass': scheduleevent} +events

PACKET textmemo:
    301 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text
    4 LGCALDATE memotime # time the memo was writen LG time

PACKET textmemofile:
    4 UINT itemcount
    * LIST { 'elementclass': textmemo } +items
