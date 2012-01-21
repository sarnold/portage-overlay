### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: qtopiadesktop.py 1559 2004-09-04 07:05:08Z rogerb $

"""Be at one with Qtopia desktop (eg as used by the Zaurus)"""

# See recipe 12.6 in the Python Cookbook for the XML parsing bit

import xml.parsers.expat
import os

import encodings.ascii

class XMLParser:

    def __init__(self, filename):
        parser=xml.parsers.expat.ParserCreate()
        parser.CharacterDataHandler=self._handleCharData
        parser.StartElementHandler=self._handleStartElement
        parser.EndElementHandler=self._handleEndElement

        parser.ParseFile(open(filename, "rt"))

    def _handleCharData(self, data): pass
    def _handleEndElement(self, name): pass

    def _handleStartElement(self, name, attrs):
        raise NotImplementedException()

class CategoriesParser(XMLParser):

    def __init__(self, filename="Categories.xml"):
        filename=getqdpath(filename)
        self._data={}
        XMLParser.__init__(self, filename)

    def _handleStartElement(self, name, attrs):
        if name!="Category":
            return
        self._data[int(ununicodify(attrs["id"]))]=ununicodify(attrs["name"])

    def categories(self):
        return self._data


class ABParser(XMLParser):
    def __init__(self, filename="addressbook/addressbook.xml", categories={}):
        filename=getqdpath(filename)
        self.categories=categories
        self._data=[]
        XMLParser.__init__(self, filename)

    def _handleStartElement(self, name, attrs):
        if name!="Contact":
            return
        d=cleandict(attrs)
        # fixup fields
        # d["Uid"]=int(d["Uid"]) - leaving as string for moment since semantics of value are not clear (eg does two's complement of number mean the same thing?)
        # categories
        c=d.get("Categories", "")
        cats=[]
        if len(c):
            c=[int(x) for x in c.split(";")]
            for cat in c:
                if self.categories.has_key(cat):
                    cats.append(self.categories[cat])
                else:
                    if __debug__:
                        print "couldn't find category",cat,"in",`self.categories`
        if len(cats):
            d["Categories"]=cats
        else:
            if d.has_key("Categories"):
                del d["Categories"]
        # emails
        if d.has_key("Emails"):
            d["Emails"]=d["Emails"].split()
        # ::TODO:: gender also needs to be munged
        self._data.append(d)

    def contacts(self):
        return self._data

def getqdpath(filename):
    filename=os.path.expanduser(os.path.join("~/.palmtopcenter", filename))
    if filename.startswith("~"):
        # windows 98, no home directory present
        filename="c:\\"+filename[1:]
    return os.path.abspath(filename)


def getfilename():
    "Returns the filename we need"
    return getqdpath("addressbook/addressbook.xml")

# XML returns all the values as strings, so these two routines
# help strip out the unicode bit
def cleandict(d):
    # remove all unicode from the dict
    newd={}
    for k,v in d.items():
        newd[ununicodify(k)]=ununicodify(v)
    return newd

def ununicodify(value):
    try:
        return str(value)
    except UnicodeEncodeError:
        return value.encode("ascii", 'xmlcharrefreplace')

def getcontacts():
    cats=CategoriesParser()
    ab=ABParser(categories=cats.categories())
    return ab.contacts()

if __name__=="__main__":

    print getcontacts()
