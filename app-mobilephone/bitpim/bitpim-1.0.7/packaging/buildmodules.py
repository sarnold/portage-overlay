#!/usr/bin/env python
#
# Build our various dependencies.  This is an alternative to a top
# level Makefile

import sys
import os
import shutil
import glob

topdir=os.getcwd()

ALL=["usb", "strings", "bmp2avi"]

args=sys.argv[1:] if __name__=='__main__' else []
if len(args)==1 and args[0]=="all":
    args=ALL
elif len(args)==0:
    args=["usb", "strings"] # default

for v in args:
    if v not in ALL:
        print "Unknown part",v," - valid parts are",ALL
        sys.exit(1)

# fixup
sys.path=['']+sys.path

def run(cmd):
    print cmd
    res=os.system(cmd)
    if res!=0:
        raise Exception("Command failed with code "+`res`)

if "usb" in args:
    # USB
    print "===== src/native/usb"
    if sys.platform in ('darwin', 'linux2'):
        os.chdir("src/native/usb")
        if os.path.exists("_libusb.so"):
            os.remove("_libusb.so")
        if sys.platform=='darwin':
            run("sh -x ./macbuild.sh")
        else:
            run("sh -x ./build.sh")
        assert os.path.exists("_libusb.so")
        os.chdir(topdir)

if "strings" in args:
    # JARO WINKLER STRINGS
    print "===== src/native/strings"
    os.chdir("src/native/strings")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if sys.platform=='win32':
        fname='jarow.pyd'
    else:
        fname='jarow.so'
    if os.path.exists(fname):
        os.remove(fname)
    sys.argv=[sys.argv[0]]+['build']
    if sys.platform=='win32':
        sys.argv.append("--compiler=mingw32")
    import setup
    shutil.copy2(glob.glob("build/*/"+fname)[0], '.')
    os.chdir(topdir)

if "bmp2avi" in args:
    # BMP2AVI convertor
    print "==== src/native/av/bmp2avi"
    fname={'linux2': 'bmp2avi.lbin',
           'darwin': 'bmp2avi.mbin',
           'win32':  'bmp2avi.exe'}[sys.platform]
    if os.path.exists(os.path.join("helpers", fname)):
        os.remove(os.path.join("helpers", fname))
    os.chdir("src/native/av/bmp2avi")
    if os.path.exists(fname):
        os.remove(fname)
    if sys.byteorder!="little":
        run("make EXTRADEFINES=-D__BIG_ENDIAN__ "+fname)
    else:
        run("make "+fname)
    shutil.copy2(fname, os.path.join(topdir, "helpers", fname))
    os.chdir(topdir)
