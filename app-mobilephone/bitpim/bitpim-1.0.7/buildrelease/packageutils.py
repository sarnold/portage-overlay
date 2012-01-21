#!/usr/bin/env python
### BITPIM
###
### Copyright (C) 2006 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: packageutils.py 3754 2006-12-07 09:48:11Z rogerb $

# Various functions to help with packaging

import xml.dom.minidom 
import os
import shutil

def copysvndir(srcdir, destinationdir, filterfunc=None):
    """Copy files from srcdir to destinationdir that are listed in Subversion.

    You can supply a filterfunc which will be called with each source
    and destination filename.  Return (srcfname, destfname) from that
    function or None.  You can use this to filter out content or
    change where it comes from or goes to."""

    metadata=xml.dom.minidom.parseString(os.popen("svn info -R --xml \"%s\"" % (srcdir,), "r").read())

    for entry in metadata.documentElement.getElementsByTagName("entry"):
        kind=entry.getAttribute("kind")
        name=entry.getAttribute("path")[len(srcdir):].lstrip("\\/")
        if name=="": # directory itself
            continue
        if kind=="dir":
            # ::TODO:: deal with these - need to make output directory as well
            assert False
            continue
        if kind!="file":
            # how do i deal with these?
            assert False
            continue
        src=os.path.join(srcdir, name)
        dest=os.path.join(destinationdir, name)
        if filterfunc:
            res=filterfunc(src, dest)
            if res is None:
                continue
            src,dest=res
        if not os.path.isdir(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        print dest
        shutil.copy2(src, dest)
