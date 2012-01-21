### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_brew.p 4614 2008-06-02 00:15:05Z sawecw $

%{

"""Various descriptions of data used in Brew Protocol"""

from prototypes import *

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

new_fileopen_mode_read=0
new_fileopen_mode_write=0x41
new_fileopen_flag_existing=0
new_fileopen_flag_create=1

import com_brew

DEFAULT_PHONE_ENCODING='ascii'
PHONE_ENCODING=DEFAULT_PHONE_ENCODING

# These parameters only work with BREW2 at the moment.
# Note about read block size:
#  - Largest successful read size: 1KB
#  - The LG VX-8700 returns 1KB of data if req.bytes >= 1KB.
#  - If all phones behave in this way it would be safe to change the default read size to 1KB.
BREW_READ_SIZE=0xEB

# Note about write block size:
#  - Largest successful write size: 7.9kB
#  - Too large a write block will cause a timeout error.
BREW_WRITE_SIZE=0xEA

%}

# Note that we don't include the trailing CRC and 7f

PACKET requestheader:
    "The bit in front on all Brew request packets"
    1 UINT {'constant': 0x59} +commandmode
    1 UINT command

PACKET responseheader:
    "The bit in front on all Brew response packets"
    1 UINT {'constant': 0x59} commandmode
    1 UINT command
    1 UINT errorcode

PACKET readfilerequest:
    * requestheader {'command': 0x04} +header
    1 UINT {'constant': 0} +blocknumber
    * USTRING {'terminator': 0, 'pascal': True,
               'encoding': PHONE_ENCODING } filename

PACKET readfileresponse:
    * responseheader header
    1 UINT blockcounter
    1 BOOL thereismore "true if there is more data available after this block"
    4 UINT filesize
    2 UINT datasize
    * DATA {'sizeinbytes': self.datasize} data

PACKET readfileblockrequest:
    * requestheader {'command': 0x04} +header
    1 UINT blockcounter  "always greater than zero, increment with each request, loop to 0x01 from 0xff"

PACKET readfileblockresponse:
    * responseheader header
    1 UINT blockcounter
    1 BOOL thereismore  "true if there is more data available after this block"
    2 UINT datasize
    * DATA {'sizeinbytes': self.datasize} data

PACKET writefilerequest:
    * requestheader {'command': 0x05} +header
    1 UINT {'value': 0} +blockcounter
    1 BOOL {'value': self.filesize>0x100} +*thereismore
    1 UINT {'constant': 1} +unknown1
    4 UINT filesize
    4 UINT {'constant': 0x000100ff} +unknown2 "probably file attributes"
    * USTRING {'terminator': 0, 'pascal': True,
               'encoding': PHONE_ENCODING } filename
    2 UINT {'value': len(self.data)} +*datalen
    * DATA data
        
PACKET writefileblockrequest:
    * requestheader {'command': 0x05} +header
    1 UINT blockcounter
    1 BOOL thereismore
    2 UINT {'value': len(self.data)} +*datalen
    * DATA data
    
PACKET listdirectoriesrequest:
    "Lists the subdirectories of dirname"
    * requestheader {'command': 0x02} +header
    * USTRING {'terminator': 0, 'pascal': True,
               'encoding': PHONE_ENCODING } dirname

PACKET listdirectoriesresponse:
    * responseheader header
    2 UINT numentries
    if self.numentries>0:
        # Samsung A620 has garbage from this point on if numentries==0
        2 UINT datalen
        * LIST {'length': self.numentries} items:
            * USTRING { 'encoding': PHONE_ENCODING } subdir
    
PACKET listfilerequest:
    "This gets one directory entry (files only) at a time"
    * requestheader {'command': 0x0b} +header
    4 UINT entrynumber
    * USTRING {'terminator': 0, 'pascal': True,
               'encoding': PHONE_ENCODING } dirname

PACKET listfileresponse:
    * responseheader header
    4 UINT entrynumber  
    4 UNKNOWN unknown1  "probably the file attributes"
    4 UINT date         
    4 UINT size         
    4 UNKNOWN unknown2
    * com_brew.SPURIOUSZERO spuriouszero  "on some models there is a zero here"
    1 UINT dirnamelen "which portion of the filename is the directory, including the last /"
    * com_brew.EXTRAZERO extrazero  "on some models there is a zero here"
    * USTRING {'terminator': None, 'pascal': True,
               'encoding': PHONE_ENCODING } filename 

PACKET listdirectoryrequest:
    "This gets one directory entry (directory only) at a time"
    * requestheader {'command': 0x0a} +header
    4 UINT entrynumber
    * USTRING {'terminator': 0, 'pascal': True,
               'encoding': PHONE_ENCODING } dirname

PACKET listdirectoryresponse:
    * responseheader header
    4 UINT entrynumber  
    17 UNKNOWN unknown1  "probably the directory attributes"
    * com_brew.EXTRAZERO extrazero  "on some models there is a zero here"
    * USTRING {'terminator': None, 'pascal': True,
               'encoding': PHONE_ENCODING } subdir 

PACKET statfilerequest:
    "Get the status of the file"
    * requestheader { 'command': 7 } +header
    * USTRING {'terminator': 0, 'pascal': True,
               'encoding': PHONE_ENCODING } filename

PACKET statfileresponse:
    * responseheader header
    4 UNKNOWN unknown1  "probably the file attributes"
    4 UINT date         
    4 UINT size         
    
PACKET mkdirrequest:
    * requestheader {'command': 0x00} +header
    * USTRING {'terminator': 0, 'pascal': True,
               'encoding': PHONE_ENCODING } dirname

PACKET rmdirrequest:
    * requestheader {'command': 0x01} +header
    * USTRING {'terminator': 0, 'pascal': True,
               'encoding': PHONE_ENCODING } dirname

PACKET rmfilerequest:
    * requestheader {'command': 0x06} +header
    * USTRING {'terminator': 0, 'pascal': True,
               'encoding': PHONE_ENCODING } filename

PACKET memoryconfigrequest:
    * requestheader {'command': 0x0c} +header

PACKET memoryconfigresponse:
    * responseheader header
    4 UINT amountofmemory  "how much memory the EFS has in bytes"

PACKET firmwarerequest:
    1 UINT {'constant': 0x00} +command

PACKET firmwareresponse:
    1 UINT command
    11 USTRING {'terminator': None}  date1
    8 USTRING {'terminator': None}  time1
    11 USTRING {'terminator': None}  date2
    8 USTRING {'terminator': None}  time2
    8 USTRING {'terminator': None}  string1
    1 UNKNOWN dunno1
    11 USTRING {'terminator': None}  date3
    1 UNKNOWN dunno2
    8 USTRING {'terminator': None}  time3
    11 UNKNOWN dunno3
    10 USTRING {'terminator': None}  firmware
    # things differ from this point on depending on the model
    # 7 UNKNOWN dunno4
    # 16 USTRING {'terminator': None}  phonemodel
    # 5 USTRING {'terminator': None}  prl

PACKET ESN_req:
    1 UINT { 'default': 1, 'constant': 1 } +command

PACKET ESN_resp:
    1 UINT { 'constant': 1 } command
    4 UINT esn

PACKET testing0crequest:
    1 UINT {'constant': 0x0c} +command

PACKET testing0cresponse:
    * UNKNOWN pad

PACKET setmoderequest:
    1 UINT {'constant': 0x29} +command
    1 UINT request  "1=offline 2-reset.  Reset has no effect unless already offline"
    1 UINT {'constant': 0x00} +zero

PACKET setmoderesponse:
    * UNKNOWN pad

PACKET setmodemmoderequest:
    # Tell phone to leave Diagnostic mode back to modem mode where AT
    # commands work.  In qcplink, this was called reboot.  Perhaps it reboots
    # older phones.  For at least some Sanyo and Samsung phones, it puts
    # phone back in modem mode without a reboot.
    1 UINT  {'constant': 0x44} +command

PACKET setfileattrrequest:
    "Set the attributes of the file"
    * requestheader { 'command': 8 } +header
    4 UINT {'constant': 0x000100ff} +unknown "probably file attributes"
    4 UINT date  # in GPS time
    * USTRING {'terminator': 0, 'pascal': True,
               'encoding': PHONE_ENCODING } filename

PACKET data:
    * DATA bytes

# these "new" commands are for the RealBrewProtocol2 class, they are an
# alternative way to talk to newer phones such as the lg vx8100
# all the date/time fields are in unix time, a change from GPS time
# that the '59' commands use. The phone also knows what time zone it is 
# in so the time needs to be localized for displaying

PACKET new_requestheader:
    "The bit in front on all Brew request packets"
    2 UINT {'constant': 0x134B} +commandmode
    1 UINT command
    1 UINT {'constant': 0} +zero

PACKET new_responseheader:
    "The bit in front on all Brew response packets"
    2 UINT {'constant': 0x134B} commandmode
    1 UINT command
    1 UINT zero

PACKET new_openfilerequest:
    * new_requestheader {'command': 0x02} +header
    4 UINT mode # 0=read, 0x41=write
    4 UINT flags # 0=open_existing, 1=create
    * USTRING {'terminator': 0,
               'encoding': PHONE_ENCODING } filename
        
PACKET new_openfileresponse:
    * new_responseheader header
    4 UINT handle
    4 UINT error # matches unix error codes

PACKET new_closefilerequest:
    * new_requestheader {'command': 0x03} +header
    4 UINT handle

PACKET new_closefileresponse:
    * new_responseheader header
    4 UINT error # matches unix error codes

PACKET new_readfilerequest:
    * new_requestheader {'command': 0x04} +header
    4 UINT handle
    4 UINT bytes # max 0xEB observed
    4 UINT position

PACKET new_readfileresponse:
    * new_responseheader header
    4 UINT handle
    4 UINT position # position the bytes were read from
    4 UINT bytes # less than requested if EOF
                 # there is no EOF flag in the packet
    4 UINT error # matches unix error codes
    * DATA {'sizeinbytes': self.bytes} data

PACKET new_writefilerequest:
    * new_requestheader {'command': 0x05} +header
    4 UINT handle
    4 UINT position
    P UINT bytes
    * DATA {'sizeinbytes': self.bytes} data # max 243 bytes

PACKET new_writefileresponse:
    * new_responseheader header
    4 UINT handle
    4 UINT position # position the bytes were written to
    4 UINT bytes
    4 UINT error # matches unix error codes

PACKET new_rmfilerequest:
    """Remove file, full path should be provided, 
    but the root character / is not required at the start of the name.
    """
    * new_requestheader {'command': 0x08} +header
    * USTRING {'terminator': 0,
               'encoding': PHONE_ENCODING } filename
    1 UINT {'constant':1} +dunno

PACKET new_mkdirrequest:
    """Make a new directory, full path of the new directory should be
    provided, but the root character / is not required at the start of the name
    """
    * new_requestheader {'command': 0x09} +header
    2 UINT {'constant': 0x01ff} +mode # mode_t type. example 0777 == 0x1ff == rwxrwxrwx
    * USTRING {'terminator': 0,
               'encoding': PHONE_ENCODING } dirname

PACKET new_rmdirrequest:
    """Remove directory, full path should be provided, but the
    root character / is not required at the start of the name.
    """
    * new_requestheader {'command': 0x0a} +header
    * USTRING {'terminator': 0,
               'encoding': PHONE_ENCODING } dirname

PACKET new_opendirectoryrequest:
    * new_requestheader {'command': 0x0b} +header
    * USTRING {'terminator': 0,
               'encoding': PHONE_ENCODING } dirname

PACKET new_opendirectoryresponse:
    * new_responseheader header
    4 UINT handle
    4 UINT error # matches unix error codes

PACKET new_listentryrequest:
    * new_requestheader {'command': 0x0c} +header
    4 UINT handle
    4 UINT entrynumber

PACKET new_listentryresponse:
    * new_responseheader header
    4 UINT handle
    4 UINT entrynumber
    4 UINT pad1 # zeros
    4 UINT type # 0=file 1=directory
    4 UINT mode 
    4 UINT size # garbage for directories
    8 UINT pad2 # zero
    4 UINT date # LG date format, date file created
    * USTRING {'terminator': 0,
               'encoding': PHONE_ENCODING } entryname

PACKET new_closedirectoryrequest:
    * new_requestheader {'command': 0x0d} +header
    4 UINT handle

PACKET new_closedirectoryresponse:
    * new_responseheader header
    4 UINT error # matches unix error codes

PACKET new_statfilerequest:
    "Get the status of the file"
    * new_requestheader { 'command': 0x0f } +header
    * USTRING {'terminator': 0,
               'encoding': PHONE_ENCODING } filename

PACKET new_statfileresponse:
    * new_responseheader header
    4 UINT error # matches unix error codes
    4 UNKNOWN dunno # flags of some sort
    4 UINT size # for directories this is the number of entries+2 (maybe '.' and'..' are counted internally) aka. link count (man ls)
    4 UINT type # 1=file, 2+=directory (if 2+ this field is number of subdirectories + 2)
    4 UINT accessed_date
    4 UINT modified_date
    4 UINT created_date

PACKET new_chmodrequest:
    * new_requestheader {'command': 0x12} +header
    2 UINT +mode # mode_t
    * USTRING {'terminator': 0, 'encoding': PHONE_ENCODING } +filename

PACKET new_chmodresponse:
    * new_responseheader header
    4 UINT error # matches unix error codes

PACKET new_reconfigfilesystemrequest:
    """Called after mkdir/rmdir and writing files,
    possibly a filesystem status request with space used/free etc.
    """
    * new_requestheader {'command': 0x13} +header
    2 UINT {'constant': 0x002f} +dirname # happens to be the same as / which is the root

PACKET new_reconfigfilesystemresponse:
    * new_responseheader header
    44 UNKNOWN +unknown # some data in here unsure of meaning

%{
# Several responses are nothing
mkdirresponse=responseheader
rmdirresponse=responseheader
rmfileresponse=responseheader
writefileresponse=responseheader
writefileblockresponse=responseheader
setfileattrresponse=responseheader
new_mkdirresponse=new_responseheader
new_rmdirresponse=new_responseheader
new_rmfileresponse=new_responseheader
%}
