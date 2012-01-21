import sys
import os
import time
import cStringIO
import string
import getopt

def datatohexstring(data):
    """Returns a pretty printed hexdump of the data

    @rtype: string"""
    res=cStringIO.StringIO()
    lchar=""
    lhex="00000000 "
    for count in range(0, len(data)):
        b=ord(data[count])
        lhex=lhex+"%02x " % (b,)
        if b>=32 and string.printable.find(chr(b))>=0:
            lchar=lchar+chr(b)
        else:
            lchar=lchar+'.'

        if (count+1)%16==0:
            res.write(lhex+"    "+lchar+"\n")
            lhex="%08x " % (count+1,)
            lchar=""
    if len(data):
        while (count+1)%16!=0:
            count=count+1
            lhex=lhex+"   "
        res.write(lhex+"    "+lchar+"\n")
    return res.getvalue()

def filtermergerw(lines):
    "A filter that merges all successful consecutive reads and writes"
    l=1
    while l<len(lines):
        # if we are a read or write and we are successful and the same can be said
        # for the previous line, put out data into their line and delete our line
        if (lines[l][1]=="IRP_MJ_READ" or lines[l][1]=="IRP_MJ_WRITE") and lines[l][2]=='SUCCESS' and \
           lines[l-1][1]==lines[l][1] and lines[l-1][2]=='SUCCESS':
            data=lines[l][3].split(":",1)[1]
            lines[l-1][3]+=" "+data
            del lines[l]
            continue
        l+=1
            
def filterremovenoise(lines):
    "A filter that removes most 'noise' requests"
    l=0
    while l<len(lines):
        v=lines[l][1]
        if v in ('IOCTL_SERIAL_GET_TIMEOUTS', 'IOCTL_SERIAL_GET_BAUD_RATE', 'IOCTL_SERIAL_GET_LINE_CONTROL',
                 'IOCTL_SERIAL_GET_HANDFLOW', 'IOCTL_SERIAL_GET_CHARS', 'IOCTL_SERIAL_GET_WAIT_MASK',
                 'IOCTL_SERIAL_WAIT_ON_MASK', 'IOCTL_SERIAL_GET_COMMSTATUS', 'IOCTL_SERIAL_PURGE'):
            del lines[l]
            continue
        l+=1
        
def usage():
    print "This program converts output from portmon to BitPim analyser"
    print "usage: portmon2analyser [option ...] portmonfile.log"
    print "  -o file             Output filename (default is portmonfile.txt)"
    print "  --output file"
    print "  -m | --mergerw      Runs a filter that merges consecutive successful"
    print "                      reads and writes (useful if the program does many"
    print "                      one byte reads and writes)"
    print "  -s | --stripnoise   Runs a filter that ignores a whole bunch of"
    print "                      superfluous lines"
    sys.exit(1)


args,rest=getopt.getopt(sys.argv[1:], "o:ms", ["output", "mergerw", "stripnoise"])

if len(rest)!=1:
    print "You need to specify exactly one input filename"
    usage()

infile=rest[0]
outfile=os.path.splitext(infile)[0]+".txt"
filters=[]

for k,v in args:
    if k=="-o" or k=="--output":
        outfile=v
    elif k=="-m" or k=="--mergerw":
        filters.append(filtermergerw)
    elif k=='-s' or k=='--stripnoise':
        filters.append(filterremovenoise)
    else:
        assert False, "unknown argument "+k
        sys.exit(2)

# we need to do filters in a particular order
f=[]
if filterremovenoise in filters: f.append(filterremovenoise)
if filtermergerw in filters: f.append(filtermergerw)
filters=f

lines=[]

f=open(infile, "rt")
for line in f:
    line=[l.strip() for l in line.split(None, 6)[1:]]
    line[0]=float(line[0]) # turn time into float
    del line[1] # don't care about program name
    del line[2] # don't need driver name either
    lines.append(line)
f.close()

# is time steadily increasing, or a delta?
v=0
inc=0
for l in lines[:min(len(lines), 200)]: # look at the first 200 lines
    v2=l[0]
    if v2>v: inc+=1
    elif v2<v: inc-=1
    v=v2

if not inc+10>min(len(lines),200):
    # ok, they are deltas, so fix them up to be monotonous
    for l in range(1,len(lines)):
        lines[l][0]+=lines[l-1][0]

# some filters
for f in filters:
    f(lines)

basetime=time.time()
f=open(outfile, "wt")
for l in lines:
    lastlineread=l
    try:
        if l[2]=='Length':  # incomplete READ - SUCCESS/FAILURE field not filled in
            continue
        tt=basetime+l[0]
        t=time.localtime(tt)
        print >>f, "%02d:%02d:%02d.%03d" % (t[3], t[4], t[5], int((tt-int(tt))*1000)),
        print >>f, l[1],
        if l[2]!='SUCCESS':
            print >>f, l[2],
        if l[1]!="IRP_MJ_READ" and l[1]!='IRP_MJ_WRITE':
            print >>f, " ".join(l[3:])
            continue
        # read or write - deal with data
        f.write("\n")
        if l[2]!="SUCCESS": continue
        assert l[3].startswith("Length"), "Line %s doesn't begin with Length" % (`l`,)
        data=l[3].split(":",1)[1].split()
        # data is now each byte as a hex string, turn into actual stream of bytes
        data="".join([chr(int(x,16)) for x in data])
        if len(data):
            print >>f, datatohexstring(data)
    except:
        print "Last line read is\n"+`lastlineread`
        raise
f.close()
