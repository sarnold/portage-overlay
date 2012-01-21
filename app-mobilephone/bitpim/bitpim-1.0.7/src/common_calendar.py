### BITPIM
###
### Copyright (C) 2004 Joe Pham <djpham@netzero.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: common_calendar.py 4711 2008-09-27 21:04:32Z djpham $

"Common stuff for the Calendar Import functions"

# system modules
from __future__ import with_statement
import calendar
import copy
import datetime
import sys

# wxPython modules
import wx
import wx.calendar
import wx.lib.mixins.listctrl as listmix

# local modules
import database
import guihelper
import guiwidgets
import pubsub

no_end_date=(4000, 1, 1, 0, 0)

def bp_repeat_str(dict, v):
    if v is None:
        return ''
    return v

def bp_date_str(dict, v):
    try:
        if v[0]>=no_end_date[0]:
            # no-end date, don't display it
            if dict.get('allday', False):
                return ''
            else:
                return '%02d:%02d'%v[3:]

        if dict.get('allday', False):
            return '%04d-%02d-%02d'%v[:3]
        else:
            return '%04d-%02d-%02d  %02d:%02d'% v
    except (ValueError, TypeError):
        return ''
    except:
        if __debug__: raise
        return ''

def bp_alarm_str(dict, v):
    try:
        if dict.get('alarm', False):
            v=dict.get('alarm_value', 0)
            if v:
                return '-%d min'%v
            else:
                return 'Ontime'
        else:
            return ''
    except (ValueError, TypeError):
        return ''
    except:
        if __debug__: raise
        return ''

def category_str(dict, v):
    try:
        s=''
        for d in v:
            if len(d):
                if len(s):
                    s+=', '+d
                else:
                    s=d
        return s
    except (ValueError, TypeError):
        return ''
    except:
        if __debug__: raise
        return ''

#-------------------------------------------------------------------------------
class ImportDataSource(object):
    # how to define, and retrieve calendar import data source

    # subclass might want to set these
    message_str='Select the source'
    wildcard='*.*'

    def __init__(self):
        self._source=None

    def browse(self, parent=None):
        # how to select a source, default to select a file
        with guihelper.WXDialogWrapper(wx.FileDialog(parent, self.message_str, wildcard=self.wildcard),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self._source=dlg.GetPath()

    def get(self):
        # return a source suitable for importing data
        return self._source

    def name(self):
        # return a string name for the source, default is the source itself
        return self._source or ''

    def _get_id(self):
        # return the ID string of this source (mainly for Outlook),
        # by default, just return the name
        return self.name()
    def _set_id(self, id):
        # set the ID of this source (mainly for Outlook),
        # by default, just set the source to it
        self._source=id
    id=property(fget=_get_id, fset=_set_id)

#-------------------------------------------------------------------------------
class PreviewDialog(wx.Dialog, listmix.ColumnSorterMixin):
    ID_ADD=wx.NewId()
    ID_MERGE=wx.NewId()

    def __init__(self, parent, id, title, col_labels, data={},
                 config_name=None,
                 style=wx.CAPTION|wx.MAXIMIZE_BOX| \
                 wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):

        wx.Dialog.__init__(self, parent, id=id, title=title, style=style)
        
        self.__col_labels=col_labels
        self.__config_name=config_name
        self.itemDataMap={}
        # main boxsizer
        main_bs=wx.BoxSizer(wx.VERTICAL)
        # add custom controls here
        self.getcontrols(main_bs)
        # create a data preview list with supplied column labels
        self.__list=wx.ListView(self, wx.NewId())
        self.__image_list=wx.ImageList(16, 16)
        self.__ig_up=self.__image_list.Add(wx.ArtProvider_GetBitmap(wx.ART_GO_UP,
                                                             wx.ART_OTHER,
                                                             (16, 16)))
        self.__ig_dn=self.__image_list.Add(wx.ArtProvider_GetBitmap(wx.ART_GO_DOWN,
                                                             wx.ART_OTHER,
                                                             (16, 16)))
        self.__list.SetImageList(self.__image_list, wx.IMAGE_LIST_SMALL)
        li=wx.ListItem()
        li.m_mask=wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE
        li.m_image=-1
        for i, d in enumerate(self.__col_labels):
            # insert a column with specified name and width
            li.m_text=d[1]
            self.__list.InsertColumnInfo(i, li)
            self.__list.SetColumnWidth(i, d[2])
        main_bs.Add(self.__list, 1, wx.EXPAND, 0)
        self.populate(data)
        # the Mixin sorter
        listmix.ColumnSorterMixin.__init__(self, len(col_labels))
        # now the buttons
        self.getpostcontrols(main_bs)
        # handle events
        # all done
        self.SetSizer(main_bs)
        self.SetAutoLayout(True)
        main_bs.Fit(self)
        # save my own size, if specified
        if config_name is not None:
            guiwidgets.set_size(config_name, self)
            wx.EVT_SIZE(self, self.__save_size)

    def getcontrols(self, main_bs):
        # controls to be placed above the preview pane
        # by default, put nothing.
        pass

    def getpostcontrols(self, main_bs):
        # control to be placed below the preview pane
        # by default, just add the OK & CANCEL button
        main_bs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        main_bs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
    def populate(self, data):
        self.__list.DeleteAllItems()
        m={}
        m_count=0
        for k in data:
            try:
                d=data[k]
                col_idx=None
                mm={}
                for i, l in enumerate(self.__col_labels):
                    entry=d.get(l[0], None)
                    s=''
                    if l[3] is None:
                        s=str(entry)
                    else:
                        s=l[3](d, entry)
                    mm[i]=s
                    if i:
                        self.__list.SetStringItem(col_idx, i, s)
                    else:
                        col_idx=self.__list.InsertImageStringItem(sys.maxint, s, -1)
                self.__list.SetItemData(col_idx, m_count)
                m[m_count]=mm
                m_count += 1
            except:
                # something wrong happened, drop this event
                if __debug__: raise
        self.itemDataMap=m

    def GetListCtrl(self):
        return self.__list

    def GetSortImages(self):
        return (self.__ig_dn, self.__ig_up)

    def __save_size(self, evt):
        if self.__config_name is not None:
            guiwidgets.save_size(self.__config_name, self.GetRect())
        evt.Skip()

#-------------------------------------------------------------------------------
class FilterDataObject(database.basedataobject):
    _knownproperties=['rpt_events', 'no_alarm', 'alarm_override',
                      'ringtone', 'vibrate', 'alarm_value',
                      'preset_date' ]
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    _knownlistproperties.update( {'categories': ['category'],
                                  'start': ['year', 'month', 'day'],
                                  'end': ['year', 'month', 'day'] })
    def __init__(self, data=None):
        if data:
            self.update(data)

filterobjectfactory=database.dataobjectfactory(FilterDataObject)
#-------------------------------------------------------------------------------
class FilterDialogBase(wx.Dialog):
    unnamed="Select:"
    def __init__(self, parent, id, caption, categories, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, id,
                           title=caption, style=style)
        # the main box sizer
        bs=wx.BoxSizer(wx.VERTICAL)
        # the flex grid sizers for the editable items
        main_fgs=wx.FlexGridSizer(0, 1, 0, 0)
        fgs=wx.FlexGridSizer(3, 2, 0, 5)
        fgs1=wx.FlexGridSizer(0, 1, 0, 0)
        fgs2=wx.FlexGridSizer(0, 2, 0, 5)
        # set the date options
        self.SetDateControls(fgs, fgs1)
        # new repeat to single events option
        self._rpt_chkbox=wx.CheckBox(self, id=wx.NewId(), label='Repeat Events:',
                                      style=wx.ALIGN_RIGHT)
        self._rpt_chkbox.Disable()
        fgs.Add(self._rpt_chkbox, 0, wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM, 5)
        self._rpt_chkbox_text=wx.StaticText(self, -1, 'Import as multi-single events.')
        fgs.Add(self._rpt_chkbox_text, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTRE, 0)
        self._rpt_chkbox_text.Disable()
        # alarm option
        choices=('Disable All Alarms', 'Use Alarm Settings From Calender', 
                 'Set Alarm On All Events') 
        self.__alarm_setting = wx.RadioBox(self, id=wx.NewId(),
                                           label="Select Alarm Settings For Imported Events",
                                           choices=choices,
                                           majorDimension=1,
                                           size=(280,-1))
        fgs1.Add(self.__alarm_setting, 0, wx.ALIGN_CENTRE|wx.TOP|wx.BOTTOM, 5)
        #alarm vibrate
        self.__vibrate=wx.CheckBox(self, id=wx.NewId(), label='Alarm Vibrate:',
                                   style=wx.ALIGN_RIGHT)
        fgs2.Add(self.__vibrate, 0, wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM, 5)
        self.__vibrate_text=wx.StaticText(self, -1, 'Enable vibrate for alarms.')
        fgs2.Add(self.__vibrate_text, 0, wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, 5)
        # alarm settings
        self.__ringtone_text=wx.StaticText(self, -1, 'Alarm Ringtone:')
        fgs2.Add(self.__ringtone_text, 0, wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM, 5)
        self.__ringtone=wx.ComboBox(self, id=wx.NewId(),
                                    style=wx.CB_DROPDOWN|wx.CB_READONLY,
                                    choices=[self.unnamed], size=(160,-1))
        fgs2.Add(self.__ringtone, 0, wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, 2)
        # alarm value
        self.__alarm_value_text=wx.StaticText(self, -1, 'Alert before (mins):')
        fgs2.Add(self.__alarm_value_text, 0, wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM, 5)
        self.__alarm_value=wx.lib.intctrl.IntCtrl(self, id=wx.NewId(), size=(50,-1), 
                                               value=0, min=0, max=1000)
        fgs2.Add( self.__alarm_value, 0, wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, 2)
        # category option
        self.__cat_chkbox=wx.CheckBox(self, id=wx.NewId(), label='Categories:',
                                      style=wx.ALIGN_RIGHT)
        fgs2.Add(self.__cat_chkbox, 0, wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM, 5)
        for i,c in enumerate(categories):
            if not len(c):
                categories[i]='<None>'
        self.__cats=wx.CheckListBox(self, choices=categories, size=(160, 50))
        self.__cats.Disable()
        fgs2.Add(self.__cats, 0, wx.ALIGN_LEFT, 0)
        main_fgs.Add(fgs, 1, wx.EXPAND|wx.ALL, 0)
        main_fgs.Add(fgs1, 1, wx.EXPAND|wx.ALL, 0)
        main_fgs.Add(fgs2, 1, wx.EXPAND|wx.ALL, 0)
        bs.Add(main_fgs, 1, wx.EXPAND|wx.ALL, 5)
        # the buttons
        bs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        bs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        # event handles
        wx.EVT_CHECKBOX(self, self._start_date_chkbox.GetId(), self.OnCheckBox)
        wx.EVT_CHECKBOX(self, self._end_date_chkbox.GetId(), self.OnCheckBox)
        wx.EVT_CHECKBOX(self, self.__cat_chkbox.GetId(), self.OnCheckBox)
        wx.EVT_RADIOBOX(self, self.__alarm_setting.GetId(), self.OnAlarmSetting)
        # Listen to changes in ringtones list
        pubsub.subscribe(self.OnRingtoneUpdates, pubsub.ALL_RINGTONES)
        # all done
        self.SetSizer(bs)
        self.SetAutoLayout(True)
        bs.Fit(self)

    def __del__(self):
        pubsub.unsubscribe(self.OnRingtoneUpdates)

    def ShowModal(self):
        # request ringtones from 
        wx.CallAfter(pubsub.publish, pubsub.REQUEST_RINGTONES) # make the call once we are onscreen
        return wx.Dialog.ShowModal(self)

    def OnRingtoneUpdates(self, msg):
        "Receives pubsub message with ringtone list"
        tones=msg.data[:]
        #cur=self.Get()
        try:
            self.__ringtone.Clear()
            self.__ringtone.Append(self.unnamed)
            for p in tones:
                self.__ringtone.Append(p)
            rt=self.__ringtone.SetStringSelection(self.ringtone)
        except:
            self.ringtone=self.unnamed

    def __set_cats(self, chk_box, c, data):
        if data is None:
            chk_box.SetValue(False)
            c.Disable()
        else:
            chk_box.SetValue(True)
            c.Enable()
            for i,d in enumerate(data):
                if not len(d):
                    data[i]='<None>'
            for i in range(c.GetCount()):
                c.Check(i, c.GetString(i) in data)

    def __set_rpt(self, data):
        if self._start_date_chkbox.GetValue() and\
           self._end_date_chkbox.GetValue():
            self._rpt_chkbox.Enable()
            self._rpt_chkbox_text.Enable()
            self._rpt_chkbox.SetValue(data)
        else:
            self._rpt_chkbox.SetValue(False)
            self._rpt_chkbox.Disable()
            self._rpt_chkbox_text.Disable()

    def __set_alarm_fields(self, value):
        if value==0:
            self.__vibrate.Disable()
            self.__alarm_value.Disable()
            self.__ringtone.Disable()
            self.__vibrate_text.Disable()
            self.__alarm_value_text.Disable()
            self.__ringtone_text.Disable()
        elif value==1:
            self.__vibrate.Enable()
            self.__alarm_value.Disable()
            self.__ringtone.Enable()
            self.__vibrate_text.Enable()
            self.__alarm_value_text.Disable()
            self.__ringtone_text.Enable()
        else:
            self.__vibrate.Enable()
            self.__alarm_value.Enable()
            self.__ringtone.Enable()
            self.__vibrate_text.Enable()
            self.__alarm_value_text.Enable()
            self.__ringtone_text.Enable()

    def set_base(self, data):
        self.__set_rpt(data.get('rpt_events', False))
        no_alarm=data.get('no_alarm', False)
        alarm_override=data.get('alarm_override', False)
        if no_alarm:
            value=0
        elif alarm_override:
            value=2
        else:
            value=1
        self.__set_alarm_fields(value)
        self.__alarm_setting.SetSelection(value)
        self.ringtone=data.get('ringtone', self.unnamed)
        try:
            self.__ringtone.SetStringSelection(ringtone)
        except:
            self.__ringtone.SetStringSelection(self.unnamed)
        value=data.get('vibrate', False);
        self.__vibrate.SetValue(value)
        self.__alarm_value.SetValue(int(data.get('alarm_value', 0)))
        self.__set_cats(self.__cat_chkbox, self.__cats, data.get('categories', None))

    def get_base(self, r):
        r['rpt_events']=self._rpt_chkbox.GetValue()
        value=self.__alarm_setting.GetSelection()
        if value==0:
            r['no_alarm']=True
            r['alarm_override']=False
        elif value==1:
            r['no_alarm']=False
            r['alarm_override']=False
        else:
            r['no_alarm']=False
            r['alarm_override']=True
        r['ringtone']=self.__ringtone.GetStringSelection()
        r['vibrate']=self.__vibrate.GetValue()
        r['alarm_value']=self.__alarm_value.GetValue()
        if self.__cat_chkbox.GetValue():
            c=[]
            for i in range(self.__cats.GetCount()):
                if self.__cats.IsChecked(i):
                    s=self.__cats.GetString(i)
                    if s=='<None>':
                        c.append('')
                    else:
                        c.append(s)
            r['categories']=c
        else:
            r['categories']=None
        return
    
    def OnAlarmSetting(self, _):
        self.__set_alarm_fields(self.__alarm_setting.GetSelection())

    def _repeat_option(self, on=True):
        if on:
            self._rpt_chkbox.Enable()
            self._rpt_chkbox_text.Enable()
        else:
            self._rpt_chkbox.SetValue(False)
            self._rpt_chkbox.Disable()
            self._rpt_chkbox_text.Disable()

    def OnCheckBox(self, evt):
        evt_id=evt.GetId()
        if evt_id==self._start_date_chkbox.GetId():
            w1,w2=self._start_date_chkbox, self._start_date
        elif evt_id==self._end_date_chkbox.GetId():
            w1,w2=self._end_date_chkbox, self._end_date
        else:
            w1,w2=self.__cat_chkbox, self.__cats
        if w1.GetValue():
            w2.Enable()
        else:
            w2.Disable()
        # turn on the repeat event option of both start date and end date
        # are specified.
        self._repeat_option(self._start_date_chkbox.GetValue() and \
                            self._end_date_chkbox.GetValue())

#-------------------------------------------------------------------------------
class FilterDialog(FilterDialogBase):
    def __init__(self, parent, id, caption, categories, style=wx.DEFAULT_DIALOG_STYLE):
        FilterDialogBase.__init__(self, parent, id, caption, categories, style)
        self._get_from_fs()

    def _get_from_fs(self):
        _db_data=self.GetParent().GetParent().GetActiveDatabase().getmajordictvalues('calendar_filter',
                                                           filterobjectfactory)
        _data={}
        _data.update(_db_data.get('filter', {}))
        if _data.has_key('categories'):
            _cat=[x['category'] for x in _data['categories']]
            del _data['categories']
            _data['categories']=_cat
        if _data.has_key('start'):
            _d0=_data['start'][0]
            _date=(_d0['year'], _d0['month'], _d0['day'])
            del _data['start']
            _data['start']=_date
        if _data.has_key('end'):
            _d0=_data['end'][0]
            _date=(_d0['year'], _d0['month'], _d0['day'])
            del _data['end']
            _data['end']=_date
        self.set(_data)

    def _save_to_fs(self, data):
        _data=copy.deepcopy(data, {})
        del _data['categories']
        if data.has_key('categories') and data['categories']:
            _cat=[{'category': x} for x in data['categories'] ]
            _data['categories']=_cat
        del _data['start']
        if data.has_key('start') and data['start']:
            _date=[{'year': data['start'][0], 'month': data['start'][1],
                    'day': data['start'][2] }]
            _data['start']=_date
        del _data['end']
        if data.has_key('end') and data['end']:
            _date=[{'year': data['end'][0], 'month': data['end'][1],
                    'day': data['end'][2] }]
            _data['end']=_date
        _dict={ 'filter': _data }
        database.ensurerecordtype(_dict, filterobjectfactory)
        self.GetParent().GetParent().GetActiveDatabase().savemajordict('calendar_filter',
                                                            _dict)

    def SetDateControls(self, fgs, fgs1):
        self._start_date_chkbox=wx.CheckBox(self, id=wx.NewId(), 
                                             label='Start Date:',
                                             style=wx.ALIGN_RIGHT)
        fgs.Add(self._start_date_chkbox, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL, 0)
        self._start_date=wx.calendar.CalendarCtrl(self, -1, wx.DateTime_Now(),
                                          style = wx.calendar.CAL_SUNDAY_FIRST
                                          | wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION)
        self._start_date.Disable()
        fgs.Add(self._start_date, 1, wx.ALIGN_LEFT, 5)
        self._end_date_chkbox=wx.CheckBox(self, id=wx.NewId(),
                                           label='End Date:',
                                           style=wx.ALIGN_RIGHT)
        fgs.Add(self._end_date_chkbox, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL, 0)
        self._end_date=wx.calendar.CalendarCtrl(self, -1, wx.DateTime_Now(),
                                          style = wx.calendar.CAL_SUNDAY_FIRST
                                          | wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION)
        self._end_date.Disable()
        fgs.Add(self._end_date, 1, wx.ALIGN_LEFT, 5)
        self._preset_date_chkbox=wx.CheckBox(self, -1, label='Preset Duration',
                                             style=wx.ALIGN_RIGHT)
        fgs.Add(self._preset_date_chkbox, 0,
                wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL, 0)
        self._preset_date=wx.Choice(self, -1, choices=('This Week',
                                                       'This Month',
                                                       'This Year',
                                                       'Next 7 Days',))
        self._preset_date.SetSelection(1)
        self._preset_date.Disable()
        fgs.Add(self._preset_date, 0, wx.ALIGN_LEFT, 5)
        wx.EVT_CHECKBOX(self, self._preset_date_chkbox.GetId(),
                        self.OnCheckBox)

    def OnCheckBox(self, evt):
        super(FilterDialog, self).OnCheckBox(evt)
        self._repeat_option(self._start_date_chkbox.GetValue() and \
                            self._end_date_chkbox.GetValue() or \
                            self._preset_date_chkbox.GetValue())
        if evt.GetId()==self._preset_date_chkbox.GetId():
            if self._preset_date_chkbox.GetValue():
                self._preset_date.Enable()
            else:
                self._preset_date.Disable()

    def __set_date(self, chk_box, cal, d):
        if d is None:
            chk_box.SetValue(False)
            cal.Disable()
        else:
            chk_box.SetValue(True)
            cal.Enable()
            dt=wx.DateTime()
            dt.Set(d[2], year=d[0], month=d[1]-1)
            cal.SetDate(dt)

    def set_base(self, data):
        super(FilterDialog, self).set_base(data)
        self._rpt_chkbox.SetValue(data.get('rpt_events', False))

    def set(self, data):
        self.__set_date(self._start_date_chkbox, self._start_date,
                        data.get('start', None))
        self.__set_date(self._end_date_chkbox, self._end_date,
                        data.get('end', None))
        self.set_base(data)
        if data.get('preset_date', None) is not None:
            self._preset_date_chkbox.SetValue(True)
            self._preset_date.Enable()
            self._preset_date.SetSelection(data['preset_date'])
            self._repeat_option(True)
        else:
            self._preset_date_chkbox.SetValue(False)
            self._preset_date.Disable()

    def _get_preset_thisweek(self):
        # return the dates of (today, Sat)
        _today=datetime.date.today()
        _dow=_today.isoweekday()%7  #Sun=0, Sat=6
        _end=_today+datetime.timedelta(6-_dow)
        return ((_today.year, _today.month, _today.day),
                (_end.year, _end.month, _end.day))

    def _get_preset_thismonth(self):
        # return the dates of (today, end-of-month)
        _today=datetime.date.today()
        _end=_today.replace(day=calendar.monthrange(_today.year,_today.month)[1])
        return ((_today.year, _today.month, _today.day),
                (_end.year, _end.month, _end.day))

    def _get_preset_thisyear(self):
        # return the dates of (today, end-of-year)
        _today=datetime.date.today()
        _end=_today.replace(month=12, day=31)
        return ((_today.year, _today.month, _today.day),
                (_end.year, _end.month, _end.day))

    def _get_preset_next7(self):
        # return the dates of (today, today+6)
        _today=datetime.date.today()
        _end=_today+datetime.timedelta(days=6)
        return ((_today.year, _today.month, _today.day),
                (_end.year, _end.month, _end.day))

    def _get_preset_date(self):
        _choice=self._preset_date.GetSelection()
        if _choice==wx.NOT_FOUND:
            return None, None
        if _choice==0:
            return self._get_preset_thisweek()
        elif _choice==1:
            return self._get_preset_thismonth()
        elif _choice==2:
            return self._get_preset_thisyear()
        else:
            return self._get_preset_next7()

    def get(self):
        r={}
        if self._preset_date_chkbox.GetValue():
            r['start'],r['end']=self._get_preset_date()
            r['preset_date']=self._preset_date.GetSelection()
        else:
            r['preset_date']=None
            if self._start_date_chkbox.GetValue():
                dt=self._start_date.GetDate()
                r['start']=(dt.GetYear(), dt.GetMonth()+1, dt.GetDay())
            else:
                r['start']=None
            if self._end_date_chkbox.GetValue():
                dt=self._end_date.GetDate()
                r['end']=(dt.GetYear(), dt.GetMonth()+1, dt.GetDay())
            else:
                r['end']=None
        self.get_base(r)
        self._save_to_fs(r)
        return r
    
#-------------------------------------------------------------------------------
class AutoSyncFilterDialog(FilterDialogBase):
    def __init__(self, parent, id, caption, categories, style=wx.DEFAULT_DIALOG_STYLE):
        FilterDialogBase.__init__(self, parent, id, caption, categories, style)

    def SetDateControls(self, fgs, fgs1):
        #start_offset
        self._start_date_chkbox=wx.CheckBox(self, id=wx.NewId(), 
                                             label='Start Offset (days):',
                                             style=wx.ALIGN_RIGHT)
        fgs.Add(self._start_date_chkbox, 0, wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM, 5)
        self._start_date=wx.lib.intctrl.IntCtrl(self, id=wx.NewId(), size=(50,-1), 
                                                 value=0, min=0, max=1000)
        self._start_date.Disable()
        fgs.Add( self._start_date, 0, wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, 2)
        #end_offset
        self._end_date_chkbox=wx.CheckBox(self, id=wx.NewId(),
                                           label='End Offset (days):',
                                           style=wx.ALIGN_RIGHT)
        fgs.Add(self._end_date_chkbox, 0, wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM, 5)
        self._end_date=wx.lib.intctrl.IntCtrl(self, id=wx.NewId(), size=(50,-1), 
                                               value=0, min=0, max=1000)
        self._end_date.Disable()
        fgs.Add( self._end_date, 0, wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, 2)
        fgs1.Add(wx.StaticText(self, -1, 'Note: The start offset is the number of days' + 
                               ' in the past, and the end offset is the number of days' +
                               ' in the future imported from the calender into your phone. If' +
                               ' disabled, all past and/or future events are imported.',
                               size=(270,55)),
                               0, wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, 5)


    def __set_start_date(self, d):
        if d is None:
            self._start_date_chkbox.SetValue(False)
            self._start_date.Disable()
        else:
            self._start_date_chkbox.SetValue(True)
            self._start_date.Enable()
            self._start_date.SetValue(d)

    def __set_end_date(self, d):
        if d is None:
            self._end_date_chkbox.SetValue(False)
            self._end_date.Disable()
        else:
            self._end_date_chkbox.SetValue(True)
            self._end_date.Enable()
            self._end_date.SetValue(d)

    def set(self, data):
        self.__set_start_date(data.get('start_offset', None))
        self.__set_end_date(data.get('end_offset', None))
        self.set_base(data)

    def get(self):
        r={}
        if self._start_date_chkbox.GetValue():
            r['start_offset']=self._start_date.GetValue()
        else:
            r['start_offset']=None
        if self._end_date_chkbox.GetValue():
            r['end_offset']=self._end_date.GetValue()
        else:
            r['end_offset']=None
        self.get_base(r)
        return r

#-------------------------------------------------------------------------------
class ExportCalendarDialog(wx.Dialog):
    # subclass should override these
    _default_file_name=""
    _wildcards="All files|*.*"
    
    def __init__(self, parent, title):
        super(ExportCalendarDialog, self).__init__(parent, -1, title)
        # make the ui
        vbs=wx.BoxSizer(wx.VERTICAL)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.StaticText(self, -1, "File"), 0, wx.ALL|wx.ALIGN_CENTRE, 5)
        self.filenamectrl=wx.TextCtrl(self, -1, self._default_file_name)
        hbs.Add(self.filenamectrl, 1, wx.ALL|wx.EXPAND, 5)
        self.browsectrl=wx.Button(self, wx.NewId(), "Browse...")
        hbs.Add(self.browsectrl, 0, wx.ALL|wx.EXPAND, 5)
        vbs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)
        # selection GUI
        vbs.Add(self.GetSelectionGui(self), 5, wx.EXPAND|wx.ALL, 5)
        # the buttons
        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL,5)
        vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALIGN_CENTER|wx.ALL, 5)
        # event handlers
        wx.EVT_BUTTON(self, self.browsectrl.GetId(), self.OnBrowse)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
        # all done
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

    def GetSelectionGui(self, parent):
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        self._selection=wx.RadioBox(parent, wx.NewId(), 'Events Selection',
                                    choices=['All', 'Date Range'],
                                    style=wx.RA_SPECIFY_ROWS)
        hbs.Add(self._selection, 0, wx.EXPAND|wx.ALL, 5)
        sbs=wx.StaticBoxSizer(wx.StaticBox(parent, -1, 'Date Range'), wx.VERTICAL)
        gs=wx.FlexGridSizer(-1, 2, 5, 5)
        gs.AddGrowableCol(1)
        gs.Add(wx.StaticText(self, -1, 'Start:'), 0, wx.ALL, 0)
        self._start_date=wx.DatePickerCtrl(self, style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)
        gs.Add(self._start_date, 0, wx.ALL, 0)
        gs.Add(wx.StaticText(self, -1, 'End:'), 0, wx.ALL, 0)
        self._end_date=wx.DatePickerCtrl(self, style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)
        gs.Add(self._end_date, 0, wx.ALL, 0)
        sbs.Add(gs, 1, wx.EXPAND|wx.ALL, 5)
        hbs.Add(sbs, 0, wx.EXPAND|wx.ALL, 5)
        return hbs

    def OnBrowse(self, _):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, defaultFile=self.filenamectrl.GetValue(),
                                                     wildcard=self._wildcards, style=wx.SAVE|wx.CHANGE_DIR),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.filenamectrl.SetValue(dlg.GetPath())

    def _export(self):
        # perform the actual caledar data import, subclass MUST override
        raise NotImplementedError

    def OnOk(self, _):
        # do export
        self._export()
        self.EndModal(wx.ID_OK)
