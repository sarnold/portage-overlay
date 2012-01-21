### BITPIM
###
### Copyright (C) 2004 Joe Pham <djpham@netzero.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsungscha670.p 3352 2006-06-10 15:20:39Z skyjunky $

%{
# Text in this block is placed in the output file

from prototypes import *

max_ringtone_entries=40
max_image_entries=30

ringtone_index_file_name='nvm/nvm/brew_melody'
ringtone_file_path='brew/ringer'
image_index_file_name='nvm/nvm/brew_image'
image_file_path='brew/shared'
cam_pix_file_path='digital_cam'
mms_image_path='mms_image'

# map all UINT fields to lsb version
UINT=UINTlsb
BOOL=BOOLlsb

%}
PACKET ringtone:
    1  UINT c0
    1  UINT index
    1  UINT c1
    1  UINT assignment
    1  UINT c2
    17 USTRING { 'raiseonunterminatedread': False } name
    1  UINT name_len
    51 USTRING { 'raiseonunterminatedread': False } file_name
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
    51 USTRING { 'raiseonunterminatedread': False } file_name
    1  UINT file_name_len
    2  UINT c2

PACKET images:
    *  LIST { 'length': max_image_entries, 'elementclass': image } entry
