# Public domain - use as you wish

# This file is a sample for using this buildrelease system.  You
# should copy it and adjust for your own code.  You can find a
# more complicated version in the BitPim source code at
# https://svn.sourceforge.net/svnroot/bitpim/trunk/bitpim/src/package.py

import sys
import os

# If you have a src directory at the same level as buildrelease,
# and you have put this file into that src directory, then you'll
# want that directory to be on the Python search path.  This line
# ensures that the directory this file is in is added to the path
sys.path.append(os.path.dirname(__file__)) # this directory needs to be on the path

def sanitycheck():
    "Check your dependencies are present and the correct versions."
    # Raise an exception if there is a problem

    # This tests apsw as an example
    print "apsw",
    import apsw
    ver="3.2.7-r1"
    if apsw.apswversion()!=ver:
        raise Exception("Should be apsw version %s - you have %s" % (ver, apsw.apswversion()))
    print "  OK"

def getversion():
    # return your version string
    return "1.0alpha"

def getpy2exeoptions(defaults):
    # Add windowed binaries with the 'windows' key and console apps
    # with the 'console' key.  These are lists of dicts.

    defaults.update(
        {'windows': [ # These are the keys you can supply.  OPT means optional
                      {'script':          'src/foo.py',          # start file
                       'dest_base':       '%%NAME%%',                 # OPT resulting filename (bar.exe)
                       'icon_resources': [(1, 'src/foo.ico')],   # OPT icon(s)
                       # OPT The remainder become the version tab for the executable in Explorer
                       'version':         "%%DQVERSION%%",    # this must be numbers only as a dotted quad
                       'product_version': '%%VERSION%%',  # any string is fine
                       'comments':        'comments',
                       'company_name':    'company',
                       'copyright':       '%%COPYRIGHT%%',
                       'name':            '%%NAME%%',
                       'description':     '%%DESCRIPTION%%', }
                      ]}
        )

    return defaults

def getcxfreezeoptions(defaults):
    defaults.update(
        {
        'app': [{'script': 'src/foo.py', 'dest_base': '%%NAME%%'}],
        }
        )
    return defaults

def getpy2appoptions(defaults):
    defaults.update(
        {
        'app': [{'script': 'src/foo.py',}], 
        }
        )
    return defaults
        
def copyresources(destdir):
    "Copy other files to the destination directory"
    # Have a look at buildrelease/packageutils.py
    # One useful function there is copysvndir which copies
    # all the files under Subversion control from a source directory to the destdir

def finalize(destdir):
    "Do any finalizations before the installer is made"
    # You'll want to remove unneeded files, set permissions etc


def getvals():
    "Return various values about this product"
    # These values can be used elsewhere by putting them inside double percents
    # (eg %%NAME%%).  Do not put spaces in the name or version
    res={
        'NAME': "sample",
        'VERSION': getversion(),
        'RELEASE': 0,  # increment if you re-release the same version
        'DQVERSION': "1.0.2.3",
        'COMMENTS': "Provided under the GNU Public License (GPL)",
        'DESCRIPTION': "Sample Project",
        'COPYRIGHT': "Copyright (C) 2003-2006 The Developers",
        'URL': "http://www.example.com",
        'SUPPORTURL': "http://www.example.org/help/support.htm",
        # You must use a different GUID for each project otherwise they will be considered the
        # same programs by the OS and cause havoc.  You can generate one at
        # http://www.somacon.com/p113.php
        # This code deliberately has a syntax error so you won't use the one below
        'GUID': +"A3179690-B79E-11DA-B012-B622A1EF5492"-,
        'VENDOR': "Official",
        'PUBLISHER': "Acme", # this is who built and shipped this build.  makedist will prompt for it if not supplied
        }
    if sys.platform=='win32': # windows icon
        res['ICONFILE']="packaging/sample.ico"
    if sys.platform=="darwin": # mac icon
        res['GUID']='org.bitpim.bitpim' # java style guid on mac.  the above style will work as well
        res['ICONFILE']="packaging/sample.icns"

    return res
