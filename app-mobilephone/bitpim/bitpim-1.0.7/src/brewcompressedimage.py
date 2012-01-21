#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: brewcompressedimage.py 2781 2006-01-30 23:18:32Z djpham $

"""Support for the BCI (Brew Compressed Image) format

Currently this code can read a BCI file.  You should call the
L{getimage} function.

"""

"""
integers are lsb

0000 - 0003 BCI\0
0004 - 0007 ?  (x0844 = 2116) [length of file]
0008 - 000b ?  (x0434 = 1076) [offset to first image
000c - 000d ?  (1)
000e - 000f width
0010 - 0011 height
0012 - 0013 ?  (1) 2
0014 - 0015 ?  (1) 2
0016 - 0017 ?  (1) 2
0018 - 0019 ?  (0)
001a - 001b ?  (8) [bits per pixel?]
001c - 001d ?  (1)
001e - 001f ?  [0x100 = 256 ] # number of entries in palette

palette
b,g,r,0  (32 bit entry)

next palette
0000 - 0001 ? (2) palette number/id
0002 - 0003 number of entries in palette

image
0000 - 0001 data length
0002 - 0003 ? (0)
0004 - 0005 width
0006 - 0007 height
0008 - 0009 ? (1)
000a - 000b ? (1)

"""

import common
import zlib
import cStringIO

import wx

class Display(wx.Frame):
    """Used for the builtin tester"""

    def __init__(self, file, parent=None):
        bmp=wx.BitmapFromImage(wx.Image(file))
        
        wx.Frame.__init__(self, parent, -1, "Image Display")

        b=wx.StaticBitmap(self, -1, bmp)

        b.SetSize((bmp.GetWidth(), bmp.GetHeight()))
        self.Fit()
        self.Show(True)


class MyImage:
    """An encapsulation of the image"""
    
    def __init__(self, width, height, bytes, palette):
        self.width=width
        self.height=height
        offset=0
        import cStringIO
        data=cStringIO.StringIO()
        for row in range(height):
            # print "\r"+`row`,
            # 32 bit alignment
            while (offset%4)!=0:
                offset+=1
            for col in range(width):
                v=ord(bytes[offset])
                offset+=1
                data.write(palette[v])

        self.data=data.getvalue()
        # print

    def toImage(self, img=None):
        """Converts image to wxImage

        @rtype: wxImage
        """
        if img is None:
            img=wx.EmptyImage(self.width, self.height)
        else:
            img.Destroy()
            img.Create(self.width, self.height)
        img.SetData(self.data)
        return img
        
class BCIPalette:
    """An encapsulation of the palette"""
    def __init__(self, data=""):
        pal=[]
        for offset in range(0, len(data), 4):
            assert data[3]=="\x00"
            pal.append(data[offset+2]+data[offset+1]+data[offset])
        self.pal=pal

    def __getitem__(self,e):
        return self.pal[e]

class MemoryInputStream(wx.InputStream):    
    def __init__(self, data):
        import cStringIO
        wx.InputStream.__init__(self,cStringIO.StringIO(data))

class FileInputStream(wx.InputStream):    
    def __init__(self, name):
        self.f=open(name, "rb")
        wx.InputStream.__init__(self, self.f)

    def __del__(self):
        self.f.close()

def getimage(stream, intoImage=None):
    """Returns a wxImage of the stream specified"""

    # try to read the entire thing in one gulp
    data=stream.read()
    # save hex version for debugging
    # f=open(file+".hex", "w")
    # f.write(common.datatohexstring(data))
    # f.close()

    palettes={}

    ### verify format

    # header
    assert data[0x00:0x04]=='BCI\x00'
    # file length
    assert readlsb(data[0x04:0x08])<=len(data)  # this would be == but the bci tool doesn't truncate the file!
    # image offset
    imageoffset=readlsb(data[0x08:0x0b])
    assert imageoffset<len(data)
    # ? (1)
    assert readlsb(data[0x0c:0x0e])==1
    # width, height
    width=readlsb(data[0x0e:0x10])
    height=readlsb(data[0x10:0x12])
    assert width>0 and height>0
    # number of objects/frames/palettes?  no idea on order
    numitem1=readlsb(data[0x12:0x14])
    numitem2=readlsb(data[0x14:0x16])
    numitem3=readlsb(data[0x16:0x18])
    # print "number of objects/frames/palettes?  no idea on order: %d, %d, %d" % (numitem1, numitem2, numitem3)
    numpalettes=numitem1  # just a guess
    numotherthing=numitem2 # no idea what they are, possibly 'frames' as in the doc
    numimages=numitem3 # images, probably 'object' as in the doc
    # ? (0)
    assert readlsb(data[0x18:0x1a])==0
    # palette depth?
    bpp=readlsb(data[0x1a:0x1c])
    # read the palettes
    offset=0x1c
    for _ in range(numpalettes):
        id=readlsb(data[offset:offset+2])
        # print "palette id",id
        offset+=2
        numentries=readlsb(data[offset:offset+2])
        # print "contains",numentries,"entries"
        offset+=2
        # f=open(file+".palette."+`id`+".hex", "w")
        # f.write(common.datatohexstring(data[offset:offset+numentries*4]))
        # f.close()
        pal=BCIPalette(data[offset:offset+numentries*4])
        offset+=numentries*4
        palettes[id]=pal

        
    # some other type of object, possibly frames as in the doc
    for _ in range(numotherthing):
        # we just ignore the contents for the moment
        # print common.datatohexstring(data[offset:offset+0x14])
        offset+=0x14

    # images
    for _ in range(numimages):
        szdata=readlsb(data[offset:offset+4])
        width=readlsb(data[offset+4:offset+6])
        height=readlsb(data[offset+6:offset+8])
        id1=readlsb(data[offset+8:offset+0xa]) # image id?
        id2=readlsb(data[offset+0xa:offset+0xc])  # palette id?
        offset+=0xc
        buf=data[offset:offset+szdata]
        res=zlib.decompress(buf)
        # f=open(file+".image."+`id1`+".hex", "w")
        # f.write(common.datatohexstring(res))
        # f.close()

        img=MyImage(width, height, res, palettes[id2])
    
        return img.toImage(intoImage)

def readlsb(data):
    """Read binary data in lsb"""
    res=0
    shift=0
    for i in data:
        res|=ord(i)<<shift
        shift+=8
    return res

BITMAP_TYPE_BCI=wx.BITMAP_TYPE_ANY+1

class BCIImageHandler(wx.PyImageHandler):

    def __init__(self):
        super(BCIImageHandler, self).__init__()
        self.SetName("BREW Compressed Image")
        self.SetExtension("bci")
        self.SetType(BITMAP_TYPE_BCI)
        self.SetMimeType("image/x-brewcompressedimage")

    def GetImageCount(self, _):
        # ::TODO:: return multiple images
        return 1

    def LoadFile(self, image, stream, verbose, index):
        try:
            getimage(stream, image)
            return True
        except:
            return False

    def SaveFile(self, image, stream, verbose):
        raise NotImplementedError

    def DoCanRead(self, stream):
        # Check to see if the stream is a valid BCI stream,
        return stream.read(4)=='BCI\x00'

BITMAP_TYPE_LGBIT=BITMAP_TYPE_BCI+1
class LGBITImageHandler(wx.PyImageHandler):
    def __init__(self):
        super(LGBITImageHandler, self).__init__()
        self.SetName('LG BIT Image')
        self.SetExtension('bit')
        self.SetType(BITMAP_TYPE_LGBIT)

    def GetImageCount(self, _):
        return 1

    def LoadFile(self, image, stream, verbose, index):
        return False
    def SaveFile(self, image, stream, verbose):
        return False
    def DoCanRead(self, stream):
        return False

wx.Image_AddHandler(BCIImageHandler())

if __name__=='__main__':
    import sys

    app=wx.PySimpleApp()
    if len(sys.argv)==2:
        f=Display(sys.argv[1])
    elif len(sys.argv)==3:
        bciconvert(sys.argv[1], sys.argv[2])
        f=Display(sys.argv[2])
    else:
        assert Exception, "not enough params"
    
    app.MainLoop()
