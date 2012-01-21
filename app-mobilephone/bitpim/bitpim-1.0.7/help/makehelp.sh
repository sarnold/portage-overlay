#!/bin/bash

# This should only run on Windows since we also need to build CHM files
# although in theory it could run against the Linux and Mac versions
# of helpblocks

# These are what all the control files are
#
# HHP   project file (MS Html Help workshop)
# HHC   table of contents file
# HHK   index
# WXH   project file (HelpBlocks) XML

# windows fudge
PATH=/usr/bin:$PATH

if [ "$(uname -o)" = "Cygwin" ]
then
    cygwin=true
else
    cygwin=false
fi

PYTHON=python
HBDIR="/c/program files/helpblocks"
if $cygwin
then
    HBDIR="/cygdrive"$HBDIR
fi

# version info for helpblocks pre-processor
$PYTHON src/version.py > help/version.h
# phone features info
PYTHONPATH=src $PYTHON -O help/phone_features.py > help/phonesupporttable

# update web tree of docs
cd help
$PYTHON contentsme.py bitpim.hhc

# remove old files
rm -f *.htm bitpim.chm bitpim.htb ../resources/bitpim.chm ../resources/bitpim.htb

# Run helpblocks
echo "Building the help files using HelpBlocks..."
"$HBDIR"/helpblocks --rebuild --chm --wxhtml bitpim.wxh

echo "generate various ids"
# generate various ids
$PYTHON genids.py bitpim_alias.h ../src/helpids.py
cp bitpim.htb bitpim.chm ../resources

# did anyone forget to rename files?
if [ `grep doc- bitpim.hhp | wc -l` -gt 0 ]
then
     echo "You forgot to rename some files"
     grep doc- bitpim.hhp
     exit 1
fi

cd ..

# copy into website
if [ -d ../website/site/.svn ]
then
    echo "Copying help into web site tree"
    webhelp="../website/site/help"
    rm -rf "$webhelp"
    mkdir -p "$webhelp"
    $PYTHON ../website/hb2web/hb2web.py --colour "#99ffcc" help/bitpim.htb "$webhelp"
    rm -rf "$webhelp/../testhelp"
fi
