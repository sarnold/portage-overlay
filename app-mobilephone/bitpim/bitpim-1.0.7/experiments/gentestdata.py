#!/usr/bin/env python

# This file is licensed as public domain.  The exception is the
# random_midi_data function which is somewhat derived from part
# of a function in the phase.sf.net.  Feel free to figure out
# if it constitutes a derived work (in which case it is GPL)
# or not (in which case it is public domain).

# This program generates test data for BitPim
# The one and only argument should be an output directory
import random
import sys
import os
import struct
import cStringIO
import time
import calendar

from DSV import DSV

###
### The various utility functions
###

# generate random length strings

letters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
words=letters+"    "
digits="0123456789"
phonenumber=digits+"()+ -#"
wordsanddigits=words+digits
url=letters+digits+"/."
email=letters+digits+"@."
boolean=[ "0", "1", "true", "True", "false", "False" ]
categories=words+digits+" ;"

# as a special case to considerably speed up some choices we prebuild a 30,000
# character string and take random slices of that
speedups={}
for item in (letters, words, digits, phonenumber, wordsanddigits, url, email, categories):
    speedups[id(item)]="".join([random.choice(item) for i in range(30000)])

def gen_string(minlength=0, maxlength=515, choices=letters):
    if type(choices)==type([]): # use only zero or one of a list
        return random.choice(choices)
    s=speedups.get(id(choices),None)
    if s is not None:
        begin=random.randrange(0,29999-maxlength)
        return s[begin:begin+random.randrange(maxlength)]
    buffy=cStringIO.StringIO()
    map(buffy.write, [random.choice(choices)  for i in range(random.randrange(minlength, maxlength))])
    return buffy.getvalue()

def gen_strings(min=1,max=5,choices=letters):
    return [gen_string(choices=choices) for _ in range(random.randrange(min,max+1))]


###
### Generate the various bits
###

# vcards
def vcardfrigme(choices):
    if random.randrange(1,10)==7: return ""
    
    if random.choice((True,False)):
        return ";TYPE="+",".join([random.choice(choices) for _ in range(random.randrange(0, 1+len(choices)/3))])
    else:
        return ";"+";".join([random.choice(choices) for _ in range(random.randrange(0, 1+len(choices)/3))])

def FN(io):
    print >>io, "FN:"+gen_string(choices=words)

def N(io):
    print >>io, "N:"+";".join(gen_strings(5,5,choices=words))

def NICKNAME(io):
    print >>io, "NICKNAME:"+gen_string(choices=words)

atypes=( "pref", "work", "home", "dom", "intl", "postal", "parcel", "foo", "bar")

def ADR(io):
    s="ADR"
    print >>io, "ADR"+vcardfrigme(atypes)+":"+ \
          ";".join(gen_strings(7,7,choices=wordsanddigits))

ttypes=( "pref", "home", "msg", "work", "voice", "fax", "cell", "video", "pager", "bbs", "modem", "car", "isdn", "pcs", "nonesense", "boo" )

def TEL(io):
    print >>io, "TEL"+vcardfrigme(ttypes)+":"+gen_string(choices=phonenumber)

etypes= ("internet", "x400", "pref", "home", "work", "foo", "bar" )

def EMAIL(io):
    print >>io, "EMAIL"+vcardfrigme(etypes)+":"+gen_string(choices=email)

def TITLE(io):
    print >>io, "TITLE:"+gen_string(choices=wordsanddigits)

def ROLE(io):
    print >>io, "ROLE:"+gen_string(choices=words)

def ORG(io):
    print >>io, "ORG:"+";".join(gen_strings(1,5,choices=words))

def CATEGORIES(io):
    print >>io, "CATEGORIES:"+",".join(gen_strings(choices=words))

def NOTE(io):
    print >>io, "NOTE:"+gen_string(choices=words)

utypes=( "home", "work", "foo")

def URL(io):
    print >>io, "URL"+vcardfrigme(utypes)+":"+gen_string(choices=url)
        
def random_vcard(maxentries=1000):
    """Generate random vcards"""

    # the various fields in their proportions
    fields= [FN]*1       +\
            [N]*1        +\
            [NICKNAME]*1 +\
            [ADR]*4      +\
            [TEL]*7      +\
            [TITLE]*1    +\
            [ROLE]*1     +\
            [ORG]*1      +\
            [EMAIL]*4    +\
            [CATEGORIES] +\
            [URL]*2
            

    
    io=cStringIO.StringIO()
    for _ in range(random.randrange(0,maxentries)):
        print >>io, "BEGIN:vcard"
        # randomly put in a version number
        f=random.choice([None, "Version: 2.1", "Version: 3.0"])
        if f: print >>io, f

        for _ in range(random.randrange(0,len(fields))):
            random.choice(fields)(io)

        print >>io,"END:vcard"
    return io.getvalue()

def random_phonebook_csv(minlength=0, maxlength=2000, maxfields=400):
    """Generate a random phonebook in CSV format
    @param minlength: minimum number of entries
    @param maxlength: maximum number of entries
    @returns:  a list of lists of the data.  the first row is the headers
    """
    
    possfields=["First Name", "Last Name", "Middle Name",
                "Name", "Nickname", "Email Address", "Web Page", "Fax", "Home Street",
                "Home City", "Home Postal Code", "Home State",
                "Home Country/Region",  "Home Phone", "Home Fax", "Mobile Phone", "Home Web Page",
                "Business Street", "Business City", "Business Postal Code",
                "Business State", "Business Country/Region", "Business Web Page",
                "Business Phone", "Business Fax", "Pager", "Company", "Notes", "Private",
                "Category", "Categories"]

    # some fields  use different types mostly
    types={ 'Fax': phonenumber, "Home Phone": phonenumber, "Home Fax": phonenumber, "Mobile Phone": phonenumber,
            "Business Phone": phonenumber, "Business Fax": phonenumber, "Pager": phonenumber,
            "Email Address": email, "Categories": categories, "Private": boolean }

    print "Generating phonebook",
    headers=[random.choice(possfields) for i in range(random.randrange(1,maxfields))]
    numrows=random.randrange(minlength, maxlength)
    print "with",len(headers),"columns and",numrows,"rows"

    op=[ headers ]

    for i in range(numrows):
        op.append([gen_string(choices=types.get(col, words)) for col in headers])

    print "  ... generation completed"
    return DSV.exportDSV(op, quoteall=random.choice([0,1]))


# See license statement at the top of this file
# This function is partially derived from MaleCB function
# http://cvs.sourceforge.net/viewcvs.py/phase/phase/phase.c
def random_midi_data(minlength=2, maxlength=300):
    op=cStringIO.StringIO()
    # header
    op.write("MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\xc0")
    # information track
    # op.write("MTrk\x00\x00\x00\x13")
    # op.write("\x00\xff\x58\x04\x04\x02\x18\x08")
    # op.write("\x00\xff\x51\x03\x06\x8a\x1b")
    # op.write("\x00\xff\x2f\x00")
    baselength=len(op.getvalue())

    scales = ( ( 60, 62, 64, 67, 69, 72, 74, 76 ),
               ( 60, 62, 64, 65, 67, 69, 71, 72 ),
               ( 60, 62, 63, 65, 67, 68, 70, 72 ),
               ( 60, 62, 63, 65, 67, 69, 71, 72 ),
               ( 60, 62, 63, 65, 67, 68, 71, 72 ),
               ( 60, 62, 64, 66, 68, 70, 72, 74 ),
               ( 60, 62, 63, 65, 66, 68, 69, 71 ),
               ( 60, 61, 62, 63, 64, 65, 66, 67 ) )
    # music track
    op.write("MTrk\x00\x00\x00\x00") # we fill in length afterwards
    op.write("\x00")
    op.write("\xc0")
    op.write(chr(random.randrange(0,16)))
    op.write("\x00")
    op.write("\x90")

    total=96 * random.randrange(minlength, maxlength)
    
    foo=total
    j=0
    ht=24
    tablebase=random.randrange(0,12)-6
    while foo>48:
        note=tablebase+random.choice(scales[0])
        op.write(chr(note))
        op.write(chr( 64 - (ht/2) + random.randrange(0,ht)))
        dur=96
        bar=random.randrange(0,len(scales))
        op.write(chr(dur-bar))
        op.write(chr(note))
        op.write(chr(0))
        op.write(chr(bar))
        foo-=dur
    op.write(chr(note))
    op.write(chr( 64 - (ht/2) + random.randrange(0,ht)))
    op.write("\x89")
    op.write("\x77")
    op.write(chr(note))
    op.write("\x00\x00\xff\x2f\x00")

    d=list(op.getvalue())
    ld=len(d)-baselength-8 # subtract all headers
    d[baselength+4]=chr( (ld>>24)&0xff)
    d[baselength+5]=chr( (ld>>16)&0xff)
    d[baselength+6]=chr( (ld>>8)&0xff)
    d[baselength+7]=chr( (ld>>0)&0xff)

    return "".join(d)
    
    
def random_midi_files(directory, minnumber=0, maxnumber=100):
    """Generates random midi files in the specified directory
    @returns: a list of filenames (the basenames with the .mid extension included)
    """
    names=[gen_string(minlength=10, maxlength=50)+".mid" for i in range(random.randrange(minnumber, maxnumber))]

    print "Generating",len(names),"midi files"
    for n in names:
        f=open(os.path.join(directory, n), "wb")
        f.write(random_midi_data())
        f.close()
    print "  ... generation complete"
    return names

def random_wallpaper_files(directory, minnumber=0, maxnumber=100):
    """Generates random wallpaper files in the specified directory
    @returns: a list of filenames (the basenames including the extension)
    """

    names=[gen_string(minlength=10, maxlength=50) for i in range(random.randrange(minnumber, maxnumber))]
    print "Generating",len(names),"wallpaper files"

    from wxPython.lib import colourdb
    colourdb.updateColourDB()
    colours=colourdb.getColourList()

    penstyles=[ wx.SOLID, wx.DOT, wx.LONG_DASH, wx.SHORT_DASH, wx.CROSS_HATCH ]
    types=[ (wx.BITMAP_TYPE_BMP, ".bmp"), (wx.BITMAP_TYPE_JPEG, ".jpg"), (wx.BITMAP_TYPE_PNG, ".png")]

    
    for n in range(len(names)):
        width=random.randrange(1,200)
        height=random.randrange(1,200)
        bitmap=wx.EmptyBitmap(width, height)
        mdc=wx.MemoryDC()
        mdc.SelectObject(bitmap)
        mdc.Clear()
        for i in range(random.randrange(1,200)):
            pen=wx.Pen(random.choice(colours), random.randrange(1,10), random.choice(penstyles))
            mdc.SetPen(pen)
            mdc.DrawLine(random.randrange(0,width), random.randrange(0,height), random.randrange(0,width), random.randrange(0, height))
        t,e=random.choice(types)
        names[n]=names[n]+e
        mdc.SelectObject(wx.NullBitmap)
        bitmap.SaveFile(os.path.join(directory, names[n]), t)
    
    print "  ... generation complete"
    return names

def random_calendar(minnumber=0, maxnumber=500):
    """Generates random calendar data

    @returns:  a dict of calendar entries

    We put several entries around todays date so that you have something to look at"""

    num=random.randrange(minnumber, maxnumber)
    close=random.randrange(0, num)

    print "Generating",num,"calendar entries"

    res={}
    for pos in range(0,num):
        if pos<close:
            # generate a close event
            y,m,d=time.localtime()[:3]
            v=y*12+m-1
            v+=random.randrange(-1,2) # within a month or so
            y=v/12
            m=(y%12)+1
        else:
            y,m=random.randrange(1990,2015), random.randrange(1,13)

        d=random.randrange(1, 1+calendar.monthrange(y,m)[1])

        entry={}
        entry['start']=(y,m,d,random.randrange(0,24), random.randrange(0,60))

        if pos<close:
            if random.randrange(0,2):
                m+=1
                if m==13:
                    m=1
                    y+=1
            if random.randrange(0,2):
                y+=1
            d=random.randrange(1,1+calendar.monthrange(y,m)[1])

        entry['end']=(y,m,d,random.randrange(0,24), random.randrange(0,60))

        entry['description']=gen_string(choices=words)
            
        entry['repeat']=random.choice([None, "daily", "monfri", "weekly", "monthly", "yearly"])

        entry['changeserial']=1

        entry['snoozedelay']=random.randrange(0,900)

        if random.randrange(0,2):
            entry['alarm']=None
        else:
            entry['alarm']=random.randrange(0,10000)

        entry['daybitmap']=0
        entry['ringtone']=0
        entry['pos']=pos

        ex=[]
        for i in range(random.randrange(0,30)):
            s=entry['start']
            e=entry['end']
            ex.append( (random.randrange(min(s[0], e[0]), 1+max(s[0], e[0])),
                        random.randrange(min(s[1], e[1]), 1+max(s[1], e[1])),
                        random.randrange(min(s[2], e[2]), 1+max(s[2], e[2]))
                      ))
        entry['exceptions']=ex
        res[pos]=entry
    print "  ... generation complete"
    return res
    
if __name__=='__main__':

    # Move wx stuff here
    import wx
    app=wx.PySimpleApp()
    
    def gen_all():
        if not os.path.isdir(sys.argv[1]):
            os.mkdir(sys.argv[1])
        j=os.path.join

        if True:
            midis=random_midi_files(sys.argv[1])
        else:
            midis=[]

        if True:
            wps=random_wallpaper_files(sys.argv[1])
        else:
            wps=[]

        if True:
            cal=random_calendar()
            f=open(j(sys.argv[1], "calendar-index.idx"), "wt")
            f.write("result['calendar']=%s\n" % (`cal`,))
            f.write("FILEVERSION=2")
            f.close()

        if True:
            vc=random_vcard()
            f=open(j(sys.argv[1], "vcards.vcf"), "wt")
            f.write(vc)
            f.close()

        if True:
            pb=random_phonebook_csv()
            f=open(j(sys.argv[1], "phonebook.csv"), "wt")
            f.write(pb)
            f.close()

    gen_all()
    sys.exit(0)

    import hotshot, hotshot.stats, os
    file=os.path.abspath("bpprof")
    profile=hotshot.Profile(file)
    profile.run("gen_all()")
    profile.close()
    del profile
    stats=hotshot.stats.load(file)
    stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(25)
    stats.sort_stats('cum', 'calls')
    stats.print_stats(25)
    stats.sort_stats('calls', 'time')
    stats.print_stats(25)
    
