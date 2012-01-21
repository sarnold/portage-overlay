### BITPIM
###
### Copyright (C) 2006 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$

%{

"""Various descriptions of data specific to Sanyo MM-7500"""

from prototypes import *

# Make all sanyo stuff available in this module as well
from p_sanyo import *
from p_sanyomedia import *
from p_sanyonewer import *
from p_sanyo4930 import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb
_NUMPBSLOTS=500
_NUMSPEEDDIALS=8
_NUMLONGNUMBERS=5
_LONGPHONENUMBERLEN=30
_NUMEVENTSLOTS=100
_NUMCALLALARMSLOTS=15
 # Need to check.  Is max phone will hold 32/96 or 33/97
_MAXNUMBERLEN=32
_MAXEMAILLEN=96
HASRINGPICBUF=0

#BREW_FILE_SYSTEM=2

%}

PACKET messagesententry:
    1 UINT slot
    1 UINT read
    1 UINT counter
    3 UNKNOWN pad1
    1 UINT dunno1
    1 UINT dunno2
    1 UINT dunno3
    1 UNKNOWN pad2
    1 UINT dunno4
    1 UINT dunno5
    1 UNKNOWN pad3
    1 UINT message_len
    255 USTRING message "Text of the notification"
    2 UNKNOWN pad4
    1 UINT year
    1 UINT month
    1 UINT day
    1 UINT hour
    1 UINT minute
    1 UINT second
    1 UINT callback_len
    34 USTRING callback
    1 UINT phonenum_len
    37 USTRING phonenum
    1 UINT dunno6
    1 UINT priority
    3 UNKNOWN pad6
    1 UINT dunno7
    1 UINT dunno8

PACKET messagesentresponse:
    * sanyoheader header
    * messagesententry entry
    * UNKNOWN pad

