#!/usr/bin/env python
### BITPIM
###
### Copyright (C) 2003-2006 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: version.py 4315 2007-07-23 01:03:58Z djpham $

"""Information about BitPim version number"""

# We'd like to record information in this file, but without subversion
# considering the file modified.  This is done by placing the information
# in the dollar id fields.  When freeze is run, it does those various
# substitutions

__FROZEN__="$Id: version.py 4315 2007-07-23 01:03:58Z djpham $"

import os, sys
import time

name="BitPim"
vendor="$Id: version.py 4315 2007-07-23 01:03:58Z djpham $"
release=0  # when rereleases of the same version happen, this gets incremented
contact="The BitPim home page is at http://www.bitpim.org.  You can post any " \
         "questions or feedback to the mailing list detailed on that page." # where users are sent to contact with feedback

# user defined version
userdefined=False
userversion=""
uservendor=""

svnrevision=0  # we don't know
# were we frozen?
f=__FROZEN__.split()
if len(f)==3: # we were - calc svnrevision
    svnrevision=int(f[1])

# fixup vendor
if vendor[1:].startswith("Id:"):
    if len(vendor.split())>3:
        vendor=""
    else:
        vendor=vendor.split()[1]

_headurl="$HeadURL: https://bitpim.svn.sourceforge.net/svnroot/bitpim/releases/1.0.7/src/version.py $".split()[1]
# work out our version number
_rp="https://bitpim.svn.sourceforge.net/svnroot/bitpim/releases/"

if userdefined:
    def isdevelopmentversion(): return True
    version=userversion
    vendor=uservendor
elif _headurl.startswith(_rp):
    def isdevelopmentversion(): return False
    version=_headurl[len(_rp):].split("/")[0]
    if not vendor:
        vendor="official"
else:
    def isdevelopmentversion(): return True
    prefix="https://bitpim.svn.sourceforge.net/svnroot/bitpim/"
    version="-".join(_headurl[len(prefix):].split("/")[:-2]) # -2 to prune off src/version.py
    del prefix
    # were we frozen?
    if svnrevision:
        version=version+"-"+`svnrevision`
    if not vendor:
        vendor="developer build"

del _headurl
del _rp

versionstring=version

if release>0:
    versionstring+="-"+`release`

if not isdevelopmentversion():
    # dotted quad version as used on Windows (a.b.c.d where all must be digits only)
    # we use major.minor.point.last
    dqver=[int(x) for x in version.split(".")]
    while len(dqver)<3:
        dqver.append(0)
    while len(dqver)<4:
        dqver.append(svnrevision)
    dqver=dqver[:4]
else:
    dqver=[0,0,0,svnrevision] # svnrevision will be zero if we weren't frozen

dqverstr=".".join([`x` for x in dqver])

del x

url="http://www.bitpim.org"

description="BitPim "+versionstring
copyright="(C) 2003-2006 Roger Binns and others - see http://www.bitpim.org"

def setversion(versionstring, vendorstring='Test'):
    """Set the version and vendor based on user's input"""
    # my filename
    myfilename=os.path.splitext(__file__)[0]+".py"
    # update with new version and vendor
    result=[]
    if versionstring:
        # user specifies a version
        _versionflg='True'
        _version=versionstring
        _vendor=vendorstring
    else:
        _versionflg='False'
        _version=_vendor=''
    for line in file(myfilename, "rtU"):
        if line.startswith('userversion'):
            line='userversion="%s"\n'%_version
        elif line.startswith('uservendor'):
            line='uservendor="%s"\n'%_vendor
        elif line.startswith('userdefined'):
            line='userdefined=%s\n'%_versionflg
        result.append(line)
    file(myfilename, "wt").write("".join(result))
    # python doesn't check .pyc/.pyo files correctly so we proactively delete them
    for ext in (".pyc", ".pyo"):
        try:
            os.remove(os.path.splitext(__file__)[0]+ext)
        except OSError:
            pass

def __freeze():
    # my filename
    myfilename=os.path.splitext(__file__)[0]+".py"

    # modify the frozen field with the current revision number
    print "Freezing version"
    svnver=os.popen("svnversion -n .", "r").read()
    if len(svnver)<4:
        print "svnversion command doesn't appear to be working."
        sys.exit(3)
    try:
        # temporary - remove following line once code works
        if svnver[-1]=='M': svnver=svnver[:-1]
        [int(x) for x in svnver.split(":")]
    except:
        print "Your tree isn't pure. Do you have files not checked in (M)?"
        print svnver,"was returned by svnversion"
        sys.exit(4)
    svnver=svnver.split(":")[-1]
    print "Embedding svnrevision",svnver,"into",myfilename
    result=[]
    for line in open(myfilename, "rtU"):
        if line.startswith('__FROZEN__="$Id:'):
            line='__FROZEN__="$%s %s $"\n' % ("Id:", svnver)
        result.append(line)

    open(myfilename, "wt").write("".join(result))
    # python doesn't check .pyc/.pyo files correctly so we proactively delete them
    for ext in (".pyc", ".pyo"):
        try:
            os.remove(os.path.splitext(__file__)[0]+ext)
        except OSError:
            pass

if __name__=='__main__':
    import sys
    if len(sys.argv)==1:
        # generated for the benefit of the help
        # purposely missing " around values
        print "#define VERSION", versionstring
        print "#define DATENOW", time.strftime("%d %B %Y")
    elif sys.argv[1]=="freeze":
        __freeze()
    else:
        print "Unknown arguments",sys.argv[1:]
