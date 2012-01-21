### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: wma_file.py 3608 2006-10-06 02:51:56Z djpham $

""" Deal with WMA file format"""

# System modules
import struct

# BitPim modules

# constants
ASF_Header_Object_GUID="\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C"
ASF_File_Properties_Object_GUID="\xA1\xDC\xAB\x8C\x47\xA9\xCF\x11\x8E\xE4\x00\xC0\x0C\x20\x53\x65"
ASF_Stream_Properties_Object_GUID="\x91\x07\xDC\xB7\xB7\xA9\xCF\x11\x8E\xE6\x00\xC0\x0C\x20\x53\x65"
ASF_Header_Extension_Object_GUID="\xB5\x03\xBF\x5F\x2E\xA9\xCF\x11\x8E\xE3\x00\xC0\x0C\x20\x53\x65"
ASF_Content_Description_Object_GUID="\x33\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C"
ASF_Extended_Content_Description_Object_GUID="\x40\xA4\xD0\xD2\x07\xE3\xD2\x11\x97\xF0\x00\xA0\xC9\x5E\xA8\x50"

#-------------------------------------------------------------------------------
class ASF_Object(object):
    def __init__(self, data, keep_data=False):
        self.guid=None
        self.size=None
        self.data=None
        if len(data)<24:
            # not a valid ASF Object
            return
        self.guid=data[:16]
        self.size=struct.unpack('<Q', data[16:24])[0]
        self.decode(data[24:self.size])
        self.valid=bool(self.guid and self.size)
        if keep_data:
            self.data=data[:self.size]

    def unpack(self, format, data, start=0):
        return struct.unpack(format, data[start:start+struct.calcsize(format)])
    def decode(self, data):
        pass

#-------------------------------------------------------------------------------
class ASF_File_Properties_Object(ASF_Object):
    def __init__(self, data, keep_data=False):
        super(ASF_File_Properties_Object, self).__init__(data, keep_data)

    def decode(self, data):
        self.file_id=data[:16]
        (self.file_size, self.creation_date, self.data_packets_count,
         _play_duration, self.send_duration, self.preroll, _flags,
         self.min_packet_size, self.max_packet_size,
         self.max_bitrate)=self.unpack('<QQQQQQLLLL', data, 16)
        self.play_duration=_play_duration*100e-9
        self.broadcast_flag=_flags&1
        self.seekable_flag=_flags&2

#-------------------------------------------------------------------------------
class ASF_Stream_Properties_Object(ASF_Object):
    def __init__(self, data, keep_data=False):
        super(ASF_Stream_Properties_Object, self).__init__(data, keep_data)
    def decode(self, data):
        self.stream_type=data[:16]
        self.error_correction_type=data[16:32]
        (self.time_offset, self.type_specific_data_len,
         self.error_correction_data_len, _flags)=self.unpack('<QLLH', data, 32)
        self.stream_number=_flags&0x7F
        self.encrypted_content_flag=_flags&0x8000

#-------------------------------------------------------------------------------
class ASF_Header_Extension_Object(ASF_Object):
    def __init__(self, data, keep_data=False):
        super(ASF_Header_Extension_Object, self).__init__(data, keep_data)
    def decode(self, data):
        self.header_extension_data_size=self.unpack('<L', data, 18)[0]

#-------------------------------------------------------------------------------
class ASF_Content_Description_Object(ASF_Object):
    def __init__(self, data, keep_data=False):
        super(ASF_Content_Description_Object, self).__init__(data, keep_data)
    def _substr(self, data, start, len):
        if len:
            _s=str(data[start:start+len]).decode('utf_16_le', 'ignore')
            if _s[-1]=='\x00':
                _s=_s[:-1]
            return (start+len, _s)
        return (start, '')
    def decode(self, data):
        (_title_len, _author_len, _cpright_len, _desc_len,
         _rating_len)=self.unpack('<HHHHH', data)
        _start=10
        (_start, self.title)=self._substr(data, _start, _title_len)
        (_start, self.author)=self._substr(data, _start, _author_len)
        (_start, self.copyright)=self._substr(data, _start, _cpright_len)
        (_start, self.description)=self._substr(data, _start, _desc_len)
        (_start, self.rating)=self._substr(data, _start, _rating_len)

#-------------------------------------------------------------------------------
class ASF_Extended_Content_Description_Object(ASF_Object):
    def __init__(self, data, keep_data=False):
        super(ASF_Extended_Content_Description_Object, self).__init__(data,
                                                                      keep_data)
    def _decode_descriptor(self, data, start, res):
        _start=start
        _name_len=self.unpack('<H', data, _start)[0]
        _start+=2
        _name=data[_start:_start+_name_len].decode('utf_16_le', 'ignore')
        if _name[-1]=='\x00':
            _name=_name[:-1]
        _start+=_name_len
        (_value_type,
         _value_len)=self.unpack('<HH', data, _start)
        _start+=4
        if _value_type==0:
            # unicode type
            _value=data[_start:_start+_value_len].decode('utf_16_le', 'ignore')
            if _value[-1]=='\x00':
                _value=_value[:-1]
        elif _value_type==1:
            # byte array
            _value=data[_start:_start+_value_len]
        elif _value_type==2 or _value_type==3:
            _value=self.unpack('<L', data, _start)[0]
        elif _value_type==4:
            _value=self.unpack('<Q', data, _start)[0]
        elif _value_type==5:
            _value=self.unpack('<H', data, _start)[0]
        else:
            _value=None
        res[_name]=_value
        return _start+_value_len

    def decode(self, data):
        self.descriptors_count=self.unpack('<H', data)[0]
        _start=2
        self.descriptors={}
        for _cnt in range(self.descriptors_count):
            _start=self._decode_descriptor(data, _start,
                                           self.descriptors)
        
#-------------------------------------------------------------------------------
class ASF_Header_Object(ASF_Object):
    def __init__(self, data, keep_data=False):
        # Madatory objects
        self.file_properties=None
        self.stream_properties=None
        self.header_extension=None
        # List of options objects, not all are recognized and decoded
        self.content_description=None
        self.extended_content_description=None
        super(ASF_Header_Object, self).__init__(data, keep_data)

    _obj_attr_tab={
        ASF_File_Properties_Object: 'file_properties',
        ASF_Stream_Properties_Object: 'stream_properties',
        ASF_Header_Extension_Object: 'header_extension',
        ASF_Content_Description_Object: 'content_description',
        ASF_Extended_Content_Description_Object: 'extended_content_description',
        }
        
    def decode(self, data):
        self.obj_cnt=self.unpack('<L', data)[0]
        _start=6
        for _cnt in range(self.obj_cnt):
            _obj=Create_ASF_Object(data[_start:], False, ASF_Object)
            if _obj:
                _start+=_obj.size
                _attr_name=self._obj_attr_tab.get(type(_obj), None)
                if _attr_name:
                    setattr(self, _attr_name, _obj)
            else:
                break

#-------------------------------------------------------------------------------
# lookup table for object instantiation
Object_Table={
    ASF_Header_Object_GUID: ASF_Header_Object,
    ASF_File_Properties_Object_GUID: ASF_File_Properties_Object,
    ASF_Stream_Properties_Object_GUID: ASF_Stream_Properties_Object,
    ASF_Header_Extension_Object_GUID: ASF_Header_Extension_Object,
    ASF_Content_Description_Object_GUID: ASF_Content_Description_Object,
    ASF_Extended_Content_Description_Object_GUID: ASF_Extended_Content_Description_Object,
    }

def Create_ASF_Object(data, keep_data=False, default_class=None):
    global Object_Table
    # look at the data and return a corresponding ASF Object
    if len(data)<24:
        # not long enough for an ASF Header block
        return None
    _guid=data[:16]
    if Object_Table.has_key(_guid):
        return Object_Table[_guid](data, keep_data)
    if default_class:
        return default_class(data, keep_data)

#-------------------------------------------------------------------------------
class WMA_File(object):
    def __init__(self, file_wrapper):
        global Object_Table, ASF_Header_Object_GUID
        self.valid=False
        self.header=None
        self.play_duration=None
        self.title=None
        self.author=None
        self.album=None
        self.genre=None

        if file_wrapper.size<24 or \
           file_wrapper.GetBytes(0, 16)!=ASF_Header_Object_GUID:
            return
        _size=struct.unpack('<Q', file_wrapper.GetBytes(16, 8))[0]
        self.header=ASF_Header_Object(file_wrapper.GetBytes(0, _size), False)
        self.valid=self.header.valid
        if not self.valid:
            return
        if self.header.file_properties and \
           self.header.file_properties.valid:
            self.play_duration=self.header.file_properties.play_duration
        if self.header.content_description and \
           self.header.content_description.valid:
            self.title=self.header.content_description.title
            self.author=self.header.content_description.author
        if self.header.extended_content_description and \
           self.header.extended_content_description.valid:
            _descriptors=self.header.extended_content_description.descriptors
            self.album=_descriptors.get('WM/AlbumTitle', '')
            self.genre=_descriptors.get('WM/Genre', '')
