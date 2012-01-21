#!/usr/bin/env python
### BITPIM
###
### Copyright (C) 2003-2006 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2003-2004 Steven Palm <n9yty@n9yty.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: package.py 4702 2008-08-26 02:13:48Z djpham $

# This file provides the packaging definitions used by the buildrelease system

import sys
import os
import os.path
import shutil

import version

def sanitycheck():
    "Check all dependencies are present and at the correct version"
    
    print "=== Sanity check ==="

    print "svn location",
    if not "$HeadURL: https://bitpim.svn.sourceforge.net/svnroot/bitpim/releases/1.0.7/src/package.py $".split(":",1)[1].strip().startswith("https://bitpim.svn.sourceforge.net"):
        raise Exception("Needs to be checked out from https://bitpim.svn.sourceforge.net")
    print "  OK"

    print "python version",
    if sys.version_info[:2]!=(2,5):
       raise Exception("Should be  Python 2.5 - this is "+sys.version)
    print "  OK"

    print "wxPython version",
    import wx
    if wx.VERSION[:4]!=(2,8,8,1):
        raise Exception("Should be wxPython 2.8.8.1.  This is "+`wx.VERSION`)
    print "  OK"

    print "wxPython is unicode build",
    if not wx.USE_UNICODE:
        raise Exception("You need a unicode build of wxPython")
    print "  OK"

    if sys.platform!='win32':
        print "native.usb",
        import native.usb
        print "  OK"

    print "pycrypto version",
    expect='2.0.1'
    import Crypto
    if Crypto.__version__!=expect:
        raise Exception("Should be %s version of pycrypto - you have %s" % (expect, Crypto.__version__))
    print "  OK"

    print "paramiko version",
    expect='1.7.4 (Desmond)'
    import paramiko
    if paramiko.__version__!=expect:
        raise Exception("Should be %s version of paramiko - you have %s" % (expect, paramiko.__version__))
    print "  OK"
    
    print "bitfling",
    import bitfling
    print "  OK"

    print "pyserial",
    import serial
    print "  OK"

    print "apsw",
    import apsw
    ver="3.5.9-r2"
    if apsw.apswversion()!=ver:
        raise Exception("Should be apsw version %s - you have %s" % (ver, apsw.apswversion()))
    print "  OK"

    print "sqlite",
    ver="3.6.1"
    if apsw.sqlitelibversion()!=ver:
        raise Exception("Should be sqlite version %s - you have %s" % (ver, apsw.sqlitelibversion()))
    print "  OK"
        
    print "jaro/winkler string matcher",
    import native.strings.jarow
    print "  OK"

    # bsddb (Linux only, for evolution)
    if sys.platform=="linux2":
        print "bsddb ",
        import bsddb
        print "  OK"

    # win32com.shell - See http://starship.python.net/crew/theller/moin.cgi/WinShell
    if sys.platform=='win32':
        import py2exe.mf as modulefinder # in py2exe < 0.6.4 use "import modulefinder"
        import win32com
        for p in win32com.__path__[1:]:
            modulefinder.AddPackagePath("win32com", p)
        for extra in ["win32com.shell"]: #,"win32com.mapi"
            __import__(extra)
            m = sys.modules[extra]
            for p in m.__path__[1:]:
                modulefinder.AddPackagePath(extra, p)

    print "=== All checks out ==="

def resources():
    """Get a list of the resources (images, executables, sounds etc) we ship

    @rtype: dict
    @return: The key for each entry in the dict is a directory name, and the value
             is a list of files within that directory"""
    tbl={}
    # list of files
    exts=[ '*.xy', '*.png', '*.ttf', '*.wav', '*.jpg', '*.css', '*.pdc', '*.ids']
    if sys.platform=='win32':
        # on windows we also want the chm help file and the manifest needed to get Xp style widgets
        exts=exts+['*.chm', '*.manifest', '*.ico']
        exts=exts+['helpers/*.exe','helpers/*.dll']
    if sys.platform=='linux2':
        exts=exts+['helpers/*.lbin', '*.htb']
    if sys.platform=='darwin':
        exts=exts+['helpers/*.mbin', '*.htb']
    # list of directories to look in
    dirs=[ os.path.join('.', 'resources'), '.' ]
    # don't ship list
    dontship.append("pvconv.exe")  # Qualcomm won't answer if I can ship this
    for wildcard in exts:
        for dir in dirs:
            for file in glob.glob(os.path.join(dir, wildcard)):
                if os.path.basename(file).lower() in dontship: continue 
                d=os.path.dirname(file)
                if not tbl.has_key(d):
                    tbl[d]=[]
                tbl[d].append(file)

    files=[]
    for i in tbl.keys():
        files.append( (i, tbl[i]) )

    return files

def isofficialbuild():
    "Work out if this is an official build"
    import socket
    h=socket.gethostname().lower()
    # not built by rogerb (or stevep/n9yty) are unofficial
    return h in ('rh9bitpim.rogerbinns.com', "roger-ba470eb54",
                 "rogerbmac.rogerbinns.com",
                 # Joe's build machines
                 "tinyone", "tiny2one",
                 # Sean's
                 "leviathan.local",
                 )

def ensureofficial():
    """If this is not an official build then ensure that version.vendor doesn't say it is"""
    # First do a freeze
    version.__freeze()
    print "Reloading version"
    reload(version)
    officialbuild=isofficialbuild()
    if officialbuild and version.vendor=='unofficial':
        vendor='official'
    elif not officialbuild and version.vendor=='official':
        vendor='unofficial'
    else:
        vendor=None
    if vendor:
        # so modify file
        versionpy=os.path.join(os.path.dirname(__file__), "version.py")
        out=[]
        for line in open(versionpy, "rt"):
            if line.startswith('vendor="'):
                line='vendor="$%s %s $"\n' % ("Id:", vendor)
            out.append(line)
                
        open(versionpy, "wt").write("".join(out))
        reload(version)

def getversion():
    return version.version
def setversion(versionstring, vendorstring='Test'):
    version.setversion(versionstring, vendorstring)

import phones
import encodings
import glob
def getallencodingsmodules():
    # work-around for cx_freeze: add all encodings modules
    _res=[]
    _dir=os.path.dirname(encodings.__file__)
    _glob_name=os.path.join(_dir, '*.py')
    _modules=[os.path.basename(os.path.splitext(x)[0]) for x in glob.glob(_glob_name) \
              if os.path.basename(x) != '__init__.py']
    for _key in _modules:
        # collect what we have
        try:
            _mod_name='encodings.'+_key
            __import__(_mod_name)
            _res.append(_mod_name)
        except (ImportError,AttributeError):
            pass
    return _res

lazyimportmodules=['email.iterators']
if sys.platform=='darwin':
    lazyimportmodules.append('Carbon.CF')
elif sys.platform=='linux2':
    try:
        import _md5, _sha
        lazyimportmodules.append('_md5')
        lazyimportmodules.append('_sha')
    except ImportError:
        pass

def getcxfreezeoptions(defaults):
    global lazyimportmodules
    defaults.update(
        {
        'app': [{'script': 'src/bp.py', 'dest_base': 'bitpim'}],
        }
        )
    defaults['options']['cxfreeze']['includes']=phones.getallmodulenames()+\
                                                 getallencodingsmodules()+\
                                                 lazyimportmodules
    return defaults

def getpy2appoptions(defaults):
    global lazyimportmodules
    defaults.update(
        {
        'app': [{'script': 'src/bp.py',}],
        }
        )
    defaults['options']['py2app']['includes']=phones.getallmodulenames()+\
                                               lazyimportmodules
    defaults['options']['py2app']['plist']['CFBundleHelpBookFolder']="BitPim Help"
    defaults['options']['py2app']['plist']['CFBundleHelpBookName']="BitPim Help"
    return defaults

def getpy2exeoptions(defaults):
    global lazyimportmodules
    defaults.update(
        {
        'windows': [{ 'script': 'src/bp.py', 'dest_base': 'bitpimw', }],
        'console': [{ 'script': 'src/bp.py', 'dest_base': 'bitpim', }],
        }
        )
    defaults['options']['py2exe']['includes']=phones.getallmodulenames()+\
                                               lazyimportmodules
    defaults['options']['py2exe']['compressed']=0 # make setup.exe smaller but installed code larger
    return defaults

udevrules_filename='60-bitpim.rules'
udevrules_line='ACTION=="add", SYSFS{idProduct}=="%04x", SYSFS{idVendor}=="%04x", RUN+="/usr/bin/bpudev $env{DEVNAME} $number $sysfs{devnum}"'
from common import importas
def generate_udevrules():
    """Generate the udev rules file based on all the known VIDs and PIDs"""
    global udevrules_filename, udevrules_line
    _ids={}
    for _f in phones.getallmodulenames():
        _profile=importas(_f)
        if hasattr(_profile.Profile, 'usbids'):
            for _id in _profile.Profile.usbids:
                _ids[_id]=True
    _rules=[]
    for _entry in _ids:
        _rules.append(udevrules_line%(_entry[1], _entry[0]))
    _f=file('resources/%s'%udevrules_filename, 'wt').write('\n'.join(_rules))
    
def copyresources(destdir):
    if sys.platform=='linux2':
        generate_udevrules()
    import packageutils
    packageutils.copysvndir('resources', os.path.join(destdir, 'resources'), resourcefilter)
    packageutils.copysvndir('helpers', os.path.join(destdir, 'helpers'), resourcefilter)

def resourcefilter(srcfilename, destfilename):
    global udevrules_filename
    exts=[ '.xy', '.png', '.ttf', '.wav', '.jpg', '.css', '.pdc', '.ids', '.ico']
    files=[]
    if sys.platform=='win32':
        # on windows we also want the chm help file 
        exts=exts+['.chm', '.exe', '.dll']
    if sys.platform=='linux2':
        exts=exts+['.lbin', '.htb']
        files+=['bpudev', udevrules_filename]
    if sys.platform=='darwin':
        exts=exts+['.mbin', '.htb']
    if os.path.splitext(srcfilename)[1] in exts or \
       os.path.basename(srcfilename) in files:
        return srcfilename, destfilename
    return None

def build_dependences():
    # build modules
    import buildmodules
    # rebuild all the prototocol (*.p) files
    import protogen
    for f in glob.glob("src/phones/*.p"):
        protogen.processfile(f, f+"y")

def finalize(destdir):
    if sys.platform=='win32':
        for f in ("w9xpopen.exe",):
            if os.path.exists(os.path.join(destdir, f)):
                os.remove(os.path.join(destdir, f))
    if sys.platform=='darwin':
        # do apple help
        import zipfile
        helpdir=os.path.join(destdir, "English.lproj", "BitPim Help")
        os.makedirs(helpdir)
        f=zipfile.ZipFile(os.path.join(destdir, "resources", "bitpim.htb"), "r")
        for name in f.namelist():
            if os.path.splitext(name)[1] in ('.htm', '.html', '.jpg', '.png'):
                open(os.path.join(helpdir, name), "wb").write(f.read(name))
                os.chmod(os.path.join(helpdir, name), 0444)
            else:
                print "skipping help file",name
        # the idiots at apple decided to make it impossible to automate the help indexer
        # how about giving it command line options?
        v=os.popen("sw_vers -productVersion", "r").read()
        if v.startswith("10.3"):
            res=os.system("open -a \"Apple Help Indexing Tool\" \""+helpdir+"\"")
            assert res==0
            # we do this stupid loop monitoring cpu consumption and once it is
            # unchanged for 2 seconds, assume that the indexing is complete
            print "Waiting for indexing tool to stop by monitoring CPU consumption"
            import time
            lastval=""
            val="x"
            pid=0
            while val!=lastval:
                print ".",
                sys.stdout.flush()
                time.sleep(2)
                for line in os.popen("ps cx", "r"):
                    line=line.split()
                    line=line[:4]+[" ".join(line[4:])]
                    if line[4]!="Apple Help Indexing Tool":
                        continue
                    pid=line[0]
                    lastval=val
                    val=line[3]
                    break
            print "\nIt would appear to be done"
            os.system("kill "+pid)
        elif v.startswith("10.4"):
            #use Help Indexer
            res=os.system("\"/Developer/Applications/Utilities/Help Indexer.app/Contents/MacOS/Help Indexer\" \""+helpdir+"\" -PantherIndexing YES -Tokenizer 1 -ShowProgress YES -TigerIndexing YES")
            assert res==0
        # copy the css file in
        shutil.copy2(os.path.join(destdir, "resources", "bitpim.css"), os.path.join(helpdir, ".."))
        # don't need the wx style help any more
        os.remove(os.path.join(destdir, "resources", "bitpim.htb"))
    if sys.platform!='win32':
        os.system("find \""+destdir+"\" -depth -print0 | xargs -0 chmod a-w")

def getvals():
    "Return various values about this product"
    res={
        'NAME': version.name,
        'VERSION': version.version,
        'RELEASE': version.release,
        'DQVERSION': version.dqverstr,
        'COMMENTS': "Provided under the GNU Public License (GPL)",
        'DESCRIPTION': "Open Source Mobile Phone Tool",
        'COPYRIGHT': "Copyright (C) 2003-2006 The BitPim developers",
        'URL': version.url,
        'SUPPORTURL': "http://www.bitpim.org/help/support.htm",
        'GUID': "{FA61D601-A0FC-48BD-AE7A-54946BCD7FB6}",
        'VENDOR': version.vendor,
        'ISSFILE': 'packaging/bitpim.iss',
        'SPECFILE': 'packaging/bitpim.spec',
        }
    if sys.platform=='win32':
        res['ICONFILE']="packaging/bitpim.ico"

    if sys.platform=="darwin":
        res['GUID']='org.bitpim.bitpim' # Java style less opaque than the guid style above!
        res['ICONFILE']="packaging/bitpim.icns"
        # prefix with macos versiopn
        v=os.popen("sw_vers -productVersion", "r").read()
        if v.startswith("10.3"):
            res['OUTFILEPREFIX']='PANTHER-'
        elif v.startswith("10.4"):
            res['OUTFILEPREFIX']='TIGER-'
        elif v.startswith("10.2"):
            res['OUTFILEPREFIX']='JAGUAR-'
        elif v.startswith("10.5"):
            res['OUTFILEPREFIX']='LEOPARD-'
    return res
