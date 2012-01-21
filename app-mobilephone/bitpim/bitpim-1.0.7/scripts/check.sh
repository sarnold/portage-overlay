#!/bin/sh

# $Id: check.sh 4705 2008-09-01 20:56:04Z djpham $

# This script does various checks on the source code
# including epydoc and pychecker

if [ "$(uname -o)" = "Cygwin" ]
then
    cygwin=true
else
    cygwin=false
fi

EPYDOC=epydoc
PYCHECKERARGS="--only --limit 10000"
PYCHECKER="pychecker $PYCHECKERARGS"
PYXRDIR=
PYTHON=python # will probably want this to be python2.5 on rh9

case $MACHTYPE in
    *-msys ) # windows machine
        EPYDOC="python /c/python25/scripts/epydoc.py"
        PYCHECKER="python /c/python25/lib/site-packages/pychecker/checker.py $PYCHECKERARGS pychecker"
	PYXRDIR="/c/bin/pyxr"
	PATH="/usr/bin:$PATH"  # msys is usually not on path!
    ;;
    # other platforms fill in here
esac

if $cygwin
then
    EPYDOC="python $(cygpath -w /cygdrive/c/python25/scripts/epydoc.py)"
    PYCHECKER="python $(cygpath -w /cygdrive/c/python25/lib/site-packages/pychecker/checker.py) $PYCHECKERARGS pychecker"
    PYXRDIR="/cygdrive/c/python25/lib/site-packages/pyxr/"
fi

# clean everything up
rm -rf apidoc pyxr
rm -f check.out

# a function that copies a directory tree to the website if we also have that module
copytowebsite() {
    # $1 is directory here
    # $2 is url path from root of website
    if [ ! -d "$1" ]
    then
	echo "$1 doesn't exist and cant be copied!"
	return # can't do it
    fi

    # this is how we detect the website - look for a website checkout alongside this
    # directory
    if [ ! -d ../website/site/.svn ]
    then
	return  # not found
    fi

    # ok, lets copy
    echo "Copying directory $1 to be on web site at url /$2"
    rm -rf ../website/site/$2
    cp -r $1 ../website/site/$2
}

# nice little function to see if a file is in subversion
isinsvn() {
    svn info "$1" 2>/dev/null | grep "$1" >/dev/null
}

# we look for all .py files in SVN
pyfiles="bp.py gui.py guiwidgets.py guihelper.py common.py" # we have to do this in this order first else python crashes

# find files in src
for f in `find src -name '*.py' -print |sed s@^src/@@ | sort`
do
    if isinsvn src/$f
    then
       case `basename $f` in
          p_*.py | __init__.py | setup.py | p2econfig.py ) # we don't want these
            true
         ;;   
         * )
	    case $f in
		native/evolution/* | native/outlook/* | native/qtopiadesktop/* | native/usb/* | native/wab/* )
                  # pychecker barfs on the above
		  true
                ;;
                *)
		  pyfiles="$pyfiles $f"
                ;;
	    esac
         ;;
       esac
    fi
done

pyfiles="`echo $pyfiles | sed 's/\.py//g' | sed 's@/@.@g'`"
pyfiles="$pyfiles native.evolution native.outlook native.qtopiadesktop native.usb native.wab"
echo $pyfiles

if [ "$EPYDOC" != "" ]
then
    PYTHONPATH=src $EPYDOC --check $pyfiles > check.out
    PYTHONPATH=src $EPYDOC -o apidoc  --css blue  -n bitpim -u http://www.bitpim.org $pyfiles
    copytowebsite apidoc apidoc
fi

if [ "$PYXRDIR" != "" ]
then
    oldpwd=`pwd`
    cd "$PYXRDIR"
    $PYTHON buildWeb.py
    cd "$oldpwd"
    if $cygwin
    then
        mv /cygdrive/c/pyxrc /cygdrive/c/pyxr/c
        mv /cygdrive/c/pyxr .
    fi
    copytowebsite pyxr pyxr
fi

if [ "$PYCHECKER" != "" ]
then
    PYTHONPATH=src $PYCHECKER $pyfiles
fi
