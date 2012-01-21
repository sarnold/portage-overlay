### BITPIM
###
### Copyright (C) 2005 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: fileinfo.py 4731 2009-03-06 03:28:04Z hjelmn $

"Returns information about files"

import os
import struct

import common

import midifile
import wma_file
import mp4_file

class FailedFile:
    data=""
    def GetBytes(*args):   return None
    def GetLSBUint32(*args): return None
    def GetLSBUint16(*args): return None
    def GetByte(*args): return None
    def GetMSBUint32(*args): return None
    def GetMSBUint16(*args): return None

class SafeFileWrapper:
    """Wraps a file object letting you get various parts without exceptions"""

    READAHEAD=1024

    def __init__(self, filename):
        try:
            self.file=open(filename, "rb")
            self.size=os.stat(filename).st_size
            self.data=self.file.read(self.READAHEAD)
        except (OSError,IOError):
            # change our class
            self.size=-1
            self.__class__=FailedFile

    def GetBytes(self, offset, length):
        if offset+length<len(self.data):
            return self.data[offset:offset+length]
        if offset+length>self.size:
            return None
        self.file.seek(offset)
        res=self.file.read(length)
        if len(res)<length: return None
        return res

    def GetLSBUint32(self, offset):
        v=self.GetBytes(offset, 4)
        if v is None: return v
        return struct.unpack('<L', v)[0]

    def GetLSBUint16(self, offset):
        v=self.GetBytes(offset, 2)
        if v is None: return v
        return struct.unpack('<H', v)[0]

    def GetMSBUint32(self, offset):
        v=self.GetBytes(offset, 4)
        if v is None: return v
        return struct.unpack('>L', v)[0]

    def GetMSBUint16(self, offset):
        v=self.GetBytes(offset, 2)
        if v is None: return v
        return struct.unpack('>H', v)[0]

    def GetByte(self, offset):
        v=self.GetBytes(offset,1)
        if v is None: return v
        return ord(v)

class SafeStringWrapper(SafeFileWrapper):
    """
    Wraps a string object letting you get various parts w/o exceptions.
    Mainly used by the com_* modules as part of writing media to the phone.
    """
    def __init__(self, string):
        if isinstance(string, str):
            self.file=None
            self.data=string
            self.size=len(string)
        else:
            self.size=-1
            self.__class__=FailedFile

    def GetBytes(self, offset, length):
        if (offset+length)<=self.size:
            return self.data[offset:offset+length]
        
class ImgFileInfo:
    "Wraps information about an image file"

    # These will always be present
    attrnames=("width", "height", "format", "bpp", "size", "MAXSIZE")

    def __init__(self, f, **kwds):
        for a in self.attrnames:
            setattr(self, a, None)
        self.mimetypes=[]
        self.size=f.size
        self.__dict__.update(kwds)

    def shortdescription(self):
        v=getattr(self, "_shortdescription", None)
        if v is not None:
            return v(self)        
        res=[]
        if self.width is not None and self.height is not None:
            res.append( "%d x %d" % (self.width, self.height) )
        if self.format is not None:
            res.append( self.format)
        if self.bpp is not None:
            res.append( "%d bpp" % (self.bpp,))

        if len(res):
            return " ".join(res)
        return "Unknown format"

    def longdescription(self):
        v=getattr(self, "_longdescription", None)
        if v is not None:
            return v(self)
        return self.shortdescription()

def idimg_BMP(f):
    "Identify a Windows bitmap"
    # 40 is header size for windows bmp, different numbers are used by OS/2
    if f.GetBytes(0,2)=="BM" and f.GetLSBUint16(14)==40:
        d={'format': "BMP"}
        d['width']=f.GetLSBUint32(18)
        d['height']=f.GetLSBUint32(22)
        d['bpp']=f.GetLSBUint16(28)
        d['compression']=f.GetLSBUint32(30)
        d['ncolours']=f.GetLSBUint32(46)
        d['nimportantcolours']=f.GetLSBUint32(50)
        d['_longdescription']=fmt_BMP
        d['mimetypes']=['image/bmp', 'image/x-bmp']
        for i in d.itervalues():
            if i is None:  return None
        ifi=ImgFileInfo(f,**d)
        return ifi
    return None

def fmt_BMP(ifi):
    "Long description for BMP"
    res=[ifi.shortdescription()]
    if ifi.compression==0:
        res.append("No compression")
    elif ifi.compression==1:
        res.append("8 bit run length encoding")
    elif ifi.compression==2:
        res.append("4 bit run length encoding")
    elif ifi.compression==3:
        res.append("RGB bitmap with mask")
    else:
        res.append("Unknown compression "+`ifi.compression`)
    if ifi.ncolours:
        res.append("%d colours" % (ifi.ncolours,))
        if ifi.nimportantcolours:
            res[-1]=res[-1]+(" (%d important)" % (ifi.nimportantcolours,))
    return "\n".join(res)
    
def idimg_PNG(f):
    "Identify a PNG"
    if f.GetBytes(0,8)=="\x89PNG\r\n\x1a\n" and f.GetBytes(12,4)=="IHDR":
        d={'format': "PNG"}
        d['width']=f.GetMSBUint32(16)
        d['height']=f.GetMSBUint32(20)
        d['bitdepth']=f.GetByte(24)
        d['colourtype']=f.GetByte(25)
        d['compression']=f.GetByte(26)
        d['filter']=f.GetByte(27)
        d['interlace']=f.GetByte(28)
        d['_shortdescription']=fmts_PNG
        d['_longdescription']=fmt_PNG
        d['mimetypes']=['image/png', 'image/x-png']
        for i in d.itervalues():
            if i is None:  return None
        ifi=ImgFileInfo(f,**d)
        return ifi
    return None

def fmts_PNG(ifi, short=True):
    res=[]
    res.append( "%d x %d" % (ifi.width, ifi.height) )
    res.append( ifi.format)
    if ifi.colourtype in (0,4):
        res.append("%d bit grayscale" % (ifi.bitdepth,))
    elif ifi.colourtype in (2,6):
        res.append("truecolour (%d bit)" % (ifi.bitdepth*3,))
    elif ifi.colourtype==3:
        res.append("%d colours" % (2**ifi.bitdepth,))
    if not short and ifi.colourtype in (4,6):
            res.append("with transparency")
    return " ".join(res)

def fmt_PNG(ifi):
    "Long description for PNG"
    res=[fmts_PNG(ifi, False)]

    if ifi.compression==0:
        res.append("Deflate compressed")
    else:
        res.append("Unknown compression "+`ifi.compression`)

    if ifi.filter==0:
        res.append("Adaptive filtering")
    else:
        res.append("Unknown filtering "+`ifi.filter`)

    if ifi.interlace==0:
        res.append("No interlacing")
    elif ifi.interlace==1:
        res.append("Adam7 interlacing")
    else:
        res.append("Unknown interlacing "+`ifi.interlace`)
    return "\n".join(res)
                   
def idimg_BCI(f):
    "Identify a Brew Compressed Image"
    if f.GetBytes(0,4)=="BCI\x00":
        d={'format': "BCI"}
        d['width']=f.GetLSBUint16(0x0e)
        d['height']=f.GetLSBUint16(0x10)
        d['bpp']=8
        d['ncolours']=f.GetLSBUint16(0x1a)
        d['_longdescription']=fmt_BCI
        d['mimetypes']=['image/x-brewcompressedimage']
        for i in d.itervalues():
            if i is None:  return None
        ifi=ImgFileInfo(f,**d)
        return ifi
    return None

def fmt_BCI(ifi):
    "Long description for BCI"
    res=[ifi.shortdescription()]
    res.append("%d colour palette" % (ifi.ncolours,))
    return "\n".join(res)

def idimg_JPG(f):
    "Identify a JPEG image"
    # The people who did jpeg decided to see just how complicated an image
    # format they could make.
    if f.GetBytes(0,2)=="\xff\xd8":
        # in theory we could also parse EXIF information
        offset=2
        while True:
            # we just skip the segments until we find SOF0 (0xc0)
            # I can't figure out from the docs if we should also care about SOF1/SOF2 etc
            if f.GetByte(offset)!=0xff:
                return None
            id=f.GetByte(offset+1)
            offset+=2
            seglen=f.GetMSBUint16(offset)
            if seglen is None or id is None: return None
            if id!=0xc0:
                offset+=seglen
                continue
            offset+=2
            d={'format': 'JPEG'}
            d['bpp']=3*f.GetByte(offset)
            d['height']=f.GetMSBUint16(offset+1)
            d['width']=f.GetMSBUint16(offset+3)
            d['components']=f.GetByte(offset+5)
            d['_shortdescription']=fmts_JPG
            d['mimetypes']=['image/jpg', 'image/jpeg', 'image/x-jpg', 'image/x-jpeg']
            for i in d.itervalues():
                if i is None:  return None
            ifi=ImgFileInfo(f,**d)
            return ifi            
    return None

def fmts_JPG(ifi):
    res=[]
    res.append( "%d x %d" % (ifi.width, ifi.height) )
    res.append( ifi.format)
    if ifi.components==1:
        res.append("(greyscale)")
    elif ifi.components==3:
        res.append("(RGB)") # technically it is YcbCr ...
    elif ifi.components==4:
        res.append("(CMYK)")
    else:
        res.append("Unknown components "+`ifi.components`)
    return " ".join(res)

def idimg_GIF(f):
    "Identify a GIF image"
    if f.GetBytes(0, 3)!='GIF':
        # not a GIF image
        return None
    d={ 'format': 'GIF' }
    d['version']=f.GetBytes(3, 3)
    d['width']=f.GetLSBUint16(6)
    d['height']=f.GetLSBUint16(8)
    d['_shortdescription']=fmts_GIF
    d['mimetypes']=['image/gif', 'image/x-gif']
    ofs=13
    i=f.GetByte(10)
    if (i&0x80):
        # there's a global color table, skip it
        bpp=(i&0x7)+1
        d['bpp']=bpp
        ofs+=3*(2**bpp)
    # check for data block
    i=f.GetByte(ofs)
    if i!=0x2c:
        # not an image data block
        if d['version']=='89a' and i==0x21:
            # extension block, just return what we have so far
            return ImgFileInfo(f, **d)
        else:
            # unknown block, bail
            return None
    # get local data
    d['width']=f.GetLSBUint16(ofs+5)
    d['height']=f.GetLSBUint16(ofs+7)
    i=f.GetByte(ofs+9)
    if (i&0x80):
        d['bpp']=(i&0xf)+1
    return ImgFileInfo(f, **d)

def fmts_GIF(ifi):
    res=[]
    res.append( "%d x %d" % (ifi.width, ifi.height) )
    res.append( '%s%s'%(ifi.format, ifi.version))
    if ifi.bpp is not None:
        res.append( '%d BPP'%ifi.bpp)
    return ' '.join(res)

def idimg_AVI(f):
    "identify an AVI file format"
    if f.GetBytes(0, 4)!='RIFF' or f.GetBytes(8, 8)!='AVI LIST' or\
       f.GetBytes(20, 8)!='hdrlavih':
        # not an AVI file
        return None
    d={ 'format': 'AVI' }
    d['duration']=float(f.GetLSBUint32(0x20))*f.GetLSBUint32(0x30)/1000000.0
    d['width']=f.GetLSBUint32(0x40)
    d['height']=f.GetLSBUint32(0x44)
    d['_shortdescription']=fmts_AVI
    d['mimetypes']=['video/avi', 'video/msvideo', 'video/x-msvideo',
                    'video/quicktime' ]
    return ImgFileInfo(f, **d)

def fmts_AVI(ifi):
    res=['%d x %d' % (ifi.width, ifi.height)]
    res.append('%.1fs video'%ifi.duration)
    return ' '.join(res)

def idimg_LGBIT(f):
    "Identify a LGBIT image (LG phone proprietary image format)"
    # Profoundly lean and mean image format
    # width/height/image-data
    # This is for the LG-VX3200. Image data is 16 bit, R5G6B5.
    width=f.GetLSBUint16(0x00)
    height=f.GetLSBUint16(0x02)
    if width is None or height is None:
        return None
    if f.size==(width*height*2+4):
        d={'format': "LGBIT"}
        d['width']=width
        d['height']=height
        d['bpp']=16
        d['_shortdescription']=fmts_LGBIT
        for i in d.itervalues():
            if i is None:  return None
        ifi=ImgFileInfo(f,**d)
        return ifi
    return None

def fmts_LGBIT(ifi):
    res=[]
    res.append( "%d x %d" % (ifi.width, ifi.height) )
    res.append( '%s'%(ifi.format))
    if ifi.bpp is not None:
        res.append( '%d BPP'%ifi.bpp)
    return ' '.join(res)

def idimg_3GPP2(f):
    "Identify a 3GPP2(3g2) file"
    if f.GetBytes(4, 8)!='ftyp3g2a':
        # Not a 3GPP2 file
        return None
    d={ 'format': '3GPP2',
        'mimetypes': ['video/3gpp2'] }
    return ImgFileInfo(f, **d)
    
imageids=[globals()[f] for f in dir() if f.startswith("idimg_")]
def identify_imagefile(filename):
    v=thefileinfocache.get(filename)
    if v is not None: return v
    fo=SafeFileWrapper(filename)
    for f in imageids:
        obj=f(fo)
        if obj is not None:
            return thefileinfocache.set(filename,obj)
    return thefileinfocache.set(filename,ImgFileInfo(fo))

def identify_imagestring(string):
    # identify an image format based on the image data string
    fo=SafeStringWrapper(string)
    for f in imageids:
        obj=f(fo)
        if obj is not None:
            return obj

class AudioFileInfo:
    "Wraps information about an audio file"

    # These will always be present
    attrnames=("format", "size", "duration", "MAXSIZE")

    def __init__(self, f, **kwds):
        for a in self.attrnames:
            setattr(self, a, None)
        self.mimetypes=[]
        self.size=f.size
        self.__dict__.update(kwds)

    def shortdescription(self):
        v=getattr(self, "_shortdescription", None)
        if v is not None:
            return v(self)        
        res=[]
        if self.format is not None:
            res.append( self.format)
        if self.duration is not None:
            res.append( "%d seconds" % (self.duration,))

        if len(res):
            return " ".join(res)
        return "Unknown format"

    def longdescription(self):
        v=getattr(self, "_longdescription", None)
        if v is not None:
            return v(self)
        return self.shortdescription()

def idaudio_MIDI(f):
    "Identify a midi file"
    # http://www.borg.com/~jglatt/tech/midifile.htm
    #
    # You can't work out the length without working out
    # which track is the longest which you have to do by
    # parsing each note.
    m=midifile.MIDIFile(f)
    if not m.valid:
        return None
    d={'format': "MIDI"}
    d['type']=m.type
    d['numtracks']=m.num_tracks
    d['duration']=m.duration
    d['_shortdescription']=fmts_MIDI
    d['mimetypes']=['audio/x-midi', 'audio/midi']
    for i in d.itervalues():
        if i is None:  return None
    afi=AudioFileInfo(f,**d)
    return afi

def fmts_MIDI(afi):
    res=[]
    res.append( afi.format)
    res.append( "type "+`afi.type`)
    if afi.type!=0 and afi.numtracks>1:
        res.append("(%d tracks)" % (afi.numtracks,))
    res.append('%0.1f seconds'%afi.duration)
    # res.append("%04x" % (afi.division,))
    return " ".join(res)

def _getbits(start, length, value):
    assert length>0
    return (value>>(start-length+1)) & ((2**length)-1)

def getmp3fileinfo(filename):
    f=SafeFileWrapper(filename)
    return idaudio_zzMP3(f, True)

def getmp4fileinfo(filename):
    f=SafeFileWrapper(filename)
    return idaudio_MP4(f)


twooheightzeros="\x00"*208
# want to make sure this gets evaluated last
def idaudio_zzMP3(f, returnframes=False):
    # http://mpgedit.org/mpgedit/mpeg_format/mpeghdr.htm
    try:
        idv3present=False
        id3v1present=False

        header=f.GetMSBUint32(0)

        # there may be ffmpeg output with 208 leading zeros for no apparent reason
        if header==0 and f.data.startswith(twooheightzeros):
            offset=208
        # there may be an id3 header at the begining
        elif header==0x49443303:
            sz=[f.GetByte(x) for x in range(6,10)]
            if len([zz for zz in sz if zz<0 or zz>=0x80]):
                return None
            sz=(sz[0]<<21)+(sz[1]<<14)+(sz[2]<<7)+sz[3]
            offset=10+sz
            idv3present=True
            header=f.GetMSBUint32(offset)
        elif header is None:
            return None
        else:
            offset=0

        # locate the 1st sync frame
        while True:
            v=f.GetMSBUint16(offset)
            if v is None: return None
            if v&0xffe0==0xffe0:
                break
            offset=f.data.find("\xff", offset+1)
            if offset<0:
                # not an mp3 file or sync is way later in
                return None

        frames=[]
        while offset<f.size:
            if offset==f.size-128 and f.GetBytes(offset,3)=="TAG":
                offset+=128
                id3v1present=True
                continue
            frame=MP3Frame(f, offset)
            if not frame.OK or frame.nextoffset>f.size:  break
            offset=frame.nextoffset
            frames.append(frame)

        if len(frames)==0: return

        if offset!=f.size:
            print "MP3 offset is",offset,"size is",f.size

        # copy some information from the first frame
        f0=frames[0]
        d={'format': 'MP3',
           'id3v1present': id3v1present,  # badly named ...
           'idv3present': idv3present,
           'unrecognisedframes': offset!=f.size,
           'version': f0.version,
           'layer': f0.layer,
           'bitrate': f0.bitrate,
           'samplerate': f0.samplerate,
           'channels': f0.channels,
           'copyright': f0.copyright,
           'original': f0.original,
           'mimetypes': ['audio/x-mp3', 'audio/mpeg', 'audio/x-mpeg']}

        duration=f0.duration
        vbrmin=vbrmax=f0.bitrate
        
        for frame in frames[1:]:
            duration+=frame.duration
            if frame.bitrate!=f0.bitrate:
                d['bitrate']=0
            if frame.samplerate!=f0.samplerate:
                d['samplerate']=0
                vbrmin=min(frame.bitrate,vbrmin)
                vbrmax=max(frame.bitrate,vbrmax)
            if frame.channels!=f0.channels:
                d['channels']=0
          
        d['duration']=duration
        d['vbrmin']=vbrmin
        d['vbrmax']=vbrmax
        d['_longdescription']=fmt_MP3
        d['_shortdescription']=fmts_MP3

        if returnframes:
            d['frames']=frames

        return AudioFileInfo(f, **d)
    except:
        return None

def fmt_MP3(afi):
    res=[]
    res.append("MP3 (Mpeg Version %d Layer %d)" % (afi.version, afi.layer))
    res.append("%s %.1f Khz %0.1f seconds" % (["Variable!!", "Mono", "Stereo"][afi.channels], afi.samplerate/1000.0, afi.duration,))
    if afi.bitrate:
        res.append(`afi.bitrate`+" kbps")
    else:
        res.append("VBR (min %d kbps, max %d kbps)" % (afi.vbrmin, afi.vbrmax))
    if afi.unrecognisedframes:
        res.append("There are unrecognised frames in this file")
    if afi.idv3present:
        res.append("IDV3 tag present at begining of file")
    if afi.id3v1present:
        res.append("IDV3.1 tag present at end of file")
    if afi.copyright:
        res.append("Marked as copyrighted")
    if afi.original:
        res.append("Marked as the original")

    return "\n".join(res)

def fmts_MP3(afi):
    return "MP3 %s %dKhz %d sec" % (["Variable!!", "Mono", "Stereo"][afi.channels], afi.samplerate/1000.0, afi.duration,)


class MP3Frame:

    bitrates={
        # (version, layer): bitrate mapping
        (1, 1): [None, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, None],
        (1, 2): [None, 32, 48, 56,  64,  80,  96, 112, 128, 160, 192, 224, 256, 320, 384, None],
        (1, 3): [None, 32, 40, 48,  56,  64,  80,  96, 112, 128, 160, 192, 224, 256, 320, None],
        (2, 1): [None, 32, 48, 56,  64,  80,  96, 112, 128, 144, 160, 176, 192, 224, 256, None],
        (2, 2): [None,  8, 16, 24,  32,  40,  48,  56,  64,  80,  96, 112, 128, 144, 160, None],
        (2, 3): [None,  8, 16, 24,  32,  40,  48,  56,  64,  80,  96, 112, 128, 144, 160, None],
        }

    samplerates={
        1: [44100, 48000, 32000, None],
        2: [22050, 24000, 16000, None]
        }

    def __init__(self, f, offset):
        self.OK=False
        header=f.GetMSBUint32(offset)
        if header is None: return
        # first 11 buts must all be set
        if _getbits(31,11, header)!=2047:
            return
        self.header=header
        # Version
        version=_getbits(20,2,header)
        if version not in (2,3):  # we don't support 'reserved' or version 2.5
            return
        if version==3: # yes, version 1 is encoded as 3
            version=1
        self.version=version
        # Layer
        layer=_getbits(18,2,header)
        if layer==0: return # reserved which we don't support
        if layer==1:
            self.layer=3
        elif layer==2:
            self.layer=2
        elif layer==3:
            self.layer=1
        self.crc=_getbits(16,1,header)
        self.bitrate=self.bitrates[(self.version, self.layer)][_getbits(15,4,header)]
        self.samplerate=self.samplerates[self.version][_getbits(11,2,header)]
        self.padding=_getbits(9,1,header)
        if self.layer==1:
            self.framelength=(12000*self.bitrate/self.samplerate+self.padding)*4
        else:
            if self.version==1:
                self.framelength=144000*self.bitrate/self.samplerate+self.padding
            else:
                self.framelength=72000*self.bitrate/self.samplerate+self.padding
        self.duration=self.framelength*8*1.0/(self.bitrate*1000)
        self.private=_getbits(8,1,header)
        self.channelmode=_getbits(7,2,header)
        if self.channelmode in (0,1,2):
            self.channels=2
        else:
            self.channels=1
        
        self.modeextenstion=_getbits(5,2,header)
        self.copyright=_getbits(3,1,header)
        self.original=_getbits(2,1, header)
        self.emphasis=_getbits(1,2, header)

        self.offset=offset
        self.nextoffset=offset+self.framelength
        self.OK=True

def idaudio_QCP(f):
    "Identify a Qualcomm Purevoice file"
    # http://www.faqs.org/rfcs/rfc3625.html
    #
    # Sigh, another format where you have no hope of being able to work out the length
    if f.GetBytes(0,4)=="RIFF" and f.GetBytes(8,4)=="QLCM":
        d={'format': "QCP"}
        
        # fmt section
        if f.GetBytes(12,4)!="fmt ":
            return None
        # chunksize is at 16, len 4
        d['qcpmajor']=f.GetByte(20)
        d['qcpminor']=f.GetByte(21)
        # guid is at 22
        d['codecguid']=(f.GetLSBUint32(22), f.GetLSBUint16(26), f.GetLSBUint16(28), f.GetMSBUint16(30), (long(f.GetMSBUint16(32))<<32)+f.GetMSBUint32(34))
        d['codecversion']=f.GetLSBUint16(38)
        name=f.GetBytes(40,80)
        zero=name.find('\x00')
        if zero>=0:
            name=name[:zero]
        d['codecname']=name
        d['averagebps']=f.GetLSBUint16(120)
        # packetsize is at 122, len 2
        # block size is at 124, len 2
        d['samplingrate']=f.GetLSBUint16(126)
        d['samplesize']=f.GetLSBUint16(128)
        d['_longdescription']=fmt_QCP

        if d['codecguid']==( 0x5e7f6d41, 0xb115, 0x11d0, 0xba91, 0x00805fb4b97eL ) or \
           d['codecguid']==( 0x5e7f6d42, 0xb115, 0x11d0, 0xba91, 0x00805fb4b97eL ):
            d['mimetypes']=['audio/qcelp'] # in theory audio/vnd.qcelp could also be used but is deprecated
        elif d['codecguid']==( 0xe689d48dL, 0x9076, 0x46b5, 0x91ef, 0x736a5100ceb4L ):
            d['mimetypes']=['audio/evrc-qcp']
        elif d['codecguid']==( 0x8d7c2b75L, 0xa797, 0xed49, 0x985e, 0xd53c8cc75f84L ):
            d['mimetypes']=['audio/smv-qcp']
        
        for i in d.itervalues():
            if i is None:  return None
        afi=AudioFileInfo(f,**d)
        return afi
    return None

def fmt_QCP(afi):
    res=["QCP %s" % (afi.codecname,)]
    res.append("%d bps %d Hz %d bits/sample" % (afi.averagebps, afi.samplingrate, afi.samplesize))
    codecguid=afi.codecguid
    if   codecguid==( 0x5e7f6d41, 0xb115, 0x11d0, 0xba91, 0x00805fb4b97eL ):
        res.append("QCELP-13K V"+`afi.codecversion` + "  (guid 1)")
    elif codecguid==( 0x5e7f6d42, 0xb115, 0x11d0, 0xba91, 0x00805fb4b97eL ):
        res.append("QCELP-13K V"+`afi.codecversion` + "  (guid 2)")
    elif codecguid==( 0xe689d48dL, 0x9076, 0x46b5, 0x91ef, 0x736a5100ceb4L ):
        res.append("EVRC V"+`afi.codecversion`)
    elif codecguid==( 0x8d7c2b75L, 0xa797, 0xed49, 0x985e, 0xd53c8cc75f84L ):
        res.append("SMV V"+`afi.codecversion`)
    else:
        res.append("Codec Guid {%08X-%04X-%04X-%04X-%012X} V%d" % (afi.codecguid+(afi.codecversion,)))
    res.append("QCP File Version %d.%d" % (afi.qcpmajor, afi.qcpminor))
    
    return "\n".join(res)

def idaudio_PMD(f):
    "Identify a PMD/CMX file"
    # There are no specs for this file format.  From 10 minutes of eyeballing, it seems like below.
    # Each section is a null terminated string followed by a byte saying how long the data is.
    # The length is probably some sort of variable length encoding such as the high bit indicating
    # the last byte and using 7 bits.
    #
    # offset contents -- comment
    #      0 cmid     -- file type id
    #      4 \0\0     -- no idea
    #      6 7*?      -- file lengths and pointers
    #     13 vers\0   -- version section
    #     18 \x04     -- length of version section
    #     19 "string" -- a version number that has some correlation with the pmd version number
    #
    #  Various other sections that cover the contents that don't matter for identification
    try:
        if f.GetBytes(0, 4)!='cmid':
            return None
        d={ 'format': 'PMD' }
        hdr_len=f.GetMSBUint16(8)
        i=f.GetByte(10)
        d['content']=['Unknown', 'Ringer', 'Pictures&Audio'][i]
        d['numtracks']=f.GetByte(12)
        ofs=13
        ofs_end=hdr_len+10
        while ofs<ofs_end:
            s=f.GetBytes(ofs, 4)
            i=f.GetMSBUint16(ofs+4)
            ofs+=6
            if i==0:
                continue
            if s=='vers':
                d['version']=f.GetBytes(ofs, i)
            elif s=='titl':
                d['title']=f.GetBytes(ofs, i)
            elif s=='cnts':
                d['media']=f.GetBytes(ofs, i)
            ofs+=i
        d['_longdescription']=fmt_PMD
        d['_shortdescription']=fmts_PMD
        return AudioFileInfo(f, **d)
    except:
        return None

def fmts_PMD(afi):
    return 'PMD/CMF %s'% afi.content

def fmt_PMD(afi):
    res=['PMD/CMF']
    if hasattr(afi, 'version'):
        res.append('Version: '+afi.version)
    res.append('Content: '+afi.content)
    res.append('%d Tracks'%afi.numtracks)
    if hasattr(afi, 'title'):
        res.append('Title: '+afi.title)
    if hasattr(afi, 'media'):
        res.append('Media: '+afi.media)
    return '\n'.join(res)
    
def idaudio_PCM(f):
    "Identify a PCM/WAV file"
    try:
        if f.GetBytes(0, 4)!='RIFF' or f.GetBytes(8, 4)!='WAVE' or \
           f.GetBytes(12, 4)!='fmt ' or f.GetLSBUint16(20)!=1:
            return None
        d={ 'format': 'PCM',
            'mimetypes': ['audio/wav', 'audio/x-wav',
                          'audio/wave', 'audio/x-pn-wav'] }
        d['numchannels']=f.GetLSBUint16(22)
        d['samplerate']=f.GetLSBUint32(24)
        d['byterate']=f.GetLSBUint32(28)
        d['blockalign']=f.GetLSBUint16(32)
        d['bitspersample']=f.GetLSBUint16(34)
        # compute the approximate duration
        subchunk1size=f.GetLSBUint32(16)
        datasize=f.GetLSBUint32(20+subchunk1size+4)
        d['duration']=float(datasize)/(d['blockalign']*d['samplerate'])
        d['_longdescription']=fmt_PCM
        d['_shortdescription']=fmts_PCM
        return AudioFileInfo(f, **d)
    except:
        return None

def fmts_PCM(afi):
    return afi.format

def fmt_PCM(afi):
    res=['PCM/WAV']
    res.append('%d KHz %d bits %s'%\
               (afi.samplerate/1000, afi.bitspersample,\
                ['None', 'Mono', 'Stereo'][afi.numchannels]))
    return '\n'.join(res)

def getpcmfileinfo(filename):
    f=SafeFileWrapper(filename)
    return idaudio_PCM(f)

# WMA file support
def idaudio_WMA(f):
    "Identify a WMA file"
    try:
        _wma=wma_file.WMA_File(f)
        if not _wma.valid:
            return None
        d={ 'format': 'WMA',
            'mimetypes': ['audio/x-ms-wma'],
            'duration': _wma.play_duration,
            'title': _wma.title,
            'artist': _wma.author,
            'album': _wma.album,
            'genre': _wma.genre,
            '_longdescription': fmt_WMA,
            }
        return AudioFileInfo(f, **d)
    except:
        if __debug__:
            raise

def fmt_WMA(afi):
    res=['WMA', 'Duration: %.2f'%afi.duration ]
    if afi.title:
        res.append('Title: %s'%afi.title)
    if afi.artist:
        res.append('Artist: %s'%afi.artist)
    if afi.album:
        res.append('Album: %s'%afi.album)
    if afi.genre:
        res.append('Genre: %s'%afi.genre)
    return '\n'.join(res)

# MPEG4 file support
def idaudio_MP4(f):
    "Identify a MP4 file"
    try:
        _mp4=mp4_file.MP4_File(f)
        if not _mp4.valid:
            return None
        d={ 'format': 'MP4',
            'mimetypes': ['audio/mpeg4'],
            'duration': _mp4.duration,
            'title':    _mp4.title,
            'artist':   _mp4.artist,
            'album':    _mp4.album,
            'bitrate':  _mp4.bitrate,
            'samplerate': _mp4.samplerate,
            '_longdescription': fmt_MP4,
            }
        return AudioFileInfo(f, **d)
    except:
        if __debug__:
            raise


def fmt_MP4(afi):
    res=[]
    res.append("MPEG4")
    res.append("%.1f Khz %0.1f seconds" % (afi.samplerate/1000.0, afi.duration,))
    if afi.bitrate:
        res.append(`afi.bitrate`+" kbps")
    if afi.title:
        res.append('Title: %s'%afi.title)
    if afi.artist:
        res.append('Artist: %s'%afi.artist)
    if afi.album:
        res.append('Album: %s'%afi.album)
                                        
    return "\n".join(res)

audioids=[globals()[f] for f in dir() if f.startswith("idaudio_")]
def identify_audiofile(filename):
    v=thefileinfocache.get(filename)
    if v is not None: return v
    fo=SafeFileWrapper(filename)
    for f in audioids:
        obj=f(fo)
        if obj is not None:
            return thefileinfocache.set(filename, obj)
    return thefileinfocache.set(filename, AudioFileInfo(fo))

def identify_audiostring(string):
    # identify an audio format based on the audio data string
    fo=SafeStringWrapper(string)
    for f in audioids:
        obj=f(fo)
        if obj is not None:
            return obj
###
###  caches for audio/image id
###

thefileinfocache=common.FileCache(lowwater=100,hiwater=140)
