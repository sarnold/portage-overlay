### BITPIM
###
### Copyright (C) 2003-2006 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2006-2006 Simon Capper <skyjunky@sbcglobal.net>
### Copyright (C) 2006 Michael Cohen <mikepublic@nc.rr.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx8100.py 4481 2007-12-05 22:39:17Z djpham $

"""Communicate with the LG VX8100 cell phone

The VX8100 is similar to the VX7000 but also supports video.

"""

# standard modules
import re
import time
import cStringIO
import sha

# my modules
import common
import commport
import copy
import com_lgvx4400
import p_brew
import p_lgvx8100
import com_lgvx7000
import com_brew
import com_phone
import com_lg
import prototypes
import bpcalendar
import call_history
import sms
import memo
import helpids


from prototypes import *



class Phone(com_lg.LGNewIndexedMedia2, com_lg.LGDMPhone, com_lgvx7000.Phone):
    "Talk to the LG VX8100 cell phone"

    desc="LG-VX8100"
    helpid=helpids.ID_PHONE_LGVX8100
    protocolclass=p_lgvx8100
    serialsname='lgvx8100'

    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'VZW Default Ringtone') + \
                      tuple(['Ringtone '+`n` for n in range(1,11)]) + \
                      ('No Ring',)

    ringtonelocations= (
        # type       index-file   size-file directory-to-use lowest-index-to-use maximum-entries type-major icon
        ( 'ringers', 'dload/my_ringtone.dat', 'dload/my_ringtonesize.dat', 'brew/16452/lk/mr', 100, 150, 0x201, 1, 0),
        # the sound index file uses the same index as the ringers, bitpim does not support this (yet)
        ( 'sounds', 'dload/mysound.dat', 'dload/mysoundsize.dat', 'brew/16452/ms', 100, 150, 2, 0, 151),
        )

    calendarlocation="sch/newschedule.dat"
    calendarexceptionlocation="sch/newschexception.dat"
    calenderrequiresreboot=0
    memolocation="sch/neomemo.dat"

    builtinwallpapers = () # none

    wallpaperlocations= (
        ( 'images', 'dload/image.dat', 'dload/imagesize.dat', 'brew/16452/mp', 100, 50, 0, 0, 0),
        ( 'video', 'dload/video.dat', None, 'brew/16452/mf', 1000, 50, 0x0304, 0, 0),
        )

    # for removable media (miniSD cards)
    _rs_path='mmc1/'
    _rs_ringers_path=_rs_path+'ringers'
    _rs_images_path=_rs_path+'images'
    media_info={ 'ringers': {
            'localpath': 'brew/16452/lk/mr',
            'rspath': _rs_ringers_path,
            'vtype': protocolclass.MEDIA_TYPE_RINGTONE,
            'icon': protocolclass.MEDIA_RINGTONE_DEFAULT_ICON,
            'index': 100,  # starting index
            'maxsize': 155,
            'indexfile': 'dload/my_ringtone.dat',
            'sizefile': 'dload/my_ringtonesize.dat',
            'dunno': 0, 'date': False,
        },
         'sounds': {
             'localpath': 'brew/16452/ms',
             'rspath': None,
             'vtype': protocolclass.MEDIA_TYPE_SOUND,
             'icon': protocolclass.MEDIA_IMAGE_DEFAULT_ICON,
             'index': 100,
             'maxsize': 155,
             'indexfile': 'dload/mysound.dat',
             'sizefile': 'dload/mysoundsize.dat',
             'dunno': 0, 'date': False },
         'images': {
             'localpath': 'brew/16452/mp',
             'rspath': _rs_images_path,
             'vtype': protocolclass.MEDIA_TYPE_IMAGE,
             'icon': protocolclass.MEDIA_IMAGE_DEFAULT_ICON,
             'index': 100,
             'maxsize': 155,
             'indexfile': 'dload/image.dat',
             'sizefile': 'dload/imagesize.dat',
             'dunno': 0, 'date': False },
         'video': {
             'localpath': 'brew/16452/mf',
             'rspath': None,
             'vtype': protocolclass.MEDIA_TYPE_VIDEO,
             'icon': protocolclass.MEDIA_VIDEO_DEFAULT_ICON,
             'index': 1000,
             'maxsize': 155,
             'indexfile': 'dload/video.dat',
             'sizefile': 'dload/videosize.dat',
             'dunno': 0, 'date': True },
         }

    def __init__(self, logtarget, commport):
        com_lgvx4400.Phone.__init__(self, logtarget, commport)
        com_lg.LGDMPhone.__init__(self)
        self.mode=self.MODENONE

    def get_firmware_version(self):
        # return the firmware version
        req=p_brew.firmwarerequest()
        res=self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
        return res.firmware

    def setDMversion(self):
        """Define the DM version required for this phone, default to DMv5"""
        # not sure what the 8100 requirements are, default to v4 only
        self._DMv5=False

    # Fundamentals:
    #  - get_esn             - /nvm/$ESN.SYS (same as LG VX-4400)
    #  - getgroups           - defined below
    #  - getwallpaperindices - LGNewIndexedMedia2
    #  - getringtoneindices  - LGNewIndexedMedia2
    #  - DM Version          - 4 to access brew/16452/lk/mr on newer firmwares

    def getgroups(self, results):
        self.log("Reading group information")
        buf=prototypes.buffer(self.getfilecontents("pim/pbgroup.dat"))
        g=self.protocolclass.pbgroups()
        g.readfrombuffer(buf, logtitle="Groups read")
        groups={}
        for i in range(len(g.groups)):
            if len(g.groups[i].name): # sometimes have zero length names
                groups[i]={'name': g.groups[i].name }
        results['groups']=groups
        return groups

    def savegroups(self, data):
        groups=data['groups']
        keys=groups.keys()
        keys.sort()
        g=self.protocolclass.pbgroups()
        for k in keys:
            e=self.protocolclass.pbgroup()
            e.name=groups[k]['name']
            g.groups.append(e)
        buffer=prototypes.buffer()
        g.writetobuffer(buffer, logtitle="New group file")
        self.writefile("pim/pbgroup.dat", buffer.getvalue())

    def getmemo(self, result):
        # read the memo file
        res={}
        try:
            stat_res=self.statfile(self.memolocation)
            # allow for zero length file
            if stat_res!=None and stat_res['size']!=0:
                buf=prototypes.buffer(self.getfilecontents(self.memolocation))
                text_memo=self.protocolclass.textmemofile()
                text_memo.readfrombuffer(buf, logtitle="Read memo file"+self.memolocation)
                for m in text_memo.items:
                    entry=memo.MemoEntry()
                    entry.text=m.text
                    try:
                        entry.set_date_isostr("%d%02d%02dT%02d%02d00" % ((m.memotime)))
                    except ValueError:
                        # deleted memos can remain in file but have a bogus date
                        continue
                    res[entry.id]=entry
        except com_brew.BrewNoSuchFileException:
            pass
        result['memo']=res
        return result

    def savememo(self, result, merge):
        text_memo=self.protocolclass.textmemofile()
        memo_dict=result.get('memo', {})
        keys=memo_dict.keys()
        keys.sort()
        text_memo.itemcount=len(keys)
        for k in keys:
            entry=self.protocolclass.textmemo()
            entry.text=memo_dict[k].text
            t=time.strptime(memo_dict[k].date, '%b %d, %Y %H:%M')
            entry.memotime=(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min)
            if 'GPStime' in entry.getfields():
                entry.GPStime = (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
            text_memo.items.append(entry)
        buf=prototypes.buffer()
        text_memo.writetobuffer(buf, logtitle="Updated memo "+self.memolocation)
        self.writefile(self.memolocation, buf.getvalue())
        return result

    def getexceptions (self):
        try:
            buf=prototypes.buffer(self.getfilecontents(self.calendarexceptionlocation))
            ex=self.protocolclass.scheduleexceptionfile()
            ex.readfrombuffer(buf, logtitle="Calendar exceptions")
            exceptions={}
            for i in ex.items:
                try:
                    exceptions[i.pos].append( (i.year,i.month,i.day) )
                except KeyError:
                    exceptions[i.pos]=[ (i.year,i.month,i.day) ]
        except com_brew.BrewNoSuchFileException:
            exceptions={}

        return exceptions

    def getcalendarcommon(self, entry, event):
        entry.desc_loc=event.description
        entry.start=event.start
        if self.protocolclass.CALENDAR_HAS_SEPARATE_END_TIME_AND_DATE:
            if event.repeat[0] == 0:           # MIC:  If non-repeating event
                entry.end = event.end_time     # MIC:  Set entry.end to full end_time
            else:
                _,_,_,hour,minute=event.end_time
                year,month,day,_,_=event.end_date
                entry.end=(year,month,day,hour,minute)
        else:
            entry.end=event.end
        if event.alarmindex_vibrate&0x1:
            entry.vibrate=0 # vibarate bit is inverted in phone 0=on, 1=off
        else:
            entry.vibrate=1
        entry.repeat = self.makerepeat(event.repeat)
        min=event.alarmminutes
        hour=event.alarmhours
        if min==0x64 or hour==0x64:
            entry.alarm=None # no alarm set
        else:
            entry.alarm=hour*60+min
        entry.snoozedelay=0

    def getcalendar(self,result):
        res={}
        # Read exceptions file first
        exceptions = self.getexceptions ()
        
        # Now read schedule
        try:
            buf=prototypes.buffer(self.getfilecontents(self.calendarlocation))
            if len(buf.getdata())<3:
                # file is empty, and hence same as non-existent
                raise com_brew.BrewNoSuchFileException()
            sc=self.protocolclass.schedulefile()
            sc.readfrombuffer(buf, logtitle="Calendar")
            for event in sc.events:
                # the vx8100 has a bad entry when the calender is empty
                # stop processing the calender when we hit this record
                if event.pos==0: #invalid entry
                    continue
                entry=bpcalendar.CalendarEntry()
                try: # delete events are still in the calender file but have garbage dates
                    self.getcalendarcommon (entry, event)
                except ValueError:
                    continue
                if self.protocolclass.CALENDAR_HAS_SEPARATE_END_TIME_AND_DATE:
                    # MIC Unlike previous phones, the VX8300 passes the ringtone
                    # via both the index, and a path.  If the index is set to 100
                    # (0x64), then the ringtone information will be found in the
                    # "ringpath", the last 256 bytes of the calendar packet.  If
                    # the index is between 0 and 15, inclusive, then it is using
                    # one of the builtin ringers, and the ringpath is set to
                    # null.
                    try:
                        if (event.ringtone == 100):   # MIC Ringer is downloaded to phone or microSD
                            entry.ringtone = common.basename(event.ringpath)
                        else:                         # MIC Ringer is built-in
                            entry.ringtone=self.builtinringtones[event.ringtone]
                    except:
                        # hack, not having a phone makes it hard to figure out the best approach
                        if entry.alarm==None:
                            entry.ringtone='No Ring'
                        else:
                            entry.ringtone='Loud Beeps'
                else:
                    entry.ringtone=result['ringtone-index'][event.ringtone]['name']
                # check for exceptions and remove them
                if event.repeat[3] and exceptions.has_key(event.pos):
                    for year, month, day in exceptions[event.pos]:
                        entry.suppress_repeat_entry(year, month, day)
                res[entry.id]=entry

            assert sc.numactiveitems==len(res)
        except com_brew.BrewNoSuchFileException:
            pass # do nothing if file doesn't exist
        result['calendar']=res
        return result

    def makerepeat(self, repeat):
        # get all the variables out of the repeat tuple
        # and convert into a bpcalender RepeatEntry
        type,dow,interval,interval2,exceptions=repeat
        if type==0:
            repeat_entry=None
        else:
            repeat_entry=bpcalendar.RepeatEntry()
            if type==1: #daily
                repeat_entry.repeat_type=repeat_entry.daily
                repeat_entry.interval=interval
            elif type==5: #'monfri'
                repeat_entry.repeat_type=repeat_entry.daily
                repeat_entry.interval=0
            elif type==2: #'weekly'
                repeat_entry.repeat_type=repeat_entry.weekly
                repeat_entry.dow=dow
                repeat_entry.interval=interval
            elif type==3: #'monthly'
                repeat_entry.repeat_type=repeat_entry.monthly
                repeat_entry.interval2=interval2
                repeat_entry.dow=0
            elif type==6: #'monthly' #Xth Y day (e.g. 2nd friday each month)
                repeat_entry.repeat_type=repeat_entry.monthly
                repeat_entry.interval=interval #X
                repeat_entry.dow=dow #Y
                repeat_entry.interval2=interval2
            else: # =4 'yearly'
                repeat_entry.repeat_type=repeat_entry.yearly
        return repeat_entry

    def _scheduleexceptions(self, entry, data, exceptionsf):
        exceptions=0
        if entry.repeat!=None:
            if self.protocolclass.CALENDAR_HAS_SEPARATE_END_TIME_AND_DATE:
                if data.end_date[:3]==entry.no_end_date:
                    year_s,month_s,day_s,hour_s,minute_s=entry.start
                    data.end_date=(year_s + 5, month_s, day_s, 31, 63)
            else:
                if data.end[:3]==entry.no_end_date:
                    data.end=(2100, 12, 31)+data.end[3:]
            for i in entry.repeat.suppressed:
                de=self.protocolclass.scheduleexception()
                de.pos=data.pos
                de.day=i.date.day
                de.month=i.date.month
                de.year=i.date.year
                exceptions=1
                exceptionsf.items.append(de)
        if entry.repeat != None:
            data.repeat=(self.getrepeattype(entry, exceptions))
        else:
            data.repeat=((0,0,0,0,0))

    def _schedulecommon(self, entry, data):
        data.description=entry.desc_loc
        data.start=entry.start
        if self.protocolclass.CALENDAR_HAS_SEPARATE_END_TIME_AND_DATE:
            year_e,month_e,day_e,hour_e,minute_e=entry.end
            year_s,month_s,day_s,hour_s,minute_s=entry.start
            if entry.repeat!=None:           # MIC:  Added check for repeating event
                data.end_date = (year_e,month_e,day_e,31,63)
            else:
                data.end_date = (year_s+5,month_s,day_s,31,63)
            data.end_time = (year_s,month_s,day_s,hour_e,minute_e)
        else:
            data.end=entry.end
        data.ringtone=0
        data.unknown1=0

    def savecalendar(self, dict, merge):
        # ::TODO::
        # what will be written to the files
        eventsf=self.protocolclass.schedulefile()
        exceptionsf=self.protocolclass.scheduleexceptionfile()
        # what are we working with
        cal=dict['calendar']
        newcal={}
        #sort into start order, makes it possible to see if the calendar has changed
        keys=[(x.start, k) for k,x in cal.items()]
        keys.sort()
        # apply limiter
        keys=keys[:self.protocolclass.NUMCALENDARENTRIES]
        # number of entries
        eventsf.numactiveitems=len(keys)
        pos=1
        contains_alarms=False
        # play with each entry
        for (_,k) in keys:
            # entry is what we will return to user
            entry=cal[k]
            data=self.protocolclass.scheduleevent()
            data.pos=eventsf.packetsize()
            self._schedulecommon(entry, data)
            alarm_set=self.setalarm(entry, data)
            if alarm_set:
                if entry.ringtone=="No Ring" and not entry.vibrate:
                    alarm_name="Low Beep Once"
                else:
                    alarm_name=entry.ringtone
            else: # set alarm to "No Ring" gets rid of alarm icon on phone
                alarm_name="No Ring"
            if self.protocolclass.CALENDAR_HAS_SEPARATE_END_TIME_AND_DATE:
                # MIC VX8300 handles the ringtone differently than previous
                # phones.  Except for the 16 builtin ringers, ringers stored
                # directly on the phone or on the microSD are specified by
                # their fully qualified path, and an index of 100.
                for i in dict['ringtone-index']:
                    if dict['ringtone-index'][i]['name']==alarm_name:
                        if dict['ringtone-index'][i].get('filename', None):
                            data.ringtone=100
                            data.ringpath=dict['ringtone-index'][i]['filename']
                        else:
                            # builtin ringer
                            data.ringtone=i      # Set to proper index
                        break
            else:
                data.unknown2=0        # MIC Only unknown in VX8100 and prior
                                       # Moved up from line below, as we do not
                                       # want it defined for the VX8300+
                for i in dict['ringtone-index']:
                    if dict['ringtone-index'][i]['name']==alarm_name:
                        data.ringtone=i
                        break
            # check for exceptions and add them to the exceptions list
            self._scheduleexceptions(entry, data, exceptionsf)
            if data.alarmindex_vibrate!=1: # if alarm set
                contains_alarms=True
            # put entry in nice shiny new dict we are building
            entry=copy.copy(entry)
            newcal[data.pos]=entry
            eventsf.events.append(data)

        buf=prototypes.buffer()
        eventsf.writetobuffer(buf, logtitle="New Calendar")
        self.writefile(self.calendarlocation, buf.getvalue())
        if contains_alarms or self.calenderrequiresreboot:
            self.log("Your phone has to be rebooted due to the calendar changing")
            dict["rebootphone"]=True

        buf=prototypes.buffer()
        exceptionsf.writetobuffer(buf, logtitle="Writing calendar exceptions")
        self.writefile(self.calendarexceptionlocation, buf.getvalue())

        # fix passed in dict
        dict['calendar']=newcal

        return dict

    def getrepeattype(self, entry, exceptions):
        #convert the bpcalender type into vx8100 type
        repeat_entry=bpcalendar.RepeatEntry()
        interval2=0
        if entry.repeat.repeat_type==repeat_entry.monthly:
            dow=entry.repeat.dow
            interval2=entry.repeat.interval2
            if entry.repeat.dow==0:
                # set interval for month type 4 to start day of month, (required by vx8100)
                interval=entry.start[2]
                type=3
            else:
                interval=entry.repeat.interval
                type=6
        elif entry.repeat.repeat_type==repeat_entry.daily:
            dow=entry.repeat.dow
            interval=entry.repeat.interval
            if entry.repeat.interval==0:
                type=5
            else:
                type=1
        elif entry.repeat.repeat_type==repeat_entry.weekly:
            dow=entry.repeat.dow
            interval=entry.repeat.interval
            type=2
        elif entry.repeat.repeat_type==repeat_entry.yearly:
            # set interval to start day of month, (required by vx8100)
            interval=entry.start[2]
            # set dow to start month, (required by vx8100)
            dow=entry.start[1]
            type=4
        return (type, dow, interval, interval2, exceptions)

    def setalarm(self, entry, data):
        # vx8100 only allows certain repeat intervals, adjust to fit, it also stores an index to the interval
        rc=True
        if entry.alarm>=2880:
            entry.alarm=2880
            data.alarmminutes=0
            data.alarmhours=48
            data.alarmindex_vibrate=0x10
        elif entry.alarm>=1440:
            entry.alarm=1440
            data.alarmminutes=0
            data.alarmhours=24
            data.alarmindex_vibrate=0xe
        elif entry.alarm>=120:
            entry.alarm=120
            data.alarmminutes=0
            data.alarmhours=2
            data.alarmindex_vibrate=0xc
        elif entry.alarm>=60:
            entry.alarm=60
            data.alarmminutes=0
            data.alarmhours=1
            data.alarmindex_vibrate=0xa
        elif entry.alarm>=15:
            entry.alarm=15
            data.alarmminutes=15
            data.alarmhours=0
            data.alarmindex_vibrate=0x8
        elif entry.alarm>=10:
            entry.alarm=10
            data.alarmminutes=10
            data.alarmhours=0
            data.alarmindex_vibrate=0x6
        elif entry.alarm>=5:
            entry.alarm=5
            data.alarmminutes=5
            data.alarmhours=0
            data.alarmindex_vibrate=0x4
        elif entry.alarm>=0:
            entry.alarm=0
            data.alarmminutes=0
            data.alarmhours=0
            data.alarmindex_vibrate=0x2
        else: # no alarm
            data.alarmminutes=0x64
            data.alarmhours=0x64
            data.alarmindex_vibrate=1
            rc=False

        # set the vibrate bit
        if data.alarmindex_vibrate > 1 and entry.vibrate==0:
            data.alarmindex_vibrate+=1
        return rc

    my_model='VX8100'

    def getphoneinfo(self, phone_info):
        self.log('Getting Phone Info')
        try:
            s=self.getfilecontents('brew/version.txt')
            if s[:6]==self.my_model:
                phone_info.append('Model:', self.my_model)
                phone_info.append('ESN:', self.get_brew_esn())
                req=p_brew.firmwarerequest()
                res=self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
                phone_info.append('Firmware Version:', res.firmware)
                txt=self.getfilecontents("nvm/nvm/nvm_cdma")[180:190]
                phone_info.append('Phone Number:', txt)
        except:
            pass
        return

    # Media stuff---------------------------------------------------------------
    def _is_rs_file(self, filename):
        return filename.startswith(self._rs_path)

    def getmedia(self, maps, results, key):
        origins={}
        # signal that we are using the new media storage that includes the origin and timestamp
        origins['new_media_version']=1

        for type, indexfile, sizefile, directory, lowestindex, maxentries, typemajor, def_icon, idx_ofs  in maps:
            media={}
            for item in self.getindex(indexfile):
                data=None
                timestamp=None
                try:
                    stat_res=self.statfile(item.filename)
                    if stat_res!=None:
                        timestamp=stat_res['date'][0]
                    if not self._is_rs_file(item.filename):
                        data=self.getfilecontents(item.filename, True)
                except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException,com_brew.BrewNameTooLongException):
                    self.log("It was in the index, but not on the filesystem")
                except com_brew.BrewAccessDeniedException:
                    # firmware wouldn't let us read this file, just mark it then
                    self.log('Failed to read file: '+item.filename)
                    data=''
                if data!=None:
                    media[common.basename(item.filename)]={ 'data': data, 'timestamp': timestamp}
            origins[type]=media

        results[key]=origins
        return results

    def _mark_files(self, local_files, rs_files, local_dir):
        # create empty local files as markers for remote files
        _empty_files=[common.basename(x) for x,_entry in local_files.items() \
                      if not _entry['size']]
        _remote_files=[common.basename(x) for x in rs_files]
        for _file in _remote_files:
            if _file not in _empty_files:
                # mark this one
                self.writefile(local_dir+'/'+_file, '')
        for _file in _empty_files:
            if _file not in _remote_files:
                # remote file no longer exists, del the marker
                self.rmfile(local_dir+'/'+_file)

    def _write_index_file(self, type):
        _info=self.media_info.get(type, None)
        if not _info:
            return
        _files={}
        _local_dir=_info['localpath']
        _rs_dir=_info['rspath']
        _vtype=_info['vtype']
        _icon=_info['icon']
        _index=_info['index']
        _maxsize=_info['maxsize']
        _dunno=_info['dunno']
        indexfile=_info['indexfile']
        sizefile=_info['sizefile']
        _need_date=_info['date']
        try:
            _files=self.listfiles(_local_dir)
        except (com_brew.BrewNoSuchDirectoryException,
                com_brew.BrewBadPathnameException):
            pass
        try:
            if _rs_dir:
                _rs_files=self.listfiles(_rs_dir)
                if type=='ringers':
                    self._mark_files(_files, _rs_files, _local_dir)
                _files.update(_rs_files)
        except (com_brew.BrewNoSuchDirectoryException,
                com_brew.BrewBadPathnameException):
            # dir does not exist, no media files available
            pass
        # del all the markers (empty files) ringers
        if type=='ringers':
            _keys=_files.keys()
            for _key in _keys:
                if not _files[_key]['size']:
                    del _files[_key]
        # dict of all indices
        _idx_keys={}
        for _i in xrange(_index, _index+_maxsize):
            _idx_keys[_i]=True
        # assign existing indices
        for _item in self.getindex(indexfile):
            if _files.has_key(_item.filename):
                _files[_item.filename]['index']=_item.index
                _idx_keys[_item.index]=False
        # available new indices
        _idx_keys_list=[k for k,x in _idx_keys.items() if x]
        _idx_keys_list.sort()
        _idx_cnt=0
        # assign new indices
        _file_list=[x for x in _files if not _files[x].get('index', None)]
        _file_list.sort()
        if len(_file_list)>len(_idx_keys_list):
            _file_list=_file_list[:len(_idx_keys_list)]
        for i in _file_list:
            _files[i]['index']=_idx_keys_list[_idx_cnt]
            _idx_cnt+=1
        # (index, file name) list for writing
        _res_list=[(x['index'],k) for k,x in _files.items() if x.get('index', None)]
        _res_list.sort()
        _res_list.reverse()
        # writing the index file
        ifile=self.protocolclass.indexfile()
        _file_size=0
        for index,idx in _res_list:
            _fs_size=_files[idx]['size']
            ie=self.protocolclass.indexentry()
            ie.index=index
            ie.type=_vtype
            ie.filename=idx
            if _need_date:
                # need to fill in the date value
                _stat=self.statfile(_files[idx]['name'])
                if _stat:
                    ie.date=_stat['datevalue']-time.timezone
            ie.dunno=_dunno
            ie.icon=_icon
            ie.size=_fs_size
            ifile.items.append(ie)
            if not self._is_rs_file(idx):
                _file_size+=_fs_size
        buf=prototypes.buffer()
        ifile.writetobuffer(buf, logtitle="Index file "+indexfile)
        self.log("Writing index file "+indexfile+" for type "+type+" with "+`len(_res_list)`+" entries.")
        self.writefile(indexfile, buf.getvalue())
        # writing the size file
        if sizefile:
            szfile=self.protocolclass.sizefile()
            szfile.size=_file_size
            buf=prototypes.buffer()
            szfile.writetobuffer(buf, logtitle="Updated size file for "+type)
            self.log("You are using a total of "+`_file_size`+" bytes for "+type)
            self.writefile(sizefile, buf.getvalue())

    def savemedia(self, mediakey, mediaindexkey, maps, results, merge, reindexfunction):
        """Actually saves out the media

        @param mediakey: key of the media (eg 'wallpapers' or 'ringtones')
        @param mediaindexkey:  index key (eg 'wallpaper-index')
        @param maps: list index files and locations
        @param results: results dict
        @param merge: are we merging or overwriting what is there?
        @param reindexfunction: the media is re-indexed at the end.  this function is called to do it
        """

        # take copies of the lists as we modify them
        wp=results[mediakey].copy()  # the media we want to save
        wpi=results[mediaindexkey].copy() # what is already in the index files

        # remove builtins
        for k in wpi.keys():
            if wpi[k].get('origin', "")=='builtin':
                del wpi[k]

        # build up list into init
        init={}
        for type,_,_,_,lowestindex,_,typemajor,_,_ in maps:
            init[type]={}
            for k in wpi.keys():
                if wpi[k]['origin']==type:
                    index=k
                    name=wpi[k]['name']
                    fullname=wpi[k]['filename']
                    vtype=wpi[k]['vtype']
                    icon=wpi[k]['icon']
                    data=None
                    del wpi[k]
                    for w in wp.keys():
                        # does wp contain a reference to this same item?
                        if wp[w]['name']==name and wp[w]['origin']==type:
                            data=wp[w]['data']
                            del wp[w]
                    if not merge and data is None:
                        # delete the entry
                        continue
##                    assert index>=lowestindex
                    init[type][index]={'name': name, 'data': data, 'filename': fullname, 'vtype': vtype, 'icon': icon}

        # init now contains everything from wallpaper-index
        # wp contains items that we still need to add, and weren't in the existing index
        assert len(wpi)==0
        print init.keys()

        # now look through wallpapers and see if anything was assigned a particular
        # origin
        for w in wp.keys():
            o=wp[w].get("origin", "")
            if o is not None and len(o) and o in init:
                idx=-1
                while idx in init[o]:
                    idx-=1
                init[o][idx]=wp[w]
                del wp[w]

        # wp will now consist of items that weren't assigned any particular place
        # so put them in the first available space
        for type,_,_,_,lowestindex,maxentries,typemajor,def_icon,_ in maps:
            # fill it up
            for w in wp.keys():
                if len(init[type])>=maxentries:
                    break
                idx=-1
                while idx in init[type]:
                    idx-=1
                init[type][idx]=wp[w]
                del wp[w]

        # time to write the files out
        for type, indexfile, sizefile, directory, lowestindex, maxentries,typemajor,def_icon,_  in maps:
            # get the index file so we can work out what to delete
            names=[init[type][x]['name'] for x in init[type]]
            for item in self.getindex(indexfile):
                if common.basename(item.filename) not in names and \
                   not self._is_rs_file(item.filename):
                    self.log(item.filename+" is being deleted")
                    try:
                        self.rmfile(item.filename)
                    except (com_brew.BrewNoSuchDirectoryException,
                            com_brew.BrewBadPathnameException,
                            com_brew.BrewNoSuchFileException):
                        pass
                    except:
                        if __debug__:
                            raise
            # fixup the indices
            fixups=[k for k in init[type].keys() if k<lowestindex]
            fixups.sort()
            for f in fixups:
                for ii in xrange(lowestindex, lowestindex+maxentries):
                    # allocate an index
                    if ii not in init[type]:
                        init[type][ii]=init[type][f]
                        del init[type][f]
                        break
            # any left over?
            fixups=[k for k in init[type].keys() if k<lowestindex]
            for f in fixups:
                self.log("There is no space in the index for "+type+" for "+init[type][f]['name'])
                del init[type][f]
            # write each entry out
            for idx in init[type].keys():
                entry=init[type][idx]
                filename=entry.get('filename', directory+"/"+entry['name'])
                entry['filename']=filename
                fstat=self.statfile(filename)
                if 'data' not in entry:
                    # must be in the filesystem already
                    if fstat is None:
                        self.log("Entry "+entry['name']+" is in index "+indexfile+" but there is no data for it and it isn't in the filesystem.  The index entry will be removed.")
                        del init[type][idx]
                        continue
                # check len(data) against fstat->length
                data=entry['data']
                if data is None:
                    assert merge
                    continue # we are doing an add and don't have data for this existing entry
                elif not data:
                    self.log('Not writing file: '+filename)
                    continue # data is blank, could be a result of not being able to do a previous get
                if fstat is not None and len(data)==fstat['size']:
                    self.log("Not writing "+filename+" as a file of the same name and length already exists.")
                else:
                    self.writefile(filename, data)
            # write out index
            self._write_index_file(type)
        return reindexfunction(results)

#-------------------------------------------------------------------------------
parentprofile=com_lgvx7000.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX8100'

    WALLPAPER_WIDTH=176
    WALLPAPER_HEIGHT=184
    MAX_WALLPAPER_BASENAME_LENGTH=32
    WALLPAPER_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()_ .-"
    WALLPAPER_CONVERT_FORMAT="jpg"

    # the 8100 uses "W" for wait in the dialstring, it does not support "T"
    DIALSTRING_CHARS="[^0-9PW#*]"

    MAX_RINGTONE_BASENAME_LENGTH=32
    RINGTONE_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()_ .-"

    # there is an origin named 'aod' - no idea what it is for except maybe
    # 'all other downloads'

    # the vx8100 supports bluetooth for connectivity to the PC, define the "bluetooth_mgd_id"
    # to enable bluetooth discovery during phone detection
    # the bluetooth address starts with LG's the three-octet OUI, all LG phone
    # addresses start with this, it provides a way to identify LG bluetooth devices
    # during phone discovery
    # OUI=Organizationally Unique Identifier
    # see http://standards.ieee.org/regauth/oui/index.shtml for more info
    bluetooth_mfg_id="001256"

    ringtoneorigins=('ringers', 'sounds')
    excluded_ringtone_origins=('sounds')
    excluded_wallpaper_origins=('video')


    # the 8100 doesn't have seperate origins - they are all dumped in "images"
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 184, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 128, 'height': 112, 'format': "JPEG"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets


    def __init__(self):
        parentprofile.__init__(self)

    _supportedsyncs=(
        ('phonebook', 'read', None),   # all phonebook reading
        ('calendar', 'read', None),    # all calendar reading
        ('wallpaper', 'read', None),   # all wallpaper reading
        ('ringtone', 'read', None),    # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None),         # all SMS list reading
        ('memo', 'read', None),        # all memo list reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'write', 'MERGE'),       # merge and overwrite ringtone
        ('ringtone', 'write', 'OVERWRITE'),
        ('sms', 'write', 'OVERWRITE'),        # all SMS list writing
        ('memo', 'write', 'OVERWRITE'),       # all memo list writing
        )

    field_color_data={
        'phonebook': {
            'name': {
                'first': 1, 'middle': 1, 'last': 1, 'full': 1,
                'nickname': 0, 'details': 1 },
            'number': {
                'type': 5, 'speeddial': 5, 'number': 5, 'details': 5 },
            'email': 2,
            'address': {
                'type': 0, 'company': 0, 'street': 0, 'street2': 0,
                'city': 0, 'state': 0, 'postalcode': 0, 'country': 0,
                'details': 0 },
            'url': 0,
            'memo': 1,
            'category': 1,
            'wallpaper': 1,
            'ringtone': 2,
            'storage': 0,
            },
        'calendar': {
            'description': True, 'location': False, 'allday': True,
            'start': True, 'end': True, 'priority': False,
            'alarm': True, 'vibrate': True,
            'repeat': True,
            'memo': False,
            'category': False,
            'wallpaper': False,
            'ringtone': True,
            },
        'memo': {
            'subject': True,
            'date': True,
            'secret': False,
            'category': False,
            'memo': True,
            },
        'todo': {
            'summary': False,
            'status': False,
            'due_date': False,
            'percent_complete': False,
            'completion_date': False,
            'private': False,
            'priority': False,
            'category': False,
            'memo': False,
            },
        }
