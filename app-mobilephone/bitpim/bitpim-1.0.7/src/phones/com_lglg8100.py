### BITPIM
###
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2006 Simon Capper <skyjunky@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lglg8100.py 4303 2007-07-13 20:46:53Z djpham $

"""Communicate with the LG VX5200 cell phone


The code in this file mainly inherits from VX8100 code and then extends where
the 5200 has different functionality

"""

# standard modules
import time
import calendar
import cStringIO
import sha

# my modules
import common
import commport
import copy
import com_lgvx4400
import p_brew
import p_lglg8100
import com_lgvx8100
import com_brew
import com_phone
import com_lg
import prototypes
import bpcalendar
import call_history
import sms
import memo

class Phone(com_lgvx8100.Phone):
    "Talk to the LG LG8100 cell phone (Telus)"

    desc="LG-LG8100"
    helpid=None
    protocolclass=p_lglg8100
    serialsname='lglg8100'

    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps') + \
                      tuple(['Ringtone '+`n` for n in range(1,11)]) + \
                      ('No Ring',)

    ringtonelocations= (
        # type       index-file   size-file directory-to-use lowest-index-to-use maximum-entries type-major icon
        ( 'ringers', 'dload/aod.dat', 'dload/aodsize.dat', 'brew/16452/mds', 1000, 150, 6, 1, 0),
        # the sound index file uses the same index as the ringers, bitpim does not support this (yet)
#        ( 'sounds', 'dload/mysound.dat', 'dload/mysoundsize.dat', 'brew/16452/ms', 100, 150, 2, 0, 151),
        )

    calendarlocation="sch/newschedule.dat"
    calendarexceptionlocation="sch/newschexception.dat"
    calenderrequiresreboot=1
    memolocation="sch/neomemo.dat"

    builtinwallpapers = () # none

    wallpaperlocations= (
        ( 'images', 'dload/image.dat', 'dload/imagesize.dat', 'brew/16452/mp', 100, 50, 0x300, 0, 0),
        #( 'video', 'dload/video.dat', None, 'brew/16452/mf', 1000, 50, 0x0304, 0, 0),
        )
        
    # for removable media (miniSD cards)
    _rs_path='mmc1/'
    _rs_ringers_path=_rs_path+'ringers'
    _rs_images_path=_rs_path+'images'
    media_info={ 'ringers': {
            'localpath': 'brew/16452/mds',
            'rspath': _rs_ringers_path,
            'vtype': protocolclass.MEDIA_TYPE_RINGTONE,
            'icon': protocolclass.MEDIA_RINGTONE_DEFAULT_ICON,
            'index': 1000,  # starting index
            'maxsize': 155,
            'indexfile': 'dload/aod.dat',
            'sizefile': 'dload/aodsize.dat',
            'dunno': 0, 'date': True,
        },
#         'sounds': {
#             'localpath': 'brew/16452/ms',
#             'rspath': None,
#             'vtype': protocolclass.MEDIA_TYPE_SOUND,
#             'icon': protocolclass.MEDIA_IMAGE_DEFAULT_ICON,
#             'index': 100,
#             'maxsize': 155,
#             'indexfile': 'dload/mysound.dat',
#             'sizefile': 'dload/mysoundsize.dat',
#             'dunno': 0, 'date': False },
         'images': {
             'localpath': 'brew/16452/mp',
             'rspath': _rs_images_path,
             'vtype': protocolclass.MEDIA_TYPE_IMAGE,
             'icon': protocolclass.MEDIA_IMAGE_DEFAULT_ICON,
             'index': 100,
             'maxsize': 155,
             'indexfile': 'dload/image.dat',
             'sizefile': 'dload/imagesize.dat',
             'dunno': 0, 'date': True },
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
        com_lgvx4400.Phone.__init__(self,logtarget,commport)
        self.mode=self.MODENONE

    def __del__(self):
        pass

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
                    entry.end=event.end
                except ValueError:
                    continue
                if event.alarmindex_vibrate&0x1:
                    entry.vibrate=0 # vibarate bit is inverted in phone 0=on, 1=off
                else:
                    entry.vibrate=1
                entry.repeat = self.makerepeat(event.repeat, event.start)
                min=event.alarmminutes
                hour=event.alarmhours
                if min==0x64 or hour==0x64:
                    entry.alarm=None # no alarm set
                else:
                    entry.alarm=hour*60+min
                entry.ringtone=result['ringtone-index'][event.ringtone]['name']
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

    def makerepeat(self, repeat, start):
        # get all the variables out of the repeat tuple
        # and convert into a bpcalender RepeatEntry
        type,dow,interval,interval2,exceptions=repeat
        #print "repeat "+`repeat`+" start "+`start`
        if type==0:
            repeat_entry=None
        else:
            repeat_entry=bpcalendar.RepeatEntry()
            if type==1: #daily
                repeat_entry.repeat_type=repeat_entry.daily
                repeat_entry.interval=interval
            elif type==2: #'monfri'
                repeat_entry.repeat_type=repeat_entry.daily
                repeat_entry.interval=0
            elif type==3: #'weekly'
                repeat_entry.repeat_type=repeat_entry.weekly
                repeat_entry.interval=interval
            elif type==5: #'monthly'
                repeat_entry.repeat_type=repeat_entry.monthly
                repeat_entry.interval2=interval2
                repeat_entry.dow=0
            elif type==4: #'monthly' #Xth Y day (e.g. 2nd friday each month)
                repeat_entry.repeat_type=repeat_entry.monthly
                repeat_entry.interval=interval #X
                repeat_entry.dow=dow #Y
                repeat_entry.interval2=interval2
            elif type==6: #'yearly #Xth Y day of Month (2nd sunday of april)' Not supported by bitpim
                #repeat_entry.repeat_type=repeat_entry.yearly
                repeat_entry=None
            else: # =7 'yearly'
                repeat_entry.repeat_type=repeat_entry.yearly
        return repeat_entry

    def setalarm(self, entry, data):
        # vx8100 only allows certain repeat intervals, adjust to fit, it also stores an index to the interval
        rc=True
        if entry.alarm>=10080:
            entry.alarm=10080
            data.alarmminutes=0
            data.alarmhours=168 # 1 week
            data.alarmindex_vibrate=0xe
        elif entry.alarm>=4320:
            entry.alarm=4320
            data.alarmminutes=0
            data.alarmhours=72 # 3 days
            data.alarmindex_vibrate=0xc
        elif entry.alarm>=1440:
            entry.alarm=1440
            data.alarmminutes=0
            data.alarmhours=24 # 1 day
            data.alarmindex_vibrate=0xa
        elif entry.alarm>=60:
            entry.alarm=60
            data.alarmminutes=0
            data.alarmhours=1 # 1 hour
            data.alarmindex_vibrate=0x8
        elif entry.alarm>=30:
            entry.alarm=30
            data.alarmminutes=30
            data.alarmhours=0 # 30 mins
            data.alarmindex_vibrate=0x6
        elif entry.alarm>=15:
            entry.alarm=15
            data.alarmminutes=15
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
        # number of entries
        eventsf.numactiveitems=len(keys)
        pos=0
        contains_alarms=False        
        # play with each entry
        for (_,k) in keys:
            # entry is what we will return to user
            entry=cal[k]
            data=self.protocolclass.scheduleevent()
            data.index=pos
            pos+=1
            data.pos=eventsf.packetsize()
            data.description=entry.desc_loc
            data.start=entry.start
            data.end=entry.end
            alarm_set=self.setalarm(entry, data)
            data.ringtone=0
            if alarm_set:
                if entry.ringtone=="No Ring" and not entry.vibrate:
                    alarm_name="Low Beep Once"
                else:
                    alarm_name=entry.ringtone
            else:# set alarm to "No Ring" gets rid of alarm icon on phone
                alarm_name="No Ring"
            for i in dict['ringtone-index']:
                if dict['ringtone-index'][i]['name']==alarm_name:
                    data.ringtone=i
            # check for exceptions and add them to the exceptions list
            exceptions=0
            if entry.repeat!=None:
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
            if data.alarmindex_vibrate!=1: # if alarm set
                contains_alarms=True
            # put entry in nice shiny new dict we are building
            entry=copy.copy(entry)
            newcal[data.pos]=entry
            eventsf.events.append(data)

        buf=prototypes.buffer()
        eventsf.writetobuffer(buf, logtitle="New Calendar")
        # We check the existing calender as changes require a reboot for the alarms
        # to work properly, also no point writing the file if it is not changing
        if buf.getvalue()!=self.getfilecontents(self.calendarlocation):
            self.writefile(self.calendarlocation, buf.getvalue())
            if contains_alarms or self.calenderrequiresreboot:
                self.log("Your phone has to be rebooted due to the calendar changing")
                dict["rebootphone"]=True
        else:
            self.log("Phone calendar unchanged, no update required")

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
                type=5
            else:
                interval=entry.repeat.interval
                type=4
        elif entry.repeat.repeat_type==repeat_entry.daily:
            dow=entry.repeat.dow
            interval=entry.repeat.interval
            if entry.repeat.interval==0:
                type=2
            else:
                type=1
        elif entry.repeat.repeat_type==repeat_entry.weekly:
            dow=entry.repeat.dow
            interval=entry.repeat.interval
            type=3
        elif entry.repeat.repeat_type==repeat_entry.yearly:
            # set interval to start day of month, (required by vx8100)
            interval=entry.start[2]
            # set dow to start month, (required by vx8100)
            dow=entry.start[1]
            type=7
        return (type, dow, interval, interval2, exceptions)

    def eval_detect_data(self, res):
        found=False
        if res.get(self.brew_version_txt_key, None) is not None:
            found=res[self.brew_version_txt_key][:len(self.my_version_txt)]==self.my_version_txt
        if found:
            res['model']=self.my_model
            res['manufacturer']='LG Electronics Inc'
            s=res.get(self.esn_file_key, None)
            if s:
                res['esn']=self.get_esn(s)

    my_version_txt='CX8100'
    my_model='LG8100'


    # Media stuff---------------------------------------------------------------
    # Bypassing the 8100/9800 specific stuff
#    def getmedia(self, maps, results, key):
 #       return com_lg.LGNewIndexedMedia2.getmedia(self, maps, results, key)
  #  def savemedia(self, mediakey, mediaindexkey, maps, results, merge, reindexfunction):
   #     return com_lg.LGNewIndexedMedia2.savemedia(self, mediakey, mediaindexkey, maps, results, merge, reindexfunction)

parentprofile=com_lgvx8100.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='LG8100'

    WALLPAPER_WIDTH=176
    WALLPAPER_HEIGHT=220
    MAX_WALLPAPER_BASENAME_LENGTH=32
    WALLPAPER_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()-_ ."
    WALLPAPER_CONVERT_FORMAT="jpg"
   
    # the 8100 uses "W" for wait in the dialstring, it does not support "T"
    DIALSTRING_CHARS="[^0-9PW#*]"

    MAX_RINGTONE_BASENAME_LENGTH=32
    RINGTONE_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()-_ ."

    # the 8100 doesn't have seperate origins - they are all dumped in "images"
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 128, 'height': 128, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets

 
    def __init__(self):
        parentprofile.__init__(self)

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None),         # all SMS list reading
        ('memo', 'read', None),        # all memo list reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
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
            'description': True, 'location': True, 'allday': True,
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
