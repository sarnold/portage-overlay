### ( -*- Python -*- )
### Copyright (C) 2009 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
###

%{

"""Various descriptions of data specific to LG VX5500"""

from p_lgvx9700 import *
# same as the VX-9700 except as noted below

%}

# /pim/pbentry.dat format
PACKET pbfileentry:
    5   STRING { 'raiseonunterminatedread': False, 'raiseontruncate': False, 'default': '\xff\xff\xff\xff\xff' } +entry_tag
    if self.entry_tag==PB_ENTRY_SOR:
       * PBDateTime { 'defaulttocurrenttime': True } +mod_date
       6   STRING { 'terminator': None, 'default': '\xff\xff\xff\xff\xff\xff' } +unk0
       4   UINT entry_number1 # 1 based entry number -- might be just 2 bytes long
       2   UINT entry_number0 # 0 based entry number
       66  USTRING { 'encoding': 'utf_16_le', 'raiseonunterminatedread': False, 'raiseontruncate': False } +name
       2   UINT    { 'default': 0 } +group
       *  LIST {'length': NUMEMAILS} +emails:
          49 USTRING {'encoding': PHONE_ENCODING, 'raiseonunterminatedread': False} email
       2   UINT { 'default': 0xffff } +ringtone
       2   UINT { 'default': 0 } +wallpaper
       * LIST {'length': NUMPHONENUMBERS} +numbertypes:
          1 UINT { 'default': 0 } numbertype
       * LIST {'length': NUMPHONENUMBERS} +numberindices:
          2 UINT { 'default': 0xffff } numberindex
       36  USTRING { 'raiseonunterminatedread': False, 'default': '', 'encoding': PHONE_ENCODING } +memo # maybe
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

# pbgroup.dat
PACKET pbgroup:
    66 USTRING {'encoding': 'utf_16_le',
                'raiseonunterminatedread': False,
                'raiseontruncate': False,
                'default': ''} +name
    2  UINT { 'default': 0 } +groupid
    1  UINT {'default': 0} +user_added "=1 when was added by user"

PACKET pbgroups:
    "Phonebook groups"
    * LIST {'elementclass': pbgroup,
            'raiseonincompleteread': False,
            'length': MAX_PHONEBOOK_GROUPS,
            'createdefault': True} +groups
