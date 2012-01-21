#!/usr/bin/env python
### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: protogen.py 4772 2010-01-02 06:10:24Z djpham $

"Generate Python code from packet descriptions"
from __future__ import with_statement
import contextlib
import tokenize
import sys
import token
import cStringIO
import os

class protoerror(Exception):

    def __init__(self, desc, token):
        Exception.__init__(self,desc)
        self.desc=desc
        self.token=token

    def __repr__(self):
        str=self.desc+"\nLine "+`self.token[2][0]`+":\n"
        str+=self.token[4]
        str+=" "*self.token[2][1]+"^\n"
        str+=`self.token[:4]`
        return str

    def __str__(self):
        return self.__repr__()

class protogentokenizer:
    # A section enclosed in %{ ... }%.  One item follows which is the string
    LITERAL="LITERAL"

    # The start of a packet. 
    # Followed by name, generatordict (as a string), userspecced dict (as a string), a comment (or None)
    PACKETSTART="PACKETSTART"

    # End of a packet. Nothing follows
    PACKETEND="PACKETEND"

    # Start of an 'if' section. Followed by condition as string including trailing ':'
    CONDITIONALSTART="CONDITIONALSTART"

    # start if an 'else' or 'elif' section.
    CONDITIONALRESTART="CONDITIONALRESTART"

    # End of an 'if' section.  Nothing follows
    CONDITIONALEND="CONDITIONALEND"

    # An actual field. Followed by name, size [-1 means unknown size], type, generatordict, userspecced dict, comment, modifiers
    FIELD="FIELD"

    # Embedded codes: similar to LITERAL, but defined inside a PACKET.
    CODE="CODE"

    # An assertion (validity check).  Followed by string of assertion expression
    ASSERTION="ASSERTION"

    STATE_TOPLEVEL="STATE_TOPLEVEL"
    STATE_PACKET="STATE_PACKET"
    STATE_CONDITIONAL="STATE_CONDITIONAL"
    
    
    def __init__(self, tokenizer, autogennamebase):
        self.tokenizer=tokenizer
        self.pb=[]  # pushback list from what we are tokenizing
        self.state=[self.STATE_TOPLEVEL] # state stack
        self.packetstack=[] # packets being described stack
        self.resultspb=[] # our results pushback stack
        self.lines=[None] # no zeroth line
        self.autogennamebase=autogennamebase
        self.deferredpackets=[] # used for nested packets

    def _getautogenname(self, line):
        return self.autogennamebase+`line`

    def _lookahead(self, howfar=1):
        "Returns a token howfar ahead"
        assert howfar>=1
        while len(self.pb)<howfar:
            self.pb.append(self._realnext())
        return self.pb[howfar-1]

    def _realnext(self):
        "Gets the next token from our input, ignoring the pushback list"
        while True:
            t=self.tokenizer.next()
            t=(token.tok_name[t[0]],)+t[1:]

            # we grab a copy of any lines we see for the first time
            if len(self.lines)==t[2][0]:
                ll=t[4].split('\n')
                self.lines.extend(ll[:-1])
            elif t[3][0]>len(self.lines):
                # multiline token
                ll=t[4].split('\n')
                ll=ll[:-1]
                for i,l in zip(range(t[2][0],t[3][0]+1), ll):
                    # we may already have the line, hence the conditional
                    if len(self.lines)==i:
                        self.lines.append(l)

            if t[0]=='NL':
                t=('NEWLINE',)+t[1:]
            if t[0]!='COMMENT':
                break
        # print "next:",t
        return t

    def _nextignorenl(self):
        "Gets next token ignoring newlines"
        while True:
            t=self._next()
            if t[0]!='NEWLINE':
                return t

    def _next(self):
        "Gets next token from our input, looking in pushback list"
        if len(self.pb):
            t=self.pb[0]
            self.pb=self.pb[1:]
            return t
        return self._realnext()

    def _consumenl(self):
        "consumes any newlines"
        while True:
            t=self._lookahead()
            if t[0]!='NEWLINE':
                break
            self._next()

    def _getuptoeol(self):
        """Returns everything up to newline as a string.  If end of line has backslash before it then
        next line is returned as well"""
        t=self._lookahead()
        res=self._getline(t[2][0])[t[2][1]:]
        while True:
            while t[0]!='NEWLINE':
                t=self._next()
            if res[-2]!='\\':
                break
            t=self._next()
            res+=self._getline(t[2][0])
        return res

    def _getline(self, line):
        return self.lines[line]
                
    def __iter__(self):
        return self

    def next(self):
        res=None
        if len(self.resultspb):
            res=self.resultspb.pop()
        
        if self.state[-1]==self.STATE_TOPLEVEL:
            if res is not None:
                return res
            
            # any deferred packets?
            if len(self.deferredpackets):
                res=self.deferredpackets[0]
                self.deferredpackets=self.deferredpackets[1:]
                return res
            
            # outermost level in file 
            t=self._lookahead()
            if t[0]=='NEWLINE':
                self._next() # consume
                return self.next()
            if t[0]=='OP' and t[1]=='%':
                return (self.LITERAL, self._getliteral())
            if t[0]=='NAME' and t[1]=='PACKET':
                return self._processpacketheader()
            if t[0]=='ENDMARKER':
                raise StopIteration()
            raise protoerror("Unexpected token", t)

        if self.state[-1]==self.STATE_PACKET or self.state[-1]==self.STATE_CONDITIONAL:
            # describing fields in a packet
            if res is None:
                res=self._processpacketfield()
            # flatten nested packets
            if res[0]==self.PACKETSTART:
                q=[res]
                while True:
                    res=self.next()
                    q.append(res)
                    if res[0]==self.PACKETEND:
                        break
                self.deferredpackets.extend(q)
                return self.next()
            # normal
            return res
            
        raise protoerror("Unexpected state", self._lookahead())

    def _getliteral(self):
        "Returns the section enclosed in %{ ... }%. The %{ and }% must be on lines by themselves."
        t=self._next()
        if t[0]!='OP' or t[1]!='%':
            raise protoerror("Expecting '%{'", t)
        t=self._next()
        if t[0]!='OP' or t[1]!='{':
            raise protoerror("Expecting '%{'", t)
        t=self._next()
        if t[0]!='NEWLINE':
            raise protoerror("Expecting newline", t)
        # now in middle of literal
        res=""
        lastline=-1
        while True:
            t=self._lookahead()
            t2=self._lookahead(2)
            if t[0]=='OP' and t[1]=='%' and \
               t2[0]=='OP' and t2[1]=='}':
                self._next() # consume %
                self._next() # consume }
                t=self._next()
                if t[0]!='NEWLINE':
                    raise protoerror("Expecting newline",t)
                break
            t=self._next()
            res+=t[4]
            lastline=t[2][0]
            while self._lookahead()[2][0]==lastline:
                # consume all tokens on the same line
                self._next()
        return res

    def _getdict(self):
        """Returns a text string representing a dict.  If the next token is
        not a dict start then None is returned"""
        res=None
        t=self._lookahead()
        if t[0]!='OP' or t[1]!="{":
            return res
        res=""
        t=self._next()
        start=t[2]
        mostrecent=t # to aid in debugging
        nest=1
        while nest>0:
            t=self._next()
            if t[0]=='OP' and t[1]=='}':
                nest-=1
                continue
            if t[0]=='OP' and t[1]=='{':
                mostrecent=t
                nest+=1
                continue
            if t[0]=='DEDENT' or t[0]=='INDENT' or t[0]=='ENDMARKER':
                raise protoerror("Unterminated '{'", mostrecent)
            
        end=t[3]
        for line in range(start[0], end[0]+1):
            l=self._getline(line)
            if line==end[0]:
                l=l[:end[1]]
            if line==start[0]:
                l=l[start[1]:]
            res+=l

        return res

    def _processpacketheader(self):
        t=self._next()
        if t[0]!='NAME':
            raise protoerror("expecting 'PACKET'", t)
        thedict=self._getdict()
        t=self._next()
        # class name
        themodifiers=""
        while t[0]=='OP':
            themodifiers+=t[1]
            t=self._next()
        if t[0]!='NAME':
            raise protoerror("expecting packet name", t)
        thename=t[1]
        t=self._next()
        if t[0]!='OP' and t[1]!=':':
            raise protoerror("expecting ':'", t)

        # we now have to see an indent and an option string in either order, with newlines ignored
        thecomment=None
        seenindent=False
        while True:
            t=self._lookahead()
            if t[0]=='NEWLINE':
                self._next()
                continue
            if t[0]=='STRING':
                if thecomment is not None:
                    raise protoerror("Duplicate string comment", t)
                thecomment=self._next()[1]
                continue
            if t[0]=='INDENT':
                if seenindent:
                    raise protoerror("Unexpected repeat indent", t)
                seenindent=True
                self._next()
                continue
            break
        
        if not seenindent:
            raise protoerror("Expecting an indent", t)
        self._consumenl()
        # ok, now pointing to packet data
        self.state.append(self.STATE_PACKET)
        self.packetstack.append( (thename, thedict, thecomment, themodifiers) )
        return self.PACKETSTART, thename, None, thedict, thecomment, themodifiers

    def _processpacketfield(self):
        """Read in one packet field"""
        self._consumenl()
        t=self._lookahead()

        if t[0]=='DEDENT':
            # consume
            self._next() 
            # pop a packet
            x=self.state.pop()
            if x==self.STATE_CONDITIONAL:
                # check if this is an else if elif
                t=self._lookahead()
                if t[0]=='NAME' and t[1] in ('else', 'elif'):
                    self.state.append(self.STATE_CONDITIONAL)
                else:
                    return (self.CONDITIONALEND,)
            else:
                return (self.PACKETEND,)

        if t[0]=='OP' and t[1]=='%':
            # embedded codes
            return self.CODE, self._getliteral()

        # Size
        if t[0]=='NUMBER':
            self._next()
            thesize=int(t[1])
        elif t[0]=='OP' and t[1]=='*':
            self._next()
            thesize=-1
        elif t[0]=='NAME' and t[1].upper()=='P':
            self._next()
            thesize='P'
        elif t[0]=='NAME' and t[1].upper()=='A':
            self._next()
            return self.ASSERTION, self._getuptoeol()
        elif t[0]=='NAME' and t[1]=='if':
            str=self._getuptoeol()
            self._consumenl()
            t=self._next()
            if t[0]!='INDENT':
                raise protoerror("Expecting an indent after if ...: statement", t)
            self.state.append(self.STATE_CONDITIONAL)
            return (self.CONDITIONALSTART, str)
        elif t[0]=='NAME' and t[1] in ('elif', 'else'):
            str=self._getuptoeol()
            self._consumenl()
            t=self._next()
            if t[0]!='INDENT':
                raise protoerror("Expecting an indent after else: or elif ...: statement", t)
            if self.state[-1]!=self.STATE_CONDITIONAL:
                raise protoerror('An if must precede an else or elif.', t)
            return (self.CONDITIONALRESTART, str)
        else:
            raise protoerror("Expecting field size as an integer, *, P, A or 'if' statement", t)

        # Type
        t=self._next()
        if t[0]!='NAME':
            raise protoerror("Expecting field type", t)
        thetype=t[1]

        # a dot and another type (first was module)?
        t=self._lookahead()
        if t[0]=='OP' and t[1]=='.':
            self._next()
            t=self._next()
            if t[0]!='NAME':
                raise protoerror("Expecting a name after . in field type", t)
            thetype+="."+t[1]

        # Optional dict
        thedict=self._getdict()

        # Name
        themodifiers=""
        t=self._next()
        while t[0]=='OP':
            themodifiers+=t[1]
            t=self._next()
        thevisible=t[0]=='NAME'
        if thevisible:
            thename=t[1]
        else:
            # Anonymous, invisible field
            thename=self._getautogenname(t[2][0])

        # A colon (anonymous inner struct), newline, or string description
        thedesc=None
        t=self._lookahead()
        if t[0]=='OP' and t[1]==':':
            # consume :
            self._next()

            seenindent=False

            # optional newline
            self._consumenl()
            # optional description
            t=self._lookahead()
            if t[0]=='STRING':
                thedesc=t[1]
                t=self._next()
            elif t[0]=='INDENT':
                seenindent=True
                self._next()
            # optional newline
            self._consumenl()
            # there should be an indent
            if not seenindent:
                t=self._next()
                if t[0]!='INDENT':
                    raise protoerror("Expected an indent after : based field", t)
                
            # put new packet on results pushback
            autoclass=self._getautogenname(t[2][0])
            self.resultspb.append( (self.PACKETSTART, autoclass, None, None, "'Anonymous inner class'", "") )
            self.state.append(self.STATE_PACKET)

            return self.FIELD, thename, thesize, thetype, "{'elementclass': "+autoclass+"}", \
                   thedict, thedesc, themodifiers, thevisible
        
        # optional string
        if t[0]=='STRING':
            thedesc=t[1]
            self._next()
        # optional newline
        self._consumenl()
        # the string this time on the next line?
        if thedesc is None:
            t=self._lookahead()
            if t[0]=='STRING':
                thedesc=t[1]
                self._next()
                self._consumenl()
        # return what have digested ..
        return self.FIELD, thename, thesize, thetype, None, thedict, thedesc,\
               themodifiers, thevisible

def indent(level=1):
    return "    "*level


class codegen:
    def __init__(self, tokenizer):
        self.tokenizer=tokenizer

    def gencode(self):
        tokens=self.tokenizer
        out=cStringIO.StringIO()
        
        print >>out, "# THIS FILE IS AUTOMATICALLY GENERATED.  EDIT THE SOURCE FILE NOT THIS ONE"

        for t in tokens:
            if t[0]==tokens.LITERAL:
                out.write(t[1])
                continue
            if t[0]==tokens.PACKETSTART:
                classdetails=t
                classfields=[]
                classcodes=[]
                continue
            if t[0]==tokens.PACKETEND:
                self.genclasscode(out, classdetails, classfields, classcodes)
                continue
            if t[0]==tokens.CODE:
                classcodes.append(t)
            else:
                classfields.append(t)

        return out.getvalue()

    def genclasscode(self, out, namestuff, fields, codes):
        classname=namestuff[1]
        tokens=self.tokenizer
        _read_only='-' in namestuff[5]
        print >>out, "class %s(BaseProtogenClass):" % (classname,)
        if namestuff[4] is not None:
            print >>out, indent()+namestuff[4]
        if _read_only:
            print >>out, indent(1)+"# Read-From-Buffer-Only Class"
        # fields
        fieldlist=[f[1] for f in fields if f[0]==tokens.FIELD and f[8]]

        print >>out, indent(1)+"__fields="+`fieldlist`
        print >>out, ""


        # Constructor
        print >>out, indent()+"def __init__(self, *args, **kwargs):"
        print >>out, indent(2)+"dict={}"
        if namestuff[2] is not None:
            print >>out, indent(2)+"# Default generator arguments"
            print >>out, indent(2)+"dict.update("+namestuff[2]+")"
        if namestuff[3] is not None:
            print >>out, indent(2)+"# User specified arguments in the packet description"
            print >>out, indent(2)+"dict.update("+namestuff[3]+")"
        print >>out, indent(2)+"# What was supplied to this function"
        print >>out, indent(2)+"dict.update(kwargs)"
        print >>out, indent(2)+"# Parent constructor"
        print >>out, indent(2)+"super(%s,self).__init__(**dict)"%(namestuff[1],)
        print >>out, indent(2)+"if self.__class__ is %s:" % (classname,)
        print >>out, indent(3)+"self._update(args,dict)"
        print >>out, "\n"
        # getfields
        print >>out, indent()+"def getfields(self):"
        print >>out, indent(2)+"return self.__fields"
        print >>out, "\n"
        # update function
        print >>out, indent()+"def _update(self, args, kwargs):"
        print >>out, indent(2)+"super(%s,self)._update(args,kwargs)"%(namestuff[1],)
        print >>out, indent(2)+"keys=kwargs.keys()"
        print >>out, indent(2)+"for key in keys:"
        print >>out, indent(3)+"if key in self.__fields:"
        print >>out, indent(4)+"setattr(self, key, kwargs[key])"
        print >>out, indent(4)+"del kwargs[key]"
        print >>out, indent(2)+"# Were any unrecognized kwargs passed in?"
        print >>out, indent(2)+"if __debug__:"
        print >>out, indent(3)+"self._complainaboutunusedargs(%s,kwargs)" % (namestuff[1],)
        # if only field, pass stuff on to it
        if len(fields)==1:
            print >>out, indent(2)+"if len(args):"
            # we can't use makefield as we have to make a new dict
            d=[]
            if f[2]>=0:
                d.append("{'sizeinbytes': "+`f[2]`+"}")
            for xx in 4,5:
                if f[xx] is not None:
                    d.append(f[xx])
            for dd in d: assert dd[0]=="{" and dd[-1]=='}'
            d=[dd[1:-1] for dd in d]
            print >>out, indent(3)+"dict2={%s}" % (", ".join(d),)
            print >>out, indent(3)+"dict2.update(kwargs)"
            print >>out, indent(3)+"kwargs=dict2"
            print >>out, indent(3)+"self.__field_%s=%s(*args,**dict2)" % (f[1],f[3])
        # else error if any args
        else:
            print >>out, indent(2)+"if len(args): raise TypeError('Unexpected arguments supplied: '+`args`)"
        print >>out, indent(2)+"# Make all P fields that haven't already been constructed"
        for f in fields:
            if f[0]==tokens.FIELD and f[2]=='P':
##                print >>out, indent(2)+"if getattr(self, '__field_"+f[1]+"', None) is None:"
                print >>out, indent(2)+"try: self.__field_"+f[1]
                print >>out, indent(2)+"except:"
                self.makefield(out, 3, f)

        print >>out, "\n"

        # Write to a buffer
        i=2
        print >>out, indent()+"def writetobuffer(self,buf,autolog=True,logtitle=\"<written data>\"):"
        print >>out, indent(i)+"'Writes this packet to the supplied buffer'"
        if _read_only:
            print >>out, indent(i)+"raise NotImplementedError"
        else:
            print >>out, indent(i)+"self._bufferstartoffset=buf.getcurrentoffset()"
            for f in fields:
                if f[0]==tokens.FIELD and f[2]!='P':
                    if '+' in f[7]:
                        print >>out, indent(i)+"try: self.__field_%s" % (f[1],)
                        print >>out, indent(i)+"except:"
                        self.makefield(out, i+1, f, isreading=False)
                    print >>out, indent(i)+"self.__field_"+f[1]+".writetobuffer(buf)"
                elif f[0]==tokens.CONDITIONALSTART:
                    print >>out, indent(i)+f[1]
                    i+=1
                elif f[0]==tokens.CONDITIONALRESTART:
                    print >>out, indent(i-1)+f[1]
                elif f[0]==tokens.CONDITIONALEND:
                    i-=1
            assert i==2
            print >>out, indent(2)+"self._bufferendoffset=buf.getcurrentoffset()"
            print >>out, indent(2)+"if autolog and self._bufferstartoffset==0: self.autologwrite(buf, logtitle=logtitle)"
        print >>out, "\n"
                
        # Read from a buffer
        print >>out, indent()+"def readfrombuffer(self,buf,autolog=True,logtitle=\"<read data>\"):"
        print >>out, indent(2)+"'Reads this packet from the supplied buffer'"
        i=2
        print >>out, indent(2)+"self._bufferstartoffset=buf.getcurrentoffset()"
        print >>out, indent(2)+"if autolog and self._bufferstartoffset==0: self.autologread(buf, logtitle=logtitle)"
        for f in fields:
            if f[0]==tokens.FIELD:
                if f[2]=='P':
                    continue
                if _read_only and not f[8]:
                    # anonymous field, use temp field instead
                    print >>out, indent(i)+self._maketempfieldstr(f)+".readfrombuffer(buf)"
                else:
                    self.makefield(out, i, f)
                    print >>out, indent(i)+"self.__field_%s.readfrombuffer(buf)" % (f[1],)
            elif f[0]==tokens.CONDITIONALSTART:
                print >>out, indent(i)+f[1]
                i+=1
            elif f[0]==tokens.CONDITIONALRESTART:
                print >>out, indent(i-1)+f[1]
            elif f[0]==tokens.CONDITIONALEND:
                i-=1
        assert i==2
        print >>out, indent(2)+"self._bufferendoffset=buf.getcurrentoffset()"
        print >>out, "\n"

        # Setup each field as a property
        for f in fields:
            if f[0]==tokens.FIELD and f[8]:
                # get
                print >>out, indent()+"def __getfield_%s(self):" % (f[1],)
                if '+' in f[7]:
                    print >>out, indent(2)+"try: self.__field_%s" % (f[1],)
                    print >>out, indent(2)+"except:"
                    self.makefield(out, 3, f)
                print >>out, indent(2)+"return self.__field_%s.getvalue()\n" % (f[1],)
                # set
                print >>out, indent()+"def __setfield_%s(self, value):" % (f[1],)
                print >>out, indent(2)+"if isinstance(value,%s):" % (f[3],)
                print >>out, indent(3)+"self.__field_%s=value" % (f[1],)
                print >>out, indent(2)+"else:"
                self.makefield(out, 3, f, "value,", isreading=False)
                print >>out, ""
                # del
                print >>out, indent()+"def __delfield_%s(self): del self.__field_%s\n" % (f[1], f[1])
                # Make it a property
                print >>out, indent()+"%s=property(__getfield_%s, __setfield_%s, __delfield_%s, %s)\n" % (f[1], f[1], f[1], f[1], f[6])
                if '++' in f[7]:
                    # allow setting attributes
                    print >>out, indent()+"def ss_pb_count_respset_%s_attr(self, **kwargs):"%f[1]
                    print >>out, indent(2)+"self.%s"%f[1]
                    print >>out, indent(2)+"self.__field_%s.update(**kwargs)\n"%f[1]

        # we are a container
        print >>out, indent()+"def iscontainer(self):"
        print >>out, indent(2)+"return True\n"

        print >>out, indent()+"def containerelements(self):"
        i=2
        _pass_flg= { i: True }
        for f in fields:
            if f[0]==tokens.FIELD and f[8]:
                print >>out, indent(i)+"yield ('%s', self.__field_%s, %s)" % (f[1], f[1], f[6])
                _pass_flg[i]=False
            elif f[0]==tokens.CONDITIONALSTART:
                print >>out, indent(i)+f[1]
                _pass_flg[i]=False
                i+=1
                _pass_flg[i]=True
            elif f[0]==tokens.CONDITIONALRESTART:
                if _pass_flg[i]:
                    print >>out, indent(i)+"pass"
                else:
                    _pass_flg[i]=True
                print >>out, indent(i-1)+f[1]
            elif f[0]==tokens.CONDITIONALEND:
                if _pass_flg[i]:
                    print >>out, indent(i)+"pass"
                i-=1
        assert i==2

        # generate embeded codes
        print >>out
        for _l in codes:
            print >>out, _l[1]

        print >>out, "\n\n"

    def makefield(self, out, indentamount, field, args="", isreading=True):
        d=[]
        if field[2]!='P' and field[2]>=0:
            d.append("{'sizeinbytes': "+`field[2]`+"}")
        if not (isreading and '*' in field[7]):
            for xx in 4,5:
                if field[xx] is not None:
                    d.append(field[xx])

        for dd in d:
            assert dd[0]=='{' and dd[-1]=='}'

        if len(d)==0:
            print >>out, indent(indentamount)+"self.__field_%s=%s(%s)" % (field[1], field[3], args)
            return

        d=[dd[1:-1] for dd in d]
        dd="{"+", ".join(d)+"}"
        print >>out, indent(indentamount)+"self.__field_%s=%s(%s**%s)" % (field[1], field[3], args, dd)

    def _maketempfieldstr(self, field, args='', isreading=True):
        # create and return string that creates a temporary field
        d=[]
        if field[2]!='P' and field[2]>=0:
            d.append("{'sizeinbytes': "+`field[2]`+"}")
        if not (isreading and '*' in field[7]):
            for xx in 4,5:
                if field[xx] is not None:
                    d.append(field[xx])

        for dd in d:
            assert dd[0]=='{' and dd[-1]=='}'

        if len(d)==0:
            return "%s(%s)" % (fields[3], args)

        d=[dd[1:-1] for dd in d]
        dd="{"+", ".join(d)+"}"
        return "%s(%s**%s)" % (field[3], args, dd)


def processfile(inputfilename, outputfilename):
    print "Processing",inputfilename,"to",outputfilename
    fn=os.path.basename(outputfilename)
    fn=os.path.splitext(fn)[0]
    with contextlib.nested(file(inputfilename, "rtU"),
                           file(outputfilename, "wt")) as (f, f2):
        tokens=tokenize.generate_tokens(f.readline)
        tt=protogentokenizer(tokens, "_gen_"+fn+"_")
        cg=codegen(tt)
        f2.write(cg.gencode())

if __name__=='__main__':
    if len(sys.argv)>3 or (len(sys.argv)==2 and sys.argv[1]=="--help"):
        print "protogen                compiles all .p files in this directory to .py"
        print "protogen foo.p          compiles foo.p to foo.py"
        print "protogen foo.p bar.py   compiles foo.p to bar.py"
        sys.exit(1)
    elif len(sys.argv)==3:
        processfile(sys.argv[1], sys.argv[2])
    elif len(sys.argv)==2:
        processfile(sys.argv[1], sys.argv[1]+"y")
    elif len(sys.argv)==1:
        import glob
        for f in glob.glob("*.p"):
            processfile(f, f+"y")
        for f in glob.glob("phones/*.p"):
            processfile(f, f+"y")

