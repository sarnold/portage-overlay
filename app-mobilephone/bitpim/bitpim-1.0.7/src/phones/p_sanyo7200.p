### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sanyo7200.p 1036 2004-03-11 04:45:16Z sawecw $

%{

"""Various descriptions of data specific to Sanyo SCP-7200"""

from prototypes import *

# Make all sanyo stuff available in this module as well
from p_sanyo import *
import p_sanyo

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
 
#for sym in dir(p_sanyo):
#    print sym
    
%}

