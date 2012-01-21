### BITPIM
###
### Copyright (C) 2005 Stephen A. Wood <saw@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsungspha740.p 2801 2006-02-12 05:46:25Z sawecw $
 
%{

"""Proposed descriptions of data usign AT commands"""

from prototypes import *
from p_samsung_packet import *
from p_samsungspha620 import *

# We use LSB for all integer like fields in diagnostic mode
UINT=UINTlsb
BOOL=BOOLlsb
#

NUMPHONEBOOKENTRIES=300
NUMEMAILS=3
NUMPHONENUMBERS=6
MAXNUMBERLEN=32
NUMTODOENTRIES=9
NUMSMSENTRIES=94

NUMGROUPS=4

AMSREGISTRY="ams/AmsRegistry"

DEFAULT_RINGTONE=0
DEFAULT_WALLPAPER=0

%}

