### BITPIM
###
### Copyright (C) 2003-2004 Stephen Wood <sawecw@users.sf.net>
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: conversions.py 4381 2007-08-29 00:19:51Z djpham $

"Routines to do various file format conversions"
from __future__ import with_statement
import contextlib
import os
import tempfile
import struct
import subprocess
import sys
import wx


import common

class ConversionFailed(Exception): pass

helperdir=os.path.join(common.get_main_dir(), "helpers")

osext={'win32': '.exe',
       'darwin': '.mbin',
       'linux2': '.lbin'} \
       [sys.platform]

# This shortname crap is needed because Windows programs (including ffmpeg)
# don't correctly parse command line arguments.
if sys.platform=='win32':
    import win32api
    def shortfilename(x):
        # the name may already be short (eg from tempfile which always returns short names)
        # and may not exist, so we are careful to only call GetShortPathName if necessary
        if " " in x:
            return win32api.GetShortPathName(x)
        return x
else:
    def shortfilename(x): return x

def gethelperbinary(basename):
    "Returns the full pathname to the specified helper binary"
    if basename=="pvconv":
        return getpvconvbinary()
    f=os.path.join(helperdir, basename)+osext
    try:
        f=shortfilename(f)
    except:
        # this craps out if the helper does not exist!
        raise common.HelperBinaryNotFound(basename, basename+osext, [helperdir])
    if not os.path.isfile(f):
        raise common.HelperBinaryNotFound(basename, basename+osext, [helperdir])
    return f


_foundpvconv=None

def getpvconvbinary():
    "PVConv can't be distributed with BitPim so the user has to install it and we have to find it"
    global _foundpvconv
    # check each time as user could delete or more binary
    if _foundpvconv is not None and os.path.isfile(_foundpvconv):
        return _foundpvconv
    _foundpvconv=None
    lookin=[]
    if sys.platform=='win32':
        binary="pvconv.exe"
        lookin.append("c:\\bin")
        from win32com.shell import shell, shellcon
        path=shell.SHGetFolderPath(0, shellcon.CSIDL_PROGRAM_FILES, None, 0)
        if path:
            lookin.append(os.path.join(path, "Qualcomm"))
            lookin.append(os.path.join(path, "pvconv"))
        path=shell.SHGetFolderPath(0, shellcon.CSIDL_WINDOWS, None, 0)
        if path:
            lookin.append(path)
    elif sys.platform=='linux2':
        binary="pvconv"
        lookin.append(_expand("~/bin"))
        lookin.append(_expand("~"))
        lookin.append(_expand("/usr/local/bin"))
    elif sys.platform=='darwin':
        binary="pvconv"
        lookin.append(_expand("~/bin"))
        lookin.append(_expand("~"))
        lookin.append(_expand("/usr/local/bin"))
        lookin.append(_expand("/usr/bin"))
    else:
        raise Exception("Unknown platform "+sys.platform)
    for dir in lookin:
        f=os.path.join(dir, binary)
        if os.path.exists(f):
            _foundpvconv=f
            return _foundpvconv

    raise common.HelperBinaryNotFound("pvconv", binary, lookin)
        
        

def _expand(x):
    return os.path.expandvars(os.path.expanduser(x))

def run(*args):
    """Runs the specified command (args[0]) with supplied parameters.
    Note that your path is not searched for the command."""
    print args
    p=subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True)
    _res=p.communicate()
    if p.returncode:
        # an error occurred, log it
        print _res[1]
        raise common.CommandExecutionFailed(p.returncode, args, _res[1])

def convertto8bitpng(pngdata, maxsize):
    "Convert a PNG file to 8bit color map"

    # Return files small enough, or not PNG as is
    size=len(pngdata)
    if size<=maxsize or pngdata[1:4]!='PNG':
        return pngdata

    p=sys.path[0]
    if os.path.isfile(p):
        p=os.path.dirname(p)
    helpersdirectory=os.path.abspath(os.path.join(p, 'helpers'))
    print "Helper Directory: "+helpersdirectory
    if sys.platform=='win32':
        osext=".exe"
    if sys.platform=='darwin':
        osext=".mbin"
    if sys.platform=='linux2':
        osext=".lbin"
        
    pngtopnmbin=gethelperbinary('pngtopnm')
    ppmquantbin=gethelperbinary('ppmquant')
    pnmtopngbin=gethelperbinary('pnmtopng')
    print "pngtopnm: "+pngtopnmbin
    print "ppmquant: "+ppmquantbin
    print "pnmtopng: "+pnmtopngbin

    # Write original image to a temp file
    png=common.gettempfilename("png")
    open(png, "wb").write(pngdata)

    # Convert this image to pnm
    pnm=common.gettempfilename("pnm")
    s='"'+pngtopnmbin+'"' + ' < '+png+' > '+pnm
    os.system(s)
    #self.log(s)
    os.remove(png)

    # Binary search to find largest # of colors with a file size still
    # less than maxsize

    ncolormax=257
    ncolormin=1
    ncolortry=256
    ncolor=ncolortry
    pnmq=common.gettempfilename("pnm")

    while size>maxsize or ncolormax-ncolor>1:
        ncolor=ncolortry
        s='"'+ppmquantbin+'"'+' '+`ncolortry`+' '+pnm+ ' > '+pnmq
        #self.log(s)
        os.system(s)
        s ='"'+pnmtopngbin+'"' + ' < ' + pnmq + ' > '+png
        #self.log(s)
        os.system(s)
        os.remove(pnmq)
        pngquantdata=open(png,"rb").read()
        os.remove(png)
        size=len(pngquantdata)
        print `ncolor`+' '+`size`
        if size>maxsize:
            ncolormax=ncolor
            ncolortry=(ncolor+ncolormin)/2
        else:
            ncolormin=ncolor
            ncolortry=(ncolor+ncolormax)/2

    os.remove(pnm)
    return pngquantdata

def convertto8bitpng_joe(pngdata):
    "Convert a PNG file to 8bit color map"
    "Separate routine for now so not to screw up existing one, may merge later"
    if pngdata[1:4]!='PNG':
        return pngdata
    # get the path to helper
        
    pngtopnmbin=gethelperbinary('pngtopnm')
    ppmquantbin=gethelperbinary('ppmquant')
    pnmtopngbin=gethelperbinary('pnmtopng')
    print "pngtopnm: "+pngtopnmbin
    print "ppmquant: "+ppmquantbin
    print "pnmtopng: "+pnmtopngbin
    # Write original image to a temp file
    png=common.gettempfilename("png")
    open(png, "wb").write(pngdata)
    num_of_colors=wx.Image(png).ComputeHistogram(wx.ImageHistogram())
    print 'number of colors:', num_of_colors
    if num_of_colors>256:
        # no optimization possible, just return
        os.remove(png)
        return pngdata
    # else optimize it
    # Convert this image to pnm
    pnm=common.gettempfilename("pnm")
    s='"'+pngtopnmbin+'"' + ' < '+png+' > '+pnm
    os.system(s)
    os.remove(png)
    # quantize & convert
    pnmq=common.gettempfilename("pnm")
    s='"'+ppmquantbin+'"'+' '+`num_of_colors`+' '+pnm+ ' > '+pnmq
    os.system(s)
    s ='"'+pnmtopngbin+'"' + ' < ' + pnmq + ' > '+png
    os.system(s)
    os.remove(pnmq)
    pngquantdata=open(png, 'rb').read()
    os.remove(png)
    os.remove(pnm)
    print 'old size: ',len(pngdata),', new size: ',len(pngquantdata)
    return pngquantdata


def converttomp3(inputfilename, bitrate, samplerate, channels):
    """Reads inputfilename and returns data for an mp3 conversion

    @param bitrate: bitrate to use in khz (ie 16 is 16000 bits per second)
    @param samplerate: audio sampling rate in Hertz
    @param channels: 1 is mono, 2 is stereo
    """
    ffmpeg=gethelperbinary("ffmpeg")
    with common.usetempfile('mp3') as mp3file:
        try:
            run(ffmpeg, "-i", shortfilename(inputfilename), "-hq", "-ab", `bitrate`, "-ar", `samplerate`, "-ac", `channels`, shortfilename(mp3file))
        except common.CommandExecutionFailed, e:
            # we get this exception on bad parameters, or any other
            # issue so we assume bad parameters for the moment.
            raise ConversionFailed, ' '.join(e.args)+'\n'+e.logstr
        return file(mp3file, "rb").read()

def converttowav(mp3filename, wavfilename, samplerate=None,
                    channels=None, start=None, duration=None):
    ffmpeg=gethelperbinary("ffmpeg")
    cmd=(ffmpeg, "-i", shortfilename(mp3filename))
    if samplerate is not None:
        cmd+=('-ar', str(samplerate))
    if channels is not None:
        cmd+=('-ac', str(channels))
    if start is not None:
        cmd+=('-ss', str(start))
    if duration is not None:
        cmd+=('-t', str(duration))
    cmd+=(shortfilename(wavfilename),)
    # ffmpeg queries about overwrite - grrr
    try: os.remove(cmd[-1])
    except OSError: pass

    run(*cmd)

_qcp_optimization_params=('ffr', 'vfr', 'fhr', 'vhr')
def convertwavtoqcp(wavfile, qcpfile, optimization=None):
    pvconv=shortfilename(gethelperbinary('pvconv'))
    w_name=shortfilename(wavfile)
    q_name=common.stripext(w_name)+'.qcp'
    try:
        os.remove(q_name)
    except:
        pass
    # Have not figured out how to specify output file for pvconv
    if optimization is None:
        run(pvconv, w_name)
    else:
        run(pvconv, '-r', _qcp_optimization_params[optimization], w_name)
    # mv output file to qcpfile
    try:
        os.remove(qcpfile)
    except:
        pass
    os.rename(q_name, qcpfile)

def convertqcptowav(qcpfile, wavfile):
    pvconv=shortfilename(gethelperbinary('pvconv'))
    q_name=shortfilename(qcpfile)
    w_name=common.stripext(q_name)+'.wav'
    try:
        os.remove(w_name)
    except:
        pass
    run(pvconv, q_name)
    try:
        os.remove(wavfile)
    except:
        pass
    os.rename(w_name, wavfile)

def adjustwavfilevolume(wavfilename, gain):
    """ Ajdust the volume of a wav file.
    """
    with file(wavfilename, 'rb') as f:
        # read in the headers
        headers=f.read(20)
        subchunk1size=common.LSBUint32(headers[16:20])
        headers+=f.read(subchunk1size)
        headers+=f.read(8)  # 4 byte ID and 4 byte length
        subchunk2size=common.LSBUint32(headers[-4:])
        bitspersample=common.LSBUint16(headers[34:36])
        if bitspersample!=16:
            print 'Volume adjustment only works with 16-bit wav file',bitspersample
            return
        sample_num=subchunk2size/2  # always 16-bit per channel per sample
        temp_name=common.gettempfilename("wav")
        with file(temp_name, 'wb') as f_temp:
            f_temp.write(headers)
            delta=pow(10.0, (gain/10.0))
            for i in range(sample_num):
                d=int(struct.unpack('<h', f.read(2))[0]*delta)
                if d>32767:
                    d=32767
                elif d<-32768:
                    d=-32768
                f_temp.write(struct.pack('<h', d))
    os.remove(wavfilename)
    os.rename(temp_name, wavfilename)

def trimwavfile(wavfilename, wavoutfilename, start, duration=None, gain=None):
    with file(wavfilename, 'rb') as f:
        # read in the headers
        headers=f.read(20)
        subchunk1size=common.LSBUint32(headers[16:20])
        headers+=f.read(subchunk1size)
        subchunk2id=f.read(4)
        subchunk2size=common.LSBUint32(f.read(4))
        # check for a PCM file format
        if headers[:4]!='RIFF' or headers[8:12]!='WAVE' or \
        headers[12:16]!='fmt ' or common.LSBUint16(headers[20:22])!=1:
            # not a PCM file
            raise TypeError
        subchunk2start=20+subchunk1size
        subchunk2datastart=subchunk2start+8
        samplerate=common.LSBUint32(headers[24:28])
        blockalign=common.LSBUint16(headers[32:34])
        # compute new start & duration
        new_start=int(start*samplerate)*blockalign
        new_size=subchunk2size-new_start
        if duration is not None:
            i=int(duration*samplerate)*blockalign
            if i<new_size:
                new_size=i
        # go get it
        f.seek(new_start, 1)
        open(wavoutfilename, 'wb').write("".join(['RIFF',
                                                  common.LSBstr32(4+8+subchunk1size+8+new_size),
                                                  headers[8:],
                                                  'data',
                                                  common.LSBstr32(new_size),
                                                  f.read(new_size)]))
        if gain is not None:
            adjustwavfilevolume(wavoutfilename, gain)

def trimwavdata(wavedatain, start, duration=None):
    # check for a PCM file format
    if wavedatain[:4]!='RIFF' or wavedatain[8:12]!='WAVE' or \
       wavedatain[12:16]!='fmt ' or common.LSBUint16(wavedatain[20:22])!=1:
        raise ValueError, 'not a PCM file'
    subchunk1size=common.LSBUint32(wavedatain[16:20])
    subchunk2start=20+subchunk1size
    subchunk2size=common.LSBUint32(wavedatain[subchunk2start+4:subchunk2start+8])
    subchunk2datastart=subchunk2start+8
    samplerate=common.LSBUint32(wavedatain[24:28])
    blockalign=common.LSBUint16(wavedatain[32:34])
    # compute new start & duration
    new_start=int(start*samplerate)*blockalign
    newsubchunk2datastart=subchunk2datastart+new_start
    new_size=subchunk2size-new_start
    if duration is not None:
        i=int(duration*samplerate)*blockalign
        if i<new_size:
            new_size=i
    # return new data
    return 'RIFF'+common.LSBstr32(4+8+subchunk1size+8+new_size)+\
           wavedatain[8:subchunk2start]+\
           'data'+common.LSBstr32(new_size)+\
           wavedatain[newsubchunk2datastart:newsubchunk2datastart+new_size]

def convertjpgtoavi(jpg_data, avi_file_name, fps=4, new_file=False):
    bmp2avi=shortfilename(gethelperbinary('bmp2avi'))
    if new_file:
        # delete any existing file and start fresh
        try:
            os.remove(avi_file_name)
        except:
            pass
    # convert the jpg data to bmp data
    with contextlib.nested(common.usetempfile('jpg'),
                           common.usetempfile('bmp')) as (_jpg, _bmp):
        jpg_name=shortfilename(_jpg)
        bmp_name=shortfilename(_bmp)
        file(jpg_name, "wb").write(jpg_data)
        wx.Image(jpg_name).SaveFile(bmp_name, wx.BITMAP_TYPE_BMP)
        # add the bmp frame to the avi file
        run(bmp2avi, '-f', `fps`, '-i', bmp_name, '-o', avi_file_name)

def convertavitobmp(avi_data, frame_num=0):
    with common.usetempfile('avi') as _avi:
        avi_file=shortfilename(_avi)
        file(avi_file, 'wb').write(avi_data)
        return convertfileavitobmp(avi_file, frame_num)

def convertfileavitobmp(avi_file_name, frame_num=0):
    bmp2avi=shortfilename(gethelperbinary('bmp2avi'))
    with common.usetempfile('bmp') as _bmp:
        bmp_file_name=shortfilename(_bmp)
        run(bmp2avi, '-t', `frame_num`, '-i', shortfilename(avi_file_name),
            '-o', bmp_file_name)
        return wx.Image(bmp_file_name)

def convertfilelgbittobmp(bit_file_name):
    "File-based wrapper for convertlgbittobmp."
    with common.usetempfile('png') as bmp:
        bmpdata=convertlgbittobmp(file(bit_file_name,"rb").read())
        file(bmp, "wb").write(bmpdata)
        return wx.Image(bmp)
    
def convertlgbittobmp(bit_data):
    """Takes a BIT image file (LG proprietary) and returns BMP

    @param bit_data: 16BPP BIT image file data
    @return: 24BPP BMP image file data
    """
    width=common.LSBUint16(bit_data[0:2])
    height=common.LSBUint16(bit_data[2:4])
    img='BM'
    img+=common.LSBstr32(width*height*3+54)  # file size
    img+=common.LSBstr16(0)                  # unused
    img+=common.LSBstr16(0)                  # unused
    img+=common.LSBstr32(54)                 # offset to pixel data (from byte 0)
    img+=common.LSBstr32(40)                 # info section size
    img+=common.LSBstr32(width)              # image width
    img+=common.LSBstr32(height)             # image height
    img+=common.LSBstr16(1)                  # image planes
    img+=common.LSBstr16(24)                 # bits-per-pixel
    img+=common.LSBstr32(0)                  # compression type (0=uncompressed)
    img+=common.LSBstr32(0)                  # image size (may be 0 for uncompressed images)
    img+=common.LSBstr32(0)                  # (ignored)
    img+=common.LSBstr32(0)                  # (ignored)
    img+=common.LSBstr32(0)                  # (ignored)
    img+=common.LSBstr32(0)                  # (ignored)
    # Now on to the char data
    for h in range(height):
        for w in range(width):
            # images can be zero len on phone
            if len(bit_data)==0:
                bitdata = 0xffff
            else:
                bitind=(height-h-1)*width*2+(w*2)+4
                bitdata=common.LSBUint16(bit_data[bitind:bitind+2])
            red=(bitdata & 0xf800) >> 8
            green=(bitdata & 0x07e0) >> 3
            blue=(bitdata & 0x001f) << 3
            if (red & 0x8) != 0:
                red=red | 0x7
            if (green & 0x4) != 0:
                green=green | 0x3
            if (blue & 0x8) != 0:
                blue=blue | 0x7
            img+=chr(blue)
            img+=chr(green)
            img+=chr(red)
    return img

def convertbmptolgbit(bmp_data):
    """Takes a BMP image file and returns BIT image file (LG proprietary)

    @param bit_data: 8BPP or 24BPP BMP image file data
    @return: 16BPP LGBIT image file data
    """
    # This function only exists for the LG proprietary images (wallpaper, etc.)
    # on the LG-VX3200. 
    if bmp_data[0:2]!='BM':
        return None
    width=common.LSBUint32(bmp_data[18:22])
    height=common.LSBUint32(bmp_data[22:26])
    offset=common.LSBUint32(bmp_data[10:14])
    bpp=common.LSBUint16(bmp_data[28:30])
    img=common.LSBstr16(width)
    img+=common.LSBstr16(height)
    # Now on to the char data
    if bpp==8:
        # 8BPP (paletted) BMP data
        palette=bmp_data[54:54+256*4]
        for h in range(height):
            for w in range(width):
                bitind=(height-h-1)*width+w+offset
                palind=ord(bmp_data[bitind:bitind+1])*4
                blue=ord(palette[palind:palind+1])
                green=ord(palette[palind+1:palind+2])
                red=ord(palette[palind+2:palind+3])
                bitval=((red & 0xf8) << 8) | ((green & 0xfc) << 3) | ((blue & 0xf8) >> 3)
                img+=common.LSBstr16(bitval)
    elif bpp==24:
        # 24BPP (non-paletted) BMP data
        for h in range(height):
            for w in range(width):
                bitind=(height-h-1)*width*3+(w*3)+offset
                blue=ord(bmp_data[bitind:bitind+1])
                green=ord(bmp_data[bitind+1:bitind+2])
                red=ord(bmp_data[bitind+2:bitind+3])
                bitval=((red & 0xf8) << 8) | ((green & 0xfc) << 3) | ((blue & 0xf8) >> 3)
                img+=common.LSBstr16(bitval)
    else:
        return None
    return img

def helperavailable(helper_name):
    try:
        f=gethelperbinary(helper_name)
        return True
    except common.HelperBinaryNotFound:
        return False
    except:
        if __debug__: raise
        return False
