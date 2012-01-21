### BITPIM
###
### Copyright (C) 2005 Yosef Meller <mellerf@netvision.net.il>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sk6100.p 3092 2006-04-13 03:13:47Z skyjunky $

%{

"""Various descriptions of data specific to SKTT IMT2000"""

from prototypes import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

NUM_PBENTRIES=1200
NUM_PBGROUPS=41
NUM_PHONES=2400

%}

PACKET wholebook:
    16 USTRING filename
    * LIST {'elementclass': pbentry, 'length': NUM_PBENTRIES}	pbentries

PACKET pbentry:
    1 UINT	slot		"All of them are numbered"
    3 UNKNOWN	unk1	
    1 UINT	group_id
    1 UNKNOWN	unk3	
    1 UINT	record		"Only nonzero if not deleted"
    5 UNKNOWN	unk4
    20 USTRING { 'encoding': 'iso-8859-8' } name 		"The place until the zeroes end"
    96 UNKNOWN	unk2	

PACKET groups:
    16 USTRING	filename	"group file name"
    * LIST	{'elementclass': pbgroup, 'length': NUM_PBGROUPS}	pbgroups

PACKET pbgroup:
    1 UINT	group_id	
    3 UNKNOWN	unk1
    21 USTRING { 'encoding': 'iso-8859-8' } name
    1 UINT	unk3
    30 UNKNOWN	unk2

PACKET phones:
    16 USTRING	filename
    * LIST {'elementclass': phone, 'length': NUM_PHONES} records

# 44 total record length
PACKET phone:
    2 UINT	slot
    4 UINT	others
    4 UINT	owner_id
    1 UINT	type	"Home / Work / Cell / Fax"
    33 USTRING	number
