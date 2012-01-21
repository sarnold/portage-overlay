### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: vcard.py 4369 2007-08-20 01:59:33Z djpham $

"""Code for reading and writing Vcard

VCARD is defined in RFC 2425 and 2426
"""
from __future__ import with_statement
import sys
import quopri
import base64
import codecs
import cStringIO

import common
import nameparser
import phonenumber

class VFileException(Exception):
    pass

class VFile:
    _charset_aliases={
        'MACINTOSH': 'MAC_ROMAN'
        }
    def __init__(self, source):
        self.source=source    
        

        self.saved=None

    def __iter__(self):
        return self

    def next(self):
        # Get the next non-blank line
        while True:  # python desperately needs do-while
            line=self._getnextline()
            if line is None:
                raise StopIteration()
            if len(line)!=0:
                break

        # Hack for evolution.  If ENCODING is QUOTED-PRINTABLE then it doesn't
        # offset the next line, so we look to see what the first char is
        normalcontinuations=True
        colon=line.find(':')
        if colon>0:
            s=line[:colon].lower().split(";")
            if "quoted-printable" in s or 'encoding=quoted-printable' in s:
                normalcontinuations=False
                while line[-1]=="=" or line[-2]=='=':
                    if line[-1]=='=':
                        i=-1
                    else:
                        i=-2
                    nextl=self._getnextline()
                    if nextl[0] in ("\t", " "): nextl=nextl[1:]
                    line=line[:i]+nextl

        while normalcontinuations:
            nextline=self._lookahead()
            if nextline is None:
                break
            if len(nextline)==0:
                break
            if  nextline[0]!=' ' and nextline[0]!='\t':
                break
            line+=self._getnextline()[1:]

        colon=line.find(':')
        if colon<1:
            # some evolution vcards don't even have colons
            # raise VFileException("Invalid property: "+line)
            if __debug__:
                print "Fixing up bad line",line
            colon=len(line)
            line+=":"

        b4=line[:colon]
        line=line[colon+1:].strip()

        # upper case and split on semicolons
        items=b4.upper().split(";")

        newitems=[]
        if isinstance(line, unicode):
            charset=None
        else:
            charset="LATIN-1"
        for i in items:
            # ::TODO:: probably delete anything preceding a '.'
            # (see 5.8.2 in rfc 2425)
            # look for charset parameter
            if i.startswith("CHARSET="):
                charset = i[8:] or "LATIN-1"
                continue
            # unencode anything that needs it
            if not i.startswith("ENCODING=") and not i=="QUOTED-PRINTABLE": # evolution doesn't bother with "ENCODING="
                # ::TODO:: deal with backslashes, being especially careful with ones quoting semicolons
                newitems.append(i)
                continue
            try:
                if i=='QUOTED-PRINTABLE' or i=="ENCODING=QUOTED-PRINTABLE":
                    # technically quoted printable is ascii only but we decode anyway since not all vcards comply
                    line=quopri.decodestring(line)
                elif i=='ENCODING=B':
                    line=base64.decodestring(line)
                    charset=None
                else:
                    raise VFileException("unknown encoding: "+i)
            except Exception,e:
                if isinstance(e,VFileException):
                    raise e
                raise VFileException("Exception %s while processing encoding %s on data '%s'" % (str(e), i, line))
        # ::TODO:: repeat above shenanigans looking for a VALUE= thingy and
        # convert line as in 5.8.4 of rfc 2425
        if len(newitems)==0:
            raise VFileException("Line contains no property: %s" % (line,))
        # charset frigging
        if charset is not None:
            try:
                decoder=codecs.getdecoder(self._charset_aliases.get(charset, charset))
                line,_=decoder(line)
            except LookupError:
                raise VFileException("unknown character set '%s' in parameters %s" % (charset, b4))          
        if newitems==["BEGIN"] or newitems==["END"]:
            line=line.upper()
        return newitems,line

    def _getnextline(self):
        if self.saved is not None:
            line=self.saved
            self.saved=None
            return line
        else:
            return self._readandstripline()

    def _readandstripline(self):
        line=self.source.readline()
        if line is not None:
            if len(line)==0:
                return None
            elif line[-2:]=="\r\n":    
        

                return line[:-2]
            elif line[-1]=='\r' or line[-1]=='\n':
                return line[:-1]
        return line
    
    def _lookahead(self):
        assert self.saved is None
        self.saved=self._readandstripline()
        return self.saved
        
class VCards:
    "Understands vcards in a vfile"

    def __init__(self, vfile):
        self.vfile=vfile

    def __iter__(self):
        return self

    def next(self):
        # find vcard start
        field=value=None
        for field,value in self.vfile:
            if (field,value)!=(["BEGIN"], "VCARD"):
                continue
            found=True
            break
        if (field,value)!=(["BEGIN"], "VCARD"):
            # hit eof without any BEGIN:vcard
            raise StopIteration()
        # suck up lines
        lines=[]
        for field,value in self.vfile:
            if (field,value)!=(["END"], "VCARD"):
                lines.append( (field,value) )
                continue
            break
        if (field,value)!=(["END"], "VCARD"):
            raise VFileException("There is a BEGIN:VCARD but no END:VCARD")
        return VCard(lines)

class VCard:
    "A single vcard"

    def __init__(self, lines):
        self._version=(2,0)  # which version of the vcard spec the card conforms to
        self._origin=None    # which program exported the vcard
        self._data={}
        self._groups={}
        self.lines=[]
        # extract version field
        for f,v in lines:
            assert len(f)
            if f==["X-EVOLUTION-FILE-AS"]: # all evolution cards have this
                self._origin="evolution"
            if f[0].startswith("ITEM") and (f[0].endswith(".X-ABADR") or f[0].endswith(".X-ABLABEL")):
                self._origin="apple"
            if len(v) and v[0].find(">!$_") > v[0].find("_$!<") >=0:
                self.origin="apple"
            if f==["VERSION"]:
                ver=v.split(".")
                try:
                    ver=[int(xx) for xx in ver]    
                except ValueError:
                    raise VFileException(v+" is not a valid vcard version")
                self._version=ver
                continue
            # convert {home,work}.{tel,label} to {tel,label};{home,work}
            # this probably dates from *very* early vcards
            if f[0]=="HOME.TEL": f[0:1]=["TEL", "HOME"]
            elif f[0]=="HOME.LABEL": f[0:1]=["LABEL", "HOME"]
            elif f[0]=="WORK.TEL": f[0:1]=["TEL", "WORK"]
            elif f[0]=="WORK.LABEL": f[0:1]=["LABEL", "WORK"]
            self.lines.append( (f,v) )
        self._parse(self.lines, self._data)
        self._update_groups(self._data)

    def getdata(self):
        "Returns a dict of the data parsed out of the vcard"
        return self._data

    def _getfieldname(self, name, dict):
        """Returns the fieldname to use in the dict.

        For example, if name is "email" and there is no "email" field
        in dict, then "email" is returned.  If there is already an "email"
        field then "email2" is returned, etc"""
        if name not in dict:
            return name
        for i in xrange(2,99999):
            if name+`i` not in dict:
                return name+`i`

    def _parse(self, lines, result):
        for field,value in lines:
            if len(value.strip())==0: # ignore blank values
                continue
            if '.' in field[0]:
                f=field[0][field[0].find('.')+1:]
            else: f=field[0]
            t=f.replace("-", "_")
            func=getattr(self, "_field_"+t, self._default_field)
            func(field, value, result)

    def _update_groups(self, result):
        """Update the groups info """
        for k,e in self._groups.items():
            self._setvalue(result, *e)

    # fields we ignore

    def _field_ignore(self, field, value, result):
        pass

    _field_LABEL=_field_ignore        # we use the ADR field instead
    _field_BDAY=_field_ignore         # not stored in bitpim
    _field_ROLE=_field_ignore         # not stored in bitpim
    _field_CALURI=_field_ignore       # not stored in bitpim
    _field_CALADRURI=_field_ignore    # variant of above
    _field_FBURL=_field_ignore        # not stored in bitpim
    _field_REV=_field_ignore          # not stored in bitpim
    _field_KEY=_field_ignore          # not stored in bitpim
    _field_SOURCE=_field_ignore       # not stored in bitpim (although arguably part of serials)
    _field_PHOTO=_field_ignore        # contained either binary image, or external URL, not used by BitPim

    # simple fields
    
    def _field_FN(self, field, value, result):
        result[self._getfieldname("name", result)]=self.unquote(value)

    def _field_TITLE(self, field, value, result):
        result[self._getfieldname("title", result)]=self.unquote(value)

    def _field_NICKNAME(self, field, value, result):
        # ::TODO:: technically this is a comma seperated list ..
        result[self._getfieldname("nickname", result)]=self.unquote(value)

    def _field_NOTE(self, field, value, result):
        result[self._getfieldname("notes", result)]=self.unquote(value)

    def _field_UID(self, field, value, result):
        result["uid"]=self.unquote(value) # note that we only store one UID (the "U" does stand for unique)

    #
    #  Complex fields
    # 

    def _field_N(self, field, value, result):
        value=self.splitandunquote(value)
        familyname=givenname=additionalnames=honorificprefixes=honorificsuffixes=None
        try:
            familyname=value[0]
            givenname=value[1]
            additionalnames=value[2]
            honorificprefixes=value[3]
            honorificsuffixes=value[4]
        except IndexError:
            pass
        if familyname is not None and len(familyname):
            result[self._getfieldname("last name", result)]=familyname
        if givenname is not None and len(givenname):
            result[self._getfieldname("first name", result)]=givenname
        if additionalnames is not None and len(additionalnames):
            result[self._getfieldname("middle name", result)]=additionalnames
        if honorificprefixes is not None and len(honorificprefixes):
            result[self._getfieldname("prefix", result)]=honorificprefixes
        if honorificsuffixes is not None and len(honorificsuffixes):
            result[self._getfieldname("suffix", result)]=honorificsuffixes

    _field_NAME=_field_N  # early versions of vcard did this

    def _field_ORG(self, field, value, result):
        value=self.splitandunquote(value)
        if len(value):
            result[self._getfieldname("organisation", result)]=value[0]
        for f in value[1:]:
            result[self._getfieldname("organisational unit", result)]=f

    _field_O=_field_ORG # early versions of vcard did this

    def _field_EMAIL(self, field, value, result):
        value=self.unquote(value)
        # work out the types
        types=[]
        for f in field[1:]:
            if f.startswith("TYPE="):
                ff=f[len("TYPE="):].split(",")
            else: ff=[f]
            types.extend(ff)

        # the standard doesn't specify types of "home" and "work" but
        # does allow for random user defined types, so we look for them
        type=None
        for t in types:
            if t=="HOME": type="home"
            if t=="WORK": type="business"
            if t=="X400": return # we don't want no steenking X.400

        preferred="PREF" in types

        if type is None:
            self._setvalue(result, "email", value, preferred)
        else:
            addr={'email': value, 'type': type}
            self._setvalue(result, "email", addr, preferred)

    def _field_URL(self, field, value, result):
        # the standard doesn't specify url types or a pref type,
        # but we implement it anyway
        value=self.unquote(value)
        # work out the types
        types=[]
        for f in field[1:]:
            if f.startswith("TYPE="):
                ff=f[len("TYPE="):].split(",")
            else: ff=[f]
            types.extend(ff)

        type=None
        for t in types:
            if t=="HOME": type="home"
            if t=="WORK": type="business"

        preferred="PREF" in types

        if type is None:    
            self._setvalue(result, "url", value, preferred)
        else:
            addr={'url': value, 'type': type}
            self._setvalue(result, "url", addr, preferred)        

    def _field_X_SPEEDDIAL(self, field, value, result):
        if '.' in field[0]:
            group=field[0][:field[0].find('.')]
        else:
            group=None
        if group is None:
            # this has to belong to a group!!
            print 'speedial has no group'
        else:
            self._setgroupvalue(result, 'phone', { 'speeddial': int(value) },
                                group, False)

    def _field_TEL(self, field, value, result):
        value=self.unquote(value)
        # see if this is part of a group
        if '.' in field[0]:
            group=field[0][:field[0].find('.')]
        else:
            group=None

        # work out the types
        types=[]
        for f in field[1:]:
            if f.startswith("TYPE="):
                ff=f[len("TYPE="):].split(",")
            else: ff=[f]
            types.extend(ff)

        # type munging - we map vcard types to simpler ones
        munge={ "BBS": "DATA", "MODEM": "DATA", "ISDN": "DATA", "CAR": "CELL", "PCS": "CELL" }
        types=[munge.get(t, t) for t in types]

        # reduce types to home, work, msg, pref, voice, fax, cell, video, pager, data
        types=[t for t in types if t in ("HOME", "WORK", "MSG", "PREF", "VOICE", "FAX", "CELL", "VIDEO", "PAGER", "DATA")]

        # if type is in this list and voice not explicitly mentioned then it is not a voice type
        antivoice=["FAX", "PAGER", "DATA"]
        if "VOICE" in types:
            voice=True
        else:
            voice=True # default is voice
            for f in antivoice:
                if f in types:
                    voice=False
                    break
                
        preferred="PREF" in types

        # vcard allows numbers to be multiple things at the same time, such as home voice, home fax
        # and work fax so we have to test for all variations

        # if neither work or home is specified, then no default (otherwise things get really complicated)
        iswork=False
        ishome=False
        if "WORK" in types: iswork=True
        if "HOME" in types: ishome=True

        if len(types)==0 or types==["PREF"]: iswork=True # special case when nothing else is specified
    
        
        value=phonenumber.normalise(value)
        if iswork and voice:
            self._setgroupvalue(result,
                           "phone", {"type": "business", "number": value},
                           group, preferred)
        if ishome and voice:
            self._setgroupvalue(result,
                           "phone", {"type": "home", "number": value},
                           group, preferred)
        if not iswork and not ishome and "FAX" in types:
            # fax without explicit work or home
            self._setgroupvalue(result,
                           "phone", {"type": "fax", "number": value},
                           group, preferred)
        else:
            if iswork and "FAX" in types:
                self._setgroupvalue(result, "phone",
                               {"type": "business fax", "number": value},
                               group, preferred)
            if ishome and "FAX" in types:
                self._setgroupvalue(result, "phone",
                               {"type": "home fax", "number": value},
                               group, preferred)
        if "CELL" in types:
            self._setgroupvalue(result,
                           "phone", {"type": "cell", "number": value},
                           group, preferred)
        if "PAGER" in types:
            self._setgroupvalue(result,
                           "phone", {"type": "pager", "number": value},
                           group, preferred)
        if "DATA" in types:
            self._setgroupvalue(result,
                           "phone", {"type": "data", "number": value},
                           group, preferred)

    def _setgroupvalue(self, result, type, value, group, preferred=False):
        """ Set value of an item of a group
        """
        if group is None:
            # no groups specified
            return self._setvalue(result, type, value, preferred)
        group_type=self._groups.get(group, None)
        if group_type is None:
            # 1st one of the group
            self._groups[group]=[type, value, preferred]
        else:
            if type!=group_type[0]:
                print 'Group',group,'has different types:',type,groups_type[0]
            if preferred:
                group_type[2]=True
            group_type[1].update(value)

    def _setvalue(self, result, type, value, preferred=False):
        if type not in result:
            result[type]=value
            return
        if not preferred:
            result[self._getfieldname(type, result)]=value
            return
        # we need to insert our value at the begining
        values=[value]
        for suffix in [""]+range(2,99):
            if type+str(suffix) in result:
                values.append(result[type+str(suffix)])
            else:
                break
        suffixes=[""]+range(2,len(values)+1)
        for l in range(len(suffixes)):
            result[type+str(suffixes[l])]=values[l]

    def _field_CATEGORIES(self, field, value, result):
        # comma seperated just for fun
        values=self.splitandunquote(value, seperator=",")
        values=[v.replace(";", "").strip() for v in values]  # semi colon is used as seperator in bitpim text field
        values=[v for v in values if len(v)]
        v=result.get('categories', None)
        if v:
            result['categories']=';'.join([v, ";".join(values)])
        else:
            result['categories']=';'.join(values)

    def _field_SOUND(self, field, value, result):
        # comma seperated just for fun
        values=self.splitandunquote(value, seperator=",")
        values=[v.replace(";", "").strip() for v in values]  # semi colon is used as seperator in bitpim text field
        values=[v for v in values if len(v)]
        result[self._getfieldname("ringtones", result)]=";".join(values)
        
    _field_CATEGORY=_field_CATEGORIES  # apple use "category" which is not in the spec

    def _field_ADR(self, field, value, result):
        # work out the type
        preferred=False
        type="business"
        for f in field[1:]:
            if f.startswith("TYPE="):
                ff=f[len("TYPE="):].split(",")
            else: ff=[f]
            for x in ff:
                if x=="HOME":
                    type="home"
                if x=="PREF":
                    preferred=True
        
        value=self.splitandunquote(value)
        pobox=extendedaddress=streetaddress=locality=region=postalcode=country=None
        try:
            pobox=value[0]
            extendedaddress=value[1]
            streetaddress=value[2]
            locality=value[3]
            region=value[4]
            postalcode=value[5]
            country=value[6]
        except IndexError:
            pass
        addr={}
        if pobox is not None and len(pobox):
            addr["pobox"]=pobox
        if extendedaddress is not None and len(extendedaddress):
            addr["street2"]=extendedaddress
        if streetaddress is not None and len(streetaddress):
            addr["street"]=streetaddress
        if locality is not None and len(locality):
            addr["city"]=locality
        if region is not None and len(region):
            addr["state"]=region
        if postalcode is not None and len(postalcode):
            addr["postalcode"]=postalcode
        if country is not None and len(country):
            addr["country"]=country
        if len(addr):
            addr["type"]=type
            self._setvalue(result, "address", addr, preferred)

    def _field_X_PALM(self, field, value, result):
        # handle a few PALM custom fields
        ff=field[0].split(".")
        f0=ff[0]
        f1=ff[1] if len(ff)>1 else ''
        if f0.startswith('X-PALM-CATEGORY') or f1.startswith('X-PALM-CATEGORY'):
            self._field_CATEGORIES(['CATEGORIES'], value, result)
        elif f0=='X-PALM-NICKNAME' or f1=='X-PALM-NICKNAME':
            self._field_NICKNAME(['NICKNAME'], value, result)
        else:
            if __debug__:
                print 'ignoring PALM custom field',field
        
    def _default_field(self, field, value, result):
        ff=field[0].split(".")
        f0=ff[0]
        f1=ff[1] if len(ff)>1 else ''
        if f0.startswith('X-PALM-') or f1.startswith('X-PALM-'):
            self._field_X_PALM(field, value, result)
            return
        elif f0.startswith("X-") or f1.startswith("X-"):
            if __debug__:
                print "ignoring custom field",field
            return
        if __debug__:
            print "no idea what do with"
            print "field",field
            print "value",value[:80]

    def unquote(self, value):
        # ::TODO:: do this properly (deal with all backslashes)
        return value.replace(r"\;", ";") \
               .replace(r"\,", ",") \
               .replace(r"\n", "\n") \
               .replace(r"\r\n", "\r\n") \
               .replace("\r\n", "\n") \
               .replace("\r", "\n")

    def splitandunquote(self, value, seperator=";"):
        # also need a splitandsplitandunquote since some ; delimited fields are then comma delimited

        # short cut for normal case - no quoted seperators
        if value.find("\\"+seperator)<0:
            return [self.unquote(v) for v in value.split(seperator)]

        # funky quoting, do it the slow hard way
        res=[]
        build=""
        v=0
        while v<len(value):
            if value[v]==seperator:
                res.append(build)
                build=""
                v+=1
                continue    
        

            if value[v]=="\\":
                build+=value[v:v+2]
                v+=2
                continue
            build+=value[v]
            v+=1
        if len(build):
            res.append(build)

        return [self.unquote(v) for v in res]

    def version(self):
        "Best guess as to vcard version"
        return self._version

    def origin(self):
        "Best guess as to what program wrote the vcard"
        return self._origin    
        
    def __repr__(self):
        str="Version: %s\n" % (`self.version()`)
        str+="Origin: %s\n" % (`self.origin()`)
        str+=common.prettyprintdict(self._data)
        # str+=`self.lines`
        return str+"\n"

###
###  Outputting functions
###    

# The formatters return a string

def myqpencodestring(value):
    """My own routine to do qouted printable since the builtin one doesn't encode CR or NL!"""
    return quopri.encodestring(value).replace("\r", "=0D").replace("\n", "=0A")

def format_stringv2(value):
    """Return a vCard v2 string.  Any embedded commas or semi-colons are removed."""
    return value.replace("\\", "").replace(",", "").replace(";", "")

def format_stringv3(value):
    """Return a vCard v3 string.  Embedded commas and semi-colons are backslash quoted"""
    return value.replace("\\", "").replace(",", r"\,").replace(";", r"\;")

_string_formatters=(format_stringv2, format_stringv3)

def format_binary(value):
    """Return base 64 encoded string"""
    # encodestring always adds a newline so we have to strip it off
    return base64.encodestring(value).rstrip()

def _is_sequence(v):
    """Determine if v is a sequence such as passed to value in out_line.
    Note that a sequence of chars is not a sequence for our purposes."""
    return isinstance(v, (type( () ), type([])))

def out_line(name, attributes, value, formatter, join_char=";"):
    """Returns a single field correctly formatted and encoded (including trailing newline)

    @param name:  The field name
    @param attributes: A list of string attributes (eg "TYPE=intl,post" ).  Usually
                  empty except for TEL and ADR.  You can also pass in None.
    @param value: The field value.  You can also pass in a list of components which will be
                  joined with join_char such as the 6 components of N
    @param formatter:  The function that formats the value/components.  See the
                  various format_ functions.  They will automatically ensure that
                  ENCODING=foo attributes are added if appropriate"""

    if attributes is None:     attributes=[] # ensure it is a list
    else: attributes=list(attributes[:]) # ensure we work with a copy

    if formatter in _string_formatters:
        if _is_sequence(value):
            qp=False
            for f in value:
                f=formatter(f)
                if myqpencodestring(f)!=f:
                    qp=True
                    break
            if qp:
                attributes.append("ENCODING=QUOTED-PRINTABLE")
                value=[myqpencodestring(f) for f in value]
                
            value=join_char.join(value)
        else:
            value=formatter(value)
            # do the qp test
            qp= myqpencodestring(value)!=value
            if qp:
                value=myqpencodestring(value)
                attributes.append("ENCODING=QUOTED-PRINTABLE")
    else:
        assert not _is_sequence(value)
        if formatter is not None:
            value=formatter(value) # ::TODO:: deal with binary and other formatters and their encoding types

    res=";".join([name]+attributes)+":"
    res+=_line_reformat(value, 70, 70-len(res))
    assert res[-1]!="\n"
    
    return res+"\n"

def _line_reformat(line, width=70, firstlinewidth=0):
    """Takes line string and inserts newlines
    and spaces on following continuation lines
    so it all fits in width characters

    @param width: how many characters to fit it in
    @param firstlinewidth: if >0 then first line is this width.
         if equal to zero then first line is same width as rest.
         if <0 then first line will go immediately to continuation.
         """
    if firstlinewidth==0: firstlinewidth=width
    if len(line)<firstlinewidth:
        return line
    res=""
    if firstlinewidth>0:
        res+=line[:firstlinewidth]
        line=line[firstlinewidth:]
    while len(line):
        res+="\n "+line[:width]
        if len(line)<width: break
        line=line[width:]
    return res

def out_names(vals, formatter, limit=1):
    res=""
    for v in vals[:limit]:
        # full name
        res+=out_line("FN", None, nameparser.formatsimplename(v), formatter)
        # name parts
        f,m,l=nameparser.getparts(v)
        res+=out_line("N", None, (l,f,m,"",""), formatter)
        # nickname
        nn=v.get("nickname", "")
        if len(nn):
            res+=out_line("NICKNAME", None, nn, formatter)
    return res

# Apple uses wrong field name so we do some futzing ...
def out_categories(vals, formatter, field="CATEGORIES"):
    cats=[v.get("category") for v in vals]
    if len(cats):
        return out_line(field, None, cats, formatter, join_char=",")
    return ""

def out_categories_apple(vals, formatter):
    return out_categories(vals, formatter, field="CATEGORY")

# Used for both email and urls. we don't put any limits on how many are output
def out_eu(vals, formatter, field, bpkey):
    res=""
    first=True
    for v in vals:
        val=v.get(bpkey)
        type=v.get("type", "")
        if len(type):
            if type=="business": type="work" # vcard uses different name
            type=type.upper()
            if first:
                type=type+",PREF"
        elif first:
            type="PREF"
        if len(type):
            type=["TYPE="+type+["",",INTERNET"][field=="EMAIL"]] # email also has "INTERNET"
        else:
            type=None
        res+=out_line(field, type, val, formatter)
        first=False
    return res

def out_emails(vals, formatter):
    return out_eu(vals, formatter, "EMAIL", "email")

def out_urls(vals, formatter):
    return out_eu(vals, formatter, "URL", "url")

# fun fun fun
_out_tel_mapping={ 'home': 'HOME',
                   'office': 'WORK',
                   'cell': 'CELL',
                   'fax': 'FAX',
                   'pager': 'PAGER',
                   'data': 'MODEM',
                   'none': 'VOICE'
                   }
def out_tel(vals, formatter):
    # ::TODO:: limit to one type of each number
    phones=['phone'+str(x) for x in ['']+range(2,len(vals)+1)]
    res=""
    first=True
    idx=0
    for v in vals:
        sp=v.get('speeddial', None)
        if sp is None:
            # no speed dial
            res+=out_line("TEL",
                          ["TYPE=%s%s" % (_out_tel_mapping[v['type']], ("", ",PREF")[first])],
                          phonenumber.format(v['number']), formatter)
        else:
            res+=out_line(phones[idx]+".TEL",
                          ["TYPE=%s%s" % (_out_tel_mapping[v['type']], ("", ",PREF")[first])],
                          phonenumber.format(v['number']), formatter)
            res+=out_line(phones[idx]+".X-SPEEDDIAL", None, str(sp), formatter)
            idx+=1
        first=False
    return res

# and addresses
def out_adr(vals, formatter):
    # ::TODO:: limit to one type of each address, and only one org
    res=""
    first=True
    for v in vals:
        o=v.get("company", "")
        if len(o):
            res+=out_line("ORG", None, o, formatter)
        if v.get("type")=="home": type="HOME"
        else: type="WORK"
        type="TYPE="+type+("", ",PREF")[first]
        res+=out_line("ADR", [type], [v.get(k, "") for k in (None, "street2", "street", "city", "state", "postalcode", "country")], formatter)
        first=False
    return res

def out_note(vals, formatter, limit=1):
    return "".join([out_line("NOTE", None, v["memo"], formatter) for v in vals[:limit]])

# Sany SCP-6600 (Katana) support
def out_tel_scp6600(vals, formatter):
    res=""
    _pref=len(vals)>1
    for v in vals:
        res+=out_line("TEL",
                      ["TYPE=%s%s" % ("PREF," if _pref else "",
                                      _out_tel_mapping[v['type']])],
                      phonenumber.format(v['number']), formatter)
        _pref=False
    return res
def out_email_scp6600(vals, formatter):
    res=''
    for _idx in range(min(len(vals), 2)):
        v=vals[_idx]
        if v.get('email', None):
            res+=out_line('EMAIL', ['TYPE=INTERNET'],
                          v['email'], formatter)
    return res
def out_url_scp660(vals, formatter):
    if vals and vals[0].get('url', None):
        return out_line('URL', None, vals[0]['url'], formatter)
    return ''
def out_adr_scp6600(vals, formatter):
    for v in vals:
        if v.get('type', None)=='home':
            _type='HOME'
        else:
            _type='WORK'
        return out_line("ADR", ['TYPE=%s'%_type],
                        [v.get(k, "") for k in (None, "street2", "street", "city", "state", "postalcode", "country")],
                        formatter)
    return ''

# This is the order we write things out to the vcard.  Although
# vCard doesn't require an ordering, it looks nicer if it
# is (eg name first)
_field_order=("names", "wallpapers", "addresses", "numbers", "categories", "emails", "urls", "ringtones", "flags", "memos", "serials")

def output_entry(entry, profile, limit_fields=None):

    # debug build assertion that limit_fields only contains fields we know about
    if __debug__ and limit_fields is not None:
        assert len([f for f in limit_fields if f not in _field_order])==0
    
    fmt=profile["_formatter"]
    io=cStringIO.StringIO()
    io.write(out_line("BEGIN", None, "VCARD", None))
    io.write(out_line("VERSION", None, profile["_version"], None))

    if limit_fields is None:
        fields=_field_order
    else:
        fields=[f for f in _field_order if f in limit_fields]

    for f in fields:
        if f in entry and f in profile:
            func=profile[f]
            # does it have a limit?  (nice scary introspection :-)
            if "limit" in func.func_code.co_varnames[:func.func_code.co_argcount]:
                lines=func(entry[f], fmt, limit=profile["_limit"])
            else:
                lines=func(entry[f], fmt)
            if len(lines):
                io.write(lines)

    io.write(out_line("END", None, "VCARD", fmt))
    return io.getvalue()

profile_vcard2={
    '_formatter': format_stringv2,
    '_limit': 1,
    '_version': "2.1",
    'names': out_names,
    'categories': out_categories,
    'emails': out_emails,
    'urls': out_urls,
    'numbers': out_tel,
    'addresses': out_adr,
    'memos': out_note,
    }

profile_vcard3=profile_vcard2.copy()
profile_vcard3['_formatter']=format_stringv3
profile_vcard3['_version']="3.0"

profile_apple=profile_vcard3.copy()
profile_apple['categories']=out_categories_apple

profile_full=profile_vcard3.copy()
profile_full['_limit']=99999

profile_scp6600=profile_full.copy()
del profile_scp6600['categories']
profile_scp6600.update(
    { 'numbers': out_tel_scp6600,
      'emails': out_email_scp6600,
      'urls': out_url_scp660,
      'addresses': out_adr_scp6600,
      })

profiles={
    'vcard2':  { 'description': "vCard v2.1", 'profile': profile_vcard2 },
    'vcard3':  { 'description': "vCard v3.0", 'profile': profile_vcard3 },
    'apple':   { 'description': "Apple",      'profile': profile_apple  },
    'fullv3':  { 'description': "Full vCard v3.0", 'profile': profile_full},
    'scp6600': { 'description': "Sanyo SCP-6600 (Katana)",
                 'profile': profile_scp6600 },
}
    
    
if __name__=='__main__':

    def _wrap(func):
        try: return func()
        except:
            print common.formatexception()
            sys.exit(1)

    def dump_vcards():
        for vcard in VCards(VFile(common.opentextfile(sys.argv[1]))):
            # pass
            print vcard

    def turn_around():
        p="fullv3"
        if len(sys.argv)==4: p=sys.argv[4]
        print "Using profile", profiles[p]['description']
        profile=profiles[p]['profile']

        d={'result': {}}
        try:
            execfile(sys.argv[1], d,d)
        except UnicodeError:
            common.unicode_execfile(sys.argv[1], d,d)
    
        with file(sys.argv[2], "wt") as f:
            for k in d['result']['phonebook']:
                print >>f, output_entry(d['result']['phonebook'][k], profile)

    if len(sys.argv)==2:
        # import bp
        # bp.profile("vcard.prof", "dump_vcards()")
        _wrap(dump_vcards)
    elif len(sys.argv)==3 or len(sys.argv)==4:
        _wrap(turn_around)
    else:
        print """one arg:  import the named vcard file
two args:  first arg is phonebook/index.idx file,  write back out to arg2 in vcard format
three args: same as two but last arg is profile to use.
     profiles are""", profiles.keys()
