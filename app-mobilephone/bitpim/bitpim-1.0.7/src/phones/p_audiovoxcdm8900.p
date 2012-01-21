### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_audiovoxcdm8900.p 3352 2006-06-10 15:20:39Z skyjunky $

%{

"""Various descriptions of data specific to Audiovox CDM8900"""

from prototypes import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

_NUMSLOTS=300
_NUMGROUPS=7
_ALLGROUP=0
_MAXGROUPLEN=16
_MAXPHONENUMBERLEN=32
_MAXNAMELEN=16
_MAXEMAILLEN=48
_MAXMEMOLEN=48
%}

# Audiovox commands

# 0x80  write group
# 0x81  read group
# 0x82  write phonebookentry
# 0x83  read phonebookentry
# 0x84  write slots
# 0x85  read slots

PACKET readpbslotsrequest:
    "Get a list of which slots are used"
    1 UINT {'constant': 0x85} +cmd

PACKET readpbslotsresponse:
    1 UINT {'constant': 0x85} cmd
    #  each byte is a bitmask of which fields are set although we defer to the actual entries to find that out
    * DATA present  "a non-zero value indicates a slot is present"

PACKET writepbslotsrequest:
    1 UINT {'constant': 0x84} +cmd
    * DATA present  "a non-zero value indicates a slot is present"

PACKET writepbslotsresponse:
    1 UINT {'constant': 0x84} cmd

PACKET readpbentryrequest:
    1 UINT {'constant': 0x83} +cmd
    2 UINT slotnumber

PACKET readpbentryresponse:
    1 UINT {'constant': 0x83} +cmd
    2 UINT slotnumber
    * pbentry entry

PACKET writepbentryrequest:
    1 UINT {'constant': 0x82} +cmd
    2 UINT slotnumber
    * pbentry entry

PACKET writepbentryresponse:
    1 UINT {'constant': 0x82} cmd
    2 UINT slotnumber

PACKET pbentry:
    1 UINT secret "non-zero if entry is secret/locked"
    1 UINT group   
    2 UINT previous "?index number for previous entry"
    2 UINT next     "?index number for next entry"
    # these use a fixed size buffer with counter byte saying how much to use
    33 COUNTEDBUFFEREDSTRING mobile
    33 COUNTEDBUFFEREDSTRING home
    33 COUNTEDBUFFEREDSTRING office
    33 COUNTEDBUFFEREDSTRING pager
    33 COUNTEDBUFFEREDSTRING fax
    # these have space for the field and a null terminator
    17 USTRING name
    49 USTRING email
    49 USTRING wireless
    49 USTRING memo
    2 UINT ringtone
    2 UINT msgringtone
    2 UINT wallpaper

PACKET readgroupentryrequest:
    1 UINT {'constant': 0x81} +cmd
    1 UINT number

PACKET readgroupentryresponse:
    1 UINT {'constant': 0x81} cmd
    1 UINT number
    1 UINT anothergroupnum
    2 UINT dunno "first member?"
    17 USTRING name  # always terminated
    2 UINT nummembers "how many members of the group"

PACKET writegroupentryrequest:
    1 UINT {'constant': 0x80} +cmd
    1 UINT number
    1 UINT anothernumber  "same as number"
    2 UINT {'constant': 0xffff} +dunno "?first member of the group"
    17 USTRING name
    2 UINT nummembers

PACKET writegroupentryresponse:
    1 UINT {'constant': 0x80} cmd
    
PACKET dunnorequest:
    1 UINT {'constant': 0x26} +cmd
    1 UINT {'constant': 0xf7} +cmd2
    1 UINT {'constant': 0x03} +cmd3
    1 UINT which

PACKET dunnoresponse:
    * DATA stuff


# also available but not used by BitPim
PACKET readlockcoderequest:
    1 UINT {'constant': 0x26} +cmd
    1 UINT {'constant': 0x52} +cmd2
    1 UINT {'constant': 0x00} +cmd3
    130 DATA +padding # this may not be necessary

PACKET readlockcoderesponse:
    1 UINT {'constant': 0x26} cmd
    1 UINT {'constant': 0x52} cmd2
    1 UINT {'constant': 0x00} cmd3
    * USTRING lockcode
