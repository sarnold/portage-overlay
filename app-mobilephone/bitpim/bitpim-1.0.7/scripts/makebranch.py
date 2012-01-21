#!/usr/bin/env python
# $Id: makebranch.py 3177 2006-04-27 06:25:26Z rogerb $

# Check subversion is on the path
import os, sys, xml.dom.minidom, tempfile

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
if len(sys.argv)<2 or not sys.argv[1].startswith("/"):
    print "The first argument needs to be where you want the branch to appear"
    print "and should be relative to the top of the repository.  For example"
    print "/developer/rogerb/gofaster would put the branch at"
    print "https://svn.sourceforge.net/svnroot/bitpim/developer/rogerb/gofaster"
    sys.exit(3)

branchtarget="https://svn.sourceforge.net/svnroot/bitpim"+sys.argv[1]

branchdirs=sys.argv[2:]
if len(branchdirs)<=1:
    print "You need to supply the list of directories you want to branch"
    print "The most likely one is src"
    sys.exit(4)

for d in branchdirs:
    if d not in topdirs:
        print d,"is not a valid directory!"
        sys.exit(5)

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
    
    if d in branchdirs:
        # we want to branch this one - dir, target, rev, path
        copies.append( (d, "/".join([branchtarget, d]), rev, "/".join([toppath, d])) )
    else:
        externals.append( (d, url) )

cmd='svn mkdir -m "new branch on dirs %s from rev %d of %s" %s' % (`branchdirs`, toprev, toppath, branchtarget)
run(cmd)
for src,dest,rev,path in copies:
    cmd='svn copy -m "branch from rev %d of %s" %s %s' % (rev, path, src, dest)
    run(cmd)

# subversion doesn't allow setting properties against a URL - it has to be against local copy
branchdirname=tempfile.mkdtemp(prefix="__branch__")
externalsfile=tempfile.mkstemp(prefix="__externals__")
os.close(externalsfile[0])
externalsfile=externalsfile[1]

try:
    open(externalsfile, "wt").write("\n".join(["   ".join([d,url]) for d,url in externals]))
    cmd="svn checkout --non-recursive --quiet --non-interactive --ignore-externals %s %s" % (branchtarget, branchdirname)
    run(cmd)
    cmd="svn propset svn:externals --file %s %s" % (externalsfile, branchdirname)
    run(cmd)
    print "====", externalsfile
    print open(externalsfile, "rt").read()
    print "----", externalsfile
    cmd='svn commit -m "Directories %s are not branched here" %s' % (`[d for d in topdirs if d not in branchdirs]`, branchdirname)
    run(cmd)
finally:
    import shutil
    shutil.rmtree(branchdirname)
    os.remove(externalsfile)
    

