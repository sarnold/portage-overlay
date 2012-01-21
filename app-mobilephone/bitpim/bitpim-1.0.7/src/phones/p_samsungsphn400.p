### BITPIM
###
### Copyright (C) 2006 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsungsphn400.p 3352 2006-06-10 15:20:39Z skyjunky $

%{

"""Various descriptions of data specific to Sanyo phones"""

from prototypes import *

# We use LSB for all integer like fields

UINT=UINTlsb
BOOL=BOOLlsb

 %}

PACKET getphonestatus:
    1 UINT {'constant': 0x0c} +command
    
PACKET getphoneresponse:
    * UNKNOWN pad
    
PACKET firmwarerequest:
    1 UINT {'constant': 0x00} +command

PACKET firmwareresponse:
    1 UINT command
    11 USTRING {'terminator': None}  date1
    8 USTRING {'terminator': None}  time1
    11 USTRING {'terminator': None}  date2
    8 USTRING {'terminator': None}  time2
    8 USTRING {'terminator': None}  string1
    8 UNKNOWN dunno1

PACKET esnrequest:
    1 UINT {'constant': 0x01} +command

PACKET beginendupdaterequest:
    1 UINT {'constant': 0x29} +command
    1 UINT beginend

PACKET {'readwrite': 0x26} samheader:
    1 UINT readwrite
    2 UINT attribute
    
PACKET phonebooknamerequest:
    * samheader {'attribute': 0x026B} +header
    1 UINT slot
    129 UNKNOWN +pad

PACKET phonebookname:
    1 UNKNOWN pad1
    2 UINT nonzeroifused
    2 UINT pspeed
    * LIST {'length': 7} numbers:
        2 UINT pnumber
    2 UINT pemail
    2 UINT purl
    2 UINT dunno2
    12 USTRING name
    3 UNKNOWN pad2
    87 UNKNOWN pad2
    2 UINT {'default': 5} sometimesfive
    
PACKET phonebooknameresponse:
    * samheader header
    1 UINT slot
    * phonebookname entry
    * UNKNOWN pad

PACKET phonebooknumbersrequest:
    * samheader {'attribute': 0x026A} +header
    1 UINT slot
    129 UNKNOWN +pad

PACKET phonebooknumbers:
    2 UNKNOWN pad
    1 UINT number_len
    32 USTRING {'raiseonunterminatedread': False} number
    
PACKET phonebooknumbersresponse:
    * samheader header
    1 UINT slot
    * phonebooknumbers entry
    * UNKNOWN pad

PACKET attributerequest:
    1 UINT {'constant': 0x26} +command
    2 UINT attribute
    259 UNKNOWN +pad

    

