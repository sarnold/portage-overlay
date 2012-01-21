#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2007 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: newdb_wiz.py 4378 2007-08-27 17:47:50Z djpham $

"""
Wizard to create a new BitPim storage area.
"""

# system module
from __future__ import with_statement
import os
import os.path

# wx modules
import wx
import wx.wizard as wiz
from wx.lib.expando import ExpandoTextCtrl

# BitPim modules
import bp_config
import guihelper
import setphone_wizard

if guihelper.IsMSWindows():
    from win32com import client

parentpage=setphone_wizard.MyPage
#-------------------------------------------------------------------------------
class NamePage(parentpage):
    def __init__(self, parent):
        super(NamePage, self).__init__(parent,
                                       'Select BitPim Storage Name')
    def GetMyControls(self):
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(wx.StaticText(self, -1, 'Storage Name:'), 0,
                wx.EXPAND|wx.ALL, 5)
        self.name=wx.TextCtrl(self, -1, '')
        vbs.Add(self.name, 0, wx.EXPAND|wx.ALL, 5)
        return vbs

    def ok(self):
        return bool(self.name.GetValue())
    def get(self, data):
        data['name']=self.name.GetValue()
    def set(self, data):
        self.name.SetValue(data.get('name', ''))

#-------------------------------------------------------------------------------
class PathPage(parentpage):
    def __init__(self, parent):
        super(PathPage, self).__init__(parent,
                                       'Select New Storage Dir')
        if guihelper.IsMSWindows():
            shell=client.Dispatch("WScript.Shell")
            self.defaultdir=os.path.join(shell.SpecialFolders("MyDocuments"),
                                         'Phones')
        else:
            self.defaultdir=os.path.expanduser('~/Phones')

    def GetMyControls(self):
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(wx.StaticText(self, -1, 'Storage Dir:'),
                0, wx.EXPAND|wx.ALL, 5)
        self.path=ExpandoTextCtrl(self, -1, '', style=wx.TE_READONLY)
        self.path.SetBackgroundColour(self.GetBackgroundColour())
        vbs.Add(self.path, 0, wx.EXPAND|wx.ALL, 5)
        btn=wx.Button(self, -1, 'Browse')
        wx.EVT_BUTTON(self, btn.GetId(), self.OnBrowse)
        vbs.Add(btn, 0, wx.ALL, 5)
        return vbs

    def ok(self):
        return bool(self.path.GetValue())
    def get(self, data):
        data['path']=self.path.GetValue()
    def set(self, data):
        path=data.get('path', '')
        if not path:
            path=os.path.join(self.defaultdir, data.get('name', ''))
        self.path.SetValue(path)

    def OnBrowse(self, _):
        with guihelper.WXDialogWrapper(wx.DirDialog(self, defaultPath=self.path.GetLabel(),
                                                    style=wx.DD_NEW_DIR_BUTTON),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.path.SetValue(dlg.GetPath())

#-------------------------------------------------------------------------------
class OptionsPage(parentpage):
    def __init__(self, parent):
        super(OptionsPage, self).__init__(parent,
                                          'Select Options')
    def GetMyControls(self):
        vbs=wx.BoxSizer(wx.VERTICAL)
        self.setting=wx.RadioBox(self, -1, 'Initial Config Settings:',
                                 choices=['Use Default Settings',
                                          'Use Current Settings'],
                                 style=wx.RA_SPECIFY_ROWS)
        vbs.Add(self.setting, 0, wx.EXPAND|wx.ALL, 5)
        if guihelper.IsMSWindows():
            sbs=wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Shortcut Options:'),
                                  wx.VERTICAL)
            self.desktop=wx.CheckBox(self, -1, 'Create a shortcut on your Desktop')
            sbs.Add(self.desktop, 0, wx.EXPAND|wx.ALL, 5)
            self.startmenu=wx.CheckBox(self, -1,
                                       'Create a shortcut in your Start Menu')
            sbs.Add(self.startmenu, 0, wx.EXPAND|wx.ALL, 5)
            vbs.Add(sbs, 0, wx.EXPAND|wx.ALL, 5)
        return vbs

    def get(self, data):
        data['currentsettings']=self.setting.GetSelection()==1
        if guihelper.IsMSWindows():
            data['desktop']=self.desktop.GetValue()
            data['startmenu']=self.startmenu.GetValue()
    def set(self, data):
        if data.get('currentsettings', False):
            self.setting.SetSelection(1)
        else:
            self.setting.SetSelection(0)
        if guihelper.IsMSWindows():
            self.desktop.SetValue(data.get('desktop', False))
            self.startmenu.SetValue(data.get('startmenu', False))

#-------------------------------------------------------------------------------
class SummaryPage(parentpage):
    def __init__(self, parent):
        super(SummaryPage, self).__init__(parent, 'Selection Summary')
    def GetMyControls(self):
        vbs=wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Selection Summary:'),
                              wx.VERTICAL)
        self.summary=ExpandoTextCtrl(self, -1, '')
        self.summary.SetBackgroundColour(self.GetBackgroundColour())
        vbs.Add(self.summary, 0, wx.EXPAND|wx.ALL, 5)
        self._box=vbs
        return vbs
    def set(self, data):
        text=['Name:\t%s'%data.get('name', '')]
        text.append('Dir:\t%s'%data.get('path', ''))
        if data.get('currentsettings', False):
            text.append('Use current BitPim settings.')
        else:
            text.append('Use default BitPim settings.')
        if guihelper.IsMSWindows():
            if data.get('desktop', False):
                text.append('Create a shortcut on your Desktop.')
            if data.get('startmenu', False):
                text.append('Create a shortcut in your Start Menu.')
        self.summary.SetValue('\n\n'.join(text))

#-------------------------------------------------------------------------------
class NewDBWizard(wiz.Wizard):
    def __init__(self, parent):
        super(NewDBWizard, self).__init__(parent, -1,
                                          'New BitPim Storage Wizard')
        self.data={}
        namepage=NamePage(self)
        pathpage=PathPage(self)
        optionspage=OptionsPage(self)
        summarypage=SummaryPage(self)
        wiz.WizardPageSimple_Chain(namepage, pathpage)
        wiz.WizardPageSimple_Chain(pathpage, optionspage)
        wiz.WizardPageSimple_Chain(optionspage, summarypage)
        self.firstpage=namepage
        self.GetPageAreaSizer().Add(namepage, 1, wx.EXPAND|wx.ALL, 5)
        wiz.EVT_WIZARD_PAGE_CHANGING(self, self.GetId(), self.OnPageChanging)
        wiz.EVT_WIZARD_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)

    def RunWizard(self, firstPage=None):
        return super(NewDBWizard, self).RunWizard(firstPage or self.firstpage)

    def OnPageChanging(self, evt):
        pg=evt.GetPage()
        if not evt.GetDirection() or pg.ok():
            pg.get(self.data)
        else:
            evt.Veto()

    def OnPageChanged(self, evt):
        evt.GetPage().set(self.data)

    def get(self):
        return self.data

#-------------------------------------------------------------------------------
def create_desktop_shortcut(name, filename):
    shell=client.Dispatch("WScript.Shell")
    desktopphones=os.path.join(shell.SpecialFolders("Desktop"), 'Phones')
    if not os.path.isdir(desktopphones):
        os.makedirs(desktopphones)
    target=os.path.join(desktopphones, name+'.lnk')
    try:
        os.remove(target)
    except:
        pass
    link=shell.CreateShortcut(target)
    link.TargetPath=filename
    link.Save()

#-------------------------------------------------------------------------------
def create_startmenu_shortcut(name, filename):
    shell=client.Dispatch("WScript.Shell")
    startmenu=os.path.join(shell.SpecialFolders("StartMenu"), 'Programs')
    startmenuphones=os.path.join(startmenu, 'Phones')
    if not os.path.isdir(startmenuphones):
        os.makedirs(startmenuphones)
    target=os.path.join(startmenuphones, name+'.lnk')
    try:
        os.remove(target)
    except:
        pass
    link=shell.CreateShortcut(target)
    link.TargetPath=filename
    link.Save()

#-------------------------------------------------------------------------------
def create_new_db(parent, config=None):
    # Create a new BitPim Storage area
    with guihelper.WXDialogWrapper(NewDBWizard(parent)) as wz:
        if wz.RunWizard():
            data=wz.get()
            name=data.get('name', '')
            # Dir should aleady exist, but check anyway
            path=data.get('path', '')
            if not os.path.isdir(path):
                os.makedirs(path)
            # create a config file
            filename=os.path.join(path, '.bitpim')
            if data.get('currentsettings', False) and config:
                config.write(file(filename, 'wt'))
            conf=bp_config.Config(filename)
            conf.Write('name', name)
            # and optionally create shortcuts (Windows only)
            if guihelper.IsMSWindows():
                if data.get('desktop', False):
                    create_desktop_shortcut(name, filename)
                if data.get('startmenu', False):
                    create_startmenu_shortcut(name, filename)

#-------------------------------------------------------------------------------
# Testing
if __name__=="__main__":
    app=wx.PySimpleApp()
    f=wx.Frame(None, title='newdb_wizard')
    create_new_db(f)
