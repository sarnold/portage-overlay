### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: bitfling.py 4228 2007-05-10 02:59:06Z djpham $

"""This is the BitFling client

It acts as an XML-RPC server over SSH.  The UI consists of a tray icon (Windows)
or a small icon (Linux, Mac) that you can click on to get the dialog."""

# Standard Modules
import sys
import cStringIO
import os
import random
import sha
import thread
import fnmatch
import socket
import threading
import time
from xmlrpclib import Fault, Binary

# wx stuff
import wx
import wx.html
import wx.lib.newevent
import wx.lib.masked.textctrl
import wx.lib.mixins.listctrl

# others
import paramiko

# My stuff
try:
    import native.usb as usb
except ImportError:
    usb=None
import usbscan
import comscan
import commport
    
import guihelper
import xmlrpcstuff
import version

ID_CONFIG=wx.NewId()
ID_LOG=wx.NewId()
ID_RESCAN=wx.NewId()
ID_EXIT=wx.NewId()


XmlServerEvent, EVT_XMLSERVER = wx.lib.newevent.NewEvent()

guithreadid=thread.get_ident()

# in theory this should also work for GTK, but in practise it doesn't
if guihelper.IsMSWindows(): parentclass=wx.TaskBarIcon
else: parentclass=wx.Frame

class MyTaskBarIcon(parentclass):

    def __init__(self, mw, menu):
        self.mw=mw
        self.menu=menu
        iconfile="bitfling.png"
        if parentclass is wx.Frame:
            parentclass.__init__(self, None, -1, "BitFling Window", size=(32,32), style=wx.FRAME_TOOL_WINDOW)
            self.genericinit(iconfile)
        else:
            parentclass.__init__(self)
            self.windowsinit(iconfile)
            
        self.leftdownpos=0,0
        #wx.EVT_MENU(menu, ID_CONFIG, self.OnConfig)
        #wx.EVT_MENU(menu, ID_LOG, self.OnLog)
        wx.EVT_MENU(menu, ID_EXIT, self.OnExit)
        #wx.EVT_MENU(menu, ID_RESCAN, self.OnRescan)

    def GoAway(self):
        if parentclass is wx.Frame:
            self.Close(True)
        else:
            self.RemoveIcon()
        self.Destroy()

    def OnConfig(self,_):
        print "I would do config at this point"

    def OnLog(self,_):
        print "I would do log at this point"

    def OnHelp(self,_):
        print "I would do help at this point"

    def OnRescan(self, _):
        print "I would do rescan at this point"

    def OnExit(self,_):
        self.mw.Close(True)

    def OnRButtonUp(self, evt=None):
        if parentclass is wx.Frame:
            self.PopupMenu(self.menu, evt.GetPosition())
        else:
            self.PopupMenu(self.menu)

    def OnLButtonUp(self, evt=None):
        if self.leftdownpos is None:
            return # cleared out by motion stuff
        if self.mw.IsShown():
            self.mw.Show(False)
        else:
            self.mw.Show(True)
            self.mw.Raise()

    def OnLeftDown(self, evt):
        if guihelper.IsMSWindows():
            self.leftdownpos=0
        else:
            self.leftdownpos=evt.GetPosition()
        self.motionorigin=self.leftdownpos

    def OnMouseMotion(self, evt):
        if not evt.Dragging():
            return
        if evt.RightIsDown() or evt.MiddleIsDown():
            return
        if not evt.LeftIsDown():
            return
        self.leftdownpos=None
        x,y=evt.GetPosition()
        xdelta=x-self.motionorigin[0]
        ydelta=y-self.motionorigin[1]
        screenx,screeny=self.GetPositionTuple()
        self.MoveXY(screenx+xdelta, screeny+ydelta)

    def windowsinit(self, iconfile):
        bitmap=wx.Bitmap(guihelper.getresourcefile(iconfile), wx.BITMAP_TYPE_PNG)
        icon=wx.EmptyIcon()
        icon.CopyFromBitmap(bitmap)
        self.SetIcon(icon, "BitFling")
        wx.EVT_TASKBAR_RIGHT_UP(self, self.OnRButtonUp)
        wx.EVT_TASKBAR_LEFT_UP(self, self.OnLButtonUp)
        #wx.EVT_TASKBAR_MOVE(self, self.OnMouseMotion)
        wx.EVT_TASKBAR_LEFT_DOWN(self, self.OnLeftDown)
        
    def genericinit(self, iconfile):
        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        bitmap=wx.Bitmap(guihelper.getresourcefile(iconfile), wx.BITMAP_TYPE_PNG)
        bit=wx.StaticBitmap(self, -1, bitmap)
        self.Show(True)
        wx.EVT_RIGHT_UP(bit, self.OnRButtonUp)
        wx.EVT_LEFT_UP(bit, self.OnLButtonUp)
        wx.EVT_MOTION(bit, self.OnMouseMotion)
        wx.EVT_LEFT_DOWN(bit, self.OnLeftDown)
        self.bit=bit

class ConfigPanel(wx.Panel, wx.lib.mixins.listctrl.ColumnSorterMixin):

    def __init__(self, mw, parent, id=-1):
        wx.Panel.__init__(self, parent, id)
        self.mw=mw
        vbs=wx.BoxSizer(wx.VERTICAL)

        # General
        bs=wx.StaticBoxSizer(wx.StaticBox(self, -1, "General"), wx.HORIZONTAL)
        bs.Add(wx.StaticText(self, -1, "Fingerprint"), 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        self.fingerprint=wx.TextCtrl(self, -1, "a", style=wx.TE_READONLY,  size=(300,-1))
        bs.Add(self.fingerprint, 0, wx.EXPAND|wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        bs.Add(wx.StaticText(self, -1, ""), 0, wx.ALL, 5) # spacer
        bs.Add(wx.StaticText(self, -1, "Port"), 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        self.porttext=wx.StaticText(self, -1, "<No Port>")
        bs.Add(self.porttext, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        vbs.Add(bs, 0, wx.EXPAND|wx.ALL, 5)

        # authorization
        bs=wx.StaticBoxSizer(wx.StaticBox(self, -1, "Authorization"), wx.VERTICAL)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        butadd=wx.Button(self, wx.NewId(), "Add ...")
        hbs.Add(butadd, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        hbs.Add(wx.StaticText(self, -1, ""), 0, wx.ALL, 5) # spacer
        self.butedit=wx.Button(self, wx.NewId(), "Edit ...")
        self.butedit.Enable(False)
        hbs.Add(self.butedit, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        hbs.Add(wx.StaticText(self, -1, ""), 0, wx.ALL, 5) # spacer
        self.butdelete=wx.Button(self, wx.NewId(), "Delete")
        self.butdelete.Enable(False)
        hbs.Add(self.butdelete, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        bs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)

        wx.EVT_BUTTON(self, butadd.GetId(), self.OnAddAuth)
        wx.EVT_BUTTON(self, self.butedit.GetId(), self.OnEditAuth)
        wx.EVT_BUTTON(self, self.butdelete.GetId(), self.OnDeleteAuth)

        # and the authorization listview
        self.authlist=wx.ListCtrl(self, wx.NewId(), style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
        self.authlist.InsertColumn(0, "User")
        self.authlist.InsertColumn(1, "Allowed Addresses")
        self.authlist.InsertColumn(2, "Expires")
        self.authlist.SetColumnWidth(0, 300)
        self.authlist.SetColumnWidth(1, 300)
        self.authlist.SetColumnWidth(2, 100)
        bs.Add(self.authlist, 1, wx.EXPAND|wx.ALL, 5)
        
        vbs.Add(bs, 1, wx.EXPAND|wx.ALL, 5)
        self.itemDataMap={}
        wx.lib.mixins.listctrl.ColumnSorterMixin.__init__(self,3)

        wx.EVT_LIST_ITEM_ACTIVATED(self.authlist, self.authlist.GetId(), self.OnEditAuth)
        wx.EVT_LIST_ITEM_SELECTED(self.authlist, self.authlist.GetId(), self.OnAuthListItemFondled)
        wx.EVT_LIST_ITEM_DESELECTED(self.authlist, self.authlist.GetId(), self.OnAuthListItemFondled)
        wx.EVT_LIST_ITEM_FOCUSED(self.authlist, self.authlist.GetId(), self.OnAuthListItemFondled)

        # devices
        bs=wx.StaticBoxSizer(wx.StaticBox(self, -1, "Devices"), wx.VERTICAL)
        buttoggle=wx.Button(self, wx.NewId(), "Toggle Allowed")
        bs.Add(buttoggle, 0, wx.ALL, 5)
        self.devicelist=wx.ListCtrl(self, wx.NewId(), style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
        self.devicelist.InsertColumn(0, "Allowed")
        self.devicelist.InsertColumn(1, "Name")
        self.devicelist.InsertColumn(2, "Available")
        self.devicelist.InsertColumn(3, "Description")
        self.devicelist.SetColumnWidth(0, 100)
        self.devicelist.SetColumnWidth(1, 300)
        self.devicelist.SetColumnWidth(2, 100)
        self.devicelist.SetColumnWidth(3, 300)
        bs.Add(self.devicelist, 1, wx.EXPAND|wx.ALL, 5)

        vbs.Add(bs, 1, wx.EXPAND|wx.ALL, 5)
        
        self.setupauthorization()
        self.SortListItems()
        
        self.SetSizer(vbs)
        self.SetAutoLayout(True)

    def _updateauthitemmap(self, itemnum):
        pos=-1
        if itemnum in self.itemDataMap:
            # find item by looking for ItemData, and set pos
            # to corresponding pos in list
            for i in range(self.authlist.GetItemCount()):
                if self.authlist.GetItemData(i)==itemnum:
                    pos=i
                    break
            assert pos!=-1
        # clear the is connection allowed cache
        self.mw.icacache={}
        v=self.mw.authinfo[itemnum]
        username=v[0]
        expires=v[2]
        addresses=" ".join(v[3])
        if pos<0:
            pos=self.authlist.GetItemCount()
            self.authlist.InsertStringItem(pos, username)
        else:
            self.authlist.SetStringItem(pos, 0, username)
        self.authlist.SetStringItem(pos, 2, `expires`)
        self.authlist.SetStringItem(pos, 1, addresses)
        self.authlist.SetItemData(pos, itemnum)
        self.itemDataMap[itemnum]=(username, addresses, expires)

    def GetListCtrl(self):
        "Used by the ColumnSorter mixin"
        return self.authlist

    def setupauthorization(self):
        dict={}
        items=[]
        for i in range(1000):
            if self.mw.config.HasEntry("user-"+`i`):
                username,password,expires,addresses=self.mw.config.Read("user-"+`i`).split(":")
                expires=int(expires)
                addresses=addresses.split()
                dict[i]=username,password,expires,addresses
                items.append(i)
        self.mw.authinfo=dict
        for i in items:
            self._updateauthitemmap(i)


    def OnAddAuth(self,_):
        dlg=AuthItemDialog(self, "Add Entry")
        if dlg.ShowModal()==wx.ID_OK:
            username,password,expires,addresses=dlg.GetValue()
            for i in range(1000):
                if i not in self.mw.authinfo:
                    self.mw.config.Write("user-"+`i`, "%s:%s:%d:%s" % (username, password, expires, " ".join(addresses)))
                    self.mw.config.Flush()
                    self.mw.authinfo[i]=username,password,expires,addresses
                    self._updateauthitemmap(i)
                    self.SortListItems()
                    break
        dlg.Destroy()

    def OnDeleteAuth(self, _):
        item=self._getselectedlistitem(self.authlist)
        key=self.authlist.GetItemData(item)
        del self.mw.authinfo[key]
        self.authlist.DeleteItem(item)
        self.mw.config.DeleteEntry("user-"+`key`)
        self.mw.config.Flush()

    def _getselectedlistitem(self, listctrl):
        "Finds the selected item in a listctrl since the wx methods don't actually work"
        i=-1
        while True:
            nexti=listctrl.GetNextItem(i, state=wx.LIST_STATE_SELECTED)
            if nexti<0:
                break
            i=nexti
            return i
        return None

    def OnAuthListItemFondled(self, _):
        "Called whenever list items are selected, unselectected or similar fondling"
        selitem=self._getselectedlistitem(self.authlist)
        self.butedit.Enable(selitem is not None)
        self.butdelete.Enable(selitem is not None)

    def OnEditAuth(self, _):
        "Called to edit the currently selected entry"
        item=self._getselectedlistitem(self.authlist)
        key=self.authlist.GetItemData(item)
        username,password,expires,addresses=self.mw.authinfo[key]
        dlg=AuthItemDialog(self, "Edit Entry", username=username, password=password, expires=expires, addresses=addresses)
        if dlg.ShowModal()==wx.ID_OK:
            username,password,expires,addresses=dlg.GetValue()
            self.mw.authinfo[key]=username,password,expires,addresses
            self._updateauthitemmap(key)
        dlg.Destroy()

class AuthItemDialog(wx.Dialog):

    _password_sentinel="\x01\x02\x03\x04\x05\x06\x07\x08" # magic value used to detect if user has changed the field

    def __init__(self, parent, title, username="New User", password="", expires=0, addresses=[]):
        wx.Dialog.__init__(self, parent, -1, title, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        p=self
        gs=wx.FlexGridSizer(4, 2, 5, 5)
        gs.AddGrowableCol(1)
        gs.AddGrowableRow(3)

        gs.Add(wx.StaticText(p, -1, "Username/Email"))
        self.username=wx.TextCtrl(self, -1, username)
        gs.Add(self.username,0, wx.EXPAND)
        gs.Add(wx.StaticText(p, -1, "Password"))
        self.password=wx.TextCtrl(self, -1, "", style=wx.TE_PASSWORD)
        self.origpassword=password
        if len(password): self.password.SetValue(self._password_sentinel)
        gs.Add(self.password, 0, wx.EXPAND)
        gs.Add(wx.StaticText(p, -1, "Expires"))
        self.expires=wx.lib.masked.textctrl.TextCtrl(p, -1, "", autoformat="EUDATETIMEYYYYMMDD.HHMM")
        gs.Add(self.expires)
        gs.Add(wx.StaticText(p, -1, "Allowed Addresses"))
        self.addresses=wx.TextCtrl(self, -1, "\n".join(addresses), style=wx.TE_MULTILINE)
        gs.Add(self.addresses, 1, wx.EXPAND)


        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(gs,1, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(vbs)
        vbs.Fit(self)


    def GenPassword(self, string):
        # random salt
        salt="".join([chr(random.randint(0,127)) for x in range(8)])
        saltstr="".join(["%02x" % (ord(x),) for x in salt])
        # we use a sha of the salt followed by the string
        val=sha.new(salt+string)
        # return generated password as $ seperated hex strings
        return "$".join([saltstr, val.hexdigest()])
        

    def GetValue(self):
        # ::TODO:: ensure no colons in username or addresses
        # figure out password
        if self.password.GetValue()!=self._password_sentinel:
            password=self.GenPassword(self.password.GetValue())
        else:
            password=self.origpassword
        return [self.username.GetValue(), password, 0, self.addresses.GetValue().split()]

class MainWindow(wx.Frame):

    def __init__(self, parent, id, title):
        self.taskwin=None # set later
        wx.Frame.__init__(self, parent, id, title, style=wx.RESIZE_BORDER|wx.SYSTEM_MENU|wx.CAPTION)

        sys.excepthook=self.excepthook

        self.authinfo={}  # updated by config panel
        self.icacache={}  # used by IsConnectionAllowed

        # Establish config stuff
        cfgstr='bitfling'
        if guihelper.IsMSWindows():
            cfgstr="BitFling"  # nicely capitalized on Windows
        self.config=wx.Config(cfgstr, style=wx.CONFIG_USE_LOCAL_FILE)
        # self.config.SetRecordDefaults(True)
        # for help to save prefs
        wx.GetApp().SetAppName(cfgstr)
        wx.GetApp().SetVendorName(cfgstr)

        self.setuphelp()
        
        wx.EVT_CLOSE(self, self.CloseRequested)

        panel=wx.Panel(self, -1)
        
        bs=wx.BoxSizer(wx.VERTICAL)

        self.nb=wx.Notebook(panel, -1)
        bs.Add(self.nb, 1, wx.EXPAND|wx.ALL, 5)
        bs.Add(wx.StaticLine(panel, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)

        gs=wx.GridSizer(1,4, 5, 5)

        for name in ("Rescan", "Hide", "Help", "Exit" ):
            but=wx.Button(panel, wx.NewId(), name)
            setattr(self, name.lower(), but)
            gs.Add(but)
        bs.Add(gs,0,wx.ALIGN_CENTRE|wx.ALL, 5)

        panel.SetSizer(bs)
        panel.SetAutoLayout(True)

        # the notebook pages
        self.configpanel=ConfigPanel(self, self.nb)
        self.nb.AddPage(self.configpanel, "Configuration")
        self.lw=guihelper.LogWindow(self.nb)
        self.nb.AddPage(self.lw, "Log")

        wx.EVT_BUTTON(self, self.hide.GetId(), self.OnHideButton)
        wx.EVT_BUTTON(self, self.help.GetId(), self.OnHelpButton)
        wx.EVT_BUTTON(self, self.exit.GetId(), self.OnExitButton)

        EVT_XMLSERVER(self, self.OnXmlServerEvent)

        self.xmlrpcserver=None
        wx.CallAfter(self.StartIfICan)

    def setuphelp(self):
        """Does all the nonsense to get help working"""
        import wx.html
        # Add the Zip filesystem
        wx.FileSystem_AddHandler(wx.ZipFSHandler())
        # Get the help working
        self.helpcontroller=wx.html.HtmlHelpController()
        self.helpcontroller.AddBook(guihelper.getresourcefile("bitpim.htb"))
        self.helpcontroller.UseConfig(self.config, "help")

        # now context help
        # (currently borken)
        # self.helpprovider=wx.HelpControllerHelpProvider(self.helpcontroller)
        # wx.HelpProvider_Set(provider)
        
    def IsConnectionAllowed(self, peeraddr, username=None, password=None):
        """Verifies if a connection is allowed

        If username and password are supplied (as should be the case if calling this method
        before executing some code) then they are checked as being from a valid address
        as well.

        If username and password are not supplied then this method checks if any
        of the authentication rules allow a connection from the peeraddr.  This form
        is used immediately after calling accept() on a socket, but before doing
        anything else."""
        # Note that this method is not called in the main thread, and any variables could be
        # updated underneath us.  Be threadsafe and only use atomic methods on shared data!
        
        v=(peeraddr[0], username, password)
        if username is not None and password is None:
            self.Log("%s: No password supplied for user %s" % (peeraddr, `username`))
            assert False, "No password supplied"
            return False # not allowed to have None as password
        print "ica of "+`v`
        val=self.icacache.get(v, None)
        if val is not None:
            allowed, expires = val
            if allowed:
                if self._has_expired(expires):
                    msg="Connection from %s no longer allowed due to expiry" % (peeraddr[0],)
                    if username is not None:
                        msg+=".  Username "+`username`
                    self.Log(msg)
                    return False
                return True
            return False

        ret_allowed=False
        ret_expiry=0  # an expiry of zero is infinite, so this will be overridden by any specific expiries
        for uname, pwd, expires, addresses in self.authinfo.values():  # values() is threadsafe
            # do any of the addresses match?
            if not self._does_address_match(peeraddr[0], addresses):
                continue
            # check username/password if username supplied
            if username is not None:
                if  username!=uname:
                    continue
                # check password
                if not self._verify_password(password, pwd):
                    self.Log("Wrong password supplied for user %s from %s" % (`username`, peeraddr[0]))
                    continue
            # remember expiry value (largest value)
            ret_expiry=max(ret_expiry, expires)
            ret_allowed=True

        if not ret_allowed:
            if username is not None:
                self.Log("No valid credentials for user %s from %s" % (username, peeraddr[0]))
            else:
                self.Log("No defined users for address "+`peeraddr`)
            
        # recurse so that correct log messages about expiry get generated
        self.icacache[v]=ret_allowed, ret_expiry
        return self.IsConnectionAllowed(peeraddr, username, password)

    def _verify_password(self, password, pwd):
        """Returns True if password matches pwd
        @param password: password supplied by user
        @param pwd:  password as we store it (salt $ hash)"""
        salt,hash=pwd.split("$", 1)
        # turn salt back into binary
        x=""
        for i in range(0, len(salt), 2):
            x+=chr(int(salt[i:i+2], 16))
        salt=x
        # we do this silly string stuff to avoid issues with encoding - it only works for iso 8859-1
        str=[]
        str.extend([ord(x) for x in salt])
        str.extend([ord(x) for x in password])
        val=sha.new("".join([chr(x) for x in str]))
        print password, pwd, val.hexdigest(), val.hexdigest()==hash
        return val.hexdigest()==hash
            
    def _does_address_match(self, peeraddr, addresses):
        """Returns if the peeraddr matches any of the supplied addresses"""
        # note this function can be called from any thread.  do not access any data
        for addr in addresses:
            # the easy case
            if peeraddr==addr: return True
            # is addr a glob pattern?
            if '*' in addr or '?' in addr or '[' in addr:
                if fnmatch.fnmatch(peeraddr, addr):
                    return True
            # ::TODO::  addr/bits style checking - see Python cookbook 10.5 for code
            # ok, do dns lookup on it
            ips=[]
            try:
                ips=socket.getaddrinfo(addr, None)
            except:
                pass
            for _, _, _, _, ip in ips:
                if peeraddr==ip[0]:
                    return True
        return False

    def _has_expired(self, expires):
        if expires==0:
            return False
        if time.time()>expires:
            return True
        return False
                            
    def CloseRequested(self, evt):
        if evt.CanVeto():
            self.Show(False)
            evt.Veto()
            return
        self.taskwin.GoAway()
        evt.Skip()
        sys.excepthook=sys.__excepthook__

    def OnXmlServerEvent(self, msg):
        if msg.cmd=="log":
            self.Log(msg.data)
        elif msg.cmd=="logexception":
            self.LogException(msg.data)
        else:
            assert False, "bad message "+`msg`
            pass
            

    def OnExitButton(self, _):
        self.Close(True)

    def OnHideButton(self, _):
        self.Show(False)

    def OnHelpButton(self, _):
        import helpids
        self.helpcontroller.Display(helpids.ID_BITFLING)

    def Log(self, text):
        if thread.get_ident()!=guithreadid:
            wx.PostEvent(self, XmlServerEvent(cmd="log", data=text))
        else:
            self.lw.log(text)

    def LogException(self, exc):
        if thread.get_ident()!=guithreadid:
            # need to send it to guithread
            wx.PostEvent(self, XmlServerEvent(cmd="log", data="Exception in thread "+threading.currentThread().getName()))
            wx.PostEvent(self, XmlServerEvent(cmd="logexception", data=exc))
        else:
            self.lw.logexception(exc)

    def excepthook(self, *args):
        """Replacement exception handler that sends stuff to our log window"""
        self.LogException(args)

    def GetCertificateFilename(self):
        """Return certificate filename

        By default $HOME (or My Documents) / .bitfling.key
        but can be overridden with "certificatefile" config key"""
        
        if guihelper.IsMSWindows(): # we want subdir of my documents on windows
            # nice and painful
            from win32com.shell import shell, shellcon
            path=shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
            path=os.path.join(path, ".bitfling.key")
        else:
            path=os.path.expanduser("~/.bitfling.key")
        return self.config.Read("certificatefile", path)
        

    def StartIfICan(self):
        certfile=self.GetCertificateFilename()
        if not os.path.isfile(certfile):
            wx.BeginBusyCursor(wx.StockCursor(wx.CURSOR_ARROWWAIT))
            bi=wx.BusyInfo("Creating BitFling host certificate and keys")
            try:
                generate_certificate(certfile)
                if not os.path.isfile(certfile):
                    # ::TODO:: report that we failed
                    certfile=None
            finally:
                del bi
                wx.EndBusyCursor()
        port=self.config.ReadInt("port", 12652)
        if port<1 or port>65535: port=None
        host=self.config.Read("bindaddress", "")
        if certfile is None or port is None:
            return
        self.Log("Starting on port "+`port`)
        key=paramiko.DSSKey.from_private_key_file(certfile)
        fp=paramiko.util.hexify(key.get_fingerprint())
        self.configpanel.fingerprint.SetValue(fp)
        self.configpanel.porttext.SetLabel(`port`)
        self.configpanel.GetSizer().Layout()
        self.xmlrpcserver=BitFlingService(self, host, port, key)
        self.xmlrpcserver.setDaemon(True)
        self.xmlrpcserver.start()
        

def generate_certificate(outfile):
    key=paramiko.DSSKey.generate()
    key.write_private_key_file(outfile, None)



class XMLRPCService(xmlrpcstuff.Server):

    def __init__(self, mainwin, host, port, servercert):
        self.mainwin=mainwin
        xmlrpcstuff.Server.__init__(self, host, port, servercert)

    def OnLog(self, msg):
        wx.PostEvent(self.mainwin, XmlServerEvent(cmd="log", data=msg))

    def OnLogException(self, exc):
        wx.PostEvent(self.mainwin, XmlServerEvent(cmd="logexception", data=exc))

    def OnNewAccept(self, clientaddr):
        return self.mainwin.IsConnectionAllowed(clientaddr)

    def OnNewUser(self, clientaddr, username, password):
        return self.mainwin.IsConnectionAllowed(clientaddr, username, password)

    def OnMethodDispatch(self, method, params, username, clientaddr):
        method="exp_"+method
        if not hasattr(self, method):
            raise Fault(3, "No such method")

        context={ 'username': username, 'clientaddr': clientaddr }
        
        return getattr(self, method)(*params, **{'context': context})


class BitFlingService(XMLRPCService):

    def __init__(self, mainwin, host, port, servercert):
        XMLRPCService.__init__(self, mainwin, host, port, servercert)
        self.handles={}

    def stashhandle(self, context, comm):
        for i in range(10000):
            if i not in self.handles:
                self.handles[i]=[context, comm]
                return i

    def gethandle(self, context, num):
        # ::TODO:: check context has access
        return self.handles[num][1]

    # Only methods begining with exp are exported to XML-RPC
    
    def exp_scan(self, context):
        if usb is None:
            return comscan.comscan()
        else:
            return usbscan.usbscan()+comscan.comscan()
    
    def exp_getversion(self, context):
        return version.description

    def exp_deviceopen(self, port, baud, timeout, hardwareflow, softwareflow, context):
        # ::TODO:: None is pointer to log object
        return self.stashhandle(context, commport.CommConnection(None, port, baud, timeout,
                                                                 hardwareflow, softwareflow))

    def exp_deviceclose(self, handle, context):
        comm=self.gethandle(context, handle)
        comm.close()
        del self.handles[handle]
        return True

    def exp_devicesetbaudrate(self, handle, rate, context):
        return self.gethandle(context, handle).setbaudrate(rate)

    def exp_devicesetdtr(self, handle, dtr, context):
        return self.gethandle(context, handle).setdtr(dtr)

    def exp_devicesetrts(self, handle, rts, context):
        return self.gethandle(context, handle).setrts(rts)

    def exp_devicewrite(self, handle, data, context):
        self.gethandle(context, handle).write(data.data)
        return len(data.data)

    def exp_devicesendatcommand(self, handle, atcommand, ignoreerror, context):
        "Special handling for empty lists and exceptions"
        try:
            res=self.gethandle(context, handle).sendatcommand(atcommand.data, ignoreerror=ignoreerror)
            if len(res)==0:
                res=1
        except:
            res=0
        return res
    
    def exp_devicereaduntil(self, handle, char, numfailures, context):
        return Binary(self.gethandle(context, handle).readuntil(char.data, numfailures=numfailures))

    def exp_deviceread(self, handle, numchars, context):
        return Binary(self.gethandle(context, handle).read(numchars))

    def exp_devicereadsome(self, handle, numchars, context):
        if numchars==-1:
            numchars=None
        return Binary(self.gethandle(context, handle).readsome(log=True,numchars=numchars))

    def exp_devicewritethenreaduntil(self, handle, data, char, numfailures, context):
        return Binary(self.gethandle(context, handle).writethenreaduntil(data.data, False, char.data, False, False, numfailures))

def run(args):
    theApp=wx.PySimpleApp()

    menu=wx.Menu()
    #menu.Append(ID_CONFIG, "Configuration")
    #menu.Append(ID_LOG, "Log")
    #menu.Append(ID_RESCAN, "Rescan devices")
    menu.Append(ID_EXIT, "Exit")

    mw=MainWindow(None, -1, "BitFling")
    taskwin=MyTaskBarIcon(mw, menu)
    mw.taskwin=taskwin
    theApp.MainLoop()
    
if __name__ == '__main__':
    run()
