### BITPIM
###
### Copyright (C) 2006 Denis Tonn <denis@tonn.ca>
### Inspiration and code liberally adopted from:
### Stephen A. Wood and Joe Pham
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$
 
%{

"""Proposed descriptions of data usign AT commands"""

from prototypes import *
from p_samsung_packet import *

# We use LSB for all integer like fields in diagnostic mode
UINT=UINTlsb
BOOL=BOOLlsb
#

NUMCALENDAREVENTS=20
NUMPHONEBOOKENTRIES=500
NUMEMAILS=1
NUMPHONENUMBERS=5
MAXNUMBERLEN=32
NUMTODOENTRIES=9
NUMSMSENTRIES=94

NUMMEMOENTRIES=3


NUMGROUPS=4

# Phone does not cleanly return from BREW mode, so everything done through modem mode
# AMSREGISTRY="ams/AmsRegistry"

DEFAULT_RINGTONE=0
DEFAULT_WALLPAPER=8
DEFAULT_WALLPAPER_MODIFIER=0
DEFAULT_GROUP=0

%}

PACKET pbentry:
    * CSVINT slot "Internal Slot"
    * CSVINT uslot "User Slot, Speed dial"
# Phone does not support groups properly - default 0
    * CSVINT {'default': 0} +group 
# 0=default 1-5=Ring 1-5 6-10=Melody 1-5
    * CSVINT {'default': 0} +ringtone "0: Default, 1: Ring 1, 2: Ring 2, 3: Ring 3, 4: Ring 4, 5: Ring 5, 6: Melody 1, 7: Melody 2, 8: Melody 3, 9: Melody 4, 10: Melody 5"
    * CSVSTRING name
    * CSVINT speeddial "Which phone number assigned to speed dial uslot"
    * CSVINT {'default': 0} +dunno1
    * LIST {'length': NUMPHONENUMBERS, 'createdefault': True, 'elementclass': phonenumber} +numbers
# email and url must have a space in the value when writing    
    * CSVSTRING {'default': ""} +email 
# actually there are 2 email addresses but this simplified my cut and paste
    * CSVSTRING {'default': ""} +url
# this is really a freeform text field, but can be used for birthdays - perhaps should be a memo.. 
    * CSVSTRING {'default': ""} +birthday
# wallpaper values    
# 8 = no image
# 3 = human
# 4 = animal
# 5 = others
# 2 = gallery - and wallpaper_pic_path points to the file name
# 7 = image clips 
    * CSVINT {'default': 8} +wallpaper "8: No Image, 3: Human, 4: Animal, 5: Other, 2: Gallery, 7: Image"
# wallpaper_modifier   
# selects specific image in human, animal, others
# selects offset in file for image clips
# must be 0 if no image
# value ignored if gallery image
    * CSVINT {'default': 0} +wallpaper_modifier
    * CSVSTRING wallpaper_file
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
    * CSVSTRING groupname
    * CSVINT {'default': 0} +unknown_4
    * CSVSTRING {'quotechar': None} dunno2 "A single character C or S"
    * CSVTIME {'terminator': None} timestamp

PACKET unparsedresponse:
    * UNKNOWN pad
    
PACKET eventrequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PISHR='} +command
    * CSVINT {'terminator': None} +slot

PACKET eventresponse:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'constant': '#PISHR:'} command
    * CSVINT slot
    * CSVTIME start
    * CSVTIME end
    * CSVTIME timestamp
    * CSVINT alarm "0: No Alarm, 1: On Time, 2: 10 minutes, 3: 30 minutes, 4: 60 minutes"
    * CSVSTRING {'quotechar': None} dunno
    * CSVSTRING {'terminator': None} eventname

PACKET eventupdaterequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PISHW='} +command
    * CSVINT slot
    * CSVTIME start
    * CSVTIME end
    * CSVTIME timestamp
    * CSVINT alarm "0: No Alarm, 1: On Time, 2: 10 minutes, 3: 30 minutes, 4: 60 minutes"
    * CSVSTRING {'terminator': None} eventname
    
PACKET eventsloterase:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PISHW='} +command
    * CSVINT {'terminator': None} +slot

PACKET eventupdateresponse:
    * UNKNOWN pad
    
