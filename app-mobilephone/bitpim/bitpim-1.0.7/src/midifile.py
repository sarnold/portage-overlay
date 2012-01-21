### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: midifile.py 3608 2006-10-06 02:51:56Z djpham $

import common


module_debug=False

class MIDIEvent(object):
    META_EVENT=0
    SYSEX_EVENT=1
    SYSEX1_EVENT=2
    MIDI_EVENT=3
    LAST_MIDI_EVENT=4
    type_str=('Meta', 'SYSEX', 'SYSEX cont', 'MIDI', 'Last MIDI')
    
    def __init__(self, file, offset, last_cmd=None):
        self.__f=file
        self.__start=self.__ofs=offset
        self.__time_delta=self.__get_var_len()
        b=self.__get_int()
        if b==0xff:
            # meta event
            self.__get_meta_event()
        elif b==0xf0 or b==0xf7:
            # sysex event
            self.__get_sysex_event(b)
        else:
            # MIDI Channel event
            self.__get_midi_event(b, last_cmd)
        self.__total_len=self.__ofs-self.__start

    def __get_int(self):
        i=int(self.__f.GetByte(self.__ofs))
        self.__ofs+=1
        return i

    def __get_bytes(self, len):
        data=self.__f.GetBytes(self.__ofs, len)
        self.__ofs+=len
        return data

    def __get_var_len(self):
        t=0
        b=self.__get_int()
        while (b&0x80):
            t=(t<<7)|(b&0x7f)
            b=self.__get_int()
        return (t<<7)|(b&0x7f)

    def __get_meta_event(self):
        self.__type=self.META_EVENT
        self.__cmd=self.__get_int()
        self.__len=self.__get_var_len()
        if self.__len:
            self.__param1=self.__get_bytes(self.__len)
        else:
            self.__param1=None
        self.__param2=None

    def __get_sysex_event(self, cmd):
        if cmd==0xf0:
            self.__type=self.SYSEX_EVENT
        else:
            self.__type=self.SYSEX1_EVENT
        self.__cmd=cmd
        self.__len=self.__get_var_len()
        if self.__len:
            self.__param1=self.__get_bytes(self.__len)
        else:
            self.__param1=None
        self.__param2=None

    def __get_midi_event(self, cmd, last_cmd):
        if cmd&0x80:
            # not a running command
            i=cmd
            self.__type=self.MIDI_EVENT
            self.__param1=self.__get_int()
        else:
            i=last_cmd
            self.__type=self.LAST_MIDI_EVENT
            self.__param1=cmd
        self.__cmd=(i&0xf0)>>4
        self.__midi_channel=i&0x0f
        if self.__cmd==0x0c or self.__cmd==0x0d:
            self.__len=1
            self.__param2=None
        else:
            self.__len=2
            self.__param2=self.__get_int()

    def __get_type(self):
        return self.__type
    type=property(fget=__get_type)

    def __get_time_delta(self):
        return self.__time_delta
    time_delta=property(fget=__get_time_delta)

    def __get_total_len(self):
        return self.__total_len
    total_len=property(fget=__get_total_len)
    
    def __get_cmd(self):
        return self.__cmd
    cmd=property(fget=__get_cmd)

    def __get_midi_channel(self):
        return self.__midi_channel
    midi_channel=property(fget=__get_midi_channel)

    def __get_param_len(self):
        return self.__len
    param_len=property(fget=__get_param_len)

    def __get_params(self):
        return self.__param1, self.__param2
    params=property(fget=__get_params)
    
    def __str__(self):
        if self.type==self.MIDI_EVENT or \
           self.type==self.LAST_MIDI_EVENT:
            return '0x%04x: %s cmd: 0x%x, Channel: %d, Len: %d'%\
                   (self.time_delta, self.type_str[self.type],
                    self.cmd, self.midi_channel, self.param_len)
        else:
            return '0x%04x: %s cmd: 0x%x, Len: %d'%\
                   (self.time_delta, self.type_str[self.type],
                    self.cmd, self.param_len)

class MIDITrack(object):
    def __init__(self, file, offset):
        self.__f=file
        self.__ofs=offset
        if module_debug:
            print 'New Track @ ofs:', offset
        if self.__f.GetBytes(self.__ofs, 4)!='MTrk':
            raise TypeError, 'not an MIDI track'
        self.__len=self.__f.GetMSBUint32(self.__ofs+4)
        ofs=self.__ofs+8
        ofs_end=ofs+self.__len
        last_cmd=None
        self.__time_delta=0
        self.__mpqn=None
        while ofs<ofs_end:
            e=MIDIEvent(file, ofs, last_cmd)
            if module_debug:
                print e
            ofs+=e.total_len
            self.__time_delta+=e.time_delta
            if e.type==e.META_EVENT:
                if e.cmd==0x51:
                    # set tempo
                    p1, p2=e.params
                    self.__mpqn=(ord(p1[0])<<16)|(ord(p1[1])<<8)|ord(p1[2])
            if e.type==e.MIDI_EVENT or e.type==e.LAST_MIDI_EVENT:
                last_cmd=(e.cmd<<4)|e.midi_channel
            else:
                last_cmd=e.cmd
        self.__total_len=ofs-self.__ofs
        if module_debug:
            print 'self.__ofs', self.__ofs+8, 'self.__len:', self.__len, 'ofs: ', ofs
            print 'time delta:', self.__time_delta, 'MPQN: ', self.__mpqn

    def __get_time_delta(self):
        return self.__time_delta
    time_delta=property(fget=__get_time_delta)
    def __get_total_len(self):
        return self.__total_len
    total_len=property(fget=__get_total_len)
    def __get_mpqn(self):
        return self.__mpqn
    mpqn=property(fget=__get_mpqn)

class MIDIFile(object):
    def __init__(self, file_wraper):
        try:
            self.__valid=False
            self.__file=file_wraper
            if self.__file.GetBytes(0, 4)!='MThd' or \
               self.__file.GetMSBUint32(4)!=6:
                # not a valid MIDI header
                return
            self.__valid=True
            self.__type=self.__file.GetMSBUint16(8)
            self.__num_tracks=self.__file.GetMSBUint16(10)
            self.__time_division=self.__file.GetMSBUint16(12)
            self.__tracks=[]
            self.__mpqn=2000000
            file_ofs=14
            time_delta=0
            for i in range(self.__num_tracks):
                trk=MIDITrack(self.__file, file_ofs)
                self.__tracks.append(trk)
                file_ofs+=trk.total_len
                time_delta=max(time_delta, trk.time_delta)
                if trk.mpqn is not None:
                    self.__mpqn=trk.mpqn
            self.__duration=(self.__mpqn*time_delta/self.__time_division)/1000000.0
            if module_debug:
                print 'type:', self.__type
                print 'time division:', self.__time_division
                print 'num of tracks:', self.__num_tracks
                print 'MPQN:', self.__mpqn
                print 'longest time delta: ', time_delta
                print 'duration:', self.__duration
        except:
            self.__valid=False

    def __get_valid(self):
        return self.__valid
    valid=property(fget=__get_valid)

    def __get_type(self):
        return self.__type
    type=property(fget=__get_type)

    def __get_num_tracks(self):
        return self.__num_tracks
    num_tracks=property(fget=__get_num_tracks)

    def __get_duration(self):
        return self.__duration
    duration=property(fget=__get_duration)




