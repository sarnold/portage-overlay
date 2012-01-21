#!/usr/bin/env python
### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: bpcalendar.py 4706 2008-09-03 21:40:23Z djpham $

"""Calendar user interface and data for bitpim.

This module has a bp prefix so it doesn't clash with the system calendar module

Version 3:

The format for the calendar is standardised.  It is a dict with the following
fields:
(Note: hour fields are in 24 hour format)
'string id': CalendarEntry object.

CalendarEntry properties:
description - 'string description'
location - 'string location'
desc_loc - combination of description & location in the form of 'description[location]'
priority - None=no priority, int from 1-10, 1=highest priority
alarm - how many minutes beforehand to set the alarm (use 0 for on-time, None or -1 for no alarm)
allday - True for an allday event, False otherwise
start - (year, month, day, hour, minute) as integers
end - (year, month, day, hour, minute) as integers
serials - list of dicts of serials.
repeat - None, or RepeatEntry object
id - string id of this object.  Created the same way as bpserials IDs for phonebook entries.
notes - string notes
categories - [ { 'category': string category }, ... ]
ringtone - string ringtone assignment
wallpaper - string wallpaper assignment.
vibrate - True if the alarm is set to vibrate, False otherwise
voice - ID of voice alarm

CalendarEntry methods:
get() - return a copy of the internal dict
get_db_dict()- return a copy of a database.basedataobject dict.
set(dict) - set the internal dict with the supplied dict
set_db_dict(dict) - set internal data with the database.basedataobject dict
is_active(y, m, d) - True if this event is active on (y,m,d)
suppress_repeat_entry(y,m,d) - exclude (y,m,d) from this repeat event.

RepeatEntry properties:
repeat_type - one of daily, weekly, monthly, or yearly.
interval - for daily: repeat every nth day.  For weekly, for every nth week.
interval2 - for monhtly: repeat every nth month.
dow - bitmap of which day of week are being repeated.
weekstart - the start of the work week ('MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU')
suppressed - list of (y,m,d) being excluded from this series.

--------------------------------------------------------------------------------
Version 2:

The format for the calendar is standardised.  It is a dict with the following
fields:

(Note: hour fields are in 24 hour format)

start:

   - (year, month, day, hour, minute) as integers
end:

   - (year, month, day, hour, minute) as integers  # if you want no end, set to the same value as start, or to the year 4000

repeat:

   - one of None, "daily", "monfri", "weekly", "monthly", "yearly"

description:

   - "String description"
   
changeserial:

   - Set to integer 1
   
snoozedelay:

   - Set to an integer number of minutes (default 0)
   
alarm:

   - how many minutes beforehand to set the alarm (use 0 for on-time, None for no alarm)
   
daybitmap:

   - default 0, it will become which days of the week weekly events happen on (eg every monday and friday)
   
ringtone:

   - index number of the ringtone for the alarm (use 0 for none - will become a string)
   
pos:

   - integer that should be the same as the dictionary key for this entry
   
exceptions:

   - (optional) A list of (year,month,day) tuples that repeats are suppressed
"""

# Standard modules
from __future__ import with_statement
import os
import copy
import calendar
import datetime
import random
import sha
import time

# wx stuff
import wx
import wx.lib
import wx.lib.masked.textctrl
import wx.lib.intctrl
import wx.grid as gridlib

# my modules
import bphtml
import bptime
import calendarcontrol
import calendarentryeditor
import common
import database
import guihelper
import guiwidgets
import helpids
import pubsub
import today
import xyaptu

#-------------------------------------------------------------------------------
class CalendarDataObject(database.basedataobject):
    """
    This class is a wrapper class to enable CalendarEntry object data to be
    stored in the database stuff.  Once the database module is updated, this
    class will also be updated and eventually replace CalendarEntry.
    """
    _knownproperties=['description', 'location', 'priority', 'alarm',
                      'notes', 'ringtone', 'wallpaper',
                      'start', 'end', 'vibrate', 'voice' ]
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    _knownlistproperties.update( {
                                  'repeat': ['type', 'interval',
                                             'interval2', 'dow', 'weekstart'],
                                  'suppressed': ['date'],
                                  'categories': ['category'] })
    def __init__(self, data=None):
        if data is None or not isinstance(data, CalendarEntry):
            # empty data, do nothing
            return
        self.update(data.get_db_dict())

calendarobjectfactory=database.dataobjectfactory(CalendarDataObject)
#-------------------------------------------------------------------------------
class RepeatEntry(object):
    # class constants
    daily='daily'
    weekly='weekly'
    monthly='monthly'
    yearly='yearly'
    _interval=0
    _dow=1
    _dom=0
    _moy=1
    _interval2=2
    _dow_names=(
        {1: 'Sun'}, {2: 'Mon'}, {4: 'Tue'}, {8: 'Wed'},
        {16: 'Thu'}, {32: 'Fri'}, {64: 'Sat'})
    # this faster than log2(x)
    _dow_num={ 1: wx.DateTime.Sun,
               2: wx.DateTime.Mon,
               4: wx.DateTime.Tue,
               8: wx.DateTime.Wed,
               16: wx.DateTime.Thu,
               32: wx.DateTime.Fri,
               64: wx.DateTime.Sat }
    dow_names={ 'Sun': 1, 'Mon': 2, 'Tue': 4, 'Wed': 8,
                'Thu': 16, 'Fri': 32, 'Sat': 64 }
    dow_weekday=0x3E
    dow_weekend=0x41
    dow_weekstart={
        'SU': 7, 'MO': 1, 'TU': 2, 'WE': 3, 'TH': 4, 'FR': 5, 'SA': 6 }

    def __init__(self, repeat_type=daily):
        self._type=repeat_type
        self._data=[0,0,0]
        self._suppressed=[]
        self._wkstart=7 # default to Sun

    def __eq__(self, rhs):
        # return T if equal
        if not isinstance(rhs, RepeatEntry):
            return False
        if self.repeat_type!=rhs.repeat_type:
            return False
        if self.repeat_type==RepeatEntry.daily:
            if self.interval!=rhs.interval:
                return False
        elif self.repeat_type==RepeatEntry.weekly:
            if self.interval!=rhs.interval or \
               self.dow!=rhs.dow:
                return False
        elif self.repeat_type==RepeatEntry.monthly:
            if self.interval!=rhs.interval or \
               self.interval2!=rhs.interval2 or \
               self.dow!=rhs.dow:
                return False
        return True
    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def get(self):
        # return a dict representing internal data
        # mainly used for populatefs
        r={}
        if self._type==self.daily:
            r[self.daily]= { 'interval': self._data[self._interval] }
        elif self._type==self.weekly:
            r[self.weekly]= { 'interval': self._data[self._interval],
                              'dow': self._data[self._dow] }
        elif self._type==self.monthly:
            r[self.monthly]={ 'interval': self._data[self._interval],
                              'interval2': self._data[self._interval2],
                              'dow': self._data[self._dow] }
        else:
            r[self.yearly]=None
        s=[]
        for n in self._suppressed:
            s.append(n.get())
        r['suppressed']=s
        return r

    def get_db_dict(self):
        # return a copy of the dict compatible with the database stuff
        db_r={}
        r={}
        r['type']=self._type
        r['weekstart']=self.weekstart
        if self._type==self.daily:
            r['interval']=self._data[self._interval]
        elif self._type==self.weekly or self._type==self.monthly:
            r['interval']=self._data[self._interval]
            r['dow']=self._data[self._dow]
            if self._type==self.monthly:
                r['interval2']=self._data[self._interval2]
        # and the suppressed stuff
        s=[]
        for n in self._suppressed:
            s.append({ 'date': n.iso_str(True) })
        db_r['repeat']=[r]
        if len(s):
            db_r['suppressed']=s
        return db_r

    def set(self, data):
        # setting data from a dict, mainly used for getfromfs
        if data.has_key(self.daily):
            # daily type
            self.repeat_type=self.daily
            self.interval=data[self.daily]['interval']
        elif data.has_key(self.weekly):
            # weekly type
            self.repeat_type=self.weekly
            self.interval=data[self.weekly]['interval']
            self.dow=data[self.weekly]['dow']
        elif data.has_key(self.monthly):
            self.repeat_type=self.monthly
            self.dow=data[self.monthly].get('dow', 0)
            self.interval=data[self.monthly].get('interval', 0)
            self.interval2=data[self.monthly].get('interval2', 1)
        else:
            self.repeat_type=self.yearly
        s=[]
        for n in data.get('suppressed', []):
            s.append(bptime.BPTime(n))
        self.suppressed=s

    def set_db_dict(self, data):
        r=data.get('repeat', [{}])[0]
        self.repeat_type=r['type']
        _dow=r.get('dow', 0)
        _interval=r.get('interval', 0)
        self.weekstart=r.get('weekstart', 'SU')
        if self.repeat_type==self.daily:
            self.interval=_interval
        elif self.repeat_type==self.weekly or self.repeat_type==self.monthly:
            self.interval=_interval
            self.dow=_dow
            if self.repeat_type==self.monthly:
                self.interval2=r.get('interval2', 1)
        # now the suppressed stuff
        s=[]
        for n in data.get('suppressed', []):
            s.append(bptime.BPTime(n['date']))
        self.suppressed=s

    def get_nthweekday(self, date):
        """Utility routine: return the nth weekday of the specified date"""
        _wxmonth=date[1]-1
        _year=date[0]
        _day=date[2]
        _dt=wx.DateTimeFromDMY(_day, _wxmonth, _year)
        _dt.SetToWeekDay(_dt.GetWeekDay(), 1, _wxmonth, _year)
        return (_day-_dt.GetDay())/7+1

    def _check_daily(self, s, d):
        if self.interval:
            # every nth day
            return (int((d-s).days)%self.interval)==0
        else:
            # every weekday
            return d.weekday()<5
    def _next_daily(self, ymd):
        """Return the date (y,m,d) of the next occurrence of this event"""
        _d0=datetime.date(*ymd)
        if self.interval:
            # every nth day:
            _delta=self.interval
        else:
            # every weekday
            if _d0.isoweekday()<5:
                # next weekday
                _delta=1
            else:
                # the following Monday
                _delta=3
        _d1=_d0+datetime.timedelta(days=_delta)
        return (_d1.year, _d1.month, _d1.day)

    def _weekof(self, d):
        # return the date of the start of the week into which that d falls.
        _workweek=self.weekstart
        _dow=d.isoweekday()
        return d-datetime.timedelta((_dow-_workweek) if _dow>=_workweek \
                                    else (_dow+7-_workweek))

    def _check_weekly(self, s, d):
        # check if at least one day-of-week is specified, if not default to the
        # start date
        if self.dow==0:
            self.dow=1<<(s.isoweekday()%7)
        # check to see if this is the nth week
        day_of_week=d.isoweekday()%7  # Sun=0, ..., Sat=6
        if ((self._weekof(d)-self._weekof(s)).days/7)%self.interval:
            # wrong week
            return False
        # check for the right weekday
        return ((1<<day_of_week)&self.dow) != 0
    def _next_weekly(self, ymd):
        """Return the next occurrence of this event from ymd date"""
        _oneday=datetime.timedelta(days=1)
        _d0=datetime.date(*ymd)+_oneday
        _dowbit=1<<(_d0.isoweekday()%7)
        while _dowbit!=1:
            if self.dow&_dowbit:
                return (_d0.year, _d0.month, _d0.day)
            _dowbit<<=1
            if _dowbit==128:
                _dowbit=1
            _d0+=_oneday
        _delta=(self.interval-1)*7
        _d0+=datetime.timedelta(days=_delta)
        while _dowbit!=128:
            if self.dow&_dowbit:
                return (_d0.year, _d0.month, _d0.day)
            _dowbit<<=1
            _d0+=_oneday

    def _check_monthly(self, s, d):
        if not self.interval2:
            # default to every month
            self.interval2=1
        if d.month>=s.month:
            if (d.month-s.month)%self.interval2:
                # wrong month
                return False
        elif (12+d.month-s.month)%self.interval2:
            return False
        if self.dow==0:
            # no weekday specified, implied nth day of the month
            return d.day==s.day
        else:
            # every interval-th dow-day (ie 1st Mon) of the month
            _dow=(1<<(d.isoweekday()%7))&self.dow
            if not _dow:
                # not even the right day-of-week
                return False
            dt=wx.DateTime.Now()
            if self.interval<5:
                # nth *day of the month
                _nth=self.interval
            else:
                # last *day of the month
                _nth=-1
            return dt.SetToWeekDay(self._dow_num[_dow],
                                   _nth, month=d.month-1, year=d.year) and \
                                   dt.GetDay()==d.day
    def _next_monthly(self, ymd):
        """Return the date of the next occurrence of this event"""
        _day=ymd[2]
        _month=ymd[1]+self.interval2
        if _month%12:
            _year=ymd[0]+_month/12
            _month=_month%12
        else:
            _year=ymd[0]+_month/12-1
            _month=12
        _d1=datetime.date(_year, _month, _day)
        if self.dow==0:
            # nth day of the month
            return (_d1.year, _d1.month, _d1.day)
        else:
            # every interval-th dow-day (ie 1st Mon) of the month
            if self.interval<5:
                # nth *day of the month
                _nth=self.interval
            else:
                # last *day of the month
                _nth=-1
            _dt=wx.DateTime()
            _dt.SetToWeekDay(self._dow_num[self.dow], _nth, month=_d1.month-1,
                             year=_d1.year)
            return (_dt.GetYear(), _dt.GetMonth()+1, _dt.GetDay())

    def _check_yearly(self, s, d):
        return d.month==s.month and d.day==s.day
    def _next_yearly(self, ymd):
        """Return the date of the next occurrence of this event"""
        return (ymd[0]+1, ymd[1], ymd[2])

    def is_active(self, s, d):
        # check in the suppressed list
        if bptime.BPTime(d) in self._suppressed:
            # in the list, not part of this repeat
            return False
        # determine if the date is active
        if self.repeat_type==self.daily:
            return self._check_daily(s, d)
        elif self.repeat_type==self.weekly:
            return self._check_weekly(s, d)
        elif self.repeat_type==self.monthly:
            return self._check_monthly(s, d)
        elif self.repeat_type==self.yearly:
            return self._check_yearly(s, d)
        else:
            return False

    def next_date(self, ymd):
        """Return the date of the next occurrence of this event"""
        if self.repeat_type==self.daily:
            return self._next_daily(ymd)
        elif self.repeat_type==self.weekly:
            return self._next_weekly(ymd)
        elif self.repeat_type==self.monthly:
            return self._next_monthly(ymd)
        else:
            return self._next_yearly(ymd)

    def _get_type(self):
        return self._type
    def _set_type(self, repeat_type):
        if repeat_type in (self.daily, self.weekly,
                    self.monthly, self.yearly):
            self._type = repeat_type
        else:
            raise AttributeError, 'type'
    repeat_type=property(fget=_get_type, fset=_set_type)
    
    def _get_interval(self):
        if self._type==self.yearly:
            raise AttributeError
        return self._data[self._interval]
    def _set_interval(self, interval):
        if self._type==self.yearly:
            raise AttributeError
        self._data[self._interval]=interval
    interval=property(fget=_get_interval, fset=_set_interval)

    def _get_interval2(self):
        if self._type==self.yearly:
            raise AttributeError
        return self._data[self._interval2]
    def _set_interval2(self, interval):
        if self._type==self.yearly:
            raise AttributeError
        self._data[self._interval2]=interval
    interval2=property(fget=_get_interval2, fset=_set_interval2)

    def _get_dow(self):
        if self._type==self.yearly:
            raise AttributeError
        return self._data[self._dow]
    def _set_dow(self, dow):
        if self._type==self.yearly:
            raise AttributeError
        if isinstance(dow, (int, long)):
            self._data[self._dow]=int(dow)
        elif isinstance(dow, (list, tuple)):
            self._data[self._dow]=1<<(datetime.date(*dow[:3]).isoweekday()%7)
        else:
            raise TypeError,"Must be an int or a list/tuple"
    dow=property(fget=_get_dow, fset=_set_dow)
    def _get_dow_str(self):
        try:
            _dow=self.dow
        except AttributeError:
            return ''
        names=[]
        for l in self._dow_names:
            for k,e in l.items():
                if k&_dow:
                    names.append(e)
        return ';'.join(names)
    dow_str=property(fget=_get_dow_str)

    def _get_wkstart(self):
        return self._wkstart
    def _set_wkstart(self, wkstart):
        if isinstance(wkstart, (int, long)):
            if wkstart in range(1, 8):
                self._wkstart=int(wkstart)
            else:
                raise ValueError('Must be between 1-7')
        elif isinstance(wkstart, (str, unicode)):
            self._wkstart=self.dow_weekstart.get(str(wkstart.upper()), 7)
        else:
            raise TypeError("Must be either a string or int")
    weekstart=property(fget=_get_wkstart, fset=_set_wkstart)

    def _get_suppressed(self):
        return self._suppressed
    def _set_suppressed(self, d):
        if not isinstance(d, list):
            raise TypeError, 'must be a list of string or BPTime'
        if not len(d) or isinstance(d[0], bptime.BPTime):
            # empty list or already a list of BPTime
            self._suppressed=d
        elif isinstance(d[0], str):
            # list of 'yyyy-mm-dd'
            self._suppressed=[]
            for n in d:
                self._suppressed.append(bptime.BPTime(n.replace('-', '')))
    def add_suppressed(self, y, m, d):
        self._suppressed.append(bptime.BPTime((y, m, d)))
    def get_suppressed_list(self):
        return [x.date_str() for x in self._suppressed]
    suppressed=property(fget=_get_suppressed, fset=_set_suppressed)
    def _get_suppressed_str(self):
        return ';'.join(self.get_suppressed_list())
    suppressed_str=property(fget=_get_suppressed_str)

#-------------------------------------------------------------------------------
class CalendarEntry(object):
    # priority const
    priority_high=1
    priority_normal=5
    priority_low=10
    # no end date
    no_end_date=(4000, 1, 1)
    # required and optional attributes, mainly used for comparison
    _required_attrs=('description', 'start','end')
    _required_attr_names=('Description', 'Start', 'End')
    _optional_attrs=('location', 'priority', 'alarm', 'allday', 'vibrate',
                     'voice', 'repeat', 'notes', 'categories',
                     'ringtone', 'wallpaper')
    _optional_attr_names=('Location', 'Priority', 'Alarm', 'All-Day',
                          'Vibrate', '', 'Repeat', 'Notes', 'Categories',
                          'Ringtone', 'Wallpaper')
    def __init__(self, year=None, month=None, day=None):
        self._data={}
        # setting default values
        if day is not None:
            self._data['start']=bptime.BPTime((year, month, day))
            self._data['end']=bptime.BPTime((year, month, day))
        else:
            self._data['start']=bptime.BPTime()
            self._data['end']=bptime.BPTime()
        self._data['serials']=[]
        self._create_id()

    def matches(self, rhs):
        # Match self against this entry, which may not have all the
        # optional attributes
        if not isinstance(rhs, CalendarEntry):
            return False
        for _attr in CalendarEntry._required_attrs:
            if getattr(self, _attr) != getattr(rhs, _attr):
                return False
        for _attr in CalendarEntry._optional_attrs:
            _rhs_attr=getattr(rhs, _attr)
            if _rhs_attr is not None and getattr(self, _attr)!=_rhs_attr:
                return False
        return True
    def get_changed_fields(self, rhs):
        # Return a CSV string of all the fields having different values
        if not isinstance(rhs, CalendarEntry):
            return ''
        _res=[]
        for _idx,_attr in enumerate(CalendarEntry._required_attrs):
            if getattr(self, _attr) != getattr(rhs, _attr):
                _res.append(CalendarEntry._required_attr_names[_idx])
        for _idx,_attr in enumerate(CalendarEntry._optional_attrs):
            _rhs_attr=getattr(rhs, _attr)
            if _rhs_attr is not None and getattr(self, _attr)!=_rhs_attr:
                _res.append(CalendarEntry._optional_attr_names[_idx])
        return ','.join(_res)

    def similar(self, rhs):
        # return T if rhs is similar to self
        # for now, they're similar if they have the same start time
        return self.start==rhs.start

    def replace(self, rhs):
        # replace the contents of this entry with the new one
        for _attr in CalendarEntry._required_attrs+\
            CalendarEntry._optional_attrs:
            _rhs_attr=getattr(rhs, _attr)
            if _rhs_attr is not None:
                setattr(self, _attr, _rhs_attr)

    def __eq__(self, rhs):
        if not isinstance(rhs, CalendarEntry):
            return False
        for _attr in CalendarEntry._required_attrs+CalendarEntry._optional_attrs:
            if getattr(self, _attr)!=getattr(rhs, _attr):
                return False
        return True
    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def get(self):
        r=copy.deepcopy(self._data, _nil={})
        if self.repeat is not None:
            r['repeat']=self.repeat.get()
        r['start']=self._data['start'].iso_str()
        r['end']=self._data['end'].iso_str()
        return r

    def get_db_dict(self):
        # return a dict compatible with the database stuff
        r=copy.deepcopy(self._data, _nil={})
        # adjust for start & end
        r['start']=self._data['start'].iso_str(self.allday)
        r['end']=self._data['end'].iso_str(self.allday)
        # adjust for repeat & suppressed
        if self.repeat is not None:
            r.update(self.repeat.get_db_dict())
        # take out uneeded keys
        if r.has_key('allday'):
            del r['allday']
        return r

    def set(self, data):
        self._data={}
        self._data.update(data)
        self._data['start']=bptime.BPTime(data['start'])
        self._data['end']=bptime.BPTime(data['end'])
        if self.repeat is not None:
            r=RepeatEntry()
            r.set(self.repeat)
            self.repeat=r
        # try to clean up the dict
        for k, e in self._data.items():
            if e is None or e=='' or e==[]:
                del self._data[k]

    def set_db_dict(self, data):
        # update our data with dict return from database
        self._data={}
        self._data.update(data)
        # adjust for allday
        self.allday=len(data['start'])==8
        # adjust for start and end
        self._data['start']=bptime.BPTime(data['start'])
        self._data['end']=bptime.BPTime(data['end'])
        # adjust for repeat
        if data.has_key('repeat'):
            rp=RepeatEntry()
            rp.set_db_dict(data)
            self.repeat=rp

    def is_active(self, y, m ,d):
        # return true if if this event is active on this date,
        # mainly used for repeating events.
        s=self._data['start'].date
        e=self._data['end'].date
        d=datetime.date(y, m, d)
        if d<s or d>e:
            # before start date, after end date
            return False
        if self.repeat is None:
            # not a repeat event, within range so it's good
            return True
        # repeat event: check if it's in range.
        return self.repeat.is_active(s, d)

    def suppress_repeat_entry(self, y, m, d):
        if self.repeat is None:
            # not a repeat entry, do nothing
            return
        self.repeat.add_suppressed(y, m, d)

    def _set_or_del(self, key, v, v_list=()):
        if v is None or v in v_list:
            if self._data.has_key(key):
                del self._data[key]
        else:
            self._data[key]=v
        
    def _get_description(self):
        return self._data.get('description', '')
    def _set_description(self, desc):
        self._set_or_del('description', desc, ('',))
    description=property(fget=_get_description, fset=_set_description)

    def _get_location(self):
        return self._data.get('location', '')
    def _set_location(self, location):
        self._set_or_del('location', location, ('',))
    location=property(fget=_get_location, fset=_set_location)

    def _get_desc_loc(self):
        # return 'description[location]'
        if self.location:
            return self.description+'['+self.location+']'
        return self.description
    def _set_desc_loc(self, v):
        # parse and set for 'description[location]'
        _idx1=v.find('[')
        _idx2=v.find(']')
        if _idx1!=-1 and _idx2!=-1 and _idx2>_idx1:
            # location specified
            self.location=v[_idx1+1:_idx2]
            self.description=v[:_idx1]
        else:
            self.description=v
    desc_loc=property(fget=_get_desc_loc, fset=_set_desc_loc)

    def _get_priority(self):
        return self._data.get('priority', None)
    def _set_priority(self, priority):
        self._set_or_del('priority', priority)
    priority=property(fget=_get_priority, fset=_set_priority)

    def _get_alarm(self):
        return self._data.get('alarm', -1)
    def _set_alarm(self, alarm):
        self._set_or_del('alarm', alarm)
    alarm=property(fget=_get_alarm, fset=_set_alarm)

    def _get_allday(self):
        return self._data.get('allday', False)
    def _set_allday(self, allday):
        self._data['allday']=allday
    allday=property(fget=_get_allday, fset=_set_allday)

    def _get_start(self):
        return self._data['start'].get()
    def _set_start(self, datetime):
        self._data['start'].set(datetime)
    start=property(fget=_get_start, fset=_set_start)
    def _get_start_str(self):
        return self._data['start'].date_str()+' '+\
               self._data['start'].time_str(False, '00:00')
    start_str=property(fget=_get_start_str)
    
    def _get_end(self):
        return self._data['end'].get()
    def _set_end(self, datetime):
        self._data['end'].set(datetime)
    end=property(fget=_get_end, fset=_set_end)
    def _get_end_str(self):
        return self._data['end'].date_str()+' '+\
               self._data['end'].time_str(False, '00:00')
    end_str=property(fget=_get_end_str)
    def open_ended(self):
        # True if this is an open-ended event
        return self.end[:3]==self.no_end_date

    def _get_vibrate(self):
        return self._data.get('vibrate', 0)
    def _set_vibrate(self, v):
        self._set_or_del('vibrate', v, (None, 0, False))
    vibrate=property(fget=_get_vibrate, fset=_set_vibrate)

    def _get_voice(self):
        return self._data.get('voice', None)
    def _set_voice(self, v):
        self._set_or_del('voice', v, (None,))
    voice=property(fget=_get_voice, fset=_set_voice)

    def _get_serials(self):
        return self._data.get('serials', None)
    def _set_serials(self, serials):
        self._data['serials']=serials
    serials=property(fget=_get_serials, fset=_set_serials)

    def _get_repeat(self):
        return self._data.get('repeat', None)
    def _set_repeat(self, repeat):
        self._set_or_del('repeat', repeat)
    repeat=property(fget=_get_repeat, fset=_set_repeat)

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

    def _get_notes(self):
        return self._data.get('notes', '')
    def _set_notes(self, s):
        self._set_or_del('notes', s, ('',))
    notes=property(fget=_get_notes, fset=_set_notes)

    def _get_categories(self):
        return self._data.get('categories', [])
    def _set_categories(self, s):
        self._set_or_del('categories', s,([],))
        if s==[] and self._data.has_key('categories'):
            del self._data['categories']
    categories=property(fget=_get_categories, fset=_set_categories)
    def _get_categories_str(self):
        c=self.categories
        if len(c):
            return ';'.join([x['category'] for x in c])
        else:
            return ''
    categories_str=property(fget=_get_categories_str)

    def _get_ringtone(self):
        return self._data.get('ringtone', '')
    def _set_ringtone(self, rt):
        self._set_or_del('ringtone', rt, ('',))
    ringtone=property(fget=_get_ringtone, fset=_set_ringtone)

    def _get_wallpaper(self):
        return self._data.get('wallpaper', '',)
    def _set_wallpaper(self, wp):
        self._set_or_del('wallpaper', wp, ('',))
    wallpaper=property(fget=_get_wallpaper, fset=_set_wallpaper)

    # we use two random numbers to generate the serials.  _persistrandom
    # is seeded at startup
    _persistrandom=random.Random()
    def _create_id(self):
        "Create a BitPim serial for this entry"
        rand2=random.Random() # this random is seeded when this function is called
        num=sha.new()
        num.update(`self._persistrandom.random()`)
        num.update(`rand2.random()`)
        self._data["serials"].append({"sourcetype": "bitpim", "id": num.hexdigest()})

    def _get_print_data(self):
        """ return a list of strings used for printing this event:
        [0]: start time, [1]: '', [2]: end time, [3]: Description
        [4]: Repeat Type, [5]: Alarm
        """
        if self.allday:
            t0='All Day'
            t1=''
        else:
            t0=self._data['start'].time_str()
            t1=self._data['end'].time_str()
        rp=self.repeat
        if rp is None:
            rp_str=''
        else:
            rp_str=rp.repeat_type[0].upper()
        if self.alarm==-1:
            alarm_str=''
        else:
            alarm_str='%d:%02d'%(self.alarm/60, self.alarm%60)
        return [t0, '', t1, self.description, rp_str, alarm_str]
    print_data=property(fget=_get_print_data)
    @classmethod
    def cmp_by_time(cls, a, b):
        """ compare 2 objects by start times.
        -1 if a<b, 0 if a==b, and 1 if a>b
        allday is always less than having start times.
        Mainly used for sorting list of events
        """
        if not isinstance(a, cls) or \
           not isinstance(b, cls):
            raise TypeError, 'must be a CalendarEntry object'
        if a.allday and b.allday:
            return 0
        if a.allday and not b.allday:
            return -1
        if not a.allday and b.allday:
            return 1
        t0=a.start[3:]
        t1=b.start[3:]
        if t0<t1:
            return -1
        if t0==t1:
            return 0
        if t0>t1:
            return 1

    def _summary(self):
        # provide a one-liner summary string for this event
        if self.allday:
            str=self.description
        else:
            hr=self.start[3]
            ap="am"
            if hr>=12:
                ap="pm"
                hr-=12
            if hr==0: hr=12
            str="%2d:%02d %s" % (hr, self.start[4], ap)
            str+=" "+self.description
        return str
    summary=property(fget=_summary)


#-------------------------------------------------------------------------------
class Calendar(calendarcontrol.Calendar):
    """A class encapsulating the GUI and data of the calendar (all days).  A seperate dialog is
    used to edit the content of one particular day."""

    CURRENTFILEVERSION=3
    
    def __init__(self, mainwindow, parent, id=-1):
        """constructor

        @type  mainwindow: gui.MainWindow
        @param mainwindow: Used to get configuration data (such as directory to save/load data.
        @param parent:     Widget acting as parent for this one
        @param id:         id
        """
        self.mainwindow=mainwindow
        self.entrycache={}
        self.entries={}
        self.repeating=[]  # nb this is stored unsorted
        self._data={} # the underlying data
        calendarcontrol.Calendar.__init__(self, parent, rows=5, id=id)
        self.dialog=calendarentryeditor.Editor(self)
        pubsub.subscribe(self.OnMediaNameChanged, pubsub.MEDIA_NAME_CHANGED)
        today.bind_notification_event(self.OnTodayItem,
                                      today.Today_Group_Calendar)
        today.bind_request_event(self.OnTodayRequest)
        pubsub.subscribe(self.OnTodayButton, pubsub.MIDNIGHT)

    def OnPrintDialog(self, mainwindow, config):
        with guihelper.WXDialogWrapper(CalendarPrintDialog(self, mainwindow, config),
                                       True):
            pass
    def CanPrint(self):
        return True

    def OnMediaNameChanged(self, msg):
        d=msg.data
        _type=d.get(pubsub.media_change_type, None)
        _old_name=d.get(pubsub.media_old_name, None)
        _new_name=d.get(pubsub.media_new_name, None)
        if _type is None or _old_name is None or _new_name is None:
            # invalid/incomplete data
            return
        if _type!=pubsub.wallpaper_type and \
           _type!=pubsub.ringtone_type:
            # neither wallpaper nor ringtone
            return
        _old_name=common.basename(_old_name)
        _new_name=common.basename(_new_name)
        if _type==pubsub.wallpaper_type:
            attr_name='wallpaper'
        else:
            attr_name='ringtone'
        modified=False
        for k,e in self._data.items():
            if getattr(e, attr_name, None)==_old_name:
                setattr(e, attr_name, _new_name)
                modified=True
        if modified:
            # changes were made, update everything
            self.updateonchange()

    def getdata(self, dict):
        """Return underlying calendar data in bitpim format

        @return:   The modified dict updated with at least C{dict['calendar']}"""
        if dict.get('calendar_version', None)==2:
            # return a version 2 dict
            dict['calendar']=self._convert3to2(self._data,
                                                dict.get('ringtone-index', None))
        else:
            dict['calendar']=copy.deepcopy(self._data, _nil={})
        return dict

    def updateonchange(self):
        """Called when our data has changed

        The disk, widget and display are all updated with the new data"""
        d={}
        d=self.getdata(d)
        self.populatefs(d)
        self.populate(d)
        # Brute force - assume all entries have changed
        self.RefreshAllEntries()

    def AddEntry(self, entry):
        """Adds and entry into the calendar data.

        The entries on disk are updated by this function.

        @type  entry: a dict containing all the fields.
        @param entry: an entry.  It must contain a C{pos} field. You
                     should call L{newentryfactory} to make
                     an entry that you then modify
        """
        self._data[entry.id]=entry
        self.updateonchange()

    def DeleteEntry(self, entry):
        """Deletes an entry from the calendar data.

        The entries on disk are updated by this function.

        @type  entry: a dict containing all the fields.
        @param entry: an entry.  It must contain a C{pos} field
                      corresponding to an existing entry
        """
        del self._data[entry.id]
        self.updateonchange()

    def DeleteEntryRepeat(self, entry, year, month, day):
        """Deletes a specific repeat of an entry
        See L{DeleteEntry}"""
        self._data[entry.id].suppress_repeat_entry(year, month, day)
        self.updateonchange()
        
    def ChangeEntry(self, oldentry, newentry):
        """Changes an entry in the calendar data.

        The entries on disk are updated by this function.
        """
        assert oldentry.id==newentry.id
        self._data[newentry.id]=newentry
        self.updateonchange()

    def getentrydata(self, year, month, day):
        """return the entry objects for corresponding date

        @rtype: list"""
        # return data from cache if we have it
        res=self.entrycache.get( (year,month,day), None)
        if res is not None:
            return res
        # find non-repeating entries
        res=self.entries.get((year,month,day), [])
        for i in self.repeating:
            if i.is_active(year, month, day):
                res.append(i)
        self.entrycache[(year,month,day)] = res
        return res
        
    def newentryfactory(self, year, month, day):
        """Returns a new 'blank' entry with default fields

        @rtype: CalendarEntry
        """
        # create a new entry
        res=CalendarEntry(year, month, day)
        # fill in default start & end data
        now=time.localtime()
        event_start=(year, month, day, now.tm_hour, now.tm_min)
        event_end=[year, month, day, now.tm_hour, now.tm_min]
        # we make end be the next hour, unless it has gone 11pm
        # in which case it is 11:59pm
        if event_end[3]<23:
            event_end[3]+=1
            event_end[4]=0
        else:
            event_end[3]=23
            event_end[4]=59
        res.start=event_start
        res.end=event_end
        res.description='New Event'
        return res

    def getdaybitmap(self, start, repeat):
        if repeat!="weekly":
            return 0
        dayofweek=calendar.weekday(*(start[:3]))
        dayofweek=(dayofweek+1)%7 # normalize to sunday == 0
        return [2048,1024,512,256,128,64,32][dayofweek]

    def OnGetEntries(self, year, month, day):
        """return pretty printed sorted entries for date
        as required by the parent L{calendarcontrol.Calendar} for
        display in a cell"""
        entry_list=self.getentrydata(year, month, day)
        res=[]
        for _entry in entry_list:
            (_y,_m,_d,_h,_min, _desc)=_entry.start+(_entry.description,)
            if _entry.allday:
                res.append((None, None, _desc))
            elif _entry.repeat or (_y,_m,_d)==(year, month, day):
                res.append((_h, _min, _desc))
            else:
                res.append((None, None, '...'+_desc))
        res.sort()
        return res

    def OnEdit(self, year, month, day, entry=None):
        """Called when the user wants to edit entries for a particular day"""
        if self.dialog.dirty:
            # user is editing a field so we don't allow edit
            wx.Bell()
        else:
            self.dialog.setdate(year, month, day, entry)
            self.dialog.Show(True)

    def OnTodayItem(self, evt):
        self.ActivateSelf()
        if evt.data:
            args=evt.data['datetime']+(evt.data['entry'],)
            self.OnEdit(*args)

    def OnTodayButton(self, evt):
        """ Called when the user goes to today cell"""
        super(Calendar, self).OnTodayButton(evt)
        if self.dialog.IsShown():
            # editor dialog is up, update it
            self.OnEdit(*self.selecteddate)

    def _publish_today_events(self):
        now=datetime.datetime.now()
        l=self.getentrydata(now.year, now.month, now.day)
        l.sort(CalendarEntry.cmp_by_time)
        today_event=today.TodayCalendarEvent()
        for e in l:
            today_event.append(e.summary, { 'datetime': (now.year, now.month, now.day),
                                            'entry': e })
        today_event.broadcast()

    def _publish_thisweek_events(self):
        now=datetime.datetime.now()
        one_day=datetime.timedelta(1)
        d1=now
        _days=6-(now.isoweekday()%7)
        res=[]
        today_event=today.ThisWeekCalendarEvent()
        for i in range(_days):
            d1+=one_day
            l=self.getentrydata(d1.year, d1.month, d1.day)
            if l:
                _dow=today.dow_initials[d1.isoweekday()%7]
                l.sort(CalendarEntry.cmp_by_time)
                for i,x in enumerate(l):
                    if i:
                        _name=today.dow_initials[-1]+'   '
                    else:
                        _name=_dow+' - '
                    _name+=x.summary
                    today_event.append(_name, { 'datetime': (d1.year, d1.month, d1.day),
                                                'entry': x })
        today_event.broadcast()
            
    def OnTodayRequest(self, _):
        self._publish_today_events()
        self._publish_thisweek_events()

    def _add_entries(self, entry):
        # Add this entry, which may span several days, to the entries list
        _t0=datetime.datetime(*entry.start[:3])
        _t1=datetime.datetime(*entry.end[:3])
        _oneday=datetime.timedelta(days=1)
        for _ in range((_t1-_t0).days+1):
            self.entries.setdefault((_t0.year, _t0.month, _t0.day), []).append(entry)
            _t0+=_oneday

    def populate(self, dict):
        """Updates the internal data with the contents of C{dict['calendar']}"""
        if dict.get('calendar_version', None)==2:
            # Cal dict version 2, need to convert to current ver(3)
            self._data=self._convert2to3(dict.get('calendar', {}),
                                          dict.get('ringtone-index', {}))
        else:
            self._data=dict.get('calendar', {})
        self.entrycache={}
        self.entries={}
        self.repeating=[]

        for entry in self._data:
            entry=self._data[entry]
            y,m,d,h,min=entry.start
            if entry.repeat is None:
                self._add_entries(entry)
            else:
                self.repeating.append(entry)
        # tell everyone that i've changed

        self._publish_today_events()
        self._publish_thisweek_events()
        self.RefreshAllEntries()

    def populatefs(self, dict):
        """Saves the dict to disk"""

        if dict.get('calendar_version', None)==2:
            # Cal dict version 2, need to convert to current ver(3)
            cal_dict=self._convert2to3(dict.get('calendar', {}),
                                        dict.get('ringtone-index', {}))
        else:
            cal_dict=dict.get('calendar', {})

        db_rr={}
        for k, e in cal_dict.items():
            db_rr[k]=CalendarDataObject(e)
        database.ensurerecordtype(db_rr, calendarobjectfactory)
        db_rr=database.extractbitpimserials(db_rr)
        self.mainwindow.database.savemajordict('calendar', db_rr)
        return dict

    def getfromfs(self, dict):
        """Updates dict with info from disk

        @Note: The dictionary passed in is modified, as well
        as returned
        @rtype: dict
        @param dict: the dictionary to update
        @return: the updated dictionary"""
        self.thedir=self.mainwindow.calendarpath
        if os.path.exists(os.path.join(self.thedir, "index.idx")):
            # old index file exists: read, convert, and discard file
            dct={'result': {}}
            common.readversionedindexfile(os.path.join(self.thedir, "index.idx"),
                                          dct, self.versionupgrade,
                                          self.CURRENTFILEVERSION)
            converted=dct['result'].has_key('converted')
            db_r={}
            for k,e in dct['result'].get('calendar', {}).items():
                if converted:
                    db_r[k]=CalendarDataObject(e)
                else:
                    ce=CalendarEntry()
                    ce.set(e)
                    db_r[k]=CalendarDataObject(ce)
            # save it in the new database
            database.ensurerecordtype(db_r, calendarobjectfactory)
            db_r=database.extractbitpimserials(db_r)
            self.mainwindow.database.savemajordict('calendar', db_r)
            # now that save is succesful, move file out of the way
            os.rename(os.path.join(self.thedir, "index.idx"), os.path.join(self.thedir, "index-is-now-in-database.bak"))
        # read data from the database
        cal_dict=self.mainwindow.database.getmajordictvalues('calendar',
                                                      calendarobjectfactory)
        #if __debug__:
        #    print 'Calendar.getfromfs: dicts returned from Database:'
        r={}
        for k,e in cal_dict.items():
            #if __debug__:
            #    print e
            ce=CalendarEntry()
            ce.set_db_dict(e)
            r[ce.id]=ce
        dict.update({ 'calendar': r })

        return dict

    def mergedata(self, result):
        """ Merge the newdata (from the phone) into current data
        """
        with guihelper.WXDialogWrapper(MergeDialog(self, self._data, result.get('calendar', {})),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self._data=dlg.get()
                self.updateonchange()

    def versionupgrade(self, dict, version):
        """Upgrade old data format read from disk

        @param dict:  The dict that was read in
        @param version: version number of the data on disk
        """

        # version 0 to 1 upgrade
        if version==0:
            version=1  # they are the same

        # 1 to 2 
        if version==1:
            # ?d field renamed daybitmap
            version=2
            for k in dict['result']['calendar']:
                entry=dict['result']['calendar'][k]
                entry['daybitmap']=self.getdaybitmap(entry['start'], entry['repeat'])
                del entry['?d']

        # 2 to 3 etc
        if version==2:
            version=3
            dict['result']['calendar']=self.convert_dict(dict['result'].get('calendar', {}), 2, 3)
            dict['result']['converted']=True    # already converted

        # 3 to 4 etc

    def convert_dict(self, dict, from_version, to_version, ringtone_index={}):
        """
        Convert the calendatr dict from one version to another.
        Currently only support conversion between version 2 and 3.
        """
        if dict is None:
            return None
        if from_version==2 and to_version==3:
            return self._convert2to3(dict, ringtone_index)
        elif from_version==3 and to_version==2:
            return self._convert3to2(dict, ringtone_index)
        else:
            raise 'Invalid conversion'

    def _convert2to3(self, dict, ringtone_index):
        """
        Convert calendar dict from version 2 to 3.
        """
        r={}
        for k,e in dict.items():
            ce=CalendarEntry()
            ce.start=e['start']
            ce.end=e['end']
            ce.description=e['description']
            ce.alarm=e['alarm']
            ce.ringtone=ringtone_index.get(e['ringtone'], {}).get('name', '')
            repeat=e['repeat']
            if repeat is None:
                ce.repeat=None
            else:
                repeat_entry=RepeatEntry()
                if repeat=='daily':
                    repeat_entry.repeat_type=repeat_entry.daily
                    repeat_entry.interval=1
                elif repeat=='monfri':
                    repeat_entry.repeat_type=repeat_entry.daily
                    repeat_entry.interval=0
                elif repeat=='weekly':
                    repeat_entry.repeat_type=repeat_entry.weekly
                    repeat_entry.interval=1
                    dow=datetime.date(*e['start'][:3]).isoweekday()%7
                    repeat_entry.dow=1<<dow
                elif repeat=='monthly':
                    repeat_entry.repeat_type=repeat_entry.monthly
                else:
                    repeat_entry.repeat_type=repeat_entry.yearly
                s=[]
                for n in e.get('exceptions',[]):
                    s.append(bptime.BPTime(n))
                repeat_entry.suppressed=s
                ce.repeat=repeat_entry
            r[ce.id]=ce
        return r

    def _convert_daily_events(self, e, d):
        """ Conver a daily event from v3 to v2 """
        rp=e.repeat
        if rp.interval==1:
            # repeat everyday
            d['repeat']='daily'
        elif rp.interval==0:
            # repeat every weekday
            d['repeat']='monfri'
        else:
            # the interval is every nth day, with n>1
            # generate exceptions for those dates that are N/A
            d['repeat']='daily'
            t0=datetime.date(*e.start[:3])
            t1=datetime.date(*e.end[:3])
            delta_t=datetime.timedelta(1)
            while t0<=t1:
                if not e.is_active(t0.year, t0.month, t0.day):
                    d['exceptions'].append((t0.year, t0.month, t0.day))
                t0+=delta_t

    def _convert_weekly_events(self, e, d, idx):
        """
        Convert a weekly event from v3 to v2
        """
        rp=e.repeat
        dow=rp.dow
        t0=datetime.date(*e.start[:3])
        t1=t3=datetime.date(*e.end[:3])
        delta_t=datetime.timedelta(1)
        delta_t7=datetime.timedelta(7)
        if (t1-t0).days>6:
            # end time is more than a week away
            t1=t0+datetime.timedelta(6)
        d['repeat']='weekly'
        res={}
        while t0<=t1:
            dow_0=t0.isoweekday()%7
            if (1<<dow_0)&dow:
                # we have a hit, generate a weekly repeat event here
                dd=copy.deepcopy(d)
                dd['start']=(t0.year, t0.month, t0.day, e.start[3], e.start[4])
                dd['daybitmap']=self.getdaybitmap(dd['start'], dd['repeat'])
                # generate exceptions for every nth week case
                t2=t0
                while t2<=t3:
                    if not e.is_active(t2.year, t2.month, t2.day):
                        dd['exceptions'].append((t2.year, t2.month, t2.day))
                    t2+=delta_t7
                # done, add it to the dict
                dd['pos']=idx
                res[idx]=dd
                idx+=1
            t0+=delta_t
        return idx, res

    def _convert3to2(self, dict, ringtone_index):
        """Convert calendar dict from version 3 to 2."""
        r={}
        idx=0
        for k,e in dict.items():
            d={}
            d['start']=e.start
            d['end']=e.end
            d['description']=e.description
            d['alarm']=e.alarm
            d['changeserial']=1
            d['snoozedelay']=0
            d['ringtone']=0 # by default
            try:
                d['ringtone']=[i for i,r in ringtone_index.items() \
                               if r.get('name', '')==e.ringtone][0]
            except:
                pass
            rp=e.repeat
            if rp is None:
                d['repeat']=None
                d['exceptions']=[]
                d['daybitmap']=0
            else:
                s=[]
                for n in rp.suppressed:
                    s.append(n.get()[:3])
                d['exceptions']=s
                if rp.repeat_type==rp.daily:
                    self._convert_daily_events(e, d)
                elif rp.repeat_type==rp.weekly:
                    idx, rr=self._convert_weekly_events(e, d, idx)
                    r.update(rr)
                    continue
                elif rp.repeat_type==rp.monthly:
                    d['repeat']='monthly'
                elif rp.repeat_type==rp.yearly:
                    d['repeat']='yearly'
                d['daybitmap']=self.getdaybitmap(d['start'], d['repeat'])
            d['pos']=idx
            r[idx]=d
            idx+=1
        if __debug__:
            print 'Calendar._convert3to2: V2 dict:'
            print r
        return r

#-------------------------------------------------------------------------------
class CalendarPrintDialog(guiwidgets.PrintDialog):

    _regular_template='cal_regular.xy'
    _regular_style='cal_regular_style.xy'
    _monthly_template='cal_monthly.xy'
    _monthly_style='cal_monthly_style.xy'
        
    def __init__(self, calwidget, mainwindow, config):
        super(CalendarPrintDialog, self).__init__(calwidget, mainwindow,
                                                  config, 'Print Calendar')
        self._dt_index=self._dt_start=self._dt_end=None
        self._date_changed=self._style_changed=False

    def _create_contents(self, vbs):
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        # the print range box
        sbs=wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Print Range'),
                              wx.VERTICAL)
        gs=wx.FlexGridSizer(-1, 2, 5, 5)
        gs.AddGrowableCol(1)
        gs.Add(wx.StaticText(self, -1, 'Start:'), 0, wx.ALL, 0)
        self._start_date=wx.DatePickerCtrl(self, style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)
        wx.EVT_DATE_CHANGED(self, self._start_date.GetId(),
                            self.OnDateChanged)
        gs.Add(self._start_date, 0, wx.ALL, 0)
        gs.Add(wx.StaticText(self, -1, 'End:'), 0, wx.ALL, 0)
        self._end_date=wx.DatePickerCtrl(self, style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)
        wx.EVT_DATE_CHANGED(self, self._end_date.GetId(),
                            self.OnDateChanged)
        gs.Add(self._end_date, 0, wx.ALL, 0)
        sbs.Add(gs, 1, wx.EXPAND|wx.ALL, 5)
        hbs.Add(sbs, 0, wx.ALL, 5)
        # thye print style box
        self._print_style=wx.RadioBox(self, -1, 'Print Style',
                                       choices=['List View', 'Month View'],
                                       style=wx.RA_SPECIFY_ROWS)
        wx.EVT_RADIOBOX(self, self._print_style.GetId(), self.OnStyleChanged)
        hbs.Add(self._print_style, 0, wx.ALL, 5)
        vbs.Add(hbs, 0, wx.ALL, 5)

    # constant class variables
    _one_day=wx.DateSpan(days=1)
    _empty_day=['', []]
    def _one_day_data(self):
        # generate data for 1 day
        r=[str(self._dt_index.GetDay())]
        events=[]
        if self._dt_start<=self._dt_index<=self._dt_end:
            entries=self._widget.getentrydata(self._dt_index.GetYear(),
                                                   self._dt_index.GetMonth()+1,
                                                   self._dt_index.GetDay())
        else:
            entries=[]
        self._dt_index+=self._one_day
        if len(entries):
            entries.sort(CalendarEntry.cmp_by_time)
            for e in entries:
                print_data=e.print_data
                events.append('%s: %s'%(print_data[0], print_data[3]))
        r.append(events)
        return r
    def _one_week_data(self):
        # generate data for 1 week
        dow=self._dt_index.GetWeekDay()
        if dow:
            r=[self._empty_day]*dow
        else:
            r=[]
        for d in range(dow, 7):
            r.append(self._one_day_data())
            if self._dt_index.GetDay()==1:
                # new month
                break
        return r
    def _one_month_data(self):
        # generate data for a month
        m=self._dt_index.GetMonth()
        y=self._dt_index.GetYear()
        r=['%s %d'%(self._dt_index.GetMonthName(m), y)]
        while self._dt_index.GetMonth()==m:
            r.append(self._one_week_data())
        return r
    def _get_monthly_data(self):
        """ generate a dict suitable to print monthly events
        """
        res=[]
        self._dt_index=wx.DateTimeFromDMY(1, self._dt_start.GetMonth(),
                                           self._dt_start.GetYear())
        while self._dt_index<=self._dt_end:
            res.append(self._one_month_data())
        return res

    def _get_list_data(self):
        """ generate a dict suitable for printing"""
        self._dt_index=wx.DateTimeFromDMY(self._dt_start.GetDay(),
                                    self._dt_start.GetMonth(),
                                    self._dt_start.GetYear())
        current_month=None
        res=a_month=month_events=[]
        while self._dt_index<=self._dt_end:
            y=self._dt_index.GetYear()
            m=self._dt_index.GetMonth()
            d=self._dt_index.GetDay()
            entries=self._widget.getentrydata(y, m+1, d)
            self._dt_index+=self._one_day
            if not len(entries):
                # no events on this day
                continue
            entries.sort(CalendarEntry.cmp_by_time)
            if m!=current_month:
                # save the current month
                if len(month_events):
                    a_month.append(month_events)
                    res.append(a_month)
                # start a new month
                current_month=m
                a_month=['%s %d'%(self._dt_index.GetMonthName(m), y)]
                month_events=[]
            # go through the entries and build a list of print data
            for i,e in enumerate(entries):
                if i:
                    date_str=day_str=''
                else:
                    date_str=str(d)
                    day_str=self._dt_index.GetWeekDayName(
                        self._dt_index.GetWeekDay()-1, wx.DateTime.Name_Abbr)
                month_events.append([date_str, day_str]+e.print_data)
        if len(month_events):
            # data left in the list
            a_month.append(month_events)
            res.append(a_month)
        return res

    def _init_print_data(self):
        # Initialize the dns dict with empty data
        super(CalendarPrintDialog, self)._init_print_data()
        self._dns['events']=[]

    def _gen_print_data(self):
        if not self._date_changed and \
           not self._style_changed and \
           self._html is not None:
            # already generate the print data, no changes needed
            return
        self._dt_start=self._start_date.GetValue()
        self._dt_end=self._end_date.GetValue()
        if not self._dt_start.IsValid() or not self._dt_end.IsValid():
            # invalid print range
            return
        print_data=(
            (self._regular_template, self._regular_style, self._get_list_data),
            (self._monthly_template, self._monthly_style, self._get_monthly_data))
        print_style=self._print_style.GetSelection()
        # tell the calendar widget to give me the dict I need
        print_dict=print_data[print_style][2]()
        # generate the html data
        if self._xcp is None:
            # build the whole document template
            self._xcp=xyaptu.xcopier(None)
            tmpl=file(guihelper.getresourcefile(print_data[print_style][0]),
                      'rt').read()
            self._xcp.setupxcopy(tmpl)
        elif self._style_changed:
            # just update the template
            tmpl=file(guihelper.getresourcefile(print_data[print_style][0]),
                      'rt').read()
            self._xcp.setupxcopy(tmpl)
        if self._dns is None:
            self._init_print_data()
        self._dns['events']=print_dict
        self._dns['date_range']='%s - %s'%\
                                  (self._dt_start.FormatDate(),
                                   self._dt_end.FormatDate())
        html=self._xcp.xcopywithdns(self._dns.copy())
        # apply styles
        sd={'styles': {}, '__builtins__': __builtins__ }
        try:
            execfile(guihelper.getresourcefile(print_data[print_style][1]), sd, sd)
        except UnicodeError:
            common.unicode_execfile(guihelper.getresourcefile(print_data[print_style][1]), sd, sd)
        try:
            self._html=bphtml.applyhtmlstyles(html, sd['styles'])
        except:
            if __debug__:
                file('debug.html', 'wt').write(html)
            raise
        self._date_changed=self._style_change=False

    def OnDateChanged(self, _):
        self._date_changed=True
    def OnStyleChanged(self, _):
        self._style_changed=True

#-------------------------------------------------------------------------------

class MergeDataTable(gridlib.PyGridTableBase):
    # colums attributes
    _cols_attrs=(
        { 'label': 'Description',
          'readonly': True,
          'alignment': (wx.ALIGN_LEFT, wx.ALIGN_CENTRE),
          'type': gridlib.GRID_VALUE_STRING },
        { 'label': 'Start',
          'readonly': True,
          'alignment': (wx.ALIGN_LEFT, wx.ALIGN_CENTRE),
          'type': gridlib.GRID_VALUE_STRING },
        { 'label': 'Changed',
          'readonly': True,
          'alignment': (wx.ALIGN_CENTRE, wx.ALIGN_CENTRE),
          'type': gridlib.GRID_VALUE_BOOL },
        { 'label': 'New',
          'readonly': False,
          'alignment': (wx.ALIGN_CENTRE, wx.ALIGN_CENTRE),
          'type': gridlib.GRID_VALUE_BOOL },
        { 'label': 'Ignore',
          'readonly': False,
          'alignment': (wx.ALIGN_CENTRE, wx.ALIGN_CENTRE),
          'type': gridlib.GRID_VALUE_BOOL },
        { 'label': 'Changed Details',
          'readonly': True,
          'alignment': (wx.ALIGN_LEFT, wx.ALIGN_CENTRE),
          'type': gridlib.GRID_VALUE_STRING },
        )
    # index into each row
    _desc_index=0
    _start_index=1
    _changed_index=2
    _new_index=3
    _ignore_index=4
    _details_index=5
    _key_index=6
    _similar_key_index=7

    def __init__(self, olddata, newdata):
        super(MergeDataTable, self).__init__()
        self._old=olddata
        self._new=newdata
        self.data=[]
        self._bins={}
        self._similarpairs={}
        self._generate_table()
    
    def _generate_table(self):
        # Generate table data from the given data
        # first, separate old events into bins for efficient comparison
        self._bins={}
        for _key,_entry in self._old.items():
            self._bins.setdefault(_entry.start[:3], []).append(_key)
        self._similarpairs={}
        for _key,_entry in self._new.items():
            # default to a new event being added
            _row=[_entry.description, _entry.start_str, 0, 1, 0, 'New event', _key]
            _bin_key=_entry.start[:3]
            for _item_key in self._bins.get(_bin_key, []):
                _old_event=self._old[_item_key]
                if _old_event.matches(_entry):
                    # same event, no action
                    _row[self._new_index]=0
                    _row[self._details_index]='No changes'
                    break
                elif _old_event.similar(_entry):
                    # changed event, being merged
                    _row[self._changed_index]=1
                    _row[self._new_index]=0
                    _row[self._details_index]=_old_event.get_changed_fields(_entry)
                    _row.append(_item_key)
                    break
            self.data.append(_row)
    def _merge(self):
        # merge the new data into the old one, and return the result
        for _row in self.data:
            if _row[self._ignore_index]:
                # ignore this new entry
                continue
            elif _row[self._new_index]:
                # add this new entry
                _key=_row[self._key_index]
                self._old[_key]=self._new[_key]
            elif _row[self._changed_index]:
                # replace the old entry with this new one
                _new_key=_row[self._key_index]
                _old_key=_row[self._similar_key_index]
                self._old[_old_key].replace(self._new[_new_key])
        return self._old
    def _replace(self):
        # return non-ignore events
        _res={}
        for _row in self.data:
            if not _row[self._ignore_index]:
                _key=_row[self._key_index]
                _res[_key]=self._new[_key]
        return _res
    def get(self, merge=False):
        # return the result data
        if not merge:
            # replace all with new data
            return self._replace()
        else:
            # return merged data
            return self._merge()

    #--------------------------------------------------
    # required methods for the wxPyGridTableBase interface
    def GetNumberRows(self):
        return len(self.data)
    def GetNumberCols(self):
        return len(self._cols_attrs)
    def IsEmptyCell(self, row, col):
        if row>len(self.data) or col>len(self._cols_attrs):
            return True
        return False
    # Get/Set values in the table.  The Python version of these
    # methods can handle any data-type, (as long as the Editor and
    # Renderer understands the type too,) not just strings as in the
    # C++ version.
    def GetValue(self, row, col):
        try:
            return self.data[row][col]
        except IndexError:
            return ''
    def SetValue(self, row, col, value):
        try:
            self.data[row][col] = value
        except IndexError:
            pass

    #--------------------------------------------------
    # Some optional methods
    # Called when the grid needs to display labels
    def GetColLabelValue(self, col):
        try:
            return self._cols_attrs[col]['label']
        except IndexError:
            return ''
    def IsReadOnlyCell(self, row, col):
        try:
            return self._cols_attrs[col]['readonly']
        except IndexError:
            return False
    def GetAlignments(self, row, col):
        try:
            return self._cols_attrs[col]['alignment']
        except IndexError:
            return None
    # Called to determine the kind of editor/renderer to use by
    # default, doesn't necessarily have to be the same type used
    # natively by the editor/renderer if they know how to convert.
    def GetTypeName(self, row, col):
        return self._cols_attrs[col]['type']
    # Called to determine how the data can be fetched and stored by the
    # editor and renderer.  This allows you to enforce some type-safety
    # in the grid.
    def CanGetValueAs(self, row, col, typeName):
        return self._cols_attrs[col]['type']==typeName
    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)

class MergeDataGrid(gridlib.Grid):
    def __init__(self, parent, table):
        super(MergeDataGrid, self).__init__(parent, -1)
        self.SetTable(table, True)
        # set col attributes
        for _col in range(table.GetNumberCols()):
            _ro=table.IsReadOnlyCell(0, _col)
            _alignments=table.GetAlignments(0, _col)
            if  _ro or _alignments:
                _attr=gridlib.GridCellAttr()
                if _ro:
                    _attr.SetReadOnly(True)
                if _alignments:
                    _attr.SetAlignment(*_alignments)
                self.SetColAttr(_col, _attr)
        self.SetRowLabelSize(0)
        self.SetMargins(0,0)
        self.AutoSize()
        self.Refresh()

class MergeDialog(wx.Dialog):
    def __init__(self, parent, olddata, newdata):
        super(MergeDialog, self).__init__(parent, -1,
                                          'Calendar Data Merge',
                                          style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self._merge=False
        vbs=wx.BoxSizer(wx.VERTICAL)
        self._grid=MergeDataGrid(self, MergeDataTable(olddata, newdata))
        vbs.Add(self._grid, 1, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        _btn=wx.Button(self, -1, 'Replace All')
        wx.EVT_BUTTON(self, _btn.GetId(), self.OnReplaceAll)
        hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        _btn=wx.Button(self, -1, 'Merge')
        wx.EVT_BUTTON(self, _btn.GetId(), self.OnMerge)
        hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        _btn=wx.Button(self, wx.ID_CANCEL, 'Cancel')
        hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        _btn=wx.Button(self, wx.ID_HELP, 'Help')
        wx.EVT_BUTTON(self, wx.ID_HELP,
                      lambda _: wx.GetApp().displayhelpid(helpids.ID_DLG_CALENDAR_MERGE))
        hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(hbs, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        guiwidgets.set_size("CalendarMergeEditor", self, 52, 1.0)
    def OnOK(self, _=None):
        guiwidgets.save_size("CalendarMergeEditor", self.GetRect())
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.SetReturnCode(wx.ID_OK)
            self.Show(False)
    def OnReplaceAll(self, evt):
        self._merge=False
        self.OnOK()
    def OnMerge(self, _):
        self._merge=True
        self.OnOK()
    def get(self):
        # return the merge data
        return self._grid.GetTable().get(self._merge)
