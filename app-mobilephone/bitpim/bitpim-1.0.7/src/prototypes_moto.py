### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: prototypes_moto.py 3460 2006-07-08 23:55:09Z djpham $

"""Implement specific prototypes class for Motorola phones"""

import re

import prototypes

class CAL_DATE(prototypes.CSVSTRING):
    """Dates used for Calendar Events (mm-dd-yyyy)"""
    def __init__(self, *args, **kwargs):
        super(CAL_DATE, self).__init__(*args, **kwargs)
        self._valuedate=(0, 0, 0) # y,m,d
        if self._ismostderived(CAL_DATE):
            self._update(args, kwargs)

    def _converttostring(self, date):
        s=''
        if len(date)>=3:
            year,month,day=date[:3]
            if month>0 or day>0 or year>0:
                s='%2.2d-%2.2d-%4.4d'%(month, day, year)
        return s

    def _update(self, args, kwargs):
        for k in ('constant', 'default', 'value'):
            if kwargs.has_key(k):
                kwargs[k]=self._converttostring(kwargs[k])
        if len(args)==0:
            pass
        elif len(args)==1:
            args=(self._converttostring(args[0]),)
        else:
            raise TypeError("expected (year,month,day) as arg")
        super(CAL_DATE, self)._update(args, kwargs)
        self._complainaboutunusedargs(CAL_DATE, kwargs)

    def getvalue(self):
        s=super(CAL_DATE, self).getvalue()
        val=s.split('-')
        if len(val)<2:
            year=0
            month=0
            day=0
        else:
            year=int(val[2])
            month=int(val[0])
            day=int(val[1])
        return (year, month, day)

class CAL_TIME(prototypes.CSVSTRING):
    """Times used for Calendar Events (hh:mm)"""
    def __init__(self, *args, **kwargs):
        super(CAL_TIME, self).__init__(*args, **kwargs)
        self._valuetime=(0, 0) # h,m
        if self._ismostderived(CAL_TIME):
            self._update(args, kwargs)

    def _converttostring(self, date):
        s=''
        if len(date)>=2:
            s='%2.2d:%2.2d'%tuple(date[:2])
        return s

    def _update(self, args, kwargs):
        for k in ('constant', 'default', 'value'):
            if kwargs.has_key(k):
                kwargs[k]=self._converttostring(kwargs[k])
        if len(args)==0:
            pass
        elif len(args)==1:
            args=(self._converttostring(args[0]),)
        else:
            raise TypeError("expected (hour, min) as arg")
        super(CAL_TIME, self)._update(args, kwargs)
        self._complainaboutunusedargs(CAL_TIME, kwargs)

    def getvalue(self):
        s=super(CAL_TIME, self).getvalue()
        val=s.split(':')
        if len(val)==2:
            return (int(val[0]), int(val[1]))
        return (0, 0)

class M_SMSDATETIME(prototypes.CSVSTRING):
    """ Represent date time with the format 'yyyy/M+/d+,h+:m+:s+' used
    by Motorola SMS messages.
    Currently works only 1 way: SMS Date Time -> ISO String
    """
    _re_pattern='^\d\d+/\d+/\d+,\d+:\d+:\d+$'
    _re_compiled_pattern=None
    def __init__(self, *args, **kwargs):
        if M_SMSDATETIME._re_compiled_pattern is None:
            M_SMSDATETIME._re_compiled_pattern=re.compile(M_SMSDATETIME._re_pattern)
        super(M_SMSDATETIME, self).__init__(*args, **kwargs)
        if self._ismostderived(M_SMSDATETIME):
            self._update(args, kwargs)

    def _update(self, args, kwargs):
        super(M_SMSDATETIME, self)._update(args, kwargs)
        # strip blanks, and replace quotechar
        if self._value:
            self._value=self._value.strip(' ').replace('"', '')
        if self._value and \
           not re.match(M_SMSDATETIME._re_compiled_pattern, self._value):
            raise ValueError('Correct Format: [yy]yy/[M]M/[d]d,[h]h:[m]m:[s]s')

    def getvalue(self):
        """Returns the ISO Format 'yyyyMMddThhmmss"""
        if self._value:
            _d,_t=self._value.strip(' ').replace('"', '').split(',')
            _d=_d.split('/')
            _t=_t.split(':')
            return '%s%s%sT%s%s%s'%(_d[0].zfill(4), _d[1].zfill(2), _d[2].zfill(2),
                                    _t[0].zfill(2), _t[1].zfill(2), _t[2].zfill(2))
