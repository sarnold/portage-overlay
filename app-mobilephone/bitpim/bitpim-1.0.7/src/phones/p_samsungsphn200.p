### BITPIM
###
### Copyright (C) 2003-2004 Stephen A. Wood <saw@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsungsphn200.p 3352 2006-06-10 15:20:39Z skyjunky $
 
%{

"""Proposed descriptions of data usign AT commands"""

from prototypes import *
from p_samsung_packet import *

# We use LSB for all integer like fields in diagnostic mode
UINT=UINTlsb
BOOL=BOOLlsb
#

NUMPHONEBOOKENTRIES=239
NUMPHONENUMBERS=6
NUMCALENDAREVENTS=70
MAXNUMBERLEN=32
NUMTODOENTRIES=20

NUMGROUPS=4

%}

# Packets describe single line AT responses or commands with no carriage
# returns or line feeds.

PACKET pbentry:
    P USTRING {'default': ""} +url
    P CSVDATE {'default': ""} +birthday
    * CSVINT slot "Internal Slot"
    * CSVSTRING name
    * CSVINT {'default': 255} +dunno1
    * LIST {'elementclass': phonenumber} +numbers

PACKET phonenumber:
    P BOOL {'default': True} +last_number
    * CSVINT +numbertype
    if not self.last_number:
        * CSVSTRING {'quotechar': None, 'default': ""} +number
    if self.last_number:
        * CSVSTRING {'quotechar': None, 'default': "", 'terminator': None} +number

PACKET phonebookslotrequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PBOKR='} +command
    * CSVINT {'terminator': None} +slot "Internal Slot"

PACKET phonebookslotresponse:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'constant': '#PBOKR:'} command
    * pbentry entry

PACKET phonebookslotupdaterequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PBOKW='} +command
    * pbentry entry
    
