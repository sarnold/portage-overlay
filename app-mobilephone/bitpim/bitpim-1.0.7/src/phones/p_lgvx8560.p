### BITPIM -*- Python -*-
###
### Copyright (C) 2008 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_lgvx8560.p 4640 2008-07-23 05:03:29Z djpham $

%{

"""Various descriptions of data specific to LG VX8560/VX8610"""

# groups     - same as VX-8700
# speeds     - same as VX-8550
# sms        - same as VX-9100/VX-9700
# calendar   - same as VX-8550
from p_lgvx9700 import *

# memo       - same as VX-8550
from p_lgvx8550 import textmemo,textmemofile

# indexentry - same as VX-8800
# indexfile  - same as VX-8800
from p_lgvx8800 import indexfile,indexentry

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
    4 UINT  pbentrynum   #entry number in phonebook
    24 DATA unk2

PACKET callhistory:
    4 UINT { 'default': 0x00020000 } unk0
    4 UINT numcalls
    1 UINT unk1
    * LIST {'elementclass': call} +calls
