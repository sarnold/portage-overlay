### ( -*- Python -*- )
### Copyright (C) 2007-2008 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx8550.p 4639 2008-07-22 19:50:21Z djpham $

%{

"""Various descriptions of data specific to LG VX8550"""

from p_lgvx8700 import *
# same as the VX-8700 except as noted below

NUMPHONEBOOKENTRIES=1000
NUMPHONENUMBERENTRIES=5000

NUMSPEEDDIALS=100
FIRSTSPEEDDIAL=1
LASTSPEEDDIAL=99

NUMCALENDARENTRIES=300
NUMEMERGENCYCONTACTS=3

# sizes of pbfileentry and pnfileentry
PHONEBOOKENTRYSIZE=256
PHONENUMBERENTRYSIZE=64

NUM_EMAILS=2
NUMPHONENUMBERS=5

pb_file_name         = 'pim/pbentry.dat'
pb_recordid_filename = 'pim/record_id.dat'
pn_file_name         = 'pim/pbnumber.dat'
speed_file_name      = 'pim/pbspeed.dat'
ice_file_name        = 'pim/pbiceentry.dat'

PB_ENTRY_SOR='<PE>'
PB_NUMBER_SOR='<PN>'

%}

# Phonebook stuff
# *NOTE*
#  The VX-8550 appears to be the first LG Verizon phone not to use the LG phonebook protocol. The VX-8550 responds to phonebook commands with
#  a bad brew command error.

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
       * PBDateTime { 'defaulttocurrenttime': True } +mod_date
       6   STRING { 'terminator': None, 'default': '\xff\xff\xff\xff\xff\xff' } +unk0
       4   UINT entry_number1 # 1 based entry number -- might be just 2 bytes long
       2   UINT entry_number0 # 0 based entry number
       33  USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } +name
       2   UINT    { 'default': 0 } +group
       *  LIST {'length': NUMEMAILS} +emails:
          49 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} email
       2   UINT { 'default': 0xffff } +ringtone
       2   UINT { 'default': 0 } +wallpaper
       * LIST {'length': NUMPHONENUMBERS} +numbertypes:
          1 UINT { 'default': 0 } numbertype
       * LIST {'length': NUMPHONENUMBERS} +numberindices:
          2 UINT { 'default': 0xffff } numberindex
       69  USTRING { 'raiseonunterminatedread': False, 'default': '', 'encoding': PHONE_ENCODING } +memo # maybe
       6   USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '</PE>'} +exit_tag
    else:
        # this is a blank entry, fill it up with 0xFF
        251 DATA { 'default': '\xff'*251 } +dontcare
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
    221 DATA   { 'default': '\x00'*221 } + blanks
    7 STRING { 'default': '</HPE>',
               'raiseonunterminatedread': False,
               'raiseontruncate': False  } +eof_close_tag

# /pim/pbnumber.dat format
PACKET pnfileentry:
    4   STRING { 'terminator': None,
                 'raiseonunterminatedread': False,
                 'raiseontruncate': False,
                 'default': '\xff\xff\xff\xff'} +entry_tag # some entries don't have this??
    if self.entry_tag != '\xff\xff\xff\xff':
        # this is a valid slot
        1 UINT { 'default': 0 } +pad00
        # year, month, day, hour, min, sec
        * PBDateTime {'defaulttocurrenttime': True } +mod_date
        6   STRING { 'default': '', 'raiseonunterminatedread': False } +unk0
        2   UINT pn_id # 0 based
        2   UINT pe_id # 0 based
        1   UINT pn_order "0-based order of this phone within this contact"
        25  LGHEXPN phone_number
        2   UINT ntype
        3   UINT { 'default': 0 } +unk2
        6   USTRING { 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '</PN>'} +exit_tag # some entries don't have this??
    else:
        # empty slot: all 0xFF
        60 DATA { 'default': '\xFF'*60 } +blanks
    %{
    def valid(self):
         return self.phone_number != None
    def malformed(self):
         # malformed (yet valid) entries have been seen on several phones including the VX-8550 and VX-10000
         return self.entry_tag != PB_NUMBER_SOR
    %}

PACKET pnfile:
    * LIST { 'elementclass': pnfileentry,
             'createdefault': True,
             'length': NUMPHONENUMBERENTRIES } +items

PACKET PathIndexEntry:
    255 USTRING { 'encoding': PHONE_ENCODING,
                  'default': '' } +pathname
PACKET PathIndexFile:
    * LIST { 'elementclass': PathIndexEntry,
             'createdefault': True,
             'length': NUMPHONEBOOKENTRIES } +items

# record_id.dat
PACKET RecordIdEntry:
    4 UINT idnum

# ICE
# /pim/pbiceentry.dat
PACKET iceentry:
    "ICE index entries"
    2 UINT { 'default': 0 } +entry_assigned "0 if not assigned, 1 if assigned"
    2 UINT { 'default': 0xffff } +entry_number "0-based ICE entry number" # don't care when not assigned
    2 UINT { 'default': 0 } +pb_index "0-based phone book entry number"
    82 DATA { 'default': '\x00'*82 } +dontcare
    %{
    def valid(self):
        return self.entry_assigned==1 and \
               self.entry_number<NUMEMERGENCYCONTACTS and \
               self.pb_index<NUMPHONEBOOKENTRIES
    %}

PACKET iceentryfile:
     * LIST { 'elementclass': iceentry,
              'createdefault': True,
              'length': NUMEMERGENCYCONTACTS } +items

# calendar
# The event file format on the VX-8550 are almost identical to that of the VX-8700.
PACKET scheduleevent:
    P  UINT { 'constant': 138 } packet_size
    4  UINT { 'default': 0 } +pos "position within file, used as an event id"
    33 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '' } +description
    4  GPSDATE { 'default': GPSDATE.now() } +cdate      # creation date
    4  GPSDATE { 'default': GPSDATE.now() } +mdate      # modification date
    4  LGCALDATE { 'default': (0,0,0,0,0) } +start
    4  LGCALDATE { 'default': (0,0,0,0,0) } +end_time
    4  LGCALDATE { 'default': (0,0,0,0,0) } +end_date
    4  LGCALREPEAT { 'default': (0,0,0,0,0) } +repeat # complicated bit mapped field
    1  UINT { 'default': 0 } +alarmindex_vibrate #LSBit of this set vibrate ON(0)/OFF(1), the 7 MSBits are the alarm index
                                                 #the alarmindex is the index into the amount of time in advance of the 
                                                 #event to notify the user. It is directly related to the alarmminutes 
                                                 #and alarmhours below, valid values are
                                                 # 8=2days, 7=1day, 6=2hours, 5=1hour, 4=15mins, 3=10mins, 2=5mins, 1=0mins, 0=NoAlarm
    1  UINT { 'default': 0 } +ringtone
    1  UINT { 'default': 0 } +unknown1
    1  UINT { 'default': 0xff } +alarmminutes  "a value of 0xFF indicates not set"
    1  UINT { 'default': 0xff } +alarmhours    "a value of 0xFF indicates not set"
    1  UINT { 'default': 0 } +unknown2
    2  UINT { 'default': 0x01FB } +unknown3
    4  UINT { 'default': 0 } +unknown4
    65 USTRING { 'default': '000000ca-00000000-0000000000-VX855V01', 'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } +serial_number

PACKET schedulefile:
    2 UINT numactiveitems
    * LIST { 'elementclass': scheduleevent, 'length': NUMCALENDARENTRIES, 'createdefault': True } +events

PACKET scheduleringerfile:
    4 UINT numringers
    * LIST +ringerpaths:
        256 USTRING { 'encoding': PHONE_ENCODING, 'raiseontruncate': True } path

PACKET textmemo:
    4 GPSDATE { 'default': GPSDATE.now(),
                'unique': True } +cdate
    301 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False, 'raiseontruncate': False } text
    4 LGCALDATE memotime # time the memo was writen LG time
    3 UNKNOWN +zeros

PACKET textmemofile:
    4 UINT itemcount
    * LIST { 'elementclass': textmemo } +items
