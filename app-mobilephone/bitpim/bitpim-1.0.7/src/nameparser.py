### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: nameparser.py 3632 2006-10-27 03:08:31Z djpham $

"""Various routines that deal with names"""

def formatfullname(name):
    """Returns a string of the name, including all fields that are present"""

    res=""
    full=name.get("full", "")
    fml=' '.join([x for x in getparts(name) if x])

    if len(fml) or len(full):
        # are they the same
        if fml==full:
            res+=full
        else:
            # different
            if len(full):
                res+=full
            if len(fml):
                if len(res):
                    res+=" | "
                res+=fml

    if name.has_key("nickname"):
        res+=" ("+name["nickname"]+")"
    return res

def formatsimplename(name):
    "like L{formatname}, except we use the first matching component"
    _fullname=getfullname(name)
    if _fullname:
        return _fullname
    return name.get('nickname', "")

def formatsimplefirstlast(name):
    "Returns the name formatted as First Middle Last"
    return ' '.join([x for x in getparts(name) if x])
def formatsimplelastfirst(name):
    "Returns the name formatted as Last, First Middle"
    f,m,l=getparts(name)
    if len(l):
        if len(f+m):
            return l+", "+" ".join([f,m])
        return l
    return " ".join([f,m])

def getfullname(name):
    """Gets the full name, joining the first/middle/last if necessary"""
    if name.has_key("full"):
        return name["full"]
    return ' '.join([x for x in getparts(name) if x])

# See the following references for name parsing and how little fun it
# is.
#
# The simple way:
# http://cvs.gnome.org/lxr/source/evolution-data-server/addressbook/libebook/
# e-name-western*
#
# The "proper" way:
# http://cvs.xemacs.org/viewcvs.cgi/XEmacs/packages/xemacs-packages/mail-lib/mail-extr.el
#
# How we do it
#
#  [1] The name is split into white-space seperated parts
#  [2] If there is only one part, it becomes the firstname
#  [3] If there are only two parts, they become first name and surname
#  [4] For three or more parts, the first part is the first name and the last
#      part is the surname.  Then while the last part of the remainder starts with
#      a lower case letter or is in the list below, it is prepended to the surname.
#      Whatever is left becomes the middle name.

lastparts= [ "van", "von", "de", "di" ]

# I would also like to proudly point out that this code has no comment saying
# "Have I no shame".  It will be considered incomplete until that happens

def _getparts_FML(name):
    n=name.get("full")
    
    # [1]
    parts=n.split()

    # [2]
    if len(parts)<=1:
        return (n, "", "")
    
    # [3]
    if len(parts)==2:
        return (parts[0], "", parts[1])

    # [4]
    f=[parts[0]]
    m=[]
    l=[parts[-1]]
    del parts[0]
    del parts[-1]
    while len(parts) and (parts[-1][0].lower()==parts[-1][0] or parts[-1].lower() in lastparts):
        l=[parts[-1]]+l
        del parts[-1]
    m=parts

    # return it all
    return (" ".join(f), " ".join(m), " ".join(l))

def _getparts_LFM(name):
    n=name.get("full")
    
    parts=n.split(',')

    if len(parts)<=1:
        return (n, '', '')
    
    _last=parts[0]
    _first=''
    _middle=''
    parts=parts[1].split()
    if len(parts)>=1:
        _first=parts[0]
        if len(parts)>1:
            _middle=' '.join(parts[1:])
    return (_first, _middle, _last)
    
def getparts(name):
    """Returns (first, middle, last) for name.  If the part doesn't exist
    then a blank string is returned"""

    # do we have any of the parts?
    for i in ("first", "middle", "last"):
        if name.has_key(i):
            return (name.get("first", ""), name.get("middle", ""), name.get("last", ""))

    # check we have full.  if not return nickname
    if not name.has_key("full"):
        return (name.get("nickname", ""), "", "")

    n=name.get("full")
    if ',' in n:
        return _getparts_LFM(name)
    return _getparts_FML(name)

# convenience functions

def getfirst(name):
    return getparts(name)[0]

def getmiddle(name):
    return getparts(name)[1]

def getlast(name):
    return getparts(name)[2]
