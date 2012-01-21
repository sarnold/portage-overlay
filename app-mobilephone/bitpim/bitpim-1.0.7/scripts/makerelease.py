#!/usr/bin/env python
# $Id: makebranch.py 2868 2006-03-05 03:39:32Z rogerb $

# Check subversion is on the path
import os, sys, xml.dom.minidom
if os.popen("svn help", "r").read().find("proplist")<0:
    print "You need to have the Subversion binaries available.  A good start is"
    print "http://subversion.tigris.org/project_packages.html"
    sys.exit(1)


# check to see we are at a top level directory
topdirs=('buildrelease', 'dev-doc', 'examples', 'experiments', 'help', 'helpers', 'packaging', 'resources', 'scripts', 'src')
for d in topdirs:
    if not os.path.isdir(d):
        print "There should be a directory named",d
        sys.exit(2)

# sys.argv[1] is the branch target
if len(sys.argv)!=2:
    print "The one and only  argument needs to be the new version number."
    print "One example would be 0.8.09"
    sys.exit(3)
release=sys.argv[1]

branchtarget="https://bitpim.svn.sourceforge.net/svnroot/bitpim/releases/"+sys.argv[1]

branchdirs=topdirs

def run(cmd):
    print cmd
    res=os.system(cmd)
    if res:
        print "Returned code",res,"! Aborting!"
        sys.exit(res)


externals=[]
copies=[]

metadata=xml.dom.minidom.parseString(os.popen("svn info --xml .", "r").read())
toprev=int(metadata.documentElement.getElementsByTagName("entry")[0].getAttribute("revision"))
topurl=str(metadata.documentElement.getElementsByTagName("entry")[0].getElementsByTagName("url")[0].firstChild.nodeValue)
toproot=str(metadata.documentElement.getElementsByTagName("entry")[0].getElementsByTagName("repository")[0].getElementsByTagName("root")[0].firstChild.nodeValue)
assert topurl.startswith(toproot)
toppath=topurl[len(toproot):]

for d in topdirs:
    metadata=xml.dom.minidom.parseString(os.popen("svn info --xml "+d, "r").read())
    url=str(metadata.documentElement.getElementsByTagName("entry")[0].getElementsByTagName("url")[0].firstChild.nodeValue)
    rev=int(metadata.documentElement.getElementsByTagName("entry")[0].getAttribute("revision"))
    root=str(metadata.documentElement.getElementsByTagName("entry")[0].getElementsByTagName("repository")[0].getElementsByTagName("root")[0].firstChild.nodeValue)
    assert url.startswith(root)
    path=url[len(root):]
    
    # same rigmarole for the revision number
    rev=int(metadata.documentElement.getElementsByTagName("entry")[0].getAttribute("revision"))
    
    # we want to branch this one - dir, target, rev, path
    copies.append( (d, "/".join([branchtarget, d]), rev, "/".join([toppath, d])) )

cmd='svn mkdir -m "making a release from rev %d of %s" %s' % (toprev, toppath, branchtarget)
run(cmd)
for src,dest,rev,path in copies:
    cmd='svn copy -m "release %s from rev %d of %s" %s %s' % (release, rev, path, src, dest)
    run(cmd)

