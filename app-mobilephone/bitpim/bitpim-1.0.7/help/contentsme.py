#!/usr/bin/env python

# $Id: contentsme.py 4547 2008-01-05 07:00:04Z djpham $

import HTMLParser
import sys

class HHCParser(HTMLParser.HTMLParser):

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.seenul=False

    def handle_starttag(self, tag, attrs):
        getattr(self, "handle_start_"+tag)(attrs)

    def handle_endtag(self, tag):
        getattr(self, "handle_end_"+tag)()

    def handle_end_body(self):
        pass

    def handle_end_html(self):
        pass

    def handle_start_html(self, attrs):
        pass

    def handle_start_head(self, attrs):
        pass
    
    def handle_end_head(self):
        pass

    def handle_start_meta(self, attrs):
        pass

    def handle_start_body(self, attrs):
        self.hier=[]
        self.parent=[]

    def handle_start_ul(self, attrs):
        self.hier.append([])
        self.seenul=True

    def handle_end_ul(self):
        if len(self.hier)>1:
            self.hier[-2].append(self.hier[-1])
            self.hier.pop()

    def handle_start_li(self, attrs):
        self.item={}

    def handle_start_object(self, attrs):
        pass

    def handle_start_param(self, attrs):
        if not self.seenul: return
        name=None
        value=None
        for a,v in attrs:
            if a.lower()=='name':
                name=v.lower()
            elif a.lower()=='value':
                value=v
        assert name is not None and value is not None
        self.item[name]=value

    def handle_end_object(self):
        if not self.seenul: return
        self.hier[-1].append(self.item)


def printhier(hier, indent=0):
    for i in hier:
        if isinstance(i, type([])):
            printhier(i, indent+1)
        else:
            print "    "*indent, i['name'], i['local']

def genhtmllist(items, indent=0):
    istr="    "*(indent+1)
    if len(items)==0:
        return ""
    op="%sTOC_%d\n" % (istr, indent)
    for i in items:
        if isinstance(i, type([])):
            op+=genhtmllist(i, indent+1)
        else:
            op+="%sTOCITEM_%d(%s,%s)\n" % (istr,indent, i['name'], i['local'])
    op+="%sENDTOC_%d\n" % (istr, indent)
    return op

def fixupcontentspages(hier):
    i=0
    while i+1< len(hier):
        if isinstance(hier[i+1], type([])):
            fixuppage(hier[i]['local'][:-1]+'d', # source file is .htd not htm
                      hier[i+1])
            fixupcontentspages(hier[i+1])
            i+=1
        i+=1

def fixuppage(file, children):
    print file,

    op=""
    found=False
    spew=True
    f=open(file, "rt")
    for line in f.readlines():
        if line.find("<!-- CONTENTS BEGIN -->")>=0:
            spew=False
            op+=line
            op+="BEGIN_TOC\n"
            op+=genhtmllist(children)
            op+="END_TOC\n"
            found=True
            continue
        if line.find("<!-- CONTENTS END -->")>=0:
            spew=True
        if spew:
            op+=line
    f.close()

    if found:
        f=open(file, "wt")
        f.write(op)
        f.close()
        print "\t[updated]"
    else:
        print "\t[no tags]"


if __name__ == '__main__':
    parser=HHCParser()

    parser.feed(open(sys.argv[1]).read())
    parser.close()

    parser.hier=parser.hier[0]

    # printhier(parser.hier)
    fixupcontentspages(parser.hier)
    fixuppage("rootcontents.htd", parser.hier)
