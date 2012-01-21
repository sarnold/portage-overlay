### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@netzero.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: todo.py 4459 2007-11-24 07:55:33Z djpham $

"""
Code to handle Todo Items

The format for the Todo items is standardized.  It is a dict with the following
fields:

TodoEntry properties:
summary - 'string subject'
note - 'string note'
due_date - 'YYYYMMDD'
status - (None, NotStarted, InProgress, NeedActions, Completed, Cancelled)
percent_complete - None, range(101)
completion_date - 'YYYYMMDD'
categories - [{ 'category': string }]
private - True/<False|None>
priority - range(1, 11) 1=Highest, 5=Normal, 10=Lowest

TodoEntry Methods:
get() - return a copy of the internal dict
set(dict) - set the internal dict
check_completion() - check the task for completion and if so set appropriate
                     values
completion() - set the task as completed and set appropriate values

To implement Todo read/write for a phone module:
 Add 2 entries into Profile._supportedsyncs:
        ...
        ('todo', 'read', None),     # all todo reading
        ('todo', 'write', 'OVERWRITE')  # all todo writing

implement the following 2 methods in your Phone class:
    def gettodo(self, result):
        ...
        return result

    def savetodo(self, result, merge):
        ...
        return result

The result dict key is 'todo'.

"""

# standard modules
from __future__ import with_statement
import copy
import datetime
import time

# wx modules
import wx
import wx.lib.calendar
import wx.calendar as cal
import wx.lib.scrolledpanel as scrolled

# BitPim modules
import calendarentryeditor as cal_editor
import database
import guihelper
import helpids
import field_color
import phonebookentryeditor as pb_editor
import pubsub
import today
import guihelper
import widgets

widgets_list=[]

#-------------------------------------------------------------------------------
class TodoDataObject(database.basedataobject):
    _knownproperties=['summary', 'note', 'due_date', 'status',
                      'percent_complete', 'completion_date', 'priority' ]
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    _knownlistproperties.update( {'categories': ['category'],
                                  'flags': ['secret'] })

    def __init__(self, data=None):
        if data is None or not isinstance(data, TodoEntry):
            return;
        self.update(data.get_db_dict())
todoobjectfactory=database.dataobjectfactory(TodoDataObject)

#-------------------------------------------------------------------------------
class TodoEntry(object):
    ST_NotStarted=1
    ST_InProgress=2
    ST_NeedActions=3
    ST_Completed=4
    ST_Cancelled=5
    ST_Last=6
    ST_Range=xrange(ST_NotStarted, ST_Last)
    ST_Names=(
        '<None>', 'Not Started', 'In Progess', 'Need Actions',
        'Completed', 'Cancelled', 'LAST')
    PC_Range=xrange(101)  # % Complete: 0-100%
    PR_Range=xrange(1, 11)
    _id_index=0
    _max_id_index=999

    def __init__(self):
        self._data={ 'serials': [] }
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

    def complete(self):
        # complete this task: set relevant values to indicate so
        if self.status != self.ST_Completed:
            self.status=self.ST_Completed
        if self.percent_complete != 100:
            self.percent_complete=100
        if not len(self.completion_date):
            self.completion_date=datetime.date.today().strftime('%Y%m%d')

    def check_completion(self):
        if self.status==self.ST_Completed or self.percent_complete==100 or \
           len(self.completion_date):
            self.complete()

    def _set_or_del(self, key, v, v_list=[]):
        if v is None or v in v_list:
            if self._data.has_key(key):
                del self._data[key]
        else:
            self._data[key]=v

    def _create_id(self):
        "Create a BitPim serial for this entry"
        self._data.setdefault("serials", []).append(\
            {"sourcetype": "bitpim",
             "id": '%.3f%03d'%(time.time(), TodoEntry._id_index) })
        if TodoEntry._id_index<TodoEntry._max_id_index:
            TodoEntry._id_index+=1
        else:
            TodoEntry._id_index=0
    def _get_id(self):
        s=self._data.get('serials', [])
        for n in s:
            if n.get('sourcetype', None)=='bitpim':
                return n.get('id', None)
        return None
    id=property(fget=_get_id)

    def _get_summary(self):
        return self._data.get('summary', '')
    def _set_summary(self, v):
        self._set_or_del('summary', v, [''])
    summary=property(fget=_get_summary, fset=_set_summary)

    def _get_note(self):
        return self._data.get('note', '')
    def _set_note(self, v):
        self._set_or_del('note', v, [''])
    note=property(fget=_get_note, fset=_set_note)

    def _get_due_date(self):
        return self._data.get('due_date', '')
    def _set_due_date(self, v):
        self._set_or_del('due_date', v, [''])
    due_date=property(fget=_get_due_date, fset=_set_due_date)

    def _get_status(self):
        return self._data.get('status', None)
    def _set_status(self, v):
        if v is not None and v not in self.ST_Range:
            raise ValueError, 'Illegal Status Value'
        self._set_or_del('status', v, [])
        if v==self.ST_Completed:
            self.complete()
    status=property(fget=_get_status, fset=_set_status)
    def is_active(self):
        _status=self.status
        return _status!=self.ST_Completed and _status!=self.ST_Cancelled

    def _get_percent_complete(self):
        return self._data.get('percent_complete', None)
    def _set_percent_complete(self, v):
        if v is not None and v not in self.PC_Range:
            raise ValueError, 'Illegal Percent Complete Value'
        self._set_or_del('percent_complete', v, [])
        if v==100:
            self.complete()
    percent_complete=property(fget=_get_percent_complete,
                              fset=_set_percent_complete)

    def _get_completion_date(self):
        return self._data.get('completion_date', '')
    def _set_completion_date(self, v):
        self._set_or_del('completion_date', v, [''])
        if v is not None and len(v):
            self.complete()
    completion_date=property(fget=_get_completion_date,
                             fset=_set_completion_date)

    def _get_priority(self):
        return self._data.get('priority', None)
    def _set_priority(self, v):
        if v is not None and v not in self.PR_Range:
            raise ValueError, 'Illegal priority value'
        self._set_or_del('priority', v, [])
    priority=property(fget=_get_priority, fset=_set_priority)

    def _get_categories(self):
        return self._data.get('categories', [])
    def _set_categories(self, s):
        self._set_or_del('categories', s,[])
        if not s and self._data.has_key('categories'):
            del self._data['categories']
    categories=property(fget=_get_categories, fset=_set_categories)

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
    private=property(fget=_get_secret, fset=_set_secret)

#-------------------------------------------------------------------------------
class StatusComboBox(wx.ComboBox):
    def __init__(self, parent, _=None):
        self._choices=[TodoEntry.ST_Names[x] for x in range(TodoEntry.ST_Last)]
        super(StatusComboBox, self).__init__(parent, -1,
                                             self._choices[0],
                                              (-1, -1), (-1, -1),
                                              self._choices, wx.CB_READONLY)
        wx.EVT_COMBOBOX(self, self.GetId(), parent.OnMakeDirty)
    def GetValue(self):
        s=super(StatusComboBox, self).GetValue()
        for v,n in enumerate(self._choices):
            if n==s:
                break;
        if v:
            return v
        else:
            return None
    def SetValue(self, v):
        if v is None:
            v=0
        super(StatusComboBox, self).SetValue(self._choices[v])

#-------------------------------------------------------------------------------
class PercentCompleteBox(wx.ComboBox):
    def __init__(self, parent, _=None):
        self. _choices=['<None>', '0%', '10%', '20%', '30%', '40%',
                 '50%', '60%', '70%', '80%', '90%', '100%']
        super(PercentCompleteBox, self).__init__(parent, -1, self._choices[0],
                                                 (-1,-1), (-1,-1),
                                                 self._choices,  wx.CB_READONLY)
        wx.EVT_COMBOBOX(self, self.GetId(), parent.OnMakeDirty)
    def GetValue(self):
        s=super(PercentCompleteBox, self).GetValue()
        for v,n in enumerate(self._choices):
            if n==s:
                break
        if v:
            return (v-1)*10
        else:
            return None
    def SetValue(self, v):
        if v is None:
            v=0
        else:
            v=(v/10)+1
        super(PercentCompleteBox, self).SetValue(self._choices[v])

#-------------------------------------------------------------------------------
class PriorityBox(wx.ComboBox):
    def __init__(self, parent, _= None):
        self._choices=['<None>', '1 - Highest', '2', '3', '4', '5 - Normal',
                 '6', '7', '8', '9', '10 - Lowest']
        super(PriorityBox, self).__init__(parent, -1, self._choices[0],
                                              (-1, -1), (-1, -1),
                                              self._choices, wx.CB_READONLY)
        wx.EVT_COMBOBOX(self, self.GetId(), parent.OnMakeDirty)
    def GetValue(self):
        s=super(PriorityBox, self).GetValue()
        for v,n in enumerate(self._choices):
            if n==s:
                break
        if v:
            return v
        else:
            return None
    def SetValue(self, v):
        if v is None:
            v=0
        super(PriorityBox, self).SetValue(self._choices[v])

#-------------------------------------------------------------------------------
class DateControl(wx.Panel, widgets.BitPimWidget):
    def __init__(self, parent, _=None):
        super(DateControl, self).__init__(parent, -1)
        self._dt=None
        # main box sizer, a label, and a button
        self._hs=wx.BoxSizer(wx.HORIZONTAL)
        self._date_str=wx.StaticText(self, -1, '<None>')
        self._date_btn=wx.Button(self, -1, 'Set Date')
        self._hs.Add(self._date_str, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        self._hs.Add(self._date_btn, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        # events
        wx.EVT_BUTTON(self, self._date_btn.GetId(), self._OnSetDate)
        # all done
        self.SetSizer(self._hs)
        self.SetAutoLayout(True)
    def _refresh(self):
        if self._dt is None:
            s='<None>'
        else :
            s=self._dt.strftime('%Y-%m-%d')
        self._date_str.SetLabel(s)
        self._hs.Layout()
        self.GetParent().OnMakeDirty(None)
    def _OnSetDate(self, _):
        # bring up a calendar dlg
        if self._dt is None:
            dt=datetime.date.today()
        else:
            dt=self._dt
        with guihelper.WXDialogWrapper(wx.lib.calendar.CalenDlg(self,
                                                                month=dt.month,
                                                                day=dt.day,
                                                                year=dt.year)) as dlg:
            dlg.Centre()
            if dlg.ShowModal() == wx.ID_OK:
                self._dt=datetime.date(dlg.calend.GetYear(),
                                        dlg.calend.GetMonth(),
                                        dlg.calend.GetDay())
                self._refresh()
    def SetValue(self, v):
        # set a date string from the dict
        if v is None or not len(v):
            self._dt=None
        else:
            self._dt=datetime.date(int(v[:4]), int(v[4:6]), int(v[6:]))
        self._refresh()
    def GetValue(self):
        # return a date string YYYYMMDD
        if self._dt is None:
            return ''
        return self._dt.strftime('%Y%m%d')

#-------------------------------------------------------------------------------
class DirtyCheckBox(wx.CheckBox):
    def __init__(self, parent, _=None):
        super(DirtyCheckBox, self).__init__(parent, -1)
        wx.EVT_CHECKBOX(self, self.GetId(), parent.OnMakeDirty)

#-------------------------------------------------------------------------------
class GeneralEditor(pb_editor.DirtyUIBase):
    _dict_key_index=0
    _label_index=1
    _class_index=2
    _get_index=3
    _set_index=4
    _w_index=5
    _flg_index=6

    def __init__(self, parent, _=None):
        global widgets_list

        super(GeneralEditor, self).__init__(parent)
        self._fields=[
            ['summary', 'Summary:', cal_editor.DVTextControl, None, None, None, wx.EXPAND],
            ['status', 'Status:', StatusComboBox, None, None, None, 0],
            ['due_date', 'Due Date:', DateControl, None, None, None, wx.EXPAND],
            ['percent_complete', '% Complete:', PercentCompleteBox, None, None, None, 0],
            ['completion_date', 'Completion Date:', DateControl, None, None, None, wx.EXPAND],
            ['private', 'Private:', DirtyCheckBox, None, None, None, 0],
            ['priority', 'Priority:', PriorityBox, None, None, None, 0]
            ]
        gs=wx.FlexGridSizer(-1, 2, 5, 5)
        gs.AddGrowableCol(1)
        for n in self._fields:
            _txt=wx.StaticText(self, -1, n[self._label_index],
                               style=wx.ALIGN_LEFT)
            widgets_list.append((_txt, n[self._dict_key_index]))
            gs.Add(_txt, 0, wx.EXPAND|wx.BOTTOM, 0)
            w=n[self._class_index](self, -1)
            gs.Add(w, 0, n[self._flg_index]|wx.BOTTOM, 5)
            n[self._w_index]=w
        # event handlers
        # all done
        self.SetSizer(gs)
        self.SetAutoLayout(True)
        gs.Fit(self)

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
                w.SetValue(getattr(data, n[self._dict_key_index]))
        self.ignore_dirty=self.dirty=False

    def Get(self, data):
        self.ignore_dirty=self.dirty=False
        if data is None:
            return
        for n in self._fields:
            w=n[self._w_index]
            v=w.GetValue()
##            if v is not None:
            setattr(data, n[self._dict_key_index], v)

#-------------------------------------------------------------------------------
class TodoWidget(wx.Panel, widgets.BitPimWidget):
    color_field_name='todo'

    def __init__(self, mainwindow, parent):
        global widgets_list

        super(TodoWidget, self).__init__(parent, -1)
        self._main_window=mainwindow
        self._data=self._data_map={}
        # main box sizer
        vbs=wx.BoxSizer(wx.VERTICAL)
        # horizontal sizer for the listbox and tabs
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        # the list box
        self._item_list=wx.ListBox(self, wx.NewId(),
                                    style=wx.LB_SINGLE|wx.LB_HSCROLL|wx.LB_NEEDED_SB)
        hbs.Add(self._item_list, 1, wx.EXPAND|wx.BOTTOM, border=5)
        # the detailed info pane as a scrolled panel
        scrolled_panel=scrolled.ScrolledPanel(self, -1)
        vbs1=wx.BoxSizer(wx.VERTICAL)
        self._items=(
            (GeneralEditor, 0, None),
            (cal_editor.CategoryEditor, 1, 'category'),
            (pb_editor.MemoEditor, 1, 'memo')
            )
        self._w=[]
        for n in self._items:
            w=n[0](scrolled_panel, -1)
            vbs1.Add(w, n[1], wx.EXPAND|wx.ALL, 5)
            self._w.append(w)
            if n[2]:
                widgets_list.append((w.static_box, n[2]))
        scrolled_panel.SetSizer(vbs1)
        scrolled_panel.SetAutoLayout(True)
        vbs1.Fit(scrolled_panel)
        scrolled_panel.SetupScrolling()
        hbs.Add(scrolled_panel, 3, wx.EXPAND|wx.ALL, border=5)
        # save references to the widgets
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
                      lambda _: wx.GetApp().displayhelpid(helpids.ID_TAB_TODO))
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
                                      today.Today_Group_Todo)
        today.bind_request_event(self.OnTodayRequest)
        # color coded labels
        field_color.reload_color_info(self, widgets_list)
        pubsub.subscribe(self.OnPhoneChanged, pubsub.PHONE_MODEL_CHANGED)

    def OnPhoneChanged(self, _):
        # just reload the color info based on the new phone
        field_color.reload_color_info(self, widgets_list)
        self.Refresh()

    def _clear(self):
        self._item_list.Clear()
        self._clear_each()

    def _clear_each(self):
        for w in self._w:
            w.Set(None)
            w.Enable(False)
        self.Refresh()

    def _publish_today_events(self):
        now=datetime.datetime.now()
        _today='%04d%02d%02d'%(now.year, now.month, now.day)
        keys=self._data.keys()
        keys.sort()
        today_event=today.TodayTodoEvent()
        for k in keys:
            if self._data[k].is_active() and \
               (not self._data[k].due_date or \
                self._data[k].due_date<=_today):
                today_event.append(self._data[k].summary,
                                   { 'key': k,
                                     'index': self._data_map[k] })
        today_event.broadcast()

    def _publish_thisweek_events(self):
        now=datetime.datetime.now()
        _today='%04d%02d%02d'%(now.year, now.month, now.day)
        s=now+datetime.timedelta(7-now.isoweekday()%7)
        _sun='%04d%02d%02d'%(s.year, s.month, s.day)
        keys=self._data.keys()
        keys.sort()
        today_event=today.ThisWeekTodoEvent()
        dow_flg=[False]*7
        for k in keys:
            due_date=self._data[k].due_date
            if due_date>_today and due_date<_sun:
                dt=datetime.datetime(int(due_date[:4]), int(due_date[4:6]),
                                         int(due_date[6:8]))
                _dow=dt.isoweekday()%7
                if dow_flg[_dow]:
                    _name=today.dow_initials[-1]+'   '+self._data[k].summary
                else:
                    dow_flg[_dow]=True
                    _name=today.dow_initials[_dow]+' - '+self._data[k].summary
                today_event.append(_name, { 'key': k,
                                            'index': self._data_map[k] })
        today_event.broadcast()

    def OnTodayRequest(self, _):
        self._publish_today_events()
        self._publish_thisweek_events()

    def OnTodaySelection(self, evt):
        self.ActivateSelf()
        if evt.data:
            self._item_list.SetSelection(evt.data.get('index', wx.NOT_FOUND))
            self._populate_each(evt.data.get('key', None))

    def _populate(self):
        # populate new data
        self._clear()
        self._data_map={}
        # populate the list with data
        keys=self._data.keys()
        keys.sort()
        for k in keys:
            n=self._data[k]
            i=self._item_list.Append(n.summary)
            self._item_list.SetClientData(i, k)
            self._data_map[k]=i
        self._publish_today_events()
        self._publish_thisweek_events()

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
        self._memo_editor_w.Set({ 'memo': entry.note })
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

    def GetDeleteInfo(self):
        return guihelper.ART_DEL_TODO, "Delete Todo Item"

    def GetAddInfo(self):
        return guihelper.ART_ADD_TODO, "Add Todo Item"

    def CanAdd(self):
        if self.dirty:
            return False
        return True

    def OnAdd(self, _):
        # add a new memo item
        if self.dirty:
            # busy editing, cannot add now, just return
            return
        m=TodoEntry()
        m.summary='New Task'
        self._data[m.id]=m
        self._populate()
        self._save_to_db(self._data)
        self._item_list.Select(self._data_map[m.id])
        self._populate_each(m.id)

    def CanDelete(self):
        sel_idx=self._item_list.GetSelection()
        if sel_idx is None or sel_idx==-1:
            # none selected
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
        dict['todo']=copy.deepcopy(self._data)
        return dict

    def populate(self, dict):
        self._data=dict.get('todo', {})
        self._populate()

    def _save_to_db(self, todo_dict):
        db_rr={}
        for k, e in todo_dict.items():
            db_rr[k]=TodoDataObject(e)
        database.ensurerecordtype(db_rr, todoobjectfactory)
        self._main_window.database.savemajordict('todo', db_rr)
        self._publish_today_events()
        self._publish_thisweek_events()
        
    def populatefs(self, dict):
        self._save_to_db(dict.get('todo', {}))
        return dict

    def getfromfs(self, result):
        # read data from the database
        todo_dict=self._main_window.database.\
                   getmajordictvalues('todo',todoobjectfactory)
        r={}
        for k,e in todo_dict.items():
            ce=TodoEntry()
            ce.set_db_dict(e)
            r[ce.id]=ce
        result.update({ 'todo': r })
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
        entry.note=self._memo_editor_w.Get().get('memo', None)
        entry.categories=self._cat_editor_w.Get()
        entry.check_completion()
        self._general_editor_w.Set(entry)
        self._item_list.SetString(sel_idx, entry.summary)
        self._save_to_db(self._data)
        self.ignoredirty=False
        self.setdirty(False)

    def _OnRevert(self, evt):
        self.ignoredirty=True
        self._item_list.Enable()
        sel_idx=self._item_list.GetSelection()
        if sel_idx!=wx.NOT_FOUND:
            k=self._item_list.GetClientData(sel_idx)
            self._populate_each(k)
        self.ignoredirty=False
        self.setdirty(False)

#-------------------------------------------------------------------------------
