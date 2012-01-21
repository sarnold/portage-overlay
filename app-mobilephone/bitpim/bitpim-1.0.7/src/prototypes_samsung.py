### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: prototypes_samsung.py 4777 2010-01-07 03:24:27Z djpham $

"""The various types used in protocol descriptions specific to Samsung phones"""

import calendar
import datetime
import time

import prototypes

class DateTime(prototypes.UINTlsb):
    _daylight=None
    def __init__(self, *args, **kwargs):
        if DateTime._daylight is None:
            DateTime._daylight=time.localtime()[-1]
        super(DateTime, self).__init__(*args, **kwargs)
        kwargs.update({ 'sizeinbytes': 4 })
        if self._ismostderived(DateTime):
            self._update(args, kwargs)

    def _update(self, args, kwargs):
        for k in 'constant', 'default', 'value':
            if kwargs.has_key(k):
                kwargs[k]=self._converttoint(kwargs[k])
        if len(args)==0:
            pass
        elif len(args)==1:
            args=(self._converttoint(args[0]),)
        else:
            raise TypeError("expected (year,month,day,hour,minute) as arg")

        super(DateTime, self)._update(args, kwargs)
        self._complainaboutunusedargs(DateTime, kwargs)
        assert self._sizeinbytes==4

    _time_delta=315514800.0
    def _converttoint(self, date):
        assert len(date)>4
        _timetuple=datetime.datetime(*date[:5]).timetuple()[:-1]+(DateTime._daylight,)
        return int(calendar.timegm(_timetuple)-self._time_delta)

    def getvalue(self):
        """Unpack 32 bit value into date/time
        @rtype: tuple
        @return: (year, month, day, hour, minute)
        """
        val=super(DateTime, self).getvalue()
        return time.gmtime(val+self._time_delta)[:5]
    @classmethod
    def now(_):
        return time.localtime()[:5]

class DateTime1(DateTime):
    # similar to DateTime, except getvalue includes seconds
    def __init__(self, *args, **kwargs):
        super(DateTime1, self).__init__(*args, **kwargs)
        kwargs.update({ 'sizeinbytes': 4 })
        if self._ismostderived(DateTime1):
            self._update(args, kwargs)

    def getvalue(self):
        """Unpack 32 bit value into date/time
        @rtype: tuple
        @return: (year, month, day, hour, minute, second)
        """
        val=prototypes.UINTlsb.getvalue(self)
        return time.gmtime(val+self._time_delta)[:6]

class DateTime2(DateTime1):
    # similar to DateTime, with different time delta
    _time_delta=315532800.0
    def __init__(self, *args, **kwargs):
        super(DateTime2, self).__init__(*args, **kwargs)
        kwargs.update({ 'sizeinbytes': 4 })
        if self._ismostderived(DateTime2):
            self._update(args, kwargs)


class ExpiringTime(prototypes.UINTlsb):
    # Implement a weird expiring time used by Samsung calendar events
    def __init__(self, *args, **kwargs):
        super(ExpiringTime, self).__init__(*args, **kwargs)
        dict={ 'sizeinbytes': 4 }
        dict.update(kwargs)
        if self._ismostderived(ExpiringTime):
            self._update(args, dict)

    def _update(self, args, kwargs):
        for k in 'constant', 'default', 'value':
            if kwargs.has_key(k):
                kwargs[k]=self._converttoint(kwargs[k])
        if len(args)==0:
            pass
        elif len(args)==1:
            args=(self._converttoint(args[0]),)
        else:
            raise TypeError("expected (hour, minute, duration) as arg")

        super(ExpiringTime, self)._update(args, kwargs)
        self._complainaboutunusedargs(ExpiringTime, kwargs)
        assert self._sizeinbytes==4

    _delta=3786843600L
    def _converttoint(self, v):
        assert len(v)==2
        hour, min=v
        return hour*3600+min*60+self._delta
