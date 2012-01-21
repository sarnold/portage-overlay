### BITPIM
###
### Copyright (C) 2006 Simon Capper <skyjunky@sbcglobal.net.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

%{

"""Various descriptions of data specific to LG 6200 (Sprint)"""

import re

from prototypes import *
from prototypeslg import *

# Make all lg stuff available in this module as well
from p_lg import *
# very similar to the pm225
from p_lgpm225 import *


# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

NUMSPEEDDIALS=99
FIRSTSPEEDDIAL=1
LASTSPEEDDIAL=99
NUMPHONEBOOKENTRIES=200
MEMOLENGTH=33

NORINGTONE=0
NOMSGRINGTONE=0
NOWALLPAPER=0

NUMEMAILS=3
NUMPHONENUMBERS=5

SMS_CANNED_MAX_ITEMS=40
SMS_CANNED_MAX_LENGTH=104
SMS_CANNED_FILENAME="sms/canned_msg.dat"
SMS_PATTERNS={'Inbox': re.compile(r"^.*/inbox[0-9][0-9][0-9]\.dat$"),
             'Sent': re.compile(r"^.*/outbox[0-9][0-9][0-9]\.dat$"),
             'Saved': re.compile(r"^.*/sf[0-9][0-9]\.dat$"),
             }

numbertypetab=( 'cell', 'home', 'office', 'fax', 'pager' )

# Text Memo const
text_memo_file='sch/memo.dat'
content_file_name='ams/contentInfo'
content_count_file_name='ams/realContent'

media_directory='ams'
ringerindex='setas/amsRingerIndex.map'
imageindex='setas/amsImageIndex.map'
ringerconst=2
imageconst=3
max_ringers=100
max_images=100

phonebook_media='pim/pbookcontact.dat'

# Calendar parameters
NUMCALENDARENTRIES=300  # ?? for VX4400
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

PHONE_ENCODING='iso8859_1'

%}

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
# need to modify com_lg6200 to give a different truncateat parameter
# in the convertphonebooktophone method
PACKET pbentry:
    4  UINT serial1
    2  UINT {'constant': 0x026e} +entrysize
    2  UINT entrynumber                 
    2  UINT {'default': 0} +unknown1		
    33 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    2  UINT group
    2  UINT {'default': 0x10} +unknown2 #ringtone ??
    1  BOOL secret
    *  USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'sizeinbytes': MEMOLENGTH} memo
    *  LIST {'length': NUMEMAILS} +emails:
        73 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} email
    73 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} url
    * LIST {'length': NUMPHONENUMBERS} +numberspeeds:
        1 UINT numberspeed
    * LIST {'length': NUMPHONENUMBERS} +numbertypes:
        1 UINT numbertype
    *  LIST {'length': NUMPHONENUMBERS} +numbers:
        49 USTRING {'raiseonunterminatedread': False} number
    2  UINT {'constant': 0x0278} +EndOfRecord # size of packet
    P  UINT {'default': 0x600} +ringtone
    P  UINT {'default': 0x100} +wallpaper

PACKET pbgroup:
    "A single group"
    1 UINT group_id
    1 UINT rectype 	# 0x30 or 0xFF if deleted
    3 UNKNOWN +unknown2
    3 UNKNOWN +unknown3
    33 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name

PACKET pbgroups:
    "Phonebook groups"
    * LIST {'elementclass': pbgroup} +groups

PACKET pb_contact_media_entry:
    """Reads the wallpaper/ringer info for each 
    contact on the phone"""
    2 UINT index # matches serial1 in pbentry despite being a different size
    18 DATA dont_care1
    2 UINT ringer
    33 USTRING {'encoding': PHONE_ENCODING} name # this is null terminated
    182 DATA dont_care2
    2 UINT wallpaper
    4 DATA dont_care3

PACKET pb_contact_media_file:
    * LIST {'elementclass': pb_contact_media_entry} +contacts

###
### Media indexes
###
#
#   The 6200 has 2 index files for media and for ringtones and wallpaper uses
#   both of them. The "indexfile" packet is the same as the other versizon LG
#   phones, but the "content_file" packet is different. One index file contains
#   all downloaded content including games, images and ringtone. The two
#   index files need to be synchronised for things to work correctly.

PACKET indexentry:
    1 UINT index
    1 UINT const
    80 USTRING {'default': ""} +name

PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    # A bit of a silly design again.  Entries with an index of 0xffff are
    # 'blank'.  Thus it is possible for numactiveitems and the actual
    # number of valid entries to be mismatched.
    2 UINT numactiveitems
    * LIST {'elementclass': indexentry, 'createdefault': True} +items

PACKET content_entry:
    3 USTRING {'terminator': 0xA} type
    if self.type=='!C':
        * USTRING {'terminator': 0xA} index1
        * USTRING {'terminator': 0xA} name1
        * USTRING {'terminator': 0xA, 'default': '-1'} +unknown1 
        8 UINT {'default' :0} +unknown2
        * USTRING {'terminator': 0xA} mime_type
        * USTRING {'terminator': 0xA} content_type # 'Games', 'Screen Savers', 'Ringers'
        * USTRING {'terminator': 0xA, 'default':'bitpim.org'} +url
        2 UINT {'default':0x08AA} + unknown_int1
        * USTRING {'terminator': 0xA, 'default':''} +unknown3 
        2 UINT {'default':0x08AA} + unknown_int2
        * USTRING {'terminator': 0xA, 'default':''} +unknown4
        * USTRING {'terminator': 0xA, 'default':'0'} +unknown5 
        * USTRING {'terminator': 0xA} size
    if self.type=='!E':
        * USTRING {'terminator': 0xA, 'default':'ams:'} +location_maybe
        * USTRING {'terminator': 0xA} index2
        * USTRING {'terminator': 0xA} name2
        * USTRING {'terminator': 0xA, 'default':''} +unknown6

PACKET content_file:
    "Used to store all content on the phone, apps, ringers and images (with the exception of the camera)"
    * LIST {'elementclass': content_entry, 'createdefault': True} +items

PACKET content_count:
    "Stores the number of items in the content file"
    * USTRING {'terminator': None} count

###
### Text Memos
###

PACKET textmemo:
    151 USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text

PACKET textmemofile:
    4 UINT itemcount
    * LIST { 'elementclass': textmemo } +items

