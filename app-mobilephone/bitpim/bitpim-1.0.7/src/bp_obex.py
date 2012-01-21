### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: bp_obex.py 3460 2006-07-08 23:55:09Z djpham $

"""Provide support to OBEX protocol"""

# System Modules
import time
import struct
import xml.dom.minidom

# BitPim modules
import bptime

module_debug=False

# Header Codes
Header_Count=0xC
Header_Name=0x01
Header_Type=0x42
Header_Length=0xC3
Header_Time=0x44
Header_Description=0x05
Header_Target=0x46
Header_HTTP=0x47
Header_Body=0x48
Header_BodyEnd=0x49
Header_Who=0x4A
Header_ConnectionID=0xCB
Header_AppParameters=0x4C
Header_AuthChallenge=0x4D
Header_AuthResponse=0x4E
Header_ObjectClass=0x4F
# Header String
Header_Count_Str='Count'
Header_Name_Str='Name'
Header_Type_Str='Type'
Header_Length_Str='Length'
Header_Time_Str='Time'
Header_Description_Str='Description'
Header_Target_Str='Target'
Header_HTTP_Str='HTTP'
Header_Body_Str='Body'
Header_BodyEnd_Str='BodyEnd'
Header_Who_Str='Who'
Header_ConnectionID_Str='ConnectionID'
Header_AppParameters_Str='AppParameters'
Header_AuthChallenge_Str='AuthChallenge'
Header_AuthResponse_Str='AuthResponse'
Header_ObjectClass_Str='ObjectClass'
# Code-to-name dict
Header_Name_Dict={
    Header_Count: Header_Count_Str,
    Header_Name: Header_Name_Str,
    Header_Type: Header_Type_Str,
    Header_Length: Header_Length_Str,
    Header_Time: Header_Time_Str,
    Header_Description: Header_Description_Str,
    Header_Target: Header_Target_Str,
    Header_HTTP: Header_HTTP_Str,
    Header_Body: Header_Body_Str,
    Header_BodyEnd: Header_BodyEnd_Str,
    Header_Who: Header_Who_Str,
    Header_ConnectionID: Header_ConnectionID_Str,
    Header_AppParameters: Header_AppParameters_Str,
    Header_AuthChallenge: Header_AuthChallenge_Str,
    Header_AuthResponse: Header_AuthResponse_Str,
    Header_ObjectClass: Header_ObjectClass_Str,
    }
Valid_Header_Codes=Header_Name_Dict.keys()

# Packet code constants
Packet_Connect=0x80
Packet_Disconnect=0x81
Packet_Put=0x02
Packet_PutEnd=0x82
Packet_Get=0x03
Packet_GetEnd=0x83
Packet_SetPath=0x85
Packet_Abort=0xFF
Packet_Resp_Continue=0x90
Packet_Resp_OK=0xA0
Packet_Resp_Created=0xA1
Packet_Resp_Accepted=0xA2
Packet_Resp_NonAuthoritativeInfo=0xA3
Packet_Resp_NoContent=0xA4
Packet_Resp_ResetContent=0xA5
Packet_Resp_PartialContent=0xA6
Packet_Resp_MultipleChoices=0xB0
Packet_Resp_MovedPermanently=0xB1
Packet_Resp_MovedTemporarily=0xB2
Packet_Resp_SeeOther=0xB3
Packet_Resp_NotModified=0xB4
Packet_Resp_UseProxy=0xB5
Packet_Resp_BadRequest=0xC0
Packet_Resp_Unauthorized=0xC1
Packet_Resp_PaymentRequired=0xC2
Packet_Resp_Forbidden=0xC3
Packet_Resp_NotFound=0xC4
Packet_Resp_MethodNotAllowed=0xC5
Packet_Resp_NotAcceptable=0xC6
Packet_Resp_ProxyAuthenticationRequired=0xC7
Packet_Resp_RequestTimeOut=0xC8
Packet_Resp_Conflict=0xC9
Packet_Resp_Gone=0xCA
Packet_Resp_LengthRequired=0xCB
Packet_Resp_PreconditionFailed=0xCC
Packet_Resp_RequestedEntityTooLarge=0xCD
Packet_Resp_RequestURLTooLarge=0xCE
Packet_Resp_UnsupportedMediaType=0xCF
Packet_Resp_InternalServerError=0xD0
Packet_Resp_NotImplemented=0xD1
Packet_Resp_BadGateway=0xD2
Packet_Resp_ServiceUnavailable=0xD3
Packet_Resp_GatewayTimeout=0xD4
Packet_Resp_HTTPVersionNotSupported=0xD5
Packet_Resp_DatabaseFull=0xE0
Packet_Resp_DatabaseLocked=0xE1
# Packet code name
Packet_Connect_Str='Connect'
Packet_Disconnect_Str='Disconnect'
Packet_Put_Str='Put'
Packet_PutEnd_Str='PutEnd'
Packet_Get_Str='Get'
Packet_GetEnd_Str='GetEnd'
Packet_SetPath_Str='SetPath'
Packet_Abort_Str='Abort'
Packet_Resp_Continue_Str='Continue'
Packet_Resp_OK_Str='OK'
Packet_Resp_Created_Str='Created'
Packet_Resp_Accepted_Str='Accepted'
Packet_Resp_NonAuthoritativeInfo_Str='NonAuthoritative Information'
Packet_Resp_NoContent_Str='No Content'
Packet_Resp_ResetContent_Str='Reset Content'
Packet_Resp_PartialContent_Str='Partial Content'
Packet_Resp_MultipleChoices_Str='Multiple Choices'
Packet_Resp_MovedPermanently_Str='Moved Permanently'
Packet_Resp_MovedTemporarily_Str='Moved Temporarily'
Packet_Resp_SeeOther_Str='See Other'
Packet_Resp_NotModified_Str='Not Modified'
Packet_Resp_UseProxy_Str='Use Proxy'
Packet_Resp_BadRequest_Str='Bad Request'
Packet_Resp_Unauthorized_Str='Unauthorized'
Packet_Resp_PaymentRequired_Str='Payment Required'
Packet_Resp_Forbidden_Str='Forbidden'
Packet_Resp_NotFound_Str='Not Found'
Packet_Resp_MethodNotAllowed_Str='Method Not Allowed'
Packet_Resp_NotAcceptable_Str='NotAcceptable'
Packet_Resp_ProxyAuthenticationRequired_Str='Proxy Authentication Required'
Packet_Resp_RequestTimeOut_Str='Request Time Out'
Packet_Resp_Conflict_Str='Conflict'
Packet_Resp_Gone_Str='Gone'
Packet_Resp_LengthRequired_Str='Length Required'
Packet_Resp_PreconditionFailed_Str='Precondition Failed'
Packet_Resp_RequestedEntityTooLarge_Str='Requested Entity Too Large'
Packet_Resp_RequestURLTooLarge_Str='Request URL Too Large'
Packet_Resp_UnsupportedMediaType_Str='Unsupported Media Type'
Packet_Resp_InternalServerError_Str='Internal Server Error'
Packet_Resp_NotImplemented_Str='Not Implemented'
Packet_Resp_BadGateway_Str='Bad Gateway'
Packet_Resp_ServiceUnavailable_Str='Service Unavailable'
Packet_Resp_GatewayTimeout_Str='Gateway Timeout'
Packet_Resp_HTTPVersionNotSupported_Str='HTTP Version Not Supported'
Packet_Resp_DatabaseFull_Str='Database Full'
Packet_Resp_DatabaseLocked_Str='Database Locked'
# Code-to-name dict
Packet_Name_Dict={
    Packet_Connect: Packet_Connect_Str,
    Packet_Disconnect: Packet_Disconnect_Str,
    Packet_Put: Packet_Put_Str,
    Packet_PutEnd: Packet_PutEnd_Str,
    Packet_Get: Packet_Get_Str,
    Packet_GetEnd: Packet_GetEnd_Str,
    Packet_SetPath: Packet_SetPath_Str,
    Packet_Abort: Packet_Abort_Str,
    Packet_Resp_Continue: Packet_Resp_Continue_Str,
    Packet_Resp_OK: Packet_Resp_OK_Str,
    Packet_Resp_Created: Packet_Resp_Created_Str,
    Packet_Resp_Accepted: Packet_Resp_Accepted_Str,
    Packet_Resp_NonAuthoritativeInfo: Packet_Resp_NonAuthoritativeInfo_Str,
    Packet_Resp_NoContent: Packet_Resp_NoContent_Str,
    Packet_Resp_ResetContent: Packet_Resp_ResetContent_Str,
    Packet_Resp_PartialContent: Packet_Resp_PartialContent_Str,
    Packet_Resp_MultipleChoices: Packet_Resp_MultipleChoices_Str,
    Packet_Resp_MovedPermanently: Packet_Resp_MovedPermanently_Str,
    Packet_Resp_MovedTemporarily: Packet_Resp_MovedTemporarily_Str,
    Packet_Resp_SeeOther: Packet_Resp_SeeOther_Str,
    Packet_Resp_NotModified: Packet_Resp_NotModified_Str,
    Packet_Resp_UseProxy: Packet_Resp_UseProxy_Str,
    Packet_Resp_BadRequest: Packet_Resp_BadRequest_Str,
    Packet_Resp_Unauthorized: Packet_Resp_Unauthorized_Str,
    Packet_Resp_PaymentRequired: Packet_Resp_PaymentRequired_Str,
    Packet_Resp_Forbidden: Packet_Resp_Forbidden_Str,
    Packet_Resp_NotFound: Packet_Resp_NotFound_Str,
    Packet_Resp_MethodNotAllowed: Packet_Resp_MethodNotAllowed_Str,
    Packet_Resp_NotAcceptable: Packet_Resp_NotAcceptable_Str,
    Packet_Resp_ProxyAuthenticationRequired: Packet_Resp_ProxyAuthenticationRequired_Str,
    Packet_Resp_RequestTimeOut: Packet_Resp_RequestTimeOut_Str,
    Packet_Resp_Conflict: Packet_Resp_Conflict_Str,
    Packet_Resp_Gone: Packet_Resp_Gone_Str,
    Packet_Resp_LengthRequired: Packet_Resp_LengthRequired_Str,
    Packet_Resp_PreconditionFailed: Packet_Resp_PreconditionFailed_Str,
    Packet_Resp_RequestedEntityTooLarge: Packet_Resp_RequestedEntityTooLarge_Str,
    Packet_Resp_RequestURLTooLarge: Packet_Resp_RequestURLTooLarge_Str,
    Packet_Resp_UnsupportedMediaType: Packet_Resp_UnsupportedMediaType_Str,
    Packet_Resp_InternalServerError: Packet_Resp_InternalServerError_Str,
    Packet_Resp_NotImplemented: Packet_Resp_NotImplemented_Str,
    Packet_Resp_BadGateway: Packet_Resp_BadGateway_Str,
    Packet_Resp_ServiceUnavailable: Packet_Resp_ServiceUnavailable_Str,
    Packet_Resp_GatewayTimeout: Packet_Resp_GatewayTimeout_Str,
    Packet_Resp_HTTPVersionNotSupported: Packet_Resp_HTTPVersionNotSupported_Str,
    Packet_Resp_DatabaseFull: Packet_Resp_DatabaseFull_Str,
    Packet_Resp_DatabaseLocked: Packet_Resp_DatabaseLocked_Str,
    }
Valid_Packet_Code=Packet_Name_Dict.keys()
FolderBrowsingServiceID='\xF9\xEC\x7B\xC4\x95\x3C\x11\xD2\x98\x4E\x52\x54\x00\xDC\x9E\x09'
FolderListingType='x-obex/folder-listing'

# OBEX Exceptions
class OBEXBadHeaderCode(Exception):
    def __init__(self, code):
        Exception.__init__(self, 'Bad Header Code: 0x%02X'%code)
        self.bad_code=code
class OBEXBadPacketCode(Exception):
    def __init__(self, code):
        Exception.__init__(self, 'Bad Packet Code: 0x%02X'%code)
        self.bad_code=code
class OBEXBadPacketLength(Exception):
    def __init__(self, expected_length, bad_length):
        Exception.__init__(self, 'Bad Packet Length: %d instead of %d'%(bad_length,
                                                                        expected_length))
        self.expected_length=expected_length
        self.bad_length=bad_length
class OBEXBadResponse(Exception):
    def __init__(self, code):
        Exception.__init__(self, 'Bad response code: %d (%s)'%(code, Packet_Name_Dict.get(code, 'Unknown code')))
        self.bad_code=code
class OBEXNoResponse(Exception):
    def __init__(self):
        Exception.__init__(self, 'No response received from device')


# OBEX FolderListingObject
class OBEXFolderListingObject(object):
    def __init__(self, data=None):
        if data:
            self.decode(data)
        else:
            self.data=None

    def _decode_date(self, dt_str):
        _date=bptime.BPTime(dt_str).mktime()
        return _date, time.strftime("%x %X", time.gmtime(_date))

    def decode(self, data):
        dom=xml.dom.minidom.parseString(data)
        _folder_listing=dom.getElementsByTagName('folder-listing')[0]
        self.data={}
        for _f in _folder_listing.getElementsByTagName('file'):
            _file_dict={ 'name': _f.getAttribute('name'),
                         'size': int(_f.getAttribute('size')),
                         'type': 'file',
                         'date':  self._decode_date(_f.getAttribute('modified')) }
            self.data[_file_dict['name']]=_file_dict
        for _f in _folder_listing.getElementsByTagName('folder'):
            _file_dict={ 'name': _f.getAttribute('name'),
                         'type': 'directory' }
            self.data[_file_dict['name']]=_file_dict
                         
# OBEXHeader--------------------------------------------------------------------
class OBEXHeader(object):
    """Handle an OBEX Header object"""
    def __init__(self, header_code, data=None):
        self.code=header_code
        if self.code is None and data:
            self.decode(data)
        else:
            self.data=data

    def len(self):
        """Return the length of this header"""
        return len(self.encode())
    def get_name(self):
        return Header_Name_Dict.get(self.code, 'Unknown Header Code')
    def get(self, string_key=False):
        if string_key:
            return { self.get_name(): self.data }
        return { self.code: self.data }

    # encoding routines---------------------------------------------------------
    def _encode_unicode(self):
        if self.data is not None:
            _s=(self.data+'\x00').encode('utf_16be')
            return struct.pack('B', self.code)+struct.pack('!H', len(_s)+3)+_s
        return struct.pack('B', self.code)+'\x00\x03'

    def _encode_bytes(self):
        if self.data:
            return struct.pack('B', self.code)+\
                   struct.pack('!H', len(self.data)+3)+\
                   self.data
        return struct.pack('B', self.code)+'\x00\x03'

    def _encode_1(self):
        return struct.pack('BB', self.code, self.data and self.data&0xff or 0)

    def _encode_4(self):
        return struct.pack('!BI', self.code, self.data or 0)

    encode_list=(_encode_unicode, _encode_bytes, _encode_1, _encode_4)
    def encode(self):
        """Return an encoded string of this header"""
        if self.code not in Valid_Header_Codes:
            raise OBEXBadHeaderCode(self.code)
        _encode_type=(self.code & 0xC0)>>6
        return self.encode_list[_encode_type](self)

    # decoding routines---------------------------------------------------------
    def _decode_unicode(self, data):
        _len=struct.unpack('!H', data[1:3])[0]
        self.data=data[3:_len].decode('utf_16be')[:-1]
    def _decode_bytes(self, data):
        _len=struct.unpack('!H', data[1:3])[0]
        self.data=data[3:_len]
    def _decode_1(self, data):
        self.data=struct.unpack('B', data[1])[0]
    def _decode_4(self, data):
        self.data=struct.unpack('!I', data[1:5])[0]
    decode_list=(_decode_unicode, _decode_bytes, _decode_1, _decode_4)
    def decode(self, data):
        global Valid_Header_Codes
        """decode the raw data received from a device"""
        self.code=struct.unpack('B', data[0])[0]
        if self.code not in Valid_Header_Codes:
            raise OBEXBadHeaderCode(self.code)
        _decode_type=(self.code&0xC0)>>6
        self.decode_list[_decode_type](self, data)

# Packet Class------------------------------------------------------------------
class OBEXPacket(object):
    def __init__(self, code, data=None):
        self.version_number=None
        self.flags=None
        self.max_packet_length=None
        self.constants=None
        self._headers=[]
        self.code=code
        if code is None and data:
            self.decode(data)
            
    def len(self):
        return len(self.encode())
    def get_name(self):
        return Packet_Name_Dict.get(self.code, 'Unknown Packet Code')
    def append(self, header_code, data=None):
        self._headers.append(OBEXHeader(header_code, data))
    def clear(self):
        self._headers=[]
    def get(self, string_key=False):
        _res={}
        for _h in self._headers:
            _res.update(_h.get(string_key))
        return _res

    # encoding stuff
    def encode(self):
        global Valid_Packet_Code
        if self.code not in Valid_Packet_Code:
            raise OBEXBadPacketCode(self.code)
        _packet_len=3   # code+len
        _packet_str=[struct.pack('B', self.code), '']
        if self.version_number is not None:
            _packet_len+=1
            _packet_str.append(struct.pack('B', self.version_number))
        if self.flags is not None:
            _packet_len+=1
            _packet_str.append(struct.pack('B', self.flags))
        if self.max_packet_length is not None:
            _packet_len+=2
            _packet_str.append(struct.pack('!H', self.max_packet_length))
        elif self.constants is not None:
            _packet_len+=1
            _packet_str.append(struct.pack('B', self.constants))
        for _h in self._headers:
            _s=_h.encode()
            _packet_len+=len(_s)
            _packet_str.append(_s)
        _packet_str[1]=struct.pack('!H', _packet_len)
        return ''.join(_packet_str)

    # decoding stuff
    def decode(self, data):
        global Valid_Packet_Code
        self.code=struct.unpack('B', data[0])[0]
        if self.code not in Valid_Packet_Code:
            raise OBEXBadPacketCode(self.code)
        _packet_len=struct.unpack('!H', data[1:3])[0]
        if _packet_len!=len(data):
            raise OBEXBadPacketLength(_packet_len, len(data))
        if self.code==Packet_Connect:
            self.version_number, self.flags, self.max_packet_length=struct.unpack('!BBH',
                                                                                  data[3:7])
            _idx=7
        elif self.code==Packet_SetPath:
            self.flags, self.constants=struct.unpack('BB', data[3:5])
            _idx=5
        else:
            _idx=3
        while _idx<_packet_len:
            _h=OBEXHeader(None, data[_idx:])
            _idx+=_h.len()
            self._headers.append(_h)

class OBEXPacketConnectResp(OBEXPacket):
    # Special response packet to a Connect request
    # This one has a slightly different format than the standard response
    # Should ONLY be used for decoding incoming response to a Connect request
    def decode(self, data):
        global Valid_Packet_Code
        self.code=struct.unpack('B', data[0])[0]
        if self.code not in Valid_Packet_Code:
            raise OBEXBadPacketCode(self.code)
        _packet_len=struct.unpack('!H', data[1:3])[0]
        if _packet_len!=len(data):
            raise OBEXBadPacketLength(_packet_len, len(data))
        self.version_number, self.flags, self.max_packet_length=struct.unpack('!BBH',
                                                                              data[3:7])
        _idx=7
        while _idx<_packet_len:
            _h=OBEXHeader(None, data[_idx:])
            _idx+=_h.len()
            self._headers.append(_h)

# Class FolderBrowsingService---------------------------------------------------
class FolderBrowsingService(object):
    def __init__(self, logtarget, commport):
        self.log=self._log
        self.progress=self._progress
        if logtarget:
            if hasattr(logtarget, 'log'):
                self.log=logtarget.log
            if hasattr(logtarget, 'progress'):
                self.progress=logtarget.progress
        self.comm=commport
        self.connection_id=0
        self.max_packet_length=0x2000
        self.server_max_packet_length=255
        self.version_number=0x10
        self.data_block_length=0x07E0   # default length of a data block

    def _log(self, str):
        print str
    def _progress(self, pos, max, desc):
        print desc,pos,'out of',max

    def _send_packet(self, packet):
        global module_debug
        _s=packet.encode()
        if module_debug:
            self.log('Sending Packet: '+' '.join(['0x%02X'%ord(x) for x in _s]))
        self.comm.write(_s)

    def _get_response(self):
        global module_debug
        _code=self.comm.read(1)
        if not _code:
            raise OBEXNoResponse()
        _len_str=self.comm.read(2)
        _len=struct.unpack('!H', _len_str)[0]
        if _len>3:
            _data=self.comm.read(_len-3)
        else:
            _data=''
        _s=_code+_len_str+_data
        if module_debug:
            self.log('Receiving Packet: '+' '.join(['0x%02X'%ord(x) for x in _s]))
        return _s

    def _send_and_check_return(self, packet, expected_code=[Packet_Resp_OK]):
        self._send_packet(packet)
        _resp=OBEXPacket(None, self._get_response())
        if _resp.code not in expected_code:
            raise OBEXBadResponse(_resp.code)
        return _resp

    def _get_body(self, packet, totallen=None, filename=None):
        _resp=self._send_and_check_return(packet,
                                          [Packet_Resp_OK, Packet_Resp_Continue])
        _s=''
        _pkt=OBEXPacket(Packet_GetEnd)
        while _resp.code==Packet_Resp_Continue:
            _dict=_resp.get()
            if _dict.has_key(Header_Body):
                if _dict[Header_Body]:
                    _s+=_dict[Header_Body]
            elif _dict.has_key(Header_BodyEnd):
                if _dict[Header_BodyEnd]:
                    _s+=_dict[Header_BodyEnd]
            _resp=self._send_and_check_return(_pkt,
                                              [Packet_Resp_OK,
                                               Packet_Resp_Continue])
            if totallen and filename:
                self.progress(len(_s), totallen, 'Reading file: '+filename)
        if _resp.code==Packet_Resp_OK:
            _dict=_resp.get()
            if _dict.get(Header_BodyEnd, None):
                _s+=_dict[Header_BodyEnd]
        return _s

    def _send_body(self, packet, data, filename=None):
        _resp=self._send_and_check_return(packet, [Packet_Resp_Continue])
        _len_data=len(data)
        _pkt=OBEXPacket(Packet_Put)
        for _block in range(0, _len_data, self.data_block_length):
            _start_idx=_block
            _end_idx=min(_start_idx+self.data_block_length, _len_data)
            _pkt.clear()
            _pkt.append(Header_Body, data[_start_idx:_end_idx])
            self._send_and_check_return(_pkt, [Packet_Resp_Continue])
            if filename:
                self.progress(_end_idx, _len_data, 'Writing file: '+filename)
        _pkt=OBEXPacket(Packet_PutEnd)
        _pkt.append(Header_BodyEnd)
        self._send_and_check_return(_pkt, [Packet_Resp_OK])
                                          
    def connect(self):
        # connect to a phone
        try:
            _pkt=OBEXPacket(Packet_Connect)
            _pkt.version_number=self.version_number
            _pkt.flags=0
            _pkt.max_packet_length=self.max_packet_length
            _pkt.append(Header_Target, FolderBrowsingServiceID)
            self._send_packet(_pkt)
            _s=self._get_response()
            _resp=OBEXPacketConnectResp(None, _s)
            if _resp.code!=Packet_Resp_OK:
                return False
            self.server_max_packet_length=_resp.max_packet_length
            _pkt_dict=_resp.get()
            if _pkt_dict.has_key(Header_ConnectionID):
                self.connection_id=_pkt_dict[Header_ConnectionID]
            return True
        except Exception, e:
            if __debug__:
                raise
            self.log('Exception raise: '+str(e))
            return False

    def disconnect(self):
        try:
            _pkt=OBEXPacket(Packet_Disconnect)
            _pkt.append(Header_ConnectionID, self.connection_id)
            self._send_packet(_pkt)
            self._get_response()
        except Exception, e:
            if __debug__:
                raise
            self.log('Exception raise: '+str(e))

    def _setpath(self, dirname=''):
        # go to the root first
        _pkt=OBEXPacket(Packet_SetPath)
        _pkt.flags=2
        _pkt.constants=0
        _pkt.append(Header_ConnectionID, self.connection_id)
        _pkt.append(Header_Name, dirname)
        self._send_and_check_return(_pkt)

    def _set_path_root(self):
        # go back to root
        # The V710 OBEX firmware SetPath to root has a bug
        # this is a work-around for it but also works with other device too.
        _pkt=OBEXPacket(Packet_SetPath)
        _pkt.flags=3    # go up one, don't create
        _pkt.constants=0
        _pkt.append(Header_ConnectionID, self.connection_id)
        _pkt.append(Header_Name)
        while True:
            # keep going one dir up until no further
            try:
                self._send_and_check_return(_pkt)
            except OBEXBadResponse:
                break

    def _list_current_folder(self):
        _pkt=OBEXPacket(Packet_GetEnd)
        _pkt.append(Header_ConnectionID, self.connection_id)
        _pkt.append(Header_Name, '')
        _pkt.append(Header_Type, FolderListingType+'\x00')
        return OBEXFolderListingObject(self._get_body(_pkt)).data

    def setpath(self, dir=''):
        self._set_path_root()
        for _path in dir.split('/'):
            if _path:
                self._setpath(_path)

    def _update_filesystem_dict(self, fs_dict, dir):
        _res={}
        for _,_entry in fs_dict.items():
            if dir:
                _name=dir+'/'+_entry['name']
            else:
                _name=_entry['name']
            _res[_name]=_entry
            _res[_name]['name']=_name
        return _res

    def getfilesystem(self, dir='', recurse=0):
        self.log('Listing OBEX dir '+dir)
        try:
            self.setpath(dir)
            _res=self._update_filesystem_dict(self._list_current_folder(),
                                              dir)
            if recurse:
                _subdir_list=[_key for _key,_entry in _res.items() \
                              if _entry.get('type', None)=='directory']
                for _subdir in _subdir_list:
                    _res.update(self.getfilesystem(_subdir, recurse-1))
            return _res
        except Exception, e:
            if __debug__:
                raise
            self.log('Exception raised: '+str(e))
            return {}

    def listfiles(self, dir=''):
        _res={}
        for _key,_entry in self.getfilesystem(dir).items():
            if _entry['type']=='file':
                _res[_key]=_entry
        return _res

    def listsubdirs(self, dir='', recurse=0):
        _res={}
        for _key,_entry in self.getfilesystem(dir, recurse).items():
            if _entry['type']=='directory':
                _res[_key]=_entry
        return _res

    def writefile(self, name, data):
        self.log('Writing OBEX file: '+name)
        _name_list=name.split('/')
        _dir_name='/'.join(_name_list[:-1])
        _file_name=_name_list[-1]
        self.setpath('/'.join(name.split('/')[:-1]))
        _pkt=OBEXPacket(Packet_Put)
        _pkt.append(Header_ConnectionID, self.connection_id)
        _pkt.append(Header_Length, len(data))
        _pkt.append(Header_Name, _file_name)
        self._send_body(_pkt, data, _file_name)

    def rmfile(self, name):
        self.log('Deleting OBEX file: '+name)
        _name_list=name.split('/')
        _dir_name='/'.join(_name_list[:-1])
        _file_name=_name_list[-1]
        self.setpath('/'.join(name.split('/')[:-1]))
        _pkt=OBEXPacket(Packet_PutEnd)
        _pkt.append(Header_ConnectionID, self.connection_id)
        _pkt.append(Header_Name, _file_name)
        self._send_and_check_return(_pkt)

    def getfilecontents(self, name, size=None):
        self.log('Reading OBEX file: '+name)
        _name_list=name.split('/')
        _dir_name='/'.join(_name_list[:-1])
        _file_name=_name_list[-1]
        if size:
            self.setpath('/'.join(name.split('/')[:-1]))
            _totallen=size
        else:
            _file_list=self.listfiles(_dir_name)
            _totallen=_file_list.get(name, {}).get('size', None)
        _pkt=OBEXPacket(Packet_GetEnd)
        _pkt.append(Header_ConnectionID, self.connection_id)
        _pkt.append(Header_Name, _file_name)
        return self._get_body(_pkt, _totallen, _file_name)
