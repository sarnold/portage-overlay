### BITPIM
###
### Copyright (C) 2004 Joe Pham <djpham@netzero.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsungscha650.p 3352 2006-06-10 15:20:39Z skyjunky $

%{
# Text in this block is placed in the output file

from prototypes import *

max_pb_slots=501
max_pb_entries=534
user_pb_entry_range=xrange(1, 501)
max_number_entries=501
max_ringtone_entries=20
max_image_entries=10

slot_file_name='nvm/nvm/pclink_tbl'
pb_file_name='nvm/nvm/dial_tbl'
number_file_name='nvm/nvm/dial'
ringtone_index_file_name='nvm/nvm/brew_melody'
ringtone_file_path='user/sound/ringer'
image_index_file_name='nvm/nvm/brew_image'
image_file_path='nvm/brew/shared'

# map all UINT fields to lsb version
UINT=UINTlsb
BOOL=BOOLlsb

%}

PACKET pbslot:
    1  UINT c0                  # either 0 or 1
    2  UINT pbbook_index        # index into pbbook
    1  UINT status              # status of this slot
    *  LIST { 'length': 4 } timestamp:
        1   UINT    t

PACKET pbslots:
    *  LIST { 'length': max_pb_slots, 'elementclass': pbslot } +slot

PACKET pbentry:
    1  UINT  c0
    2  UINT  mem_index
    1  UINT  c3
    2  UINT speed_dial_index
    2  UINT home_num_index
    2  UINT office_num_index
    2  UINT mobile_num_index
    2  UINT pager_num_index
    2  UINT fax_num_index
    2  UINT alias_num_index
    2  UINT unused_index
    2  UINT email_index
    22 USTRING {'raiseonunterminatedread': False } name
    1  UINT c4
    1  UINT ringer_type
    1  UINT group_num
    *  LIST { 'length': 7 } +c5:
        1   UINT  c5

PACKET pbbook:
    *  LIST  { 'length': max_pb_entries, 'elementclass': pbentry } +entry

PACKET number:
    2  UINT valid
    2  UINT type
    1  UINT length
    49 USTRING { 'raiseonunterminatedread': False } name
    2  UINT pb_index

PACKET numbers:
    *  LIST { 'length': max_number_entries, 'elementclass': number } +entry

PACKET ringtone:
    1  UINT c0
    1  UINT index
    1  UINT c1
    1  UINT assignment
    1  UINT c2
    17 USTRING { 'raiseonunterminatedread': False } name
    1  UINT name_len
    46 USTRING { 'raiseonunterminatedread': False } file_name
    1  UINT file_name_len
    2  UINT c3

PACKET ringtones:
    *  LIST { 'length': max_ringtone_entries, 'elementclass': ringtone } entry

PACKET image:
    1  UINT c0
    1  UINT index
    1  UINT c1
    1  UINT assignment
    17 USTRING { 'raiseonunterminatedread': False } name
    1  UINT name_len
    46 USTRING { 'raiseonunterminatedread': False } file_name
    1  UINT file_name_len
    2  UINT c2

PACKET images:
    *  LIST { 'length': max_image_entries, 'elementclass': image } entry

