### BITPIM
###
### Copyright (C) 2005 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sanyo3100.p 2766 2006-01-24 05:22:04Z sawecw $

%{

"""Various descriptions of data specific to Sanyo MM-3100"""

from prototypes import *

# Make all sanyo stuff available in this module as well
from p_sanyo import *
from p_sanyomedia import *
from p_sanyonewer import *
from p_brew import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb
_NUMPBSLOTS=300
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

PACKET req41:
    1 UINT {'default': 0x41} +fortyone
    6 USTRING {'terminator': None} msl

PACKET res41:
    1 UINT {'default': 0x41} fortyone
    1 UINT ans


PACKET fastatusrequest:
    * sanyofaheader {'faset': 0x13} +preamble
    1 UINT {'default': 0} +command
    1 UINT {'default': 0} +packettype

PACKET fastatusresponse:
    * sanyofaheader +preamble
    1 UINT {'default': 0} status
    1 UINT {'default': 0} packettype

PACKET response:
    * UNKNOWN pad
    
    
