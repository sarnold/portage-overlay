### BITPIM ( -*- python -*- )
###
### Copyright (C) 2008 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx9700.p 4719 2009-03-01 21:08:51Z hjelmn $

%{

"""Various descriptions of data specific to LG VX9700"""

# groups     - same as VX-8700
# phonebook  - LG Phonebook v1.0 (same as VX-8550)
# schedule   - same as VX-8550
from p_lgvx8550 import *

# sms        - same as VX-9100
from p_lgvx9100 import msg_record,recipient_record,sms_saved,sms_out,SMSINBOXMSGFRAGMENT,sms_in

# SMS index files
inbox_index     = "dload/inbox.dat"
outbox_index    = "dload/outbox.dat"
drafts_index    = "dload/drafts.dat"

%}

# Index files
PACKET indexentry:
    256 USTRING {'encoding': PHONE_ENCODING,
                 'raiseonunterminatedread': False,
                 'raiseontruncate': False } filename  "full pathname"
    4 UINT size
    4 UINT {'default': 0} +date
    4 UINT type
    4 UINT {'default': 0} +unk0
    4 UINT {'default': 0} +unk1
    4 UINT {'default': 0} +unk2

PACKET indexfile:
    "Used for tracking wallpaper and ringtones"
    * LIST {'elementclass': indexentry, 'createdefault': True} +items

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
    4 UINT  pbentrynum   #entry number in phonebook
    24 DATA unk2

# same as the VX-8560 without the unknown entry at the beginning of the file
PACKET callhistory:
    4 UINT numcalls
    1 UINT unk1
    * LIST {'elementclass': call, 'length': self.numcalls} +calls

                                                    
