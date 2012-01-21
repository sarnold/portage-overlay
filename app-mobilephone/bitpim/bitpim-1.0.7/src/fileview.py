#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2003-2006 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: fileview.py 4732 2009-03-06 03:53:02Z hjelmn $


###
### File viewer
###
from __future__ import with_statement
import os
import copy
import cStringIO
import time
import base64
import phone_media_codec
import wx
import guihelper
import aggregatedisplay
import pubsub
import common
import widgets
import guiwidgets
import shutil
import database
import helpids
import tempfile


basename=common.basename
stripext=common.stripext
getext=common.getext


#-------------------------------------------------------------------------------
class MediaDataObject(database.basedataobject):
    # modified_datatime is unix time
    _knownproperties=['name', 'origin', 'index', 'timestamp']
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    _knownlistproperties.update( { 'mediadata': ['data'] })
    def __init__(self, data=None):
        if data is None or not isinstance(data, MediaEntry):
            return;
        self.update(data.get_db_dict())
mediaobjectfactory=database.dataobjectfactory(MediaDataObject)

#-------------------------------------------------------------------------------
class MediaEntry(object):
    _id_index=0
    _max_id_index=999
    def __init__(self):
        self._data={ 'serials': [] }
        self._create_id()

    def get(self):
        res=copy.deepcopy(self._data, None, {})
        # account for the medidadata field
        if res.has_key('mediadata'):
            if res['mediadata'] is not None:
                res['mediadata']=[{'data': buffer(res['mediadata']) }]
            else:
                del res['mediadata']
        return res
    def set(self, d):
        self._data={}
        self._data.update(d)
        # check for mediadata
        if d.get('mediadata', None) is not None:
            self._data['mediadata']=str(d['mediadata'][0]['data'])

    def get_db_dict(self):
        return self.get()
    def set_db_dict(self, d):
        self.set(d)

    def _create_id(self):
        "Create a BitPim serial for this entry"
        self._data.setdefault("serials", []).append(\
            {"sourcetype": "bitpim",
             "id": '%.3f%03d'%(time.time(), MediaEntry._id_index) })
        if MediaEntry._id_index<MediaEntry._max_id_index:
            MediaEntry._id_index+=1
        else:
            MediaEntry._id_index=0
    def _get_id(self):
        s=self._data.get('serials', [])
        for n in s:
            if n.get('sourcetype', None)=='bitpim':
                return n.get('id', None)
        return None
    def _set_id(self, id):
        s=self._data.get('serials', [])
        for n in s:
            if n.get('sourcetype', None)=='bitpim':
                n['id']=id
                return
        self._data['serials'].append({'sourcetype': 'bitpim', 'id': id } )
    id=property(fget=_get_id, fset=_set_id)

    def _set_or_del(self, key, v, v_list=[]):
        if v is None or v in v_list:
            if self._data.has_key(key):
                del self._data[key]
        else:
            self._data[key]=v

    def _get_origin(self):
        return self._data.get('origin', '')
    def _set_origin(self, v):
        if v is None:               
            if self._data.has_key('origin'):
                del self._data['origin']
                return
        if not isinstance(v, (str, unicode)):
            raise TypeError,'not a string or unicode type'
        self._data['origin']=v
    origin=property(fget=_get_origin, fset=_set_origin)

    def _get_mediadata(self):
        return self._data.get('mediadata', None)
    def _set_mediadata(self, v):
        if v is not None:
            self._set_or_del('mediadata', v, [])
    mediadata=property(fget=_get_mediadata, fset=_set_mediadata)

    def _get_name(self):
        return self._data.get('name', '')
    def _set_name(self, v):
        self._set_or_del('name', v, ('',))
    name=property(fget=_get_name, fset=_set_name)

    def _get_index(self):
        return self._data.get('index', -1)
    def _set_index(self, v):
        self._set_or_del('index', v, ('',))
    index=property(fget=_get_index, fset=_set_index)

    def _get_timestamp(self):
        return self._data.get('timestamp', None)
    def _set_timestamp(self, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise TypeError('timestamp property is an int arg')
            v=int(v)
        self._set_or_del('timestamp', v)
    timestamp=property(fget=_get_timestamp, fset=_set_timestamp)

def DrawTextWithLimit(dc, x, y, text, widthavailable, guardspace, term="..."):
    """Draws text and if it will overflow the width available, truncates and  puts ... at the end

    @param x: start position for text
    @param y: start position for text
    @param text: the string to draw
    @param widthavailable: the total amount of space available
    @param guardspace: if the text is longer than widthavailable then this amount of space is
             reclaimed from the right handside and term put there instead.  Consequently
             this value should be at least the width of term
    @param term: the string that is placed in the guardspace if it gets truncated.  Make sure guardspace
             is at least the width of this string!
    @returns: The extent of the text that was drawn in the end as a tuple of (width, height)
    """
    w,h=dc.GetTextExtent(text)
    if w<widthavailable:
        dc.DrawText(text,x,y)
        return w,h
    extents=dc.GetPartialTextExtents(text)
    limit=widthavailable-guardspace
    # find out how many chars in we have to go before hitting limit
    for i,offset in enumerate(extents):
        if offset>limit:
            break
    # back off 1 in case the new text's a tad long
    if i:
        i-=1
    text=text[:i]+term
    w,h=dc.GetTextExtent(text)
    assert w<=widthavailable
    dc.DrawText(text, x, y)
    return w,h

media_codec=phone_media_codec.codec_name
class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, target, drag_over=False, enter_leave=False):
        wx.FileDropTarget.__init__(self)
        self.target=target
        self.drag_over=drag_over
        self.enter_leave=enter_leave
        
    def OnDropFiles(self, x, y, filenames):
        return self.target.OnDropFiles(x,y,filenames)

    def OnDragOver(self, x, y, d):
        if self.drag_over:
            return self.target.OnDragOver(x,y,d)
        return wx.FileDropTarget.OnDragOver(self, x, y, d)

    def OnEnter(self, x, y, d):
        if self.enter_leave:
            return self.target.OnEnter(x,y,d)
        return wx.FileDropTarget.OnEnter(self, x, y, d)

    def OnLeave(self):
        if self.enter_leave:
            return self.target.OnLeave()
        return wx.FileDropTarget.OnLeave(self)

class FileView(wx.Panel, widgets.BitPimWidget):

    # Various DC objects used for drawing the items.  We have to calculate them in the constructor as
    # the app object hasn't been constructed when this file is imported.
    item_selection_brush=None
    item_selection_pen=None
    item_line_font=None
    item_term="..."
    item_guardspace=None
    # Files we should ignore
    skiplist= ( 'desktop.ini', 'thumbs.db', 'zbthumbnail.info' )
    database_key=""

    # how much data do we want in call to getdata
    NONE=0
    SELECTED=1
    ALL=2

    # maximum length of a filename
    maxlen=-1  # set via phone profile
    # acceptable characters in a filename
    filenamechars=None # set via phone profile
    # Default Help page, children can override
    helpid=helpids.ID_TAB_MEDIA

    def __init__(self, mainwindow, parent, media_root, watermark=None):
        wx.Panel.__init__(self,parent,style=wx.CLIP_CHILDREN)
        # adjust the DB to accommodate the new schema if necessary
        self._fixupdb(mainwindow.database)
        # item attributes
        if self.item_selection_brush is None:
            self.item_selection_brush=wx.TheBrushList.FindOrCreateBrush("MEDIUMPURPLE2", wx.SOLID)
            self.item_selection_pen=wx.ThePenList.FindOrCreatePen("MEDIUMPURPLE2", 1, wx.SOLID)
            f1=wx.TheFontList.FindOrCreateFont(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            f2=wx.TheFontList.FindOrCreateFont(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
            self.item_line_font=[f1, f2, f2, f2]
            dc=wx.MemoryDC()
            dc.SelectObject(wx.EmptyBitmap(100,100))
            self.item_guardspace=dc.GetTextExtent(self.item_term)[0]
            del dc

        # no redraw ickiness
        # wx.EVT_ERASE_BACKGROUND(self, lambda evt: None)
        
        self.parent=parent
        self.mainwindow=mainwindow
        self.thedir=None
        self.wildcard="I forgot to set wildcard in derived class|*"
        self.__dragging=False
        self._in_context_menu=False
        self.media_root=media_root
        self.show_thumbnail=True
        self.active_section=""
        # origins that should not be used for phonebook
        self.excluded_origins=()

        # use the aggregatedisplay to do the actual item display
        self.aggdisp=aggregatedisplay.Display(self, self, watermark) # we are our own datasource
        self.vbs=wx.BoxSizer(wx.VERTICAL)

        ### toolbar
        self.tb=wx.ToolBar(self, -1, style=wx.TB_3DBUTTONS|wx.TB_HORIZONTAL)
        self.tb.SetToolBitmapSize(wx.Size(18,18))
        sz=self.tb.GetToolBitmapSize()

        # list and thumbnail tools
        self.tb.AddRadioLabelTool(guihelper.ID_FILEVIEW_THUMBNAIL, "Thumbnail",
                                    wx.ArtProvider.GetBitmap(guihelper.ART_MEDIA_THUMB_VIEW, wx.ART_TOOLBAR, sz),
                                    wx.ArtProvider.GetBitmap(guihelper.ART_MEDIA_THUMB_VIEW, wx.ART_TOOLBAR, sz),
                                    "Show Thumbnails", "Show items as thumbnails")
        self.tb.AddRadioLabelTool(guihelper.ID_FILEVIEW_LIST, "List", 
                                    wx.ArtProvider.GetBitmap(guihelper.ART_MEDIA_LIST_VIEW, wx.ART_TOOLBAR, sz),
                                    wx.ArtProvider.GetBitmap(guihelper.ART_MEDIA_LIST_VIEW, wx.ART_TOOLBAR, sz),
                                    "Show List", "Show items in a list")
        self.vbs.Add(self.tb, 0, wx.EXPAND|wx.ALL, 1)
        self.aggr_sizer=self.vbs.Add(self.aggdisp, 1, wx.EXPAND|wx.ALL, 2)

        # main list
        column_info=self.GetColumnNames()
        self.item_list=guiwidgets.BitPimListCtrl(self, column_info)
        self.nodes={}
        self.nodes_keys={}
        self.item_list.ResetView(self.nodes, self.nodes_keys)
        self.item_sizer=self.vbs.Add(self.item_list, 1, wx.EXPAND|wx.ALL, 2)
        self.item_sizer.Show(False)
        self.note=self.vbs.Add(wx.StaticText(self, -1, '  Note: Click column headings to sort data'), 0, wx.ALIGN_CENTRE|wx.BOTTOM, 10)
        self.note.Show(False)
        self.SetSizer(self.vbs)
        timerid=wx.NewId()
        self.thetimer=wx.Timer(self, timerid)
        wx.EVT_TIMER(self, timerid, self.OnTooltipTimer)
        self.motionpos=None
        wx.EVT_MOUSE_EVENTS(self.aggdisp, self.OnMouseEvent)
        self.tipwindow=None
        if True: # guihelper.IsMSWindows() or guihelper.IsGtk():
            # turn on drag-and-drag for all platforms
            wx.EVT_MOTION(self.aggdisp, self.OnStartDrag)

        # Menus

        self.itemmenu=wx.Menu()
        self.itemmenu.Append(guihelper.ID_FV_OPEN, "Open")
        self.itemmenu.Append(guihelper.ID_FV_SAVE, "Save ...")
        self.itemmenu.AppendSeparator()
        if guihelper.IsMSWindows():
            self.itemmenu.Append(guihelper.ID_FV_COPY, "Copy")
        self.itemmenu.Append(guihelper.ID_FV_DELETE, "Delete")
        self.itemmenu.Append(guihelper.ID_FV_RENAME, "Rename")
        self.movemenu=wx.Menu()
        self.itemmenu.AppendMenu(guihelper.ID_FV_MOVE, "Move to", self.movemenu)
        self.itemmenu.AppendSeparator()
        self.itemmenu.Append(guihelper.ID_FV_REPLACE, "Replace")
        # self.itemmenu.Append(guihelper.ID_FV_RENAME, "Rename")
        self.itemmenu.Append(guihelper.ID_FV_REFRESH, "Refresh")

        self.bgmenu=wx.Menu()
        self.bgmenu.Append(guihelper.ID_FV_ADD, "Add ...")
        self.bgmenu.Append(guihelper.ID_FV_PASTE, "Paste")
        self.bgmenu.Append(guihelper.ID_FV_REFRESH, "Refresh")

        wx.EVT_MENU(self.tb, guihelper.ID_FILEVIEW_THUMBNAIL, self.OnThumbnailView)
        wx.EVT_MENU(self.tb, guihelper.ID_FILEVIEW_LIST, self.OnListView)


        wx.EVT_MENU(self.itemmenu, guihelper.ID_FV_OPEN, self.OnLaunch)
        wx.EVT_MENU(self.itemmenu, guihelper.ID_FV_SAVE, self.OnSave)
        if guihelper.IsMSWindows():
            wx.EVT_MENU(self.itemmenu, guihelper.ID_FV_COPY, self.OnCopy)
        wx.EVT_MENU(self.itemmenu, guihelper.ID_FV_DELETE, self.OnDelete)
        wx.EVT_MENU(self.itemmenu, guihelper.ID_FV_RENAME, self.OnRename)
        wx.EVT_MENU(self.itemmenu, guihelper.ID_FV_REPLACE, self.OnReplace)
        wx.EVT_MENU(self.itemmenu, guihelper.ID_FV_REFRESH, lambda evt: self.OnRefresh())
        wx.EVT_MENU(self.bgmenu, guihelper.ID_FV_ADD, self.OnAdd)
        wx.EVT_MENU(self.bgmenu, guihelper.ID_FV_PASTE, self.OnPaste)
        wx.EVT_MENU(self.bgmenu, guihelper.ID_FV_REFRESH, lambda evt: self.OnRefresh)

        wx.EVT_RIGHT_UP(self.aggdisp, self.OnRightClick)
        wx.EVT_LIST_ITEM_RIGHT_CLICK(self.item_list, self.item_list.GetId(), self.OnRightClick)
        aggregatedisplay.EVT_ACTIVATE(self.aggdisp, self.aggdisp.GetId(), self.OnLaunch)
        wx.EVT_LIST_ITEM_ACTIVATED(self.item_list, self.item_list.GetId(), self.OnLaunch)

        self.droptarget=MyFileDropTarget(self)
        self.SetDropTarget(self.droptarget)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_IDLE(self, self.OnIdle)
        wx.EVT_KEY_DOWN(self.aggdisp, self.OnKeyDown)
        wx.EVT_KEY_UP(self.aggdisp, self.OnKeyUp)
        self.tb.Realize()
        pubsub.subscribe(self.OnMediaInfo, pubsub.REQUEST_MEDIA_INFO)
        pubsub.subscribe(self.OnMediaOpen, pubsub.REQUEST_MEDIA_OPEN)

    def OnIdle(self, _):
        "Save out changed data"
        if self.modified:
            self.modified=False
            self._populatefs(self._data)
            self.OnListRequest() # broadcast changes

    def OnKeyDown(self, evt):
        if guihelper.IsGtk():
            if evt.GetKeyCode()==wx.WXK_SHIFT:
                self._shift_down=True
        else:
            self._shift_down=evt.ShiftDown()
        evt.Skip()

    def OnKeyUp(self, evt):
        if guihelper.IsGtk():
            if evt.GetKeyCode()==wx.WXK_SHIFT:
                self._shift_down=False
        else:
            self._shift_down=evt.ShiftDown()
        evt.Skip()

    def OnThumbnailView(self, _):
        self.thetimer.Stop()
        self.show_thumbnail=True
        self.item_sizer.Show(False)
        self.note.Show(False)
        self.aggr_sizer.Show(True)
        self.aggdisp.SetFocus()
        self.vbs.Layout()

    def OnListView(self, _):
        self.thetimer.Stop()
        self.show_thumbnail=False
        self.aggr_sizer.Show(False)
        # resize to hide the thumbnails otherwise it still gets the mouse scroll events.
        self.aggdisp.SetSize((1,1))
        self.item_sizer.Show(True)
        self.item_list.SetFocus()
        self.note.Show(True)
        self.vbs.Layout()

    def OnSelected(self, node):
        self.active_section=self.media_root.GetNodeName(self, node)
        self.aggdisp.SetActiveSection(self.active_section)
        self.MakeMoveMenu()
        self.OnRefreshList()

    def GetRightClickMenuItems(self, node):
        # we set these values so that the event hander knows only to save
        # this origin rather than all media, we clear these values after
        # the menu is dismissed (see OnRightClickMenuExit below)
        self.media_root.widget_to_save=self
        self.media_root.origin_to_save=self.active_section
        result=[]
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EDITADDENTRY, "Add to %s" % self.active_section, "Add a new media items"))
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EDITDELETEENTRY, "Delete Selected", "Delete Selected Items"))
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EDITSELECTALL, "Select All", "Select All Items"))
        if guihelper.IsMSWindows():
            result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EDITCOPY, "Copy", "Copy Selected Items"))
        result.append((widgets.BitPimWidget.MENU_SPACER, 0, "", ""))
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EXPORT_MEDIA_TO_DIR, "Export %s to Folder ..." % self.active_section, "Export the media to a folder on your hard drive"))
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EXPORT_MEDIA_TO_ZIP, "Export %s to Zip File ..." % self.active_section, "Export the media to a zip file"))
        return result

    def OnRightClickMenuExit(self):
        # clear these values now that the event has been processed
        self.media_root.widget_to_save=None
        self.media_root.origin_to_save=""

    def MakeMoveMenu(self):
        # redo the move menu
        menuItems = self.movemenu.GetMenuItems()
        for i, menuItem in enumerate(menuItems):
            self.Unbind(wx.EVT_MENU, id=menuItem.GetId())
            self.movemenu.DeleteItem(menuItem)

        # get the list of origins
        origins=self.media_root.GetNodeList(self)
        origins.remove(self.active_section)
        if len(origins):
            for origin in origins:
                mid=wx.NewId()
                self.movemenu.Append(mid, origin)
                wx.EVT_MENU(self, mid, self.OnMoveItem)

    def GetColumnNames(self):
        columns=[]
        columns.append(("Name", 120, False))
        columns.append(("Size/bytes", 80, True))
        columns.append(("Date Modified", 120, False))
        columns.append(("File Details", 380, False))
        return columns

    def OnSize(self, evt):
        # stop the tool tip from poping up when we're resizing!
        if self.thetimer.IsRunning():
            self.thetimer.Stop()
        evt.Skip()

    def OnRightClick(self, evt):
        """Popup the right click context menu

        @param widget:  which widget to popup in
        @param position:  position in widget
        @param onitem: True if the context menu is for an item
        """
        if len(self.GetSelectedItems()):
            menu=self.itemmenu
            item=self.GetSelectedItems()[0]
            single=len(self.GetSelectedItems())==1
            menu.Enable(guihelper.ID_FV_RENAME, single)
            # we always launch on mac
            if not guihelper.IsMac():
                menu.FindItemById(guihelper.ID_FV_OPEN).Enable(guihelper.GetOpenCommand(item.mimetypes, item.name) is not None)
        else:
            menu=self.bgmenu
            menu.Enable(guihelper.ID_FV_PASTE, self.CanPaste())
        if menu is None:
            return
        # we're putting up the context menu, quit the tool tip timer.
        self._in_context_menu=True
        self.aggdisp.PopupMenu(menu, evt.GetPosition())
        self._in_context_menu=False

    def OnMoveItem(self, evt):
        new_origin=None
        items=self.GetSelectedItems()
        new_origin=self.movemenu.FindItemById(evt.GetId()).GetLabel()
        for item in items:
            if new_origin!=None and new_origin in self.media_root.GetNodeList(self):
                # make sure this name is not already used
                for i in self._data[self.database_key]:
                    if self._data[self.database_key][i].origin==new_origin and \
                       self._data[self.database_key][i].name==item.name:
                        wx.MessageBox("A file with the same name already exists in %s!" % new_origin, "Move Error", wx.OK|wx.ICON_EXCLAMATION)
                        return
                wx.BeginBusyCursor()
                item.ChangeOriginInIndex(new_origin)
                self.OnRefresh()
                wx.EndBusyCursor()

    def _launch(self, item):
        # Open/Launch the specified item
        me=self._data[self.database_key][item.key]
        fname=self._gettempfile(me)
        if guihelper.IsMac():
            import findertools
            findertools.launch(fname)
            return
        cmd=guihelper.GetOpenCommand(item.mimetypes, fname)
        if cmd is None:
            wx.Bell()
        else:
            wx.Execute(cmd, wx.EXEC_ASYNC)

    @guihelper.BusyWrapper
    def OnLaunch(self, _):
        self._launch(self.GetSelectedItems()[0])

    if True: # guihelper.IsMSWindows() or guihelper.IsGtk():
        # drag-and-drop files should work on all platforms
        def OnStartDrag(self, evt):
            evt.Skip()
            if not evt.LeftIsDown():
                return
            items=self.GetSelectedItems()
            if not len(items):
                return
            drag_source=wx.DropSource(self)
            file_names=wx.FileDataObject()
            for item in items:
                me=self._data[self.database_key][item.key]
                fname=self._gettempfile(me)
                if not os.path.isfile(fname):
                    continue
                file_names.AddFile(fname)
            drag_source.SetData(file_names)
            self.__dragging=True
            res=drag_source.DoDragDrop(wx.Drag_AllowMove)
            self.__dragging=False
            # check of any of the files have been removed,
            # can't trust result returned by DoDragDrop
            for item in items:
                me=self._data[self.database_key][item.key]
                fname=self._gettempfile(me)
                if not os.path.isfile(fname):
                    item.RemoveFromIndex()

    def OnMouseEvent(self, evt):
        self.motionpos=evt.GetPosition()
        # on windows if we quickly move the mouse out of bitpim window we never get an event and we will pop up
        # the tooltip when we should not, so we check the position after the timeout and see if it has moved.
        self.abs_mouse_pos=wx.GetMousePosition()
        evt.Skip()
        self.thetimer.Stop()
        if evt.AltDown() or evt.MetaDown() or evt.ControlDown() or \
           evt.ShiftDown() or evt.Dragging() or evt.IsButton() or \
           self._in_context_menu or not self.show_thumbnail:
            return
        self.thetimer.Start(1750, wx.TIMER_ONE_SHOT)

    def OnTooltipTimer(self, _):
        if self._in_context_menu or not self.show_thumbnail or \
           wx.GetApp().critical.isSet():
            # we're putting up a context menu or main app is busy, forget this
            return
        # see if we have moved
        if self.abs_mouse_pos!=wx.GetMousePosition():
            return
        x,y=self.aggdisp.CalcUnscrolledPosition(*self.motionpos)
        res=self.aggdisp.HitTest(x,y)
        if res.item is not None:
            try:    self.tipwindow.Destroy()
            except: pass
            self.tipwindow=res.item.DisplayTooltip(self.aggdisp, res.itemrectscrolled)

    def OnRefresh(self):
        # update aggregate view
        self.aggdisp.UpdateItems()
        self.OnRefreshList()
        self.media_root.DoMediaSummary()

    def OnRefreshList(self):
        # update list view
        self.nodes={}
        self.nodes_keys={}
        index=0
        for k,e in self.sections:
            if self.active_section==None or k.label==self.active_section:
                for item in e:
                    # replace linefeeds in description
                    dlist=item.long.splitlines()
                    d=""
                    for l in dlist: 
                        if len(d):
                            d+=" - "
                        d+=l
                    self.nodes[index]=(item.name, str(item.size), item.timestamp, d)
                    self.nodes_keys[index]=item
                    index+=1
        self.item_list.ResetView(self.nodes, self.nodes_keys)

    def GetSelectedItems(self):
        if self.show_thumbnail:
            return [item for _,_,_,item in self.aggdisp.GetSelection()]
        res=[]
        sel=self.item_list.GetSelections()
        for sel_idx in sel:
            res.append(self.item_list.GetItemData(sel[sel_idx]))
        return res

    def GetAllItems(self):
        return [item for _,_,_,item in self.aggdisp.GetAllItems()]

    def CanSelectAll(self):
        return self.item_list.GetItemCount() > 0

    def OnSelectAll(self, _):
        self.aggdisp.SelectAll()
        self.item_list.SelectAll()

    def OnSave(self, _):
        # If one item is selected we ask for a filename to save.  If
        # multiple then we ask for a directory, and users don't get
        # the choice to affect the names of files.  Note that we don't
        # allow users to select a different format for the file - we
        # just copy it as is.
        items=self.GetSelectedItems()
        if len(items)==1:
            ext=getext(items[0].name)
            if ext=="": ext="*"
            else: ext="*."+ext
            with guihelper.WXDialogWrapper(wx.FileDialog(self, "Save item", wildcard=ext, defaultFile=items[0].name, style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR),
                                           True) as (dlg, retcode):
                if retcode==wx.ID_OK:
                    file(dlg.GetPath(), "wb").write(self._data[items[0].datakey][items[0].key].mediadata)
                    if self._data[items[0].datakey][items[0].key].timestamp!=None:
                        os.utime(dlg.GetPath(), (self._data[items[0].datakey][items[0].key].timestamp, 
                                                 self._data[items[0].datakey][items[0].key].timestamp))
        else:
            with guihelper.WXDialogWrapper(wx.DirDialog(self, "Save items to", style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON),
                                           True) as (dlg, retcode):
                if retcode==wx.ID_OK:
                    for item in items:
                        fname=item.name.encode(media_codec)
                        fname=os.path.join(dlg.GetPath(), basename(fname))
                        file(fname, 'wb').write(self._data[item.datakey][item.key].mediadata)
                        if self._data[item.datakey][item.key].timestamp!=None:
                            os.utime(fname, (self._data[item.datakey][item.key].timestamp, 
                                             self._data[item.datakey][item.key].timestamp))

    if guihelper.IsMSWindows():
        def OnCopy(self, _):
            items=self.GetSelectedItems()
            if not len(items):
                # nothing selected
                return
            file_names=wx.FileDataObject()
            for item in items:
                me=self._data[self.database_key][item.key]
                fname=self._gettempfile(me)
                if not os.path.isfile(fname):
                    continue
                file_names.AddFile(fname)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(file_names)
                wx.TheClipboard.Close()
        def CanCopy(self):
            return len(self.GetSelectedItems())

    if guihelper.IsGtk():
        # Gtk just pastes the file names as text onto the Clipboard
        def OnPaste(self, _=None):
            if not wx.TheClipboard.Open():
                # can't access the clipboard
                return
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_UNICODETEXT)):
                file_names=wx.TextDataObject()
                has_data=wx.TheClipboard.GetData(file_names)
            else:
                has_data=False
            wx.TheClipboard.Close()
            if has_data:
                # collect file names if any.
                _names=[x for x in file_names.GetText().split('\n') \
                        if os.path.isfile(x) ]
                if _names:
                    self.OnAddFiles(_names)
        def CanPaste(self):
            """ Return True if can accept clipboard data, False otherwise
            """
            if not wx.TheClipboard.Open():
                return False
            r=wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_UNICODETEXT))
            if r:
                file_names=wx.TextDataObject()
                r=wx.TheClipboard.GetData(file_names)
                if r:
                    for _name in file_names.GetText().split('\n'):
                        if not os.path.isfile(_name):
                            r=False
                            break
            wx.TheClipboard.Close()
            return r
    else:
        def OnPaste(self, _=None):
            if not wx.TheClipboard.Open():
                # can't access the clipboard
                return
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_FILENAME)):
                file_names=wx.FileDataObject()
                has_data=wx.TheClipboard.GetData(file_names)
            else:
                has_data=False
            wx.TheClipboard.Close()
            if has_data:
                self.OnAddFiles(file_names.GetFilenames())

        def CanPaste(self):
            """ Return True if can accept clipboard data, False otherwise
            """
            if not wx.TheClipboard.Open():
                return False
            r=wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_FILENAME))
            wx.TheClipboard.Close()
            return r

    def CanDelete(self):
        if len(self.GetSelectedItems()):
            return True
        return False        

    def OnDelete(self,_):
        items=self.GetSelectedItems()
        for item in items:
            item.RemoveFromIndex()
        self.OnRefresh()

    def AddToIndex(self, file, origin, data, dict, timestamp=None, index=-1):
        # see if it is already in the origin
        if dict.has_key(self.database_key):
            for i in dict[self.database_key]:
                # see if the media is already in the database
                # if so update the existing entry, the display objects have references to the keys, if
                # we delete items the keys go bad and we require a refresh
                if dict[self.database_key][i].name==file and dict[self.database_key][i].origin==origin:
                    # update the index
                    if index>=0:
                        dict[self.database_key][i].index=index 
                    # update the timestamp
                    if timestamp!=None:
                        dict[self.database_key][i].timestamp=timestamp 
                    # if there is no data dont update the dict
                    # when indexes are updates the data is not provided
                    if data!=None and data!='':
                        dict[self.database_key][i].mediadata=data
                    return
        else:
            dict[self.database_key]={}
        entry=MediaEntry()
        entry.name=file
        entry.origin=origin
        entry.mediadata=data
        entry.index=index
        entry.timestamp=timestamp
        dict[self.database_key][entry.id]=entry
        self.modified=True

    def _fixupdb(self, db):
        # fixup the database to accommodate the new schema
        adjustflg=False
        for _,_name,_type in db.getcolumns(self.database_key):
            if _name=='mediadata' and _type!='indirectBLOB':
                # old schema, need to adjust
                adjustflg=True
                break
        # adjust the table: replace the mediadata field
        if adjustflg:
            db._altertable(self.database_key, [('mediadata', 'indirectBLOB')],
                           ['mediadata'], 1)

    def _gettempfile(self, item):
        # store the the media data in a temporary file and return the full file
        # path
        filename=os.path.join(tempfile.gettempdir(),
                              item.name.encode(media_codec))
        file(filename, 'wb').write(item.mediadata)
        return filename

    def _filename(self, item):
        # return the filename associated with a media file
        if hasattr(item, 'origin'):
            _origin=item.origin
            _name=item.name
        else:
            _origin=item.get('origin', '')
            _name=item.get('name', '')
        relative_name=os.path.join(_origin,
                                   _name.encode(media_codec))
        return os.path.join(self.mainwindow.blob_path, relative_name)

    def _save_to_db(self, dict):
        db_rr={}
        for k,e in dict.items():
            db_rr[k]=MediaDataObject(e)
            # the media data does not go into the actual database, we store it 
            # in a regular file to minimise the database size, it 
            # gets very big if the data is stored in it and starts to get slow.
        database.ensurerecordtype(db_rr, mediaobjectfactory)
        self.mainwindow.database.savemajordict(self.database_key, db_rr)

    def _load_from_db(self, result):
        dict=self.mainwindow.database.\
                   getmajordictvalues(self.database_key,
                                      mediaobjectfactory)
        r={}
        for k,e in dict.items():
            ce=MediaEntry()
            ce.set_db_dict(e)
            if ce.mediadata is None:
                # try reading the data from the "old" way
                try:
                    ce.mediadata=file(self._filename(ce), 'rb').read()
                except:
                    # abandon data that has no file it probably means that 
                    # blobs directory is corrupted, maybe the user deleted
                    # the file themselves
                    pass
            r[ce.id]=ce
        result.update({ self.database_key: r})
        return result

    def convert_to_dict(self, result, res=None):
        if res==None:
            res={}
        for rec in result[self.database_key]:
            fname=result[self.database_key][rec]['name']
            # legacy format does not always contain origin
            if result[self.database_key][rec].has_key('origin'):
                origin=result[self.database_key][rec]['origin']
            else:
                origin=self.default_origin
            data, timestamp=self.get_media_data(result, fname, origin)
            # None and '' are treated differently by viewer. data=='' means we could not read from 
            # the phone but we still want to display, 
            # None means we do not want to display like the builtin media
            if data=='': # no data read, see if we have this file in the dict already and use its data, 
                         # provides a workaround for phones that don't let us read the ringtones back 
                         # which we wrote in the first place
                for i in self._data[self.database_key]:
                    if self._data[self.database_key][i].name==result[self.database_key][rec]['name'] \
                             and self._data[self.database_key][i].origin==result[self.database_key][rec]['origin'] \
                             and self._data[self.database_key][i].mediadata!=None:
                        data=self._data[self.database_key][i].mediadata
            self.AddToIndex(result[self.database_key][rec]['name'], origin, data, res, timestamp, rec)
        return res

    def get_media_data(self, result, name, origin):
        data=None
        timestamp=None # unix time
        if result.has_key(self.media_key):
            if result[self.media_key].has_key("new_media_version"):
                if result[self.media_key].has_key(origin):
                    if result[self.media_key][origin].has_key(name):
                        data=result[self.media_key][origin][name]['data']
                        if result[self.media_key][origin][name].has_key('timestamp'):
                            timestamp=result[self.media_key][origin][name]['timestamp']
                pass
            # old style data with no origin info, means that the filenames have
            # to be unique across all the origins for the widget
            elif result[self.media_key].has_key(name):
                data=result[self.media_key][name]
        return data, timestamp

    def updateindex(self, index):
        self._data=self.convert_to_dict(index, self._data)
        # delete unused medias
        del_list=[]
        for i in self._data[self.database_key]:
            found=False
            for rec in index[self.database_key]:
                if self._data[self.database_key][i].name==index[self.database_key][rec]['name'] \
                         and self._data[self.database_key][i].origin==index[self.database_key][rec]['origin']:
                    found=True
                    break
            if not found:
                del_list.append(i)
        for i in del_list:
            del self._data[self.database_key][i]
        self.modified=True

    def populatefs(self, dict):
        res={}
        dict=self.convert_to_dict(dict)
        return self._populatefs(dict)

    def _populatefs(self, dict):
        self._save_to_db(dict.get(self.database_key, {}))
        return dict

    def populate(self, dict):
        if not dict.has_key('media_from_db'):
            # update the existing dict (the key are referenced from the display objects, doing a refresh causes
            # a long delay
            self._data=self.convert_to_dict(dict, self._data)
            # delete unused medias
            del_list=[]
            for i in self._data[self.database_key]:
                found=False
                for rec in dict[self.database_key]:
                    if self._data[self.database_key][i].name==dict[self.database_key][rec]['name'] \
                             and self._data[self.database_key][i].origin==dict[self.database_key][rec]['origin']:
                        found=True
                        break
                if not found:
                    del_list.append(i)
            for i in del_list:
                del self._data[self.database_key][i]

            self.modified=True
            self.OnRefresh()
        else:
            if dict[self.database_key]!=self._data[self.database_key]:
                self._data[self.database_key]=dict[self.database_key].copy()
                self.modified=True
                self.OnRefresh()
                    
    def getfromfs(self, result):
        if self.mainwindow.database.doestableexist(self.database_key):
            result=self._load_from_db(result)
        else: # if there is no data in the database then try to read the legacy media
            res={}
            res=self.legacygetfromfs(res, self.media_key, self.database_key, self.CURRENTFILEVERSION) 
            # if we got anything save into the database and delete the old index file
            if res.has_key(self.database_key) and len(res[self.database_key])!=0:
                result.update(self.convert_to_dict(res))
                self._populatefs(result)
                self.delete_old_media()
            else:
                result=self._load_from_db(result)
        result['media_from_db']=1
        return result

    def legacygetfromfs(self, result, key, indexkey, currentversion):
        dict={}
        index_found=False
        if os.path.isdir(self.thedir):
            for file in os.listdir(self.thedir):
                if file=='index.idx':
                    d={}
                    d['result']={}
                    common.readversionedindexfile(os.path.join(self.thedir, file), d, self.versionupgrade, currentversion)
                    result.update(d['result'])
                    index_found=True
                elif file.lower() in self.skiplist:
                    # ignore windows detritus
                    continue
                elif key is not None:
                    dict[file.decode(media_codec)]=open(os.path.join(self.thedir, file), "rb").read()
        if index_found:
            if key is not None:
                result[key]=dict
            if indexkey not in result:
                result[indexkey]={}
        return result

    def delete_old_media(self):
        # No longer do this since it messes up the virtual tables setup!
        pass

    def OnDropFiles(self, _, dummy, filenames):
        # There is a bug in that the most recently created tab
        # in the notebook that accepts filedrop receives these
        # files, not the most visible one.  We find the currently
        # viewed tab in the notebook and send the files there
        if self.__dragging:
            # I'm the drag source, forget 'bout it !
            return
        target=self # fallback
        t=self._tree.mw.GetCurrentActiveWidget()
        if isinstance(t, FileView):
            # changing target in dragndrop
            target=t
        target.OnAddFiles(filenames)

    def CanAdd(self):
        return True

    def OnAdd(self, _=None):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, "Choose files", style=wx.OPEN|wx.MULTIPLE, wildcard=self.wildcard),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.OnAddFiles(dlg.GetPaths())

    def CanRename(self):
        return len(self.GetSelectedItems())==1
    # subclass needs to define this
    media_notification_type=None
    def OnRename(self, _=None):
        items=self.GetSelectedItems()
        if len(items)!=1:
               # either none or more than 1 items selected
               return
        old_name=items[0].name
        with guihelper.WXDialogWrapper(wx.TextEntryDialog(self, "Enter a new name:", "Item Rename",
                                                          old_name),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                new_name=dlg.GetValue()
                if len(new_name) and new_name!=old_name:
                    items[0].name=new_name
                    items[0].RenameInIndex(new_name)
                    pubsub.publish(pubsub.MEDIA_NAME_CHANGED,
                                   data={ pubsub.media_change_type: self.media_notification_type,
                                          pubsub.media_old_name: old_name,
                                          pubsub.media_new_name: new_name })
          
    def OnAddFiles(self,_):
        raise NotImplementedError

    def OnReplace(self, _=None):
        items=self.GetSelectedItems()
        if len(items)!=1:
               # either none or more than 1 items selected
               return
        with guihelper.WXDialogWrapper(wx.FileDialog(self, "Choose file",
                                                     style=wx.OPEN, wildcard=self.wildcard),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.ReplaceContents(items[0].name, items[0].origin, dlg.GetPath())
                items[0].Refresh()

    def get_media_name_from_filename(self, filename, newext=''):
        path,filename=os.path.split(filename)
        # degrade to ascii
        degraded_fname=common.encode_with_degrade(filename, 'ascii', 'ignore')
        # decode with media codec in case it contains escape characters
        degraded_fname=degraded_fname.decode(media_codec)
        if not 'A' in self.filenamechars:
            degraded_fname=degraded_fname.lower()
        if not 'a' in self.filenamechars:
            degraded_fname=degraded_fname.upper()
        if len(newext):
            degraded_fname=stripext(degraded_fname)
        media_name="".join([x for x in degraded_fname if x in self.filenamechars])
        media_name=media_name.replace("  "," ").replace("  ", " ")  # remove double spaces
        media_name=media_name.replace(".m4a",".mp4") # change file extension of mpeg4 files
        if len(newext):
            media_name+='.'+newext
        if len(media_name)>self.maxlen:
            chop=len(media_name)-self.maxlen
            media_name=stripext(media_name)[:-chop].strip()+'.'+getext(media_name)
        return media_name

    def getdata(self,dict,want=NONE):
        items=None
        media_index={}
        media_data={}
        old_dict={}
        data_key=0

        if want==self.SELECTED:
            items=self.GetSelectedItems()
            if len(items)==0:
                want=self.ALL

        if want==self.SELECTED:
            if items is not None:
                media_data={}
                i=0
                for item in items:
                    me=self._data[item.datakey][item.key]
                    if me.mediadata!=None:
                        media_data[data_key]={'name': me.name, 'data': me.mediadata, 'origin': me.origin}
                        data_key+=1

        # convert into the old format
        index_cnt=-1
        for i in self._data[self.database_key]:
            me=self._data[self.database_key][i]
            # make sure the index is unique
            if me.index in media_index:
                while index_cnt in media_index:
                    index_cnt-=1
                index=index_cnt
            else:
                index=me.index
            media_index[index]={'name': me.name, 'origin': me.origin} 
            if want==self.ALL and me.mediadata!=None:
                media_data[data_key]={'name': me.name, 'data': me.mediadata, 'origin': me.origin}
                data_key+=1
        old_dict[self.database_key]=media_index
        dict.update(old_dict)
        dict[self.media_key]=media_data
        return dict

    def CompareItems(self, a, b):
        s1=a.name.lower()
        s2=b.name.lower()
        if s1<s2:
            return -1
        if s1==s2:
            return 0
        return 1

    def log(self, log_str):
        self.mainwindow.log(log_str)

    def GetHelpID(self):
        return self.helpid

    def OnMediaInfo(self, msg):
        # return the list of strings (lines) describing this item
        client, name, origin=msg.data
        for _item in self.GetAllItems():
            if (origin is None or _item.origin==origin) and \
               _item.name==name:
                    pubsub.publish(pubsub.RESPONSE_MEDIA_INFO,
                                   { 'client': client,
                                     'canopen': bool(guihelper.GetOpenCommand(_item.mimetypes, _item.name)),
                                     'desc': _item.lines })
    def OnMediaOpen(self, msg):
        # Launch the specified item name
        name, origin=msg.data
        for _item in self.GetAllItems():
            if (origin is None or _item.origin==origin) and \
               _item.name==name:
                return self._launch(_item)

class FileViewDisplayItem(object):

    datakey="Someone forgot to set me"
    PADDING=3

    def __init__(self, view, key):
        self.view=view
        self.key=key
        self.thumbsize=10,10
        self.setvals()
        self.lastw=None

    def setvals(self):
        me=self.view._data[self.datakey][self.key]
        self.name=me.name
        self.origin=me.origin
        self.mimetypes=''
        self.short=''
        self.long=''
        self.timestamp=''
        self.thumb=None
        if me.mediadata!=None:
            self.size=len(me.mediadata)
            self.no_data=False
            if me.timestamp!=None and me.timestamp!=0:
                try:
                    self.timestamp=time.strftime("%x %X", time.localtime(me.timestamp))
                except: # unexplained errors sometimes, so skip timestamp if this fails
                    self.timestamp=''
            fileinfo=self.view.GetFileInfoString(me.mediadata)
            if fileinfo!=None:
                self.short=fileinfo.shortdescription()
                self.long=fileinfo.longdescription()
                self.mimetypes=fileinfo.mimetypes
                self.fileinfo=fileinfo
        else:
            self.size=0
            self.no_data=True
        self.selbbox=None
        self.lines=[self.name, self.short,
                    '%.1f kb' % (self.size/1024.0,)]

    def Draw(self, dc, width, height, selected):
        if self.thumb==None:
            try:
                if self.size:
                    me=self.view._data[self.datakey][self.key]
                    self.thumb=self.view.GetItemThumbnail(me.mediadata, self.thumbnailsize[0], self.thumbnailsize[1], self.fileinfo)
                else:
                    self.thumb=self.view.GetItemThumbnail(None, self.thumbnailsize[0], self.thumbnailsize[1])
            except:
                self.thumb=self.view.GetItemThumbnail(None, self.thumbnailsize[0], self.thumbnailsize[1])
        redrawbbox=False
        if selected:
            if self.lastw!=width or self.selbbox is None:
                redrawbbox=True
            else:
                oldb=dc.GetBrush()
                oldp=dc.GetPen()
                dc.SetBrush(self.view.item_selection_brush)
                dc.SetPen(self.view.item_selection_pen)
                dc.DrawRectangle(*self.selbbox)
                dc.SetBrush(oldb)
                dc.SetPen(oldp)
        dc.DrawBitmap(self.thumb, self.PADDING+self.thumbnailsize[0]/2-self.thumb.GetWidth()/2, self.PADDING, True)
        xoff=self.PADDING+self.thumbnailsize[0]+self.PADDING
        yoff=self.PADDING*2
        widthavailable=width-xoff-self.PADDING
        maxw=0
        old=dc.GetFont()
        for i,line in enumerate(self.lines):
            dc.SetFont(self.view.item_line_font[i])
            w,h=DrawTextWithLimit(dc, xoff, yoff, line, widthavailable, self.view.item_guardspace, self.view.item_term)
            maxw=max(maxw,w)
            yoff+=h
        dc.SetFont(old)
        self.lastw=width
        self.selbbox=(0,0,xoff+maxw+self.PADDING,max(yoff+self.PADDING,self.thumb.GetHeight()+self.PADDING*2))
        if redrawbbox:
            return self.Draw(dc, width, height, selected)
        return self.selbbox

    def DisplayTooltip(self, parent, rect):
        res=["Name: "+self.name, "Origin: "+(self.origin, "default")[self.origin is None],
             'File size: %.1f kb (%d bytes)' % (self.size/1024.0, self.size), "\n"+self.datatype+" information:\n", self.long]
        # tipwindow takes screen coordinates so we have to transform
        x,y=parent.ClientToScreen(rect[0:2])
        return wx.TipWindow(parent, "\n".join(res), 1024, wx.Rect(x,y,rect[2], rect[3]))

    def RemoveFromIndex(self):
        del self.view._data[self.datakey][self.key]
        self.view.modified=True
        self.view.OnRefresh()

    def RenameInIndex(self, new_name):
        self.view._data[self.datakey][self.key].name=new_name
        self.view.modified=True
        self.view.OnRefresh()

    def ChangeOriginInIndex(self, new_origin):
        self.view._data[self.datakey][self.key].origin=new_origin
        self.view._data[self.datakey][self.key].index=-1
        self.view.modified=True
        self.view.OnRefresh()

    def Refresh(self):
        self.setvals()
        self.view.modified=True
        self.view.OnRefresh()
