### BITPIM
###
###
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
### by David Ritter 7/10/07
### Write to phonebook working msg ringtones not supported
### Write to Calendar, wallpaper, and ringtones is working


%{
##from common import PhoneBookBusyException

from p_lgvx9900 import *
 
from prototypes import *
from prototypeslg import *
 
# Make all lg stuff available in this module as well
from p_lg import *
from p_brew import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

BREW_FILE_SYSTEM=2
NOMSGRINGTONE=1
NUMSPEEDDIALS=100
FIRSTSPEEDDIAL=2
LASTSPEEDDIAL=99
NUMPHONEBOOKENTRIES=500
pb_file_name='pim/pbentry.dat'


PHONE_ENCODING='iso-8859-1'


# Media type
MEDIA_TYPE_RINGTONE=0x0201
MEDIA_TYPE_IMAGE=0x400
MEDIA_TYPE_SOUND=0x0402
MEDIA_TYPE_SDIMAGE=0x0008
MEDIA_TYPE_SDSOUND=0x000C
MEDIA_TYPE_VIDEO=0x0304
MEDIA_RINGTONE_DEFAULT_ICON=1
MEDIA_IMAGE_DEFAULT_ICON=0
MEDIA_VIDEO_DEFAULT_ICON=0

# need to call stat to get the file time/data
broken_filelist_date=True
 # Calendar parameters
NUMCALENDARENTRIES=300
# vx8100 uses a type based index for speed dials instead of positional like the vx4400
SPEEDDIALINDEX=1 
MAXCALENDARDESCRIPTION=32

CALENDAR_HAS_SEPARATE_END_TIME_AND_DATE=0
%}
# Misc stuff
PACKET LockKeyReq:
    1 UINT { 'default': 0x21 } +cmd
    2 UINT { 'default': 0 } +lock "0=Lock, 1=Unlock"

PACKET KeyPressReq:
     1 UINT { 'default': 0x20 } +cmd
     1 UINT { 'default': 0 } +hold
     1 STRING { 'terminator': None,
                'sizeinbytes': 1 } key


PACKET indexentry:
    2 UINT index
    2 UINT type
    256 USTRING {'encoding': PHONE_ENCODING,
                'raiseonunterminatedread': False,
                'raiseontruncate': False } filename  "includes full pathname"
    4 UINT {'default':0} +icon
    4 UINT {'default': 0} +date "i think this is bitfield of the date"
    4 UINT dunno
    4 UINT {'default': 0} +size "size of the file, can be set to zero"
    4 UINT dunno1
       
PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    * LIST {'elementclass': indexentry, 'createdefault': True} +items

PACKET speeddial:
    2 UINT {'default': 0xffff} +entry
    1 UINT {'default': 0xff} +number

PACKET speeddials:
    * LIST {'length': NUMSPEEDDIALS, 'elementclass': speeddial} +speeddials
    
    
PACKET pbgroup:
    23 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } name
    2 UINT { 'default': 0xffff } +ringtone

PACKET pbgroups:
    "Phonebook groups"
    * LIST {'elementclass': pbgroup} +groups

PACKET pbinforequest:
    "Random information about the phone"
    * pbheader {'command': 0x15, 'flag': 0x01} +header
    6 UNKNOWN +pad

PACKET pbinforesponse:
    * pbheader header
    10 UNKNOWN dunno1
    4 UINT firstentry
    2 UINT numentries  # fields from this point on differ by model and are not decoded correctly
    * UNKNOWN dunno2


PACKET pbfileentry:
    4   UINT    serial1
    2   UINT    entrynumber
    172 DATA    data1
    2   UINT    ringtone
    2   UINT    group
    2   UINT    wallpaper
    256  DATA    data2
    * UNKNOWN unknown


PACKET pbfile:
    * LIST { 'elementclass': pbfileentry } items

PACKET wallpaper_id:
    80 USTRING { 'terminator': None, 'pad': 0xFF, 'default': "" } +path
       
PACKET wallpaper_id_file:
    * LIST { 'length': NUMPHONEBOOKENTRIES,
             'elementclass': wallpaper_id,
             'createdefault': True } +items


    
PACKET PathIndexEntry:
    255 USTRING { 'encoding': PHONE_ENCODING,
                  'default': '' } +pathname
PACKET PathIndexFile:
    * LIST { 'elementclass': PathIndexEntry,
             'createdefault': True,
             'length': NUMPHONEBOOKENTRIES } +items


PACKET scheduleexception:
    4 UINT pos "Refers to event id (position in schedule file) that this suppresses"
    1 UINT day
    1 UINT month
    2 UINT year

PACKET scheduleexceptionfile:
    * LIST {'elementclass': scheduleexception} +items

PACKET scheduleevent:
    4 UINT pos "position within file, used as an event id"
    33 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } description
    4 LGCALDATE start
    4 LGCALDATE end
    4 LGCALREPEAT repeat # complicated bit mapped field
    1 UINT alarmindex_vibrate #LSBit of this set vibrate ON(0)/OFF(1), the 7 MSBits are the alarm index
                              #the alarmindex is the index into the amount of time in advance of the
                              #event to notify the user. It is directly related to the alarmminutes
                              #and alarmhours below, valid values are
                              # 8=2days, 7=1day, 6=2hours, 5=1hour, 4=15mins, 3=10mins, 2=5mins, 1=0mins, 0=NoAlarm


    2 UINT ringtone
    1 UINT alarmminutes  "a value of 0xFF indicates not set"
    1 UINT alarmhours    "a value of 0xFF indicates not set"
    1 UINT unknown1
    2 UINT unknown2


PACKET schedulefile:
    2 UINT numactiveitems
    * LIST {'elementclass': scheduleevent} +events

PACKET ULReq:
    ""
    1 UINT { 'default': 0xFE } +cmd
    1 UINT { 'default': 0x00 } +unlock_code
    4 UINT unlock_key
    1 UINT { 'default': 0x00 } +zero

PACKET ULRes:
    ""
    1 UINT cmd
    1 UINT unlock_code
    4 UINT unlock_key
    1 UINT unlock_ok


# Text Memos. LG memo support is weak, it only supports the raw text and none of
# the features that other phones support, when you run bitpim you see loads of
# options that do not work in the vx8100 on the memo page
PACKET textmemo:
    151 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text
    4 LGCALDATE memotime # time the memo was writen LG time

PACKET textmemofile:
    4 UINT itemcount
    * LIST { 'elementclass': textmemo } +items


PACKET call:
    4 GPSDATE GPStime #no. of seconds since 0h 1-6-80, based off local time.
    4 UINT unknown2 # different for each call
    4 UINT duration #seconds, not certain about length of this field
    49 USTRING {'raiseonunterminatedread': False} number
    36 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    2 UINT numberlength # length of phone number
    1 UINT pbnumbertype # 1=cell, 2=home, 3=office, 4=cell2, 5=fax, 6=vmail, 0xFF=not in phone book
    3 UINT unknown2 #
    2 UINT pbentrynum #entry number in phonebook
    58 UINT unknown3
       
PACKET callhistory:
    4 UINT numcalls
    1 UINT unknown1
    * LIST {'elementclass': call} +calls
