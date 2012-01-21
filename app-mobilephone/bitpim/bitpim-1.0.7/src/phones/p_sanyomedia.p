### BITPIM
###
### Copyright (C) 2004 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_sanyomedia.p 3352 2006-06-10 15:20:39Z skyjunky $

%{

"""Descriptions of Sanyo Media Packets"""

from prototypes import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

%}

# Experimental packet descriptions for media upload.  Eventually move into
# p_sanyo.p


# Eventually move to p_sanyo.p because this header is
# used by many phones.
# faset values:
#   0x02  Phonebook protocol read
#   0x03  Phonebook protocol write
#   0x05  Sanyo4900 media upload
#   0x10  

PACKET sanyomediaheader:
    2 UINT {'constant': 0xfa} +fa
    1 UINT {'default': 0x09} +faset
    2 UINT command
    2 UINT {'default': 0xffff} +pad

PACKET sanyochangedir:
    * sanyomediaheader {'command': 0x71} +header
    170 UNKNOWN +pad
    2 UINT dirindex
    
PACKET sanyochangedirresponse:
    * sanyomediaheader header
    169 UNKNOWN +pad
    1 UINT status
    2 UINT dirindex
    
PACKET sanyonumfilesrequest:
    * sanyomediaheader {'command': 0x72} +header
    172 UNKNOWN +pad

PACKET sanyonumfilesresponse:
    * sanyomediaheader header
    165 UNKNOWN +pad1
    1 UINT count
    6 UNKNOWN +pad2
    
PACKET sanyomediafilenamerequest:
    * sanyomediaheader {'command': 0x73} +header
    161 UNKNOWN +pad1
    1 UINT index
    10 UNKNOWN +pad2

PACKET sanyomediafilenameresponse:
    * sanyomediaheader header
    1 UINT pad1
    154 USTRING filename
    1 UINT num1
    1 UNKNOWN pad2
    1 UINT num2
    1 UNKNOWN pad3
    1 UINT num3
    1 UNKNOWN pad4
    1 UINT num4
    10 UNKNOWN pad5
    
PACKET sanyomediafragmentrequest:
    * sanyomediaheader {'command': 0x74} +header
    155 UNKNOWN +pad1
    1 UINT fileindex
    16 UNKNOWN +pad2

PACKET sanyomediafragmentresponse:
    * sanyomediaheader header
    1 UNKNOWN pad1
    150 DATA data
    1 UINT length
    3 UNKNOWN pad2
    1 UINT fileindex
    15 UNKNOWN pad3
    1 UINT more

PACKET sanyomediafilegragment:
    * sanyomediaheader +header
    2 UINT {'constant': 0} +word
    1 UINT {'constant': 150} +len
    150 DATA data
    21 UNKNOWN +pad
    
PACKET sanyomediaresponse:
    * sanyomediaheader header
    * UNKNOWN UNKNOWN
    
PACKET sanyosendfilename:
    * sanyomediaheader {'command': 0xffa1, 'pad': 0, 'faset': 0x05} +header
    1 UINT {'constant': 0x96} +payloadsize
    150 USTRING {'default': ""} +filename
    21 UNKNOWN +pad

PACKET sanyosendfilesize:
    * sanyomediaheader {'command': 0xffc1, 'pad': 0, 'faset': 0x05} +header
    1 UINT {'constant': 0x96} +payloadsize
    1 UNKNOWN +pad1
    2 UINT filesize
    168 UNKNOWN +pad2 

PACKET sanyosendfilefragment:
    * sanyomediaheader {'pad': 0, 'faset': 0x05} +header
    1 UINT {'constant': 0x96} +payloadsize
    150 DATA data
    21 UNKNOWN +pad

PACKET sanyosendfileterminator:
    * sanyomediaheader {'command': 0xffe1, 'pad': 0, 'faset': 0x05} +header
    1 UINT {'constant': 0x96} +payloadsize
    171 UNKNOWN +pad

PACKET sanyosendfileresponse:
    * sanyomediaheader +header
    1 UINT payloadsize
    171 UNKNOWN pad

PACKET sanyomediathingyrequest:
    2 UINT {'constant': 0xfa} +fa
    1 UINT faset
    2 UINT {'default': 0x0} +value
    
PACKET sanyomediathingyresponse:
    2 UINT fa
    1 UINT faset
    2 UINT value
    
