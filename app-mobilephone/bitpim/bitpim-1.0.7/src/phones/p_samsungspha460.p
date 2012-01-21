### BITPIM
###
### Copyright (C) 2003-2004 Stephen A. Wood <saw@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsungspha460.p 3633 2006-10-29 22:21:33Z sawecw $
 
%{

"""Proposed descriptions of data usign AT commands"""

from prototypes import *
from p_samsung_packet import *

# We use LSB for all integer like fields in diagnostic mode
UINT=UINTlsb
BOOL=BOOLlsb
#

NUMPHONEBOOKENTRIES=250
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
    * CSVINT uslot "User Slot, Speed dial"
    * CSVINT group
    * CSVINT {'default': 20} +ringtone
    * CSVSTRING name
    * CSVINT speeddial "Which phone number assigned to speed dial uslot"
    * CSVINT {'default': 0} +dunno1
    * LIST {'length': NUMPHONENUMBERS, 'createdefault': True, 'elementclass': phonenumber} +numbers
    * CSVSTRING {'quotechar': None, 'default': ""} +dunno3
    * CSVSTRING {'quotechar': None, 'default': ""} +dunno4
    * CSVSTRING email
    * CSVTIME {'terminator': None, 'default': (1980,1,1,12,0,0)} +timestamp "Use terminator None for last item"

PACKET phonebookslotresponse:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'constant': '#PBOKR:'} command
    * pbentry entry

PACKET phonebookslotupdaterequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PBOKW=0,'} +command
    * pbentry entry
    
PACKET groupnameresponse:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'constant': '#PBGRR:'} command
    * groupnameentry entry

PACKET groupnameentry:
    * CSVINT gid
    * CSVSTRING {'terminator': None} groupname

PACKET unparsedresponse:
    * UNKNOWN pad
