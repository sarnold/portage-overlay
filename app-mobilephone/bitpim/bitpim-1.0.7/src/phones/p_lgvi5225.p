### BITPIM
###
### Copyright (C) 2006 Stephen A. Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvi5225.p 3352 2006-06-10 15:20:39Z skyjunky $

%{

"""Various descriptions of data specific to LG VI5225"""

from prototypes import *
from prototypeslg import *

# Make all lg stuff available in this module as well
from p_lg import *

# we are the same as lgvx4400 except as noted
# below
from p_lgvx4400 import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

NUMSPEEDDIALS=100
FIRSTSPEEDDIAL=2
LASTSPEEDDIAL=99
NUMPHONEBOOKENTRIES=500
MAXCALENDARDESCRIPTION=38

NUMEMAILS=1
NUMPHONENUMBERS=5
MEMOLENGTH=48

pb_file_name='pim/pbentry.dat'

# Calendar parameters
NUMCALENDARENTRIES=300
CAL_REP_NONE=0x10
CAL_REP_DAILY=0x11
CAL_REP_MONFRI=0x12
CAL_REP_WEEKLY=0x13
CAL_REP_MONTHLY=0x14
CAL_REP_YEARLY=0x15
CAL_DOW_SUN=0x0800
CAL_DOW_MON=0x0400
CAL_DOW_TUE=0x0200
CAL_DOW_WED=0x0100
CAL_DOW_THU=0x0080
CAL_DOW_FRI=0x0040
CAL_DOW_SAT=0x0020
CAL_DOW_EXCEPTIONS=0x0010
CAL_REMINDER_NONE=0
CAL_REMINDER_ONTIME=1
CAL_REMINDER_5MIN=2
CAL_REMINDER_10MIN=3
CAL_REMINDER_1HOUR=4
CAL_REMINDER_1DAY=5
CAL_REMINDER_2DAYS=6
CAL_REPEAT_DATE=(2100, 12, 31)

cal_dir='sch'
cal_data_file_name='sch/schedule.dat'
cal_exception_file_name='sch/schexception.dat'
cal_has_voice_id=False

%}

PACKET ffpacket:
    1 UINT {'constant': 0xff} +header
    1 UINT command
    1 UINT dunno1
    1 UINT dunno2
    4 UKNOWN pad
    1 UINT dunno3
    1 UINT dunno4

# Looks same as 4400
PACKET speeddial:
    1 UINT {'default': 0xff} +entry
    1 UINT {'default': 0xff} +number

PACKET speeddials:
    * LIST {'length': NUMSPEEDDIALS, 'elementclass': speeddial} +speeddials

PACKET pbreadentryresponse:
    "Results of reading one entry"
    *  pbheader header
    *  pbentry  entry

PACKET pbupdateentryrequest:
    * pbheader {'command': 0x04, 'flag': 0x01} +header
    * pbentry entry

PACKET pbappendentryrequest:
    * pbheader {'command': 0x03, 'flag': 0x01} +header
    * pbentry entry

# All STRINGS have raiseonterminatedread as False since the phone does
# occassionally leave out the terminator byte
# Note if you change the length of any of these fields, you also
# need to modify com_lgvx4400 to give a different truncateat parameter
# in the convertphonebooktophone method
PACKET pbentry:
    P UINT {'constant': NOWALLPAPER} wallpaper
    4 UINT serial1
    2 UINT {'constant': 0x01E0} +entrysize
    4 UINT serial2
    2 UINT entrynumber 
    23 USTRING {'raiseonunterminatedread': False} name
    2 UINT group
    * LIST {'length': NUMEMAILS} +emails:
        73 USTRING {'raiseonunterminatedread': False} email
    73 USTRING {'raiseonunterminatedread': False} url
    1 UINT ringtone                                     "ringtone index for a call"
    1 UINT secret
    * USTRING {'raiseonunterminatedread': False, 'sizeinbytes': MEMOLENGTH} memo
    1 UINT {'default': 0} +dunno1
    2 UINT {'default': 0} +dunno2
    * LIST {'length': NUMPHONENUMBERS} +numbertypes:
        1 UINT numbertype
    * LIST {'length': NUMPHONENUMBERS} +numbers:
        49 USTRING {'raiseonunterminatedread': False} number

    
