### BITPIM
###
### Copyright (C) 2003-2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: phone_media_codec.py 2369 2005-05-10 05:56:14Z djpham $

"""
Codec for converting phone media file names to local file names.
"""

# standard modules
import codecs

# wx modules
import wx

# BitPim modules

escape_char='%'
bad_chars={
    '__WXMSW__': (escape_char, '/', '\\', '[', ']', '?', '*', ':',
                  '"', '<', '>', '|', '=', ';'),
    '__WXMAC__': (escape_char, '/', ':'),
    '__WXGTK__': (escape_char, '/') }
def phone_media_encode(input, errors='ignore'):
    """ Encodes the phone media file name into local storage file name
    """
    assert errors=='ignore'
    l=[]
    for c in input:
        ord_c=ord(c)
        if ord_c<32 or ord_c>127 or \
           c in bad_chars.get(wx.Platform, ()):
            l+=hex(ord_c).replace('0x', escape_char)
        else:
            l+=c
    return (str(''.join(l)), len(input))

def phone_media_decode(input, errors='ignore'):
    """ Decodes local system file name to phone media file name
    """
    assert errors=='ignore'
    l=[]
    esc_str=''
    for c in input:
        if c==escape_char:
            # starting the escape sequence
            if len(esc_str):
                # current escape sequence is broken, ignore
                l+=esc_str
            esc_str=c
        elif len(esc_str):
            # in an esc sequence
            esc_str+=c
            if len(esc_str)==3:
                # got an %xx -> attempt to decode
                try:
                    h=int(esc_str[1:], 16)
                    l+=chr(h)
                except:
                    # broken esc sequence, ignore
                    l+=esc_str
                esc_str=''
        else:
            l+=c
    return (''.join(l), len(input))

class Codec(codecs.Codec):

    def encode(self, input,errors='strict'):
        return phone_media_encode(input,errors)
    def decode(self, input,errors='strict'):
        return phone_media_decode(input,errors)

class StreamWriter(Codec,codecs.StreamWriter):
    pass

class StreamReader(Codec,codecs.StreamReader):
    pass

### encodings module API
codec_name='phone_media'
def search_func(name):
    if name==codec_name:
        return (phone_media_encode, phone_media_decode,
                StreamReader, StreamWriter)
