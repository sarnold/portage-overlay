### BITPIM
###
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: prototypeslg.py 4715 2008-10-21 01:51:40Z djpham $

import bpcalendar

import calendar
import prototypes
import re
import time

class LGCALDATE(prototypes.UINTlsb):
    def __init__(self, *args, **kwargs):
        """A date/time as used in the LG calendar"""
        super(LGCALDATE,self).__init__(*args, **kwargs)
        self._valuedate=(0,0,0,0,0)  # year month day hour minute

        dict={'sizeinbytes': 4}
        dict.update(kwargs)

        if self._ismostderived(LGCALDATE):
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
            raise TypeError("expected (year,month,day,hour,minute) as arg")

        super(LGCALDATE,self)._update(args, kwargs) # we want the args
        self._complainaboutunusedargs(LGCALDATE,kwargs)
        assert self._sizeinbytes==4

    def getvalue(self):
        """Unpack 32 bit value into date/time

        @rtype: tuple
        @return: (year, month, day, hour, minute)
        """
        val=super(LGCALDATE,self).getvalue()
        min=val&0x3f # 6 bits
        val>>=6
        hour=val&0x1f # 5 bits (uses 24 hour clock)
        val>>=5
        day=val&0x1f # 5 bits
        val>>=5
        month=val&0xf # 4 bits
        val>>=4
        year=val&0xfff # 12 bits
        return (year, month, day, hour, min)

    def _converttoint(self, date):
        assert len(date)==5
        year,month,day,hour,min=date
        if year>4095:
            year=4095
        val=year
        val<<=4
        val|=month
        val<<=5
        val|=day
        val<<=5
        val|=hour
        val<<=6
        val|=min
        return val

class LGCALREPEAT(prototypes.UINTlsb):
    def __init__(self, *args, **kwargs):
        """A 32-bit bitmapped value used to store repeat info for events in the LG calendar"""
        super(LGCALREPEAT,self).__init__(*args, **kwargs)
        
        # The meaning of the bits in this field
        # MSB                          LSB
        #  3         2         1         
        # 10987654321098765432109876543210
        #                              210  repeat_type
        #                            0      exceptions, set to 1 if there are exceptions
        #                     6543210       dow_weekly (weekly repeat type)
        #                         210       dow (monthly repeat type)
        #             543210                interval
        #               3210                month_index
        #  543210                           day_index    

        # repeat_type: 0=none, 1=daily, 2=weekly, 3=monthly, 4=yearly, 5=weekdays, 6=XthDayEachMonth(e.g. 3rd Friday each month)
        # dow_weekly: Weekly repeat type only. Identical to bpcalender dow bits, multiple selections allowed(Bit0=sun,Bit1=mon,Bit2=tue,Bit3=wed,Bit4=thur,Bit5=fri,Bit6=sat)  
        # dow_monthly: Monthly repeat type 6 only. (0=sun,1=mon,2=tue,3=wed,4=thur,5=fri,6=sat)
        # interval: repeat interval, eg. every 1 week, 2 weeks 4 weeks etc. Also be used for months, but bp does not support this.
        # month_index: For type 4 this is the month the event starts in
        # day_index: For type 6 this represents the number of the day that is the repeat, e.g. "2"nd tuesday
        #            For type 3&4 this is the day of the month that the repeat occurs, usually the same as the start date.
        #            bp does not support this not being the support date

        dict={'sizeinbytes': 4}
        dict.update(kwargs)

        if self._ismostderived(LGCALREPEAT):
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
            raise TypeError("expected (type, dow, interval) as arg")

        super(LGCALREPEAT,self)._update(args, kwargs) # we want the args
        self._complainaboutunusedargs(LGCALDATE,kwargs)
        assert self._sizeinbytes==4

    def getvalue(self):
        val=super(LGCALREPEAT,self).getvalue()
        type=val&0x7 # 3 bits
        val>>=4
        exceptions=val&0x1
        val>>=1
        #get day of week, only valid for some repeat types
        #format of data is also different for different repeat types
        interval2=(val>>9)&0x3f
        if type==6: # for monthly repeats
            dow=self._to_bp_dow[val&7] #day of month, valid for monthly repeat types, need to convert to bitpim format
        elif type==2: #weekly 
            dow=val&0x7f # 7 bits, already matched bpcalender format
        else:
            dow=0
        # get interval
        if type==6:
            val>>=20
            interval=val&0x1f # day_index
        else:
            val>>=9
            interval=val&0x3f
        return (type, dow, interval, interval2, exceptions)

    _caldomvalues={
        0x01: 0x0, #sun
        0x02: 0x1, #mon
        0x04: 0x2, #tue
        0x08: 0x3, #wed
        0x10: 0x4, #thur
        0x20: 0x5, #fri
        0x40: 0x6  #sat
        }
    _to_bp_dow={
        0: 0x01,    # Sun
        1: 0x02,    # Mon
        2: 0x04,    # Tue
        3: 0x08,    # Wed
        4: 0x10,    # Thu
        5: 0x20,    # Fri
        6: 0x40,    # Sat
        }
        
    def _converttoint(self, repeat):
        if not isinstance(repeat, (tuple, list)):
            if __debug__:
                raise TypeError
            else:
                return 0
        if len(repeat)!=5:
            if __debug__:
                raise ValueError
            else:
                return 0
        type,dow,interval,interval2,exceptions=repeat
        val=0
        # construct bitmapped value for repeat
        # look for weekday type
        val=interval
        if type==6 or type==3:
            val<<=11
            val|=interval2
        if type==4: #yearly
            val<<=11
            val|=dow
        val<<=9
        if type==2:
            val|=dow
        elif type==6:
            if self._caldomvalues.has_key(dow):
                val|=self._caldomvalues[dow]
            else:
                # invalid day-of-week for monthly type, just bail
                return 0
        val<<=1
        val|=exceptions
        val<<=4
        val|=type
        return val

class GPSDATE(prototypes.UINTlsb):
    _time_t_ofs=calendar.timegm((1980, 1, 6, 0, 0, 0))
    _counter=0
    def __init__(self, *args, **kwargs):
        """A date/time as used in the LG call history files,
        @keyword unique: (True/False, Optional) Ensure that each GSPDATE instance
                          is unique.
        @keyword raiseonbadvalue: (default False) raise L{ValueError} if the
                        GPSDATE value is bad.
        """
        super(GPSDATE, self).__init__(*args, **kwargs)
        self._unique=False
        self._raiseonbadvalue=False
        dict={'sizeinbytes': 4}
        dict.update(kwargs)

        if self._ismostderived(GPSDATE):
            self._update(args, dict)

    def _update(self, args, kwargs):
        self._consumekw(kwargs, ('unique', 'raiseonbadvalue'))
        for k in 'constant', 'default', 'value':
            if kwargs.has_key(k):
                kwargs[k]=self._converttoint(kwargs[k])

        if len(args)==0:
            pass
        elif len(args)==1:
            args=(self._converttoint(args[0]),)
        else:
            raise TypeError("expected (year,month,day,hour,minute,sec) as arg")

        super(GPSDATE, self)._update(args, kwargs) # we want the args
        self._complainaboutunusedargs(GPSDATE,kwargs)
        assert self._sizeinbytes==4

    def getvalue(self):
        """Convert 32 bit value into date/time

        @rtype: tuple
        @return: (year, month, day, hour, minute, sec)
        """
        try:
            return time.gmtime(self._time_t_ofs+super(GPSDATE, self).getvalue())[:6]
        except ValueError:
            if self._raiseonbadvalue:
                raise
            return (1980, 1, 6, 0, 0, 0)

    def _converttoint(self, date):
        assert len(date)==6
        _val=calendar.timegm(date)-self._time_t_ofs
        if self._unique:
            _val+=GPSDATE._counter
            GPSDATE._counter+=1
            if GPSDATE._counter==0xffff:
                GPSDATE._counter=0
        return _val
    @classmethod
    def now(_):
        return time.gmtime()[:6]

class GSMCALDATE(prototypes.CSVSTRING):
    """ Represent date string with format "YYMMDD*"
    This format is being used in LG GSM Calendar Evetns
    """
    def __init__(self, *args, **kwargs):
        super(GSMCALDATE, self).__init__(*args, **kwargs)
        self._data=None
        self._readmode=True
        if self._ismostderived(GSMCALDATE):
            self._update(args, kwargs)

    def _set_data(self, v=None):
        if v:
            self._data=v[:3]
        else:
            self._data=(2000+int(self._value[:2]), int(self._value[2:4]),
                        int(self._value[4:6]))
    def _set_value(self):
        self._value='%02d%02d%02d'%(self._data[0]-2000, self._data[1],
                                    self._data[2])

    def _update(self, args, kwargs):
        self._consumekw(kwargs, ('readmode',))
        if len(args)==1:
            if isinstance(args[0], (list, tuple)):
                super(GSMCALDATE, self)._update((), kwargs)
                self._set_data(args[0])
                self._set_value()
            elif isinstance(args[0], (str, unicode)):
                super(GSMCALDATE, self)._update(args, kwargs)
                self._set_data()
            else:
                raise TypeError
        elif len(args)==0:
            super(GSMCALDATE, self)._update(args, kwargs)
        else:
            raise TypeError
        self._complainaboutunusedargs(GSMCALDATE, kwargs)

    def readfrombuffer(self, buf):
        super(GSMCALDATE, self).readfrombuffer(buf)
        if self._value:
            self._set_data()
        else:
            self._data=None

    def getvalue(self):
        """Returns the tuple of (year, month, day)"""
        if self._data is None:
            if self._value is None:
                raise prototypes.ValueNotSetException()
            self._set_data()
        if self._readmode:
            return self._data
        else:
            if self._quotechar:
                _quote=chr(self._quotechar)
            else:
                _quote=''
            return _quote+self._value+_quote

class GSMCALTIME(GSMCALDATE):
    """ Represent date time with format "hhm"
    This format is being used in LG GSM Calendar Evetns
    """

    def __init__(self, *args, **kwargs):
        super(GSMCALTIME, self).__init__(*args, **kwargs)
        if self._ismostderived(GSMCALTIME):
            self._update(args, kwargs)

    def _set_data(self, v=None):
        if v:
            self._data=v[:2]
        else:
            self._data=(int(self._value[:2]), int(self._value[2:4]))

    def _set_value(self):
        self._value='%02d%02d'%self._data

class SMSDATETIME(prototypes.CSVSTRING):
    """ Represent date time with the format 'yy/MM/dd,hh:mm:ss+-zz' used
    by GSM SMS messages.
    Currently works only 1 way: SMS Date Time -> ISO String
    """
    _re_pattern='^\d\d/\d\d/\d\d,\d\d:\d\d:\d\d[+\-]\d\d$'
    _re_compiled_pattern=None
    def __init__(self, *args, **kwargs):
        if SMSDATETIME._re_compiled_pattern is None:
            SMSDATETIME._re_compiled_pattern=re.compile(SMSDATETIME._re_pattern)
        super(SMSDATETIME, self).__init__(*args, **kwargs)
        if self._ismostderived(SMSDATETIME):
            self._update(args, kwargs)

    def _update(self, args, kwargs):
        super(SMSDATETIME, self)._update(args, kwargs)
        if self._value and \
           not re.match(SMSDATETIME._re_compiled_pattern, self._value):
            raise ValueError('COrrect Format: yy/MM/dd,hh:mm:ss+-zz')

    def getvalue(self):
        """Returns the ISO Format 'YYYMMDDTHHMMSS+-mmss'"""
        if self._value:
            _s=self._value.split(',')
            return '20%sT%s00'%(_s[0].replace('/', ''),
                                _s[1].replace(':', ''))

class TELUSLGCALREPEAT(prototypes.UINTlsb):
    def __init__(self, *args, **kwargs):
        """A 32-bit bitmapped value used to store repeat info for events in the LG calendar"""
        super(TELUSLGCALREPEAT,self).__init__(*args, **kwargs)
        
        # The meaning of the bits in this field
        # MSB                          LSB
        #  3         2         1         
        # 10987654321098765432109876543210
        #                              210  repeat_type
        #                            0      exceptions, set to 1 if there are exceptions
        #                     6543210       dow_weekly (weekly repeat type)
        #                         210       dow (monthly repeat type)
        #             543210                interval
        #               3210                month_index
        # 6543210                           day_index    

        # repeat_type: 0=none, 1=daily, 2=weekdays, 3=weekly, 4=Month Nth Xday, 5=monthly on date, 6=yearly Nth Xday in month, 7=yearly on date 
        # dow_weekly: Weekly repeat type only. Identical to bpcalender dow bits, multiple selections allowed(Bit0=sun,Bit1=mon,Bit2=tue,Bit3=wed,Bit4=thur,Bit5=fri,Bit6=sat)  
        # dow_monthly: Monthly repeat type 6 only. (0=sun,1=mon,2=tue,3=wed,4=thur,5=fri,6=sat)
        # interval: repeat interval, eg. every 1 week, 2 weeks 4 weeks etc. Also be used for months, but bp does not support this.
        # month_index: For type 4 this is the month the event starts in
        # day_index: For type 6 this represents the number of the day that is the repeat, e.g. "2"nd tuesday
        #            For type 3&4 this is the day of the month that the repeat occurs, usually the same as the start date.
        #            For type 0&2 set to 0x7F
        #            For type 1&3 set to 0

        dict={'sizeinbytes': 4}
        dict.update(kwargs)

        if self._ismostderived(TELUSLGCALREPEAT):
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
            raise TypeError("expected (type, dow, interval) as arg")

        super(TELUSLGCALREPEAT,self)._update(args, kwargs) # we want the args
        self._complainaboutunusedargs(TELUSLGCALREPEAT,kwargs)
        assert self._sizeinbytes==4

    def getvalue(self):
        val=super(TELUSLGCALREPEAT,self).getvalue()
        type=val&0x7 # 3 bits
        val>>=4
        exceptions=val&0x1
        val>>=1
        #get day of week, only valid for some repeat types
        #format of data is also different for different repeat types
        interval2=(val>>9)&0x3f
        if type==4: # for monthly repeats
            dow=self._to_bp_dow[val&7] #day of month, valid for monthly repeat types, need to convert to bitpim format
        elif type==3: #weekly 
            dow=val&0x7f # 7 bits, already matched bpcalender format
        else:
            dow=0
        # get interval
        if type==4:
            val>>=20
            interval=val&0x1f # day_index
        else:
            val>>=9
            interval=val&0x3f
        return (type, dow, interval, interval2, exceptions)

    _caldomvalues={
        0x01: 0x0, #sun
        0x02: 0x1, #mon
        0x04: 0x2, #tue
        0x08: 0x3, #wed
        0x10: 0x4, #thur
        0x20: 0x5, #fri
        0x40: 0x6  #sat
        }
    _to_bp_dow={
        0: 0x01,    # Sun
        1: 0x02,    # Mon
        2: 0x04,    # Tue
        3: 0x08,    # Wed
        4: 0x10,    # Thu
        5: 0x20,    # Fri
        6: 0x40,    # Sat
        }
        
    def _converttoint(self, repeat):
        if not isinstance(repeat, (tuple, list)):
            if __debug__:
                raise TypeError
            else:
                return 0
        if len(repeat)!=5:
            if __debug__:
                raise ValueError
            else:
                return 0
        type,dow,interval,interval2,exceptions=repeat
        val=0
        # construct bitmapped value for repeat
        val=interval
        if type==0 or type==2:
            val=0x7F
            val<<=11
            val|=interval
        if type==4 or type==5:
            val<<=11
            val|=interval2
        if type==7: #yearly
            val<<=11
            val|=dow
        val<<=9
        if type==2:
            val|=dow
        elif type==4:
            val|=self._caldomvalues[dow]
        val<<=1
        val|=exceptions
        val<<=4
        val|=type
        return val

#-------------------------------------------------------------------------------
class T9USERDBBLOCK(prototypes.BaseProtogenClass):
    """
    Special class to handle data blocks within the LG T9 User Database file.
    Perhaps, the prototypes syntax should be enhanced to more gracefully
    handle cases like this!
    """

    # known types of this block
    FreeBlock_Type='Free Block'
    A0_Type='A0 Block'
    WordsList_Type='Words List'
    C_Type='C'
    Garbage_Type='Garbage'

    def __init__(self, *args, **kwargs):
        super(T9USERDBBLOCK, self).__init__(*args, **kwargs)
        self._value=None
        self._type=None
        if self._ismostderived(T9USERDBBLOCK):
            self._update(args, kwargs)

    def _update(self, args, kwargs):
        super(T9USERDBBLOCK, self)._update(args, kwargs)
        # we have no special keywords to process so complain away
        self._complainaboutunusedargs(T9USERDBBLOCK, kwargs)
        # Set our value if one was specified
        if len(args)==0:
            pass
        elif len(args)==1:
            self._set_value(args[0])
        else:
            raise TypeError("Unexpected arguments "+`args`)

    def _set_value(self, v):
        # set the value of this block
        # the value must be a dict having 2 keys: 'type' and 'value'
        if not isinstance(v, dict):
            raise TypeError('Value must be a dict')
        if not v.has_key('type') or not v.has_key('value'):
            raise ValueError('Missing type or value keyword')
        _type=v['type']
        _value=v['value']
        if _type==self.FreeBlock_Type:
            # this is a free block, the value is an integer specifying
            # the length of this free block
            if not isinstance(_value, int):
                raise TypeError('Value must be an int')
        elif _type==self.WordsList_Type:
            # this is a list of words, the value is a list of dicts,
            # each dict should have 2 keys: 'word', 'weight'.
            # value['word'] is a string
            # value['weight'] is an int, default to 0xA000
            if not isinstance(_value, list):
                raise TypeError('Value must be a list of dicts')
        elif _type==self.A0_Type:
            _value=0xA0
        else:
            raise ValueError('Invalid type: '+_type)
        self._type=_type
        self._value=_value

    def _extract_words_list(self, buf):
        # read and construct a word list
        _res=[]
        _size=buf.peeknextbyte()
        while _size<0x80:
            _size=buf.getnextbyte()
            _weight=buf.getnextbyte()|(buf.getnextbyte()<<8)
            _res.append({ 'word': buf.getnextbytes(_size),
                          'weight': _weight })
            _size=buf.peeknextbyte()
        return _res
    def readfrombuffer(self, buf):
        try:
            self._bufferstartoffset=buf.getcurrentoffset()
            _ch=buf.peeknextbyte()
            if _ch&0xF0==0xC0:
                self._type=self.C_Type
                self._value=''
                while True:
                    b=buf.getnextbytes(1)
                    self._value+=b
                    if b=='\x09':
                        self._value+=buf.getnextbytes(1)
                        break
            elif _ch&0xF0==0xA0:
                self._type=self.A0_Type
                self._value=buf.getnextbyte()
            elif _ch&0xF0==0x80:
                self._type=self.FreeBlock_Type
                self._value=((buf.getnextbyte()&0x0F)<<8)|buf.getnextbyte()
                buf.getnextbytes(self._value-2)
            elif _ch<0x80:
                self._type=self.WordsList_Type
                self._value=self._extract_words_list(buf)
            else:
                raise ValueError('Unknown block type: 0x%02X'%_ch)
        except IndexError:
            # ignore garbage at the end
            self._type=self.Garbage_Type
            self._value=0
##        print 'type:',self._type
##        print 'value:',self._value
        self._bufferendoffset=buf.getcurrentoffset()

    def getvalue(self):
        if self._value is None or self._type is None:
            raise ValueNotSetException()
        return { 'type': self._type,
                 'value': self._value }

    def packetsize(self):
        # return the size of this packet
        if self._value is None or self._type is None:
            raise ValueNotSetException()
        if self._type==self.C_Type or \
           self._type==self.A0_Type:
            return len(self._value)
        if self._type==self.FreeBlock_Type:
            return self._value
        if self._type==self.WordsList_Type:
            _size=0
            for _entry in self._value:
                _size+=len(_entry['word'])+3
            return _size

    def writetobuffer(self, buf):
        if self._value is None or self._type is None:
            raise ValueNotSetException()
        self._bufferstartoffset=buf.getcurrentoffset()
        if self._type==self.C_Type:
            buf.appendbytes(self._value)
        elif self._type==self.A0_Type:
            buf.appendbyte(0xA0)
        elif self._type==self.FreeBlock_Type:
            buf.appendbyte(0x80|((self._value&0xF00)>>8))
            buf.appendbyte(self._value&0xff)
            for _ in range(self._value-2):
                buf.appendbyte(0)
        elif self._type==self.WordsList_Type:
            for _entry in self._value:
                buf.appendbyte(len(_entry['word']))
                _weight=_entry.get('weight', 0xA000)
                buf.appendbyte(_weight&0xff)
                buf.appendbyte((_weight&0xFF00)>>8)
                buf.appendbytes(_entry['word'])
        self._bufferendoffset=buf.getcurrentoffset()

class LGHEXPN(prototypes.DATA):
    """ Phone numbers stored as hex. i.e. 0x5555551212f0 == 555-555-1212
    """
    def __init__(self, *args, **kwargs):
        """A date/time as used in the LG calendar"""
        super(LGHEXPN,self).__init__(*args, **kwargs)
        self._update(args, kwargs)

    def _update (self, args, kwargs):
        for k in 'constant', 'default', 'value':
            if kwargs.has_key(k):
                kwargs[k]=self._string_to_lghexpn (kwargs[k])
        if len(args)==0:
            pass
        elif len(args)==1:
            args = (self._string_to_lghexpn (args[0]),)
        else:
            raise TypeError("Expected phone number string as arg")

        super(LGHEXPN,self)._update(args, kwargs)

    def _digit_to_char (self, digit):
        if digit <= 0x09:
            return chr (digit + ord('0'))
        elif digit == 0x0A:
            return '*'
        elif digit == 0x0B:
            return '#'
        elif digit == 0x0C:
            return 'W'
        elif digit == 0x0D:
            return 'P'
        else:
            # 0x0f is not an error
            raise

    def _char_to_digit (self, char):
        if char >= '0' and char <= '9':
            return ord(char) - ord('0')
        elif char == '*':
            return 0x0A
        elif char == '#':
            return 0x0B
        elif char == 'W':
            return 0x0C
        elif char == 'P':
            return 0x0D
        else:
            raise ValueError

    def _string_to_lghexpn (self, pn):
        val = ''
        
        byte = 0xf0
        for i in range(0, len (pn)):
            digit = self._char_to_digit (pn[i])
            if i % 2:
                val += chr(byte & (0xf0 | digit))
                byte = 0xf0
            else:
                byte = (digit << 4) | 0x0f
        # write terminating byte
        val += chr(byte)

        return val
    
    def getvalue(self):
        """Unpack hex phone number

        @rtype: string
        @return: phone number
        """
        val=super(LGHEXPN,self).getvalue()
        pn = ''
        for byte in val:
            fd = ord(byte) >> 4
            sd = ord(byte) & 0x0f

            try:
                pn += self._digit_to_char(fd)
                pn += self._digit_to_char(sd)
            except:
                # end of packed number, not an error
                break
        return pn

class PBDateTime(prototypes.BaseProtogenClass):
    "Handle  six 2-byte UINTs: y, m, d, h, m, s"

    def __init__(self, *args, **kwargs):
        """
        Class to handle the date/time format of 6 2-byte UINTs: y, m, d, h, m, s
        @keyword default: (Optional) Our default value
        @keyword defaulttocurrenttime: (Optional) Default to the current date/time
        """
        super(PBDateTime, self).__init__(*args, **kwargs)
        self._default=None
        self._defaulttocurrenttime=False
        self._value=None

        if self._ismostderived(PBDateTime):
            self._update(args, kwargs)
    
    def _update(self, args, kwargs):
        super(PBDateTime, self)._update(args, kwargs)
        self._consumekw(kwargs, ("default", "defaulttocurrenttime", "value"))
        self._complainaboutunusedargs(PBDateTime, kwargs)

        if len(args)==0:
            pass
        elif len(args)==1:
            self._value=args[0]
        else:
            raise TypeError("Unexpected arguments "+`args`)

        if self._value is None:
            # value not specified, check for either default or default to
            # current time
            if self._default:
                self._value=self._default
            elif self._defaulttocurrenttime:
                self._value=time.localtime()[:6]

    def readfrombuffer(self, buf):
        self._bufferstartoffset=buf.getcurrentoffset()

        _res=[]
        for i in range(6):
            _res.append(buf.getnextbyte()|(buf.getnextbyte()<<8))
        self._value=_res

        self._bufferendoffset=buf.getcurrentoffset()

    def writetobuffer(self, buf):
        if self._value is None:
            raise ValueNotSetException()
        if not isinstance(self._value, (list, tuple)):
            raise TypeError('value needs to be a list/tuple')
        if len(self._value)!=6:
            raise TypeError('len of value needs to be 6')

        self._bufferstartoffset=buf.getcurrentoffset()
        for _num in self._value:
            buf.appendbyte(_num&0xff)
            buf.appendbyte((_num>>8)&0xff)
        self._bufferendoffset=buf.getcurrentoffset()

    def packetsize(self):
        """Size in bytes"""
        return 12

    def getvalue(self):
        if self._value is None:
            raise ValueNotSetException()
        return self._value
