### BITPIM
###
### Copyright (C) 2005 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sanyo2300.p 2707 2006-01-01 03:33:18Z sawecw $

%{

"""Various descriptions of data specific to Sanyo VI-2300"""

from prototypes import *

# Make all sanyo stuff available in this module as well
from p_sanyo import *
from p_sanyomedia import *
from p_sanyonewer import *

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
_MAXNUMBERLEN=32
_MAXEMAILLEN=96
 
#for sym in dir(p_sanyo):
#    print sym
    
%}

