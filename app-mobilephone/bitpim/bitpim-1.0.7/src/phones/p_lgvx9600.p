### BITPIM ( -*- python -*- )
###
### Copyright (C) 2008 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx9600.p 4754 2009-08-02 18:11:17Z hjelmn $

%{

"""Various descriptions of data specific to LG VX9700"""

# groups     - same as VX-8700
# phonebook  - LG Phonebook v1.0 (same as VX-8550)
# schedule   - same as VX-8550
# sms        - same as VX-9700
# memos      - same as VX-8550
# call history - same as VX-9700
from p_lgvx9700 import *

# SMS index files
inbox_index     = "dload/inbox.dat"
outbox_index    = "dload/outbox.dat"
drafts_index    = "dload/drafts.dat"

# Phonebook favorites
favorites_file_name  = "pim/pbFavorite.dat"
NUMFAVORITES=10

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
    2 UINT  pbentrynum   #entry number in phonebook
    27 DATA unk2

PACKET callhistory:
    4 UINT numcalls
    1 UINT unk1
    * LIST {'elementclass': call} +calls


# Favorites -- added on the Versa (LG VX-9600)
PACKET favorite:
    2 UINT { 'default': 0 }      +unk0
    2 UINT { 'default': 0xffff } +pb_index  # contact or group id
    4 UINT { 'default': 0 }      +unk1
    4 UINT { 'default': 0x45 }   +unk2
    %{
    def has_pbentry(self):
        return self.pb_index != 0xffff
    %}

PACKET favorites:
    2 UINT { 'default': 0 } +count
    * LIST { 'elementclass': favorite, 'length': self.count } +items
    * LIST { 'length': NUMFAVORITES - self.count } pad:
        12 DATA { 'default': '\xff'*507 } +dontcare
    %{
    def set_favorite(self, index, entity_index, ispbentry):
        # index is not used for the VX-9600
        if ispbentry and count < NUMFAVORITES:
            new_favorite = self.favorite ()
            new_favorite.pb_index = entity_index
            self.items.append (new_favorite)
            self.count += 1
    %}

