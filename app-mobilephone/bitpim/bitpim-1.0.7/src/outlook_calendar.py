### BITPIM
###
### Copyright (C) 2004 Joe Pham <djpham@netzero.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: outlook_calendar.py 4405 2007-09-24 21:49:06Z djpham $

"Deals with Outlook calendar import stuff"

# System modules
from __future__ import with_statement
import datetime
import pywintypes
import sys
import time

# wxPython modules
import wx
import wx.calendar
import wx.lib.mixins.listctrl as listmix

# Others

# My modules
import bpcalendar
import common
import common_calendar
import guihelper
import guiwidgets
import helpids
import native.outlook

# common convertor functions
def to_bp_date(dict, v, oc):
    # convert a pyTime to (y, m, d, h, m)
    if not isinstance(v, pywintypes.TimeType):
        raise TypeError, 'illegal type'
    if v.year>common_calendar.no_end_date[0]:
        return common_calendar.no_end_date
    return (v.year, v.month, v.day, v.hour, v.minute)

def bp_repeat_str(dict, v):
    if v is None:
        return ''
    elif v==OutlookCalendarImportData.olRecursDaily:
        return 'Daily'
    elif v==OutlookCalendarImportData.olRecursWeekly:
        return 'Weekly'
    elif v==OutlookCalendarImportData.olRecursMonthly or \
         v==OutlookCalendarImportData.olRecursMonthNth:
        return 'Monthly'
    elif v==OutlookCalendarImportData.olRecursYearly:
        return 'Yearly'
    else:
        return '<Unknown Value>'

def convert_categories(dict, v, oc):
    return [x.strip() for x in v.split(",") if len(x)]

def set_recurrence(item, dict, oc):
    oc.update_display()
    if not dict['repeat']:
        # no reccurrence, ignore
        dict['repeat']=None
        return True
    # get the recurrence pattern and map it to BP Calendar
    return oc.process_repeat(item, dict)

#-------------------------------------------------------------------------------
class ImportDataSource(common_calendar.ImportDataSource):
    # how to define, and retrieve calendar import data source

    def browse(self, parent=None):
        # how to select a source
        self._source=native.outlook.pickfolder()
    
    def name(self):
        # return a string name for the source
        if self._source:
            return native.outlook.getfoldername(self._source)
        return ''

    def _get_id(self):
        if self._source:
            return native.outlook.getfolderid(self._source)
        return None
    def _set_id(self, id):
        self._source=None
        if id:
            self._source=native.outlook.getfolderfromid(id, False, 'calendar')
    id=property(fget=_get_id, fset=_set_id)

#-------------------------------------------------------------------------------
class OutlookCalendarImportData:
    _non_auto_sync_calendar_keys=[
        # (Outlook field, BP Calendar field, convertor function)
        ('Subject', 'description', None),
        ('Location', 'location', None),
        ('Start', 'start', to_bp_date),
        ('End', 'end', to_bp_date),
        ('Categories', 'categories', convert_categories),
        ('IsRecurring', 'repeat', None),
        ('ReminderSet', 'alarm', None),
        ('ReminderMinutesBeforeStart', 'alarm_value', None),
        ('Importance', 'priority', None),
        ('Body', 'notes', None),
        ('AllDayEvent', 'allday', None)
        ]
    # the auto_sync calender fields do not support the "body" of the appointment
    # accessing this field causes an outlook warning to appear which prevents automation
    _auto_sync_calendar_keys=[
        # (Outlook field, BP Calendar field, convertor function)
        ('Subject', 'description', None),
        ('Location', 'location', None),
        ('Start', 'start', to_bp_date),
        ('End', 'end', to_bp_date),
        ('Categories', 'categories', convert_categories),
        ('IsRecurring', 'repeat', None),
        ('ReminderSet', 'alarm', None),
        ('ReminderMinutesBeforeStart', 'alarm_value', None),
        ('Importance', 'priority', None),
        ('AllDayEvent', 'allday', None)
        ]
    _recurrence_keys=[
        # (Outlook field, BP Calendar field, convertor function)
        ('NoEndDate', 'NoEndDate', None),
        ('PatternStartDate', 'PatternStartDate', to_bp_date),
        ('PatternEndDate', 'PatternEndDate', to_bp_date),
        ('Instance', 'Instance', None),
        ('DayOfWeekMask', 'DayOfWeekMask', None),
        ('Interval', 'Interval', None),
        ('Occurrences', 'Occurrences', None),
        ('RecurrenceType', 'RecurrenceType', None)
        ]
    _exception_keys=[
        # (Outlook field, BP Calendar field, convertor function)
        ('OriginalDate', 'exception_date', to_bp_date),
        ('Deleted', 'deleted', None)
        ]
    _default_filter={
        'start': None,
        'end': None,
        'categories': None,
        'rpt_events': False,
        'no_alarm': False,
        'ringtone': None,
        'alarm_override':False,
        'vibrate':False,
        'alarm_value':0
        }

    # Outlook constants
    olRecursDaily    = native.outlook.outlook_com.constants.olRecursDaily
    olRecursMonthNth = native.outlook.outlook_com.constants.olRecursMonthNth
    olRecursMonthly  = native.outlook.outlook_com.constants.olRecursMonthly
    olRecursWeekly   = native.outlook.outlook_com.constants.olRecursWeekly
    olRecursYearNth  = native.outlook.outlook_com.constants.olRecursYearNth
    olRecursYearly   = native.outlook.outlook_com.constants.olRecursYearly
    olImportanceHigh = native.outlook.outlook_com.constants.olImportanceHigh
    olImportanceLow  = native.outlook.outlook_com.constants.olImportanceLow
    olImportanceNormal = native.outlook.outlook_com.constants.olImportanceNormal

    def __init__(self, outlook=native.outlook, auto_sync_only=0):
        self._outlook=outlook
        self._data=[]
        self._error_list=[]
        self._single_data=[]
        self._folder=None
        self._filter=self._default_filter
        self._total_count=0
        self._current_count=0
        self._update_dlg=None
        self._exception_list=[]
        if auto_sync_only:
            self._calendar_keys=self._auto_sync_calendar_keys
        else:
            self._calendar_keys=self._non_auto_sync_calendar_keys

    def _accept(self, entry):
        s_date=entry['start'][:3]
        e_date=entry['end'][:3]
        if entry.get('repeat', False):
            # repeat event, must not fall outside the range
            if self._filter['start'] is not None and \
               e_date<self._filter['start'][:3]:
                return False
            if self._filter['end'] is not None and \
               s_date>self._filter['end'][:3]:
                return False
        else:
            # non-repeat event, must fall within the range
            if self._filter['start'] is not None and \
               e_date<self._filter['start'][:3]:
                return False
            if self._filter['end'] is not None and \
               e_date>self._filter['end'][:3]:
                return False
        # check the catefory
        c=self._filter.get('categories', None)
        if c is None or not len(c):
            # no categories specified => all catefories allowed.
            return True
        if len([x for x in entry['categories'] if x in c]):
            return True
        return False

    def _populate_entry(self, e, ce):
        # populate an calendar entry with outlook data
        ce.description=e.get('description', None)
        ce.location=e.get('location', None)
        v=e.get('priority', None)
        if v is not None:
            if v==self.olImportanceNormal:
                ce.priority=ce.priority_normal
            elif v==self.olImportanceLow:
                ce.priority=ce.priority_low
            elif v==self.olImportanceHigh:
                ce.priority=ce.priority_high
        if not self._filter.get('no_alarm', False) and \
               not self._filter.get('alarm_override', False) and \
               e.get('alarm', False):
            ce.alarm=e.get('alarm_value', 0)
            ce.ringtone=self._filter.get('ringtone', "")
            ce.vibrate=self._filter.get('vibrate', False)
        elif not self._filter.get('no_alarm', False) and \
               self._filter.get('alarm_override', False):
            ce.alarm=self._filter.get('alarm_value', 0)
            ce.ringtone=self._filter.get('ringtone', "")
            ce.vibrate=self._filter.get('vibrate', False)
        ce.allday=e.get('allday', False)
        if ce.allday:
            if not e.get('repeat', False):
                ce.start=e['start'][:3]+(0,0)
                # for non-recurrent allday events, Outlook always set the
                # end date to 1-extra day.
                _dt=datetime.datetime(*e['end'])-datetime.timedelta(1)
                ce.end=(_dt.year, _dt.month, _dt.day, 23, 59)
            else:
                # unless it is a repeating all day event!
                # we can now handle allday events that span more than one day!
                ce.start=e['start'][:3]+(0,0)
                ce.end=e['end'][:3]+(23,59)
        else:
            ce.start=e['start']
            ce.end=e['end']
        ce.notes=e.get('notes', None)
        v=[]
        for k in e.get('categories', []):
            v.append({ 'category': k })
        ce.categories=v
        # look at repeat events
        if not e.get('repeat', False):
            # not a repeat event, just return
            return
        rp=bpcalendar.RepeatEntry()
        rt=e['repeat_type']
        r_interval=e.get('repeat_interval', 0)
        r_interval2=e.get('repeat_interval2', 1)
        r_dow=e.get('repeat_dow', 0)
        if rt==self.olRecursDaily:
            rp.repeat_type=rp.daily
        elif rt==self.olRecursWeekly:
            if r_interval:
                # weekly event
                rp.repeat_type=rp.weekly
            else:
                # mon-fri event
                rp.repeat_type=rp.daily
        elif rt==self.olRecursMonthly or rt==self.olRecursMonthNth:
            rp.repeat_type=rp.monthly
        else:
            rp.repeat_type=rp.yearly
        if rp.repeat_type==rp.daily:
            rp.interval=r_interval
        elif rp.repeat_type==rp.weekly or rp.repeat_type==rp.monthly:
            rp.interval=r_interval
            rp.interval2=r_interval2
            rp.dow=r_dow
        # check for invalid monthly type
        if rp.repeat_type==rp.monthly and \
           rp.dow in (rp.dow_weekday, rp.dow_weekend):
            rp.dow=0
        # add the list of exceptions
        for k in e.get('exceptions', []):
            rp.add_suppressed(*k[:3])
        ce.repeat=rp

    def _generate_repeat_events(self, e):
        # generate multiple single events from this repeat event
        ce=bpcalendar.CalendarEntry()
        self._populate_entry(e, ce)
        l=[]
        new_e=e.copy()
        new_e['repeat']=False
        for k in ('repeat_type', 'repeat_interval', 'repeat_dow'):
            if new_e.has_key(k):
                del new_e[k]
        s_date=datetime.datetime(*self._filter['start'])
        e_date=datetime.datetime(*self._filter['end'])
        one_day=datetime.timedelta(1)
        this_date=s_date
        while this_date<=e_date:
            date_l=(this_date.year, this_date.month, this_date.day)
            if ce.is_active(*date_l):
                new_e['start']=date_l+new_e['start'][3:]
                new_e['end']=date_l+new_e['end'][3:]
                l.append(new_e.copy())
            this_date+=one_day
        return l
        
    def get(self):
        res={}
        single_rpt=self._filter.get('rpt_events', False)
        for k in self._data:
            if self._accept(k):
                if k.get('repeat', False) and single_rpt:
                    d=self._generate_repeat_events(k)
                else:
                    d=[k]
                for n in d:
                    ce=bpcalendar.CalendarEntry()
                    self._populate_entry(n, ce)
                    res[ce.id]=ce
        return res

    def get_display_data(self):
        cnt=0
        res={}
        single_rpt=self._filter.get('rpt_events', False)
        no_alarm=self._filter.get('no_alarm', False)
        for k in self._data:
            if self._accept(k):
                if k.get('repeat', False) and single_rpt:
                    d=self._generate_repeat_events(k)
                else:
                    d=[k.copy()]
                for n in d:
                    if no_alarm:
                        n['alarm']=False
                    res[cnt]=n
                    cnt+=1
        return res

    def get_category_list(self):
        l=[]
        for e in self._data:
            l+=[x for x in e.get('categories', []) if x not in l]
        return l
            
    def pick_folder(self):
        return self._outlook.pickfolder()

    def set_folder(self, f):
        if f is None:
            # default folder
            self._folder=self._outlook.getfolderfromid('', True, 'calendar')
        else:
            self._folder=f

    def get_folder_id(self):
        return self._outlook.getfolderid(self._folder)

    def set_folder_id(self, id):
        if id is None or id=="":
            self.set_folder(None)
        else:
            self._folder=self._outlook.getfolderfromid(id)

    def set_filter(self, filter):
        self._filter=filter

    def get_filter(self):
        return self._filter

    def get_folder_name(self):
        if self._folder is None:
            return ''
        return self._outlook.getfoldername(self._folder)

    def read(self, folder=None, update_dlg=None):
        # folder from which to read
        if folder is not None:
            self._folder=folder
        if self._folder is None:
            self._folder=self._outlook.getfolderfromid('', True, 'calendar')
        self._update_dlg=update_dlg
        self._total_count=self._folder.Items.Count
        self._current_count=0
        self._exception_list=[]
        self._data, self._error_list=self._outlook.getdata(self._folder,
                                                           self._calendar_keys,
                                                           {}, self,
                                                           set_recurrence)
        # add in the exception list, .. or shoule we keep it separate ??
        self._data+=self._exception_list

    def _set_repeat_dates(self, dict, r):
        dict['start']=r['PatternStartDate'][:3]+dict['start'][3:]
        dict['end']=r['PatternEndDate'][:3]+dict['end'][3:]
        dict['repeat_type']=r['RecurrenceType']

    def _is_daily_or_weekly(self, dict, r):
        if r['RecurrenceType']==self.olRecursDaily or \
           r['RecurrenceType']==self.olRecursWeekly:
            self._set_repeat_dates(dict, r)
            dict['repeat_interval']=r['Interval']
            dict['repeat_dow']=r['DayOfWeekMask']
            return True
        return False

    def _is_monthly(self, dict, r):
        if r['RecurrenceType']==self.olRecursMonthly or \
           r['RecurrenceType']==self.olRecursMonthNth:
            self._set_repeat_dates(dict, r)
            dict['repeat_interval2']=r['Interval']
            if r['RecurrenceType']==self.olRecursMonthNth:
                dict['repeat_interval']=r['Instance']
                dict['repeat_dow']=r['DayOfWeekMask']
            return True
        return False

    def _is_yearly(self, dict, r):
        if r['RecurrenceType']==self.olRecursYearly and \
           r['Interval']==12:
            self._set_repeat_dates(dict, r)
            return True
        return False

    def _process_exceptions(self, dict, r):
        # check for and process exceptions for this event
        r_ex=r.Exceptions
        if not r_ex.Count:
            # no exception, bail
            return
        for i in range(1, r_ex.Count+1):
            ex=self._outlook.getitemdata(r_ex.Item(i), {},
                                          self._exception_keys, self)
            dict.setdefault('exceptions', []).append(ex['exception_date'])
            if not ex['deleted']:
                # if this instance has been changed, then need to get it
                appt=self._outlook.getitemdata(r_ex.Item(i).AppointmentItem,
                                                {}, self._calendar_keys, self)
                # by definition, this instance cannot be a repeat event
                appt['repeat']=False
                appt['end']=appt['start'][:3]+appt['end'][3:]
                # and add it to the exception list
                self._exception_list.append(appt)
                
    def process_repeat(self, item, dict):
        # get the recurrence info that we need.
        rec_pat=item.GetRecurrencePattern()
        r=self._outlook.getitemdata(rec_pat, {},
                                     self._recurrence_keys, self)
        if self._is_daily_or_weekly(dict, r) or \
           self._is_monthly(dict, r) or \
           self._is_yearly(dict, r):
            self._process_exceptions(dict, rec_pat)
            return True
        # invalide repeat type, turn this event into a regular event
        dict['repeat']=False
        dict['end']=dict['start'][:3]+dict['end'][3:]
        dict['notes']+=' [BITPIM: Unrecognized repeat event, repeat event discarded]'
        return True

    def update_display(self):
        # update the progress dialog if specified
        self._current_count += 1
        if self._update_dlg is not None:
            self._update_dlg.Update(100*self._current_count/self._total_count)

    def has_errors(self):
        return bool(self._error_list)
    def get_error_list(self):
        # return a list of strings of failed items
        res=[]
        for d in self._error_list:
            # the format is 'YY-MM-DD hh:mm Description' if available
            _start=d.get('start', None)
            s=''
            if _start:
                if len(_start)>4:
                    s='%02d-%02d-%02d %02d:%02d '%_start[:5]
                elif len(_start)>2:
                    s='%02d-%02d-%02d '%_start[:3]
            _desc=d.get('description', None)
            if _desc:
                s+=_desc
            if not s:
                s='<Unknown>'
            res.append(s)
        return res

#-------------------------------------------------------------------------------
class OutlookImportCalDialog(common_calendar.PreviewDialog):
    _column_labels=[
        ('description', 'Description', 400, None),
        ('start', 'Start', 150, common_calendar.bp_date_str),
        ('end', 'End', 150, common_calendar.bp_date_str),
        ('repeat_type', 'Repeat', 80, bp_repeat_str),
        ('alarm', 'Alarm', 80, common_calendar.bp_alarm_str),
        ('categories', 'Category', 150, common_calendar.category_str)
        ]

    _config_name='import/calendar/outlookdialog'
    _browse_label='Outlook Calendar Folder:'
    _progress_dlg_title='Outlook Calendar Import'
    _error_dlg_title='Outlook Calendar Import Error'
    _error_dlg_text='Outlook Calendar Items that failed to import:'
    _data_class=OutlookCalendarImportData
    _filter_dlg_class=common_calendar.FilterDialog

    def __init__(self, parent, id, title):
        self._oc=self._data_class(native.outlook)
        self._oc.set_folder(None)
        common_calendar.PreviewDialog.__init__(self, parent, id, title,
                               self._column_labels,
                               self._oc.get_display_data(),
                               config_name=self._config_name)
        
    def getcontrols(self, main_bs):
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        # label
        hbs.Add(wx.StaticText(self, -1, self._browse_label), 0, wx.ALL|wx.ALIGN_CENTRE, 2)
        # where the folder name goes
        self.folderctrl=wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        self.folderctrl.SetValue(self._oc.get_folder_name())
        hbs.Add(self.folderctrl, 1, wx.EXPAND|wx.ALL, 2)
        # browse button
        id_browse=wx.NewId()
        hbs.Add(wx.Button(self, id_browse, 'Browse ...'), 0, wx.EXPAND|wx.ALL, 2)
        main_bs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)
        main_bs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        wx.EVT_BUTTON(self, id_browse, self.OnBrowseFolder)

    def getpostcontrols(self, main_bs):
        main_bs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        id_import=wx.NewId()
        hbs.Add(wx.Button(self, id_import, 'Import'), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs.Add(wx.Button(self, wx.ID_OK, 'Replace All'), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs.Add(wx.Button(self, self.ID_ADD, 'Add'), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs.Add(wx.Button(self, self.ID_MERGE, 'Merge'), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs.Add(wx.Button(self, wx.ID_CANCEL, 'Cancel'), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        id_filter=wx.NewId()
        hbs.Add(wx.Button(self, id_filter, 'Filter'), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs.Add(wx.Button(self, wx.ID_HELP, 'Help'), 0,  wx.ALIGN_CENTRE|wx.ALL, 5)
        main_bs.Add(hbs, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, id_import, self.OnImport)
        wx.EVT_BUTTON(self, id_filter, self.OnFilter)
        wx.EVT_BUTTON(self, self.ID_ADD, self.OnEndModal)
        wx.EVT_BUTTON(self, self.ID_MERGE, self.OnEndModal)
        wx.EVT_BUTTON(self, wx.ID_HELP, lambda *_: wx.GetApp().displayhelpid(helpids.ID_DLG_CALENDAR_IMPORT))

    @guihelper.BusyWrapper
    def OnImport(self, evt):
        with guihelper.WXDialogWrapper(wx.ProgressDialog(self._progress_dlg_title,
                                                         'Importing Outlook Data, please wait ...\n(Please also watch out for the Outlook Permission Request dialog)',
                                                         parent=self)) as dlg:
            self._oc.read(None, dlg)
            self.populate(self._oc.get_display_data())
            if self._oc.has_errors():
                # display the list of failed items
                with guihelper.WXDialogWrapper(wx.SingleChoiceDialog(self,
                                                                    self._error_dlg_text,
                                                                    self._error_dlg_title,
                                                                    self._oc.get_error_list()),
                                               True):
                    pass

    def OnBrowseFolder(self, evt):
        f=self._oc.pick_folder()
        if f is None:
            return # user hit cancel
        self._oc.set_folder(f)
        self.folderctrl.SetValue(self._oc.get_folder_name())

    def OnFilter(self, evt):
        cat_list=self._oc.get_category_list()
        with guihelper.WXDialogWrapper(self._filter_dlg_class(self, -1, 'Filtering Parameters', cat_list),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self._oc.set_filter(dlg.get())
                self.populate(self._oc.get_display_data())

    def OnEndModal(self, evt):
        self.EndModal(evt.GetId())

    def get(self):
        return self._oc.get()

    def get_categories(self):
        return self._oc.get_category_list()

#-------------------------------------------------------------------------------
def ImportCal(folder, filters):
    _oc=OutlookCalendarImportData(native.outlook, auto_sync_only=1)
    _oc.set_folder_id(folder)
    _oc.set_filter(filters)
    _oc.read()
    res={ 'calendar':_oc.get() }
    return res

#-------------------------------------------------------------------------------
class OutlookAutoConfCalDialog(wx.Dialog):
    def __init__(self, parent, id, title, folder, filters,
                 style=wx.CAPTION|wx.MAXIMIZE_BOX| \
                 wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        self._oc=OutlookCalendarImportData(native.outlook, auto_sync_only=1)
        self._oc.set_folder_id(folder)
        self._oc.set_filter(filters)
        self.__read=False
        wx.Dialog.__init__(self, parent, id=id, title=title, style=style)
        main_bs=wx.BoxSizer(wx.VERTICAL)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        # label
        hbs.Add(wx.StaticText(self, -1, "Outlook Calendar Folder:"), 0, wx.ALL|wx.ALIGN_CENTRE, 2)
        # where the folder name goes
        self.folderctrl=wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        self.folderctrl.SetValue(self._oc.get_folder_name())
        hbs.Add(self.folderctrl, 1, wx.EXPAND|wx.ALL, 2)
        # browse button
        id_browse=wx.NewId()
        hbs.Add(wx.Button(self, id_browse, 'Browse ...'), 0, wx.EXPAND|wx.ALL, 2)
        main_bs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)
        main_bs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        wx.EVT_BUTTON(self, id_browse, self.OnBrowseFolder)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.Button(self, wx.ID_OK, 'OK'), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs.Add(wx.Button(self, wx.ID_CANCEL, 'Cancel'), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        id_filter=wx.NewId()
        hbs.Add(wx.Button(self, id_filter, 'Filter'), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs.Add(wx.Button(self, wx.ID_HELP, 'Help'), 0,  wx.ALIGN_CENTRE|wx.ALL, 5)
        main_bs.Add(hbs, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, id_filter, self.OnFilter)
        wx.EVT_BUTTON(self, wx.ID_HELP, lambda *_: wx.GetApp().displayhelpid(helpids.ID_DLG_CALENDAR_IMPORT))
        self.SetSizer(main_bs)
        self.SetAutoLayout(True)
        main_bs.Fit(self)

    def OnBrowseFolder(self, evt):
        f=self._oc.pick_folder()
        if f is None:
            return # user hit cancel
        self._oc.set_folder(f)
        self.folderctrl.SetValue(self._oc.get_folder_name())
        self.__read=False

    def OnFilter(self, evt):
        # read the calender to get the category list
        if not self.__read:
            self._oc.read()
            self.__read=True
        cat_list=self._oc.get_category_list()
        with guihelper.WXDialogWrapper(common_calendar.AutoSyncFilterDialog(self, -1, 'Filtering Parameters', cat_list)) as dlg:
            dlg.set(self._oc.get_filter())
            if dlg.ShowModal()==wx.ID_OK:
                self._oc.set_filter(dlg.get())

    def GetFolder(self):
        return self._oc.get_folder_id()

    def GetFilter(self):
        return self._oc.get_filter()
