### BITPIM
###
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: common.py 4381 2007-08-29 00:19:51Z djpham $


# Documentation
"""Various classes and functions that are used by GUI and command line versions of BitPim"""

from __future__ import with_statement
from contextlib import contextmanager

# standard modules
import string
import cStringIO
import StringIO
import sys
import traceback
import tempfile
import random
import os
import imp
import unicodedata

class FeatureNotAvailable(Exception):
     """The device doesn't support the feature"""
     def __init__(self, device, message="The device doesn't support the feature"):
          Exception.__init__(self, "%s: %s" % (device, message))
          self.device=device
          self.message=message

class IntegrityCheckFailed(Exception):
     def __init__(self, device, message):
          Exception.__init__(self, "%s: %s" % (device, message))
          self.device=device
          self.message=message

class PhoneBookBusyException(Exception):
     "The phonebook is busy on the phone"
     pass
                  
class HelperBinaryNotFound(Exception):
     def __init__(self, basename, fullname, paths):
          Exception.__init__(self, "Helper binary %s not found.  It should be in one of %s" % (fullname, ", ".join(paths)))
          self.basename=basename
          self.fullname=fullname
          self.paths=paths

class CommandExecutionFailed(Exception):
     def __init__(self, retcode, args, logstr=None):
          Exception.__init__(self, "Command execution failed with code %d: %s" % (retcode, " ".join(args)))
          self.retcode=retcode
          self.args=args
          self.logstr=logstr
          
class ConversionNotSupported(Exception):
     def __init__(self, msg):
          Exception.__init__(self, msg)
          self.msg=msg

class InSafeModeException(Exception):
     def __init__(self):
          Exception.__init__(self, "BitPim is in safe mode - this operation has been blocked")

# generic comms exception and then various specialisations
class CommsException(Exception):
     """Generic commmunications exception"""
     def __init__(self, message, device="<>"):
        Exception.__init__(self, "%s: %s" % (device, message))
        self.device=device
        self.message=message

class CommsNeedConfiguring(CommsException):
     """The communication settings need to be configured"""
     pass

class CommsDeviceNeedsAttention(CommsException):
     """The communication port or device attached to it needs some
     manual intervention"""
     pass

class CommsDataCorruption(CommsException):
     """There was some form of data corruption"""
     pass

class CommsTimeout(CommsException):
    """Timeout while reading or writing the commport"""
    pass

class CommsOpenFailure(CommsException):
    """Failed to open the communications port/device"""
    pass

class CommsWrongPort(CommsException):
     """The wrong port has been selected, typically the modem port on an LG composite device"""
     pass

class AutoPortsFailure(CommsException):
     """Failed to auto detect a useful port"""
     def __init__(self, portstried):
          self.device="auto"
          self.message="Failed to auto-detect the port to use.  "
          if portstried is not None and len(portstried):
               self.message+="I tried "+", ".join(portstried)
          else:
               self.message+="I couldn't detect any candidate ports"
          CommsException.__init__(self, self.message, self.device)

class PhoneStringDecodeException(Exception):
    def __init__(self, string=None, codec=None):
        self.string=string
        self.codec=codec
        Exception.__init__(self, "Unable to decode <%s> using codec <%s>" % (`string`, codec))

class PhoneStringEncodeException(Exception):
    def __init__(self, string=None, codec=None):
        self.string=string
        self.codec=codec
        Exception.__init__(self, "Unable to encode <%s> using codec <%s>" % (`string`, codec))

def datatohexstring(data):
    """Returns a pretty printed hexdump of the data

    @rtype: string"""
    res=cStringIO.StringIO()
    lchar=""
    lhex="00000000 "
    for count in range(0, len(data)):
        b=ord(data[count])
        lhex=lhex+"%02x " % (b,)
        if b>=32 and string.printable.find(chr(b))>=0:
            lchar=lchar+chr(b)
        else:
            lchar=lchar+'.'

        if (count+1)%16==0:
            res.write(lhex+"    "+lchar+"\n")
            lhex="%08x " % (count+1,)
            lchar=""
    if len(data):
        while (count+1)%16!=0:
            count=count+1
            lhex=lhex+"   "
        res.write(lhex+"    "+lchar+"\n")
    return res.getvalue()

def hexify(data):
     "Turns binary data into a hex string (like the output of MD5/SHA hexdigest)"
     return "".join(["%02x" % (ord(x),) for x in data])

def prettyprintdict(dictionary, indent=0):
     """Returns a pretty printed version of the dictionary

     The elements are sorted into alphabetical order, and printed
     one per line.  Dictionaries within the values are also pretty
     printed suitably indented.

     @rtype: string"""

     res=cStringIO.StringIO()

     # the indent string
     istr="  "

     # opening brace
     res.write("%s{\n" % (istr*indent,))
     indent+=1

     # sort the keys
     keys=dictionary.keys()
     keys.sort()

     # print each key
     for k in keys:
          v=dictionary[k]
          # is it a dict
          if isinstance(v, dict):
               res.write("%s%s:\n%s\n" % (istr*indent, `k`, prettyprintdict(v, indent+1)))
          else:
               # is it a list of dicts?
               if isinstance(v, list):
                    dicts=0
                    for item in v:
                         if isinstance(item, dict):
                              dicts+=1
                    if dicts and dicts==len(v):
                         res.write("%s%s:\n%s[\n" % (istr*indent,`k`,istr*(indent+1)))
                         for item in v:
                              res.write(prettyprintdict(item, indent+2))
                         res.write("%s],\n" % (istr*(indent+1)))
                         continue
               res.write("%s%s: %s,\n" % (istr*indent, `k`, `v`))

     # closing brace
     indent-=1
     if indent>0:
          comma=","
     else:
          comma=""
     res.write("%s}%s\n" % (istr*indent,comma))

     return res.getvalue()

     
class exceptionwrap:
     """A debugging assist class that helps in tracking down functions returning exceptions"""
     def __init__(self, callable):
          self.callable=callable
          
     def __call__(self, *args, **kwargs):
          try:

               return self.callable(*args, **kwargs)
          except:
               print "in exception wrapped call", `self.callable`
               print formatexception()
               raise

def unicode_execfile(filename, dict1=0, dict2=0):
     # this version allows the path portion of the filename to 
     # contain non-acsii characters, the filename itself cannot contain
     # ascii characters, execfile does not work if the filename contains
     # non-ascii characters
     curdir=os.getcwdu()
     filepath, file=os.path.split(filename)
     os.chdir(filepath)
     if dict1==0:
        execfile(file)
     elif dict2==0:
        execfile(file, dict1)
     else:
        execfile(file, dict1, dict2)
     os.chdir(curdir)

def readversionedindexfile(filename, dict, versionhandlerfunc, currentversion):
     assert currentversion>0
     try:
         execfile(filename, dict, dict)
     except UnicodeError:
         unicode_execfile(filename, dict, dict)
     if not dict.has_key('FILEVERSION'):
          version=0
     else:
          version=dict['FILEVERSION']
          del dict['FILEVERSION']
     if version<currentversion:
          versionhandlerfunc(dict, version)

def writeversionindexfile(filename, dict, currentversion):
     assert currentversion>0
     with file(filename, 'w') as f:
          for key in dict:
               v=dict[key]
               if isinstance(v, type({})):
                    f.write("result['%s']=%s\n" % (key, prettyprintdict(dict[key])))
               else:
                    f.write("result['%s']=%s\n" % (key, `v`))
          f.write("FILEVERSION=%d\n" % (currentversion,))

def formatexceptioneh(*excinfo):
     print formatexception(excinfo)

def formatexception(excinfo=None, lastframes=8):
     """Pretty print exception, including local variable information.

     See Python Cookbook, recipe 14.4.

     @param excinfo: tuple of information returned from sys.exc_info when
               the exception occurred.  If you don't supply this then
               information about the current exception being handled
               is used
     @param lastframes: local variables are shown for these number of
                  frames
     @return: A pretty printed string
               """
     if excinfo is None:
          excinfo=sys.exc_info()

     s=StringIO.StringIO()
     traceback.print_exception(*excinfo, **{'file': s})
     tb=excinfo[2]

     stack=[]

     while tb:
          stack.append(tb.tb_frame)
          tb=tb.tb_next
          
     if len(stack)>lastframes:
          stack=stack[-lastframes:]
     print >>s, "\nVariables by last %d frames, innermost last" % (lastframes,)
     for frame in stack:
          print >>s, ""
          print >>s, "Frame %s in %s at line %s" % (frame.f_code.co_name,
                                                    frame.f_code.co_filename,
                                                    frame.f_lineno)
          for key,value in frame.f_locals.items():
               # filter out modules
               if type(value)==type(sys):
                    continue
               print >>s,"%15s = " % (key,),
               try:
                    if type(value)==type({}):
                         kk=value.keys()
                         kk.sort()
                         print >>s, "Keys",kk
                         print >>s, "%15s   " % ("",) ,
                    print >>s,`value`[:80]
               except:
                    print >>s,"(Exception occurred printing value)"
     return s.getvalue()
                    
def gettempfilename(extension=None):
    "Returns a filename to be used for a temporary file"
    # safest Python 2.3 method
    if extension:
        x=tempfile.NamedTemporaryFile(suffix="."+extension)
    else:
        x=tempfile.NamedTemporaryFile()
    n=x.name
    x.close()
    del x
    return n

def getfullname(name):
     """Returns the object corresponding to name.
     Imports will be done as necessary to resolve
     every part of the name"""
     mods=name.split('.')
     dict={}
     for i in range(len(mods)):
          # import everything
          try:
               exec "import %s" % (".".join(mods[:i])) in dict, dict
          except:
               pass
     # ok, we should have the name now
     return eval(name, dict, dict)

def list_union(*lists):
     res=[]
     for l in lists:
          for item in l:
               if item not in res:
                    res.append(item)
     return res

def getkv(dict, key, updates=None):
     "Gets a key and value from a dict, returning as a dict potentially applying updates"
     d={key: dict[key].copy()} 
     if updates: 
          d[key].update(updates)
     return d 

# some obfuscation
# obfuscate pwd
_magic=[ord(x) for x in "IamAhaPp12&s]"]

# the oldies are the best
def obfus_encode(str):
    res=[]
    for i in range(len(str)):
        res.append(ord(str[i])^_magic[i%len(_magic)])
    return "".join(["%02x" % (x,) for x in res])

def obfus_decode(str):
    res=[]
    for i in range(0, len(str), 2):
        res.append(int(str[i:i+2], 16))
    x=""
    for i in range(len(res)):
        x+=chr(res[i]^_magic[i%len(_magic)])
    return x

# unicode byte order markers to codecs
# this really should be part of the standard library

# we try to import the encoding first.  that has the side
# effect of ensuring that the freeze tools pick up the
# right bits of code as well
import codecs

_boms=[]
# 64 bit 
try:
     import encodings.utf_64
     _boms.append( (codecs.BOM64_BE, "utf_64") )
     _boms.append( (codecs.BOM64_LE, "utf_64") )
except:  pass

# 32 bit
try:
     import encodings.utf_32
     _boms.append( (codecs.BOM_UTF32, "utf_32") )
     _boms.append( (codecs.BOM_UTF32_BE, "utf_32") )
     _boms.append( (codecs.BOM_UTF32_LE, "utf_32") )
except:  pass

# 16 bit
try:
     import encodings.utf_16
     _boms.append( (codecs.BOM_UTF16, "utf_16") )
     _boms.append( (codecs.BOM_UTF16_BE, "utf_16_be") )
     _boms.append( (codecs.BOM_UTF16_LE, "utf_16_le") )
except:  pass

# 8 bit
try:
     import encodings.utf_8
     _boms.append( (codecs.BOM_UTF8, "utf_8") )
except: pass

# Work arounds for the idiots at Apple that decided not to even
# include BOMs
_boms.append( ("\0B\0E\0G\0I\0N\0:\0V\0C\0A\0R\0D", "utf_16_be") )
_boms.append( ("B\0E\0G\0I\0N\0:\0V\0C\0A\0R\0D\0", "utf_16_le") )


# NB: the 32 bit and 64 bit versions have the BOM constants defined in Py 2.3
# but no corresponding encodings module.  They are here for completeness.
# The order of above also matters since the first ones have longer
# boms than the latter ones, and we need to be unambiguous

_maxbomlen=max([len(bom) for bom,codec in _boms])

def opentextfile(name):
     """This function detects unicode byte order markers and if present
     uses the codecs module instead to open the file instead with
     appropriate unicode decoding, else returns the file using standard
     open function"""
     with file(name, 'rb') as f:
          start=f.read(_maxbomlen)
          for bom,codec in _boms:
               if start.startswith(bom):
                    # some codecs don't do readline, so we have to vector via stringio
                    # many postings also claim that the BOM is returned as the first
                    # character but that hasn't been the case in my testing
                    return StringIO.StringIO(codecs.open(name, "r", codec).read())
     return file(name, "rtU")


# don't you just love i18n

# the following function is actually defined in guihelper and
# inserted into this module.  the intention is to ensure this
# module doesn't have to import wx.  The guihelper version
# checks if wx is in unicode mode

#def strorunicode(s):
#     if isinstance(s, unicode): return s
#     return str(s)

def forceascii(s):
     return get_ascii_string(s, 'replace')

# The CRC and escaping mechanisms are the same as used in PPP, HDLC and
# various other standards.

pppterminator="\x7e"

def pppescape(data):
    return data.replace("\x7d", "\x7d\x5d") \
           .replace("\x7e", "\x7d\x5e")

def pppunescape(d):
    if d.find("\x7d")<0: return d
    res=list(d)
    try:
        start=0
        while True:
            p=res.index("\x7d", start)
            res[p:p+2]=chr(ord(res[p+1])^0x20)
            start=p+1
    except ValueError:
        return "".join(res)

# See http://www.repairfaq.org/filipg/LINK/F_crc_v35.html for more info
# on CRC
_crctable=(
    0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf,   # 0 - 7
    0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7,   # 8 - 15
    0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e,   # 16 - 23
    0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876,   # 24 - 31
    0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd,   # 32 - 39
    0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5,   # 40 - 47
    0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c,   # 48 - 55
    0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974,   # 56 - 63
    0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb,   # 64 - 71
    0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3,   # 72 - 79
    0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a,   # 80 - 87
    0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72,   # 88 - 95
    0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9,   # 96 - 103
    0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1,   # 104 - 111
    0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738,   # 112 - 119
    0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70,   # 120 - 127
    0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7,   # 128 - 135
    0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff,   # 136 - 143
    0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036,   # 144 - 151
    0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e,   # 152 - 159
    0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5,   # 160 - 167
    0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd,   # 168 - 175
    0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134,   # 176 - 183
    0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c,   # 184 - 191
    0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3,   # 192 - 199
    0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb,   # 200 - 207
    0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232,   # 208 - 215
    0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a,   # 216 - 223
    0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1,   # 224 - 231
    0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9,   # 232 - 239
    0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330,   # 240 - 247
    0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78,   # 248 - 255
    )

def crc(data, initial=0xffff):
    "CRC calculation - returns 16 bit integer"
    res=initial
    for byte in data:
        curres=res
        res=res>>8  # zero extended
        val=(ord(byte)^curres) & 0xff
        val=_crctable[val]
        res=res^val

    res=(~res)&0xffff
    return res

def crcs(data, initial=0xffff):
    "CRC calculation - returns 2 byte string LSB"
    r=crc(data, initial)
    return "%c%c" % ( r& 0xff, (r>>8)&0xff)



###
### Pathname processing (independent of host OS)
###

def basename(name):
    if name.rfind('\\')>=0 or name.rfind('/')>=0:
        pos=max(name.rfind('\\'), name.rfind('/'))
        name=name[pos+1:]
    return name

def dirname(name):
    if name.rfind('\\')>=0 or name.rfind('/')>=0:
        pos=max(name.rfind('\\'), name.rfind('/'))
        name=name[:pos]
    return name

def stripext(name):
    if name.rfind('.')>=0:
        name=name[:name.rfind('.')]
    return name

def getext(name):
    if name.rfind('.')>=0:
        return name[name.rfind('.')+1:]
    return ''

#-------------------------------------------------------------------------------
# number <-> string conversion routines

def LSBUint16(v):
    if len(v)<2:
        return None
    return ord(v[0])+(ord(v[1])<<8)

def LSBUint32(v):
    if len(v)<4:
        return None
    return ord(v[0])+(ord(v[1])<<8)+(ord(v[2])<<16)+(ord(v[3])<<24)
    
def MSBUint16(v):
    if len(v)<2:
        return None
    return ord(v[1])+(ord(v[0])<<8)

def MSBUint32(v):
    if len(v)<4:
        return None
    return ord(v[3])+(ord(v[2])<<8)+(ord(v[1])<<16)+(ord(v[0])<<24)

def LSBstr16(v):
    return chr(v&0xff)+chr((v>>8)&0xff)

def LSBstr32(v):
    return chr(v&0xff)+chr((v>>8)&0xff)+chr((v>>16)&0xff)+chr((v>>24)&0xff)

def MSBstr16(v):
    return chr((v>>8)&0xff)+chr(v&0xff)

def MSBstr32(v):
    return chr((v>>24)&0xff)+chr((v>>16)&0xff)+chr((v>>8)&0xff)+chr(v&0xff)


###
### Binary handling
###

nibbles=("0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111", "1000", "1001", "1010", "1011", "1100", "1101", "1110", "1111")

def tobinary(v):
     return nibbles[v>>4]+nibbles[v&0x0f]

def frombinary(v):
     res=0
     for i in v:
          res*=2
          res+=bool(i=="1")
     return res

# This could be done more efficiently through clever combinations of
# masks and shifts but it is harder to write and debug (I tried :-)
# and isn't any more effective on the short strings we work with
def decodecharacterbits(bytes, bitsperchar, charconv=chr, terminator=None):
     """Decodes the characters out of a string of bytes where each
     character takes a fixed number of bits (eg 7)

     @param bytes: atring containing the raw bytes
     @param bitsperchar: number of bits making up each character
     @param charconv: the function used to convert the integer value
                 into a character
     @param terminator: if this character is seen then it and the remaining bits are ignored"""
     bits="".join([tobinary(ord(c)) for c in bytes])
     value=[]
     while len(bits):
            c=charconv(frombinary(bits[:bitsperchar]))
            if c==terminator:
                break
            value.append(c)
            bits=bits[bitsperchar:]
     return "".join(value)
  

def encode_with_degrade(uni_string, codec='ascii', error_handling='strict'):

    temp_str=''
    if uni_string is None:
        return temp_str
    try:
        temp_str=uni_string.encode(codec)
        return temp_str
    except UnicodeError:
        pass # we'll have another go with dumbing down    
    
    temp_str=''
    if codec=='ascii':
        temp_str=get_ascii_string(uni_string, error_handling)
    else:
        # go through all characters dumbing down the ones we cannot convert
        # we could do all at once but we only want to degrade characters the encoding
        # does not support
        for i in range(len(uni_string)):
            try:
                temp_char=uni_string[i].encode(codec)
            except UnicodeError:
                temp_char=get_ascii_string(uni_string[i], error_handling)
            temp_str+=temp_char
    return temp_str
        
def get_ascii_string(uni_string, error_handling='strict'):
    "converts any type into an ascii byte string, for unicode string it will degrade if possible"
    if uni_string is None:
        return None
    if not isinstance(uni_string, (str, unicode)):
        # convert numbers into strings
        return str(uni_string)
    if not isinstance(uni_string, unicode):
        # we are already a byte string!
        return uni_string

    # normalise the string
    kd_str=unicodedata.normalize('NFKD', uni_string)
    stripped_str=u''
    # go through removing all accoutrements from the character and convert some other characters
    # defined by unicode standard ver. 3.2.0
    replace_chars= {
        u"\N{COMBINING GRAVE ACCENT}": u"",
        u"\N{COMBINING ACUTE ACCENT}": u"",
        u"\N{COMBINING CIRCUMFLEX ACCENT}": u"",
        u"\N{COMBINING TILDE}": u"",
        u"\N{COMBINING MACRON}": u"",
        u"\N{COMBINING OVERLINE}": u"",
        u"\N{COMBINING BREVE}": u"",
        u"\N{COMBINING DOT ABOVE}": u"",
        u"\N{COMBINING DIAERESIS}": u"",
        u"\N{COMBINING HOOK ABOVE}": u"",
        u"\N{COMBINING RING ABOVE}": u"",
        u"\N{COMBINING DOUBLE ACUTE ACCENT}": u"",
        u"\N{COMBINING CARON}": u"",
        u"\N{COMBINING VERTICAL LINE ABOVE}": u"",
        u"\N{COMBINING DOUBLE VERTICAL LINE ABOVE}": u"",
        u"\N{COMBINING DOUBLE GRAVE ACCENT}": u"",
        u"\N{COMBINING CANDRABINDU}": u"",
        u"\N{COMBINING INVERTED BREVE}": u"",
        u"\N{COMBINING TURNED COMMA ABOVE}": u"",
        u"\N{COMBINING COMMA ABOVE}": u"",
        u"\N{COMBINING REVERSED COMMA ABOVE}": u"",
        u"\N{COMBINING COMMA ABOVE RIGHT}": u"",
        u"\N{COMBINING GRAVE ACCENT BELOW}": u"",
        u"\N{COMBINING ACUTE ACCENT BELOW}": u"",
        u"\N{COMBINING LEFT TACK BELOW}": u"",
        u"\N{COMBINING RIGHT TACK BELOW}": u"",
        u"\N{COMBINING LEFT ANGLE ABOVE}": u"",
        u"\N{COMBINING HORN}": u"",
        u"\N{COMBINING LEFT HALF RING BELOW}": u"",
        u"\N{COMBINING UP TACK BELOW}": u"",
        u"\N{COMBINING DOWN TACK BELOW}": u"",
        u"\N{COMBINING PLUS SIGN BELOW}": u"",
        u"\N{COMBINING MINUS SIGN BELOW}": u"",
        u"\N{COMBINING PALATALIZED HOOK BELOW}": u"",
        u"\N{COMBINING RETROFLEX HOOK BELOW}": u"",
        u"\N{COMBINING DOT BELOW}": u"",
        u"\N{COMBINING DIAERESIS BELOW}": u"",
        u"\N{COMBINING RING BELOW}": u"",
        u"\N{COMBINING COMMA BELOW}": u"",
        u"\N{COMBINING CEDILLA}": u"",
        u"\N{COMBINING OGONEK}": u"",
        u"\N{COMBINING VERTICAL LINE BELOW}": u"",
        u"\N{COMBINING BRIDGE BELOW}": u"",
        u"\N{COMBINING INVERTED DOUBLE ARCH BELOW}": u"",
        u"\N{COMBINING CARON BELOW}": u"",
        u"\N{COMBINING CIRCUMFLEX ACCENT BELOW}": u"",
        u"\N{COMBINING BREVE BELOW}": u"",
        u"\N{COMBINING INVERTED BREVE BELOW}": u"",
        u"\N{COMBINING TILDE BELOW}": u"",
        u"\N{COMBINING MACRON BELOW}": u"",
        u"\N{COMBINING LOW LINE}": u"",
        u"\N{COMBINING DOUBLE LOW LINE}": u"",
        u"\N{COMBINING TILDE OVERLAY}": u"",
        u"\N{COMBINING SHORT STROKE OVERLAY}": u"",
        u"\N{COMBINING LONG STROKE OVERLAY}": u"",
        u"\N{COMBINING SHORT SOLIDUS OVERLAY}": u"",
        u"\N{COMBINING LONG SOLIDUS OVERLAY}": u"",
        u"\N{COMBINING RIGHT HALF RING BELOW}": u"",
        u"\N{COMBINING INVERTED BRIDGE BELOW}": u"",
        u"\N{COMBINING SQUARE BELOW}": u"",
        u"\N{COMBINING SEAGULL BELOW}": u"",
        u"\N{COMBINING X ABOVE}": u"",
        u"\N{COMBINING VERTICAL TILDE}": u"",
        u"\N{COMBINING DOUBLE OVERLINE}": u"",
        u"\N{COMBINING GRAVE TONE MARK}": u"",
        u"\N{COMBINING ACUTE TONE MARK}": u"",
        u"\N{COMBINING GREEK PERISPOMENI}": u"",
        u"\N{COMBINING GREEK KORONIS}": u"",
        u"\N{COMBINING GREEK DIALYTIKA TONOS}": u"",
        u"\N{COMBINING GREEK YPOGEGRAMMENI}": u"",
        u"\N{COMBINING BRIDGE ABOVE}": u"",
        u"\N{COMBINING EQUALS SIGN BELOW}": u"",
        u"\N{COMBINING DOUBLE VERTICAL LINE BELOW}": u"",
        u"\N{COMBINING LEFT ANGLE BELOW}": u"",
        u"\N{COMBINING NOT TILDE ABOVE}": u"",
        u"\N{COMBINING HOMOTHETIC ABOVE}": u"",
        u"\N{COMBINING ALMOST EQUAL TO ABOVE}": u"",
        u"\N{COMBINING LEFT RIGHT ARROW BELOW}": u"",
        u"\N{COMBINING UPWARDS ARROW BELOW}": u"",
        u"\N{COMBINING GRAPHEME JOINER}": u"",
        u'\N{BROKEN BAR}': '|',
        u'\N{CENT SIGN}': 'c',
        u'\N{COPYRIGHT SIGN}': '(C)',
        u'\N{DIVISION SIGN}': '/',
        u'\N{INVERTED EXCLAMATION MARK}': '!',
        u'\N{INVERTED QUESTION MARK}': '?',
        u'\N{LATIN CAPITAL LETTER AE}': 'Ae',
        u'\N{LATIN CAPITAL LETTER ETH}': 'Th',
        u'\N{LATIN CAPITAL LETTER THORN}': 'Th',
        u'\N{LATIN SMALL LETTER AE}': 'ae',
        u'\N{LATIN SMALL LETTER ETH}': 'th',
        u'\N{LATIN SMALL LETTER SHARP S}': 'ss',
        u'\N{LATIN SMALL LETTER THORN}': 'th',
        u'\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}': '<<',
        u'\N{MIDDLE DOT}': '*',
        u'\N{MULTIPLICATION SIGN}': '*',
        u'\N{PLUS-MINUS SIGN}': '+/-',
        u'\N{REGISTERED SIGN}': '(R)',
        u'\N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}': '>>',
        u'\N{SOFT HYPHEN}': '-',
        u'\N{VULGAR FRACTION ONE HALF}': '1/2',
        u'\N{VULGAR FRACTION ONE QUARTER}': '1/4',
        u'\N{VULGAR FRACTION THREE QUARTERS}': '3/4',
        }
    for i in range(len(kd_str)):
        if kd_str[i] in replace_chars:
            stripped_str+=replace_chars[kd_str[i]]
        else:
            stripped_str+=kd_str[i]
    # now we have removed all the stuff we can try converting
    # error handling is managed by the calling routine
    temp_str=stripped_str.encode('ascii', error_handling)
    return temp_str

###
### Cache information against a file
###

def statinfo(filename):
    """Returns a simplified version of os.stat results that can be used to tell if a file
    has changed.  The normal structure returned also has things like last access time
    which should not be used to tell if a file has changed."""
    try:
        s=os.stat(filename)
        return (s.st_mode, s.st_ino, s.st_dev, s.st_uid, s.st_gid, s.st_size, s.st_mtime,
                s.st_ctime)
    except:
        return None

class FileCache:

     def __init__(self, lowwater=100, hiwater=140):
          self.items={}
          self.hiwater=hiwater
          self.lowwater=lowwater

     def get(self, filename):
          v=self.items.get(filename, None)
          if v is None: return None
          si,value=v
          # check freshness
          if si==statinfo(filename):
               return value
          return None

     def set(self, filename, value):
          # we deliberately return value make this easy to use in return statement
          if len(self.items)>=self.hiwater:
               while len(self.items)>self.lowwater:
                    del self.items[random.choice(self.items.keys())]
          # yes there is a race condition with statinfo changing after program
          # has calculated value but before calling this function
          self.items[filename]=statinfo(filename),value
          return value

# wrapper for __import__
def importas(name):
    return __import__(name, globals(), locals(),
                      [name.split('.')[-1]])

# http://starship.python.net/crew/theller/moin.cgi/HowToDetermineIfRunningFromExe
def main_is_frozen():
    """ Return T if running from an exe, F otherwise
    """
    return (hasattr(sys, "frozen")  # new py2exe
           or hasattr(sys, "importers") # old py2exe
           or imp.is_frozen("__main__") # tools/freeze
            or os.path.isfile(sys.path[0])) # cxfreeze

def get_main_dir():
    """Return the absoluate path of the main BitPim dir
    """
    if main_is_frozen():
        if sys.platform!='win32':
             p=sys.path[0]
             if os.path.isfile(p):
                  p=os.path.dirname(p)
             return p
        # windows running from exe, return as is
        return os.path.abspath(os.path.dirname(sys.executable))
    # running from src, up one
    return os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))[0]

if sys.platform=='win32':
    # From Tim Golden's Win32 How Do I ...?
    from win32api import GetFileVersionInfo, LOWORD, HIWORD
    def get_version_number (filename):
        """Return the version of a Windows DLL or EXE file
        """
        try:
            info = GetFileVersionInfo (filename, "\\")
            ms = info['FileVersionMS']
            ls = info['FileVersionLS']
            return HIWORD (ms), LOWORD (ms), HIWORD (ls), LOWORD (ls)
        except:
            return None

# simple generator that generates temp file name and del it afterward
@contextmanager
def usetempfile(ext):
    _name=gettempfilename(ext)
    try:
        yield _name
    finally:
          try:
              os.remove(_name)
          except OSError:
               # ignore if failed to del temp file
               pass
