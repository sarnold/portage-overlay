### BITPIM
###
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2006 Simon Capper <skyjunky@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: phone_root.py 4390 2007-09-05 00:08:19Z djpham $

"""The main gui code for BitPim"""

# System modules
import ConfigParser
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

# my modules
import guiwidgets
import common
import version
import helpids
import bpcalendar
import comdiagnose
import phonebook
import importexport
import wallpaper
import ringers
import guihelper
import database
import memo
import todo
import sms_tab
import call_history
import today
import pubsub
import playlist
import filesystem
import widgets
import media_root
import t9editor
import vtab_media

if guihelper.IsMSWindows():
    import win32api
    import win32con
    import win32gui

class PhoneTree(wx.TreeCtrl):
    def __init__(self, parent, mw, id):
        wx.TreeCtrl.__init__(self, parent, id, style=wx.TR_HAS_BUTTONS)
        self.parent=parent
        self.mw=mw
        self.config=mw.config
        bmsize=(22,22)
        wx.EVT_TREE_SEL_CHANGED(self,id, self.OnItemSelected)
        self.image_list=wx.ImageList(22, 22)
        self.img_dir=self.image_list.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,
                                                             wx.ART_OTHER,
                                                             bmsize))
        art=["phonebook", "wallpaper", "ringers", "calendar", "callhistory", "calls", "sms", "message", "memo",
           "file", "log", "todo", "playlist", "protocol", "console", "phone_root", "phone", "root_image", "media",
           "image", "video", "camera", "sounds"]
        for k in art:
            s="self.%s= self.image_list.Add(wx.ArtProvider_GetBitmap(guihelper.ART_SEL_%s,wx.ART_TOOLBAR,bmsize))" % (k,k.upper())
            exec(s)
        self.SetImageList(self.image_list)
        if self.config.ReadInt('startwithtoday', 0):
            self.startuppage='Phone'
        else:
            self.startuppage=self.config.Read("viewnotebookpage", "")
        self.startuppage_item=None
        self.DeleteAllItems()
        self.active_phone=None
        self.active_panel=self.root_panel=widgets.RootWidget(self.parent, wx.NewId())
        self.root=self.AddPage(None, self.root_panel, "BitPim", self.root_image)
        self.del_bmp, self.short_help_delete=self.root_panel.GetDeleteInfo()
        self.add_bmp, self.short_help_add=self.root_panel.GetAddInfo()
        self.lw=None
        self.lwdata=None
        self.filesystemwidget=None

        wx.EVT_RIGHT_UP(self, self.OnRightUp)
        wx.EVT_KEY_DOWN(self, self.OnKeyDown)
        wx.EVT_KEY_UP(self, self.OnKeyUp)

        # add shared tabs
        self.lw=guiwidgets.LogWindow(self.parent)
        self.lw_id=self.AddPage(self.root, self.lw, "Log", self.log)

        # Final widgets that depend on config
        lv=self.config.ReadInt("viewlogdata", 0)
        if lv:
            self.OnViewLogData(None)

        fv=self.config.ReadInt("viewfilesystem", 0)
        if fv:
            self.OnViewFilesystem(None)
            wx.Yield()

    def OnKeyUp(self, evt):
        self.active_panel.OnKeyUp(evt)
        # pass onto widget

    def OnKeyDown(self, evt):
        self.active_panel.OnKeyDown(evt)
        # pass onto widget

    def CreatePhone(self, name, config, path, database_name):
        phone=Phone(self.parent)
        phone_id=self.AddPage(self.root, phone, name, self.phone, None, helpids.ID_TAB_TODAY)
        phone.Initialise(self, self.mw, config, path, phone_id, database_name)
        if self.active_phone==None:
            self.Expand(phone_id)
            self.active_phone=phone

    def GetActivePhone(self):
        return self.active_phone

    def GetActiveWidget(self):
        return self.active_panel

    def AddPage(self, phone, panel, name, image=None, after=None, help_id=None):
        if image==None:
            image=self.img_dir
        if phone==None:
            item=self.AddRoot(name)
        elif after==None:
            item=self.PrependItem(phone, name)
        else:
            item=self.InsertItem(phone, after, name)
        self.SetPyData(item, panel)
        self.SetItemImage(item, image)
        panel.Show(False)
        panel.InitialiseWidget(self, item, phone, self.config, help_id)
        if not self.startuppage_item and name==self.startuppage:
            self.startuppage_item=item
        return item

    def SetStartupPage(self):
        if self.startuppage_item:
            self.SelectItem(self.startuppage_item)

    def AddNode(self, panel, name, image=None):
        if image==None:
            image=self.img_dir
        item=self.AppendItem(panel.id, name)
        self.SetPyData(item, panel)
        self.SetItemImage(item, image)
        return item

    def DeletePage(self, id):
        self.Delete(id)

    def OnItemSelected(self, _):
        item=self.GetSelection()
        if item.IsOk(): 
            if self.GetItemPyData(item):
                self.active_panel=self.GetItemPyData(item)
                self.active_panel.OnSelected(item)
                text=self.active_panel.GetWidgetName()
                if text is not None:
                    self.config.Write("viewnotebookpage", text)
        wx.CallAfter(self.mw.SetActivePanel, self.active_panel)
        # deal with graying out/in menu items on notebook page changing
        del_bmp, short_help_delete=self.active_panel.GetDeleteInfo()
        add_bmp, short_help_add=self.active_panel.GetAddInfo()
        if del_bmp!=self.del_bmp or add_bmp!=self.add_bmp or self.short_help_delete!=short_help_delete:
            self.mw.UpdateToolbarOnPanelChange(add_bmp, short_help_add, del_bmp, short_help_delete)
            self.add_bmp=add_bmp
            self.del_bmp=del_bmp
            self.short_help_delete=short_help_delete
            self.short_help_add=short_help_add

    def OnRightUp(self, event):
        pt = event.GetPosition();
        item, flags = self.HitTest(pt)
        if item.IsOk():
            self.active_panel=self.GetItemPyData(item)
            self.active_panel.OnPopupMenu(self, item, pt)
                    
    # update handlers for controls that are not always available
    def ViewLogDataUIEvent(self, event):
        event.Check(self.lwdata != None)

    def ViewFileSystemUIEvent(self, event):
        event.Check(self.filesystemwidget != None)

    def DataSendPhoneUpdateUIEvent(self, event):
        event.Enable(not wx.GetApp().SAFEMODE)

    def EditCopyUpdateUIEvent(self, event):
        event.Enable(self.active_panel.CanCopy())

    def EditPasteUpdateUIEvent(self, event):
        event.Enable(self.active_panel.CanPaste())

    def EditRenameUpdateUIEvent(self, event):
        event.Enable(self.active_panel.CanRename())

    def DataDeleteItemUpdateUIEvent(self, event):
        event.Enable(self.active_panel.CanDelete())

    def DataAddItemUpdateUIEvent(self, event):
        event.Enable(self.active_panel.CanAdd())

    def HistoricalDataUpdateUIEvent(self, event):
        event.Enable(self.active_panel.HasHistoricalData())

    def ViewPreviewDataUpdateUIEvent(self, event):
        event.Enable(self.active_panel.HasPreviewPane())
        event.Check(self.active_panel.IsPreviewPaneEnabled())

    def ViewColumnsUpdateUIEvent(self, event):
        event.Enable(self.active_panel.HasColumnSelector())

    def FilePrintDataUpdateUIEvent(self, event):
        event.Enable(self.active_panel.CanPrint())

    def SelectAllDataUpdateUIEvent(self, event):
        event.Enable(self.active_panel.CanSelectAll())

    def OnFilePrint(self,_):
        self.active_panel.OnPrintDialog(self, self.config)

    def OnDataHistorical(self, _):
        self.active_panel.OnHistoricalData()

    def OnEditAddEntry(self, evt):
        self.active_panel.OnAdd(evt)

    def OnEditDeleteEntry(self, evt):
        self.active_panel.OnDelete(evt)

    def OnEditSelectAll(self, evt):
        self.active_panel.OnSelectAll(evt)

    def OnCopyEntry(self, evt):
        self.active_panel.OnCopy(evt)

    def OnPasteEntry(self, evt):
        self.active_panel.OnPaste(evt)

    def OnRenameEntry(self, evt):
        self.active_panel.OnRename(evt)

    def OnViewClearLogs(self, _):
        self.lw.Clear()
        if self.lwdata is not None:
            self.lwdata.Clear()

    def OnViewColumns(self, _):
        self.active_panel.OnViewColumnSelector()

    def OnViewPreview(self, evt):
        if not self.active_panel.IsPreviewPaneEnabled():
            config=1
            preview_on=True
        else:
            config=0
            preview_on=False
        self.active_panel.OnViewPreview(preview_on)

    def OnViewLogData(self, _):
        # toggle state of the log data
        logdatatitle="Protocol Log"
        if self.lwdata is None:
            self.lwdata=guiwidgets.LogWindow(self.parent)
            self.lwdata_id=self.AddPage(self.root, self.lwdata, logdatatitle, self.log, self.lw_id)
            self.config.WriteInt("viewlogdata", 1)
        else:
            self.lwdata=None
            self.DeletePage(self.lwdata_id)
            self.lwdata_id=0
            self.config.WriteInt("viewlogdata", 0)

    def OnViewFilesystem(self,_):
        # toggle filesystem view
        logtitle="Log"
        fstitle="Filesystem"
        if self.filesystemwidget is None:
            self.filesystemwidget=filesystem.FileSystemView(self.mw, self.parent, id=97)
            pos=self.GetPrevSibling(self.lw_id)
            self.filesystemwidget_id=self.AddPage(self.root, self.filesystemwidget, fstitle, self.file, pos)
            self.config.WriteInt("viewfilesystem", 1)
        else:
            self.filesystemwidget=None
            self.DeletePage(self.filesystemwidget_id)
            self.config.WriteInt("viewfilesystem", 0)

    def OnBusyStart(self):
        return self.mw.OnBusyStart()
        
    def OnBusyEnd(self):
        return self.mw.OnBusyEnd()

class Phone(today.TodayWidget):
    def __init__(self, parent):
        self.parent=parent
        today.TodayWidget.__init__(self, self, self.parent)
        pubsub.subscribe(self.OnPhoneChanged, pubsub.PHONE_MODEL_CHANGED)

    def Initialise(self, tree, mw, config, path, phone_id, database_name):
        self.tree=tree
        self.mw=mw
        self.phone_id=phone_id
        self.config=config
        self.path=path
        self.phoneprofile=self.mw.phoneprofile
        id=None

        blob_path=database_name+"_blobs"
        self.blob_path=self._fixup(os.path.join(self.path, blob_path))
        self.ringerpath=self._fixup(os.path.join(self.path, "ringer"))
        self.wallpaperpath=self._fixup(os.path.join(self.path, "wallpaper"))
        self.phonebookpath=self._fixup(os.path.join(self.path, "phonebook"))
        self.calendarpath=self._fixup(os.path.join(self.path, "calendar"))

        self.EnsureDatabase(self.path, self.path, database_name)
        # create all the panels for this phone
        if self.config.ReadInt("console", 0):
            import developer
            id=self.tree.AddPage(self.phone_id, developer.DeveloperPanel(self.parent, {'mw': self.mw, 'db': self.database} ), "Console", self.tree.console)
        self.phonewidget=phonebook.PhoneWidget(self, self.parent, self.config)
        id=self.tree.AddPage(self.phone_id, self.phonewidget, "PhoneBook", self.tree.phonebook,id)
        self.mediawidget=media_root.MediaWidget(self, self.parent)
        id=self.tree.AddPage(self.phone_id, self.mediawidget,
                             "Media", self.tree.media, id,
                             helpids.ID_TAB_MEDIA)
        self.calendarwidget=bpcalendar.Calendar(self, self.parent)
        id=self.tree.AddPage(self.phone_id, self.calendarwidget, "Calendar", self.tree.calendar,id)
        self.memowidget=memo.MemoWidget(self, self.parent)
        id=self.tree.AddPage(self.phone_id, self.memowidget, "Memo", self.tree.memo,id)
        self.todowidget=todo.TodoWidget(self, self.parent)
        id=self.tree.AddPage(self.phone_id, self.todowidget, 'Todo', self.tree.todo,id)
        self.smswidget=sms_tab.SMSWidget(self, self.parent)
        id=self.tree.AddPage(self.phone_id, self.smswidget, 'SMS',
                             self.tree.sms,id, helpids.ID_TAB_SMS)
        self.callhistorywidget=call_history.CallHistoryWidget(self, self.parent)
        id=self.tree.AddPage(self.phone_id, self.callhistorywidget, 'Call History', self.tree.callhistory, id)
        self.playlistwidget=playlist.PlaylistWidget(self, self.parent)
        id=self.tree.AddPage(self.phone_id, self.playlistwidget, 'Play List', self.tree.playlist,id)
        self.t9editorwidget=t9editor.T9EditorWidget(self, self.parent)
        id=self.tree.AddPage(self.phone_id, self.t9editorwidget, 'T9 Editor',
                          None, id, helpids.ID_TAB_T9EDITOR)

        # update the the status bar info
        self.mw.SetPhoneModelStatus()
        self.mw.SetVersionsStatus()

        # populate all the widgets
        try:
            results={}
            # get info
            self.phonewidget.getfromfs(results)
            self.mediawidget.GetWallpaper().getfromfs(results)
            self.mediawidget.GetRinger().getfromfs(results)    
            self.calendarwidget.getfromfs(results)
            self.memowidget.getfromfs(results)
            self.todowidget.getfromfs(results)
            self.smswidget.getfromfs(results)
            self.callhistorywidget.getfromfs(results)
            self.playlistwidget.getfromfs(results)
            self.t9editorwidget.getfromfs(results)
            # update controls
            wx.SafeYield(onlyIfNeeded=True)
            self.phonewidget.populate(results)
            wx.SafeYield(onlyIfNeeded=True)
            self.mediawidget.GetWallpaper().populate(results)
            wx.SafeYield(onlyIfNeeded=True)
            self.mediawidget.GetRinger().populate(results)
            wx.SafeYield(onlyIfNeeded=True)
            self.calendarwidget.populate(results)
            wx.SafeYield(onlyIfNeeded=True)
            self.memowidget.populate(results)
            wx.SafeYield(onlyIfNeeded=True)
            self.todowidget.populate(results)
            wx.SafeYield(onlyIfNeeded=True)
            self.smswidget.populate(results)
            wx.SafeYield(onlyIfNeeded=True)
            self.callhistorywidget.populate(results)
            wx.SafeYield(onlyIfNeeded=True)
            self.playlistwidget.populate(results)
            wx.SafeYield(onlyIfNeeded=True)
            self.t9editorwidget.populate(results)
        except Exception, e:
            if __debug__:
                raise
   	wx.CallAfter(self.tree.SetStartupPage)

    def OnPhoneChanged(self, _):
        self.phoneprofile=self.mw.phoneprofile

    # deal with the database
    def EnsureDatabase(self, newpath, oldpath, database_file):
        newdbpath=os.path.abspath(os.path.join(newpath, database_file))
        if oldpath is not None and len(oldpath) and oldpath!=newpath:
            # copy database to new location
            if self.database:
                self.database=None # cause it to be closed
            olddbpath=os.path.abspath(os.path.join(oldpath, "bitpim.db"))
            if os.path.exists(olddbpath) and not os.path.exists(newdbpath):
                shutil.copyfile(olddbpath, newdbpath)
        self.database=None # allow gc
        # Preparing for virtual tables to store media data
        vtabs=[ { 'tablename': 'ringtone-index__mediadata',
                  'modulename': 'ringtonemodule',
                  'moduleclass': vtab_media.Media,
                  'args': (self.ringerpath,) },
                { 'tablename': 'wallpaper-index__mediadata',
                  'modulename': 'wallpapermodule',
                  'moduleclass': vtab_media.Media,
                  'args': (self.wallpaperpath,) }
                ]
        self.database=database.Database(newdbpath, vtabs)
            
    def GetDatabase(self):
        return self.database

    def _fixup(self, path):
        # os.path.join screws up adding root directory of a drive to
        # a directory.  eg join("c:\", "foo") gives "c:\\foo" whch
        # is invalid.  This function fixes that
        if len(path)>=3:
            if path[1]==':' and path[2]=='\\' and path[3]=='\\':
                return path[0:2]+path[3:]
        return path
        
    def OnBusyStart(self):
        return self.mw.OnBusyStart()
        
    def OnBusyEnd(self):
        return self.mw.OnBusyEnd()

    def log(self, str):
        self.mw.log(str)


