### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: sqlite2_file.py 3460 2006-07-08 23:55:09Z djpham $

"""Handle reading data off an SQLit2 2.x data file"""

# System modules
import struct

# SQLite2 constants
# byte order format
BO='<'  # default to LE
signature='** This file contains an SQLite 2.1 database **\x00'
signature_len=len(signature)
LE_string='\x28\x75\xe3\xda'
BE_string='\xda\xe3\x75\x28'
Page_Length=1024
Max_Cell_Data_Len=238

# SQLite 2.x file handling stuff------------------------------------------------
class InvalidFile(Exception):
    def __init__(self, bad_sig):
        global signature
        Exception.__init__(self, 'Invalid signature: expecting %s, got %s'%(signature, bad_sig))
        self.bad_sig=bad_sig

class InvalidByteOrder(Exception):
    def __init__(self, bad_data):
        Exception.__init__(self, 'Invalid Byte Order String: %s'%bad_data)
        self.bad_data=bad_data

class BadTable(Exception):
    def __init__(self, name):
        Exception.__init__(self, 'Failed to find table: %s'%name)
        self.name=name

class Cell(object):
    def __init__(self, data):
        global BO, Max_Cell_Data_Len
        self.prev_key=struct.unpack('%cI'%BO, data[:4])[0]
        _key_size=struct.unpack('%cH'%BO, data[4:6])[0]
        self.next_cell=struct.unpack('%cH'%BO, data[6:8])[0]
        _keysize_hi=struct.unpack('B', data[8])[0]
        _datasize_hi=struct.unpack('B', data[9])[0]
        _data_size=struct.unpack('%cH'%BO, data[10:12])[0]
        _key_size+=_keysize_hi<<16
        _data_size+=_datasize_hi<<16
        self.key=struct.unpack('%cI'%BO, data[12:16])
        if _data_size>Max_Cell_Data_Len:
            self.data=data[16:250]
            self.overflow_page=struct.unpack('%cI'%BO, data[250:254])[0]
        else:
            self.data=data[16:16+_data_size]
            self.overflow_page=0
        self.data_size=_data_size

    def get_data(self, page, db_file):
        global Max_Cell_Data_Len
        _res=[]
        if self.prev_key:
            _res=db_file.get_data(self.prev_key)
        _my_data=self.data
        if self.overflow_page:
            _my_data+=db_file.get_data(self.overflow_page,
                                       self.data_size-Max_Cell_Data_Len)
        _res.append(_my_data)
        if self.next_cell:
            _res+=page.get_cell_data(self.next_cell, db_file)
        return _res

class Page(object):
    def __init__(self, data):
        global BO, Page_Length
        self.prev_key=struct.unpack('%cI'%BO, data[:4])[0]
        self.cell0=struct.unpack('%cH'%BO, data[4:6])[0]
        self.freeblock=struct.unpack('%cH'%BO, data[6:8])[0]
        self.data=data[:Page_Length]

    def get_cell_data(self, offset, db_file):
        return Cell(self.data[offset:]).get_data(self, db_file)
                      
    def get_data(self, db_file, _=None):
        # return the payload of this page
        _res=[]
        if self.prev_key:
            _res=db_file.get_data(self.prev_key)
        _res+=self.get_cell_data(self.cell0, db_file)
        return _res

class Page1(object):
    def __init__(self, data):
        global signature, BO, signature_len, LE_string, BE_string
        _sig=data[:signature_len]
        if _sig!=signature:
            raise InvalidFile(_sig)
        _idx=signature_len
        _bo_string=data[_idx:_idx+4]
        if _bo_string==LE_string:
            BO='<'
        elif _bo_string==BE_string:
            BO='>'
        else:
            raise InvalidByteOrder(_bo_string)
        _idx+=4
        self.first_free_page=struct.unpack('%cI'%BO, data[_idx:_idx+4])[0]
        _idx+=4
        self.freelist_pages=struct.unpack('%cI'%BO, data[_idx:_idx+4])[0]

class OverflowPage(object):
    Max_Len=1020
    def __init__(self, data):
        global BO, Page_Length
        self.next=struct.unpack('%cI'%BO, data[:4])[0]
        self.data=data[4:Page_Length]

    def get_data(self, db_file, data_size=None):
        if data_size:
            if data_size>self.Max_Len:
                _res=self.data
                if self.next:
                    _res+=db_file.get_data(self.next, data_size-self.Max_Len)
            else:
                _res=self.data[:data_size]
        else:
            _res=self.data
        return _res

class DBFile(object):
    def __init__(self, data):
        self.data=data
        self.page1=Page1(data)
        self.tables=self._get_tables()

    def get_data(self, page_num, data_size=None):
        global Page_Length
        if not page_num:
            return []
        # We cheat here a bit since we know the page length is 1k
##        _pg_ofs=(page_num-1)*Page_Length
        _pg_ofs=(page_num-1)<<10
        if data_size:
            return OverflowPage(self.data[_pg_ofs:_pg_ofs+Page_Length]).get_data(self,
                                                                                 data_size)
        return Page(self.data[_pg_ofs:_pg_ofs+Page_Length]).get_data(self)

    def extract_data(self, data, numofcols):
        # extract one string of data in to a list of numofcols
        _data_len=len(data)
        if _data_len<256:
            _ofs_size=1
        elif _data_len<65536:
            _ofs_size=2
        else:
            _ofs_size=3
        _idx=(numofcols+1)*_ofs_size
        return data[_idx:].split('\x00')[:numofcols]

    def _get_tables(self):
        # build a list of tables in this DB
        _res={}
        # the master table is stored in page 2, and has 5 fields
        for _entry in self.get_data(2):
            _row=self.extract_data(_entry, 5)
            if _row[0]=='table':
                _res[_row[1]]={ 'name': _row[1],
                                'page': int(_row[3]),
                                'numofcols': _row[4].count(',')+1 }
        return _res

    def get_table_data(self, table_name):
        # return a list of rows of this table, each row is a list of values
        if not self.tables.has_key(table_name):
            raise BadTable(table_name)
        _page=self.tables[table_name]['page']
        _numofcols=self.tables[table_name]['numofcols']
        _res=[]
        for _entry in self.get_data(_page):
            _res.append(self.extract_data(_entry, _numofcols))
        return _res
