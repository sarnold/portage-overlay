### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: guihelper.py 1638 2004-10-07 03:21:09Z n9yty $

"""Various convenience functions and widgets to assist the gui"""

import time
import os
import sys
import StringIO
import traceback


import wx

# some library routines
def IsMSWindows():
    """Are we running on Windows?

    @rtype: Bool"""
    return wx.Platform=='__WXMSW__'

def IsGtk():
    """Are we running on GTK (Linux)

    @rtype: Bool"""
    return wx.Platform=='__WXGTK__'

def IsMac():
    """Are we running on Mac

    @rtype: Bool"""
    return wx.Platform=='__WXMAC__'

class LogWindow(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self,parent, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        self.tb=wx.TextCtrl(self, 1, style=wx.TE_MULTILINE|wx.TE_RICH2|wx.NO_FULL_REPAINT_ON_RESIZE|wx.TE_DONTWRAP|wx.TE_READONLY)
        f=wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL )
        ta=wx.TextAttr(font=f)
        self.tb.SetDefaultStyle(ta)
        self.sizer=wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.tb, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.sizer.Fit(self)
        wx.EVT_IDLE(self, self.OnIdle)
        self.outstandingtext=""

    def Clear(self):
        self.tb.Clear()

    def OnIdle(self,_):
        if len(self.outstandingtext):
            self.tb.AppendText(self.outstandingtext)
            self.outstandingtext=""
            self.tb.ScrollLines(-1)

    def log(self, str):
        now=time.time()
        t=time.localtime(now)
        if len(str)==0 or str[0]=="&": # already has time etc stamps
            self.outstandingtext+=str[1:]+"\r\n"
        else:
            self.outstandingtext+="%d:%02d:%02d.%03d: %s\r\n"  % ( t[3], t[4], t[5],  int((now-int(now))*1000), str)

    def logexception(self, excinfo=None):
        str=formatexception(excinfo)
        self.log(str)


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
                    print >>s,`value`[:160]
               except:
                    print >>s,"(Exception occurred printing value)"
     return s.getvalue()


# Where to find bitmaps etc
if IsMac():
    p=os.getcwd()
else:
    p=sys.path[0]
if p.lower().endswith(".zip"): # zip importer in action
    p=os.path.dirname(p)
resourcedirectory=os.path.join(os.path.abspath(p), "resources")

def getresourcefile(filename):
    """Returns name of file by adding it to resource directory pathname

    No attempt is made to verify the file exists
    @rtype: string
    """
    return os.path.join(resourcedirectory, filename)

def run(*args):
    """Execute the command.

    The path is searched"""
    sl=os.spawnl
    if sys.platform!='win32':
        sl=os.spawnlp
        ret=apply(sl, (os.P_WAIT,args[0])+args)
    else:
        # win98 was fine with above code, winxp just chokes
        # so we call system() instead
        str=""
        for a in args:
            if len(a)==0:
                str+=' ""'
            elif a.find(' ')>=0:
                str+=' "'+a+'"'
            else:
                str+=" "+a
        str=str[1:] # remove first space
        # If you ever wanted proof how idiotic windows is, here it is
        # if there is a value enclosed in double quotes, it is
        # taken as the window title, even if it comes after all
        # the switches, so i have to supply one, otherwise it mistakes
        # the command to run as the window title
        ret=os.system('start /b /wait "%s" %s' % (args[0], str))
    return ret
