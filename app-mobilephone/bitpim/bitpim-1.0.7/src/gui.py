### BITPIM
###
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: gui.py 4768 2009-11-06 02:17:29Z hjelmn $

"""The main gui code for BitPim""" 

# System modules
from __future__ import with_statement
import contextlib
import thread, threading
import Queue
import time
import os
import cStringIO
import zipfile
import re
import sys
import shutil
import types
import datetime
import sha
import codecs

# wx modules
import wx
import wx.lib.colourdb
import wx.html

# my modules
import guiwidgets
import common
import version
import helpids
import comdiagnose
import phonebook
import importexport
import guihelper
import bphtml
import bitflingscan
import update
import phoneinfo
import phone_detect
import phone_media_codec
import pubsub
import phones.com_brew as com_brew
import auto_sync
import phone_root
import playlist
import fileview
import data_recording
import analyser
import t9editor
import newdb_wiz
import bp_config

if guihelper.IsMSWindows():
    import win32api
    import win32con
    import win32gui
    import msvcrt
else:
    import fcntl

###
### Used to check our threading
###
mainthreadid=thread.get_ident()
helperthreadid=-1 # set later

###
### Used to handle Task Bar Icon feature (Windows only)
###
if guihelper.IsMSWindows():
    class TaskBarIcon(wx.TaskBarIcon):
        def __init__(self, mw):
            super(TaskBarIcon, self).__init__()
            self.mw=mw
            self._set_icon()
            wx.EVT_TASKBAR_LEFT_DCLICK(self, self.OnDclkRestore)

        def _create_menu(self):
            _menu=wx.Menu()
            _id=wx.NewId()
            if self.mw.IsIconized():
                _menu.Append(_id, 'Restore')
                wx.EVT_MENU(self, _id, self.OnRestore)
            else:
                _menu.Append(_id, 'Minimize')
                wx.EVT_MENU(self, _id, self.OnMinimize)
            _menu.AppendSeparator()
            _id=wx.NewId()
            _menu.Append(_id, 'Close')
            wx.EVT_MENU(self, _id, self.OnClose)
            return _menu

        def _set_icon(self):
            _icon=wx.Icon(guihelper.getresourcefile('bitpim.ico'),
                          wx.BITMAP_TYPE_ICO)
            if _icon.Ok():
                self.SetIcon(_icon, 'BitPim')

        def CreatePopupMenu(self):
            return self._create_menu()
        def OnDclkRestore(self, _):
            self.mw.Iconize(False)
            wx.PostEvent(self.mw, wx.IconizeEvent(self.mw.GetId(), False))
        def OnRestore(self, _):
            self.mw.Iconize(False)
        def OnMinimize(self, _):
            self.mw.Iconize(True)
        def OnClose(self, _):
            self.RemoveIcon()
            self.mw.Close()

###
### Implements a nice flexible callback object
###

class Callback:
    "Callback class.  Extra arguments can be supplied at call time"
    def __init__(self, method, *args, **kwargs):
        if __debug__:
            global mainthreadid
            assert mainthreadid==thread.get_ident()
        self.method=method
        self.args=args
        self.kwargs=kwargs

    def __call__(self, *args, **kwargs):
        if __debug__:
            global mainthreadid
            assert mainthreadid==thread.get_ident()
        d=self.kwargs.copy()
        d.update(kwargs)
        apply(self.method, self.args+args, d)

class Request:
    def __init__(self, method, *args, **kwargs):
        # created in main thread
        if __debug__:
            global mainthreadid
            assert mainthreadid==thread.get_ident()
        self.method=method
        self.args=args
        self.kwargs=kwargs

    def __call__(self, *args, **kwargs):
        # called in helper thread
        if __debug__:
            global helperthreadid
            assert helperthreadid==thread.get_ident()
        d=self.kwargs.copy()
        d.update(kwargs)
        return apply(self.method, self.args+args, d)
        

###
### Event used for passing results back from helper thread
###

class HelperReturnEvent(wx.PyEvent):
    def __init__(self, callback, *args, **kwargs):
        if __debug__:
            # verify being called in comm worker thread
            global helperthreadid
##            assert helperthreadid==thread.get_ident()
        global EVT_CALLBACK
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_CALLBACK)
        self.cb=callback
        self.args=args
        self.kwargs=kwargs

    def __call__(self):
        if __debug__:
            global mainthreadid
##            assert mainthreadid==thread.get_ident()
        return apply(self.cb, self.args, self.kwargs)

###
### Our helper thread where all the work gets done
###

thesplashscreen=None  # set to non-none if there is one

class MySplashScreen(wx.SplashScreen):
    def __init__(self, app, config):
        self.app=app
        # how long are we going to be up for?
        time=config.ReadInt("splashscreentime", 2500)
        if time>0:
            bmp=guihelper.getbitmap("splashscreen")
            self.drawnameandnumber(bmp)
            wx.SplashScreen.__init__(self, bmp, wx.SPLASH_CENTRE_ON_SCREEN|wx.SPLASH_TIMEOUT,
                                    time,
                                    None, -1)
            wx.EVT_CLOSE(self, self.OnClose)
            self.Show()
            app.Yield(True)
            global thesplashscreen
            thesplashscreen=self
            return
        # timeout is <=0 so don't show splash screen
        self.goforit()

    def drawnameandnumber(self, bmp):
        dc=wx.MemoryDC()
        dc.SelectObject(bmp)
        # where we start writing
        x=23 
        y=40
        # Product name
        if False:
            str=version.name
            dc.SetTextForeground( wx.NamedColour("MEDIUMORCHID4") ) 
            dc.SetFont( self._gimmethedamnsizeirequested(25, wx.ROMAN, wx.NORMAL, wx.NORMAL) )
            w,h=dc.GetTextExtent(str)
            dc.DrawText(str, x, y)
            y+=h+0
        # Version number
        x=58
        y=127
        str=version.versionstring+"-"+version.vendor
        dc.SetTextForeground( wx.NamedColour("MEDIUMBLUE") )
        dc.SetFont( self._gimmethedamnsizeirequested(15, wx.ROMAN, wx.NORMAL, wx.NORMAL) )
        w,h=dc.GetTextExtent(str)
        dc.DrawText(str, x+10, y)
        y+=h+0
        # all done
        dc.SelectObject(wx.NullBitmap)

    def _gimmethedamnsizeirequested(self, ps, family, style, weight):
        # on Linux we have to ask for bigger than we want
        if guihelper.IsGtk():
            ps=ps*1.6
        font=wx.TheFontList.FindOrCreateFont(int(ps), family, style, weight)
        return font

    def goforit(self):
        self.app.makemainwindow()
        
    def OnClose(self, evt):
        self.goforit()
        evt.Skip()

class BitPimExit(Exception):
    pass

class WorkerThreadFramework(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name="BitPim helper")
        self.q=Queue.Queue()

    def setdispatch(self, dispatchto):
        self.dispatchto=dispatchto

    def checkthread(self):
        # Function to verify we are running in the correct
        # thread.  All functions in derived class should call this
        global helperthreadid
        assert helperthreadid==thread.get_ident()
        
    def run(self):
        global helperthreadid
        helperthreadid=thread.get_ident()
        first=1
        while True:
            if not first:
                wx.PostEvent(self.dispatchto, HelperReturnEvent(self.dispatchto.endbusycb))
            else:
                first=0
            item=self.q.get()
            wx.PostEvent(self.dispatchto, HelperReturnEvent(self.dispatchto.startbusycb))
            call=item[0]
            resultcb=item[1]
            ex=None
            res=None
            try:
                res=call()
            except Exception,e:
                ex=e
                if not hasattr(e,"gui_exc_info"):
                    ex.gui_exc_info=sys.exc_info()
                
            wx.PostEvent(self.dispatchto, HelperReturnEvent(resultcb, ex, res))
            if isinstance(ex, BitPimExit):
                # gracefully end this thread!
                break

    def progressminor(self, pos, max, desc=""):
        wx.PostEvent(self.dispatchto, HelperReturnEvent(self.dispatchto.progressminorcb, pos, max, desc))

    def progressmajor(self, pos, max, desc=""):
        wx.PostEvent(self.dispatchto, HelperReturnEvent(self.dispatchto.progressmajorcb, pos, max, desc))

    def progress(self, pos, max, desc=""):
        self.progressminor(pos, max, desc)

    def log(self, str):
        if self.dispatchto.wantlog:
            wx.PostEvent(self.dispatchto, HelperReturnEvent(self.dispatchto.logcb, str))

    def logdata(self, str, data, klass=None, data_type=None):
        if self.dispatchto.wantlog:
            wx.PostEvent(self.dispatchto, HelperReturnEvent(self.dispatchto.logdatacb, str, data, klass,
                                                            data_type))

####
#### Main application class.  Runs the event loop etc
####

# safe mode items
def _notsafefunc(*args, **kwargs):
    raise common.InSafeModeException()

class _NotSafeObject:
    def __getattr__(self, *args):  _notsafefunc()
    def __setattr__(self, *args): _notsafefunc()

_NotSafeObject=_NotSafeObject()

class Event(object):
    """Simple Event class that supports Context Manager"""
    def __init__(self):
        self._event=threading.Event()
    def __enter__(self):
        self._event.set()
    def __exit__(self, exc_type, exc_value, tb):
        self._event.clear()
    def set(self):
        return self._event.set()
    def clear(self):
        return self._event.clear()
    def isSet(self):
        return self._event.isSet()
    def wait(self, timeout=None):
        return self._event.wait(timeout)

EVT_CALLBACK=None
class MainApp(wx.App):
    def __init__(self, argv, config_filename=None):
        self.frame=None
        self.SAFEMODE=False
        codecs.register(phone_media_codec.search_func)
        self._config_filename=config_filename
        # simple Event object to flag when entering/leaving critical section
        self.critical=Event()
        wx.App.__init__(self, redirect=False,
                        useBestVisual=not guihelper.IsGtk())

    def lock_file(self, filename):
        # if the file can be locked, lock it and return True.
        # return False otherwise.
        try:
            self.lockedfile=file(filename, 'w')
        except IOError:
            # failed to create the file, just bail
            self.lockedfile=None
            return True
        try:
            if guihelper.IsMSWindows():
                msvcrt.locking(self.lockedfile.fileno(),
                               msvcrt.LK_NBLCK, 1)
            else:
                # Linux & Mac
                fcntl.flock(self.lockedfile.fileno(),
                            fcntl.LOCK_EX|fcntl.LOCK_NB)
            return True
        except IOError:
            return False

    def usingsamedb(self):
        # using a simple file locking method
        return not self.lock_file(os.path.join(self.config._path, '.lock'))

    def OnInit(self):
        self.made=False
        # Routine maintenance
        wx.lib.colourdb.updateColourDB()
        
        # Thread stuff
        global mainthreadid
        mainthreadid=thread.get_ident()

        # for help to save prefs
        cfgstr='bitpim'
        self.SetAppName(cfgstr)
        self.SetVendorName(cfgstr)

        # Establish config stuff
        self.config=bp_config.Config(self._config_filename)
        # Check to see if we're the 2nd instance running on the same DB
        if self.usingsamedb():
            guihelper.MessageDialog(None, 'Another copy of BitPim is using the same data dir:\n%s'%self.config._path,
                                    'BitPim Error',
                                    style=wx.OK|wx.ICON_ERROR)
            return False
        # this is for wx native use, like the freaking help controller !
        self.wxconfig=wx.Config(cfgstr, style=wx.CONFIG_USE_LOCAL_FILE)

        # safe mode is read at startup and can't be changed
        self.SAFEMODE=self.config.ReadInt("SafeMode", False)

        # we used to initialise help here, but in wxPython the stupid help window
        # appeared on Windows just setting it up.  We now defer setting it up
        # until it is needed
        self.helpcontroller=None

        # html easy printing
        self.htmlprinter=bphtml.HtmlEasyPrinting(None, self.config, "printing")

        global EVT_CALLBACK
        EVT_CALLBACK=wx.NewEventType()

        # initialize the Brew file cache
        com_brew.file_cache=com_brew.FileCache(self.config.Read('path', ''))

        # get the splash screen up
        MySplashScreen(self, self.config)

        return True

    def ApplySafeMode(self):
        # make very sure we are in safe mode
        if not self.SAFEMODE:
            return
        if self.frame is None:
            return
        # ensure various objects/functions are changed to not-safe
        objects={self.frame:
                    ( "dlgsendphone", "OnDataSendPhone", "OnDataSendPhoneGotFundamentals", "OnDataSendPhoneResults"),
                 self.frame.tree.filesystemwidget:
                    ( "OnFileDelete", "OnFileOverwrite", "OnNewSubdir", "OnNewFile", "OnDirDelete", "OnRestore"),
                 self.frame.wt:
                    ( "senddata", "writewallpaper", "writeringtone", "writephonebook", "writecalendar", "rmfile",
                      "writefile", "mkdir", "rmdir", "rmdirs", "restorefiles" ),
                 self.frame.phoneprofile:
                    ( "convertphonebooktophone", ),
                 self.frame.phonemodule.Phone:
                    ( "mkdir", "mkdirs", "rmdir", "rmfile", "rmdirs", "writefile", "savegroups", "savephonebook",
                      "savecalendar", "savewallpapers", "saveringtones")
                 }

        for obj, names in objects.iteritems():
            if obj is None:
                continue
            for name in names:
                field=getattr(obj, name, None)
                if field is None or field is _notsafefunc or field is _NotSafeObject:
                    continue
                if isinstance(field, (types.MethodType, types.FunctionType)):
                    newval=_notsafefunc
                else: newval=_NotSafeObject
                setattr(obj, name, newval)

        # remove various menu items if we can find them
        removeids=(guihelper.ID_DATASENDPHONE, guihelper.ID_FV_OVERWRITE, guihelper.ID_FV_NEWSUBDIR,
                   guihelper.ID_FV_NEWFILE, guihelper.ID_FV_DELETE, guihelper.ID_FV_RENAME,
                   guihelper.ID_FV_RESTORE, guihelper.ID_FV_ADD)
        mb=self.frame.GetMenuBar()
        menus=[mb.GetMenu(i) for i in range(mb.GetMenuCount())]
        fsw=self.frame.tree.filesystemwidget
        if  fsw is not None:
            menus.extend( [fsw.list.filemenu, fsw.tree.dirmenu, fsw.list.genericmenu] )
        for menu in menus:
            for id in removeids:
                item=menu.FindItemById(id)
                if item is not None:
                    menu.RemoveItem(item)
        
            
        

##    def setuphelpiwant(self):
##        """This is how the setuphelp code is supposed to be, but stuff is missing from wx"""
##        self.helpcontroller=wx.BestHelpController()
##        self.helpcontroller.Initialize(gethelpfilename)

    def _setuphelp(self):
        """Does all the nonsense to get help working"""
        if guihelper.IsMSWindows():
            self.helpcontroller=True
            return
        elif guihelper.IsMac():
            # we use apple's help mechanism
            from Carbon import AH
            path=os.path.abspath(os.path.join(guihelper.resourcedirectory, "..", "..", ".."))
            # path won't exist if we aren't a bundle
            if  os.path.exists(path) and path.endswith(".app"):
                res=AH.AHRegisterHelpBook(path)
                self.helpcontroller=True
                return

        # Standard WX style help
        # htmlhelp isn't correctly wrapper in wx package
        # Add the Zip filesystem
        wx.FileSystem_AddHandler(wx.ZipFSHandler())
        # Get the help working
        self.helpcontroller=wx.html.HtmlHelpController()
        self.helpcontroller.AddBook(guihelper.gethelpfilename()+".htb")
        self.helpcontroller.UseConfig(self.wxconfig, "help")

        # now context help
        # (currently borken)
        # self.helpprovider=wx.HelpControllerHelpProvider(self.helpcontroller)
        # wx.HelpProvider_Set(provider)

    def displayhelpid(self, id):
        """Display a specific Help Topic"""
        if self.helpcontroller is None:
            self._setuphelp()

        if guihelper.IsMSWindows():
            import win32help
            fname=guihelper.gethelpfilename()+".chm>Help"
            if id is None:
                id=helpids.ID_WELCOME
            # display the topic
            _hwnd=win32gui.GetDesktopWindow()
            win32help.HtmlHelp(_hwnd, fname, win32help.HH_DISPLAY_TOPIC, id)
            # and sync the TOC
            win32help.HtmlHelp(_hwnd, fname, win32help.HH_SYNC, id)

        elif guihelper.IsMac() and self.helpcontroller is True:
            from Carbon import AH
            res=AH.AHGotoPage('BitPim Help', id, None)

        else:
            if id is None:
                self.helpcontroller.DisplayContents()
            else:
                self.helpcontroller.Display(id)

    def makemainwindow(self):
        if self.made:
            return # already been called
        self.made=True
        # make the main frame
        title='BitPim'
        name=self.config.Read('name', None)
        if name:
            title+=' - '+name
        self.frame=MainWindow(None, -1, title, self.config)
        self.frame.Connect(-1, -1, EVT_CALLBACK, self.frame.OnCallback)
        if guihelper.IsMac():
            self.frame.MacSetMetalAppearance(True)

        # make the worker thread
        wt=WorkerThread()
        wt.setdispatch(self.frame)
        wt.setDaemon(1)
        wt.start()
        self.frame.wt=wt
        self.SetTopWindow(self.frame)
        self.SetExitOnFrameDelete(True)
        self.ApplySafeMode()
        wx.CallAfter(self.CheckDetectPhone)
        wx.CallAfter(self.CheckUpdate)
        # double-check the locked file
        if self.lockedfile is None:
            self.usingsamedb()

    update_delta={ 'Daily': 1, 'Weekly': 7, 'Monthly': 30 }
    def CheckUpdate(self):
        if version.isdevelopmentversion():
            return
        if self.frame is None: 
            return
        # tell the frame to do a check-for-update
        update_rate=self.config.Read('updaterate', '')
        if not len(update_rate) or update_rate =='Never':
            return
        last_update=self.config.Read('last_update', '')
        try:
            if len(last_update):
                last_date=datetime.date(int(last_update[:4]), int(last_update[4:6]),
                                        int(last_update[6:]))
                next_date=last_date+datetime.timedelta(\
                    self.update_delta.get(update_rate, 7))
            else:
                next_date=last_date=datetime.date.today()
        except ValueError:
            # month day swap problem
            next_date=last_date=datetime.date.today()
        if datetime.date.today()<next_date:
            return
        self.frame.AddPendingEvent(\
            wx.PyCommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED,
                              guihelper.ID_HELP_UPDATE))

    def CheckDetectPhone(self):
        if self.config.ReadInt('autodetectstart', 0) or self.frame.needconfig:
            self.frame.AddPendingEvent(
                wx.PyCommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED,
                                  guihelper.ID_EDITDETECT))

    def OnExit(self): 
        self.config.Flush()
        # we get stupid messages about daemon threads, and Python's library
        # doesn't provide any way to interrupt them, nor to suppress these
        # messages.  ::TODO:: maybe remove the onexit handler installed by
        # treading._MainThread
        sys.excepthook=donothingexceptionhandler

    def ExitMainLoop(self):
        if guihelper.IsGtk():
            # This hangs for GTK, so what the heck!
            self.OnExit()
            sys.exit(0)
        super(MainApp, self).ExitMainLoop()

# do nothing exception handler
def donothingexceptionhandler(*args):
    pass

# Entry point
def run(argv, kwargs):
    return MainApp(argv, **kwargs).MainLoop()

###
### Main Window (frame) class
###

class MenuCallback:
    "A wrapper to help with callbacks that ignores arguments when invoked"
    def __init__(self, func, *args, **kwargs):
        self.func=func
        self.args=args
        self.kwargs=kwargs
        
    def __call__(self, *args):
        return self.func(*self.args, **self.kwargs)

class MainWindow(wx.Frame):
    def __init__(self, parent, id, title, config):
        wx.Frame.__init__(self, parent, id, title,
                         style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        wx.GetApp().frame=self

        wx.GetApp().htmlprinter.SetParentFrame(self)

        sys.excepthook=Callback(self.excepthook)
        ### plumbing, callbacks        
        self.wt=None # worker thread
        self.progressminorcb=Callback(self.OnProgressMinor)
        self.progressmajorcb=Callback(self.OnProgressMajor)
        self.logcb=Callback(self.OnLog)
        self.logdatacb=Callback(self.OnLogData)
        self.startbusycb=Callback(self.OnBusyStart)
        self.endbusycb=Callback(self.OnBusyEnd)
        self.queue=Queue.Queue()

        ### random variables
        self.exceptiondialog=None
        self.wantlog=1  # do we want to receive log information
        self.config=config
        self.progmajortext=""
        self.__owner_name=''

        self._taskbar=None
        self._taskbar_on_closed=False
        self._close_button=False
        self.__phone_detect_at_startup=False
        self._autodetect_delay=0
        self._dr_rec=None   # Data Recording
        self._dr_play=None  # Data Play back

        ### Status bar

        sb=guiwidgets.MyStatusBar(self)
        self.SetStatusBar(sb)
        self.SetStatusBarPane(sb.GetHelpPane())

        ### Art
        # establish the custom art provider for custom icons
        # this is a global setting, so no need to call it for each toolbar
        wx.ArtProvider.PushProvider(guihelper.ArtProvider())

        # frame icon
        ib=wx.IconBundle()
        ib.AddIconFromFile(guihelper.getresourcefile("bitpim.ico"), wx.BITMAP_TYPE_ANY)
        self.SetIcons(ib)

        ### Menubar

        menuBar = wx.MenuBar()
        menu = wx.Menu()
        # menu.Append(guihelper.ID_FILENEW,  "&New", "Start from new")
        # menu.Append(guihelper.ID_FILEOPEN, "&Open", "Open a file")
        # menu.Append(guihelper.ID_FILESAVE, "&Save", "Save your work")
        menu.Append(guihelper.ID_FILEPRINT, "&Print...", "Print phonebook")
        # menu.AppendSeparator()
        
        # imports
        impmenu=wx.Menu()
        for x, desc, help, func in importexport.GetPhonebookImports():
            if isinstance(func, tuple):
                # submenu
                _submenu=wx.Menu()
                for _id, _desc, _help, _func in func:
                    _submenu.Append(_id, _desc, _help)
                    if _func:
                        wx.EVT_MENU(self, _id, MenuCallback(_func, self))
                impmenu.AppendMenu(x, desc, _submenu, help)
            else:
                impmenu.Append(x, desc, help)
                wx.EVT_MENU(self, x, MenuCallback(func, self) )

        menu.AppendMenu(guihelper.ID_FILEIMPORT, "&Import", impmenu)

        # exports
        expmenu=wx.Menu()
        for x, desc, help, func in importexport.GetPhonebookExports():
            expmenu.Append(x, desc, help)
            wx.EVT_MENU(self, x, MenuCallback(func, self) )

        menu.AppendMenu(guihelper.ID_FILEEXPORT, "&Export", expmenu)

        if not guihelper.IsMac():
            menu.AppendSeparator()
            menu.Append(guihelper.ID_FILEEXIT, "E&xit", "Close down this program")
        menuBar.Append(menu, "&File");
        self.__menu_edit=menu=wx.Menu()
        menu.Append(guihelper.ID_EDITSELECTALL, "&Select All\tCtrl+A", "Select All")
        menu.AppendSeparator()
        menu.Append(guihelper.ID_EDITADDENTRY, "&New...\tCtrl+N", "Add an item")
        menu.Append(guihelper.ID_EDITCOPY, "&Copy\tCtrl+C", "Copy to the clipboard")
        menu.Append(guihelper.ID_EDITPASTE,"&Paste\tCtrl+V", "Paste from the clipboard")
        menu.Append(guihelper.ID_EDITDELETEENTRY, "&Delete", "Delete currently selected entry")
        menu.Append(guihelper.ID_EDITRENAME, "&Rename\tF2", "Rename currently selected entry")
        menu.AppendSeparator()
        menu.Append(guihelper.ID_EDITDETECT,
                    "D&etect Phone", "Auto Detect Phone")
        if guihelper.IsMac():
            wx.App_SetMacPreferencesMenuItemId(guihelper.ID_EDITSETTINGS)
            menu.Append(guihelper.ID_EDITSETTINGS, "Pre&ferences...", "Edit Settings")
        else:
            menu.AppendSeparator()
            menu.Append(guihelper.ID_EDITSETTINGS, "&Settings", "Edit settings")
        menuBar.Append(menu, "&Edit");

        menu=wx.Menu()
        menu.Append(guihelper.ID_DATAGETPHONE, "Get Phone &Data ...", "Loads data from the phone")
        menu.Append(guihelper.ID_DATASENDPHONE, "&Send Phone Data ...", "Sends data to the phone")
        menu.Append(guihelper.ID_DATAHISTORICAL, "&Historical Data ...", "View Current & Historical Data")
        menu.AppendSeparator()
        menu.Append(guihelper.ID_DATANEWDB, 'Create New Storage ...',
                    'Create a New BitPim Storage Area')
        menuBar.Append(menu, "&Data")

        menu=wx.Menu()
        menu.Append(guihelper.ID_VIEWCOLUMNS, "&Columns ...", "Which columns to show")
        menu.AppendCheckItem(guihelper.ID_VIEWPREVIEW, "&Phonebook Preview", "Toggle Phonebook Preview Pane")
        menu.AppendSeparator()
        menu.AppendCheckItem(guihelper.ID_VIEWLOGDATA, "&View protocol logging", "View protocol logging information")
        menu.Append(guihelper.ID_VIEWCLEARLOGS, "Clear &Logs", "Clears the contents of the log panes")
        menu.AppendSeparator()
        menu.AppendCheckItem(guihelper.ID_VIEWFILESYSTEM, "View &Filesystem", "View filesystem on the phone")
        menu.AppendSeparator()
        menu.Append(guihelper.ID_EDITPHONEINFO,
                    "Phone &Info", "Display Phone Information")
        menuBar.Append(menu, "&View")
        # Debug menu
        menu=wx.Menu()
        menu.Append(guihelper.ID_DR_SETTINGS, '&Data Recording',
                    'Data Recording Settings')
##        menu.Append(guihelper.ID_DEBUG_SCRIPT, '&Script',
##                    'Run Debug Script')
        menuBar.Append(menu, "De&bug")
        # Help menu
        menu=wx.Menu()
        if guihelper.IsMac():
            menu.Append(guihelper.ID_HELPHELP, "&Help on this panel", "Help for the panel you are looking at")
        else:
            menu.Append(guihelper.ID_HELPHELP, "&Help", "Help for the panel you are looking at")
        menu.Append(guihelper.ID_HELPTOUR, "&Tour", "Tour of BitPim")
        menu.Append(guihelper.ID_HELPCONTENTS, "&Contents", "Table of contents for the online help")
        menu.Append(guihelper.ID_HELPHOWTOS, "H&owTos", "Help on how to do certain function")
        menu.Append(guihelper.ID_HELPFAQ, "&FAQ", "Frequently Asked Questions")
        menu.Append(guihelper.ID_HELPSUPPORT, "&Support", "Getting support for BitPim")
        menu.Append(guihelper.ID_HELPPHONE, "Your &Phone", "Help on specific phonemodel")
        if version.vendor=='official':
            menu.AppendSeparator()
            menu.Append(guihelper.ID_HELP_UPDATE, "&Check for Update", "Check for any BitPim Update")
        if guihelper.IsMac():
            wx.App_SetMacAboutMenuItemId(guihelper.ID_HELPABOUT)
            menu.Append(guihelper.ID_HELPABOUT, "&About BitPim", "Display program information")
            wx.App_SetMacHelpMenuTitleName("&Help")
            wx.App_SetMacExitMenuItemId(guihelper.ID_FILEEXIT)
        else:
            menu.AppendSeparator()
            menu.Append(guihelper.ID_HELPABOUT, "&About", "Display program information")
        menuBar.Append(menu, "&Help");
        self.SetMenuBar(menuBar)

        ### toolbar
        self.tb=self.CreateToolBar(wx.TB_HORIZONTAL)
        self.tb.SetToolBitmapSize(wx.Size(32,32))
        sz=self.tb.GetToolBitmapSize()

        # add and delete tools
        self.tb.AddSimpleTool(guihelper.ID_DATAGETPHONE, wx.ArtProvider.GetBitmap(guihelper.ART_DATAGETPHONE, wx.ART_TOOLBAR, sz),
                                                "Get Phone Data", "Synchronize BitPim with Phone")
        self.tb.AddLabelTool(guihelper.ID_DATASENDPHONE, "Send Phone Data", wx.ArtProvider.GetBitmap(guihelper.ART_DATASENDPHONE, wx.ART_TOOLBAR, sz),
                                          shortHelp="Send Phone Data", longHelp="Synchronize Phone with BitPim")
        self.tb.AddLabelTool(guihelper.ID_DATAHISTORICAL, "BitPim Help", wx.ArtProvider.GetBitmap(guihelper.ART_DATAHISTORICAL, wx.ART_TOOLBAR, sz),
                                             shortHelp="Historical Data", longHelp="Show Historical Data")
        self.tb.AddSeparator()
        self.tb.AddLabelTool(guihelper.ID_EDITADDENTRY, "Add", wx.ArtProvider.GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_TOOLBAR, sz),
                                          shortHelp="Add", longHelp="Add an item")
        self.tb.AddLabelTool(guihelper.ID_EDITDELETEENTRY, "Delete", wx.ArtProvider.GetBitmap(wx.ART_DEL_BOOKMARK, wx.ART_TOOLBAR, sz),
                                             shortHelp="Delete", longHelp="Delete item")
        self.tb.AddLabelTool(guihelper.ID_EDITPHONEINFO, "Phone Info", wx.ArtProvider.GetBitmap(guihelper.ART_EDITPHONEINFO, wx.ART_TOOLBAR, sz),
                                          shortHelp="Phone Info", longHelp="Show Phone Info")
        self.tb.AddLabelTool(guihelper.ID_EDITDETECT, "Find Phone", wx.ArtProvider.GetBitmap(guihelper.ART_EDITDETECT, wx.ART_TOOLBAR, sz),
                                          shortHelp="Find Phone", longHelp="Find Phone")
        self.tb.AddLabelTool(guihelper.ID_EDITSETTINGS, "Edit Settings", wx.ArtProvider.GetBitmap(guihelper.ART_EDITSETTINGS, wx.ART_TOOLBAR, sz),
                                          shortHelp="Edit Settings", longHelp="Edit BitPim Settings")
        self.tb.AddSeparator()
        self.tb.AddSimpleTool(guihelper.ID_AUTOSYNCEXECUTE, wx.ArtProvider.GetBitmap(guihelper.ART_AUTOSYNCEXECUTE, wx.ART_TOOLBAR, sz),
                                            "Autosync Calendar", "Synchronize Phone Calendar with PC")
        self.tb.AddSeparator()
        self.tb.AddLabelTool(guihelper.ID_HELPHELP, "BitPim Help", wx.ArtProvider.GetBitmap(guihelper.ART_HELPHELP, wx.ART_TOOLBAR, sz),
                                             shortHelp="BitPim Help", longHelp="BitPim Help")


        # You have to make this call for the toolbar to draw itself properly
        self.tb.Realize()

        ### persistent dialogs
        self.dlggetphone=guiwidgets.GetPhoneDialog(self, "Get Data from Phone")
        self.dlgsendphone=guiwidgets.SendPhoneDialog(self, "Send Data to Phone")

        # the splitter
        self.sw=wx.SplitterWindow(self, wx.NewId(), style=wx.SP_3D|wx.SP_NO_XP_THEME|wx.SP_LIVE_UPDATE)

        ### create main tree view
        self.tree = phone_root.PhoneTree(self.sw, self, wx.NewId())

        ### Events we handle
        wx.EVT_MENU(self, guihelper.ID_FILEPRINT, self.tree.OnFilePrint)
        wx.EVT_MENU(self, guihelper.ID_FILEEXIT, self.OnExit)
        wx.EVT_MENU(self, guihelper.ID_EDITSETTINGS, self.OnEditSettings)
        wx.EVT_MENU(self, guihelper.ID_DATAGETPHONE, self.OnDataGetPhone)
        wx.EVT_MENU(self, guihelper.ID_DATASENDPHONE, self.OnDataSendPhone)
        wx.EVT_MENU(self, guihelper.ID_DATAHISTORICAL, self.tree.OnDataHistorical)
        wx.EVT_MENU(self, guihelper.ID_DATANEWDB, self.OnNewDB)
        wx.EVT_MENU(self, guihelper.ID_VIEWCOLUMNS, self.tree.OnViewColumns)
        wx.EVT_MENU(self, guihelper.ID_VIEWPREVIEW, self.tree.OnViewPreview)
        wx.EVT_MENU(self, guihelper.ID_VIEWCLEARLOGS, self.tree.OnViewClearLogs)
        wx.EVT_MENU(self, guihelper.ID_VIEWLOGDATA, self.tree.OnViewLogData)
        wx.EVT_MENU(self, guihelper.ID_VIEWFILESYSTEM, self.tree.OnViewFilesystem)
        wx.EVT_MENU(self, guihelper.ID_EDITADDENTRY, self.tree.OnEditAddEntry)
        wx.EVT_MENU(self, guihelper.ID_EDITDELETEENTRY, self.tree.OnEditDeleteEntry)
        wx.EVT_MENU(self, guihelper.ID_EDITSELECTALL, self.tree.OnEditSelectAll)
        wx.EVT_MENU(self, guihelper.ID_EDITCOPY, self.tree.OnCopyEntry)
        wx.EVT_MENU(self, guihelper.ID_EDITPASTE, self.tree.OnPasteEntry)
        wx.EVT_MENU(self, guihelper.ID_EDITRENAME, self.tree.OnRenameEntry)
        wx.EVT_MENU(self, guihelper.ID_HELPABOUT, self.OnHelpAbout)
        wx.EVT_MENU(self, guihelper.ID_HELPHELP, self.OnHelpHelp)
        wx.EVT_MENU(self, guihelper.ID_HELPCONTENTS, self.OnHelpContents)
        wx.EVT_MENU(self, guihelper.ID_HELPHOWTOS, self.OnHelpHowtos)
        wx.EVT_MENU(self, guihelper.ID_HELPFAQ, self.OnHelpFAQ)
        wx.EVT_MENU(self, guihelper.ID_HELPSUPPORT, self.OnHelpSupport)
        wx.EVT_MENU(self, guihelper.ID_HELPTOUR, self.OnHelpTour)
        wx.EVT_MENU(self, guihelper.ID_HELP_UPDATE, self.OnCheckUpdate)
        wx.EVT_MENU(self, guihelper.ID_HELPPHONE, self.OnHelpPhone)
        wx.EVT_MENU(self, guihelper.ID_EDITPHONEINFO, self.OnPhoneInfo)
        wx.EVT_MENU(self, guihelper.ID_EDITDETECT, self.OnDetectPhone)
        wx.EVT_MENU(self, guihelper.ID_AUTOSYNCSETTINGS, self.OnAutoSyncSettings)
        wx.EVT_MENU(self, guihelper.ID_AUTOSYNCEXECUTE, self.OnAutoSyncExecute)
        wx.EVT_MENU(self, guihelper.ID_DR_SETTINGS, self.OnDataRecording)
        wx.EVT_CLOSE(self, self.OnClose)

        ### Double check our size is meaningful, and make bigger
        ### if necessary (especially needed on Mac and Linux)
        if min(self.GetSize())<250:
            self.SetSize( (640, 480) )

        ### Is config set?
        self.configdlg=guiwidgets.ConfigDialog(self, self)
        self.needconfig=self.configdlg.needconfig()
        self.configdlg.updatevariables()
        
        pos=self.config.ReadInt("mainwindowsplitterpos", 200)
        self.tree.active_panel.OnPreActivate()
        self.sw.SplitVertically(self.tree, self.tree.active_panel, pos)
        self.tree.active_panel.OnPostActivate()
        self.sw.SetMinimumPaneSize(50)
        wx.EVT_SPLITTER_SASH_POS_CHANGED(self, id, self.OnSplitterPosChanged)
        self.tree.Expand(self.tree.root)

        # multiple phones can be added here, although we have to figure out which phone
        # to use in send/get phone data.
        self.tree.CreatePhone("Phone", self.config, self.configpath, "bitpim.db")
        #self.tree.CreatePhone("Different database", self.config, "C:/Documents and Settings/Simon/My Documents/bitpim_old")

        ### Set autosync settings dialog
        self.calenders=importexport.GetCalenderAutoSyncImports()
        self.autosyncsetting=auto_sync.AutoSyncSettingsDialog(self, self)
        self.autosyncsetting.updatevariables()
        self.CloseSplashScreen()

        # add update handlers for controls that are not always available
        wx.EVT_UPDATE_UI(self, guihelper.ID_AUTOSYNCEXECUTE, self.AutosyncUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_DATASENDPHONE, self.tree.DataSendPhoneUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_EDITDELETEENTRY, self.tree.DataDeleteItemUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_EDITADDENTRY, self.tree.DataAddItemUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_DATAHISTORICAL, self.tree.HistoricalDataUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_VIEWCOLUMNS, self.tree.ViewColumnsUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_VIEWPREVIEW, self.tree.ViewPreviewDataUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_FILEPRINT, self.tree.FilePrintDataUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_EDITSELECTALL, self.tree.SelectAllDataUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_EDITCOPY, self.tree.EditCopyUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_EDITPASTE, self.tree.EditPasteUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_EDITRENAME, self.tree.EditRenameUpdateUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_VIEWLOGDATA, self.tree.ViewLogDataUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_VIEWFILESYSTEM, self.tree.ViewFileSystemUIEvent)
        wx.EVT_UPDATE_UI(self, guihelper.ID_HELPPHONE, self.OnHelpPhoneUpdateUI)

        # Retrieve saved settings... Use 90% of screen if not specified
        guiwidgets.set_size("MainWin", self, screenpct=90)

        ### Lets go visible
        self.Show()

        # Show tour on first use
        if self.config.ReadInt("firstrun", True):
            self.config.WriteInt("firstrun", False)
            self.config.Flush()
            wx.CallAfter(self.OnHelpTour)

        # check for device changes
        if guihelper.IsMSWindows():
            if self.config.ReadInt('taskbaricon', 0):
                self._taskbar=TaskBarIcon(self)
                self._taskbar_on_closed=self.config.ReadInt('taskbaricon1', 0)
            # save the old window proc
            self.oldwndproc = win32gui.SetWindowLong(self.GetHandle(),
                                                     win32con.GWL_WNDPROC,
                                                     self.MyWndProc)
        if self._taskbar and self._taskbar.IsOk():
            wx.EVT_ICONIZE(self, self.OnIconize)

        # response to pubsub request
        pubsub.subscribe(self.OnReqChangeTab, pubsub.REQUEST_TAB_CHANGED)
        # setup the midnight timer
        self._setup_midnight_timer()

        if self.IsIconized() and self._taskbar:
            # Ugly hack to force the icon onto the system tray when
            # the app is started minimized !!
            wx.CallAfter(self.Show, False)
        self.GetStatusBar().set_app_status_ready()
        # Linux USB port notification
        if guihelper.IsGtk():
            import comm_notify
            comm_notify.start_server(self)

    def OnSplitterPosChanged(self,_):
        pos=self.sw.GetSashPosition()
        self.config.WriteInt("mainwindowsplitterpos", pos)        

    def SetActivePanel(self, panel):
        w2=self.sw.GetWindow2()
        if w2 is None or w2 is panel:
            return
        panel.OnPreActivate()
        w2.Show(False)
        self.sw.ReplaceWindow(w2, panel)
        panel.Show(True)
        panel.SetFocus()
        panel.OnPostActivate()

    def GetActiveMemoWidget(self):
        return self.tree.GetActivePhone().memowidget

    def GetActiveMediaWidget(self):
        return self.tree.GetActivePhone().mediawidget

    def GetActiveRingerWidget(self):
        return self.tree.GetActivePhone().mediawidget.GetRinger()

    def GetActiveWallpaperWidget(self):
        return self.tree.GetActivePhone().mediawidget.GetWallpaper()

    def GetActiveTodoWidget(self):
        return self.tree.GetActivePhone().todowidget

    def GetActiveCalendarWidget(self):
        return self.tree.GetActivePhone().calendarwidget

    def GetActivePlaylistWidget(self):
        return self.tree.GetActivePhone().playlistwidget

    def GetActivePhonebookWidget(self):
        return self.tree.GetActivePhone().phonewidget

    def GetActiveCallHistoryWidget(self):
        return self.tree.GetActivePhone().callhistorywidget

    def GetActiveSMSWidget(self):
        return self.tree.GetActivePhone().smswidget

    def GetActiveT9EditorWidget(self):
        return self.tree.GetActivePhone().t9editorwidget

    def GetCurrentActiveWidget(self):
        return self.tree.GetActiveWidget()

    def GetActiveDatabase(self):
        return self.tree.GetActivePhone().GetDatabase()

    def UpdateToolbarOnPanelChange(self, add_image, add_help, delete_image, delete_help):
        sz=self.tb.GetToolBitmapSize()
        pos=self.GetToolBar().GetToolPos(guihelper.ID_EDITADDENTRY)
        self.GetToolBar().DeleteTool(guihelper.ID_EDITADDENTRY)
        self.tooladd=self.tb.InsertLabelTool(pos, guihelper.ID_EDITADDENTRY, add_help, 
                                             wx.ArtProvider.GetBitmap(add_image, wx.ART_TOOLBAR, sz),
                                             shortHelp=add_help, longHelp="Add an item")
        pos=self.GetToolBar().GetToolPos(guihelper.ID_EDITDELETEENTRY)
        self.GetToolBar().DeleteTool(guihelper.ID_EDITDELETEENTRY)
        self.tooldelete=self.tb.InsertLabelTool(pos, guihelper.ID_EDITDELETEENTRY, delete_help, 
                                                wx.ArtProvider.GetBitmap(delete_image, wx.ART_TOOLBAR, sz),
                                                shortHelp=delete_help, longHelp="Delete item")
        self.tb.Realize()


    def CloseSplashScreen(self):
        ### remove splash screen if there is one
        global thesplashscreen
        if thesplashscreen is not None:
            try:
        # on Linux this is often already deleted and generates an exception
                thesplashscreen.Show(False)
            except:
                pass
            thesplashscreen=None
            wx.SafeYield(onlyIfNeeded=True)

    def AutosyncUpdateUIEvent(self, event):
        event.Enable(self.autosyncsetting.IsConfigured())

    def OnExit(self,_=None):
        self.Close(True)

    # It has been requested that we shutdown
    def OnClose(self, event):
        if self._taskbar_on_closed and self._close_button and \
           event.CanVeto():
            self._close_button=False
            event.Veto()
            self.Iconize(True)
            return
        if not self.IsIconized():
            self.saveSize()
        if not self.wt:
            # worker thread doesn't exist yet
            self.Destroy()
            return
        # Shutdown helper thread
        self.MakeCall( Request(self.wt.exit), Callback(self.OnCloseResults) )

    def OnCloseResults(self, exception, _):
        assert isinstance(exception, BitPimExit)
        # assume it worked
        if self._taskbar:
            self._taskbar.Destroy()
        self.Destroy()

    def OnIconize(self, evt):
        if evt.Iconized():
            self.Show(False)
        else:
            self.Show(True)
            self.Raise()

    # deal with configuring the phone (commport)
    def OnEditSettings(self, _=None):
        if wx.IsBusy():
            wx.MessageBox("BitPim is busy.  You can't change settings until it has finished talking to your phone.",
                                                         "BitPim is busy.", wx.OK|wx.ICON_EXCLAMATION)
        else:
            # clear the ower's name for manual setting
            self.__owner_name=''
            self.configdlg.ShowModal()
    # about and help

    def OnHelpAbout(self,_):
        guiwidgets.show_about_dlg(self)
        
    def OnHelpHelp(self, _):
        wx.GetApp().displayhelpid(self.GetCurrentActiveWidget().GetHelpID())

    def OnHelpHowtos(self, _):
        wx.GetApp().displayhelpid(helpids.ID_HOWTOS)

    def OnHelpFAQ(self, _):
        wx.GetApp().displayhelpid(helpids.ID_FAQ)

    def OnHelpContents(self, _):
        wx.GetApp().displayhelpid(None)

    def OnHelpSupport(self, _):
        wx.GetApp().displayhelpid(helpids.ID_HELPSUPPORT)

    def OnHelpTour(self, _=None):
        wx.GetApp().displayhelpid(helpids.ID_TOUR)

    def OnHelpPhoneUpdateUI(self, event):
        if self.phonemodule and hasattr(self.phonemodule.Phone, 'desc'):
            event.SetText(self.phonemodule.Phone.desc)
        else:
            event.SetText('Phone')  
        event.Enable(bool(hasattr(self.phonemodule.Phone, "helpid") and\
                     self.phonemodule.Phone.helpid))
    def OnHelpPhone(self, _):
        wx.GetApp().displayhelpid(self.phonemodule.Phone.helpid)
    def DoCheckUpdate(self):
        s=update.check_update()
        if not len(s):
            # Failed to update
            return
        # update our config with the latest version and date
        self.config.Write('latest_version', s)
        self.config.Write('last_update',
                          time.strftime('%Y%m%d', time.localtime()))
        # update the status bar
        self.SetVersionsStatus()

    def OnCheckUpdate(self, _):
        self.DoCheckUpdate()

    def SetPhoneModelStatus(self, stat=guiwidgets.SB_Phone_Set):
        phone=self.config.Read('phonetype', 'None')
        port=self.config.Read('lgvx4400port', 'None')
        if self.__owner_name=='':
            self.GetStatusBar().set_phone_model('%s on %s'%(phone, port),
                                                stat)
        else:
            self.GetStatusBar().set_phone_model('%s %s on %s'%(self.__owner_name, phone, port),
                                                stat)

    def OnPhoneInfo(self, _):
        self.MakeCall(Request(self.wt.getphoneinfo),
                      Callback(self.OnDisplayPhoneInfo))
    def OnDisplayPhoneInfo(self, exception, phone_info):
        if self.HandleException(exception): return
        if phone_info is None:
            # data not available
            dlg=wx.MessageDialog(self, "Phone Info not available",
                             "Phone Info Error", style=wx.OK)
        else:
            dlg=phoneinfo.PhoneInfoDialog(self, phone_info)
        with guihelper.WXDialogWrapper(dlg, True):
            pass

    def OnDetectPhone(self, _=None):
        if wx.IsBusy():
            # main thread is busy, put it on the queue for the next turn
            self.queue.put((self.OnDetectPhone, (), {}), False)
            return
        self.__detect_phone()
    def __detect_phone(self, using_port=None, check_auto_sync=0, delay=0, silent_fail=False):
        self.OnBusyStart()
        self.GetStatusBar().progressminor(0, 100, 'Phone detection in progress ...')
        self.MakeCall(Request(self.wt.detectphone, using_port, None, delay),
                      Callback(self.OnDetectPhoneReturn, check_auto_sync, silent_fail))
    def _detect_this_phone(self, check_auto_sync=0, delay=0, silent_fail=False):
        # (re)detect the current phone model
        self.OnBusyStart()
        self.GetStatusBar().progressminor(0, 100, 'Phone detection in progress ...')
        self.MakeCall(Request(self.wt.detectphone,
                              self.config.Read('lgvx4400port', ''),
                              self.config.Read('phonetype', ''), delay),
                      Callback(self.OnDetectThisPhoneReturn, check_auto_sync,
                               silent_fail))
    def OnDetectThisPhoneReturn(self, check_auto_sync, silent_fail,
                                exception, r):
        if self.HandleException(exception):
            self.OnBusyEnd()
            return
        if r:
            # detected!
            return self.OnDetectPhoneReturn(check_auto_sync, silent_fail,
                                            exception, r)
        # Failed to detect current model, retry for all models
        self.queue.put((self.__detect_phone, (),
                        { 'check_auto_sync': check_auto_sync,
                          'silent_fail': silent_fail }), False)
        self.OnBusyEnd()

    def __get_owner_name(self, esn, style=wx.DEFAULT_DIALOG_STYLE):
        """ retrieve or ask user for the owner's name of this phone
        """
        if esn is None or not len(esn):
            return None
        # esn is found, check if we detected this phone before
        phone_id='phones/'+sha.new(esn).hexdigest()
        phone_name=self.config.Read(phone_id, '')
        with guihelper.WXDialogWrapper(wx.TextEntryDialog(self, "Owner's name:" ,
                                                          "Enter Phone Owner's Name", phone_name),
                                       True) as (dlg, r):
            if r==wx.ID_OK:
                # user gave a name
                phone_name=dlg.GetValue()
                self.config.Write(phone_id, phone_name)
        return phone_name
        
    def OnDetectPhoneReturn(self, check_auto_sync, silent_fail, exception, r):
        self._autodetect_delay=0
        self.OnBusyEnd()
        if self.HandleException(exception): return
        if r is None:
            if not silent_fail:
                self.__owner_name=''
                with guihelper.WXDialogWrapper(wx.MessageDialog(self, 'No phone detected/recognized.\nRun Settings?',
                                                                'Phone Detection Failed', wx.YES_NO),
                                               True) as (_dlg, retcode):
                    if retcode==wx.ID_YES:
                        wx.CallAfter(self.OnEditSettings)
                    self.SetPhoneModelStatus(guiwidgets.SB_Phone_Set)
        else:
            if silent_fail:
                self.__owner_name=None
            else:
                self.__owner_name=self.__get_owner_name(r.get('phone_esn', None))
            if self.__owner_name is None or self.__owner_name=='':
                self.__owner_name=''
            else:
                self.__owner_name+="'s"
            self.config.Write("phonetype", r['phone_name'])
            self.commportsetting=str(r['port'])
            self.wt.clearcomm()
            self.config.Write("lgvx4400port", r['port'])
            self.phonemodule=common.importas(r['phone_module'])
            self.phoneprofile=self.phonemodule.Profile()
            pubsub.publish(pubsub.PHONE_MODEL_CHANGED, self.phonemodule)
            self.SetPhoneModelStatus(guiwidgets.SB_Phone_Detected)
            if not silent_fail:
                if self.__owner_name =='':
                    wx.MessageBox('Found %s on %s'%(r['phone_name'],
                                                    r['port']),
                                                    'Phone Detection', wx.OK)
                else:
                    wx.MessageBox('Found %s %s on %s'%(self.__owner_name,
                                                       r['phone_name'],
                                                       r['port']),
                                                       'Phone Detection', wx.OK)
            if check_auto_sync:
                # see if we should re-sync the calender on connect, do it silently
                self.__autosync_phone(silent=1)

    def AddComm(self, name):
        # A new comm port became available
        print 'New device on port:',name
        # check the new device
        check_auto_sync=auto_sync.UpdateOnConnect(self)
        if name and name.lower()==self.config.Read('lgvx4400port', '').lower():
            _func=self._detect_this_phone
            _args=(check_auto_sync, self._autodetect_delay, True)
        else:
            _func=self.__detect_phone
            _args=(name, check_auto_sync, self._autodetect_delay, True)
        if wx.IsBusy():
            # current phone operation ongoing, queue this
            self.queue.put((_func, _args, {}), False)
        else:
            _func(*_args)

    def RemoveComm(self, name):
        # This comm just went away
        print "Device remove", name
        # device is removed, if it's ours, clear the port
        if name and name.lower()==self.config.Read('lgvx4400port', '').lower():
            if self.wt:
                self.wt.clearcomm()
            self.SetPhoneModelStatus(guiwidgets.SB_Phone_Unavailable)

    def NotifyComm(self, evt):
        if evt.type==evt.add:
            self.AddComm(evt.comm)
        else:
            self.RemoveComm(evt.comm)

    def OnCommNotification(self, evt):
        print 'OnCommNotification'
        if wx.Thread_IsMain():
            self.NotifyComm(evt)
        else:
            wx.CallAfter(self.NotifyComm, evt)

    def WindowsOnDeviceChanged(self, type, name="", drives=[], flag=None):
        if not name.lower().startswith("com"):
            return
        if type=='DBT_DEVICEREMOVECOMPLETE':
            self.RemoveComm(name)
            return
        if type!='DBT_DEVICEARRIVAL':
            # not interested
            return
        self.AddComm(name)

    def MyWndProc(self, hwnd, msg, wparam, lparam):

        if msg==win32con.WM_DEVICECHANGE:
            try:
                type,params=DeviceChanged(wparam, lparam).GetEventInfo()
                self.OnDeviceChanged(type, **params)
                return True
            except:
                # something bad happened! Bail and let Windows handle it
                return win32gui.CallWindowProc(self.oldwndproc, hwnd, msg,
                                               wparam, lparam)

        # Restore the old WndProc.  Notice the use of win32api
        # instead of win32gui here.  This is to avoid an error due to
        # not passing a callable object.
        if msg == win32con.WM_DESTROY:
            win32api.SetWindowLong(self.GetHandle(),
                                   win32con.GWL_WNDPROC,
                                   self.oldwndproc)
        if self._taskbar_on_closed and \
           msg==win32con.WM_NCLBUTTONDOWN and \
           wparam==win32con.HTCLOSE:
            # The system Close Box was clicked!
            self._close_button=True

        # Pass all messages (in this case, yours may be different) on
        # to the original WndProc
        return win32gui.CallWindowProc(self.oldwndproc,
                                       hwnd, msg, wparam, lparam)

    if guihelper.IsMSWindows():
        OnDeviceChanged=WindowsOnDeviceChanged

    def SetVersionsStatus(self):
        current_v=version.version
        latest_v=self.config.Read('latest_version')
        self.GetStatusBar().set_versions(current_v, latest_v)

    def update_cache_path(self):
        com_brew.file_cache.set_path(self.configpath)

    def OnNewDB(self, _):
        newdb_wiz.create_new_db(self, self.config)

    ### 
    ### Main bit for getting stuff from phone
    ###

    def OnDataGetPhone(self,_):
        todo=[]
        dlg=self.dlggetphone
        dlg.UpdateWithProfile(self.phoneprofile)
        if dlg.ShowModal()!=wx.ID_OK:
            return
        self._autodetect_delay=self.phoneprofile.autodetect_delay
        todo.append((self.wt.rebootcheck, "Phone Reboot"))
        wx.GetApp().critical.set()
        self.MakeCall(Request(self.wt.getdata, dlg, todo),
                      Callback(self.OnDataGetPhoneResults))

    def OnDataGetPhoneResults(self, exception, results):
        with wx.GetApp().critical:
            if self.HandleException(exception): return
            self.OnLog(`results.keys()`)
            self.OnLog(`results['sync']`)
            # phonebook
            if results['sync'].has_key('phonebook'):
                v=results['sync']['phonebook']

                print "phonebookmergesetting is",v
                if v=='MERGE': 
                    merge=True
                else:
                    merge=False
                self.GetActivePhonebookWidget().importdata(results['phonebook'], results.get('categories', []), merge, results.get('group_wallpapers', []))

            # wallpaper
            updwp=False # did we update the wallpaper
            if results['sync'].has_key('wallpaper'):
                v=results['sync']['wallpaper']
                if v=='MERGE': raise Exception("Not implemented")
                updwp=True
                self.GetActiveWallpaperWidget().populatefs(results)
                self.GetActiveWallpaperWidget().populate(results)
            # wallpaper-index
            if not updwp and results.has_key('wallpaper-index'):
                self.GetActiveWallpaperWidget().updateindex(results)
            # ringtone
            updrng=False # did we update ringtones
            if results['sync'].has_key('ringtone'):
                v=results['sync']['ringtone']
                if v=='MERGE': raise Exception("Not implemented")
                updrng=True
                self.GetActiveRingerWidget().populatefs(results)
                self.GetActiveRingerWidget().populate(results)
            # ringtone-index
            if not updrng and results.has_key('ringtone-index'):
                self.GetActiveRingerWidget().updateindex(results)            
            # calendar
            if results['sync'].has_key('calendar'):
                v=results['sync']['calendar']
                if v=='MERGE': raise Exception("Not implemented")
                results['calendar_version']=self.phoneprofile.BP_Calendar_Version
                self.GetActiveCalendarWidget().mergedata(results)
    ##            self.GetActiveCalendarWidget().populatefs(results)
    ##            self.GetActiveCalendarWidget().populate(results)
            # memo
            if results['sync'].has_key('memo'):
                v=results['sync']['memo']
                if v=='MERGE': raise Exception("Not implemented")
                self.GetActiveMemoWidget().populatefs(results)
                self.GetActiveMemoWidget().populate(results)
            # todo
            if results['sync'].has_key('todo'):
                v=results['sync']['todo']
                if v=='MERGE': raise NotImplementedError
                self.GetActiveTodoWidget().populatefs(results)
                self.GetActiveTodoWidget().populate(results)
            # SMS
            if results['sync'].has_key('sms'):
                v=results['sync']['sms']
                if v=='MERGE':
                    self.GetActiveSMSWidget().merge(results)
                else:
                    self.GetActiveSMSWidget().populatefs(results)
                    self.GetActiveSMSWidget().populate(results)
            # call history
            if results['sync'].has_key('call_history'):
                v=results['sync']['call_history']
                if v=='MERGE':
                    self.GetActiveCallHistoryWidget().merge(results)
                else:
                    self.GetActiveCallHistoryWidget().populatefs(results)
                    self.GetActiveCallHistoryWidget().populate(results)
            # Playlist
            if results['sync'].has_key(playlist.playlist_key):
                if results['sync'][playlist.playlist_key]=='MERGE':
                    raise NotImplementedError
                self.GetActivePlaylistWidget().populatefs(results)
                self.GetActivePlaylistWidget().populate(results)
            # T9 User DB
            if results['sync'].has_key(t9editor.dict_key):
                if results['sync'][t9editor.dict_key]=='MERGE':
                    raise NotImplementedError
                self.GetActiveT9EditorWidget().populatefs(results)
                self.GetActiveT9EditorWidget().populate(results)
    ###
    ### Main bit for sending data to the phone
    ###
    def OnDataSendPhone(self, _):
        dlg=self.dlgsendphone
        print self.phoneprofile
        dlg.UpdateWithProfile(self.phoneprofile)
        if dlg.ShowModal()!=wx.ID_OK:
            return
        data={}
        convertors=[]
        todo=[]
        funcscb=[]
        
        ### Wallpaper
        v=dlg.GetWallpaperSetting()
        if v!=dlg.NOTREQUESTED:
            merge=True
            if v==dlg.OVERWRITE: merge=False
            if merge:
                want=self.GetActiveWallpaperWidget().SELECTED
            else:
                want=self.GetActiveWallpaperWidget().ALL
            self.GetActiveWallpaperWidget().getdata(data, want)
            todo.append( (self.wt.writewallpaper, "Wallpaper", merge) )
            # funcscb.append( self.wallpaperwidget.populate )

        ### Ringtone
        v=dlg.GetRingtoneSetting()
        if v!=dlg.NOTREQUESTED:
            merge=True
            if v==dlg.OVERWRITE: merge=False
            if merge:
                want=self.GetActiveRingerWidget().SELECTED
            else:
                want=self.GetActiveRingerWidget().ALL
            self.GetActiveRingerWidget().getdata(data, want)
            todo.append( (self.wt.writeringtone, "Ringtone", merge) )
            # funcscb.append( self.ringerwidget.populate )

        ### Calendar
        v=dlg.GetCalendarSetting()
        if v!=dlg.NOTREQUESTED:
            merge=True
            if v==dlg.OVERWRITE: merge=False
            data['calendar_version']=self.phoneprofile.BP_Calendar_Version
            self.GetActiveCalendarWidget().getdata(data)
            todo.append( (self.wt.writecalendar, "Calendar", merge) )

        ### Phonebook
        v=dlg.GetPhoneBookSetting()
        if v!=dlg.NOTREQUESTED:
            if v==dlg.OVERWRITE: 
                self.GetActivePhonebookWidget().getdata(data)
                todo.append( (self.wt.writephonebook, "Phonebook") )
            convertors.append(self.GetActivePhonebookWidget().converttophone)
            # writing will modify serials so we need to update
            funcscb.append(self.GetActivePhonebookWidget().updateserials)

        ### Memo
        v=dlg.GetMemoSetting()
        if v!=dlg.NOTREQUESTED:
            merge=v!=dlg.OVERWRITE
            self.GetActiveMemoWidget().getdata(data)
            todo.append((self.wt.writememo, "Memo", merge))

        ### Todo
        v=dlg.GetTodoSetting()
        if v!=dlg.NOTREQUESTED:
            merge=v!=dlg.OVERWRITE
            self.GetActiveTodoWidget().getdata(data)
            todo.append((self.wt.writetodo, "Todo", merge))

        ### SMS
        v=dlg.GetSMSSetting()
        if v!=dlg.NOTREQUESTED:
            merge=v!=dlg.OVERWRITE
            self.GetActiveSMSWidget().getdata(data)
            todo.append((self.wt.writesms, "SMS", merge))

        ### Playlist
        v=dlg.GetPlaylistSetting()
        if v!=dlg.NOTREQUESTED:
            merge=v!=dlg.OVERWRITE
            self.GetActivePlaylistWidget().getdata(data)
            todo.append((self.wt.writeplaylist, "Playlist", merge))

        ### T9 User DB
        v=dlg.GetT9Setting()
        if v!=dlg.NOTREQUESTED:
            merge=v!=dlg.OVERWRITE
            self.GetActiveT9EditorWidget().getdata(data)
            todo.append((self.wt.writet9, "T9", merge))

        data['reboot_delay']=self.phoneprofile.reboot_delay
        self._autodetect_delay=self.phoneprofile.autodetect_delay
        todo.append((self.wt.rebootcheck, "Phone Reboot"))
        self.MakeCall(Request(self.wt.getfundamentals),
                      Callback(self.OnDataSendPhoneGotFundamentals, data, todo, convertors, funcscb))

    def OnDataSendPhoneGotFundamentals(self,data,todo,convertors, funcscb, exception, results):
        if self.HandleException(exception): return
        data.update(results)
        # call each widget to update fundamentals
        # for widget in self.calendarwidget, self.wallpaperwidget, self.ringerwidget, self.phonewidget:
        #    widget.updatefundamentals(data)
        
        # call convertors
        for f in convertors:
            f(data)

        # Now scribble to phone
        self.MakeCall(Request(self.wt.senddata, data, todo),
                      Callback(self.OnDataSendPhoneResults, funcscb))

    def OnDataSendPhoneResults(self, funcscb, exception, results):
        if self.HandleException(exception): return
        print results.keys()
        for f in funcscb:
            f(results)

    def GetCalendarData(self):
        # return calendar data for export
        d={}
        return self.GetActiveCalendarWidget().getdata(d).get('calendar', {})

        
    def OnAutoSyncSettings(self, _=None):
        if wx.IsBusy():
            with guihelper.WXDialogWrapper(wx.MessageBox("BitPim is busy.  You can't change settings until it has finished talking to your phone.",
                                                         "BitPim is busy.", wx.OK|wx.ICON_EXCLAMATION),
                                           True):
                pass
        else:
            # clear the ower's name for manual setting
            self.__owner_name=''
            self.autosyncsetting.ShowModal()

    def OnAutoSyncExecute(self, _=None):
        if wx.IsBusy():
            wx.MessageBox("BitPim is busy.  You can't run autosync until it has finished talking to your phone.",
                         "BitPim is busy.", wx.OK|wx.ICON_EXCLAMATION)
            return
        self.__autosync_phone()

    def __autosync_phone(self, silent=0):
        r=auto_sync.SyncSchedule(self).sync(self, silent)
        
    # deal with configuring the phone (commport)
    def OnReqChangeTab(self, msg=None):
        if msg is None:
            return
        data=msg.data
        if not isinstance(data, int):
            # wrong data type
            if __debug__:
                raise TypeError
            return

    # Busy handling
    def OnBusyStart(self):
        self.GetStatusBar().set_app_status_busy()
        wx.BeginBusyCursor(wx.StockCursor(wx.CURSOR_ARROWWAIT))

    def OnBusyEnd(self):
        wx.EndBusyCursor()
        self.GetStatusBar().set_app_status_ready()
        self.OnProgressMajor(0,1)
        # fire the next one in the queue
        if not self.queue.empty():
            _q=self.queue.get(False)
            wx.CallAfter(_q[0], *_q[1], **_q[2])

    # progress and logging
    def OnProgressMinor(self, pos, max, desc=""):
        self.GetStatusBar().progressminor(pos, max, desc)

    def OnProgressMajor(self, pos, max, desc=""):
        self.GetStatusBar().progressmajor(pos, max, desc)

    def OnLog(self, str):
        if self.__phone_detect_at_startup:
            return
        str=common.strorunicode(str)
        if data_recording.DR_On:
            data_recording.record(data_recording.DR_Type_Note, str)
        self.tree.lw.log(str)
        if self.tree.lwdata is not None:
            self.tree.lwdata.log(str)
        if str.startswith("<!= "):
            p=str.index("=!>")+3
            guihelper.MessageDialog(self, str[p:], "Alert", style=wx.OK|wx.ICON_EXCLAMATION)
            self.OnLog("Alert dialog closed")
    log=OnLog
    def OnLogData(self, str, data, klass=None, data_type=None):
        if data_recording.DR_On:
            data_recording.record(data_recording.DR_Type_Note, str)
            data_recording.record(data_type or data_recording.DR_Type_Data,
                                data, klass)
        if self.tree.lwdata is not None:
            self.tree.lwdata.logdata(str,data, klass)

    def excepthook(self, type, value, traceback):
        if not hasattr(value, "gui_exc_info"):
            value.gui_exc_info=(type,value,traceback)
        self.HandleException(value)

    def HandleException(self, exception):
        """returns true if this function handled the exception
        and the caller should not do any further processing"""
        if exception is None: return False
        assert isinstance(exception, Exception)
        self.CloseSplashScreen()
        # always close comm connection when we have any form of exception
        if self.wt is not None:
            self.wt.clearcomm()
        text=None
        title=None
        style=None
        # Here is where we turn the exception into something user friendly
        if isinstance(exception, common.CommsDeviceNeedsAttention):
            text="%s: %s" % (exception.device, exception.message)
            title="Device needs attention - "+exception.device
            style=wx.OK|wx.ICON_INFORMATION
            help=lambda _: wx.GetApp().displayhelpid(helpids.ID_DEVICE_NEEDS_ATTENTION)
        elif isinstance(exception, common.CommsOpenFailure):
            text="%s: %s" % (exception.device, exception.message)
            title="Failed to open communications - "+exception.device
            style=wx.OK|wx.ICON_INFORMATION
            help=lambda _: wx.GetApp().displayhelpid(helpids.ID_FAILED_TO_OPEN_DEVICE)
        elif isinstance(exception, common.AutoPortsFailure):
            text=exception.message
            title="Failed to automatically detect port"
            style=wx.OK|wx.ICON_INFORMATION
            help=lambda _: wx.GetApp().displayhelpid(helpids.ID_FAILED_TO_AUTODETECT_PORT)
        elif isinstance(exception, common.HelperBinaryNotFound) and exception.basename=="pvconv":
            text="The Qualcomm PureVoice converter program (%s) was not found.\nPlease see the help. Directories looked in are:\n\n " +\
                  "\n ".join(exception.paths)
            text=text % (exception.fullname,)
            title="Failed to find PureVoice converter"
            style=wx.OK|wx.ICON_INFORMATION
            help=lambda _: wx.GetApp().displayhelpid(helpids.ID_NO_PVCONV)
        elif isinstance(exception, common.PhoneBookBusyException):
            text="The phonebook is busy on your phone.\nExit back to the main screen and then repeat the operation."
            title="Phonebook busy on phone"
            style=wx.OK|wx.ICON_INFORMATION
            help=lambda _: wx.GetApp().displayhelpid(helpids.ID_PHONEBOOKBUSY)
        elif isinstance(exception, common.IntegrityCheckFailed):
            text="The phonebook on your phone is partially corrupt.  Please read the\nhelp for more details on the cause and fix"
            title="IntegrityCheckFailed"
            style=wx.OK|wx.ICON_EXCLAMATION
            help=lambda _: wx.GetApp().displayhelpid(helpids.ID_LG_INTEGRITYCHECKFAILED)
        elif isinstance(exception, common.CommsDataCorruption):
            text=exception.message+"\nPlease see the help."
            title="Communications Error - "+exception.device
            style=wx.OK|wx.ICON_EXCLAMATION
            help=lambda _: wx.GetApp().displayhelpid(helpids.ID_COMMSDATAERROR)
        elif isinstance(exception, com_brew.BrewAccessDeniedException):
            text="Access to the file/directory has been blocked on this phone by the phone provider"
            title="Access Denied"
            style=wx.OK|wx.ICON_EXCLAMATION
            help=lambda _: wx.GetApp().displayhelpid(helpids.ID_BREW_ACCESS_DENIED)
        elif isinstance(exception, common.PhoneStringEncodeException):
            text="Unable to convert the text <%s> into a format your phone can understand, change the text to contain only %s characters" % (exception.string, `exception.codec`)
            title="Text Conversion Error"
            style=wx.OK|wx.ICON_EXCLAMATION
            help=lambda _: wx.GetApp().displayhelpid(helpids.ID_BREW_ACCESS_DENIED)
            
        if text is not None:
            self.OnLog("Error: "+title+"\n"+text)
            with guihelper.WXDialogWrapper(guiwidgets.AlertDialogWithHelp(self,text, title, help, style=style),
                                           True):
                pass
            return True

        if self.exceptiondialog is None:
            self.excepttime=time.time()
            self.exceptcount=0
            self.exceptiondialog=guiwidgets.ExceptionDialog(self, exception)
            try:
                self.OnLog("Exception: "+self.exceptiondialog.getexceptiontext())
            except AttributeError:
                # this can happen if main gui hasn't been built yet
                pass
        else:
            self.exceptcount+=1
            if self.exceptcount<10:
                print "Ignoring an exception as the exception dialog is already up"
                try:
                    self.OnLog("Exception during exception swallowed")
                except AttributeError:
                    # this can happen if main gui hasn't been built yet
                    pass
            return True
            
        self.exceptiondialog.ShowModal()
        self.exceptiondialog.Destroy()
        self.exceptiondialog=None
        return True

    # midnight timer stuff
    def _OnTimer(self, _):
        self.MakeCall(Request(self._pub_timer),
                      Callback(self._OnTimerReturn))

    def _pub_timer(self):
        pubsub.publish(pubsub.MIDNIGHT)

    def _OnTimerReturn(self, exceptions, result):
        self._timer.Start(((3600*24)+1)*1000, True)

    def _setup_midnight_timer(self):
        _today=datetime.datetime.now()
        _timer_val=24*3600-_today.hour*3600-_today.minute*60-_today.second+1
        self._timer=wx.Timer(self)
        wx.EVT_TIMER(self, self._timer.GetId(), self._OnTimer)
        self._timer.Start(_timer_val*1000, True)
        print _timer_val,'seconds till midnight'

    # Data Recording stuff
    def OnDataRecording(self, _):
        with guihelper.WXDialogWrapper(guiwidgets.DRRecFileDialog(self),
                                       True):
            pass

    # plumbing for the multi-threading

    def OnCallback(self, event):
        assert isinstance(event, HelperReturnEvent)
        event()

    def MakeCall(self, request, cbresult):
        assert isinstance(request, Request)
        assert isinstance(cbresult, Callback)
        self.wt.q.put( (request, cbresult) )

    # remember our size and position

    def saveSize(self):
        guiwidgets.save_size("MainWin", self.GetRect())

###
### Container for midi files
###  

#class MidiFileList(wx.ListCtrl):
#    pass




###
###  Class that does all the comms and other stuff in a seperate
###  thread.  
###

class WorkerThread(WorkerThreadFramework):
    def __init__(self):
        WorkerThreadFramework.__init__(self)
        self.commphone=None
        data_recording.register(self.OnDataRecording, self.OnDataRecording,
                                self.OnDataRecording)

    def exit(self):
        if __debug__: self.checkthread()
        for i in range(0,0):
            self.progressmajor(i, 2, "Shutting down helper thread")
            time.sleep(1)
        self.log("helper thread shut down")
        raise BitPimExit("helper thread shutdown")


    def clearcomm(self):
        if self.commphone is None:
            return
        self.commphone.close()
        self.commphone=None
        
        
    def setupcomm(self):
        if __debug__: self.checkthread()
        if self.commphone is None:
            import commport
            if self.dispatchto.commportsetting is None or \
               len(self.dispatchto.commportsetting)==0:
                raise common.CommsNeedConfiguring("Comm port not configured", "DEVICE")

            if self.dispatchto.commportsetting=="auto":
                autofunc=comdiagnose.autoguessports
            else:
                autofunc=None
            comcfg=self.dispatchto.commparams

            name=self.dispatchto.commportsetting
            if name.startswith("bitfling::"):
                klass=bitflingscan.CommConnection
            else:
                klass=commport.CommConnection
                
            comport=klass(self, self.dispatchto.commportsetting, autolistfunc=autofunc,
                          autolistargs=(self.dispatchto.phonemodule,),
                          baud=comcfg['baud'], timeout=comcfg['timeout'],
                          hardwareflow=comcfg['hardwareflow'],
                          softwareflow=comcfg['softwareflow'],
                          configparameters=comcfg)
                
            try:
                self.commphone=self.dispatchto.phonemodule.Phone(self, comport)
            except:
                comport.close()
                raise

    def getfundamentals(self):
        if __debug__: self.checkthread()
        self.setupcomm()
        results={}
        self.commphone.getfundamentals(results)
        return results

    def getdata(self, req, todo):
        if __debug__: self.checkthread()
        self.setupcomm()
        results=self.getfundamentals()
        com_brew.file_cache.esn=results.get('uniqueserial', None)
        willcall=[]
        sync={}
        for i in (
            (req.GetPhoneBookSetting, self.commphone.getphonebook, "Phone Book", "phonebook"),
            (req.GetCalendarSetting, self.commphone.getcalendar, "Calendar", "calendar",),
            (req.GetWallpaperSetting, self.commphone.getwallpapers, "Wallpaper", "wallpaper"),
            (req.GetRingtoneSetting, self.commphone.getringtones, "Ringtones", "ringtone"),
            (req.GetMemoSetting, self.commphone.getmemo, "Memo", "memo"),
            (req.GetTodoSetting, self.commphone.gettodo, "Todo", "todo"),
            (req.GetSMSSetting, self.commphone.getsms, "SMS", "sms"),
            (req.GetCallHistorySetting, self.commphone.getcallhistory, 'Call History', 'call_history'),
            (req.GetPlaylistSetting, self.commphone.getplaylist, 'Play List', 'playlist'),
            (req.GetT9Setting, self.commphone.gett9db, 'T9 DB', t9editor.dict_key),
            ):
            st=i[0]()
            if st==req.MERGE:
                sync[i[3]]="MERGE"
                willcall.append(i)
            elif st==req.OVERWRITE:
                sync[i[3]]="OVERWRITE"
                willcall.append(i)

        results['sync']=sync
        count=0
        for i in willcall:
            self.progressmajor(count, len(willcall), i[2])
            count+=1
            i[1](results)

        for xx in todo:
            func=xx[0]
            desc=xx[1]
            args=[results]
            if len(xx)>2:
                args.extend(xx[2:])
            apply(func, args)

        return results

    def senddata(self, dict, todo):
        count=0
        for xx in todo:
            func=xx[0]
            desc=xx[1]
            args=[dict]
            if len(xx)>2:
                args.extend(xx[2:])
            self.progressmajor(count,len(todo),desc)
            apply(func, args)
            count+=1
        return dict

    def writewallpaper(self, data, merge):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.savewallpapers(data, merge)

    def writeringtone(self, data, merge):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.saveringtones(data, merge)

    def writephonebook(self, data):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.savephonebook(data)

    def rebootcheck(self, results):
        if __debug__: self.checkthread()
        if results.has_key('rebootphone'):
            self.log("BitPim is rebooting your phone for changes to take effect")
            delay=0
            if results.has_key('reboot_delay'):
                delay=results['reboot_delay']
            self.phonerebootrequest(delay)
            self.clearcomm()
        elif results.get('clearcomm', False):
            # some model (eg Moto) needs to clear comm after certain mode
            self.clearcomm()

    def writecalendar(self, data, merge):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.savecalendar(data, merge)

    def writememo(self, data, merge):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.savememo(data, merge)

    def writetodo(self, data, merge):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.savetodo(data, merge)

    def writesms(self, data, merge):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.savesms(data, merge)

    def writeplaylist(self, data, merge):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.saveplaylist(data, merge)

    def writet9(self, data, merge):
        if __debug__:
            self.checkthread()
        self.setupcomm()
        return self.commphone.savet9db(data, merge)

    def getphoneinfo(self):
        if __debug__: self.checkthread()
        self.setupcomm()
        if hasattr(self.commphone, 'getphoneinfo'):
            phone_info=phoneinfo.PhoneInfo()
            getattr(self.commphone, 'getphoneinfo')(phone_info)
            return phone_info

    def detectphone(self, using_port=None, using_model=None, delay=0):
        self.clearcomm()
        time.sleep(delay)
        return phone_detect.DetectPhone(self).detect(using_port, using_model)

    # various file operations for the benefit of the filesystem viewer
    def dirlisting(self, path, recurse=0):
        if __debug__: self.checkthread()
        self.setupcomm()
        try:
            return self.commphone.getfilesystem(path, recurse)
        except:
            self.log('Failed to read dir: '+path)
            return {}

    def getfileonlylist(self, path):
        if __debug__: self.checkthread()
        self.setupcomm()
        try:
            return self.commphone.listfiles(path)
        except:
            self.log('Failed to read filesystem')
            return {}

    def getdironlylist(self, path, recurse):
        results=self.commphone.listsubdirs(path)
        subdir_list=[x['name'] for k,x in results.items()]
        if recurse:
            for _subdir in subdir_list:
                try:
                    results.update(self.getdironlylist(_subdir, recurse))
                except:
                    self.log('Failed to list directories in ' +_subdir)
        return results

    def fulldirlisting(self):
        if __debug__: self.checkthread()
        self.setupcomm()
        try:
            return self.getdironlylist("", True)
        except:
            self.log('Failed to read filesystem')
            return {}

    def singledirlisting(self, path):
        if __debug__: self.checkthread()
        self.setupcomm()
        try:
            return self.getdironlylist(path, False)
        except:
            self.log('Failed to read filesystem')
            return {}

    def getfile(self, path):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.getfilecontents(path)

    def rmfile(self,path):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.rmfile(path)

    def writefile(self,path,contents):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.writefile(path, contents)

    def mkdir(self,path):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.mkdir(path)

    def rmdir(self,path):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.rmdir(path)

    def rmdirs(self,path):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.rmdirs(path)

    # offline/reboot/modemmode
    def phonerebootrequest(self, reboot_delay=0):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.offlinerequest(reset=True, delay=reboot_delay)

    def phoneofflinerequest(self):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.offlinerequest()

    def modemmoderequest(self):
        if __debug__: self.checkthread()
        self.setupcomm()
        return self.commphone.modemmoderequest()

    # backups etc
    def getbackup(self,path,recurse=0):
        if __debug__: self.checkthread()
        self.setupcomm()
        self.progressmajor(0,0,"Listing files")
        files=self.dirlisting(path, recurse)
        if path=="/" or path=="":
            strip=0 # root dir
        else:
            strip=len(path)+1 # child

        keys=files.keys()
        keys.sort()
        
        op=cStringIO.StringIO()
        with contextlib.closing(zipfile.ZipFile(op, "w", zipfile.ZIP_DEFLATED)) as zip:
            count=0
            for k in keys:
                try:
                    count+=1
                    if files[k]['type']!='file':
                        continue
                    self.progressmajor(count, len(keys)+1, "Getting files")
                    # get the contents
                    contents=self.getfile(k)
                    # an artificial sleep. if you get files too quickly, the 4400 eventually
                    # runs out of buffers and returns truncated packets
                    time.sleep(0.3)
                    # add to zip file
                    zi=zipfile.ZipInfo()
                    # zipfile does not like unicode. cp437 works on windows well, may be
                    # a better choice than ascii, but no phones currently support anything
                    # other than ascii for filenames
                    if k[strip]=='/':
                        zi.filename=common.get_ascii_string(k[strip+1:], 'ignore')
                    else:
                        zi.filename=common.get_ascii_string(k[strip:], 'ignore')
                    if files[k]['date'][0]==0:
                        zi.date_time=(0,0,0,0,0,0)
                    else:
                        zi.date_time=time.gmtime(files[k]['date'][0])[:6]
                    zi.compress_type=zipfile.ZIP_DEFLATED
                    zip.writestr(zi, contents)
                except:
                    self.log('Failed to read file: '+k)
        return op.getvalue()
    
    def restorefiles(self, files):
        if __debug__: self.checkthread()
        self.setupcomm()

        results=[]

        seendirs=[]

        count=0
        for name, contents in files:
            self.progressmajor(count, len(files), "Restoring files")
            count+=1
            d=guihelper.dirname(name)
            if d not in seendirs:
                seendirs.append(d)
                self.commphone.mkdirs(d)
            self.writefile(name, contents)
            results.append( (True, name) )
            # add a deliberate sleep - some phones (eg vx7000) get overwhelmed when writing
            # lots of files in a tight loop
            time.sleep(0.3)

        return results

    def OnDataRecording(self, _=None):
        self.clearcomm()

#-------------------------------------------------------------------------------
# For windows platform only
if guihelper.IsMSWindows():
    import struct
    class DeviceChanged:

        DBT_DEVICEARRIVAL = 0x8000
        DBT_DEVICEQUERYREMOVE = 0x8001
        DBT_DEVICEQUERYREMOVEFAILED = 0x8002
        DBT_DEVICEREMOVEPENDING =  0x8003
        DBT_DEVICEREMOVECOMPLETE = 0x8004
        DBT_DEVICETYPESPECIFIC = 0x8005    
        DBT_DEVNODES_CHANGED = 7
        DBT_CONFIGCHANGED = 0x18

        DBT_DEVTYP_OEM = 0
        DBT_DEVTYP_DEVNODE = 1
        DBT_DEVTYP_VOLUME = 2
        DBT_DEVTYP_PORT = 3
        DBT_DEVTYP_NET = 4

        DBTF_MEDIA   =   0x0001
        DBTF_NET    =    0x0002

        def __init__(self, wparam, lparam):
            self._info=None
            for name in dir(self):
                if name.startswith("DBT") and \
                   not name.startswith("DBT_DEVTYP") and \
                   getattr(self,name)==wparam:
                    self._info=(name, dict(self._decode_struct(lparam)))

        def GetEventInfo(self):
            return self._info
            
        def _decode_struct(self, lparam):
            if lparam==0: return ()
            format = "iii"
            buf = win32gui.PyMakeBuffer(struct.calcsize(format), lparam)
            dbch_size, dbch_devicetype, dbch_reserved = struct.unpack(format, buf)

            buf = win32gui.PyMakeBuffer(dbch_size, lparam) # we know true size now

            if dbch_devicetype==self.DBT_DEVTYP_PORT:
                name=""
                for b in buf[struct.calcsize(format):]:
                    if b!="\x00":
                        name+=b
                        continue
                    break
                return ("name", name),

            if dbch_devicetype==self.DBT_DEVTYP_VOLUME:
                # yes, the last item is a WORD, not a DWORD like the hungarian would lead you to think
                format="iiiih0i"
                dbcv_size, dbcv_devicetype, dbcv_reserved, dbcv_unitmask, dbcv_flags = struct.unpack(format, buf)
                units=[chr(ord('A')+x) for x in range(26) if dbcv_unitmask&(2**x)]
                flag=""
                for name in dir(self):
                    if name.startswith("DBTF_") and getattr(self, name)==dbcv_flags:
                        flag=name
                        break

                return ("drives", units), ("flag", flag)

            print "unhandled devicetype struct", dbch_devicetype
            return ()
