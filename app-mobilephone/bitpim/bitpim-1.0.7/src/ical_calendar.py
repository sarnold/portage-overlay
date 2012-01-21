### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: ical_calendar.py 4708 2008-09-06 04:10:44Z djpham $

"Deals with iCalendar calendar import stuff"

# system modules
from __future__ import with_statement
import datetime
import time

# site modules

# local modules
import bpcalendar
import bptime
import common_calendar
import guihelper
import vcal_calendar as vcal
import vcard

module_debug=False

#-------------------------------------------------------------------------------
class ImportDataSource(common_calendar.ImportDataSource):
    # how to define, and retrieve calendar import data source
    message_str="Pick an iCal Calendar File"
    wildcard='*.ics'

#-------------------------------------------------------------------------------
class Duration(object):
    def __init__(self, data):
        # Got a dict, compute the time duration in seconds
        self._duration=0
        self._neg=False
        self._extract_data(data)
    _funcs={
        'W': lambda x: x*604800,    # 7*24*60*60
        'H': lambda x: x*3600,      # 60*60
        'M': lambda x: x*60,
        'S': lambda x: x,
        'D': lambda x: x*86400,     # 24*60*60
        'T': lambda x: 0,
        'P': lambda x: 0,
        }
    def _extract_data(self, data):
        _i=0
        for _ch in data.get('value', ''):
            if _ch=='+':
                self._neg=False
            elif _ch=='-':
                self._neg=True
            elif _ch.isdigit():
                _i=_i*10+int(_ch)
            else:
                self._duration+=self._funcs.get(_ch, lambda _: 0)(_i)
                _i=0
    def get(self):
        if self._neg:
            return -self._duration
        return self._duration

#-------------------------------------------------------------------------------
parentclass=vcal.VCalendarImportData
class iCalendarImportData(parentclass):

    def __init__(self, file_name=None):
        super(iCalendarImportData, self).__init__(file_name)

    def _conv_alarm(self, v, dd):
        # return True if there's valid alarm and set dd['alarm_value']
        # False otherwise
        # Only supports negative alarm duration value.
        try:
            _params=v.get('params', {})
            if _params.get('RELATED', None)=='END':
                return False
            if _params.get('VALUE', 'DURATION')!='DURATION':
                return False
            _d=Duration(v)
            if _d.get()>0:
                return False
            dd['alarm_value']=abs(_d.get()/60)
            return True
        except:
            if __debug__:
                raise
            return False

    def _conv_valarm(self, v, dd):
        # convert a VALARM block to alarm value, if available/applicable
        if v.get('value', None)!='VALARM':
            return False
        _trigger=v.get('params', {}).get('TRIGGER', None)
        if _trigger:
            return self._conv_alarm(_trigger, dd)
        return False
        
    def _conv_duration(self, v, dd):
        # compute the 'end' date based on the duration
        return (datetime.datetime(*dd['start'])+\
                datetime.timedelta(seconds=Duration(v).get())).timetuple()[:5]

    def _conv_date(self, v, dd):
        if v.get('params', {}).get('VALUE', None)=='DATE':
            # allday event
            dd['allday']=True
        return bptime.BPTime(v['value']).get()

    # building repeat data
    def _build_value_dict(self, data):
        _value={}
        for _item in data.get('value', '').split(';'):
            _l=_item.split('=')
            if len(_l)>1:
                _value[_l[0]]=_l[1].split(',')
            else:
                _value[_l[0]]=[]
        return _value

    _sorted_weekdays=['FR', 'MO', 'TH', 'TU', 'WE']
    _dow_bitmap={
        'SU': 1,
        'MO': 2,
        'TU': 4,
        'WE': 8,
        'TH': 0x10,
        'FR': 0x20,
        'SA': 0x40
        }

    def _build_daily(self, value, dd):
        # build a daily repeat event
        dd['repeat_type']='daily'
        # only support either every nth day or every weekday
        # is this every weekday?
        _days=value.get('BYDAY', [])
        _days.sort()
        if _days==self._sorted_weekdays:
            _interval=0
        else:
            try:
                _interval=int(value.get('INTERVAL', [1])[0])
            except ValueError:
                _interval=1
        dd['repeat_interval']=_interval
        return True

    def _build_weekly(self, value, dd):
        # build a weekly repeat event
        dd['repeat_type']='weekly'
        try:
            _interval=int(value.get('INTERVAL', [1])[0])
        except ValueError:
            _interval=1
        dd['repeat_interval']=_interval
        _dow=0
        for _day in value.get('BYDAY', []):
            _dow|=self._dow_bitmap.get(_day, 0)
        dd['repeat_dow']=_dow
        return True

    def _build_monthly(self, value, dd):
        dd['repeat_type']='monthly'
        try:
            _interval2=int(value.get('INTERVAL', [1])[0])
        except ValueError:
            _interval2=1
        dd['repeat_interval2']=_interval2
        # nth day of the month by default
        _nth=0
        _dow=0
        _daystr=value.get('BYDAY', [None])[0]
        if _daystr:
            # every nth day-of-week ie 1st Monday
            _dow=self._dow_bitmap.get(_daystr[-2:], 0)
            _nth=1
            try:
                if len(_daystr)>2:
                    _nth=int(_daystr[:-2])
                elif value.get('BYSETPOS', [None])[0]:
                    _nth=int(value['BYSETPOS'][0])
            except ValueError:
                pass
            if _nth==-1:
                _nth=5
            if _nth<1 or _nth>5:
                _nth=1
        dd['repeat_dow']=_dow
        dd['repeat_interval']=_nth
        return True

    def _build_yearly(self, value, dd):
        dd['repeat_type']='yearly'
        return True

    _funcs={
        'DAILY': _build_daily,
        'WEEKLY': _build_weekly,
        'MONTHLY': _build_monthly,
        'YEARLY': _build_yearly,
        }
    def _conv_repeat(self, v, dd):
        _params=v.get('params', {})
        _value=self._build_value_dict(v)
        _rep=self._funcs.get(
            _value.get('FREQ', [None])[0], lambda *_: False)(self, _value, dd)
        if _rep:
            if _value.get('COUNT', [None])[0]:
                dd['repeat_num']=int(_value['COUNT'][0])
            elif _value.get('UNTIL', [None])[0]:
                dd['repeat_end']=bptime.BPTime(_value['UNTIL'][0]).get()
            dd['repeat_wkst']=_value.get('WKST', ['MO'])[0]
        return _rep

    def _conv_exceptions(self, v, _):
        r=[]
        try:
            _val=v if isinstance(v, (list, tuple)) else [v]
            for _item in _val:
                for n in _item['value'].split(','):
                    r.append(bptime.BPTime(n).get())
            return r
        except:
            if __debug__:
                raise
            return []

    def _conv_start_date(self, v, dd):
        _dt=bptime.BPTime(v['value']).get(default=(0,0,0, None, None))
        if _dt[-1] is None:
            # all day event
            dd['allday']=True
            _dt=_dt[:3]+(0,0)
        return _dt

    def _conv_end_date(self, v, _):
        return bptime.BPTime(v['value']).get(default=(0,0,0, 23,59))

    _calendar_keys=[
        ('CATEGORIES', 'categories', parentclass._conv_cat),
        ('DESCRIPTION', 'notes', parentclass._conv_str),
        ('DTSTART', 'start', _conv_start_date),
        ('DTEND', 'end', _conv_end_date),
        ('DURATION', 'end', _conv_duration),
        ('LOCATION', 'location', parentclass._conv_str),
        ('PRIORITY', 'priority', parentclass._conv_priority),
        ('SUMMARY', 'description', parentclass._conv_str),
        ('RRULE', 'repeat', _conv_repeat),
        ('EXDATE', 'exceptions', _conv_exceptions),
        ('BEGIN-END', 'alarm', _conv_valarm),
        ]

#-------------------------------------------------------------------------------
class iCalImportCalDialog(vcal.VcalImportCalDialog):
    _filetype_label='iCalendar File:'
    _data_type='iCalendar'
    _import_data_class=iCalendarImportData

#------------------------------------------------------------------------------
ExportDialogParent=common_calendar.ExportCalendarDialog
out_line=vcard.out_line

class ExportDialog(ExportDialogParent):
    _default_file_name="calendar.ics"
    _wildcards="ICS files|*.ics"

    def __init__(self, parent, title):
        super(ExportDialog, self).__init__(parent, title)

    def _write_header(self, f):
        f.write(out_line('BEGIN', None, 'VCALENDAR', None))
        f.write(out_line('PRODID', None, '-//BitPim//EN', None))
        f.write(out_line('VERSION', None, '2.0', None))
        f.write(out_line('METHOD', None, 'PUBLISH', None))
    def _write_end(self, f):
        f.write(out_line('END', None, 'VCALENDAR', None))

    def _write_timezone(self, f):
        # write out the timezone info, return a timezone ID
        f.write(out_line('BEGIN', None, 'VTIMEZONE', None))
        _tzid=time.tzname[0].split(' ')[0]
        f.write(out_line('TZID', None, _tzid, None))
        _offset_standard=-((time.timezone/3600)*100+time.timezone%3600)
        _offset_daylight=_offset_standard+100
        # standard part
        f.write(out_line('BEGIN', None, 'STANDARD', None))
        f.write(out_line('DTSTART', None, '20051030T020000', None))
        f.write(out_line('RRULE', None,
                         'FREQ=YEARLY;INTERVAL=1;BYDAY=1SU;BYMONTH=11', None))
        f.write(out_line('TZOFFSETFROM', None,
                         '%05d'%_offset_daylight, None))
        f.write(out_line('TZOFFSETTO', None,
                         '%05d'%_offset_standard, None))
        f.write(out_line('END', None, 'STANDARD', None))
        # daylight part
        f.write(out_line('BEGIN', None, 'DAYLIGHT', None))
        f.write(out_line('DTSTART', None, '20060402T020000', None))
        f.write(out_line('RRULE', None,
                         'FREQ=YEARLY;INTERVAL=1;BYDAY=2SU;BYMONTH=3', None))
        f.write(out_line('TZOFFSETFROM', None,
                         '%05d'%_offset_standard, None))
        f.write(out_line('TZOFFSETTO', None,
                         '%05d'%_offset_daylight, None))
        f.write(out_line('END', None, 'DAYLIGHT', None))
        # all done
        f.write(out_line('END', None, 'VTIMEZONE', None))
        return _tzid

    # support writing to ICS file routines
    def _write_categories(self, keyword, v, *args):
        _cats=[x['category'] for x in v]
        if _cats:
            return out_line(keyword, None, ','.join(_cats), None)
    def _write_string(self, keyword, v, *args):
        if v:
            return out_line(keyword, None, v, None)
    def _write_priority(self, keyword, v, *args):
        if v<1:
            return
        return out_line(keyword, None, '%d'%min(v, 9), None)
    def _write_alarm(self, keyword, v, *args):
        if v<0:
            # No Alarm
            return
        _res=out_line('BEGIN', None, 'VALARM', None)
        _res+=out_line('TRIGGER', None,
                       '-P%dDT%dH%dM'%(v/1440, (v%1440)/60, v%60), None)
        _res+=out_line('ACTION', None, 'AUDIO', None)
        _res+=out_line('END', None, 'VALARM', None)
        return _res
    def _write_times_single(self, keyword, v, event, tzid):
        # write the DTSTART/DTEND property for a single
        # (non-recurrent) event
        _start=bptime.BPTime(event.start)
        _end=bptime.BPTime(event.end)
        if event.allday:
            # all day event
            _params=('VALUE=DATE',)
            _res=out_line('DTSTART', _params,
                          _start.iso_str(no_time=True), None)
            _end+=bptime.timedelta(days=1)
            _res+=out_line('DTEND', _params,
                           _end.iso_str(no_time=True), None)
        else:
            _params=('TZID=%s'%tzid,)
            _res=out_line('DTSTART', _params, _start.iso_str(no_seconds=False), None)
            _res+=out_line('DTEND', _params, _end.iso_str(no_seconds=False), None)
        return _res
    def _write_start(self, event, tzid):
        # write the DTSTART/DURATION property for a recurrent event
        _start=bptime.BPTime(event.start)
        _end=bptime.BPTime(event.end)
        if event.allday:
            # all day event, can only handle sameday allday event (for now)
            _params=('VALUE=DATE',)
            _res=out_line('DTSTART', _params,
                          _start.iso_str(no_time=True), None)
            _end+=bptime.timedelta(days=1)
            _res+=out_line('DTEND', _params,
                           _end.iso_str(no_time=True), None)
        else:
            # can only handle 24hr-long event (for now)
            _new_end=_start+(_end-_start).seconds
            _params=('TZID=%s'%tzid,)
            _res=out_line('DTSTART', _params, _start.iso_str(no_seconds=False), None)
            _res+=out_line('DTEND',  _params, _new_end.iso_str(no_seconds=False), None)
        return _res
    def _write_repeat_daily(self, event, rpt):
        _value=['FREQ=DAILY']
        if not event.open_ended():
            _value.append('UNTIL=%04d%02d%02dT000000Z'%event.end[:3])
        if rpt.interval:
            # every nth day
            _value.append('INTERVAL=%d'%rpt.interval)
        else:
            # weekday
            _value.append('BYDAY=MO,TU,WE,TH,FR')
        return out_line('RRULE', None, ';'.join(_value), None)
    _dow_list=(
        (1, 'SU'), (2, 'MO'), (4, 'TU'), (8, 'WE'), (16, 'TH'),
        (32, 'FR'), (64, 'SA'))
    _dow_wkst={
        1: 'MO', 2: 'TU', 3: 'WE', 4: 'TH', 5: 'FR', 6: 'SA', 7: 'SU' }
    def _write_repeat_weekly(self, event, rpt):
        _dow=rpt.dow
        _byday=','.join([x[1] for x in self._dow_list \
                         if _dow&x[0] ])
        _value=['FREQ=WEEKLY',
                'INTERVAL=%d'%rpt.interval,
                'BYDAY=%s'%_byday,
                'WKST=%s'%self._dow_wkst.get(rpt.weekstart, 'MO')]
        if not event.open_ended():
            _value.append('UNTIL=%04d%02d%02d'%event.end[:3])
        return out_line('RRULE', None, ';'.join(_value), None)
    def _write_repeat_monthly(self, event, rpt):
        _value=['FREQ=MONTHLY',
                'INTERVAL=%d'%rpt.interval2,
                ]
        if not event.open_ended():
            _value.append('UNTIL=%04d%02d%02dT000000Z'%event.end[:3])
        _dow=rpt.dow
        if _dow==0:
            # every n-day of the month
            _value.append('BYMONTHDAY=%d'%event.start[2])
        else:
            # every n-th day-of-week (ie 1st Monday)
            for _entry in self._dow_list:
                if _dow & _entry[0]:
                    _dow_name=_entry[1]
                    break
            if rpt.interval<5:
                _nth=rpt.interval
            else:
                _nth=-1
            _value.append('BYDAY=%d%s'%(_nth, _dow_name))
        return out_line('RRULE', None, ';'.join(_value), None)
    def _write_repeat_yearly(self, event, rpt):
        _value=['FREQ=YEARLY',
                'INTERVAL=1',
                'BYMONTH=%d'%event.start[1],
                'BYMONTHDAY=%d'%event.start[2],
                ]
        if not event.open_ended():
            _value.append('UNTIL=%04d%02d%02dT000000Z'%event.end[:3])
        return out_line('RRULE', None, ';'.join(_value), None)
    def _write_repeat_exceptions(self, event, rpt):
        # write out the exception dates
        return out_line('EXDATE', ('VALUE=DATE',),
                        ','.join([x.iso_str(no_time=True) for x in rpt.suppressed]),
                        None)
    def _write_repeat(self, event):
        _repeat=event.repeat
        _type=_repeat.repeat_type
        if _type:
            _res=getattr(self, '_write_repeat_'+_type, lambda *_: None)(event, _repeat)
            if _res and _repeat.suppressed:
                _res+=self._write_repeat_exceptions(event, _repeat)
            return _res
    def _write_times_repeat(self, keyword, v, event, tzid):
        return self._write_start(event, tzid)+self._write_repeat(event)
    def _write_times(self, keyword, v, event, tzid):
        # write the START and DURATION property
        if event.repeat:
            return self._write_times_repeat(keyword, v, event, tzid)
        else:
            return self._write_times_single(keyword, v, event, tzid)

    _field_list=(
        ('SUMMARY', 'description', _write_string),
        ('DESCRIPTION', 'notes', _write_string),
        ('DTSTART', 'start', _write_times),
        ('LOCATION', 'location', _write_string),
        ('PRIORITY', 'priority', _write_priority),
        ('CATEGORIES', 'categories', _write_categories),
        ('TRIGGER', 'alarm', _write_alarm),
        )

    def _write_event(self, f, event, tzid):
        # write out an BitPim Calendar event
        f.write(out_line('COMMENT', None, '//----------', None))
        f.write(out_line('BEGIN', None, 'VEVENT', None))
        for _entry in self._field_list:
            _v=getattr(event, _entry[1], None)
            if _v is not None:
                _line=_entry[2](self, _entry[0], _v, event, tzid)
                if _line:
                    f.write(_line)
        f.write(out_line('DTSTAMP', None,
                         '%04d%02d%02dT%02d%02d%02dZ'%time.gmtime()[:6],
                         None))
        f.write(out_line('UID', None, event.id, None))
        f.write(out_line('END', None, 'VEVENT', None))
    def _export(self):
        filename=self.filenamectrl.GetValue()
        try:
            f=file(filename, 'wt')
        except:
            f=None
        if f is None:
            guihelper.MessageDialog(self, 'Failed to open file ['+filename+']',
                                    'Export Error')
            return
        all_items=self._selection.GetSelection()==0
        dt=self._start_date.GetValue()
        range_start=(dt.GetYear(), dt.GetMonth()+1, dt.GetDay())
        dt=self._end_date.GetValue()
        range_end=(dt.GetYear(), dt.GetMonth()+1, dt.GetDay())
        cal_dict=self.GetParent().GetCalendarData()
        self._write_header(f)
        _tzid=self._write_timezone(f)
        # now go through the data and export each event
        for k,e in cal_dict.items():
            if not all_items and \
               (e.end < range_start or e.start>range_end):
                continue
            self._write_event(f, e, _tzid)
        self._write_end(f)
        f.close()
