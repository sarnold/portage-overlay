### BITPIM
###
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: filesystem.py 4390 2007-09-05 00:08:19Z djpham $

"""The main gui code for BitPim"""

# System modules
from __future__ import with_statement
import ConfigParser
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
import fileview
import widgets

# wx modules
import wx
import wx.lib.colourdb
import wx.gizmos
import wx.html
import wx.lib.mixins.listctrl  as  listmix

# my modules
import guiwidgets
import common
import helpids
import comdiagnose
import guihelper
import hexeditor
import pubsub
import phones.com_brew as com_brew
import gui
import widgets


class FileSystemView(wx.SplitterWindow, widgets.BitPimWidget):
    def __init__(self, mainwindow, parent, id=-1):
        # the listbox and textbox in a splitter
        self.mainwindow=mainwindow
        wx.SplitterWindow.__init__(self, parent, id, style=wx.SP_LIVE_UPDATE)
        self.tree=FileSystemDirectoryView(mainwindow, self, wx.NewId(), style=(wx.TR_DEFAULT_STYLE|wx.TR_NO_LINES)&~wx.TR_TWIST_BUTTONS)
        self.list=FileSystemFileView(mainwindow, self, wx.NewId())
        self.sash_pos=mainwindow.config.ReadInt("filesystemsplitterpos", 200)
        self.update_sash=False
        self.SplitVertically(self.tree, self.list, self.sash_pos)
        self.SetMinimumPaneSize(20)
        wx.EVT_SPLITTER_SASH_POS_CHANGED(self, id, self.OnSplitterPosChanged)
        pubsub.subscribe(self.OnPhoneModelChanged, pubsub.PHONE_MODEL_CHANGED)

    def __del__(self):
        pubsub.unsubscribe(self.OnPhoneModelChanged)

    def OnPhoneModelChanged(self, msg):
        # if the phone changes we reset ourselves
        self.list.ResetView()
        self.tree.ResetView()

    def OnSplitterPosChanged(self,_):
        if self.update_sash:
            self.sash_pos=self.GetSashPosition()
            self.mainwindow.config.WriteInt("filesystemsplitterpos",
                                            self.sash_pos)

    def OnPreActivate(self):
        self.update_sash=False
    def OnPostActivate(self):
        self.SetSashPosition(self.sash_pos)
        self.update_sash=True

    def OnPhoneReboot(self,_):
        mw=self.mainwindow
        mw.MakeCall( gui.Request(mw.wt.phonerebootrequest),
                     gui.Callback(self.OnPhoneRebootResults) )

    def OnPhoneRebootResults(self, exception, _):
        # special case - we always clear the comm connection
        # it is needed if the reboot succeeds, and if it didn't
        # we probably have bad comms anyway
        mw=self.mainwindow
        mw.wt.clearcomm()
        if mw.HandleException(exception): return

    def OnPhoneOffline(self,_):
        mw=self.mainwindow
        mw.MakeCall( gui.Request(mw.wt.phoneofflinerequest),
                     gui.Callback(self.OnPhoneOfflineResults) )

    def OnPhoneOfflineResults(self, exception, _):
        mw=self.mainwindow
        if mw.HandleException(exception): return

    def OnModemMode(self,_):
        mw=self.mainwindow
        mw.MakeCall( gui.Request(mw.wt.modemmoderequest),
                     gui.Callback(self.OnModemModeResults) )

    def OnModemModeResults(self, exception, _):
        mw=self.mainwindow
        if mw.HandleException(exception): return

    def ShowFiles(self, dir, refresh=False):
        self.list.ShowFiles(dir, refresh)

    def OnNewFileResults(self, parentdir, exception, _):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        self.ShowFiles(parentdir, True)

class FileSystemFileView(wx.ListCtrl, listmix.ColumnSorterMixin):
    def __init__(self, mainwindow, parent, id, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_SINGLE_SEL):
        wx.ListCtrl.__init__(self, parent, id, style=style)
        self.parent=parent
        self.mainwindow=mainwindow
        self.datacolumn=False # used for debugging and inspection of values
        self.InsertColumn(0, "Name", width=300)
        self.InsertColumn(1, "Size", format=wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(2, "Date", width=200)
        self.font=wx.TheFontList.FindOrCreateFont(10, family=wx.SWISS, style=wx.NORMAL, weight=wx.NORMAL)

        self.ResetView()        

        if self.datacolumn:
            self.InsertColumn(3, "Extra Stuff", width=400)
            listmix.ColumnSorterMixin.__init__(self, 4)
        else:
            listmix.ColumnSorterMixin.__init__(self, 3)

        #sort by genre (column 2), A->Z ascending order (1)
        self.filemenu=wx.Menu()
        self.filemenu.Append(guihelper.ID_FV_SAVE, "Save ...")
        self.filemenu.Append(guihelper.ID_FV_HEXVIEW, "Hexdump")
        self.filemenu.AppendSeparator()
        self.filemenu.Append(guihelper.ID_FV_DELETE, "Delete")
        self.filemenu.Append(guihelper.ID_FV_OVERWRITE, "Overwrite ...")
        # generic menu
        self.genericmenu=wx.Menu()
        self.genericmenu.Append(guihelper.ID_FV_NEWFILE, "New File ...")
        self.genericmenu.AppendSeparator()
        self.genericmenu.Append(guihelper.ID_FV_OFFLINEPHONE, "Offline Phone")
        self.genericmenu.Append(guihelper.ID_FV_REBOOTPHONE, "Reboot Phone")
        self.genericmenu.Append(guihelper.ID_FV_MODEMMODE, "Go to modem mode")
        wx.EVT_MENU(self.genericmenu, guihelper.ID_FV_NEWFILE, self.OnNewFile)
        wx.EVT_MENU(self.genericmenu, guihelper.ID_FV_OFFLINEPHONE, parent.OnPhoneOffline)
        wx.EVT_MENU(self.genericmenu, guihelper.ID_FV_REBOOTPHONE, parent.OnPhoneReboot)
        wx.EVT_MENU(self.genericmenu, guihelper.ID_FV_MODEMMODE, parent.OnModemMode)
        wx.EVT_MENU(self.filemenu, guihelper.ID_FV_SAVE, self.OnFileSave)
        wx.EVT_MENU(self.filemenu, guihelper.ID_FV_HEXVIEW, self.OnHexView)
        wx.EVT_MENU(self.filemenu, guihelper.ID_FV_DELETE, self.OnFileDelete)
        wx.EVT_MENU(self.filemenu, guihelper.ID_FV_OVERWRITE, self.OnFileOverwrite)
        wx.EVT_RIGHT_DOWN(self.GetMainWindow(), self.OnRightDown)
        wx.EVT_RIGHT_UP(self.GetMainWindow(), self.OnRightUp)
        wx.EVT_LIST_ITEM_ACTIVATED(self,id, self.OnItemActivated)
        self.image_list=wx.ImageList(16, 16)
        a={"sm_up":"GO_UP","sm_dn":"GO_DOWN","w_idx":"WARNING","e_idx":"ERROR","i_idx":"QUESTION"}
        for k,v in a.items():
            s="self.%s= self.image_list.Add(wx.ArtProvider_GetBitmap(wx.ART_%s,wx.ART_TOOLBAR,(16,16)))" % (k,v)
            exec(s)
        self.img_file=self.image_list.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE,
                                                             wx.ART_OTHER,
                                                             (16, 16)))
        self.SetImageList(self.image_list, wx.IMAGE_LIST_SMALL)

        #if guihelper.IsMSWindows():
            # turn on drag-and-drag for windows
            #wx.EVT_MOTION(self, self.OnStartDrag)

        self.__dragging=False
        self.add_files=[]
        self.droptarget=fileview.MyFileDropTarget(self, True, False)
        self.SetDropTarget(self.droptarget)

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

    def OnDropFiles(self, _, dummy, filenames):
        # There is a bug in that the most recently created tab
        # in the notebook that accepts filedrop receives these
        # files, not the most visible one.  We find the currently
        # viewed tab in the notebook and send the files there
        if self.__dragging:
            # I'm the drag source, forget 'bout it !
            return
        target=self # fallback
        t=self.mainwindow.GetCurrentActiveWidget()
        if isinstance(t, FileSystemFileView):
            # changing target in dragndrop
            target=t
        self.add_files=filenames
        target.OnAddFiles()

    def OnDragOver(self, x, y, d):
        # force copy (instead of move)
        return wx._misc.DragCopy

    def OnAddFiles(self):
        mw=self.mainwindow
        if not len(self.add_files):
            return
        for file in self.add_files:
            if file is None:
                continue
            if len(self.path):
                path=self.path+"/"+os.path.basename(file)
            else:
                path=os.path.basename(file) # you can't create files in root but I won't stop you
            contents=open(file, "rb").read()
            mw.MakeCall( gui.Request(mw.wt.writefile, path, contents),
                         gui.Callback(self.OnAddFilesResults, self.path) )
            self.add_files.remove(file)
            # can only add one file at a time
            break

    def OnAddFilesResults(self, parentdir, exception, _):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        # add next file if there is one
        if not len(self.add_files):
            self.ShowFiles(parentdir, True)
        else:
            self.OnAddFiles()

    if guihelper.IsMSWindows():
        # drag-and-drop files only works in Windows
        def OnStartDrag(self, evt):
            evt.Skip()
            if not evt.LeftIsDown():
                return
            path=self.itemtopath(self.GetFirstSelected())
            drag_source=wx.DropSource(self)
            file_names=wx.FileDataObject()
            file_names.AddFile(path)
            drag_source.SetData(file_names)
            self.__dragging=True
            res=drag_source.DoDragDrop(wx.Drag_CopyOnly)
            self.__dragging=False

    def OnRightUp(self, event):
        pt = event.GetPosition()
        item, flags = self.HitTest(pt)
        if item is not -1:
            self.Select(item)
            self.PopupMenu(self.filemenu, pt)
        else:
            self.PopupMenu(self.genericmenu, pt)
                    
    def OnRightDown(self,event):
        # You have to capture right down otherwise it doesn't feed you right up
        pt = event.GetPosition();
        item, flags = self.HitTest(pt)
        try:
            self.Select(item)
        except:
            pass

    def OnNewFile(self,_):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, style=wx.OPEN|wx.HIDE_READONLY|wx.CHANGE_DIR),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                infile=dlg.GetPath()
                contents=open(infile, "rb").read()
                if len(self.path):
                    path=self.path+"/"+os.path.basename(dlg.GetPath())
                else:
                    path=os.path.basename(dlg.GetPath()) # you can't create files in root but I won't stop you
                mw=self.mainwindow
                mw.MakeCall( gui.Request(mw.wt.writefile, path, contents),
                             gui.Callback(self.parent.OnNewFileResults, self.path) )

    def OnFileSave(self, _):
        path=self.itemtopath(self.GetFirstSelected())
        mw=self.mainwindow
        mw.MakeCall( gui.Request(mw.wt.getfile, path),
                     gui.Callback(self.OnFileSaveResults, path) )
        
    def OnFileSaveResults(self, path, exception, contents):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        bn=guihelper.basename(path)
        ext=guihelper.getextension(bn)
        if len(ext):
            ext="%s files (*.%s)|*.%s" % (ext.upper(), ext, ext)
        else:
            ext="All files|*"
        with guihelper.WXDialogWrapper(wx.FileDialog(self, "Save File As", defaultFile=bn, wildcard=ext,
                                                     style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                file(dlg.GetPath(), "wb").write(contents)

    def OnItemActivated(self,_):
        self.OnHexView(self)

    def OnHexView(self, _):
        path=self.itemtopath(self.GetFirstSelected())
        mw=self.mainwindow
        mw.MakeCall( gui.Request(mw.wt.getfile, path),
                     gui.Callback(self.OnHexViewResults, path) )
        
    def OnHexViewResults(self, path, exception, result):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        # ::TODO:: make this use HexEditor
##        dlg=guiwidgets.MyFixedScrolledMessageDialog(self, common.datatohexstring(result),
##                                                    path+" Contents", helpids.ID_HEXVIEW_DIALOG)
        dlg=hexeditor.HexEditorDialog(self, result, path+" Contents")
        dlg.Show()

    def OnFileDelete(self, _):
        path=self.itemtopath(self.GetFirstSelected())
        mw=self.mainwindow
        mw.MakeCall( gui.Request(mw.wt.rmfile, path),
                     gui.Callback(self.OnFileDeleteResults, guihelper.dirname(path)) )
        
    def OnFileDeleteResults(self, parentdir, exception, _):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        self.ShowFiles(parentdir, True)

    def OnFileOverwrite(self,_):
        path=self.itemtopath(self.GetFirstSelected())
        with guihelper.WXDialogWrapper(wx.FileDialog(self, style=wx.OPEN|wx.HIDE_READONLY|wx.CHANGE_DIR),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                infile=dlg.GetPath()
                contents=open(infile, "rb").read()
                mw=self.mainwindow
                mw.MakeCall( gui.Request(mw.wt.writefile, path, contents),
                             gui.Callback(self.OnFileOverwriteResults, guihelper.dirname(path)) )
        
    def OnFileOverwriteResults(self, parentdir, exception, _):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        self.ShowFiles(parentdir, True)

    def ResetView(self):
        self.DeleteAllItems()
        self.files={}
        self.path=None
        self.itemDataMap = self.files
        self.itemIndexMap = self.files.keys()
        self.SetItemCount(0)

    def ShowFiles(self, path, refresh=False):
        mw=self.mainwindow
        if path == self.path and not refresh:
            return
        self.path=None
        mw.MakeCall( gui.Request(mw.wt.getfileonlylist, path),
                     gui.Callback(self.OnShowFilesResults, path) )
        
    def OnShowFilesResults(self, path, exception, result):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        count=self.GetItemCount()
        self.path=path
        self.DeleteAllItems()
        self.files={}
        index=0
        for file in result:
            index=index+1
            f=guihelper.basename(file)
            if self.datacolumn:
                self.files[index]=(f, `result[file]['size']`, result[file]['date'][1], result[file]['data'], file)
            else:
                self.files[index]=(f, `result[file]['size']`, result[file]['date'][1], file)
        self.itemDataMap = self.files
        self.itemIndexMap = self.files.keys()
        self.SetItemCount(index)
        self.SortListItems()
        if count!=0 and index==0:
            wx.EVT_PAINT(self, self.OnPaint)
        elif count==0 and index!=0:
            self.Unbind(wx.EVT_PAINT)

    def itemtopath(self, item):
        index=self.itemIndexMap[item]
        if self.datacolumn:
            return self.itemDataMap[index][4]
        return self.itemDataMap[index][3]

    def SortItems(self,sorter=None):
        col=self._col
        sf=self._colSortFlag[col]

        #creating pairs [column item defined by col, key]
        items=[]
        for k,v in self.itemDataMap.items():
            if col==1:
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
        return self.img_file

    def OnGetItemAttr(self, item):
        return None

class FileSystemDirectoryView(wx.TreeCtrl):
    def __init__(self, mainwindow, parent, id, style):
        wx.TreeCtrl.__init__(self, parent, id, style=style)
        self.parent=parent
        self.mainwindow=mainwindow
        wx.EVT_TREE_ITEM_EXPANDED(self, id, self.OnItemExpanded)
        wx.EVT_TREE_SEL_CHANGED(self,id, self.OnItemSelected)
        self.dirmenu=wx.Menu()
        self.dirmenu.Append(guihelper.ID_FV_NEWSUBDIR, "Make subdirectory ...")
        self.dirmenu.Append(guihelper.ID_FV_NEWFILE, "New File ...")
        self.dirmenu.AppendSeparator()
        self.dirmenu.Append(guihelper.ID_FV_BACKUP, "Backup directory ...")
        self.dirmenu.Append(guihelper.ID_FV_BACKUP_TREE, "Backup entire tree ...")
        self.dirmenu.Append(guihelper.ID_FV_RESTORE, "Restore ...")
        self.dirmenu.AppendSeparator()
        self.dirmenu.Append(guihelper.ID_FV_REFRESH, "Refresh")
        self.dirmenu.AppendSeparator()
        self.dirmenu.Append(guihelper.ID_FV_DELETE, "Delete")
        self.dirmenu.AppendSeparator()
        self.dirmenu.Append(guihelper.ID_FV_TOTAL_REFRESH, "Refresh Filesystem")
        self.dirmenu.Append(guihelper.ID_FV_OFFLINEPHONE, "Offline Phone")
        self.dirmenu.Append(guihelper.ID_FV_REBOOTPHONE, "Reboot Phone")
        self.dirmenu.Append(guihelper.ID_FV_MODEMMODE, "Go to modem mode")
        # generic menu
        self.genericmenu=wx.Menu()
        self.genericmenu.Append(guihelper.ID_FV_TOTAL_REFRESH, "Refresh Filesystem")
        self.genericmenu.Append(guihelper.ID_FV_OFFLINEPHONE, "Offline Phone")
        self.genericmenu.Append(guihelper.ID_FV_REBOOTPHONE, "Reboot Phone")
        self.genericmenu.Append(guihelper.ID_FV_MODEMMODE, "Go to modem mode")
        wx.EVT_MENU(self.genericmenu, guihelper.ID_FV_TOTAL_REFRESH, self.OnRefresh)
        wx.EVT_MENU(self.genericmenu, guihelper.ID_FV_OFFLINEPHONE, parent.OnPhoneOffline)
        wx.EVT_MENU(self.genericmenu, guihelper.ID_FV_REBOOTPHONE, parent.OnPhoneReboot)
        wx.EVT_MENU(self.genericmenu, guihelper.ID_FV_MODEMMODE, parent.OnModemMode)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_NEWSUBDIR, self.OnNewSubdir)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_NEWFILE, self.OnNewFile)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_DELETE, self.OnDirDelete)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_BACKUP, self.OnBackupDirectory)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_BACKUP_TREE, self.OnBackupTree)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_RESTORE, self.OnRestore)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_REFRESH, self.OnDirRefresh)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_TOTAL_REFRESH, self.OnRefresh)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_OFFLINEPHONE, parent.OnPhoneOffline)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_REBOOTPHONE, parent.OnPhoneReboot)
        wx.EVT_MENU(self.dirmenu, guihelper.ID_FV_MODEMMODE, parent.OnModemMode)
        wx.EVT_RIGHT_DOWN(self, self.OnRightDown)
        wx.EVT_RIGHT_UP(self, self.OnRightUp)
        self.image_list=wx.ImageList(16, 16)
        self.img_dir=self.image_list.Add(wx.ArtProvider_GetBitmap(guihelper.ART_FOLDER,
                                                             wx.ART_OTHER,
                                                             (16, 16)))
        self.img_dir_open=self.image_list.Add(wx.ArtProvider_GetBitmap(guihelper.ART_FOLDER_OPEN,
                                                             wx.ART_OTHER,
                                                             (16, 16)))
        self.SetImageList(self.image_list)
        self.add_files=[]
        self.add_target=""
        self.droptarget=fileview.MyFileDropTarget(self, True, True)
        self.SetDropTarget(self.droptarget)
        self.ResetView()

    def ResetView(self):
        self.first_time=True
        self.DeleteAllItems()
        self.root=self.AddRoot("/")
        self.item=self.root
        self.SetPyData(self.root, None)
        self.SetItemHasChildren(self.root, True)
        self.SetItemImage(self.root, self.img_dir)
        self.SetItemImage(self.root, self.img_dir_open, which=wx.TreeItemIcon_Expanded)
        self.SetPyData(self.AppendItem(self.root, "Retrieving..."), None)
        self.selections=[]
        self.dragging=False
        self.skip_dir_list=0

    def OnDropFiles(self, x, y, filenames):
        target=self
        t=self.mainwindow.GetCurrentActiveWidget()
        if isinstance(t, FileSystemDirectoryView):
            # changing target in dragndrop
            target=t
        # make sure that the files are being dropped onto a real directory
        item, flags = self.HitTest((x, y))
        if item.IsOk():
            self.SelectItem(item)
            self.add_target=self.itemtopath(item)
            self.add_files=filenames
            target.OnAddFiles()
        self.dragging=False

    def OnDragOver(self, x, y, d):
        target=self
        t=self.mainwindow.GetCurrentActiveWidget()
        if isinstance(t, FileSystemDirectoryView):
            # changing target in dragndrop
            target=t
        # make sure that the files are being dropped onto a real directory
        item, flags = self.HitTest((x, y))
        selections = self.GetSelections()
        if item.IsOk():
            if selections != [item]:
                self.UnselectAll()
                self.SelectItem(item)
            return wx._misc.DragCopy
        elif selections:
            self.UnselectAll()
        return wx._misc.DragNone

    def _saveSelection(self):
        self.selections = self.GetSelections()
        self.UnselectAll()

    def _restoreSelection(self):
        self.UnselectAll()
        for i in self.selections:
            self.SelectItem(i)
        self.selections=[]

    def OnEnter(self, x, y, d):
        self._saveSelection()
        self.dragging=True
        return d

    def OnLeave(self):
        self.dragging=False
        self._restoreSelection()

    def OnAddFiles(self):
        mw=self.mainwindow
        if not len(self.add_files):
            return
        for file in self.add_files:
            if file is None:
                continue
            if len(self.add_target):
                path=self.add_target+"/"+os.path.basename(file)
            else:
                path=os.path.basename(file) # you can't create files in root but I won't stop you
            contents=open(file, "rb").read()
            mw.MakeCall( gui.Request(mw.wt.writefile, path, contents),
                         gui.Callback(self.OnAddFilesResults, self.add_target) )
            self.add_files.remove(file)
            # can only add one file at a time
            break

    def OnAddFilesResults(self, parentdir, exception, _):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        # add next file if there is one
        if not len(self.add_files):
            self.parent.ShowFiles(parentdir, True)
        else:
            self.OnAddFiles()

    def OnRightUp(self, event):
        pt = event.GetPosition();
        item, flags = self.HitTest(pt)
        if item.IsOk():
            self.SelectItem(item)
            self.PopupMenu(self.dirmenu, pt)
        else:
            self.SelectItem(self.item)
            self.PopupMenu(self.genericmenu, pt)
                    
    def OnRightDown(self, _):
        # You have to capture right down otherwise it doesn't feed you right up
        pass

    def OnItemSelected(self,_):
        if not self.dragging and not self.first_time:
            item=self.GetSelection()
            if item.IsOk() and item != self.item:
                path=self.itemtopath(item)
                self.parent.ShowFiles(path)
                if not self.skip_dir_list:
                    self.OnDirListing(path)
                self.item=item

    def OnItemExpanded(self, event):
        if not self.skip_dir_list:
            item=event.GetItem()
            if self.first_time:
                self.GetFullFS()
            else:
                path=self.itemtopath(item)
                self.OnDirListing(path)

    def AddDirectory(self, location, name):
        new_item=self.AppendItem(location, name)
        self.SetPyData(new_item, None)
        self.SetItemImage(new_item, self.img_dir)
        self.SetItemImage(new_item, self.img_dir_open, which=wx.TreeItemIcon_Expanded)
        # workaround for bug, + does not get displayed if this is the first child
        if self.GetChildrenCount(location, False) == 1 and not self.IsExpanded(location):
            self.skip_dir_list+=1
            self.Expand(location)
            self.Collapse(location)
            self.skip_dir_list-=1
        return new_item

    def RemoveDirectory(self, parent, item):
        # if this is the last item in the parent we need to collapse the parent
        if self.GetChildrenCount(parent, False) == 1:
            self.Collapse(parent)
        self.Delete(item)

    def GetFullFS(self):
        mw=self.mainwindow
        mw.OnBusyStart()
        mw.GetStatusBar().progressminor(0, 100, 'Reading Phone File System ...')
        mw.MakeCall( gui.Request(mw.wt.fulldirlisting),
                     gui.Callback(self.OnFullDirListingResults) )

    def OnFullDirListingResults(self, exception, result):
        mw=self.mainwindow
        mw.OnBusyEnd()
        if mw.HandleException(exception):
            self.Collapse(self.root)
            return
        self.first_time=False
        self.skip_dir_list+=1
        self.SelectItem(self.root)
        self.DeleteChildren(self.root)
        keys=result.keys()
        keys.sort()
        # build up the tree
        for k in keys:
            path, dir=os.path.split(k)
            item=self.pathtoitem(path)
            self.AddDirectory(item, dir)
        self.skip_dir_list-=1
        self.parent.ShowFiles("")

    def OnDirListing(self, path):
        mw=self.mainwindow
        mw.MakeCall( gui.Request(mw.wt.singledirlisting, path),
                     gui.Callback(self.OnDirListingResults, path) )

    def OnDirListingResults(self, path, exception, result):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        item=self.pathtoitem(path)
        l=[]
        child,cookie=self.GetFirstChild(item)
        for dummy in range(0,self.GetChildrenCount(item,False)):
            l.append(child)
            child,cookie=self.GetNextChild(item,cookie)
        # we now have a list of children in l
        sort=False
        for file in result:
            children=True
            f=guihelper.basename(file)
            found=None
            for i in l:
                if self.GetItemText(i)==f:
                    found=i
                    break
            if found is None:
                # this only happens if the phone has added the directory
                # after we got the initial file view, unusual but possible
                found=self.AddDirectory(item, f)
                self.OnDirListing(file)
                sort=True
        for i in l: # remove all children not present in result
            if not result.has_key(self.itemtopath(i)):
                self.RemoveDirectory(item, i)
        if sort:
            self.SortChildren(item)

    def OnNewSubdir(self, _):
        with guihelper.WXDialogWrapper(wx.TextEntryDialog(self, "Subdirectory name?", "Create Subdirectory", "newfolder"),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                item=self.GetSelection()
                parent=self.itemtopath(item)
                if len(parent):
                    path=parent+"/"+dlg.GetValue()
                else:
                    path=dlg.GetValue()
                mw=self.mainwindow
                mw.MakeCall( gui.Request(mw.wt.mkdir, path),
                             gui.Callback(self.OnNewSubdirResults, path) )
            
    def OnNewSubdirResults(self, new_path, exception, _):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        path, dir=os.path.split(new_path)
        item=self.pathtoitem(path)
        self.AddDirectory(item, dir)
        self.SortChildren(item)
        self.Expand(item)
        # requery the phone just incase
        self.OnDirListing(path)
        
    def OnNewFile(self,_):
        parent=self.itemtopath(self.GetSelection())
        with guihelper.WXDialogWrapper(wx.FileDialog(self, style=wx.OPEN|wx.HIDE_READONLY|wx.CHANGE_DIR),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                infile=dlg.GetPath()
                contents=open(infile, "rb").read()
                if len(parent):
                    path=parent+"/"+os.path.basename(dlg.GetPath())
                else:
                    path=os.path.basename(dlg.GetPath()) # you can't create files in root but I won't stop you
                mw=self.mainwindow
                mw.MakeCall( gui.Request(mw.wt.writefile, path, contents),
                             gui.Callback(self.OnNewFileResults, parent) )
        
    def OnNewFileResults(self, parentdir, exception, _):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        self.parent.ShowFiles(parentdir, True)

    def OnDirDelete(self, _):
        path=self.itemtopath(self.GetSelection())
        mw=self.mainwindow
        mw.MakeCall( gui.Request(mw.wt.rmdirs, path),
                     gui.Callback(self.OnDirDeleteResults, path) )
        
    def OnDirDeleteResults(self, path, exception, _):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        # remove the directory from the view
        parent, dir=os.path.split(path)
        parent_item=self.pathtoitem(parent)
        del_item=self.pathtoitem(path)
        self.RemoveDirectory(parent_item, del_item)
        # requery the phone just incase
        self.OnDirListing(parent)

    def OnBackupTree(self, _):
        self.OnBackup(recurse=100)

    def OnBackupDirectory(self, _):
        self.OnBackup()

    def OnBackup(self, recurse=0):
        path=self.itemtopath(self.GetSelection())
        mw=self.mainwindow
        mw.MakeCall( gui.Request(mw.wt.getbackup, path, recurse),
                     gui.Callback(self.OnBackupResults, path) )

    def OnBackupResults(self, path, exception, backup):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        bn=guihelper.basename(path)
        if len(bn)<1:
            bn="root"
        bn+=".zip"
        ext="Zip files|*.zip|All Files|*"
        with guihelper.WXDialogWrapper(wx.FileDialog(self, "Save File As", defaultFile=bn, wildcard=ext,
                                                     style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                file(dlg.GetPath(), "wb").write(backup)

    def OnRestore(self, _):
        ext="Zip files|*.zip|All Files|*"
        path=self.itemtopath(self.GetSelection())
        bn=guihelper.basename(path)
        if len(bn)<1:
            bn="root"
        bn+=".zip"
        ext="Zip files|*.zip|All Files|*"
        with guihelper.WXDialogWrapper(wx.FileDialog(self, "Open backup file", defaultFile=bn, wildcard=ext,
                                                     style=wx.OPEN|wx.HIDE_READONLY|wx.CHANGE_DIR),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                name=dlg.GetPath()
                if not zipfile.is_zipfile(name):
                    with guihelper.WXDialogWrapper(guiwidgets.AlertDialogWithHelp(self.mainwindow, name+" is not a valid zipfile.", "Zip file required",
                                                                                  lambda _: wx.GetApp().displayhelpid(helpids.ID_NOT_A_ZIPFILE),
                                                                                  style=wx.OK|wx.ICON_ERROR),
                                                   True):
                        return
                zipf=zipfile.ZipFile(name, "r")
                xx=zipf.testzip()
                if xx is not None:
                    with guihelper.WXDialogWrapper(guiwidgets.AlertDialogWithHelp(self.mainwindow, name+" has corrupted contents.  Use a repair utility to fix it",
                                                                                  "Zip file corrupted",
                                                                                  lambda _: wx.GetApp().displayhelpid(helpids.ID_ZIPFILE_CORRUPTED),
                                                                                  style=wx.OK|wx.ICON_ERROR),
                                                   True):
                        return

                RestoreDialog(self.mainwindow, "Restore files", zipf, path, self.OnRestoreOK).Show(True)

    def OnRestoreOK(self, zipf, names, parentdir):
        if len(names)==0:
            wx.MessageBox("You didn't select any files to restore!", "No files selected",
                         wx.OK|wx.ICON_EXCLAMATION)
            return
        l=[]
        for zipname, fsname in names:
            l.append( (fsname, zipf.read(zipname)) )

        mw=self.mainwindow
        mw.MakeCall( gui.Request(mw.wt.restorefiles, l),
                     gui.Callback(self.OnRestoreResults, parentdir) )

    def OnRestoreResults(self, parentdir, exception, results):
        mw=self.mainwindow
        if mw.HandleException(exception): return
        ok=filter(lambda s: s[0], results)
        fail=filter(lambda s: not s[0], results)

        # re-read the filesystem (if anything was restored)
        if len(parentdir):
            dirs=[]
            for _, name in results:
                while(len(name)>len(parentdir)):
                    name=guihelper.dirname(name)
                    if name not in dirs:
                        dirs.append(name)
            dirs.sort()
            for d in dirs:
                self.OnDirListing(d)

        self.OnDirListing(parentdir)

        if len(ok) and len(fail)==0:
            dlg=wx.MessageDialog(mw, "All files restored ok", "All files restored",
                                wx.OK|wx.ICON_INFORMATION)
            dlg.Show(True)
            return
        if len(fail) and len(ok)==0:
            wx.MessageBox("All files failed to restore", "No files restored",
                         wx.OK|wx.ICON_ERROR)
            return

        op="Failed to restore some files.  Check the log for reasons.:\n\n"
        for s,n in fail:
            op+="   "+n+"\n"
        wx.MessageBox(op, "Some restores failed", wx.OK|wx.ICON_ERROR)

    def OnDirRefresh(self, _):
        path=self.itemtopath(self.GetSelection())
        self.parent.ShowFiles(path, True)
        self.OnDirListing(path)

    def OnRefresh(self, _):
        self.GetFullFS()

    def itemtopath(self, item):
        if item==self.root: return ""
        res=self.GetItemText(item)
        while True:
            parent=self.GetItemParent(item)
            if parent==self.root:
                return res
            item=parent
            res=self.GetItemText(item)+"/"+res
        # can't get here, but pychecker doesn't seem to realise
        assert False
        return ""
        
    def pathtoitem(self, path):
        if path=="": return self.root
        dirs=path.split('/')
        node=self.root
        for n in range(0, len(dirs)):
            foundnode=None
            child,cookie=self.GetFirstChild(node)
            for dummy in range(0, self.GetChildrenCount(node, False)):
                d=self.GetItemText(child)
                if d==dirs[n]:
                    node=child
                    foundnode=node
                    break
                child,cookie=self.GetNextChild(node,cookie)
            if foundnode is not None:
                continue
            # make the node
            node=self.AppendItem(node, dirs[n])
            self.SetPyData(node, None)
        return node

class RestoreDialog(wx.Dialog):
    """A dialog that lists all the files that will be restored"""
    
    def __init__(self, parent, title, zipf, path, okcb):
        """Constructor

        @param path: Placed before names in the archive.  Should not include a
                       trailing slash.
        """
        wx.Dialog.__init__(self, parent, -1, title, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add( wx.StaticText(self, -1, "Choose files to restore"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        nl=zipf.namelist()
        nl.sort()

        prefix=path
        if len(prefix)=="/" or prefix=="":
            prefix=""
        else:
            prefix+="/"

        nnl=map(lambda i: prefix+i, nl)

        self.clb=wx.CheckListBox(self, -1, choices=nnl, style=wx.LB_SINGLE|wx.LB_HSCROLL|wx.LB_NEEDED_SB, size=wx.Size(200,300))

        for i in range(len(nnl)):
            self.clb.Check(i, True)

        vbs.Add( self.clb, 1, wx.EXPAND|wx.ALL, 5)

        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL, 5)

        vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALIGN_CENTER|wx.ALL, 5)
    
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

        wx.EVT_BUTTON(self, wx.ID_HELP, lambda _: wx.GetApp().displayhelpid(helpids.ID_RESTOREDIALOG))
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)
        self.okcb=okcb
        self.zipf=zipf
        self.nl=zip(nl, nnl)
        self.path=path

    def OnOK(self, _):
        names=[]
        for i in range(len(self.nl)):
            if self.clb.IsChecked(i):
                names.append(self.nl[i])
        self.okcb(self.zipf, names, self.path)
        self.Show(False)
        self.Destroy()
