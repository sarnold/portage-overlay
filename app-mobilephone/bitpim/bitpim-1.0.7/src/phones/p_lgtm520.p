### BITPIM
###
### Copyright (C) 2003 Scott Craig <scott.craig@shaw.ca>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###


%{

"""Various descriptions of data specific to LG TM520"""

from prototypes import *

# Make all lg stuff available in this module as well
from p_lg import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

%}


PACKET pbreadentryresponse:
    "Results of reading one entry"
    *  pbheader header
    *  pbentry  entry

PACKET pbupdateentryrequest:
    * pbheader {'command': 0x04, 'flag': 0x01} +header
    * pbentry entry

PACKET pbappendentryrequest:
    * pbheader {'command': 0x03, 'flag': 0x01} +header
    * pbentry entry

    
# All STRINGS have raiseonterminatedread as False since the phone does
# occassionally leave out the terminator byte
PACKET numentry:
    33 USTRING {'raiseonunterminatedread': False} number
    1  UINT chksum

PACKET pbentry:
    "Results of reading one entry"
    P  UINT {'constant': 1} numberofemails
    P  UINT {'constant': 5} numberofphonenumbers
    4  UINT serial1     " == order created"
    2  UINT {'constant': 0xf5} +entrysize
    4  UINT serial2     "Same as serial1"
    1  UINT entrynumber
    17 USTRING {'raiseonunterminatedread': False} name
    1  BOOL secret
    1  UINT default	"Default number"
    * LIST {'length': self.numberofphonenumbers, 'elementclass': numentry, 'createdefault': True} +numbers
    1  UINT ringtone	"ringtone index for a call, 0x17 for custom"
    1  BOOL voicetag
    49 USTRING {'raiseonunterminatedread': False} +email

PACKET ringentry:
    1  UINT index	"Phonebook entry number"
    40 USTRING {'raiseonunterminatedread': False} name	"Path of custom ringer, or default"

PACKET ringindex:
    P UINT {'constant': 199} maxitems
    * LIST {'length': self.maxitems, 'elementclass': ringentry, 'createdefault': True} +items

PACKET scheduleevent:
    1 UINT state	"02 for an new entry, 01 for a modified entry, 00 for blank entry"
    1 UINT pos "position within file, used as an event id"
    1 UINT alarm	"00 => created, 80 => modified/never been used, B0 => alarm"
    4 UINT date
    1 UINT repeat	"01 => used, 02 => daily"
    32 USTRING {'raiseonunterminatedread': False} description
 

# Maximum of 50 entries, first one is the wake-up alarm
PACKET schedulefile:
    * LIST {'length': 50, 'elementclass': scheduleevent} +events
