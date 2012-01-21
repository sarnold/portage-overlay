### BITPIM
###
### Copyright (C) 2006 Simon Capper <scapper@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###


# standard modules
from __future__ import with_statement
import contextlib
import os
import cStringIO
import copy
import sha
import time
import string
import zipfile


# wx modules
import wx

# BitPim modules
import database
import common
import guiwidgets
import guihelper
import pubsub
import widgets
import wallpaper
import ringers

class MediaWidget(wx.Panel, widgets.BitPimWidget):
    def __init__(self, mainwindow, parent):
        super(MediaWidget, self).__init__(parent, -1)
        self._main_window=mainwindow
        self.call_history_tree_nodes={}
        self._parent=parent
        # main box sizer
        self.vbs=wx.BoxSizer(wx.VERTICAL)
        # main stats display
        self.vbs.Add(wx.StaticText(self, -1, 'Media summary'), 0, wx.ALIGN_LEFT|wx.ALL, 2)
        # all done
        self.SetSizer(self.vbs)
        self.SetAutoLayout(True)
        self.vbs.Fit(self)
        self.ringernodes={}
        self.wallpapernodes={}
        self.widget_to_save=None
        self.origin_to_save=""
        self.SetBackgroundColour(wx.WHITE)
        self.ringerwidget=ringers.RingerView(self._main_window, parent, self)
        self.wallpaperwidget=wallpaper.WallpaperView(self._main_window, parent, self)
        pubsub.subscribe(self.OnPhoneModelChanged, pubsub.PHONE_MODEL_CHANGED)
        # populate data
        #self._populate()

    def DoMediaSummary(self):
        summary=[]
        summary=self.GetWidgetSummary(self.ringerwidget, summary)
        summary=self.GetWidgetSummary(self.wallpaperwidget, summary)
        self.vbs.Clear(deleteWindows=True)
        self.vbs.Add(wx.StaticText(self, -1, 'Media summary'), 0, wx.ALIGN_LEFT|wx.ALL, 2)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        name=wx.BoxSizer(wx.VERTICAL)
        count=wx.BoxSizer(wx.VERTICAL)
        size=wx.BoxSizer(wx.VERTICAL)
        name.Add(wx.StaticText(self, -1, 'Origin'), 0, wx.ALIGN_LEFT|wx.ALL, 2)
        count.Add(wx.StaticText(self, -1, 'Number Files'), 0, wx.ALIGN_LEFT|wx.ALL, 2)
        size.Add(wx.StaticText(self, -1, 'Size'), 0, wx.ALIGN_LEFT|wx.ALL, 2)
        total_files=0
        total_size=0
        for entry in summary:
            name.Add(wx.StaticText(self, -1, entry[0]), 0, wx.ALIGN_LEFT|wx.ALL, 2)
            count.Add(wx.StaticText(self, -1, str(entry[1])), 0, wx.ALIGN_LEFT|wx.ALL, 2)
            size.Add(wx.StaticText(self, -1, self.GetNiceSizeString(entry[2])), 0, wx.ALIGN_LEFT|wx.ALL, 2)
            total_files+=entry[1]
            total_size+=entry[2]
        hbs.Add(name, 0, wx.ALIGN_LEFT|wx.ALL, 2) 
        hbs.Add(count, 0, wx.ALIGN_LEFT|wx.ALL, 2) 
        hbs.Add(size, 0, wx.ALIGN_LEFT|wx.ALL, 2) 
        self.vbs.Add(hbs,  0, wx.ALIGN_LEFT|wx.ALL, 2)
        self.vbs.Add(wx.StaticText(self, -1, "Total number of media files: %d" % total_files), 0, wx.ALIGN_LEFT|wx.ALL, 2)
        self.vbs.Add(wx.StaticText(self, -1, "Total size of media files: %s" % self.GetNiceSizeString(total_size)), 0, wx.ALIGN_LEFT|wx.ALL, 2)
        self.vbs.Layout()

    def GetNiceSizeString(self, size):
        orig=size
        size=float(size)
        if size < 1024:
            return "%d bytes" % size
        size=size/1024
        if size < 1024:
            return "%.2f KB (%d bytes)" % (size, orig)
        size=size/1024
        return "%.2f MB (%d bytes)" % (size, orig)

    def GetWidgetSummary(self, widget, res):
        for k,e in widget.sections:
            num_files=0
            total_size=0
            for item in e:
                total_size+=item.size
                num_files+=1
            res.append((k.label, num_files, total_size))
        return res

    def GetRightClickMenuItems(self, node):
        result=[]
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EXPORT_MEDIA_TO_DIR, "Export to Folder ..." , "Export the media to a folder on your hard drive"))
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EXPORT_MEDIA_TO_ZIP, "Export to Zip File ..." , "Export the media to a zip file"))
        return result

    def GetRinger(self):
        return self.ringerwidget 

    def GetWallpaper(self):
        return self.wallpaperwidget 

    def OnInit(self):
        self.AddMediaNode("ringers", self.ringerwidget, self._tree.ringers)
        self.AddMediaNode("sounds", self.ringerwidget, self._tree.sounds)
        self.AddMediaNode("images", self.wallpaperwidget, self._tree.image)
        self.ringerwidget.updateprofilevariables(self._main_window.phoneprofile)
        self.wallpaperwidget.updateprofilevariables(self._main_window.phoneprofile)
        self.DoMediaSummary()

    def OnPhoneModelChanged(self, msg):
        for name in self.ringernodes:
            self._tree.DeletePage(self.ringernodes[name])
        self.ringernodes={}
        for name in self.wallpapernodes:
            self._tree.DeletePage(self.wallpapernodes[name])
        self.wallpapernodes={}
        self.OnInit()
        self.ringerwidget.OnRefresh()
        self.wallpaperwidget.OnRefresh()

    def SaveToDir(self, directory):
        if self.widget_to_save==None:
            self.SaveWidgetToDir(directory, self.ringerwidget)
            self.SaveWidgetToDir(directory, self.wallpaperwidget)
        else:
            self.SaveWidgetToDir(directory, self.widget_to_save, self.origin_to_save)

    def SaveWidgetToDir(self, directory, widget, filter=""):
        for k,e in widget.sections:
            # skip unrequested origins
            if filter!="" and filter!=k.label:
                continue
            opath=self._main_window._fixup(os.path.join(directory, k.label))
            try:
                os.makedirs(opath)
            except:
                pass
            if not os.path.isdir(opath):
                raise Exception("Unable to create export directory "+opath)
            for item in e:
                me=widget._data[item.datakey][item.key]
                if me.mediadata!=None and me.mediadata!='':
                    fpath=self._main_window._fixup(os.path.join(opath, me.name))
                    with file(fpath, "wb") as f:
                        f.write(me.mediadata)
                    if me.timestamp!=None:
                        os.utime(fpath, (me.timestamp, me.timestamp))


    def SaveToZip(self, zip_file):
        # create the zipfile in a buffer
        # and write to disk after it is all created
        op=cStringIO.StringIO()
        with contextlib.closing(zipfile.ZipFile(op, "w", zipfile.ZIP_DEFLATED)) as zip:
            if self.widget_to_save==None:
                self.SaveWidgetToZip(zip, self.ringerwidget)
                self.SaveWidgetToZip(zip, self.wallpaperwidget)
            else:
                self.SaveWidgetToZip(zip, self.widget_to_save, self.origin_to_save)
        open(zip_file, "wb").write(op.getvalue())

    def SaveWidgetToZip(self, zip, widget, filter=""):
        for k,e in widget.sections:
            # skip unrequested origins
            if filter!="" and filter!=k.label:
                continue
            for item in e:
                me=widget._data[item.datakey][item.key]
                if me.mediadata!=None and me.mediadata!='':
                    zi=zipfile.ZipInfo()
                    # zipfile does not like unicode. cp437 works on windows well, may be
                    # a better choice than ascii, but no phones currently support anything
                    # other than ascii for filenames
                    name=k.label+"/"+me.name
                    zi.filename=common.get_ascii_string(name, 'ignore')
                    if me.timestamp==None:
                        zi.date_time=(0,0,0,0,0,0)
                    else:
                        zi.date_time=time.localtime(me.timestamp)[:6]
                    zi.compress_type=zipfile.ZIP_DEFLATED
                    zip.writestr(zi, me.mediadata)

    def GetNodeList(self, widget):
        res=[]
        if widget==self.ringerwidget:
            for name in self.ringernodes:
                res.append(name)
        else:
           for name in self.wallpapernodes:
                res.append(name)
        res.sort()
        return res            

    def AddMediaNode(self, node_name, widget, icon=None):
        if widget==self.ringerwidget:
            if node_name not in self.ringernodes:
                if icon==None:
                    if string.find(node_name, "sound")!=-1:
                        icon=self._tree.sounds
                    else:
                        icon=self._tree.ringers    
                self.ringernodes[node_name]=self.AddSubPage(widget, node_name, icon)
        else:
            if node_name not in self.wallpapernodes:
                if icon==None:
                    if string.find(node_name, "video")!=-1:
                        icon=self._tree.video
                    elif string.find(node_name, "camera")!=-1:
                        icon=self._tree.camera    
                    else:
                        icon=self._tree.image    
                self.wallpapernodes[node_name]=self.AddSubPage(widget, node_name, icon)

    def GetNodeName(self, widget, node):
        if widget==self.ringerwidget:
            for name in self.ringernodes:
                if self.ringernodes[name]==node:
                    return name
        else:
            for name in self.wallpapernodes:
                if self.wallpapernodes[name]==node:
                    return name


#------------------------------------------------------------------------------
class ExportMediaToDirDialog(wx.DirDialog):
    def __init__(self, parent, title):
        super(ExportMediaToDirDialog, self).__init__(parent, message=title, style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        self.media_root=parent.GetActiveMediaWidget()

    def DoDialog(self):
        # do export
        rc=self.ShowModal()
        if rc==wx.ID_OK:
            self.media_root.SaveToDir(self.GetPath())

class ExportMediaToZipDialog(wx.FileDialog):
    def __init__(self, parent, title):
        self.media_root=parent.GetActiveMediaWidget()
        ext="Zip files (*.zip)|*.zip|All Files (*.*)|*"
        if self.media_root.widget_to_save!=None:
            default_file=self.media_root.origin_to_save+".zip"
            print "here 1 "+default_file
        else:
            default_file="media.zip"
            print "here 2 "+default_file
        super(ExportMediaToZipDialog, self).__init__(parent, title, defaultFile=default_file, wildcard=ext, style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)

    def DoDialog(self):
        # do export
        rc=self.ShowModal()
        if rc==wx.ID_OK:
            self.media_root.SaveToZip(self.GetPath())
