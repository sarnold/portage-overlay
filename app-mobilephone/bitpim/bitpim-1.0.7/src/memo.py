### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@netzero.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: memo.py 4714 2008-10-21 01:50:47Z djpham $

"""
Code to handle memo/note items

The format for the memo is standardized.  It is a dict with the following
fields:

MemoEntry properties:
subject - 'string subject'
text - 'string text'
categories - [{ 'category': 'string' }]
secret - True/<False|None>
date - date time/stamp 'Mmm dd, YYYY HH:MM' (Read only)
id - unique id string that can be used as a dict key.

MemoEntry methods:
get() - return a copy of the memo dict.
set(dict) - set the internal dict to the new dict.
set_date_now() - set the date/time stamp to the current date/time
set_date_isostr(iso_string) - set the date/time stamp to the ISO date string
                              (YYYYMMDDTHHMMSS)

To implement memo read/write for a phone module:
 Add 2 entries into Profile._supportedsyncs:
        ...
        ('memo', 'read', None),     # all memo reading
        ('memo', 'write', 'OVERWRITE')  # all memo writing

implement the following 2 methods in your Phone class:
    def getmemo(self, result):
        ...
        return result

    def savememo(self, result, merge):
        ...
        return result

The result dict key is 'memo'.
"""

# standard modules
from __future__ import with_statement
import copy
import datetime
import time

# wx modules
import wx

# BitPim modules
import bptime
import calendarentryeditor as cal_editor
import database
import field_color
import helpids
import phonebookentryeditor as pb_editor
import pubsub
import today
import guihelper
import guiwidgets
import widgets

widgets_list=[]
module_debug=False

#-------------------------------------------------------------------------------
class MemoDataObject(database.basedataobject):
    _knownproperties=['subject', 'date']
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    _knownlistproperties.update( {'categories': ['category'],
                                  'flags': ['secret'],
                                  'body': ['type', 'data', '*' ] })

    def __init__(self, data=None):
        if data is None or not isinstance(data, MemoEntry):
            return;
        self.update(data.get_db_dict())
memoobjectfactory=database.dataobjectfactory(MemoDataObject)

#-------------------------------------------------------------------------------
class MemoEntry(object):
    _body_subject_len=12   # the # of chars from body to fill in for subj + ...
    _id_index=0
    _max_id_index=999
    def __init__(self):
        self._data={ 'body': [], 'serials': [] }
        self.set_date_now()
        self._create_id()

    def get(self):
        return copy.deepcopy(self._data, {})
    def set(self, d):
        self._data={}
        self._data.update(d)

    def get_db_dict(self):
        return self.get()
    def set_db_dict(self, d):
        self.set(d)

    def _set_or_del(self, key, v, v_list=()):
        if v is None or v in v_list:
            if self._data.has_key(key):
                del self._data[key]
        else:
            self._data[key]=v

    def _get_subject(self):
        return self._data.get('subject', '')
    def _set_subject(self, v):
        self._set_or_del('subject', v, ('',))
    subject=property(fget=_get_subject, fset=_set_subject)

    def _get_text(self):
        b=self._data.get('body', [])
        for n in b:
            if n.get('type', None)=='text':
                return n.get('data', '')
        return ''
    def _set_text(self, v):
        if v is None:
            v=''
        if not self.subject:
            self.subject=v[:self._body_subject_len]+'...'
        b=self._data.get('body', [])
        for n in b:
            if n.get('type', None)=='text':
                n['data']=v
                return
        self._data.setdefault('body', []).append(\
            {'type': 'text', 'data': v })
    text=property(fget=_get_text, fset=_set_text)

    def _get_secret(self):
        f=self._data.get('flags', [])
        for n in f:
            if n.has_key('secret'):
                return n['secret']
        return False
    def _set_secret(self, v):
        f=self._data.get('flags', [])
        for i, n in enumerate(f):
            if n.has_key('secret'):
                if v is None or not v:
                    del f[i]
                    if not self._data['flags']:
                        del self._data['flags']
                else:
                    n['secret']=v
                return
        if v is not None and v:
            self._data.setdefault('flags', []).append({'secret': v})
    secret=property(fget=_get_secret, fset=_set_secret)
    
    def _get_categories(self):
        return self._data.get('categories', [])
    def _set_categories(self, v):
        self._set_or_del('categories', v, ([],))
    categories=property(fget=_get_categories, fset=_set_categories)

    def set_date_now(self):
        # set the date/time stamp to now
        n=datetime.datetime.now()
        self._data['date']=n.strftime('%b %d, %Y %H:%M')
    def set_date_isostr(self, iso_string):
        n=bptime.BPTime(iso_string)
        self._data['date']=n.date.strftime('%b %d, %Y')+n.time.strftime(' %H:%M')
    def _get_date(self):
        return self._data.get('date', '')
    date=property(fget=_get_date)

    def _create_id(self):
        "Create a BitPim serial for this entry"
        self._data.setdefault("serials", []).append(\
            {"sourcetype": "bitpim",
             "id": '%.3f%03d'%(time.time(), MemoEntry._id_index) })
        if MemoEntry._id_index<MemoEntry._max_id_index:
            MemoEntry._id_index+=1
        else:
            MemoEntry._id_index=0
    def _get_id(self):
        s=self._data.get('serials', [])
        for n in s:
            if n.get('sourcetype', None)=='bitpim':
                return n.get('id', None)
        return None
    id=property(fget=_get_id)

#-------------------------------------------------------------------------------
class GeneralEditor(pb_editor.DirtyUIBase):
    _dict_key_index=0
    _label_index=1
    _class_index=2
    _get_index=3
    _set_index=4
    _w_index=5
    def __init__(self, parent, _=None):
        global widgets_list

        pb_editor.DirtyUIBase.__init__(self, parent)
        self._fields=[
            ['subject', 'Subject:', cal_editor.DVTextControl, None, None, None],
            ['date', 'Date:', wx.StaticText, self._get_date_str, self._set_date_str, None],
            ['secret', 'Private:', wx.CheckBox, None, None, None]
            ]
        gs=wx.FlexGridSizer(-1, 2, 5, 5)
        gs.AddGrowableCol(1)
        for n in self._fields:
            _txt=wx.StaticText(self, -1, n[self._label_index],
                               style=wx.ALIGN_LEFT)
            widgets_list.append((_txt, n[0]))
            gs.Add(_txt, 0, wx.EXPAND|wx.BOTTOM, 5)
            w=n[self._class_index](self, -1)
            gs.Add(w, 0, wx.EXPAND|wx.BOTTOM, 5)
            n[self._w_index]=w
        # event handlers
        wx.EVT_CHECKBOX(self, self._fields[2][self._w_index].GetId(),
                        self.OnMakeDirty)
        # all done
        self.SetSizer(gs)
        self.SetAutoLayout(True)
        gs.Fit(self)

    def _set_date_str(self, w, data):
        w.SetLabel(getattr(data, 'date'))
    def _get_date_str(self, w, _):
        pass
    def OnMakeDirty(self, evt):
        self.OnDirtyUI(evt)

    def Set(self, data):
        self.ignore_dirty=True
        if data is None:
            for n in self._fields:
                n[self._w_index].Enable(False)
        else:
            for n in self._fields:
                w=n[self._w_index]
                w.Enable(True)
                if n[self._set_index] is None:
                    w.SetValue(getattr(data, n[self._dict_key_index]))
                else:
                    n[self._set_index](w, data)
        self.ignore_dirty=self.dirty=False

    def Get(self, data):
        self.ignore_dirty=self.dirty=False
        if data is None:
            return
        for n in self._fields:
            w=n[self._w_index]
            if n[self._get_index] is None:
                v=w.GetValue()
            else:
                v=n[self._get_index](w, None)
            if v is not None:
                setattr(data, n[self._dict_key_index], v)

#-------------------------------------------------------------------------------
class MemoWidget(wx.Panel, widgets.BitPimWidget):
    color_field_name='memo'

    def __init__(self, mainwindow, parent):
        wx.Panel.__init__(self, parent, -1)
        self._main_window=mainwindow
        self._data={}
        self._data_map={}
        # main box sizer
        vbs=wx.BoxSizer(wx.VERTICAL)
        # horizontal sizer for the listbox and tabs
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        # the list box
        self._item_list=wx.ListBox(self, wx.NewId(),
                                    style=wx.LB_SINGLE|wx.LB_HSCROLL|wx.LB_NEEDED_SB)
        hbs.Add(self._item_list, 1, wx.EXPAND|wx.BOTTOM, border=5)
        # the detailed info pane
        vbs1=wx.BoxSizer(wx.VERTICAL)
        self._items=(
            (GeneralEditor, 0, None),
            (cal_editor.CategoryEditor, 1, 'category'),
            (pb_editor.MemoEditor, 1, 'memo')
            )
        self._w=[]
        for n in self._items:
            w=n[0](self, -1)
            vbs1.Add(w, n[1], wx.EXPAND|wx.ALL, 5)
            self._w.append(w)
            if n[2]:
                widgets_list.append((w.static_box, n[2]))
        hbs.Add(vbs1, 3, wx.EXPAND|wx.ALL, border=5)
        self._general_editor_w=self._w[0]
        self._cat_editor_w=self._w[1]
        self._memo_editor_w=self._w[2]
        # the bottom buttons
        hbs1=wx.BoxSizer(wx.HORIZONTAL)
        self._save_btn=wx.Button(self, wx.ID_SAVE)
        self._revert_btn=wx.Button(self, wx.ID_REVERT_TO_SAVED)
        help_btn=wx.Button(self, wx.ID_HELP)
        hbs1.Add(self._save_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs1.Add(help_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs1.Add(self._revert_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        # all done
        vbs.Add(hbs, 1, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        vbs.Add(hbs1, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)
        # event handlers
        wx.EVT_LISTBOX(self, self._item_list.GetId(), self._OnListBoxItem)
        wx.EVT_BUTTON(self, self._save_btn.GetId(), self._OnSave)
        wx.EVT_BUTTON(self, self._revert_btn.GetId(), self._OnRevert)
        wx.EVT_BUTTON(self, wx.ID_HELP,
                      lambda _: wx.GetApp().displayhelpid(helpids.ID_TAB_MEMO))
        # DIRTY UI Event handlers
        for w in self._w:
            pb_editor.EVT_DIRTY_UI(self, w.GetId(), self.OnMakeDirty)
        # populate data
        self._populate()
        # turn on dirty flag
        self.ignoredirty=False
        self.setdirty(False)
        # register for Today selection
        today.bind_notification_event(self.OnTodaySelection,
                                      today.Today_Group_Memo)
        # color code editable labels
        field_color.reload_color_info(self, widgets_list)
        pubsub.subscribe(self.OnPhoneChanged, pubsub.PHONE_MODEL_CHANGED)

    def OnPhoneChanged(self, _):
        # just reload the color info based on the new phone
        field_color.reload_color_info(self, widgets_list)
        self.Refresh()

    def _send_today_data(self):
        keys=self._data.keys()
        keys.sort()
        keys.reverse()
        today_event=today.TodayMemoEvent()
        for k in keys:
            today_event.append(self._data[k].subject,
                               { 'key': k, 'index': self._data_map[k] })
        today_event.broadcast()

    def OnTodaySelection(self, evt):
        self.ActivateSelf()
        if evt.data:
            self._item_list.SetSelection(evt.data.get('index', wx.NOT_FOUND))
            self._populate_each(evt.data.get('key', None))

    def _clear(self):
        self._item_list.Clear()
        self._clear_each()

    def _clear_each(self):
        for w in self._w:
            w.Set(None)
            w.Enable(False)
        self.Refresh()

    def _populate(self):
        # populate new data
        self._clear()
        self._data_map={}
        # populate the list with data
        keys=self._data.keys()
        keys.sort()
        for k in keys:
            n=self._data[k]
            i=self._item_list.Append(n.subject)
            self._item_list.SetClientData(i, k)
            self._data_map[k]=i
        self._send_today_data()

    def _populate_each(self, k):
        # populate the detailed info of the item keyed k
        if k is None:
            # clear out all the subfields
            self._clear_each()
            return
        # there're data, first enable the widgets
        self.ignoredirty=True
        for w in self._w:
            w.Enable(True)
        entry=self._data[k]
        # set the general detail
        self._general_editor_w.Set(entry)
        self._cat_editor_w.Set(entry.categories)
        self._memo_editor_w.Set({ 'memo': entry.text })
        self.ignoredirty=False
        self.setdirty(False)
        
    # called from various widget update callbacks
    def OnMakeDirty(self, _=None):
        """A public function you can call that will set the dirty flag"""
        if self.dirty or self.ignoredirty or not self.IsShown():
            # already dirty, no need to make it worse
            return
        self.setdirty(True)

    def setdirty(self, val):
        """Set the dirty flag"""
        if self.ignoredirty:
            return
        self.dirty=val
        self._item_list.Enable(not self.dirty)
        self._save_btn.Enable(self.dirty)
        self._revert_btn.Enable(self.dirty)

    def CanAdd(self):
        if self.dirty:
            return False
        return True

    def GetDeleteInfo(self):
        return guihelper.ART_DEL_MEMO, "Delete Memo"

    def GetAddInfo(self):
        return guihelper.ART_ADD_MEMO, "Add Memo"

    def OnAdd(self, _):
        # add a new memo item
        if self.dirty:
            # busy editing, cannot add now, just return
            return
        m=MemoEntry()
        m.subject='New Memo'
        self._data[m.id]=m
        self._populate()
        self._save_to_db(self._data)
        self._item_list.Select(self._data_map[m.id])
        self._populate_each(m.id)

    def CanDelete(self):
        sel_idx=self._item_list.GetSelection()
        if sel_idx is None or sel_idx==-1:
            return False
        return True

    def OnDelete(self, _):
        # delete the current selected item
        sel_idx=self._item_list.GetSelection()
        if sel_idx is None or sel_idx==-1:
            # none selected
            return
        self.ignoredirty=True
        k=self._item_list.GetClientData(sel_idx)
        self._item_list.Delete(sel_idx)
        self._clear_each()
        del self._data[k]
        del self._data_map[k]
        self._save_to_db(self._data)
        self.ignoredirty=False
        self.setdirty(False)

    def getdata(self,dict,want=None):
        dict['memo']=copy.deepcopy(self._data)
        return dict

    def get_selected_data(self):
        # return a dict of selected items
        res={}
        for _idx in self._item_list.GetSelections():
            _key=self._item_list.GetClientData(_idx)
            if _key:
                res[_key]=self._data[_key]
        return res

    def get_data(self):
        return self._data

    def populate(self, dict):
        self._data=dict.get('memo', {})
        self._populate()

    def _save_to_db(self, memo_dict):
        db_rr={}
        for k, e in memo_dict.items():
            db_rr[k]=MemoDataObject(e)
        database.ensurerecordtype(db_rr, memoobjectfactory)
        self._main_window.database.savemajordict('memo', db_rr)
        
    def populatefs(self, dict):
        self._save_to_db(dict.get('memo', {}))
        return dict

    def getfromfs(self, result):
        # read data from the database
        memo_dict=self._main_window.database.getmajordictvalues('memo',
                                                                memoobjectfactory)
        r={}
        for k,e in memo_dict.items():
            if __debug__ and module_debug:
                print e
            ce=MemoEntry()
            ce.set_db_dict(e)
            r[ce.id]=ce
        result.update({ 'memo': r })
        return result

    def _OnListBoxItem(self, evt):
        # an item was clicked on/selected
        self._populate_each(self._item_list.GetClientData(evt.GetInt()))
        self.Refresh()

    def _OnSave(self, evt):
        # save the current changes
        self.ignoredirty=True
        sel_idx=self._item_list.GetSelection()
        k=self._item_list.GetClientData(sel_idx)
        entry=self._data[k]
        self._general_editor_w.Get(entry)
        entry.text=self._memo_editor_w.Get().get('memo', None)
        entry.categories=self._cat_editor_w.Get()
        entry.set_date_now()
        self._general_editor_w.Set(entry)
        self._item_list.SetString(sel_idx, entry.subject)
        self._save_to_db(self._data)
        self._send_today_data()
        self.ignoredirty=False
        self.setdirty(False)

    def _OnRevert(self, evt):
        self.ignoredirty=True
        # Enable the list to get the selection
        self._item_list.Enable()
        sel_idx=self._item_list.GetSelection()
        if sel_idx!=wx.NOT_FOUND:
            k=self._item_list.GetClientData(sel_idx)
            self._populate_each(k)
        self.ignoredirty=False
        self.setdirty(False)

    def OnPrintDialog(self, mainwindow, config):
        with guihelper.WXDialogWrapper(guiwidgets.MemoPrintDialog(self, mainwindow, config),
                                       True):
            pass
    def CanPrint(self):
        return True

    def get_keys(self):
        """Return the list of keys as being displayed"""
        return [ self._item_list.GetClientData(x) \
                 for x in range(self._item_list.GetCount()) ]

    def get_selected_keys(self):
        """Return the list of keys of selected items being displayed"""
        return [ self._item_list.GetClientData(x) \
                 for x in self._item_list.GetSelections() ]
