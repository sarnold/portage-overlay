### BITPIM
###
### Copyright (C) 2005 Stephen A. Wood <saw@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsungspha900.p 2801 2006-02-12 05:46:25Z sawecw $
 
%{

"""Proposed descriptions of data usign AT commands"""

from prototypes import *

# We use LSB for all integer like fields in diagnostic mode
UINT=UINTlsb
BOOL=BOOLlsb
#

NUMPHONEBOOKENTRIES=500
NUMEMAILS=3
NUMPHONENUMBERS=5
MAXNUMBERLEN=32
NUMTODOENTRIES=9
NUMSMSENTRIES=94

MAXMEMOLEN=72


NUMGROUPS=4

AMSREGISTRY="ams/AmsRegistry"

DEFAULT_RINGTONE=0
DEFAULT_WALLPAPER=0

%}

PACKET firmwarerequest:
    1 UINT {'constant': 0x00} +command

PACKET firmwareresponse:
    1 UINT command
    * UNKNOWN unknown

PACKET numberheader:
    1 UINT {'default': 0x26} +head1
    1 UINT {'constant': 0x39} +head2
    1 UINT {'constant': 0x0} +head3

PACKET nameheader:
    1 UINT {'default': 0xd3} +head1
    1 UINT {'constant': 0x59} +head2
    1 UINT {'constant': 0x0e} +head3

PACKET numberrequest:
    * numberheader +header
    2 UINT slot
    128 UNKNOWN +pad

PACKET numberresponse:
    * numberheader header
    2 UINT slot
    * numberentry entry
    * UNKNOWN pad

PACKET numberentry:
    1 UNKNOWN +pad1
    1 UINT pos
    1 UINT numbertype
    2 UNKNOWN +pad2
    1 UINT numlen
    48 USTRING {'raiseonunterminatedread': False} num

PACKET numberupdaterequest:
    * numberheader {'head1': 0x27} +header
    2 UINT slot
    * numberentry +entry

PACKET namerequest:
    * nameheader +header
    2 UINT slot
    140 UNKNOWN +pad

PACKET nameresponse:
    * nameheader header
    2 UINT slot
    * nameentry entry
    * UNKNOWN pad

PACKET nameentry:
    2 UINT bitmask
    2 UNKNOWN +p2
    * LIST {'length': NUMPHONENUMBERS} +numberps:
        2 UINT {'default': 0} slot
    2 UINT {'default': 0} +emailp
    2 UINT {'default': 0} +urlp
    2 UNKNOWN +p3
    1 UINT name_len
    2 UNKNOWN +pad1
    20 USTRING {'raiseonunterminatedread': False, 'raiseontruncate': False} name
    1 UNKNOWN +pad2
    20 USTRING {'raiseonunterminatedread': False, 'default': ""} +nickname
    1 UNKNOWN +pad3
    72 USTRING {'raiseonunterminatedread': False, 'default': "", 'raiseontruncate': False} +memo
    
PACKET nameupdaterequest:
    * nameheader {'head1': 0xd4} +header
    2 UINT slot
    * nameentry +entry
    3 UNKNOWN +pad
    
PACKET beginendupdaterequest:
    1 UINT {'constant': 0x29} +command
    2 UINT beginend

PACKET beginendupdateresponse:
    1 UINT command
    2 UINT beginend

PACKET statusrequest:
    1 UINT {'constant': 0x0c} +command

PACKET statusresponse:
    P UINT {'constant': 0x0} readyvalue
    1 UINT command
    3 UNKNOWN dunno1
    4 UINT esn
    1 UINT flag0
    14 UNKNOWN dunno2
    1 UINT ready
    1 UINT dunno3
    1 UINT flag2
    6 UNKNOWN dunno4
    1 UINT flag3
    * UNKNOWN unknown
    
PACKET writeenable:
    1 UINT {'constant': 0x46} +c1
    1 UINT {'constant': 0x01} +c2
    1 UINT {'constant': 0xf2} +c3
    1 UINT {'constant': 0x03} +c4
    1 UINT {'constant': 0x0f} +c5
    1 UINT {'constant': 0x5f} +c6
    1 UINT {'constant': 0x67} +c7
    1 UINT {'constant': 0x8f} +c8
    1 UINT {'constant': 0xf9} +c9
    1 UINT {'constant': 0xa2} +c10
    1 UINT {'constant': 0x3f} +c11
    1 UINT {'constant': 0x7d} +c12
    1 UINT {'constant': 0x5e} +c13
    1 UINT {'constant': 0x35} +c14
    1 UINT {'constant': 0x5c} +c15
    1 UINT {'constant': 0x7e} +c16

PACKET writeenableresponse:
    * UNKNOWN unknown
