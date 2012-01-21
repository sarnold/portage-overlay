### BITPIM ( -*- python -*- )
###
### Copyright (C) 2009 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
###

%{

"""Various descriptions of data specific to LG VX11000"""

# groups     - same as VX-8700 (added group wallpaper bit)
# phonebook  - LG Phonebook v1.0 (same as VX-8550)
# schedule   - same as VX-8550
# memos      - same as VX-8550
# sms        - same as VX-9100
# index file - same as VX-9700
# favorites  - same as VX-9600
from p_lgvx9600 import *

# SMS index files
inbox_index     = "dload/inbox.dat"
outbox_index    = "dload/outbox.dat"
drafts_index    = "dload/drafts.dat"

# Phonebook addresses
pa_file_name = "pim/pbaddress.dat"
pb_group_filename = "pim/pbgroup.dat"

#Group Picture ID Path Index File
GroupWPPathIndexFile='pim/pbGroupPixIdSetAsPath.dat'

# Phonebook favorites
favorites_file_name  = "pim/pbFavorite.dat"
NUMFAVORITES=10

#verified these constants specific to VX11000
PHONEBOOKENTRYSIZE=512
NUMSPEEDDIALS=1000
FIRSTSPEEDDIAL=1
LASTSPEEDDIAL=999
NUMEMERGENCYCONTACTS=3
NUMPHONEBOOKENTRIES=1000
NUMEMAILS=2
NUMPHONENUMBERS=5
MAXCALENDARDESCRIPTION=32
MAX_PHONEBOOK_GROUPS=30
MEMOLENGTH=300
SMS_CANNED_MAX_ITEMS=30
SMS_CANNED_MAX_LENGTH=100
NUMCALENDARENTRIES=300 #TODO: need to verify this number

PA_ENTRY_SOR = "<PA>"

%}

# Call history

PACKET call:
    4 GPSDATE GPStime    # no. of seconds since 0h 1-6-80, based off local time.
    4 UINT  unk0         # different for each call
    4 UINT  duration     # seconds, not certain about length of this field
    49 USTRING {'raiseonunterminatedread': False} number
    36 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} name
    1 UINT  numberlength # length of phone number
    1 UINT  status       # 0=outgoing, 1=incoming, 2=missed, etc
    1 UINT  pbnumbertype # 1=cell, 2=home, 3=office, 4=cell2, 5=fax, 6=vmail, 0xFF=not in phone book
    4 UINT  unk1         # always seems to be 0
    2 UINT  pbentrynum   # entry number in phonebook
    76 DATA number_location # set by pay software

# same as the VX-8560 without the unknown entry at the beginning of the file
PACKET callhistory:
    4 UINT numcalls
    1 UINT unk1
    * LIST {'elementclass': call, 'length': self.numcalls} +calls

# pbspeed.dat
PACKET speeddial:
    2 UINT {'default': 0xffff} +entry "0-based entry number"
    1 UINT {'default': 0xff} +number "number type"
    %{
    def valid(self):
        return self.entry!=0xffff
    %}

PACKET speeddials:
   * LIST {'length': NUMSPEEDDIALS, 'elementclass': speeddial} +speeddials

# /pim/pbentry.dat format
PACKET pbfileentry:
    5   STRING { 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '\xff\xff\xff\xff\xff' } +entry_tag
    if self.entry_tag==PB_ENTRY_SOR:
       1   UINT { 'default': 0xff } + unk4
       * PBDateTime { 'defaulttocurrenttime': True } +mod_date
       6   STRING { 'terminator': None, 'default': '\xff\xff\xff\xff\xff\xff' } +unk0
       4   UINT entry_number1 # 1 based entry number -- might be just 2 bytes long
       2   UINT entry_number0 # 0 based entry number
       34  USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } +name
       2   UINT    { 'default': 0 } +group
       58  UNKNOWN +unk1
       *  LIST {'length': NUMEMAILS} +emails:
          49 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} email
       2   UINT { 'default': 0xffff } +ringtone
       2   UINT { 'default': 0 } +wallpaper
       * LIST {'length': NUMPHONENUMBERS} +numbertypes:
          1 UINT { 'default': 0 } numbertype
       1   UINT { 'default': 0 } +unk2
       * LIST {'length': NUMPHONENUMBERS} +numberindices:
          2 UINT { 'default': 0xffff } numberindex
       2   UINT { 'default': 0xffff } +addressindex
       2   UINT { 'default': 0xffff } +unk3
       260 USTRING { 'raiseonunterminatedread': False, 'default': '', 'encoding': PHONE_ENCODING } +memo # maybe
       6   USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '</PE>'} +exit_tag
    else:
        # this is a blank entry, fill it up with 0xFF
        507 DATA { 'default': '\xff'*507 } +dontcare
    %{
    def valid(self):
        global PB_ENTRY_SOR
        return self.entry_tag==PB_ENTRY_SOR and ord(self.name[0]) != 0xff
    %}

PACKET pbfile:
    * LIST { 'elementclass': pbfileentry,
             'length': NUMPHONEBOOKENTRIES,
             'createdefault': True} +items
    6 STRING { 'default': '<HPE>',
               'raiseonunterminatedread': False,
               'raiseontruncate': False } +eof_tag
    10 STRING { 'raiseonunterminatedread': False,
                'raiseontruncate': False } +model_name
    * PBDateTime { 'defaulttocurrenttime': True } +mod_date
    477 DATA   { 'default': '\x00'*221 } + blanks
    7 STRING { 'default': '</HPE>',
               'raiseonunterminatedread': False,
               'raiseontruncate': False  } +eof_close_tag

PACKET pafileentry:
    5   STRING { 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '\xff\xff\xff\xff\xff' } +entry_tag
    if self.entry_tag==PA_ENTRY_SOR:
       1   UINT { 'default': 0x00 }+pad
       *   PBDateTime { 'defaulttocurrenttime': True } +mod_date
       6   UNKNOWN +zeros
       2   UINT    +index
       2   UINT    +pb_entry
       52  USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '' } +street
       52  USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '' } +city
       52  USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '' } +state
       13  USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '' } +zip_code
       52  USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '' } +country
       6   USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '</PA>'} +exit_tag
    else:
        # this is a blank entry, fill it up with 0xFF
        250 DATA { 'default': '\xff'*250 } +dontcare
    %{
    def valid(self):
        global PA_ENTRY_SOR
        return self.entry_tag==PA_ENTRY_SOR
    %}

PACKET pafile:
    * LIST { 'elementclass': pafileentry,
             'length': NUMPHONEBOOKENTRIES,
             'createdefault': True } +items

PACKET pbgroup:
    33 USTRING {'encoding': PHONE_ENCODING,
                'raiseonunterminatedread': False,
                'raiseontruncate': False,
                'default': '' } +name
    2  UINT { 'default': 0 } +groupid
    1  UINT { 'default': 0 } +user_added "=1 when was added by user"
    2  UINT { 'default': 0 } +wallpaper

PACKET pbgroups:
    "Phonebook groups"
    * LIST {'elementclass': pbgroup,
            'raiseonincompleteread': False,
            'length': MAX_PHONEBOOK_GROUPS,
            'createdefault': True} +groups

# Favorites -- added on the Versa (LG VX-9600)
PACKET favorite:
    2 UINT { 'default': 0xffff } +pb_index  # contact or group id
    1 UINT { 'default': 0xff }   +fav_type  # 1 - contact, 2 - group
    %{
    def has_pbentry(self):
        return self.pb_index != 0xffff and self.fav_type == 1
    %}

PACKET favorites:
    * LIST { 'elementclass': favorite, 'length': NUMFAVORITES } +items
    %{
    def set_favorite(self, index, entity_index, ispbentry):
        if index < NUMFAVORITES:
            self.items[index].pb_index = entity_index
            if ispbentry:
                self.items[index].fav_type = 1
            else:
                self.items[index].fav_type = 2
    %}

PACKET GroupPicID_PathIndexEntry:
    255 USTRING { 'encoding': PHONE_ENCODING,
                  'default': '' } +pathname
PACKET GroupPicID_PathIndexFile:
    * LIST { 'elementclass': GroupPicID_PathIndexEntry,
             'raiseonincompleteread': False,
             'createdefault': True} +items            
