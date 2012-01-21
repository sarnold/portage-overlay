#!/usr/bin/env python

### BITPIM
###
### 
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
### by David Ritter 7/10/07
### Write to phonebook working msg ringtones not supported
### Write to Calendar, wallpaper, and ringtones is working
###
### $Id: com_lgax8600.py 4595 2008-02-14 03:04:01Z djpham $

"""
Communicate with the LG AX8600 cell phone
"""
# standard modules
import re
import time
import cStringIO
import sha
import datetime

# BitPim modules
import common
import commport
import fileinfo
import guihelper
import os
import copy
import com_lgvx4400
import p_brew
import p_lgax8600
import com_lgvx8100
import com_brew
import com_phone
import com_lg
import prototypes
import bpcalendar
import call_history
import sms
import memo
import playlist
import helpids

#-------------------------------------------------------------------------------
#Went back to vx8100 to inherit to avoid LGUncountedIndexedMedia

parentphone=com_lgvx8100.Phone
class Phone(parentphone):
    "Talk to LG AX-8600 cell phone"

    desc="LG-AX8600"
    helpid=helpids.ID_PHONE_LGAX8600
    protocolclass=p_lgax8600
    serialsname='lgax8600'

    external_storage_root='mmc1/'

    my_model='AX8600'
#Media locations for reading FROM the phone
    builtinringtones= ()
    ringtonelocations= (
       # type       index-file   size-file directory-to-use lowest-index-to-use maximum-entries type-major icon index_offset
 
        ( 'sounds', 'dload/lg_mysound.dat', 'dload/lg_mysoundsize.dat', 'brew/media/lk/ms', 150, 100, 0x402, 0, 0),

 #       ( 'sounds(sd)', 'dload/sd_sound.dat',  'mmc1/lg_media/other_sounds', '', 100, 0x02,  None),

	)

    calendarlocation="sch/schedule.dat"
    calendarexceptionlocation="sch/schexception.dat"
    calenderrequiresreboot=1
    memolocation="sch/memo.dat"

    builtinwallpapers = ()
    wallpaperlocations= (

        # type       index-file   size-file directory-to-use lowest-index-to-use maximum-entries type-major icon index_offset
        ( 'images', 'dload/lg_image.dat', 'dload/lg_imagesize.dat', 'brew/media/lk/mp', 150 , 100, 0x400, 0, 0),

 #       ( 'images(sd)', 'dload/sd_image.dat', 'mmc1/lg_media/other_image',    '',          100, 0x10, None),
 #       ( 'video',      'dload/lg_video.dat', 'brew/media/lk/mf', '',          100, 0x10, None),
 #       ( 'video(sd)',  'dload/sd_video.dat', 'mmc1/lg_media/other_video',   '',          100, 0x13, None),
        )
#    _rs_path=()
    # for removable media (miniSD cards)
    _rs_path='mmc1/'
    _rs_ringers_path=_rs_path+'lg_media/other_sounds'
    _rs_images_path=_rs_path+'lg_media/other_image'

#Media locations for writing TO the phone

    media_info={ 'sounds': {
             'localpath': 'brew/media/lk/ms',
             'rspath': None,
             'vtype': protocolclass.MEDIA_TYPE_SOUND,
             'icon': protocolclass.MEDIA_IMAGE_DEFAULT_ICON,
             'index': 150,
             'maxsize': 100,
             'indexfile': 'dload/lg_mysound.dat',
             'sizefile': 'dload/lg_mysoundsize.dat',
             'dunno': 0,
	     'date': False,
	     'dunno1': 0 },
         'images': {
             'localpath': 'brew/media/lk/mp',
             'rspath': None,
             'vtype': protocolclass.MEDIA_TYPE_IMAGE,
             'icon': protocolclass.MEDIA_IMAGE_DEFAULT_ICON,
             'index': 150,
             'maxsize': 100,
             'indexfile': 'dload/lg_image.dat',
             'sizefile': 'dload/lg_imagesize.dat',
	     'dunno': 0,
	     'date': False,
             'dunno1': 0 },
#         'video': {
#             'localpath': 'brew/16452/mf',
#             'rspath': None,
#             'vtype': protocolclass.MEDIA_TYPE_VIDEO,
#             'icon': protocolclass.MEDIA_VIDEO_DEFAULT_ICON,
#             'index': 1000,
#             'maxsize': 155,
#             'indexfile': 'dload/video.dat',
#             'sizefile': 'dload/videosize.dat',
#             'dunno': 0, 'date': True },
         }
        


    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)
        p_brew.PHONE_ENCODING=self.protocolclass.PHONE_ENCODING
        self.mode=self.MODENONE


    def setDMversion(self):
        self._DMv5=True
	self._timeout = 30

    def get_esn(self, data=None):
        # return the ESN of this phone
        return self.get_brew_esn()

    def get_detect_data(self, res):
        com_lgvx8100.Phone.get_detect_data(self, res)
        res[self.esn_file_key]=self.get_esn()

    #------------------------------------------------------
    # must be included for difference between alltel and verizon
    def getcallhistory(self, result):
        res={}
        # read the incoming call history file
        # the telus lg8100 programmers were on something when they wrote their code.
        if hasattr(self.protocolclass, 'this_takes_the_prize_for_the_most_brain_dead_call_history_file_naming_ive_seen'):
            self._readhistoryfile("pim/missed_log.dat", 'Incoming', res)
            self._readhistoryfile("pim/outgoing_log.dat", 'Missed', res)
            self._readhistoryfile("pim/incoming_log.dat", 'Outgoing', res)
        else:
            self._readhistoryfile("pim/missed_log.dat", 'Missed', res)
            self._readhistoryfile("pim/outgoing_log.dat", 'Outgoing', res)
            self._readhistoryfile("pim/incoming_log.dat", 'Incoming', res)
            self._readhistoryfile("pim/data_log.data", 'Data', res)
        result['call_history']=res
        return result

    # Don't need this if there're no changes
##    def _readhistoryfile(self, fname, folder, res):
##        try:
##            buf=prototypes.buffer(self.getfilecontents(fname))
##            ch=self.protocolclass.callhistory()
##            ch.readfrombuffer(buf, logtitle="Call History")
##            for call_idx in range(ch.numcalls):
##                call=ch.calls[call_idx]
##                if call.number=='' and call.name=='':
##                        continue
##                entry=call_history.CallHistoryEntry()
##                entry.folder=folder
##                if call.duration:
##                    entry.duration=call.duration
##                entry.datetime=((call.GPStime))
##                if call.number=='': # restricted calls have no number
##                    entry.number=call.name
##                else:
##                    entry.number=call.number
##                    if call.name:
##                        entry.name=call.name
##                res[entry.id]=entry
##        except (com_brew.BrewNoSuchFileException,
##                IndexError):
##            pass # do nothing if file doesn't exist or is corrupted
##        return

    def getcalendar(self,result):
        res={}
        # Read exceptions file first
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
                entry.desc_loc=event.description
                try: # delete events are still in the calender file but have garbage dates
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
                except ValueError:
                    continue
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
		    #hack for alltel
		    if entry.alarm==None:
			entry.ringtone='No Ring'
		    else:
			entry.ringtone='Loud Beeps'
#                    entry.ringtone=result['ringtone-index'][event.ringtone]['name']  ## This doesn't work on alltel
                entry.snoozedelay=0
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

    def _build_pb_info(self, fundamentals):
        # build a dict of info to update pbentry
        pbook=fundamentals.get('phonebook', {})
        wallpaper_index=fundamentals.get('wallpaper-index', {})
        ringtone_index=fundamentals.get('ringtone-index', {})
        r1={}
        for k,e in pbook.items():
            r1[e['bitpimserial']['id']]={ 'wallpaper': \
                                          self._findmediainindex(wallpaper_index,
                                                                 e['wallpaper'],
                                                                 e['name'],
                                                                 'wallpaper'),
                                          'msgringtone': \
                                          self._findmediainindex(ringtone_index,
                                                                 e['msgringtone'],
                                                                 e['name'],
                                                                 'message ringtone')}
        serialupdates=fundamentals.get("serialupdates", [])
        r2={}
        for bps, serials in serialupdates:
            r2[serials['serial1']]=r1[bps['id']]
        return r2

    def _update_pb_file(self, pb, fundamentals, pbinfo):
        # update the pbentry file
        update_flg=False
        for e in pb.items:
            _info=pbinfo.get(e.serial1, None)
            if _info:
                wp=_info.get('wallpaper', None)
                if wp is not None and wp!=e.wallpaper:
                    update_flg=True
                    e.wallpaper=wp
                rt=_info.get('ringtone', None)
                if rt is not None and rt!=e.ringtone:
                    update_flg=True
                    e.ringtone=rt
        if update_flg:
            self.log('Updating wallpaper index')
            buf=prototypes.buffer()
            pb.writetobuffer(buf, logtitle="Updated index "+self.protocolclass.pb_file_name)
            self.writefile(self.protocolclass.pb_file_name, buf.getvalue())


    def _update_pb_info(self, pbentries, fundamentals):
        # Manually update phonebook data that the normal protocol should have
        _pbinfo=self._build_pb_info(fundamentals)
        self._update_pb_file(pbentries, fundamentals, _pbinfo)

    def _write_path_index(self, pbentries, pbmediakey, media_index,
                          index_file, invalid_values):
        _path_entry=self.protocolclass.PathIndexEntry()
        _path_file=self.protocolclass.PathIndexFile()
        for _ in range(self.protocolclass.NUMPHONEBOOKENTRIES):
            _path_file.items.append(_path_entry)
        for _entry in pbentries.items:
            _idx=getattr(_entry, pbmediakey)
            if _idx in invalid_values or not media_index.has_key(_idx):
                continue
            if media_index[_idx].get('origin', None)=='builtin':
                _filename=media_index[_idx]['name']
            elif media_index[_idx].get('filename', None):
                _filename=media_index[_idx]['filename']
            else:
                continue
            _path_file.items[_entry.entrynumber]=self.protocolclass.PathIndexEntry(
                pathname=_filename)
        _buf=prototypes.buffer()
        _path_file.writetobuffer(_buf, logtitle='Writing Path ID')
        self.writefile(index_file, _buf.getvalue())

# Must be included due to changed indexfile format
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
	_dunno1=_info['dunno1']
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
	    ie.dunno1=_dunno1
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
 
# Must be there since there are no msg ringtones on ax8600

    def savephonebook(self, data):
        "Saves out the phonebook"

        res=com_lgvx4400.Phone.savephonebook(self, data)
        # retrieve the phonebook entries

        _buf=prototypes.buffer(self.getfilecontents(self.protocolclass.pb_file_name))
        _pb_entries=self.protocolclass.pbfile()
        _pb_entries.readfrombuffer(_buf, logtitle="Read phonebook file "+self.protocolclass.pb_file_name)

        # update info that the phone software failed to do!!
        self._update_pb_info(_pb_entries, data)
 
        return res

    # Misc Stuff----------------------------------------------------------------
    def get_firmware_version(self):
        # return the firmware version
        req=p_brew.firmwarerequest()
        res=self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
        return res.firmware

    def _unlock_key(self):
        _req=self.protocolclass.LockKeyReq(lock=1)
        self.sendbrewcommand(_req, self.protocolclass.data)
    def _lock_key(self):
        _req=self.protocolclass.LockKeyReq()
        self.sendbrewcommand(_req, self.protocolclass.data)

    def _press_key(self, keys):
        # simulate a series of keypress
        if not keys:
            return
        _req=self.protocolclass.KeyPressReq()
        for _k in keys:
            _req.key=_k
            self.sendbrewcommand(_req, self.protocolclass.data)


#-------------------------------------------------------------------------------
parentprofile=com_lgvx8100.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='AX8600'
    # inside screen resoluation
    WALLPAPER_WIDTH=176
    WALLPAPER_HEIGHT=220

    MAX_WALLPAPER_BASENAME_LENGTH=32
    WALLPAPER_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_() ."
    WALLPAPER_CONVERT_FORMAT="jpg"

    # the 8300 uses "W" for wait in the dialstring, it does not support "T"
    DIALSTRING_CHARS="[^0-9PW#*]"

    MAX_RINGTONE_BASENAME_LENGTH=32
    RINGTONE_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_() ."
    RINGTONE_LIMITS= {
        'MAXSIZE': 200000
    }
#    MSGRINGTONE=None

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
#    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
#    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
#    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))

    # our targets are the same for all origins
    imagetargets={}
##    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
##                                      {'width': 176, 'height': 220, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))
#    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
#                                      {'width': 128, 'height': 160, 'format': "JPEG"}))
##    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
##                                      {'width': 128, 'height': 142, 'format': "JPEG"}))


    def GetImageOrigins(self):
        return self.imageorigins

    ringtoneorigins=('ringers', 'sounds')
    excluded_ringtone_origins=('ringers')
    excluded_wallpaper_origins=('video')


    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets

    def QueryAudio(self, origin, currentextension, afi):
        _max_size=self.RINGTONE_LIMITS['MAXSIZE']
        setattr(afi, 'MAXSIZE', _max_size)
        # we don't modify any of these
        if afi.format in ("MIDI", "QCP", "PMD", "WMA"):
            return currentextension, afi
        # examine mp3
        if afi.format=="MP3":
            if afi.channels==1 and 8<=afi.bitrate<=64 and 16000<=afi.samplerate<=22050:
                return currentextension, afi
        # convert it
        return ("mp3", fileinfo.AudioFileInfo(afi, **{'format': 'MP3',
                                                      'channels': 2,
                                                      'bitrate': 48,
                                                      'samplerate': 44100,
                                                      'MAXSIZE': _max_size }))

    def __init__(self):
        parentprofile.__init__(self)

 
    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
##        ('sms', 'read', None),         # all SMS list reading
        ('memo', 'read', None),        # all memo list reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
        ('ringtone', 'write', 'OVERWRITE'),
##        ('sms', 'write', 'OVERWRITE'),        # all SMS list writing
        ('memo', 'write', 'OVERWRITE'),       # all memo list writing
##        ('t9_udb', 'read', 'OVERWRITE'),
##        ('t9_udb', 'write', 'OVERWRITE'),
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
            'memo': 0,
            'category': 1,
            'wallpaper': 1,
            'ringtone': 2,
            'storage': 0,
            },
        'calendar': {
            'description': True, 'location': False, 'allday': False,
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
