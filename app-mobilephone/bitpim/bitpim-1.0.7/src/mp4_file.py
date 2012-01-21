### BITPIM
###
### Copyright (C) 2009 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
###

""" Deal with MPEG4 file format"""

# System modules
import struct

# BitPim modules

# constants
MP4_File_Type_Header = "ftyp"
MP4_STSZ_Atom_Tag    = "stsz"
MP4_MDHD_Atom_Tag    = "mdhd"
MP4_META_Atom_Tag    = "meta"

#-------------------------------------------------------------------------------
class MP4_STSZ_Atom(object):
    def __init__ (self, data):
        if data[4:8] != MP4_STSZ_Atom_Tag:
            raise
        if struct.unpack ('>L', data[0:4])[0] < 0x14:
            raise

        self.numSamples     = struct.unpack ('>L', data[16:20])[0]
        self.average        = 0.0
        self.audibleSamples = None

        _silentSamples = 0

        # 8 for atom header + 12 for sample count and other stuff
        _dataOffset = 20
        for i in range (self.numSamples):
            _sampleSize = struct.unpack ('>L', data[_dataOffset:_dataOffset+4])[0]

            if _sampleSize == 7:
                _silentSamples += 1
            else:
                self.average += float(_sampleSize)

            _dataOffset += 4

        self.audibleSamples = self.numSamples - _silentSamples
        self.average = self.average * 8.0/float(self.audibleSamples)

    def getBitrate(self, timescale):
        _bitrate = int((self.average * float(timescale)/1000.0)/1000.0)
        _lossless = None

        if _bitrate - 32 > 320:
            # handle lossless files
            self.average  *= 1000.0/4096.0;
            _bitrate = int((self.average * float(timescale)/1000.0)/1000.0)

        return _bitrate

class MP4_Media_Header(object):
    def __init__ (self, data):
        if data[4:8] != MP4_MDHD_Atom_Tag:
            raise

        self.timeScale = struct.unpack ('>L', data[20:24])[0]
        # song duration is in Hz/second
        self.duration  = struct.unpack ('>L', data[24:28])[0]

    def getTimescale (self):
        return self.timeScale

    def getDuration (self):
        return self.duration/self.timeScale

class MP4_Meta_Data(object):
    def __init__ (self, data):
        if data[4:8] != MP4_META_Atom_Tag:
            raise

        self.title = None
        self.album = None
        self.artist = None

        _offset = 12
        while 1:
            _size = struct.unpack ('>L', data[offset:offset + 4])[0]
            _tag  = data[offset+5:offset+8]
            _tag1 = data[offset+4:offset+8]

            _dataSize = struct.unpack ('>L', data[offset + 8:offset + 12])[0]
            _tagData  = data[offset + 24:offset + 8 + _dataSize]

            if _tag1 == "free":
                break
            if _tag == "nam":
                self.title = _tagData
            if _tag == "ART":
                self.artist = _tagData
            if _tag == "alb":
                self.album = _tagData

    def getTitle (self):
        return self.title

    def getArtist (self):
        return self.artist

    def getAlbum (self):
        return self.album
#-------------------------------------------------------------------------------
class MP4_File(object):
    def __init__(self, file_wrapper):
        global Object_Table, ASF_Header_Object_GUID
        self.valid=False

        self.duration = None
        self.bitrate = None
        self.samplerate = None
        self.title  = None
        self.artist = None
        self.album  = None

        self.STSZAtom = None
        self.mediaHeader = None
        self.metaData = None

        if file_wrapper.size<24 or file_wrapper.GetBytes(4,4)!=MP4_File_Type_Header:
            return

        type_id = file_wrapper.GetBytes(8,4)

        if type_id != 'M4A ' and type_id != "mp42" and type_id != "isom":
            return

        # initial file offset (skipping the FTYP atom)
        _offset = struct.unpack ('>L', file_wrapper.GetBytes(0, 4))[0];
        while 1:
            try:
                _size = struct.unpack ('>L', file_wrapper.GetBytes(_offset, 4))[0];
                _type = file_wrapper.GetBytes(_offset + 4, 4);
            except:
                break

            if _size == 0:
                break

            try:
                if _type == MP4_STSZ_Atom_Tag and self.STSZAtom == None:
                    self.STSZAtom = MP4_STSZ_Atom (file_wrapper.GetBytes (_offset, _size))
                elif _type == MP4_MDHD_Atom_Tag and self.mediaHeader == None:
                    self.mediaHeader = MP4_Media_Header (file_wrapper.GetBytes (_offset, _size))
                elif _type == MP4_META_Atom_Tag:
                    self.metaData  = MP4_Meta_Data (file_wrapper.GetBytes (_offset, _size))
            except:
                pass

            if not self.isContainerAtom(_type):
                _offset = _offset + _size
            else:
                _offset = _offset + 8

        if self.mediaHeader:
            self.duration = self.mediaHeader.getDuration ()
            self.samplerate = self.mediaHeader.getTimescale ()
            if self.STSZAtom:
                self.STSZAtom.getBitrate (self.mediaHeader.getTimescale ())
                self.valid = True

        if self.metaData:
            self.artist = self.metaData.getArtist ()
            self.album  = self.metaData.getAlbum ()
            self.title  = self.metaData.getTitle ()

    def isContainerAtom (self, _type):
        return (_type == "trak" or _type == "mdia" or _type == "moov" or
                _type == "stbl" or _type == "minf" or _type == "dinf" or
                _type == "udta")
