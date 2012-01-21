#!/usr/bin/env python
###
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2003-2004 Steven Palm <n9yty@n9yty.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### This code was originally written to package up BitPim but has been
### refactored to build almost any Python program.
###
### $Id: makedist.py 4751 2009-07-22 23:58:44Z djpham $


# Runs on Linux, Windows and Mac

"""Builds a binary distribution of a Python program

This code runs on Windows, Linux and Mac, and will create binary distributions
suitable for mass use"""

import os
import shutil
import sys
import glob
import re
import StringIO, traceback
import distutils.core
import email.Utils
import time
import zipfile
import getopt
import subprocess

# i got real tired of typing these and having the lines get really long
opj=os.path.join
opd=os.path.dirname
opb=os.path.basename

# Aribtrary constants
PATH_CXFREEZE="/opt/cx_Freeze-3.0.3"
PATH_INNOSETUP="c:\\program files\\inno setup 5\\compil32.exe"
RT_MANIFEST = 24
WINXP_MANIFEST=manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="Program"
    type="win32"
/>
<description>Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''


def rmrf(path):
    """Delete directory tree like rm -rf does"""
    # on linux and mac, make any directories read/write.  if they were previously read only then we won't be able to delete
    if sys.platform!='win32':
        os.system("find \""+path+"\" -type d -print0 | xargs -0 chmod +w ; true")
    entries=os.listdir(path)
    for e in entries:
        fullname=opj(path,e)
        if os.path.isdir(fullname):
            rmrf(fullname)
        else:
            os.remove(fullname)
    os.rmdir(path)

def recursiveglob(pattern):
    # Note that this returns matching files only.  It won't return matching
    # directory names
    res=[]
    dir=opd(pattern)
    if len(dir):
        for d in os.listdir(dir):
            if os.path.isdir(opj(dir, d)):
                res+=recursiveglob(opj(dir, d, opb(pattern)))
    return res+[p for p in glob.glob(pattern) if os.path.isfile(p)]

def run(*args, **kwargs):
    """Execute the command.

    The path is searched"""
    verbose=kwargs.get("verbose", True)
    if verbose:
        print `args`
    p=subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True)
    _res=p.communicate()
    if verbose:
        print "returned", p.returncode
    if p.returncode:
        if not verbose:
            print `args`
            print "returned", p.returncode
        raise Exception("The command failed:\n%s", _res[1])
    
def clean():
    """Remove temporary directories created by various packaging tools"""
    if os.path.isdir("dist"):
        rmrf("dist")
    if os.path.isdir("build"):
        rmrf("build")


def dosubs(subs, infile, outfile=None):
    """Performs substitutions on a template file or string

    @param infile:  filename to read or string
    @param outfile: filename to write result to or None if infile is a string
    @type subs: dict
    @param subs: the substitutions to make
    """
    if outfile is None:
        stuff=infile
    else:
        stuff=open(infile, "rt").read()

    for k in subs:
        stuff=re.sub("%%"+k+"%%", "%s" % (subs[k],), stuff)

    if outfile:
        open(outfile, "w").write(stuff)
    else:
        return stuff

def windowsbuild(pkg, vals):
    """Do all the steps necessary to make a Windows installer"""
        
    # clean up
    clean()

    import py2exe
    defaults={
        'options': {
                     'py2exe': { 'optimize': 2, 'compressed': 1, 'dist_dir': 'dist/files'}
                  },
        'windows': [],
        'console': [],
        'script_args': ('py2exe', ),
         }
        
    opts=pkg.getpy2exeoptions(defaults)
    
    # add in manifests if not already specified
    w=[]
    for i in opts['windows']:
        # insert manifest at begining - user version will override if supplied
        i['other_resources']=[(RT_MANIFEST, 1, WINXP_MANIFEST)]+i.get('other_resources', [])
        # set other values if not provided
        for k,v in ( ('icon_resources', [(1, "%%ICONFILE%%")]),
                     ('product_version', '%%VERSION%%'),
                     ('version', '%%DQVERSION%%'),
                     ('comments', '%%COMMENTS%%'),
                     ('company_name', "%%URL%%"),
                     ('copyright', "%%COPYRIGHT%%"),
                     ('name', "%%NAME%%"),
                     ('description', "%%DESCRIPTION%%"),
                      ):
            if k not in i:
                i[k]=v
        w.append(i)

    opts['windows']=w

    # fixup vals for any that are missing
    if 'RELEASE' not in vals:
        vals['RELEASE']=0
    if 'OUTFILE' not in vals:
        if vals['RELEASE']: rstr='-r'+`vals['RELEASE']`+"-"
        else: rstr=""
        vals['OUTFILE']="%s%s-%s-%ssetup.exe" % (vals['OUTFILEPREFIX'], vals['NAME'].lower(), vals['VERSION'], rstr)

    opts=eval(dosubs(vals, repr(opts)))

    # run py2exe
    distutils.core.setup(**opts)

    # copy resources
    distdir=opts['options']['py2exe']['dist_dir']
    if hasattr(pkg, "copyresources"):
        pkg.copyresources(distdir)

    # fixups (permissions, files)
    if hasattr(pkg, "finalize"):
        pkg.finalize(distdir)

    # make the innosetup package
    vals['GUID']=vals['GUID'].replace("{", "{{") # needed for innosetup
    # must not supply .exe on end to innosetup
    while vals['OUTFILE'].endswith(".exe"):
        vals['OUTFILE']=vals['OUTFILE'][:-4]
    dosubs(vals, vals['ISSFILE'], opj("dist", opb(vals['ISSFILE'])))

    # Run innosetup
    run("c:\\program files\\inno setup 5\\compil32.exe", "/cc", opj("dist", opb(vals['ISSFILE'])))

def linuxcommonbuild(pkg, vals):
    """Do all the steps necessary to make a Linux filesystem build,
    ready for packaging"""
    clean()

    # make it look like cx-Freeze supports py2exe/py2app style options
    defaults={
        'options': {
             'cxfreeze':
                {
                   'compressed': 1,
                   'optimize': 2,
                   'dist_dir': 'dist/files',
                   'base-name': 'Console',
                   'init-script': 'ConsoleSetLibPath.py',
                 },
             },
        }

    opts=pkg.getcxfreezeoptions(defaults)

    # fixups
    for app in opts['app']:
        if 'dest_base' not in app:
            app['dest_base']=opb(os.path.splitext(app['script'])[0])
        if 'lib_path' not in app:
            app['lib_path']="/usr/lib/%%NAME%%-%%VERSION%%"
        if 'bin_path' not in app:
            app['bin_path']='/usr/bin/'+app['dest_base']
        if 'bin_ver_path' not in app:
            app['bin_ver_path']='/usr/bin/'+app['dest_base']+"-%%VERSION%%"

    # rpm names are usually lower case and the version number can't include dashes,
    # so we offer sanitized versions
    if 'RPMNAME' not in vals:
        vals['RPMNAME']=vals['NAME'].lower()
    if 'RPMVERSION' not in vals:
        vals['RPMVERSION']=vals['VERSION'].lower().replace("-", ".")


    opts=eval(dosubs(vals, repr(opts)))

    app=opts['app'][0] # ::TODO:: add support for multiple apps
    
    args=[opj(PATH_CXFREEZE, "FreezePython")]
    if opts['options']['cxfreeze']['compressed']:
        args.append("-c")
    o=opts['options']['cxfreeze']['optimize']
    if o==1:
        args.append("-O")
    if o==2:
        args.append("-OO")
    args.append("--base-name=%s" % (opts['options']['cxfreeze']['base-name']),)
    args.append("--init-script=%s" % (opts['options']['cxfreeze']['init-script']),)
    if 'includes' in opts['options']['cxfreeze']:
        args.append("--include-modules="+",".join(opts['options']['cxfreeze']['includes']))
    args.append("--target-dir=%s" % (opj(opts['options']['cxfreeze']['dist_dir'], app['lib_path'][1:]),))
    args.append("--target-name=%s" % (app['dest_base'],))
    args.append(app['script'])

    run(*args)

    # nb opj on linux is silly opj("/foo/bar", "/abc") does
    # not give "/foo/bar/abc".  Instead it only gives "/abc".
    # Consequently we have to add [1:] all over the place to stop it
    # from behaving that way.
    assert app['lib_path'][0]=='/'
    assert app['bin_path'][0]=='/'
    assert app['bin_ver_path'][0]=='/'
    
    # copy resources
    distdir=opj(opts['options']['cxfreeze']['dist_dir'], app['lib_path'][1:]) 
    if hasattr(pkg, "copyresources"):
        pkg.copyresources(distdir)

    # put in executable
    for f in ('bin_path', 'bin_ver_path'):
        p=opj(opts['options']['cxfreeze']['dist_dir'], app[f][1:])
        if not os.path.isdir(opd(p)):
            os.makedirs(opd(p))
        open(p, "wt").write(
            """#!/bin/sh
            LD_LIBRARY_PATH=%s:$LD_LIBRARY_PATH exec %s "$@"\n""" % (app['lib_path'], opj(app['lib_path'], app['dest_base'])))
        os.chmod(p, 0555)

    # fix python/wxPython shared libraries - cxfreeze doesn't bring them all in and
    # rpath needs to be stripped out
    copy={}
    for so in recursiveglob(opj(opts['options']['cxfreeze']['dist_dir'], "*.so"))+\
        recursiveglob(opj(opts['options']['cxfreeze']['dist_dir'], app['dest_base'])):
        for line in os.popen("ldd "+so, "r"):
            line=line.split()
            if line[-2].startswith("/usr/lib/wxPython-") or \
               line[-2].startswith("/usr/lib/libpython"):
                pd=opd(so)
                libs=copy.get(pd, [])
                if line[2] not in libs:
                    copy[pd]=libs+[line[2]]

    for d in copy:
        for lib in copy[d]:
            print lib,"==>",d
            shutil.copy2(lib, d)

    # we don't do this earlier because the copy stage brings in more libs
    for so in recursiveglob(opj(opts['options']['cxfreeze']['dist_dir'], "*.so")):
        run("chrpath", "-d", so, verbose=False)
        run("strip", so, verbose=False)

    # fixups (permissions, files)
    if hasattr(pkg, "finalize"):
        pkg.finalize(distdir)
    return opts

def linuxrpmbuild(pkg, vals):
    """Do all the steps necessary to make a Linux RPM"""
    # Build the tree
    opts=linuxcommonbuild(pkg, vals)
    # make a rpm.  this will contain a tar file of our code (dist.tar), a spec file,
    # and a makefile
    import tarfile
    distfilesdir=opj(opts['options']['cxfreeze']['dist_dir'])
    distdir=opd(distfilesdir)
    builddir=opj(distdir, "build")
    os.mkdir(builddir)


    tf=tarfile.open(opj(builddir, "dist.tar"), "w")
    tf.add(distfilesdir, "", recursive=True)
    tf.close()

    # Make a filelist
    fl=open(opj(builddir, "FILELIST"), "wt")
    for f in recursiveglob(opj(distfilesdir, "*")):
        print >>fl, f[len(distfilesdir):]
    fl.close()

    dosubs(vals, vals['SPECFILE'], opj(builddir, opb(vals['SPECFILE'])))

    n="%s-%s" % (vals['RPMNAME'], vals['RPMVERSION'])

    tf=tarfile.open(opj(builddir, n+".tar.gz"), "w:gz")
    tf.add(opj(builddir, "dist.tar"), opj(n, "dist.tar"))
    tf.add(opj(builddir, "FILELIST"), opj(n, "FILELIST"))
    tf.add(opj(builddir, opb(vals['SPECFILE'])), opb(vals['SPECFILE']))
    tf.close()

    # Make a rpm build directory structure
    rpmdir=opj(builddir, "rpmtopdir")
    os.mkdir(rpmdir)
    for i in ("BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"):
        os.mkdir(opj(rpmdir, i))
        
    run("rpmbuild", "-ta", "--define=_topdir "+os.path.abspath(rpmdir), opj(builddir, n+".tar.gz"))

    for rpm in recursiveglob(opj(rpmdir, "RPMS", "*.rpm")):
        shutil.copy2(rpm, distdir)

def linuxdebbuild(pkg, vals):
    """Do all the steps necessary to make a Linux deb package"""
    # Build the tree
    opts=linuxcommonbuild(pkg, vals)
    # Setting up the dir structure
    distfilesdir=opj(opts['options']['cxfreeze']['dist_dir'])
    distdir=opd(distfilesdir)
    builddir=opj(distdir, "build")
    os.mkdir(builddir)
    _debiandir=opj(builddir, 'debian')
    _debianbitpimdir=opj(_debiandir, 'bitpim')
    # copy the contents of debian dir over
    shutil.copytree(opj('packaging', 'debian'), _debiandir)
    # extract the versionhsitory (as changelog) file
    file(opj(_debiandir, 'versionhistory.htm'), 'wt').write(
        zipfile.ZipFile(opj('resources', 'bitpim.htb'), 'r').read('versionhistory.htm'))
    # copy the dist tree over
    shutil.copytree(distfilesdir, _debianbitpimdir)
    # update various variables in the control areas
    for _file in ('changelog', 'postinst', 'postrm'):
        _filename=opj(_debiandir, _file)
        dosubs(vals, _filename, _filename)
    # Build the deb package
    print 'Building deb package'
    _pwd=os.getcwd()
    os.chdir(builddir)
    run(opj('debian', 'rules'), "binary")
    os.chdir(_pwd)

def linuxebuildbuild(pkg, vals):
    """Do all the steps necessary to make a gentoo tbz2 package"""
    # Build the tree
    opts=linuxcommonbuild(pkg, vals)
    # Setting up the dir structure
    distfilesdir=opj(opts['options']['cxfreeze']['dist_dir'])
    distdir=opd(distfilesdir)
    builddir=opj(distdir, "build")
    os.mkdir(builddir)
    # setting vars to pass to ebuild
    _pwd=os.getcwd()
    vals['FILESDIR']=os.path.abspath(distfilesdir)
    vals['BUILDDIR']=os.path.abspath(builddir)
    # gentoo portage dirs
    _portage_dist_dir='/usr/portage/distfiles'
    _portage_overlay_bitpim_dir='/usr/local/portage/app-mobilephone/bitpim'
    _portage_packages_dir='/usr/portage/packages/All'
    # manually "fetch" the load
    os.chdir(distfilesdir)
    _basename=opts['app'][0]['dest_base']
    run('tar', 'cjf', opj(_portage_dist_dir, '%s-%s.tar.bz2'%(_basename, vals['VERSION'])),
        '.')
    os.chdir(_pwd)
    # copy over and subst the ebuild file
    _ebuildfile=opj(_portage_overlay_bitpim_dir, '%s-%s.ebuild'%(_basename, vals['VERSION']))
    shutil.copy2(opj('packaging', 'gentoo', '%s.ebuild'%_basename), _ebuildfile)
    dosubs(vals, _ebuildfile, _ebuildfile)
    # and run ebuild on it
    os.chdir(_portage_overlay_bitpim_dir)
    run('ebuild', _ebuildfile, 'digest', 'package', 'clean')
    os.chdir(_pwd)
    # copy the package file (tbz2) over to dist
    shutil.copy2(opj(_portage_packages_dir, '%s-%s.tbz2'%(_basename, vals['VERSION'])),
         distdir)
                     

def macbuild(pkg, vals):
    """Do all the steps necessary to make a Mac dimg
    
    Now using the py2app stuff from Bob Ippolito <bob@redivi.com>,
    the replacement for the crufty `bundlebuilder` stuff previously
    used for MacOS X executables.  This will be the new standard for
    PythonMac bundling.
    
    It can be found at:
    
    http://undefined.org/python/#py2app
    
    """

    clean()
    os.mkdir("dist")

    import py2app

    defaults={
        'options': {
             'py2app':
                {
                   'compressed': 1,
                   'iconfile': '%%ICONFILE%%',
                   'optimize': 2,
                   'dist_dir': 'dist/files',
                   'plist':
                      {
                         'CFBundleIconFile': '%%ICONFILE%%',
                         'CFBundleName': '%%NAME%%',
                         'CFBundleVersion': '%%DQVERSION%%',
                         'CFBundleShortVersionString': '%%NAME%%-%%VERSION%%',
                         'CFBundleGetInfoString': '%%NAME%%-%%VERSION%%',
                         'CFBundleExecutable': '%%NAME%%',
                         'CFBundleIdentifier': '%%GUID%%',
                         'PyResourcePackages': ['lib/python2.5/lib-dynload'],
                      },
                    'prefer_ppc': 'true',
                 },
             },
        'script_args': ('py2app',),
        }

    opts=pkg.getpy2appoptions(defaults)
    opts=eval(dosubs(vals, repr(opts)))
    
    distutils.core.setup(**opts)
    # copy resources
    distdir=opj(opts['options']['py2app']['dist_dir'], opts['options']['py2app']['plist']['CFBundleName']+".app", "Contents", "Resources")
    if hasattr(pkg, "copyresources"):
        pkg.copyresources(distdir)

    # fixups (permissions, files)
    if hasattr(pkg, "finalize"):
        pkg.finalize(distdir)

    # fixup missing values
    if 'RELEASE' not in vals:
        vals['RELEASE']=0
    if 'OUTFILE' not in vals:
        if vals['RELEASE']: rstr='-r'+`vals['RELEASE']`
        else: rstr=""
        vals['OUTFILE']="%s%s-%s%s.dmg" % (vals['OUTFILEPREFIX'], vals['NAME'].lower(), vals['VERSION'], rstr)


    if (os.uname()[2] >= "7.0.0"):
        run('hdiutil', 'create', '-imagekey', 'zlib-level=9', '-srcfolder', opts['options']['py2app']['dist_dir'], '-volname', vals['NAME'], '-nouuid', '-noanyowners', opj('dist', vals['OUTFILE']))
    else:
        # print "Create disk image with dist folder as the source in DiskCopy with name:\n    -> JAGUAR-%s.dmg <-." % verstr
        assert False
        # this code needs to be fixed up to be like above - I don't have access to Jaguar to test
        ret=os.system('/usr/local/bin/buildDMG.pl -buildDir=dist -compressionLevel=9 -volName=BitPim -dmgName=JAGUAR-%s.dmg dist/BitPim.app' % verstr)
        print "image creation returned", ret

def sanitycheck():
    if sys.platform=="win32":
        print "py2exe version",
        import py2exe
        expect='0.6.9'
        if py2exe.__version__!=expect:
            raise Exception("Should be %s version of py2exe - you have %s" % (expect, py2exe.__version__))
        print "  OK"

        print "Innosetup",
        if not os.path.isfile(PATH_INNOSETUP):
            raise Exception("InnoSetup not found at", PATH_INNOSETUP)
        print "  OK"
    if sys.platform=="darwin":
        print "py2app version",
        import py2app
        expect='0.3.6'
        if py2app.__version__!=expect:
            raise Exception("Should be %s version of py2app - you have %s" % (expect, py2app.__version__))
        print "  OK"
    if sys.platform.startswith("linux"):
        print "cx_Freeze",
        fname=opj(PATH_CXFREEZE, "FreezePython")
        if not os.path.exists(fname):
            raise Exception("Can't find "+fname)
        print "  OK"

        # ::TODO:: - add checks for rpmbuild

# This comes from src/common.py
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

     while True:
          if not tb.tb_next:
               break
          tb=tb.tb_next
     stack=[]
     f=tb.tb_frame
     while f:
          stack.append(f)
          f=f.f_back
     stack.reverse()
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

def setupconfig():
    import ConfigParser
    global _theconfig
    _theconfig=ConfigParser.RawConfigParser()
    _theconfig.read([os.path.expanduser('~/.makedist_py.ini')])
    if not _theconfig.has_section('default'):
        _theconfig.add_section('default')

def getconfig(key, default=None):
    global _theconfig
    if _theconfig.has_option('default', key):
        return _theconfig.get('default', key)
    return default

def setconfig(key, value):
    global _theconfig
    _theconfig.set('default', key, value)

def saveconfig():
    global _theconfig
    _theconfig.write(open(os.path.expanduser('~/.makedist_py.ini'), "wt"))

def makeconfig(key, description):
    while True:
        print description
        v=getconfig(key)
        if v is not None:
            print "DEFAULT (hit return):",v
        entered=raw_input("--> ")
        if len(entered):
            setconfig(key,entered)
            saveconfig()
            return entered
        if len(v) and len(entered)==0:
            return v
        print "You must enter a value"
        
    
if __name__=='__main__':
    # setup exception handler
    def eh(*args):
        print >>sys.stderr,formatexception(args)
        sys.exit(127)
    sys.excepthook=eh

    try:
        _options, _args=getopt.gnu_getopt(sys.argv[1:], 'p:v:l:')
        if _args:
            raise getopt.GetoptError('Invalid argument')
        _invalid_opt=False
    except getopt.GetoptError:
        _error_str=sys.exc_info()[1].msg
        _invalid_opt=True
    if _invalid_opt:
        print _error_str
        print 'Usage: %s [-p <package module>] [-v <version>] ' \
              '[-l redhat|debian|gentoo]'%sys.argv[0]
        sys.exit(1)

    # default support script and version
    pkg="src/package.py"
    _thisversion=None
    _platformname=None
    for _k, _v in _options:
        if _k=='-p':
            pkg=_v
        elif _k=='-v':
            _thisversion=_v
        elif _k=='-l':
            _platformname=_v.lower()

    print "Using package file",pkg

    sys.path=[os.path.abspath(os.path.dirname(pkg))]+sys.path

    pkg=__import__(os.path.splitext(os.path.basename(pkg))[0])

    if _thisversion:
        pkg.setversion(_thisversion)
    # rebuild depedence files
    if hasattr(pkg, 'build_dependences'):
        sys.path.append(os.path.join(os.getcwd(), 'packaging'))
        pkg.build_dependences()
    # do a sanity check
    sanitycheck()  # ours
    if hasattr(pkg, 'sanitycheck'):
        pkg.sanitycheck() # theirs
    if hasattr(pkg, 'ensureofficial'):
        pkg.ensureofficial()

    vals=pkg.getvals()
    print 'version', vals['VERSION']

    # fixup vals
    if 'OUTFILEPREFIX' not in vals:
        vals['OUTFILEPREFIX']=""
    if 'GUID' not in vals:
        raise Exception("You must supply a guid in the vals")

    # we need some fields
    setupconfig()
    if 'PUBLISHER' not in vals:
        vals['PUBLISHER']=makeconfig('PUBLISHER', "Enter your name and email address as the packager/publisher of this build\nFor example Joe Acme <joe.acme@example.com>")
    vals['BUILDDATETIME']=email.Utils.formatdate(time.time(), True)
    
    if sys.platform=='win32':
        windowsbuild(pkg, vals)
    elif sys.platform.startswith('linux'):
        if not _platformname:
            import platform
            _platformname=platform.dist()[0].lower()
        if _platformname in ('redhat', 'suse', 'mandrake'):
            linuxrpmbuild(pkg, vals)
        elif _platformname=='debian':
            linuxdebbuild(pkg, vals)
        elif _platformname=='gentoo':
            linuxebuildbuild(pkg, vals)
        else:
            raise Exception("Don't know what to do with "+`platform.dist()`)
    elif sys.platform=='darwin':
        macbuild(pkg, vals)
    else:
        print "Unknown platform", sys.platform
