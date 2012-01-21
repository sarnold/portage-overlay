### BITPIM
###
### Copyright (C) 2004 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: vcal_calendar.py 4708 2008-09-06 04:10:44Z djpham $

"Deals with vcard calendar import stuff"

# system modules
from __future__ import with_statement
import contextlib
import copy
import datetime

# site modules
import wx

# local modules
import bpcalendar
import bptime
import common_calendar
import guihelper
import helpids
import vcard

module_debug=False

#-------------------------------------------------------------------------------
class ImportDataSource(common_calendar.ImportDataSource):
    # how to define, and retrieve calendar import data source
    message_str="Pick a vCal Calendar File"
    wildcard='*.vcs;*.ics'

#-------------------------------------------------------------------------------
class vCalendarFile(object):
    def __init__(self, file_name=None):
        self._data=[]
        self._file_name=file_name

    def _open(self, name):
        return file(name, 'rt')

    def _read_block(self, vfile):
        """Read a BEGIN/END block and return a dict of values/params
        """
        global module_debug
        d={}
        _inblk=False
        for n,l in vfile:
            if n[0]=='BEGIN':
                _blkname=l
                _inblk=True
                _vdata=[]
            elif n[0]=='END' and l==_blkname:
                d['BEGIN-END']={ 'value': l,
                                 'params': self._read_block(_vdata) }
                _inblk=False
            elif _inblk:
                _vdata.append((n, l))
            else:
                _params={}
                for _item in n[1:]:
                    _l=_item.split('=')
                    if len(_l)==1:
                        _params[_l[0]]=None
                    else:
                        _params[_l[0]]=_l[1]
                # Some statement, i.e. EXDATE, may occur more than once,
                # in such cases, place the values into the list
                # This may break existing cases, but we'll fix them as
                # users report them
                _val={ 'value': l, 'params': _params }
                if d.has_key(n[0]):
                    # multiple statements
                    if isinstance(d[n[0]], dict):
                        d[n[0]]=[d[n[0]], _val]
                    else:
                        d[n[0]].append(_val)
                else:
                    d[n[0]]=_val
        if module_debug:
            print d,'\n'
        return d

    def read(self, file_name=None):
        self._data=[]
        if file_name is not None:
            self._file_name=file_name
        if self._file_name is None:
            # no file name specified
            return
        try:
            with contextlib.closing(self._open(self._file_name)) as f:
                vfile=vcard.VFile(f)
                has_data=False
                for n,l in vfile:
                    if n[0]=='BEGIN' and l=='VEVENT':
                        has_data=True
                        _vdata=[]
                    elif n[0]=='END' and l=='VEVENT':
                        has_data=False
                        self._data.append(self._read_block(_vdata))
                    elif has_data:
                        _vdata.append((n, l))
        except:
            if __debug__:
                raise

    def _get_data(self):
        return copy.deepcopy(self._data)
    data=property(fget=_get_data)
        
#-------------------------------------------------------------------------------
class VCalendarImportData(object):

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
    _rrule_dow={
        'SU': 0x01, 'MO': 0x02, 'TU': 0x04, 'WE': 0x08, 'TH': 0x10,
        'FR': 0x20, 'SA': 0x40 }
    _rrule_weekday=_rrule_dow['MO']|_rrule_dow['TU']|\
                  _rrule_dow['WE']|_rrule_dow['TH']|\
                  _rrule_dow['FR']
    _source_data_class=vCalendarFile
    
    def __init__(self, file_name=None):
        self._file_name=file_name
        self._data=[]
        self._filter=self._default_filter
        self.read()

    def _accept(self, entry):
        # start & end time within specified filter
        if entry.get('repeat', False):
            # repeat event
            # need to populate to get an accurate end date
            ce=bpcalendar.CalendarEntry()
            self._populate_entry(entry, ce)
            if self._filter['start'] is not None and \
               ce.end[:3]<self._filter['start'][:3]:
                # event ends before our rannge
                return False
            if self._filter['end'] is not None and \
               ce.start[:3]>self._filter['end'][:3]:
                # event starts after our range
                return False
        else:
            # single event
            if self._filter['start'] is not None and \
               entry['start'][:3]<self._filter['start'][:3]:
                return False
            if self._filter['end'] is not None and \
               entry['end'][:3]>self._filter['end'][:3] and \
               entry['end'][:3]!=common_calendar.no_end_date[:3]:
                return False
        # check the catefory
        c=self._filter['categories']
        if c is None or not len(c):
            # no categories specified => all catefories allowed.
            return True
        if len([x for x in entry['categories'] if x in c]):
            return True
        return False

    def _populate_repeat_entry(self, e, ce):
        # populate repeat entry data
        if not e.get('repeat', False) or e.get('repeat_type', None) is None:
            #  not a repeat event
            return
        rp=bpcalendar.RepeatEntry()
        rp_type=e['repeat_type']
        rp_interval=e.get('repeat_interval', 1)
        rp_interval2=e.get('repeat_interval2', 1)
        rp_end=e.get('repeat_end', None)
        rp_num=e.get('repeat_num', None)
        rp_dow=e.get('repeat_dow', 0)
        if rp_type==rp.daily:
            # daily event
            rp.repeat_type=rp.daily
            rp.interval=rp_interval
        elif rp_type==rp.weekly or rp_type==rp.monthly:
            rp.repeat_type=rp_type
            rp.interval=rp_interval
            rp.interval2=rp_interval2
            rp.dow=rp_dow
        elif rp_type==rp.yearly:
            rp.repeat_type=rp.yearly
        else:
            # not yet supported
            return
        rp.weekstart=e.get('repeat_wkst', 'MO')
        # setting the repeat duration/end-date of this event
        if rp_end is not None:
            # end date specified
            ce.end=rp_end[:3]+ce.end[3:]
        elif rp_num:
            # num of occurrences specified
            _dt=ce.start[:3]
            for i in range(rp_num-1):
                _dt=rp.next_date(_dt)
            ce.end=_dt[:3]+ce.end[3:]
        else:
            # forever duration
            ce.end=common_calendar.no_end_date[:3]+ce.end[3:]
        # add the list of exceptions
        for k in e.get('exceptions', []):
            rp.add_suppressed(*k[:3])
        # all done
        ce.repeat=rp
            
    def _populate_entry(self, e, ce):
        # populate an calendar entry with data
        ce.description=e.get('description', None)
        ce.location=e.get('location', None)
        v=e.get('priority', None)
        if v is not None:
            ce.priority=v
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
        ce_start=e.get('start', None)
        ce_end=e.get('end', None)
        if ce_start is None and ce_end is None:
            raise ValueError, "No start or end datetime"
        if ce_start is not None:
            ce.start=ce_start
        if ce_end is not None:
            ce.end=ce_end
        if ce_start is None:
            ce.start=ce.end
        elif ce_end is None:
            ce.end=ce.start
        ce.notes=e.get('notes', None)
        v=[]
        for k in e.get('categories', []):
            v.append({ 'category': k })
        ce.categories=v
        # look at repeat
        self._populate_repeat_entry(e, ce)
        ce.allday=e.get('allday', False)

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
        global module_debug
        res={}
        single_rpt=self._filter.get('rpt_events', False)
        for k in self._data:
            try:
                if self._accept(k):
                    if k.get('repeat', False) and single_rpt:
                        d=self._generate_repeat_events(k)
                    else:
                        d=[k]
                    for n in d:
                        ce=bpcalendar.CalendarEntry()
                        self._populate_entry(n, ce)
                        res[ce.id]=ce
            except:
                if module_debug:
                    raise
        return res

    def get_category_list(self):
        l=[]
        for e in self._data:
            l+=[x for x in e.get('categories', []) if x not in l]
        return l
            
    def set_filter(self, filter):
        self._filter=filter

    def get_filter(self):
        return self._filter

    def _conv_cat(self, v, _):
        return [x.strip() for x in v['value'].split(",") if len(x)]

    def _conv_alarm(self, v, dd):
        try:
            alarm_date=bptime.BPTime(v['value'].split(';')[0])
            start_date=bptime.BPTime(dd['start'])
            if alarm_date.get()<start_date.get():
                dd['alarm_value']=(start_date-alarm_date).seconds/60
                return True
            return False
        except:
            return False

    def _conv_date(self, v, _):
        return bptime.BPTime(v['value']).get()
    def _conv_priority(self, v, _):
        try:
            return int(v['value'])
        except:
            return None
    def _conv_str(self, v, _):
        return v['value'].replace('\,', ',')

    def _process_daily_rule(self, v, dd):
        # the rule is Dx #y or Dx YYYYMMDDTHHMM
        s=v['value'].split(' ')
        dd['repeat_interval']=int(s[0][1:])
        if len(s)==1:
            # no duration/end date
            return True
        if s[1][0]=='#':
            # duration
            dd['repeat_num']=int(s[1][1:])
        else:
            # end date
            dd['repeat_end']=bptime.BPTime(s[1]).get()
        dd['repeat_type']='daily'
        return True

    def _process_weekly_rule(self, v, dd):
        # the rule is Wx | Wx <#y|YYYYMMDDTHHMMSS> | Wx MO TU
        s=v['value'].split(' ')
        dd['repeat_interval']=int(s[0][1:])
        dow=0
        for i in range(1, len(s)):
            n=s[i]
            if n[0].isdigit():
                dd['repeat_end']=bptime.BPTime(n).get()
            elif n[0]=='#':
                dd['repeat_num']=int(n[1:])
            else:
                # day-of-week
                dow=dow|self._rrule_dow.get(n, 0)
        if dow:
            dd['repeat_dow']=dow
        dd['repeat_type']='weekly'
        return True

    def _process_monthly_rule(self, v, dd):
        global module_debug
        try:
            # acceptable format: MD1 <day number> <end date | #duration>
            # or MP1 <[1-4]+ | 1-> <SU-SA> <end date | #duration>
            s=v['value'].split(' ')
            if s[0][:2]!='MD' and s[0][:2]!='MP':
                return False
            dd['repeat_interval2']=int(s[0][2:])
            if s[0][:2]=='MP':
                # every nth *day of every month
                n=s[1]
                if n in ['1+', '2+', '3+', '4+', '1-']:
                    if n[1]=='-':
                        dd['repeat_interval']=5
                    else:
                        dd['repeat_interval']=int(n[0])
                else:
                    return False
                dd['repeat_dow']=self._rrule_dow.get(s[2], 0)
            else:
                dd['repeat_interval']=dd['repeat_dow']=0
            dd['repeat_type']='monthly'
            n=s[-1]
            if len(n)>7 and n[:8].isdigit():
                # end date/time specified
                dd['repeat_end']=bptime.BPTime(n).get()
            elif n[0]=='#':
                dd['repeat_num']=int(n[1:])
            return True
        except:
            if module_debug: raise
            return False
    def _process_yearly_rule(self, v, dd):
        global module_debug
        try:
            # acceptable format YM1 <Month number> <end date | #duration>
            s=v['value'].split(' ')
            if s[0]!='YM1':
                return False
            n=s[-1]
            if len(n)>7 and n[:8].isdigit():
                # end date/time specified
                dd['repeat_end']=bptime.BPTime(n).get()
            elif n[0]=='#':
                dd['repeat_num']=int(n[1:])
            dd['repeat_type']='yearly'
            return True
        except:
            if module_debug: raise
            return False
    
    def _conv_repeat(self, v, dd):
        func_dict={
            'D': self._process_daily_rule,
            'W': self._process_weekly_rule,
            'M': self._process_monthly_rule,
            'Y': self._process_yearly_rule
            }
        c=v['value'][0]
        return func_dict.get(c, lambda *arg: False)(v, dd)
    def _conv_exceptions(self, v, _):
        try:
            _val=v if isinstance(v, (list, tuple)) else [v]
            r=[]
            for _item in _val:
                for n in _item['value'].split(';'):
                    r.append(bptime.BPTime(n).get())
            return r
        except:
            if __debug__:
                raise
            return []
    _calendar_keys=[
        ('CATEGORIES', 'categories', _conv_cat),
        ('DESCRIPTION', 'notes', _conv_str),
        ('DTSTART', 'start', _conv_date),
        ('DTEND', 'end', _conv_date),
        ('LOCATION', 'location', _conv_str),
        ('PRIORITY', 'priority', _conv_priority),
        ('SUMMARY', 'description', _conv_str),
        ('AALARM', 'alarm', _conv_alarm),
        ('DALARM', 'alarm', _conv_alarm),
        ('RRULE', 'repeat', _conv_repeat),
        ('EXDATE', 'exceptions', _conv_exceptions),
        ]
    def _convert(self, vcal, d):
        global module_debug
        for i in vcal:
            try:
                dd={'start': None, 'end': None }
                for j in self._calendar_keys:
                    if i.has_key(j[0]):
                        k=i[j[0]]
                        if j[2] is not None:
                            dd[j[1]]=j[2](self, k, dd)
                        else:
                            dd[j[1]]=k['value']
                if dd['start'] is None and dd['end'] is None:
                    # no start or end, drop this one
                    continue
                if dd['start'] is None:
                    dd['start']=dd['end']
                elif dd['end'] is None:
                    dd['end']=dd['start']
                if dd.get('allday', False) and dd['end']>dd['start']:
                    # All day event, adjust the end time as necessary
                    dd['end']=(bptime.BPTime(dd['end'])-\
                               bptime.timedelta(days=1)).get()[:3]+(0, 0)

                if module_debug: print dd
                d.append(dd)
            except:
                if module_debug: raise

    def get_display_data(self):
        cnt=0
        res={}
        single_rpt=self._filter.get('rpt_events', False)
        for k in self._data:
            if self._accept(k):
                if k.get('repeat', False) and single_rpt:
                    d=self._generate_repeat_events(k)
                else:
                    d=[k.copy()]
                for n in d:
                    if self._filter.get('no_alarm', False):
                        n['alarm']=False
                    res[cnt]=n
                    cnt+=1
        return res

    def get_file_name(self):
        if self._file_name is not None:
            return self._file_name
        return ''

    def read(self, file_name=None, update_dlg=None):
        if file_name is not None:
            self._file_name=file_name
        if self._file_name is None:
            # no file name specified
            return
        v=self._source_data_class(self._file_name)
        v.read()
        self._convert(v.data, self._data)

#-------------------------------------------------------------------------------
class VcalImportCalDialog(common_calendar.PreviewDialog):
    _column_labels=[
        ('description', 'Description', 400, None),
        ('start', 'Start', 150, common_calendar.bp_date_str),
        ('end', 'End', 150, common_calendar.bp_date_str),
        ('repeat_type', 'Repeat', 80, common_calendar.bp_repeat_str),
        ('alarm', 'Alarm', 80, common_calendar.bp_alarm_str),
        ('categories', 'Category', 150, common_calendar.category_str)
        ]
    _filetype_label="VCalendar File:"
    _data_type='vCalendar'
    _import_data_class=VCalendarImportData
    def __init__(self, parent, id, title):
        self._oc=self._import_data_class()
        common_calendar.PreviewDialog.__init__(self, parent, id, title,
                               self._column_labels,
                               self._oc.get_display_data(),
                               config_name='import/calendar/vcaldialog')
        
    def getcontrols(self, main_bs):
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        # label
        hbs.Add(wx.StaticText(self, -1, self._filetype_label), 0, wx.ALL|wx.ALIGN_CENTRE, 2)
        # where the folder name goes
        self.folderctrl=wx.TextCtrl(self, -1, "") #, style=wx.TE_READONLY)
        self.folderctrl.SetValue(self._oc.get_file_name())
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
        with guihelper.WXDialogWrapper(wx.ProgressDialog('%s Import'%self._data_type,
                                                         'Importing %s Data, please wait ...'%self._data_type,
                                                         parent=self)) as dlg:
            try:
                self._oc.read(self.folderctrl.GetValue())
                self.populate(self._oc.get_display_data())
            except (ValueError, IOError):
                guihelper.MessageDialog(self, 'Failed to get import data',
                                        'Import Error',
                                        style=wx.OK|wx.ICON_ERROR)
            except:
                if __debug__:
                    raise

    def OnBrowseFolder(self, evt):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, "Pick a %s File"%self._data_type,
                                                     wildcard='*.vcs;*.ics'),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.folderctrl.SetValue(dlg.GetPath())

    def OnFilter(self, evt):
        cat_list=self._oc.get_category_list()
        with guihelper.WXDialogWrapper(common_calendar.FilterDialog(self, -1, 'Filtering Parameters', cat_list),
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
    _oc=VCalendarImportData(folder)
    _oc.set_filter(filters)
    _oc.read()
    res={ 'calendar':_oc.get() }
    return res

#-------------------------------------------------------------------------------
class VCalAutoConfCalDialog(wx.Dialog):
    def __init__(self, parent, id, title, folder, filters,
                 style=wx.CAPTION|wx.MAXIMIZE_BOX| \
                 wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        self._oc=VCalendarImportData()
        self._oc.set_filter(filters)
        self._read=False
        wx.Dialog.__init__(self, parent, id=id, title=title, style=style)
        main_bs=wx.BoxSizer(wx.VERTICAL)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        # label
        hbs.Add(wx.StaticText(self, -1, "VCalendar File:"), 0, wx.ALL|wx.ALIGN_CENTRE, 2)
        # where the folder name goes
        self.folderctrl=wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        self.folderctrl.SetValue(folder)
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
        with guihelper.WXDialogWrapper(wx.FileDialog(self, "Pick a VCalendar File", wildcard='*.vcs'),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.folderctrl.SetValue(dlg.GetPath())
                self._read=False

    def OnFilter(self, evt):
        # read the calender to get the category list
        if not self._read:
            self._oc.read(self.folderctrl.GetValue())
            self._read=True
        cat_list=self._oc.get_category_list()
        with guihelper.WXDialogWrapper(common_calendar.AutoSyncFilterDialog(self, -1, 'Filtering Parameters', cat_list)) \
             as dlg:
            dlg.set(self._oc.get_filter())
            if dlg.ShowModal()==wx.ID_OK:
                self._oc.set_filter(dlg.get())

    def GetFolder(self):
        return self.folderctrl.GetValue()

    def GetFilter(self):
        return self._oc.get_filter()
