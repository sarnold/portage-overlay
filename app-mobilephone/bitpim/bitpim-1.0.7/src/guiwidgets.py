#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: guiwidgets.py 4675 2008-08-12 21:52:12Z djpham $

"""Most of the graphical user interface elements making up BitPim"""

# standard modules
from __future__ import with_statement
import contextlib
import os
import sys
import time
import copy
import StringIO
import getpass
import sha,md5
import gzip
import base64
import thread
import Queue
import shutil
import platform

# wx. modules
import wx
import wx.html
import wx.lib.intctrl
import wx.lib.newevent
import wx.lib.mixins.listctrl  as  listmix
import wx.lib.stattext as stattext
from wx.lib.masked import NumCtrl

# my modules
import apsw
import common
import version
import helpids
import comscan
import usbscan
import comdiagnose
import analyser
import guihelper
import pubsub
import bphtml
import bitflingscan
import aggregatedisplay
import phone_media_codec
import pubsub
import widgets
import phones
import setphone_wizard
import data_recording
import xyaptu
import serial

###
### BitFling cert stuff
###

BitFlingCertificateVerificationEvent, EVT_BITFLINGCERTIFICATEVERIFICATION = wx.lib.newevent.NewEvent()


####
#### A simple text widget that does nice pretty logging.
####        

    
class LogWindow(wx.Panel, widgets.BitPimWidget):

    theanalyser=None
    
    def __init__(self, parent):
        wx.Panel.__init__(self,parent, -1)
        # have to use rich2 otherwise fixed width font isn't used on windows
        self.tb=wx.TextCtrl(self, 1, style=wx.TE_MULTILINE| wx.TE_RICH2|wx.TE_DONTWRAP|wx.TE_READONLY)
        f=wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL )
        ta=wx.TextAttr(font=f)
        self.tb.SetDefaultStyle(ta)
        self.sizer=wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.tb, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.sizer.Fit(self)
        wx.EVT_IDLE(self, self.OnIdle)
        wx.EVT_SHOW(self, self.OnShow)
        self.outstandingtext=StringIO.StringIO()

        wx.EVT_KEY_UP(self.tb, self.OnKeyUp)

    def Clear(self):
        self.tb.Clear()

    def OnSelectAll(self, _):
        self.tb.SetSelection(-1, -1)

    def OnShow(self, show):
        if show.GetShow():
            wx.CallAfter(self.CleanupView)

    def CleanupView(self):
        self.tb.SetInsertionPoint(0)
        self.tb.SetInsertionPointEnd()
        self.tb.Refresh()

    def OnIdle(self,_):
        if self.outstandingtext.tell():
            # this code is written to be re-entrant
            newt=self.outstandingtext.getvalue()
            self.outstandingtext.seek(0)
            self.outstandingtext.truncate()
            self.tb.AppendText(newt)

    def log(self, str, nl=True):
        now=time.time()
        t=time.localtime(now)
        self.outstandingtext.write("%d:%02d:%02d.%03d " % ( t[3], t[4], t[5],  int((now-int(now))*1000)))
        self.outstandingtext.write(str)
        if nl:
            self.outstandingtext.write("\n")

    def logdata(self, str, data, klass=None):
        o=self.outstandingtext
        self.log(str, nl=False)
        if data is not None:
            o.write(" Data - "+`len(data)`+" bytes\n")
            if klass is not None:
                try:
                    o.write("<#! %s.%s !#>\n" % (klass.__module__, klass.__name__))
                except:
                    klass=klass.__class__
                    o.write("<#! %s.%s !#>\n" % (klass.__module__, klass.__name__))
            o.write(common.datatohexstring(data))
        o.write("\n")

    def OnKeyUp(self, evt):
        keycode=evt.GetKeyCode()
        if keycode==ord('P') and evt.ControlDown() and evt.AltDown():
            # analyse what was selected
            data=self.tb.GetStringSelection()
            # or the whole buffer if it was nothing
            if data is None or len(data)==0:
                data=self.tb.GetValue()
            try:
                self.theanalyser.Show()
            except:
                self.theanalyser=None
                
            if self.theanalyser is None:
                self.theanalyser=analyser.Analyser(data=data)

            self.theanalyser.Show()
            self.theanalyser.newdata(data)
            evt.Skip()

    def GetValue(self):
        """return the log text"""
        return self.tb.GetValue()


###
### Dialog asking what you want to sync
###

class GetPhoneDialog(wx.Dialog):
    # sync sources ("Pretty Name", "name used to query profile")
    sources= ( ('PhoneBook', 'phonebook'),
               ('Calendar', 'calendar'),
               ('Wallpaper', 'wallpaper'),
               ('Ringtone', 'ringtone'),
               ('Memo', 'memo'),
               ('Todo', 'todo'),
               ('SMS', 'sms'),
               ('Call History', 'call_history'),
               ('Play List', 'playlist'),
               ('T9 User DB','t9_udb'))
    
    # actions ("Pretty Name", "name used to query profile")
    actions = (  ("Get", "read"), )

    NOTREQUESTED=0
    MERGE=1
    OVERWRITE=2

    # type of action ("pretty name", "name used to query profile")
    types= ( ("Add", MERGE),
             ("Replace All", OVERWRITE))
    typename={ MERGE: 'MERGE',
               OVERWRITE: 'OVERWRITE',
               NOTREQUESTED: 'NOTREQUESTED',
               }

    HELPID=helpids.ID_GET_PHONE_DATA

    def __init__(self, frame, title, id=-1):
        wx.Dialog.__init__(self, frame, id, title,
                          style=wx.CAPTION|wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE)
        gs=wx.FlexGridSizer(2+len(self.sources), 1+len(self.types),5 ,10)
        gs.AddGrowableCol(1)
        gs.AddMany( [
            (wx.StaticText(self, -1, "Source"), 0, wx.EXPAND),])

        for pretty,_ in self.types:
            gs.Add(wx.StaticText(self, -1, pretty), 0, wx.ALIGN_CENTRE)

        self._widgets={}
        for desc, source in self.sources:
            _cb=wx.CheckBox(self, wx.NewId(), desc)
            _cb.exclusive=False
            wx.EVT_CHECKBOX(self, _cb.GetId(), self.DoOkStatus)
            gs.Add(_cb, 0, wx.EXPAND)
            self._widgets[source]={ 'cb': _cb,
                                    'rb': {},
                                    }
            first=True
            for tdesc,tval in self.types:
                if first:
                    style=wx.RB_GROUP
                    first=0
                else:
                    style=0
                _rb=wx.RadioButton(self, -1, "", style=style)
                if self._dowesupport(source, self.actions[0][1], tval):
                    wx.EVT_RADIOBUTTON(self, _rb.GetId(), self.OnOptionSelected)
                else:
                    _rb.SetValue(False)
                    _rb.Enable(False)
                gs.Add(_rb, 0, wx.ALIGN_CENTRE)
                self._widgets[source]['rb'][tval]=_rb

        bs=wx.BoxSizer(wx.VERTICAL)
        bs.Add(gs, 0, wx.EXPAND|wx.ALL, 10)
        bs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 7)
        
        but=self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP)
        self._btn_ok=self.FindWindowById(wx.ID_OK)
        bs.Add(but, 0, wx.EXPAND|wx.ALL, 10)
        
        self.SetSizer(bs)
        self.SetAutoLayout(True)
        bs.Fit(self)

        wx.EVT_BUTTON(self, wx.ID_HELP, self.OnHelp)

    def _setting(self, sourcetype):
        _w=self._widgets[sourcetype]
        if not _w['cb'].GetValue():
            # Not selected
            return self.NOTREQUESTED
        for _typeval,_rb in _w['rb'].items():
            if _rb.GetValue():
                return _typeval
        # should not get here
        raise ValueError

    def GetPhoneBookSetting(self):
        return self._setting("phonebook")

    def GetCalendarSetting(self):
        return self._setting("calendar")

    def GetWallpaperSetting(self):
        return self._setting("wallpaper")

    def GetRingtoneSetting(self):
        return self._setting("ringtone")

    def GetMemoSetting(self):
        return self._setting("memo")

    def GetTodoSetting(self):
        return self._setting("todo")

    def GetSMSSetting(self):
        return self._setting("sms")
    def GetCallHistorySetting(self):
        return self._setting("call_history")
    def GetPlaylistSetting(self):
        return self._setting('playlist')
    def GetT9Setting(self):
        return self._setting('t9_udb')

    def OnHelp(self,_):
        wx.GetApp().displayhelpid(self.HELPID)

    # this is what BitPim itself supports - the phones may support a subset
    _notsupported=(
        # ('phonebook', 'read', MERGE), # sort of is
        ('calendar', 'read', MERGE),
        ('wallpaper', 'read', MERGE),
        ('ringtone', 'read', MERGE),
        ('memo', 'read', MERGE),
        ('todo', 'read', MERGE),
        ('playlist', 'read', MERGE),
        ('t9_udb', 'read', MERGE))

    def _dowesupport(self, source, action, type):
        if (source,action,type) in self._notsupported:
            return False
        return True

    def UpdateWithProfile(self, profile):
        assert len(self.types)==2
        _action=self.actions[0][1]
        for source,_w in self._widgets.items():
            _cb=_w['cb']
            _cb.Enable(False)
            # are any radio buttons enabled
            _rb_on=False
            for _type,_rb in _w['rb'].items():
                if self._dowesupport(source, _action, _type) and \
                   profile.SyncQuery(source, _action, self.typename[_type]):
                    _cb.Enable(True)
                    _cb.exclusive=profile.SyncQuery(source, _action, 'EXCLUSIVE')
                    _rb.Enable(True)
                    _rb_on|=bool(_rb.GetValue())
                else:
                    _rb.SetValue(False)
                    _rb.Enable(False)
            if _cb.IsEnabled():
                # make sure at least one radio button is set
                if not _rb_on:
                    for _rb in _w['rb'].values():
                        if _rb.IsEnabled():
                            _rb.SetValue(True)
                            break
            else:
                # uncheck of not enabled
                _cb.SetValue(False)

    def ShowModal(self):
        # we ensure the OK button is in the correct state
        self.DoOkStatus()
        return wx.Dialog.ShowModal(self)

    def _check_for_exclusive(self, w):
        if w.exclusive:
            # this one is exclusive, turn off all others
            for _w in self._widgets.values():
                if _w['cb'] is not w:
                    _w['cb'].SetValue(False)
        else:
            # this one is not exclusive, turn off all exclusive ones
            for _w in self._widgets.values():
                if _w['cb'] is not w and \
                   _w['cb'].exclusive:
                    _w['cb'].SetValue(False)

    def OnOptionSelected(self, evt):
        # User clicked on an option
        # Turn on the row to which this option belongs
        _rb=evt.GetEventObject()
        for _w1 in self._widgets.values():
            if _rb in _w1['rb'].values():
                _w1['cb'].SetValue(True)
                # and turn on the OK button
                self.DoOkStatus()
                return

    def DoOkStatus(self, evt=None):
        # ensure the OK button is in the right state
        if evt and evt.IsChecked():
            enable=True
            self._check_for_exclusive(evt.GetEventObject())
        else:
            enable=False
            for _w in self._widgets.values():
                if _w['cb'].GetValue():
                    enable=True
                    break
        self._btn_ok.Enable(enable)
        if evt is not None:
            evt.Skip()

class SendPhoneDialog(GetPhoneDialog):
    HELPID=helpids.ID_SEND_PHONE_DATA

    # actions ("Pretty Name", "name used to query profile")
    actions = (  ("Send", "write"), )
    
    def __init__(self, frame, title, id=-1):
        GetPhoneDialog.__init__(self, frame, title, id)

    # this is what BitPim itself doesn't supports - the phones may support less
    _notsupported=(
        ('call_history', 'write', None),)
        

###
###  The master config dialog
###

class ConfigDialog(wx.Dialog):
    phonemodels=phones.phonemodels
    update_choices=('Never', 'Daily', 'Weekly', 'Monthly')
    setme="<setme>"
    ID_DIRBROWSE=wx.NewId()
    ID_COMBROWSE=wx.NewId()
    ID_RETRY=wx.NewId()
    ID_BITFLING=wx.NewId()
    def __init__(self, mainwindow, frame, title="BitPim Settings", id=-1):
        wx.Dialog.__init__(self, frame, id, title,
                          style=wx.CAPTION|wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE)
        self.mw=mainwindow

        self.bitflingresponsequeues={}

        gs=wx.GridBagSizer(10, 10)
        gs.AddGrowableCol(1)
        _row=0
        # safemode
        gs.Add( wx.StaticText(self, -1, "Read Only"), pos=(_row,0), flag=wx.ALIGN_CENTER_VERTICAL)
        self.safemode=wx.CheckBox(self, wx.NewId(), "Block writing anything to the phone")
        gs.Add( self.safemode, pos=(_row,1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1

        # where we store our files
        gs.Add( wx.StaticText(self, -1, "Disk storage"), pos=(_row,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gs.Add(wx.StaticText(self, -1, self.mw.config.Read('path', '<Unknown>')),
               pos=(_row,1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1
        gs.Add(wx.StaticText(self, -1, 'Config File'), pos=(_row,0),
               flag=wx.ALIGN_CENTER_VERTICAL)
        gs.Add(wx.StaticText(self, -1, self.mw.config.Read('config')),
               pos=(_row,1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1

        # phone type
        gs.Add( wx.StaticText(self, -1, "Phone Type"), pos=(_row,0), flag=wx.ALIGN_CENTER_VERTICAL)
        keys=self.phonemodels
        keys.sort()
        self.phonebox=wx.ComboBox(self, -1, "LG-VX4400", style=wx.CB_DROPDOWN|wx.CB_READONLY,choices=keys)
        self.phonebox.SetValue("LG-VX4400")
        gs.Add( self.phonebox, pos=(_row,1), flag=wx.ALIGN_CENTER_VERTICAL)
        _phone_btn=wx.Button(self, -1, 'Phone Wizard...')
        wx.EVT_BUTTON(self, _phone_btn.GetId(), self.OnPhoneWizard)
        gs.Add(_phone_btn, pos=(_row, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1

        # com port
        gs.Add( wx.StaticText(self, -1, "Com Port"), pos=(_row,0), flag=wx.ALIGN_CENTER_VERTICAL)
        self.commbox=wx.TextCtrl(self, -1, self.setme, size=(200,-1))
        gs.Add( self.commbox, pos=(_row,1), flag=wx.ALIGN_CENTER_VERTICAL)
        gs.Add( wx.Button(self, self.ID_COMBROWSE, "Browse ..."), pos=(_row,2), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1
        # com timeout
        gs.Add(wx.StaticText(self, -1, 'Com Timeout (sec)'), pos=(_row, 0),
               flag=wx.ALIGN_CENTER_VERTICAL)
        self.commtimeout=NumCtrl(self, -1,
                                 integerWidth=2, fractionWidth=1,
                                 allowNegative=False)
        gs.Add(self.commtimeout, pos=(_row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1

        # Automatic check for update
        gs.Add(wx.StaticText(self, -1, 'Check for Update'), pos=(_row,0), flag=wx.ALIGN_CENTER_VERTICAL)
        self.updatebox=wx.ComboBox(self, -1, self.update_choices[0],
                                   style=wx.CB_DROPDOWN|wx.CB_READONLY,
                                   choices=self.update_choices)
        gs.Add(self.updatebox, pos=(_row,1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1

        # always start with the 'Today' tab
        gs.Add(wx.StaticText(self, -1, 'Startup'), pos=(_row,0),
               flag=wx.ALIGN_CENTER_VERTICAL)
        self.startup=wx.CheckBox(self, wx.NewId(), 'Always start with the Today tab')
        gs.Add(self.startup, pos=(_row,1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1

        # whether or not to use TaskBarIcon
        if guihelper.IsMSWindows():
            gs.Add(wx.StaticText(self, -1, 'Task Bar Icon'), pos=(_row,0),
                   flag=wx.ALIGN_CENTER_VERTICAL)
            self.taskbaricon=wx.CheckBox(self, wx.NewId(),
                                         'Place BitPim Icon in the System Tray when Minimized')
            gs.Add(self.taskbaricon, pos=(_row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
            wx.EVT_CHECKBOX(self, self.taskbaricon.GetId(),
                            self.OnTaskbarChkbox)
            _row+=1
            self.taskbaricon1=wx.CheckBox(self, wx.NewId(),
                                         'Place BitPim Icon in the System Tray when Closed')
            self.taskbaricon1.Enable(False)
            gs.Add(self.taskbaricon1, pos=(_row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
            _row+=1
        else:
            self.taskbaricon=None

        # whether or not to run autodetect at startup
        gs.Add(wx.StaticText(self, -1, 'Autodetect at Startup'), pos=(_row,0),
               flag=wx.ALIGN_CENTER_VERTICAL)
        self.autodetect_start=wx.CheckBox(self, wx.NewId(),
                                     'Detect phone at bitpim startup')
        gs.Add(self.autodetect_start, pos=(_row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1
        # Splashscreen time
        gs.Add(wx.StaticText(self, -1, 'SplashScreen Time (sec)'),
               pos=(_row, 0),
               flag=wx.ALIGN_CENTER_VERTICAL)
        self.splashscreen=NumCtrl(self, -1,
                                  integerWidth=2, fractionWidth=1,
                                  allowNegative=False)
        gs.Add(self.splashscreen, pos=(_row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1
        # Developer's Console
        if __debug__:
            gs.Add(wx.StaticText(self, -1, 'Developer Console'),
                   pos=(_row,0),
                   flag=wx.ALIGN_CENTER_VERTICAL)
            self.dev_console=wx.CheckBox(self, wx.NewId(),
                                         'Display Developer Console')
            gs.Add(self.dev_console, pos=(_row, 1),
                   flag=wx.ALIGN_CENTER_VERTICAL)
            _row+=1
        # bitfling
        if bitflingscan.IsBitFlingEnabled():
            self.SetupBitFlingCertVerification()
            gs.Add( wx.StaticText( self, -1, "BitFling"), pos=(_row,0), flag=wx.ALIGN_CENTER_VERTICAL)
            self.bitflingenabled=wx.CheckBox(self, self.ID_BITFLING, "Enabled")
            gs.Add(self.bitflingenabled, pos=(_row,1), flag=wx.ALIGN_CENTER_VERTICAL)
            gs.Add( wx.Button(self, self.ID_BITFLING, "Settings ..."), pos=(_row,2), flag=wx.ALIGN_CENTER_VERTICAL)
            wx.EVT_BUTTON(self, self.ID_BITFLING, self.OnBitFlingSettings)
            wx.EVT_CHECKBOX(self, self.ID_BITFLING, self.ApplyBitFlingSettings)
            if self.mw.config.Read("bitfling/password","<unconfigured>") \
               == "<unconfigured>":
                self.mw.config.WriteInt("bitfling/enabled", 0)
                self.bitflingenabled.SetValue(False)
                self.bitflingenabled.Enable(False)
        else:
            self.bitflingenabled=None
        # crud at the bottom
        bs=wx.BoxSizer(wx.VERTICAL)
        bs.Add(gs, 0, wx.EXPAND|wx.ALL, 10)
        bs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 7)
        
        but=self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP)
        bs.Add(but, 0, wx.CENTER|wx.ALL, 10)

        wx.EVT_BUTTON(self, wx.ID_HELP, self.OnHelp)
        wx.EVT_BUTTON(self, self.ID_COMBROWSE, self.OnComBrowse)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)

        self.setdefaults()

        self.SetSizer(bs)
        self.SetAutoLayout(True)
        bs.Fit(self)

        # Retrieve saved settings... (we only care about position)
        set_size("ConfigDialog", self, screenpct=-1,  aspect=3.5)

        wx.EVT_CLOSE(self, self.OnClose)

    def OnCancel(self, _):
        self.saveSize()

    def OnOK(self, _):
        self.saveSize()
        self.EndModal(wx.ID_OK)
        self.ApplyBitFlingSettings()

    def OnHelp(self, _):
        wx.GetApp().displayhelpid(helpids.ID_SETTINGS_DIALOG)

    def OnComBrowse(self, _):
        self.saveSize()
        if self.mw.wt is not None:
            self.mw.wt.clearcomm()
        # remember its size
        # w=self.mw.config.ReadInt("combrowsewidth", 640)
        # h=self.mw.config.ReadInt("combrowseheight", 480)
        p=self.mw.config.ReadInt("combrowsesash", 200)
        with guihelper.WXDialogWrapper(CommPortDialog(self, common.importas(phones.module(self.phonebox.GetValue())), defaultport=self.commbox.GetValue(), sashposition=p),
                                       True) as (dlg, res):
            self.mw.config.WriteInt("combrowsesash", dlg.sashposition)
            if res==wx.ID_OK:
                self.commbox.SetValue(dlg.GetPort())

    def ApplyBitFlingSettings(self, _=None):
        if self.bitflingenabled is not None:
            if self.bitflingenabled.GetValue():
                bitflingscan.flinger.configure(self.mw.config.Read("bitfling/username", "<unconfigured>"),
                                               bitflingscan.decode(self.mw.config.Read("bitfling/password",
                                                                                       "<unconfigured>")),
                                               self.mw.config.Read("bitfling/host", "<unconfigured>"),
                                               self.mw.config.ReadInt("bitfling/port", 12652))
            else:
                bitflingscan.flinger.unconfigure()

    def OnBitFlingSettings(self, _):
        with guihelper.WXDialogWrapper(BitFlingSettingsDialog(None, self.mw.config),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                dlg.SaveSettings()
        self.ApplyBitFlingSettings()
        if self.mw.config.Read("bitfling/password","<unconfigured>") \
               != "<unconfigured>":
            self.bitflingenabled.Enable(True)
        
    def SetupBitFlingCertVerification(self):
        "Setup all the voodoo needed for certificate verification to happen, not matter which thread wants it"
        EVT_BITFLINGCERTIFICATEVERIFICATION(self, self._wrapVerifyBitFlingCert)
        bitflingscan.flinger.SetCertVerifier(self.dispatchVerifyBitFlingCert)
        bitflingscan.flinger.setthreadeventloop(wx.SafeYield)

    def dispatchVerifyBitFlingCert(self, addr, key):
        """Handle a certificate verification from any thread

        The request is handed to the main gui thread, and then we wait for the
        results"""
        print thread.get_ident(),"dispatchVerifyBitFlingCert called"
        q=self.bitflingresponsequeues.get(thread.get_ident(), None)
        if q is None:
            q=Queue.Queue()
            self.bitflingresponsequeues[thread.get_ident()]=q
        print thread.get_ident(), "Posting BitFlingCertificateVerificationEvent"
        wx.PostEvent(self, BitFlingCertificateVerificationEvent(addr=addr, key=key, q=q))
        print thread.get_ident(), "After posting BitFlingCertificateVerificationEvent, waiting for response"
        res, exc = q.get()
        print thread.get_ident(), "Got response", res, exc
        if exc is not None:
            ex=exc[1]
            ex.gui_exc_info=exc[2]
            raise ex
        return res
        
    def _wrapVerifyBitFlingCert(self, evt):
        """Receive the event in the main gui thread for cert verification

        We unpack the parameters, call the verification method"""
        print "_wrapVerifyBitFlingCert"
        
        addr, hostkey, q = evt.addr, evt.key, evt.q
        self.VerifyBitFlingCert(addr, hostkey, q)

    def VerifyBitFlingCert(self, addr, key, q):
        print "VerifyBitFlingCert for", addr, "type",key.get_name()
        # ::TODO:: reject if not dsa
        # get fingerprint
        fingerprint=common.hexify(key.get_fingerprint())
        # do we already know about it?
        existing=wx.GetApp().config.Read("bitfling/certificates/%s" % (addr[0],), "")
        if len(existing):
            fp=existing
            if fp==fingerprint:
                q.put( (True, None) )
                return
        # throw up the dialog
        print "asking user"
        dlg=AcceptCertificateDialog(None, wx.GetApp().config, addr, fingerprint, q)
        dlg.ShowModal()

    def OnClose(self, evt):
        self.saveSize()
        # Don't destroy the dialong, just put it away...
        self.EndModal(wx.ID_CANCEL)

    def OnTaskbarChkbox(self, evt):
        if evt.IsChecked():
            self.taskbaricon1.Enable(True)
        else:
            self.taskbaricon1.SetValue(False)
            self.taskbaricon1.Enable(False)

    def setfromconfig(self):
        if len(self.mw.config.Read("lgvx4400port")):
            self.commbox.SetValue(self.mw.config.Read("lgvx4400port", ""))
        self.commtimeout.SetValue(self.mw.config.ReadFloat('commtimeout', 3.0))
        if self.mw.config.Read("phonetype", "") in self.phonemodels:
            self.phonebox.SetValue(self.mw.config.Read("phonetype"))
        if self.bitflingenabled is not None:
            self.bitflingenabled.SetValue(self.mw.config.ReadInt("bitfling/enabled", 0))
            self.ApplyBitFlingSettings()
        self.safemode.SetValue(self.mw.config.ReadInt("Safemode", 0))
        self.updatebox.SetValue(self.mw.config.Read("updaterate",
                                                    self.update_choices[0]))
        self.startup.SetValue(self.mw.config.ReadInt("startwithtoday", 0))
        if self.taskbaricon:
            if self.mw.config.ReadInt('taskbaricon', 0):
                self.taskbaricon.SetValue(True)
                self.taskbaricon1.Enable(True)
                self.taskbaricon1.SetValue(self.mw.config.ReadInt('taskbaricon1', 0))
            else:
                self.taskbaricon.SetValue(False)
                self.taskbaricon1.SetValue(False)
                self.taskbaricon1.Enable(False)
        self.autodetect_start.SetValue(self.mw.config.ReadInt("autodetectstart", 0))
        self.splashscreen.SetValue(self.mw.config.ReadInt('splashscreentime', 2500)/1000.0)
        if __debug__:
            self.dev_console.SetValue(self.mw.config.ReadInt('console', 0))

    def setdefaults(self):
        if self.commbox.GetValue()==self.setme:
            comm="auto"
            self.commbox.SetValue(comm)

    def updatevariables(self):
        path=self.mw.config.Read('path')
        self.mw.configpath=path
        self.mw.commportsetting=str(self.commbox.GetValue())
        self.mw.config.Write("lgvx4400port", self.mw.commportsetting)
        self.mw.config.WriteFloat('commtimeout',
                                  float(self.commtimeout.GetValue()))
        if self.mw.wt is not None:
            self.mw.wt.clearcomm()
        # comm parameters (retry, timeouts, flow control etc)
        commparm={}
        commparm['retryontimeout']=self.mw.config.ReadInt("commretryontimeout", False)
        commparm['timeout']=self.mw.config.ReadFloat('commtimeout', 3.0)
        commparm['hardwareflow']=self.mw.config.ReadInt('commhardwareflow', False)
        commparm['softwareflow']=self.mw.config.ReadInt('commsoftwareflow', False)
        commparm['baud']=self.mw.config.ReadInt('commbaud', 115200)
        self.mw.commparams=commparm
        # phone model
        self.mw.config.Write("phonetype", self.phonebox.GetValue())
        # do not touch this module importing code unless you check
        # that it also works with the freezing tools (py2exe, py2app,
        # cxfreeze etc).  doing the sane sensible thing (__import__)
        # results in the wrong module being loaded!
        mod=phones.module(self.phonebox.GetValue())
        exec("import "+mod)
        self.mw.phonemodule=eval(mod)
        self.mw.phoneprofile=self.mw.phonemodule.Profile()
        pubsub.publish(pubsub.PHONE_MODEL_CHANGED, self.mw.phonemodule)
        #  bitfling
        if self.bitflingenabled is not None:
            self.mw.bitflingenabled=self.bitflingenabled.GetValue()
            self.mw.config.WriteInt("bitfling/enabled", self.mw.bitflingenabled)
        # safemode - make sure you have to restart to disable
        self.mw.config.WriteInt("SafeMode", self.safemode.GetValue())
        if self.safemode.GetValue():
            wx.GetApp().SAFEMODE=True
        wx.GetApp().ApplySafeMode()
        # check for update rate
        self.mw.config.Write('updaterate', self.updatebox.GetValue())
        # startup option
        self.mw.config.WriteInt('startwithtoday', self.startup.GetValue())
        # Task Bar Icon option
        if self.taskbaricon:
            self.mw.config.WriteInt('taskbaricon', self.taskbaricon.GetValue())
            self.mw.config.WriteInt('taskbaricon1', self.taskbaricon1.GetValue())
        else:
            self.mw.config.WriteInt('taskbaricon', 0)
            self.mw.config.WriteInt('taskbaricon1', 0)
        # startup autodetect option
        self.mw.config.WriteInt('autodetectstart', self.autodetect_start.GetValue())
        # SplashScreen Time
        self.mw.config.WriteInt('splashscreentime',
                                int(self.splashscreen.GetValue()*1000))
        # developer console
        if __debug__:
            self.mw.config.WriteInt('console',
                                    self.dev_console.GetValue())
        # ensure config is saved
        self.mw.config.Flush()
        # update the status bar
        self.mw.SetPhoneModelStatus()
        # update the cache path
        self.mw.update_cache_path()

    def needconfig(self):
        # Set base config
        self.setfromconfig()
        # do we know the phone?
        if self.mw.config.Read("phonetype", "") not in self.phonemodels:
            return True
        # are any at unknown settings
        if self.commbox.GetValue()==self.setme:
            # fill in and set defaults
            self.setdefaults()
            self.updatevariables()
            # any still unset?
            if self.commbox.GetValue()==self.setme:
                return True

        return False

    def ShowModal(self):
        self.setfromconfig()
        ec=wx.Dialog.ShowModal(self)
        if ec==wx.ID_OK:
            self.updatevariables()
        return ec

    def saveSize(self):
        save_size("ConfigDialog", self.GetRect())

    def OnPhoneWizard(self, _):
        # clear the port
        if self.mw.wt is not None:
            self.mw.wt.clearcomm()
        # running the set phone wizard
        _wz=setphone_wizard.SetPhoneWizard(self)
        if _wz.RunWizard():
            _res=_wz.get()
            self.commbox.SetValue(_res.get('com', ''))
            self.phonebox.SetValue(_res.get('phone', ''))

###
### The select a comm port dialog box
###

class CommPortDialog(wx.Dialog):
    ID_LISTBOX=1
    ID_TEXTBOX=2
    ID_REFRESH=3
    ID_SASH=4
    ID_SAVE=5
    
    def __init__(self, parent, selectedphone, id=-1, title="Choose a comm port", defaultport="auto", sashposition=0):
        wx.Dialog.__init__(self, parent, id, title, style=wx.CAPTION|wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.parent=parent
        self.port=defaultport
        self.sashposition=sashposition
        self.selectedphone=selectedphone
        
        p=self # parent widget

        # the listbox and textbox in a splitter
        splitter=wx.SplitterWindow(p, self.ID_SASH, style=wx.SP_3D|wx.SP_LIVE_UPDATE)
        self.lb=wx.ListBox(splitter, self.ID_LISTBOX, style=wx.LB_SINGLE|wx.LB_HSCROLL|wx.LB_NEEDED_SB)
        self.tb=wx.html.HtmlWindow(splitter, self.ID_TEXTBOX, size=wx.Size(400,400)) # default style is auto scrollbar
        # On Mac, top pane will go to zero size on startup completely ignoring the sashposition passed in.
        # We ensure that the top pane is always visible ...
        splitter.SetMinimumPaneSize(100)
        splitter.SplitHorizontally(self.lb, self.tb, sashposition)

        # the buttons
        buttsizer=wx.GridSizer(1, 5)
        buttsizer.Add(wx.Button(p, wx.ID_OK, "OK"), 0, wx.ALL, 10)
        buttsizer.Add(wx.Button(p, self.ID_REFRESH, "Refresh"), 0, wx.ALL, 10)
        buttsizer.Add(wx.Button(p, self.ID_SAVE, "Save..."), 0, wx.ALL, 10)
        buttsizer.Add(wx.Button(p, wx.ID_HELP, "Help"), 0, wx.ALL, 10)
        buttsizer.Add(wx.Button(p, wx.ID_CANCEL, "Cancel"), 0, wx.ALL, 10)

        # vertical join of the two
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(splitter, 1, wx.EXPAND)
        vbs.Add(buttsizer, 0, wx.CENTER)

        # hook into self
        p.SetSizer(vbs)
        p.SetAutoLayout(True)
        vbs.Fit(p)

        # update dialog
        wx.CallAfter(self.OnRefresh)

        # hook in all the widgets
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
        wx.EVT_BUTTON(self, wx.ID_HELP, self.OnHelp)
        wx.EVT_BUTTON(self, self.ID_REFRESH, self.OnRefresh)
        wx.EVT_BUTTON(self, self.ID_SAVE, self.OnSave)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
        wx.EVT_LISTBOX(self, self.ID_LISTBOX, self.OnListBox)
        wx.EVT_LISTBOX_DCLICK(self, self.ID_LISTBOX, self.OnListBox)
        wx.EVT_SPLITTER_SASH_POS_CHANGED(self, self.ID_SASH, self.OnSashChange)

        # Retrieve saved settings... Use 60% of screen if not specified
        set_size("CommDialog", self, screenpct=60)
        wx.EVT_CLOSE(self, self.OnClose)

    def OnSashChange(self, _=None):
        self.sashposition=self.FindWindowById(self.ID_SASH).GetSashPosition()

    def OnRefresh(self, _=None):
        self.tb.SetPage("<p><b>Refreshing</b> ...")
        self.lb.Clear()
        self.Update()
        ports=comscan.comscan()+usbscan.usbscan()
        if bitflingscan.IsBitFlingEnabled():
            ports=ports+bitflingscan.flinger.scan()
        self.portinfo=comdiagnose.diagnose(ports, self.selectedphone)
        if len(self.portinfo):
            self.portinfo=[ ("Automatic", "auto",
                             "<p>BitPim will try to detect the correct port automatically when accessing your phone"
                             ) ]+\
                           self.portinfo
        self.lb.Clear()
        sel=-1
        for name, actual, description in self.portinfo:
            if sel<0 and self.GetPort()==actual:
                sel=self.lb.GetCount()
            self.lb.Append(name)
        if sel<0:
            sel=0
        if self.lb.GetCount():
            self.lb.SetSelection(sel)
            self.OnListBox()
        else:
            self.FindWindowById(wx.ID_OK).Enable(False)
            self.tb.SetPage("<html><body>You do not have any com/serial ports on your system</body></html>")

    def OnListBox(self, _=None):
        # enable/disable ok button
        p=self.portinfo[self.lb.GetSelection()]
        if p[1] is None:
            self.FindWindowById(wx.ID_OK).Enable(False)
        else:
            self.port=p[1]
            self.FindWindowById(wx.ID_OK).Enable(True)
        self.tb.SetPage(p[2])
        

    def OnSave(self, _):
        html=StringIO.StringIO()
        
        print >>html, "<html><head><title>BitPim port listing - %s</title></head>" % (time.ctime(), )
        print >>html, "<body><h1>BitPim port listing - %s</h1><table>" % (time.ctime(),)

        for long,actual,desc in self.portinfo:
            if actual is None or actual=="auto": continue
            print >>html, '<tr  bgcolor="#77ff77"><td colspan=2>%s</td><td>%s</td></tr>' % (long,actual)
            print >>html, "<tr><td colspan=3>%s</td></tr>" % (desc,)
            print >>html, "<tr><td colspan=3><hr></td></tr>"
        print >>html, "</table></body></html>"
        with guihelper.WXDialogWrapper(wx.FileDialog(self, "Save port details as", defaultFile="bitpim-ports.html", wildcard="HTML files (*.html)|*.html",
                                                     style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                file(dlg.GetPath(), "wt").write(html.getvalue())

    def OnCancel(self, _):
        self.saveSize()
        self.EndModal(wx.ID_CANCEL)

    def OnOk(self, _):
        self.saveSize()
        self.EndModal(wx.ID_OK)

    def OnHelp(self, _):
        wx.GetApp().displayhelpid(helpids.ID_COMMSETTINGS_DIALOG)

    def OnClose(self, evt):
        self.saveSize()
        # Don't destroy the dialong, just put it away...
        self.EndModal(wx.ID_CANCEL)

    def GetPort(self):
        return self.port

    def saveSize(self):
        save_size("CommDialog", self.GetRect())

###
###  Accept certificate dialog
###


class AcceptCertificateDialog(wx.Dialog):

    def __init__(self, parent, config, addr, fingerprint, q):
        parent=self.FindAGoodParent(parent)
        wx.Dialog.__init__(self, parent, -1, "Accept certificate?", style=wx.CAPTION|wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.config=config
        self.q=q
        self.addr=addr
        self.fingerprint=fingerprint
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.StaticText(self, -1, "Host:"), 0, wx.ALL, 5)
        hbs.Add(wx.StaticText(self, -1, addr[0]), 0, wx.ALL, 5)
        hbs.Add(wx.StaticText(self, -1, " Fingerprint:"), 0, wx.ALL, 5)
        hbs.Add(wx.StaticText(self, -1, fingerprint), 1, wx.ALL, 5)
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 7)
        but=self.CreateButtonSizer(wx.YES|wx.NO|wx.HELP)
        vbs.Add(but, 0, wx.ALIGN_CENTER|wx.ALL, 10)

        self.SetSizer(vbs)
        vbs.Fit(self)

        wx.EVT_BUTTON(self, wx.ID_YES, self.OnYes)
        wx.EVT_BUTTON(self, wx.ID_NO, self.OnNo)
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnNo)



    def OnYes(self, _):
        wx.GetApp().config.Write("bitfling/certificates/%s" % (self.addr[0],), self.fingerprint)
        wx.GetApp().config.Flush()
        if self.IsModal():
            self.EndModal(wx.ID_YES)
        else:
            self.Show(False)
        wx.CallAfter(self.Destroy)
        print "returning true from AcceptCertificateDialog"
        self.q.put( (True, None) )

    def OnNo(self, _):
        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Show(False)
        wx.CallAfter(self.Destroy)
        print "returning false from AcceptCertificateDialog"
        self.q.put( (False, None) )

    def FindAGoodParent(self, suggestion):
        win=wx.Window_FindFocus()
        while win is not None:
            try:
                if win.IsModal():
                    print "FindAGoodParent is",win
                    return win
            except AttributeError:
                parent=win.GetParent()
                win=parent
        return suggestion
        
###
###  BitFling settings dialog
###

class BitFlingSettingsDialog(wx.Dialog):

    ID_USERNAME=wx.NewId()
    ID_PASSWORD=wx.NewId()
    ID_HOST=wx.NewId()
    ID_PORT=wx.NewId()
    ID_TEST=wx.NewId()
    passwordsentinel="@+_-3@<,"

    def __init__(self, parent, config):
        wx.Dialog.__init__(self, parent, -1, "Edit BitFling settings", style=wx.CAPTION|wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.config=config
        gs=wx.FlexGridSizer(1, 2, 5, 5)
        gs.AddGrowableCol(1)
        gs.AddMany([
            (wx.StaticText(self, -1, "Username"), 0, wx.ALIGN_CENTER_VERTICAL),
            (wx.TextCtrl(self, self.ID_USERNAME), 1, wx.EXPAND),
            (wx.StaticText(self, -1, "Password"), 0, wx.ALIGN_CENTER_VERTICAL),
            (wx.TextCtrl(self, self.ID_PASSWORD, style=wx.TE_PASSWORD), 1, wx.EXPAND),
            (wx.StaticText(self, -1, "Host"), 0, wx.ALIGN_CENTER_VERTICAL),
            (wx.TextCtrl(self, self.ID_HOST), 1, wx.EXPAND),
            (wx.StaticText(self, -1, "Port"), 0, wx.ALIGN_CENTER_VERTICAL),
            (wx.lib.intctrl.IntCtrl(self, self.ID_PORT, value=12652, min=1, max=65535), 0)
            ])
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(gs, 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add((1,1), 1, wx.EXPAND)
        vbs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 10)

        gs=wx.GridSizer(1,4, 5,5)
        gs.Add(wx.Button(self, wx.ID_OK, "OK"))
        gs.Add(wx.Button(self, self.ID_TEST, "Test"))
        gs.Add(wx.Button(self, wx.ID_HELP, "Help"))
        gs.Add(wx.Button(self, wx.ID_CANCEL, "Cancel"))
        vbs.Add(gs, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        self.SetSizer(vbs)
        vbs.Fit(self)
        set_size("BitFlingConfigDialog", self, -20, 0.5)

        # event handlers
        wx.EVT_BUTTON(self, self.ID_TEST, self.OnTest)

        # fill in data
        defaultuser="user"
        try:
            defaultuser=getpass.getuser()
        except:
            pass
        self.FindWindowById(self.ID_USERNAME).SetValue(config.Read("bitfling/username", defaultuser))
        if len(config.Read("bitfling/password", "")):
            self.FindWindowById(self.ID_PASSWORD).SetValue(self.passwordsentinel)
        self.FindWindowById(self.ID_HOST).SetValue(config.Read("bitfling/host", ""))
        self.FindWindowById(self.ID_PORT).SetValue(config.ReadInt("bitfling/port", 12652))

    def ShowModal(self):
        res=wx.Dialog.ShowModal(self)
        save_size("BitFlingConfigDialog", self.GetRect())
        return res

    def GetSettings(self):
        username=self.FindWindowById(self.ID_USERNAME).GetValue()
        pwd=self.FindWindowById(self.ID_PASSWORD).GetValue()
        if pwd==self.passwordsentinel:
            pwd=bitflingscan.decode(self.config.Read("bitfling/password", self.passwordsentinel))
        host=self.FindWindowById(self.ID_HOST).GetValue()
        port=self.FindWindowById(self.ID_PORT).GetValue()
        return username, pwd, host, port

    def SaveSettings(self):
        "Copy settings from dialog fields into config object"
        username,pwd,host,port=self.GetSettings()
        self.config.Write("bitfling/username", username)
        self.config.Write("bitfling/password", bitflingscan.encode(pwd))
        self.config.Write("bitfling/host", host)
        self.config.WriteInt("bitfling/port", port)

    def OnTest(self, _):
        wx.CallAfter(self._OnTest)

    def _OnTest(self, _=None):
        try:
            bitflingscan.flinger.configure(*self.GetSettings())
            res=bitflingscan.flinger.getversion()
            guihelper.MessageDialog(self, "Succeeded. Remote version is %s" % (res,) , "Success", wx.OK|wx.ICON_INFORMATION)
        except Exception,ex:
            res="Failed: %s: %s" % sys.exc_info()[:2]
            if hasattr(ex, "gui_exc_info"):
                print common.formatexception( ex.gui_exc_info)
            else:
                print common.formatexception()
            guihelper.MessageDialog(self, res, "Failed", wx.OK|wx.ICON_ERROR)


###
### Various platform independent filename functions
###

basename=common.basename
stripext=common.stripext
getext=common.getext


###
### A dialog showing a message in a fixed font, with a help button
###

class MyFixedScrolledMessageDialog(wx.Dialog):
    """A dialog displaying a readonly text control with a fixed width font"""
    def __init__(self, parent, msg, caption, helpid, pos = wx.DefaultPosition, size = (850,600)):
        wx.Dialog.__init__(self, parent, -1, caption, pos, size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        text=wx.TextCtrl(self, 1,
                        style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 |
                        wx.TE_DONTWRAP  )
        # Fixed width font
        f=wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL )
        ta=wx.TextAttr(font=f)
        text.SetDefaultStyle(ta)

        text.AppendText(msg) # if i supply this in constructor then the font doesn't take
        text.SetInsertionPoint(0)
        text.ShowPosition(text.XYToPosition(0,0))

        # vertical sizer
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(text, 1, wx.EXPAND|wx.ALL, 10)

        # buttons
        vbs.Add(self.CreateButtonSizer(wx.OK|wx.HELP), 0, wx.ALIGN_RIGHT|wx.ALL, 10)

        # plumb
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        wx.EVT_BUTTON(self, wx.ID_HELP, lambda _,helpid=helpid: wx.GetApp().displayhelpid(helpid))

###
###  Dialog that deals with exceptions
###
import StringIO

class ExceptionDialog(wx.Dialog):
    def __init__(self, parent, exception, title="Exception"):
        wx.Dialog.__init__(self, parent, title=title, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME|wx.MAXIMIZE_BOX, size=(740, 580))
        self.maintext=wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2|wx.HSCROLL)
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(self.maintext, 1, wx.EXPAND|wx.ALL, 5)

        buttsizer=wx.GridSizer(1, 4)
        buttsizer.Add(wx.Button(self, wx.ID_CANCEL, "Abort BitPim"), 0, wx.ALL, 10)
        buttsizer.Add(wx.Button(self, wx.ID_HELP, "Help"), 0, wx.ALL, 10)
        buttsizer.Add(wx.Button(self, wx.ID_OK, "Continue"), 0, wx.ALL, 10)
        _id=wx.NewId()
        buttsizer.Add(wx.Button(self, _id, "Create Trouble Report"), 0, wx.ALL, 10)

        vbs.Add(buttsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.abort)
        wx.EVT_BUTTON(self, wx.ID_HELP, lambda _: wx.GetApp().displayhelpid(helpids.ID_EXCEPTION_DIALOG))
        wx.EVT_BUTTON(self, _id, self.OnCreateReport)
        
        self.SetSizer(vbs)
        self._text=""
        self.addexception(exception)

    def abort(self,_):
        import os
        os._exit(1)
        
    def addexception(self, exception):
        s=StringIO.StringIO()
        s.write("BitPim version: "+version.versionstring+"-"+version.vendor+"\nAn unexpected exception has occurred.\nPlease see the help for details on what to do.\n\n")
        if hasattr(exception, 'gui_exc_info'):
            s.write(common.formatexception(exception.gui_exc_info))
        else:
            s.write("Exception with no extra info.\n%s\n" % (exception.str(),))
        self._text=s.getvalue()
        self.maintext.SetValue(self._text)
        
    def getexceptiontext(self):
        return self._text

    def OnCreateReport(self, _):
        with guihelper.WXDialogWrapper(CreateTroubleReportDialog(self.GetParent()),
                                       True) as (_dlg, retcode):
            if retcode==wx.ID_OK:
                try:
                    self._create_report(_dlg.GetValue())
                    guihelper.MessageDialog(self,
                                            'Trouble Report created successfully!',
                                            'BitPim Trouble Report', style=wx.OK)
                except:
                    guihelper.MessageDialog(self,
                                            'Failed to Create Trouble Report',
                                            'Trouble Report Error',
                                            style=wx.OK|wx.ICON_ERROR)

    def _create_report(self, vals):
        with contextlib.closing(gzip.GzipFile(vals['filename'], 'wb')) as _s:
            _s.write('BitPim Trouble Report\n')
            _s.write(time.asctime()+'\n')
            _s.write('BitPim Version: %s - %s\n'%(version.versionstring, version.vendor))
            _s.write('Platorm: %s, Architecture: %s %s, Dist: %s %s %s\n'%\
                        ((platform.platform(),)+platform.architecture()+\
                         platform.dist()))
            # phone model if available
            try:
                _model=self.GetParent().phonemodule.Phone.desc
            except:
                _model='Not Available'
            _s.write('Phone Model: %s\n'%_model)
            _s.write('Name: %s\n'%vals['name'])
            _s.write('email: %s\n'%vals['email'])
            _s.write('Description: %s\n'%vals['description'])
            _s.write('Exception:\n%s\n'%self._text)
            # write out log data if evailable
            try:
                _log=self.GetParent().tree.lw.GetValue()
            except:
                # don't care if we can't get the log
                _log='Not Available'
            _s.write('BitPim Log:\n%s\n'%_log)
            # write out protocol data if available
            try:
                _log=self.GetParent().tree.lwdata.GetValue()
            except:
                _log='Not Available'
            _s.write('BitPim Protocol Data:\n%s\n'%_log)

class CreateTroubleReportDialog(wx.Dialog):

    _default_filename='bpbug.gz'
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'BitPim Trouble Report',
                          style=wx.CAPTION|wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE)

        gs=wx.GridBagSizer(10, 10)
        gs.AddGrowableCol(1)
        _width=300
        _row=0
        # Name
        gs.Add( wx.StaticText(self, -1, "Name:"), pos=(_row,0),
                flag=wx.ALIGN_CENTER_VERTICAL)
        self._name=wx.TextCtrl(self, -1, '', size=(_width,-1))
        gs.Add(self._name, pos=(_row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1
        # email
        gs.Add( wx.StaticText(self, -1, "email:"), pos=(_row,0), flag=wx.ALIGN_CENTER_VERTICAL)
        self._email=wx.TextCtrl(self, -1, '', size=(_width,-1))
        gs.Add(self._email, pos=(_row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1
        # trouble report file name
        gs.Add( wx.StaticText(self, -1, "File Name:"), pos=(_row,0), flag=wx.ALIGN_CENTER_VERTICAL)
        self._filename=wx.TextCtrl(self, -1, self._default_filename,
                                   size=(_width,-1))
        gs.Add(self._filename, pos=(_row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        _browseid=wx.NewId()
        gs.Add(wx.Button(self, _browseid, 'Browse ...'), pos=(_row, 2),
               flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1
        # Trouble Description
        gs.Add(wx.StaticText(self, -1, 'Trouble Description:'), pos=(_row, 0),
               flag=wx.ALIGN_CENTER_VERTICAL)
        self._desc=wx.TextCtrl(self, -1, '',
                               style=wx.TE_MULTILINE|wx.TE_BESTWRAP,
                               size=(_width, 100))
        gs.Add(self._desc, pos=(_row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        _row+=1

        # crud at the bottom
        bs=wx.BoxSizer(wx.VERTICAL)
        bs.Add(gs, 0, wx.EXPAND|wx.ALL, 10)
        bs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 7)
        
        but=self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP)
        bs.Add(but, 0, wx.CENTER|wx.ALL, 10)

        wx.EVT_BUTTON(self, wx.ID_HELP, self.OnHelp)
        wx.EVT_BUTTON(self, _browseid, self.OnBrowse)

        self.SetSizer(bs)
        self.SetAutoLayout(True)
        bs.Fit(self)

    def OnHelp(self, _):
        wx.GetApp().displayhelpid(helpids.ID_TROUBLEREPORT)
    def OnBrowse(self, _):
        # how to select a source, default to select a file
        with guihelper.WXDialogWrapper(wx.FileDialog(self, self._filename.GetValue(),
                                                     defaultFile=self._filename.GetValue(),
                                                     style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
                                                     wildcard='gzip files|*.gz'),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self._filename.SetValue(dlg.GetPath())
    def GetValue(self):
        # return a dict of values of this dialog
        return { 'name': self._name.GetValue(),
                 'email': self._email.GetValue(),
                 'filename': self._filename.GetValue(),
                 'description': self._desc.GetValue(),
                 }

###
###  Too much freaking effort for a simple statusbar.  Mostly copied from the demo.
###
BUFFERED=0
class StatusText(stattext.GenStaticText):
    # Status value
    red=None
    green=None
    yellow=None
    def __init__(self, parent, ID, label,
                 pos = wx.DefaultPosition, size = wx.DefaultSize,
                 style = 0,
                 name = "statustext"):
        # margin between the stoplight and the text
        self._text_margin=5
        # relative size of the status stoplight, default to 100% of the height
        self._status_size=1.0
        # color for the stop light
        if StatusText.red is None:
            StatusText.red=wx.RED
            StatusText.green=wx.GREEN
            StatusText.yellow=wx.NamedColour('YELLOW')
        self._stat=StatusText.green
        super(StatusText, self).__init__(parent, ID, label,
                                         pos=pos, style=style, name=name)
    def DoGetBestSize(self):
        """
        Overridden base class virtual.  Determines the best size of
        the control based on the label size and the current font.
        """
        _s=super(StatusText, self).DoGetBestSize()
        _s.SetWidth(_s.GetWidth()+_s.GetHeight()*self._status_size+\
                    self._text_margin)
        self.CacheBestSize(_s)
        return _s
    def _draw_status(self, dc, w, h):
        # draw the status stoplight
        dc.BeginDrawing()
        dc.SetBrush(wx.Brush(self._stat, wx.SOLID))
        _r=(h*self._status_size)/2
        dc.DrawCircle(_r, h/2, _r)
        dc.EndDrawing

    def OnPaint(self, event):
        if BUFFERED:
            dc = wx.BufferedPaintDC(self)
        else:
            dc = wx.PaintDC(self)
        width, height = self.GetClientSize()
        if not width or not height:
            return

        if BUFFERED:
            clr = self.GetBackgroundColour()
            backBrush = wx.Brush(clr, wx.SOLID)
            if wx.Platform == "__WXMAC__" and clr == self.defBackClr:
                # if colour is still the default then use the striped background on Mac
                backBrush.MacSetTheme(1) # 1 == kThemeBrushDialogBackgroundActive
            dc.SetBackground(backBrush)
            dc.Clear()
        self._draw_status(dc, width, height)
        dc.SetTextForeground(self.GetForegroundColour())
        dc.SetFont(self.GetFont())
        label = self.GetLabel()
        style = self.GetWindowStyleFlag()
        y = 0
        x=height*self._status_size+self._text_margin
        for line in label.split('\n'):
            if line == '':
                w, h = self.GetTextExtent('W')  # empty lines have height too
            else:
                w, h = self.GetTextExtent(line)
            if style & wx.ALIGN_RIGHT:
                x = width - w
            if style & wx.ALIGN_CENTER:
                x = (width - w)/2
            dc.DrawText(line, x, y)
            y += h

    def SetLabel(self, label, status=None):
        if status:
            self._stat=status
        super(StatusText, self).SetLabel(label)
    def SetStatus(self, status):
        self._stat=status
        self.Refresh()

SB_Phone_Set=0
SB_Phone_Detected=1
SB_Phone_Unavailable=2
class MyStatusBar(wx.StatusBar):
    __total_panes=3
    __version_index=2
    __phone_model_index=2
    __app_status_index=0
    __gauge_index=1
    __major_progress_index=2
    __minor_progress_index=2
    __help_str_index=2
    __general_pane=2
    __pane_width=[70, 180, -1]
    
    def __init__(self, parent, id=-1):
        wx.StatusBar.__init__(self, parent, id)
        self.__major_progress_text=self.__version_text=self.__phone_text=''
        self.sizechanged=False
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_IDLE(self, self.OnIdle)
        self.gauge=wx.Gauge(self, 1000, 1)
        self._status=StatusText(self, -1, '', style=wx.ST_NO_AUTORESIZE)
        self._phone_model=StatusText(self, -1, '', style=wx.ST_NO_AUTORESIZE)
        self.SetFieldsCount(self.__total_panes)
        self.SetStatusWidths(self.__pane_width)
##        self.Reposition()

    def OnSize(self,_):
        self.sizechanged=True

    def OnIdle(self,_):
        if not len(self.GetStatusText(self.__general_pane)):
            self.__set_version_phone_text()
        if self.sizechanged:
            try:
                self.Reposition()
            except:
                # this works around a bug in wx (on Windows only)
                # where we get a bogus exception.  See SF bug
                # 873155 
                pass

    def Reposition(self):
        self.sizechanged = False
        rect=self.GetFieldRect(self.__gauge_index)
        self.gauge.SetPosition(wx.Point(rect.x+2, rect.y+2))
        self.gauge.SetSize(wx.Size(rect.width-4, rect.height-4))
        rect=self.GetFieldRect(self.__app_status_index)
        self._status.SetPosition(wx.Point(rect.x+2, rect.y+2))
        self._status.SetSize(wx.Size(rect.width-4, rect.height-4))
        rect=self.GetFieldRect(self.__phone_model_index)
        self._phone_model.SetPosition(wx.Point(rect.x+rect.width/2+2, rect.y+2))
        self._phone_model.SetSize(wx.Size(rect.width/2-4, rect.height-4))

    def progressminor(self, pos, max, desc=""):
        self.gauge.SetRange(max)
        self.gauge.SetValue(pos)
        if len(self.__major_progress_text):
            s=self.__major_progress_text
            if len(desc):
                s+=' - '+desc
        else:
            s=desc
        self.SetStatusText(s, self.__minor_progress_index)

    def progressmajor(self, pos, max, desc=""):
        if len(desc) and max:
            self.__major_progress_text="%d/%d %s" % (pos+1, max, desc)
        else:
            self.__major_progress_text=desc
        self.progressminor(0,1)

    def GetHelpPane(self):
        return self.__help_str_index
    def set_app_status_ready(self):
        self._status.SetLabel('Ready', StatusText.green)
    def set_app_status_busy(self):
        self._status.SetLabel('BUSY', StatusText.red)
    def set_phone_model(self, str='', status=SB_Phone_Set):
        if status==SB_Phone_Detected:
            self.__phone_text=str+' - Detected'
            _stat=StatusText.green
        elif status==SB_Phone_Set:
            self.__phone_text=str+' - Manually Set'
            _stat=StatusText.yellow
        else:
            self.__phone_text=str+' - Unavailable'
            _stat=StatusText.red
        self._phone_model.SetLabel(self.__phone_text, _stat)
    def set_versions(self, current, latest=''):
        s='BitPim '+current
        if len(latest):
            s+='/Latest '+latest
        else:
            s+='/Latest <Unknown>'
        self.__version_text=s
        self.__set_version_phone_text()
    def __set_version_phone_text(self):
        self.SetStatusText(self.__version_text, self.__version_index)

###
###  A MessageBox with a help button
###

class AlertDialogWithHelp(wx.Dialog):
    """A dialog box with Ok button and a help button"""
    def __init__(self, parent, message, caption, helpfn, style=wx.DEFAULT_DIALOG_STYLE, icon=wx.ICON_EXCLAMATION):
        wx.Dialog.__init__(self, parent, -1, caption, style=style|wx.DEFAULT_DIALOG_STYLE)

        p=self # parent widget

        # horiz sizer for bitmap and text
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.StaticBitmap(p, -1, wx.ArtProvider_GetBitmap(self.icontoart(icon), wx.ART_MESSAGE_BOX)), 0, wx.CENTER|wx.ALL, 10)
        hbs.Add(wx.StaticText(p, -1, message), 1, wx.CENTER|wx.ALL, 10)

        # the buttons
        buttsizer=self.CreateButtonSizer(wx.HELP|style)

        # Both vertical
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(hbs, 1, wx.EXPAND|wx.ALL, 10)
        vbs.Add(buttsizer, 0, wx.CENTER|wx.ALL, 10)

        # wire it in
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

        wx.EVT_BUTTON(self, wx.ID_HELP, helpfn)

    def icontoart(self, id):
        if id&wx.ICON_EXCLAMATION:
            return wx.ART_WARNING
        if id&wx.ICON_INFORMATION:
            return wx.ART_INFORMATION
        # ::TODO:: rest of these
        # fallthru
        return wx.ART_INFORMATION

###
### Yet another dialog with user selectable buttons
###

class AnotherDialog(wx.Dialog):
    """A dialog box with user supplied buttons"""
    def __init__(self, parent, message, caption, buttons, helpfn=None,
                 style=wx.DEFAULT_DIALOG_STYLE, icon=wx.ICON_EXCLAMATION):
        """Constructor

        @param message:  Text displayed in body of dialog
        @param caption:  Title of dialog
        @param buttons:  A list of tuples.  Each tuple is a string and an integer id.
                         The result of calling ShowModal() is the id
        @param helpfn:  The function called if the user presses the help button (wx.ID_HELP)
        """
        wx.Dialog.__init__(self, parent, -1, caption, style=style)

        p=self # parent widget

        # horiz sizer for bitmap and text
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.StaticBitmap(p, -1, wx.ArtProvider_GetBitmap(self.icontoart(icon), wx.ART_MESSAGE_BOX)), 0, wx.CENTER|wx.ALL, 10)
        hbs.Add(wx.StaticText(p, -1, message), 1, wx.CENTER|wx.ALL, 10)

        # the buttons
        buttsizer=wx.BoxSizer(wx.HORIZONTAL)
        for label,id in buttons:
            buttsizer.Add( wx.Button(self, id, label), 0, wx.ALL|wx.ALIGN_CENTER, 5)
            if id!=wx.ID_HELP:
                wx.EVT_BUTTON(self, id, self.OnButton)
            else:
                wx.EVT_BUTTON(self, wx.ID_HELP, helpfn)
                
        # Both vertical
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(hbs, 1, wx.EXPAND|wx.ALL, 10)
        vbs.Add(buttsizer, 0, wx.CENTER|wx.ALL, 10)

        # wire it in
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

    def OnButton(self, event):
        self.EndModal(event.GetId())

    def icontoart(self, id):
        if id&wx.ICON_EXCLAMATION:
            return wx.ART_WARNING
        if id&wx.ICON_INFORMATION:
            return wx.ART_INFORMATION
        # ::TODO:: rest of these
        # fallthru
        return wx.ART_INFORMATION

###
###  Window geometry/positioning memory
###


def set_size(confname, window, screenpct=50, aspect=1.0):
    """Sets remembered/calculated dimensions/position for window

    @param confname: subkey to store/get this windows's settings from
    @param window:  the window object itself
    @param screenpct: percentage of the screen the window should occupy.
             If this value is negative then the window will not be resized,
             only repositioned (unless the current size is silly)
    @param aspect:  aspect ratio.  If greater than one then it is
             how much wider than tall the window is, and if less
             than one then the other way round
    """
    confobj=wx.GetApp().config

    # frig confname
    confname="windows/"+confname

    # Get screen size, scale according to percentage supplied
    screenSize = wx.GetClientDisplayRect()
    if (aspect >= 1):
        newWidth = screenSize.width * abs(screenpct) / 100
        newHeight = screenSize.height * abs(screenpct) / aspect / 100
    else:
        newWidth = screenSize.width * abs(screenpct) * aspect / 100
        newHeight = screenSize.height * abs(screenpct) / 100

    if screenpct<=0:
        rs_width,rs_height=window.GetSizeTuple()
    else:
        # Retrieve values (if any) from config database for this config object
        rs_width  = confobj.ReadInt(confname + "/width", int(newWidth))
        rs_height = confobj.ReadInt(confname + "/height", int(newHeight))

    # suitable magic number to show not configured.  it is an exercise for the reader
    # why it isn't -65536 (hint: virtual desktops)
    unconfigured=-65245

    rs_x = confobj.ReadInt(confname + "/x", unconfigured)
    rs_y = confobj.ReadInt(confname + "/y", unconfigured)

    # Check for small window
    if rs_height < 96:
        rs_height = newHeight
    if rs_width < 96:
        rs_width = newWidth

    # Make sure window is no larger than about screen size
    #
    # determine ratio of original oversized window so we keep the ratio if we resize...
    rs_aspect = rs_width/rs_height
    if rs_aspect >= 1:
        if rs_width > screenSize.width:
            rs_width = screenSize.width
        if rs_height > (screenSize.height):
            rs_height = (screenSize.height / rs_aspect) - screenSize.y 
    else:
        if rs_width > screenSize.width:
            rs_width = screenSize.width * rs_aspect
        if rs_height > screenSize.height - screenSize.y:
            rs_height = screenSize.height - screenSize.y

    # Off the screen?  Just pull it back a little bit so it's visible....
    if rs_x!=unconfigured and rs_x > screenSize.width:
        rs_x = screenSize.width - 50
    if rs_x!=unconfigured and rs_x + rs_width < screenSize.x:
        rs_x = screenSize.x
    if rs_y!=unconfigured and rs_y > screenSize.height:
        rs_y = screenSize.height - 50
    if rs_y!=unconfigured and rs_y + rs_height < screenSize.y:
        rs_y = screenSize.y
        

    if screenpct<=0 and (rs_width,rs_height)==window.GetSizeTuple():
        # set position only, and no need to resize
        if rs_x!=unconfigured and rs_y!=unconfigured:
            print "setting %s to position %d, %d" % (confname, rs_x, rs_y)
            window.SetPosition(wx.Point(rs_x, rs_y))
    else:
        if rs_x==unconfigured or rs_y==unconfigured:
            print "setting %s to size %d x %d" % (confname, rs_width, rs_height)
            window.SetSize(wx.Size(rs_width, rs_height))
        else:
            print "setting %s to position %d, %d - size %d x %d" % (confname, rs_x, rs_y, rs_width, rs_height)
            window.SetDimensions(rs_x, rs_y, rs_width, rs_height)

def save_size(confname, myRect):
    """Saves size to config.  L{set_size}

    @param confname: Same string as in set_size
    @param myRect:  Window size you want remembered, typically window.GetRect()
    """
    confobj=wx.GetApp().config
    
    confname="windows/"+confname

    x = myRect.x
    y = myRect.y
    width = myRect.width
    height = myRect.height

    confobj.WriteInt(confname + "/x", x)
    confobj.WriteInt(confname + "/y", y)
    confobj.WriteInt(confname + "/width", width)
    confobj.WriteInt(confname + "/height", height)
    confobj.Flush()

class LogProgressDialog(wx.ProgressDialog):
    """ display log string and progress bar at the same time
    """
    def __init__(self, title, message, maximum=100, parent=None,
                 style=wx.PD_AUTO_HIDE|wx.PD_APP_MODAL):
        super(LogProgressDialog, self).__init__(title, message, maximum,
                                                parent, style)
        self.__progress_value=0
    def Update(self, value, newmsg='', skip=None):
        self.__progress_value=value
        super(LogProgressDialog, self).Update(value, newmsg, skip)
    def log(self, msgstr):
        super(LogProgressDialog, self).Update(self.__progress_value, msgstr)

class AskPhoneNameDialog(wx.Dialog):
    def __init__(self, parent, message, caption="Enter phone owner's name", style=wx.DEFAULT_DIALOG_STYLE):
        """ Ask a user to enter an owner's name of a phone.
        Similar to the wx.TextEntryDialog but has 3 buttons, Ok, No Thanks, and
        Maybe latter.
        """
        super(AskPhoneNameDialog, self).__init__(parent, -1, caption, style=style)
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(wx.StaticText(self, -1, message), 0, wx.ALL, 5)
        self.__text_ctrl=wx.TextCtrl(self, -1, style=wx.TE_PROCESS_ENTER)
        vbs.Add(self.__text_ctrl,  0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        ok_btn=wx.Button(self, wx.ID_OK, 'OK')
        hbs.Add(ok_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        cancel_btn=wx.Button(self, wx.ID_CANCEL, 'No Thanks')
        hbs.Add(cancel_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        maybe_btn=wx.Button(self, wx.NewId(), 'Maybe next time')
        hbs.Add(maybe_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        vbs.Add(hbs, 1, wx.ALL, 5)
        wx.EVT_BUTTON(self, maybe_btn.GetId(), self.__OnMaybe)
        wx.EVT_TEXT_ENTER(self, self.__text_ctrl.GetId(), self.__OnTextEnter)
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)
    def GetValue(self):
        return self.__text_ctrl.GetValue()
    def __OnMaybe(self, evt):
        self.EndModal(evt.GetId())
    def __OnTextEnter(self, _):
        self.EndModal(wx.ID_OK)

class HistoricalDataDialog(wx.Dialog):
    Current_Data=0
    Historical_Data=1
    _Historical_Date=1
    _Historical_Event=2
    def __init__(self, parent, caption='Historical Data Selection',
                 current_choice=Current_Data,
                 historical_date=None,
                 historical_events=None):
        super(HistoricalDataDialog, self).__init__(parent, -1, caption)
        vbs=wx.BoxSizer(wx.VERTICAL)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        self.data_selector=wx.RadioBox(self, wx.NewId(),
                                       'Data Selection:',
                                       choices=('Current', 'Historical Date',
                                                'Historical Event'),
                                       style=wx.RA_SPECIFY_ROWS)
        self.data_selector.SetSelection(current_choice)
        wx.EVT_RADIOBOX(self, self.data_selector.GetId(), self.OnSelectData)
        hbs.Add(self.data_selector, 0, wx.ALL, 5)
        static_bs=wx.StaticBoxSizer(wx.StaticBox(self, -1,
                                                 'Historical Date:'),
                                    wx.VERTICAL)
        self.data_date=wx.DatePickerCtrl(self,
                                         style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)
        if historical_date is not None:
            self.data_date.SetValue(wx.DateTimeFromTimeT(historical_date))
        self.data_date.Enable(current_choice==self._Historical_Date)
        static_bs.Add(self.data_date, 1, wx.EXPAND, 0)
        hbs.Add(static_bs, 0, wx.ALL, 5)
        # historical events
        static_bs=wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Historical Events:'),
                                    wx.VERTICAL)
        self.hist_events=wx.ListBox(self, -1, style=wx.LB_SINGLE)
        if historical_events:
            self._populate_historical_events(historical_events)
        self.hist_events.Enable(current_choice==self._Historical_Event)
        static_bs.Add(self.hist_events, 1, wx.EXPAND, 0)
        hbs.Add(static_bs, 0, wx.ALL, 5)

        vbs.Add(hbs, 1, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL), 0,
                wx.ALIGN_CENTER|wx.ALL, 5)
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

    def OnSelectData(self, evt):
        self.data_date.Enable(evt.GetInt()==self._Historical_Date)
        self.hist_events.Enable(evt.GetInt()==self._Historical_Event)
        
    def GetValue(self):
        choice=self.data_selector.GetSelection()
        if choice==self.Current_Data:
            mode=self.Current_Data
            time_t=None
        elif choice==self._Historical_Date:
            dt=self.data_date.GetValue()
            dt.SetHour(23)
            dt.SetMinute(59)
            dt.SetSecond(59)
            mode=self.Historical_Data
            time_t=dt.GetTicks()
        else:
            sel=self.hist_events.GetSelection()
            if sel==wx.NOT_FOUND:
                mode=self.Current_Data
                time_t=None
            else:
                mode=self.Historical_Data
                time_t=self.hist_events.GetClientData(sel)
        return mode, time_t

    def _populate_historical_events(self, historical_events):
        keys=historical_events.keys()
        keys.sort()
        keys.reverse()
        for k in keys:
            # build the string
            self.hist_events.Append('%s  %02d-Adds  %02d-Dels  %02d-Mods'%\
                                    (time.strftime('%b %d, %y %H:%M:%S',
                                                   time.localtime(k)),
                                     historical_events[k]['add'],
                                     historical_events[k]['del'],
                                     historical_events[k]['mod']),
                                    k)


class BitPimListCtrl(wx.ListCtrl, listmix.ColumnSorterMixin):
    def __init__(self, parent, column_info):
        self.lcparent=parent
        wx.ListCtrl.__init__(self, self.lcparent, wx.NewId(), style=wx.LC_REPORT|wx.LC_VIRTUAL)
        index=0
        self.column_type=[]
        for info in column_info:
            text, width, int_sort=info
            self.InsertColumn(index, text, width=width)
            self.column_type.append(int_sort)
            index+=1
        self.handle_paint=False
        listmix.ColumnSorterMixin.__init__(self, index)
        self.font=wx.TheFontList.FindOrCreateFont(10, family=wx.SWISS, style=wx.NORMAL, weight=wx.NORMAL)
        self.image_list=wx.ImageList(16, 16)
        a={"sm_up":"GO_UP","sm_dn":"GO_DOWN","w_idx":"WARNING","e_idx":"ERROR","i_idx":"QUESTION"}
        for k,v in a.items():
            s="self.%s= self.image_list.Add(wx.ArtProvider_GetBitmap(wx.ART_%s,wx.ART_TOOLBAR,(16,16)))" % (k,v)
            exec(s)
        self.SetImageList(self.image_list, wx.IMAGE_LIST_SMALL)

    def SortItems(self,sorter=None):
        col=self._col
        sf=self._colSortFlag[col]

        #creating pairs [column item defined by col, key]
        items=[]
        for k,v in self.itemDataMap.items():
            if self.column_type[col]:
                items.append([int(v[col]),k])
            else:
                items.append([v[col],k])

        items.sort()
        k=[key for value, key in items]

        # False is descending
        if sf==False:
            k.reverse()

        self.itemIndexMap=k

        #redrawing the list
        self.Refresh()

    def GetListCtrl(self):
        return self

    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    def OnGetItemText(self, item, col):
        index=self.itemIndexMap[item]
        s = self.itemDataMap[index][col]
        return s

    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        return None

    def GetItemData(self, item):
        index=self.itemIndexMap[item]
        return self.itemPyDataMap[index]

    def SelectAll(self):
        item=self.GetTopItem()
        while item!=-1:
            self.Select(item)
            item=self.GetNextItem(item)

    def ResetView(self, display_data, data_keys):
        self.itemDataMap = display_data
        self.itemIndexMap = display_data.keys()
        self.itemPyDataMap = data_keys
        count=len(self.lcparent.nodes)
        self.SetItemCount(count)
        self.SortListItems()
        if count==0 and not self.handle_paint:
            wx.EVT_PAINT(self, self.OnPaint)
            self.handle_paint=True
        elif count!=0 and self.handle_paint:
            self.Unbind(wx.EVT_PAINT)
            self.handle_paint=False

    def OnPaint(self, evt):
        w,h=self.GetSize()
        self.Refresh()
        dc=wx.PaintDC(self)
        dc.BeginDrawing()
        dc.SetFont(self.font)
        x,y= dc.GetTextExtent("There are no items to show in this view")
        # center the text
        xx=(w-x)/2
        if xx<0:
            xx=0
        dc.DrawText("There are no items to show in this view", xx, h/3)
        dc.EndDrawing()

    def GetSelections(self):
        sels_idx={}
        index=0
        sels_idx[index]=self.GetFirstSelected()
        # build up a list of all selected items
        while sels_idx[index]!=-1:
            index+=1
            sels_idx[index]=self.GetNextSelected(sels_idx[index-1])
        del sels_idx[index]
        return sels_idx

class DRRecFileDialog(wx.Dialog):
    """
    A dialog to ask for and provide the file name for a Data Recording file
    """
    def __init__(self, parent):
        super(DRRecFileDialog, self).__init__(parent, -1,
                                           'BitPim Data Recording')
        vbs=wx.BoxSizer(wx.VERTICAL)
        fgs=wx.GridBagSizer(5, 5)
        fgs.Add(wx.StaticText(self, -1, 'File Name:'), pos=(0,0),
                flag=wx.EXPAND|wx.ALL)
        self._file_name=wx.TextCtrl(self, -1, 'bitpim.dat')
        fgs.Add(self._file_name, pos=(0, 1), flag=wx.EXPAND|wx.ALL)
        _brw_btn=wx.Button(self, -1, 'Browse')
        fgs.Add(_brw_btn, pos=(0, 2), flag=wx.EXPAND|wx.ALL)
        wx.EVT_BUTTON(self, _brw_btn.GetId(), self.OnBrowse)
        fgs.Add(wx.StaticText(self, -1, 'Open Mode:'), pos=(1,0),
                flag=wx.EXPAND|wx.ALL)
        self._append=wx.CheckBox(self, -1, 'Append to existing file')
        fgs.Add(self._append, pos=(1, 1), flag=wx.EXPAND|wx.ALL)
        if __debug__:
            _setstart_btn=wx.Button(self, -1, 'Set Start')
            wx.EVT_BUTTON(self, _setstart_btn.GetId(), self.OnSetStart)
            fgs.Add(_setstart_btn, pos=(1, 2), flag=wx.EXPAND|wx.ALL)
        fgs.Add(wx.StaticText(self, -1, 'Status:'), pos=(2,0),
                              flag=wx.EXPAND|wx.ALL)
        self._status=wx.StaticText(self, -1, 'None')
        fgs.Add(self._status, pos=(2,1), flag=wx.EXPAND|wx.ALL)
        vbs.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        if __debug__:
            _btn=wx.Button(self, -1, 'View')
            wx.EVT_BUTTON(self,_btn.GetId(), self.OnView)
            hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        _btn=wx.Button(self, -1, 'Record')
        wx.EVT_BUTTON(self, _btn.GetId(), self.OnRecord)
        hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        if __debug__:
            _btn=wx.Button(self, -1, 'Play')
            wx.EVT_BUTTON(self, _btn.GetId(), self.OnPlay)
            hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        _btn=wx.Button(self, -1, 'Stop')
        wx.EVT_BUTTON(self, _btn.GetId(), self.OnStop)
        hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        _btn=wx.Button(self, wx.ID_CANCEL, 'Close')
        hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)

        self._update_status()

        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

    def _update_status(self):
        _stat='None'
        _fname=None
        if data_recording.DR_On:
            _stat='Recording ...'
            _fname=data_recording.filename()
        elif data_recording.DR_Play:
            _stat='Playing back ...'
            _fname=data_recording.filename()
        else:
            _stat='None'
        self._status.SetLabel(_stat)
        if _fname:
            self._file_name.SetValue(_fname)

    def OnBrowse(self, _):
        _dlg=wx.FileDialog(self)
        _dlg.SetPath(self._file_name.GetValue())
        with guihelper.WXDialogWrapper(_dlg, True) as (_dlg, retcode):
            if retcode==wx.ID_OK:
                self._file_name.SetValue(_dlg.GetPath())

    def OnView(self, _):
        _dr_file=data_recording.DR_Read_File(self._file_name.GetValue())
        analyser.Analyser(data=_dr_file.get_string_data()).Show()

    def OnRecord(self, _):
        data_recording.record_to_file(self._file_name.GetValue())
        self._update_status()

    def OnPlay(self, _=None):
        data_recording.playback_from_file(self._file_name.GetValue())
        self._update_status()

    def OnStop(self, _):
        data_recording.stop()
        self._update_status()

    def OnSetStart(self, _):
        if not data_recording.DR_Play:
            # not playing back, start playing
            self.OnPlay()
        with guihelper.WXDialogWrapper(wx.SingleChoiceDialog(self, 'Select the Starting Point',
                                                             'Data Recording Set Start',
                                                             choices=data_recording.get_headers()),
                                       True) as (_dlg, retcode):
            if retcode==wx.ID_OK:
                data_recording.set_start(_dlg.GetSelection())

# About Dialog-----------------------------------------------------------------
_license="""The BitPim code is under the GNU General Public License as detailed
below.  Specific permission is granted for this code to be linked to
OpenSSL (this is necessary because the OpenSSL license is not
GPL-compatible).

   In addition, as a special exception, the BitPim copyright holders
   give permission to link the code of this program with the OpenSSL
   library (or with modified versions of OpenSSL), and distribute
   linked combinations including the two. You must obey the GNU
   General Public License in all respects for all of the code used
   other than OpenSSL. If you modify any files, you may extend this
   exception to your version of the file, but you are not obligated to
   do so. If you do not wish to do so, delete this exception statement
   from your version.

Please also note that some code is taken from other projects with a
GPL compatible license.  This is noted in the specific files.

BitPim also uses several other components with GPL compatible
licenses.  The online help details those components, credits the
authors and details the licenses.
---------------------------------------------------------------------
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as published by
the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.  Also see the BitPim Help for more details
"""

_copyright="""(C) 2003-2007 The code in BitPim is copyright by several people.  Please note the
comments at the top of each file, as well as version control history.
"""
_description="""    BitPim is a program that allows you to view and manipulate data on many CDMA phones
    from LG, Samsung, Sanyo and other manufacturers. This includes the PhoneBook,
    Calendar, WallPapers, RingTones (functionality varies by phone) and the
    Filesystem for most Qualcomm CDMA chipset based phones. To see when phones will
    be supported, which ones are already supported and which features are supported,
    see online help.
    
[%s]
"""
def _component_string():
    """return a CSV string of various software components being used by BitPim"""
    _res=[]
    _str=[]
    # Python version
    _str.append('Python %s'%sys.version.split()[0])
    _str.append('wxPython %s'%wx.version())
    _res.append(', '.join(_str))
    _str=[]
    _str.append('APSW %s'%apsw.apswversion())
    _str.append('SQLITE %s'%apsw.sqlitelibversion())
    _res.append(', '.join(_str))
    _str=[]
    _str.append('serial %s'%serial.VERSION)
    # pywin32 version
    try:
        _pywin32ver=file(os.path.join(sys.prefix,'lib','site-packages', 'pywin32.version.txt'),
                         'rt').read()[:-1]        
        _str.append('pywin32 %s'%_pywin32ver)
    except:
        pass
    _res.append(', '.join(_str))
    return '\n'.join(_res)

def show_about_dlg(parent):
    global _license, _copyright, _description
    info = wx.AboutDialogInfo()
    info.Name = "BitPim"
    info.Version = version.versionstring+" - "+version.vendor
    info.Copyright=_copyright
    info.Description = _description%_component_string()
    info.WebSite = ("http://www.bitpim.org", "www.bitpim.org")
    info.Developers = [ "Joe Pham",
                        "Stephen Wood",
                        "Sean Burke",
                        "Nathan Hjelm",
                        "and others ..."]

    info.License = _license
    # Then we call wx.AboutBox giving it that info object
    wx.AboutBox(info)

# Generic Print Dialog----------------------------------------------------------
class PrintDialog(wx.Dialog):
    """A generic print dialog from which other can subclass for their own use"""
    _template_filename=None
    _style_filename=None

    def __init__(self, widget, mainwindow, config, title):
        super(PrintDialog, self).__init__(mainwindow, -1, title)
        self._widget=widget
        self._xcp=self._html=self._dns=None
        self._tmp_file=common.gettempfilename("htm")
        # main box sizer
        vbs=wx.BoxSizer(wx.VERTICAL)
        # create the main contents of the dialog
        self._create_contents(vbs)
        # create the separator & default buttons
        self._create_buttons(vbs)
        # all done
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

    def _create_contents(self, vbs):
        # subclass must implement
        raise NotImplementedError

    def _create_buttons(self, vbs):
        vbs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        for b in ((None, wx.ID_PRINT, self.OnPrint),
                  ('Page Setup', wx.ID_PAGE_SETUP, self.OnPageSetup),
                  (None, wx.ID_PREVIEW, self.OnPrintPreview),
                  ('Save as HTML', -1, self.OnSaveHTML),
                  (None, wx.ID_CLOSE, self.OnClose)):
            if b[0]:
                btn=wx.Button(self, b[1], b[0])
            else:
                btn=wx.Button(self, b[1])
            hbs.Add(btn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
            if b[2] is not None:
                wx.EVT_BUTTON(self, btn.GetId(), b[2])
        vbs.Add(hbs, 0, wx.ALIGN_CENTRE|wx.EXPAND|wx.ALL, 5)

    def _init_print_data(self):
        # Initialize the dns dict with empty data
        self._dns={ 'common': __import__('common') }
        self._dns['guihelper']=__import__('guihelper')
        self._dns['pagebreakstr']='<div style="page-break-before:always"/>'

    def _get_print_data(self):
        raise NotImplementedError

    def _gen_print_data(self):
        # generate the html page of the print data
        if self._xcp is None:
            # build the whole document template
            self._xcp=xyaptu.xcopier(None)
            tmpl=file(guihelper.getresourcefile(self._template_filename),
                      'rt').read()
            self._xcp.setupxcopy(tmpl)
        if self._dns is None:
            self._init_print_data()
        self._get_print_data()
        self._html=self._xcp.xcopywithdns(self._dns.copy())
        # apply styles
        sd={'styles': {}, '__builtins__': __builtins__ }
        try:
            if self._style_filename:
                execfile(guihelper.getresourcefile(self._style_filename),
                         sd, sd)
        except UnicodeError:
            common.unicode_execfile(guihelper.getresourcefile(self._style_filename),
                                    sd, sd)
        try:
            self._html=bphtml.applyhtmlstyles(self._html, sd['styles'])
        except:
            if __debug__:
                file('debug.html', 'wt').write(self._html)
            raise

    # standard handlers
    def OnPrint(self, _):
        self._gen_print_data()
        wx.GetApp().htmlprinter.PrintText(self._html)
    def OnPageSetup(self, _):
        wx.GetApp().htmlprinter.PageSetup()
    def OnPrintPreview(self, _):
        self._gen_print_data()
        wx.GetApp().htmlprinter.PreviewText(self._html)
    def OnSaveHTML(self, _):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, wildcard="Web Page (*.htm;*.html)|*.htm;*html",
                                                     style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT),
                                       True) as (_dlg, retcode):
            if retcode==wx.ID_OK:
                self._gen_print_data()
                file(_dlg.GetPath(), 'wt').write(self._html)
    def OnClose(self, _):
        try:
            # remove the temp file, ignore exception if file does not exist
            os.remove(self._tmp_file)
        except:
            pass
        self.EndModal(wx.ID_CANCEL)

# SMS Print Dialog--------------------------------------------------------------
class SMSPrintDialog(PrintDialog):

    _template_filename='sms.xy'
    _title='SMS Print'
    _item_name='SMS Messages'

    def __init__(self, smswidget, mainwindow, config):
        self._sel_data=smswidget.get_selected_data()
        self._data=smswidget.get_data()
        super(SMSPrintDialog, self).__init__(smswidget, mainwindow,
                                             config, self._title)

    def _create_contents(self, vbs):
        rbs=wx.StaticBoxSizer(wx.StaticBox(self, -1, self._item_name), wx.VERTICAL)
        lsel=len(self._sel_data)
        lall=len(self._data)
        self.rows_selected=wx.RadioButton(self, wx.NewId(), "Selected (%d)" % (lsel,), style=wx.RB_GROUP)
        self.rows_all=wx.RadioButton(self, wx.NewId(), "All (%d)" % (lall,))
        if lsel==0:
            self.rows_selected.Enable(False)
            self.rows_selected.SetValue(0)
            self.rows_all.SetValue(1)
        rbs.Add(self.rows_selected, 0, wx.EXPAND|wx.ALL, 2)
        rbs.Add(self.rows_all, 0, wx.EXPAND|wx.ALL, 2)
        vbs.Add(rbs, 0, wx.EXPAND|wx.ALL, 5)

    def _init_print_data(self):
        # Initialize the dns dict with empty data
        super(SMSPrintDialog, self)._init_print_data()
        self._dns['items']={}
        self._dns['keys']=[]

    def _get_print_data(self):
        if self.rows_all.GetValue():
            _items=self._data
            _keys=self._widget.get_keys()
        else:
            _items=self._sel_data
            _keys=self._widget.get_selected_keys()
        if not _keys:
            _keys=_items.keys()
        self._dns['items']=_items
        self._dns['keys']=_keys

# Memo Print Dialog-------------------------------------------------------------
class MemoPrintDialog(SMSPrintDialog):
    _template_filename='memo.xy'
    _title='Memo Print'
    _item_name='Memo Entries'
