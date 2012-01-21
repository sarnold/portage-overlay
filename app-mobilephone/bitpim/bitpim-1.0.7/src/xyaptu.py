#!/usr/bin/env python

"""
This code is taken from the ASPN Python cookbook.  I have
combined YAPTU and XYAPTU into a single file.  The copyright,
warranty and license remain with the original authors.  Please
consult these two URLs

  - U{http://aspn.activestate.com/ASPN/Python/Cookbook/Recipe/52305}
  - U{http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/162292}

The following changes were made:

  - Removed very lengthy examples from the end (see the above URLs for
    them)
  - Added: setupxcopy() takes the template text and remembers it
  - Added: xcopywithdns() does the copy with supplied DNS (Document Name Space which is
    a dict of variables) and remembered template
    and returns the resulting string
  - Exception handling for statements was added (xyaptu only did it for
    expressions)
  - The default behaviour for exceptions now puts a dump of the exception
    into the generated output as an HTML <!-- --> style comment so you
    can view source to find out what has happened.  My common library
    exception formatter (which also dumps local variables) is used.
  

"""

import sys
import re
import string
import common

## "Yet Another Python Templating Utility, Version 1.2"

# utility stuff to avoid tests in the mainline code
class _nevermatch:
    "Polymorphic with a regex that never matches"
    def match(self, line):
        return None
_never = _nevermatch()     # one reusable instance of it suffices
def identity(string, why):
    "A do-nothing-special-to-the-input, just-return-it function"
    return string
def nohandle(*args):
    "A do-nothing handler that just re-raises the exception"
    raise

# and now the real thing
class copier:
    "Smart-copier (YAPTU) class"
    def copyblock(self, i=0, last=None):
        "Main copy method: process lines [i,last) of block"
        def repl(match, self=self):
            "return the eval of a found expression, for replacement"
            # uncomment for debug: print '!!! replacing',match.group(1)
            expr = self.preproc(match.group(1), 'eval')
            try: return common.strorunicode(eval(expr, self.globals, self.locals))
            except: return common.strorunicode(self.handle(expr))
        block = self.locals['_bl']
        if last is None: last = len(block)
        while i<last:
            line = block[i]
            match = self.restat.match(line)
            if match:   # a statement starts "here" (at line block[i])
                # i is the last line to _not_ process
                stat = match.string[match.end(0):].strip()
                j=i+1   # look for 'finish' from here onwards
                nest=1  # count nesting levels of statements
                while j<last:
                    line = block[j]
                    # first look for nested statements or 'finish' lines
                    if self.restend.match(line):    # found a statement-end
                        nest = nest - 1     # update (decrease) nesting
                        if nest==0: break   # j is first line to _not_ process
                    elif self.restat.match(line):   # found a nested statement
                        nest = nest + 1     # update (increase) nesting
                    elif nest==1:   # look for continuation only at this nesting
                        match = self.recont.match(line)
                        if match:                   # found a contin.-statement
                            nestat = match.string[match.end(0):].strip()
                            stat = '%s _cb(%s,%s)\n%s' % (stat,i+1,j,nestat)
                            i=j     # again, i is the last line to _not_ process
                    j=j+1
                stat = self.preproc(stat, 'exec')
                stat = '%s _cb(%s,%s)' % (stat,i+1,j)
                # for debugging, uncomment...: print "-> Executing: {"+stat+"}"
                try:
                    exec stat in self.globals,self.locals
                except:
                    # not as good as it could be
                    self.ouf.write(str(self.handle(stat,self.locals,self.globals)))
                i=j+1
            else:       # normal line, just copy with substitution
                self.ouf.write(self.regex.sub(repl,line))
                i=i+1
    def __init__(self, regex=_never, dict={},
            restat=_never, restend=_never, recont=_never, 
            preproc=identity, handle=nohandle, ouf=sys.stdout):
        "Initialize self's attributes"
        self.regex   = regex
        self.globals = dict
        self.locals  = { '_cb':self.copyblock }
        self.restat  = restat
        self.restend = restend
        self.recont  = recont
        self.preproc = preproc
        self.handle  = handle
        self.ouf     = ouf
    def copy(self, block=None, inf=sys.stdin):
        "Entry point: copy-with-processing a file, or a block of lines"
        if block is None: block = inf.readlines()
        self.locals['_bl'] = block
        self.copyblock()

##"XYAPTU: Lightweight XML/HTML Document Template Engine for Python"

##__version__ = '1.0.0'
##__author__= [
##  'Alex Martelli (aleax@aleax.it)', 
##  'Mario Ruggier (mario@ruggier.org)'
##]
##__copyright__ = '(c) Python Style Copyright. All Rights Reserved. No Warranty.'
##__dependencies__ = ['YAPTU 1.2, http://aspn.activestate.com/ASPN/Python/Cookbook/Recipe/52305']
##__history__= {
##  '1.0.0' : '2002/11/13: First Released Version',
##}

class xcopier(copier):
  ' xcopier class, inherits from yaptu.copier '
  
  def __init__(self, dns, rExpr=None, rOpen=None, rClose=None, rClause=None, 
               ouf=sys.stdout, dbg=0, dbgOuf=sys.stdout):
    ' set default regular expressions required by yaptu.copier '

    # Default regexps for yaptu delimeters (what xyaptu tags are first converted to)
    # These must be in sync with what is output in self._x2y_translate
    _reExpression = re.compile('_:@([^:@]+)@:_')
    _reOpen       = re.compile('\++yaptu ')
    _reClose      = re.compile('--yaptu')
    _reClause     = re.compile('==yaptu ')
    
    rExpr         = rExpr  or _reExpression
    rOpen         = rOpen  or _reOpen
    rClose        = rClose or _reClose
    rClause       = rClause or _reClause

    # Debugging
    self.dbg = dbg
    self.dbgOuf = dbgOuf
    _preproc = self._preProcess
    if dbg: _preproc = self._preProcessDbg
    
    # Call super init
    copier.__init__(self, rExpr, dns, rOpen, rClose, rClause, 
                    preproc=_preproc, handle=self._handleBadExps, ouf=ouf)


  def xcopy(self, inputText):
    '''
    Converts the value of the input stream (or contents of input filename) 
    from xyaptu format to yaptu format, and invokes yaptu.copy
    '''
    
    # Translate (xyaptu) input to (yaptu) input, and call yaptu.copy()
    from StringIO import StringIO
    yinf = StringIO(self._x2y_translate(inputText))
    self.copy(inf=yinf)
    yinf.close()

  def setupxcopy(self, inputText):
      from StringIO import StringIO
      yinf = StringIO(self._x2y_translate(inputText))
      # we have to build the list since you can only run
      # readline/s once on a file
      self.remembered=[line for line in yinf.readlines()]
      
  def xcopywithdns(self, dns):
      from StringIO import StringIO
      self.globals=dns
      out=StringIO()
      self.ouf=out
      self.copy(self.remembered)
      return out.getvalue()

  def _x2y_translate(self, xStr):
    ' Converts xyaptu markup in input string to yaptu delimeters '
        
    # Define regexps to match xml elements on.
    # The variations (all except for py-expr, py-close) we look for are: 
    # <py-elem code="{python code}" /> | 
    # <py-elem code="{python code}">ignored text</py-elem> | 
    # <py-elem>{python code}</py-elem>
    
    # ${py-expr} | $py-expr | <py-expr code="pvkey" />
    reExpr = re.compile(r'''
      \$\{([^}]+)\} |  # ${py-expr}
      \$([_\w]+) | # $py-expr
      <py-expr\s+code\s*=\s*"([^"]*)"\s*/> |
      <py-expr\s+code\s*=\s*"([^"]*)"\s*>[^<]*</py-expr> |
      <py-expr\s*>([^<]*)</py-expr\s*>
    ''', re.VERBOSE)
    
    # <py-line code="pvkeys=pageVars.keys()"/>
    reLine = re.compile(r'''
      <py-line\s+code\s*=\s*"([^"]*)"\s*/> |
      <py-line\s+code\s*=\s*"([^"]*)"\s*>[^<]*</py-line> |
      <py-line\s*>([^<]*)</py-line\s*>
    ''', re.VERBOSE)
    
    # <py-open code="for k in pageVars.keys():" />
    reOpen = re.compile(r'''
      <py-open\s+code\s*=\s*"([^"]*)"\s*/> |
      <py-open\s+code\s*=\s*"([^"]*)"\s*>[^<]*</py-open\s*> |
      <py-open\s*>([^<]*)</py-open\s*>
    ''', re.VERBOSE)
    
    # <py-clause code="else:" />
    reClause = re.compile(r'''
      <py-clause\s+code\s*=\s*"([^"]*)"\s*/> |
      <py-clause\s+code\s*=\s*"([^"]*)"\s*>[^<]*</py-clause\s*> |
      <py-clause\s*>([^<]*)</py-clause\s*>
    ''', re.VERBOSE)
    
    # <py-close />
    reClose = re.compile(r'''
      <py-close\s*/> |
      <py-close\s*>.*</py-close\s*>
    ''', re.VERBOSE)

    # Call-back functions for re substitutions 
    # These must be in sync with what is expected in self.__init__
    def rexpr(match,self=self): 
      return '_:@%s@:_' % match.group(match.lastindex)
    def rline(match,self=self): 
      return '\n++yaptu %s #\n--yaptu \n' % match.group(match.lastindex)
    def ropen(match,self=self): 
      return '\n++yaptu %s \n' % match.group(match.lastindex)
    def rclause(match,self=self): 
      return '\n==yaptu %s \n' % match.group(match.lastindex)
    def rclose(match,self=self): 
      return '\n--yaptu \n'

    # Substitutions    
    xStr = reExpr.sub(rexpr, xStr)
    xStr = reLine.sub(rline, xStr)
    xStr = reOpen.sub(ropen, xStr)
    xStr = reClause.sub(rclause, xStr)
    xStr = reClose.sub(rclose, xStr)

    # When in debug mode, keep a copy of intermediate template format
    if self.dbg:
      _sep = '====================\n'
      self.dbgOuf.write('%sIntermediate YAPTU format:\n%s\n%s' % (_sep, xStr, _sep))

    return xStr

  # Handle expressions that do not evaluate
  def _handleBadExps(self, s, locals=None, globals=None):
    ' Handle expressions that do not evaluate '
    if self.dbg: 
      self.dbgOuf.write('!!! ERROR: failed to evaluate expression: %s \n' % s)
    res="<!-- EXCEPTION: \nExpression: "+s+"\n"
    res+=common.formatexception()+"\n-->"
    print common.formatexception()
    return res+('***! %s !***' % s)

  # Preprocess code
  def _preProcess(self, s, why):
    ' Preprocess embedded python statements and expressions '
    return self._xmlDecode(s)
  def _preProcessDbg(self, s, why):
    ' Preprocess embedded python statements and expressions '
    self.dbgOuf.write('!!! DBG: %s %s \n' % (s, why))
    return self._xmlDecode(s)
  
  # Decode utility for XML/HTML special characters
  _xmlCodes = [
    ['"', '&quot;'],
    ['>', '&gt;'],
    ['<', '&lt;'],
    ['&', '&amp;'],
  ]
  def _xmlDecode(self, s):
    ' Returns the ASCII decoded version of the given HTML string. '
    codes = self._xmlCodes
    for code in codes:
      s = string.replace(s, code[1], code[0])
    return s
