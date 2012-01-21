### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sanyo5300.p 1026 2004-03-09 07:47:20Z rogerb $

%{

"""Various descriptions of data specific to Sanyo SCP-5300"""

from prototypes import *

# Make all sanyo stuff available in this module as well
from p_sanyo import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb
_NUMPBSLOTS=300
_NUMSPEEDDIALS=8
_NUMLONGNUMBERS=5
_LONGPHONENUMBERLEN=30
_NUMEVENTSLOTS=100
_NUMCALLALARMSLOTS=15
_NUMCALLHISTORY=20
_MAXNUMBERLEN=48
_MAXEMAILLEN=48
%}


# No 5300 Specific definitions yet
