### BITPIM
###
### Copyright (C) 2006 Denis Tonn <denis@tonn.ca>
### Inspiration and code liberally adopted from:
### Stephen A. Wood and Joe Pham
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$

"""Communicate with a Samsung SPH-A840 from Telus Canada"""

# Notes: 
#
# This Phone does not cleanly return from BREW mode, so everything is
# done through modem mode. 
#
# Groups are handled differently on this phone, so I have hard coded
# them. In any event, there is no way to query them as part of a
# PBentry. Restoring data to a phone loses group assignments.  
# at#pbgrw does not modify group names - seems to be ignored in phone
# even though it returns OK.   
#
# Cannot query/extract Ringtones so that is hard coded. Built in tones
# are ok and can be changed through BitPim.
#
# Cannot query/extract Wallpaper so builtin values are hardcoded and
# everything else is maintained through a write to phone  
#
# Special case email and url fields. If these are blank they MUST have
# a quoted space in the write or phone data is corrupted.
#
# uslot 1 should not be used. I have not done anything in this code to
# prevent it, but the phone will complain if you try and edit a
# pbentry with uslot = 1. Change the "location" on the phone and it's
# fine.
#
# There is no way of setting (or unsetting) a "secret" pbentry on this
# phone.
# 
# Calendar writes fail (ERROR) unless start_time and end_time are the
# same. 
#
# Occasionally the phone will have position 0 as the speeddial number,
# when it has only one number even when that number isn't in position
# 0.
#

import time
import datetime

import sha
import re
import struct

import bpcalendar
import prototypes
import todo
import memo

import common
import commport
import p_brew
import p_samsungspha840_telus
import com_brew
import com_phone
import com_samsung_packet
import helpids

numbertypetab=('home','office','cell','pager','fax')


### Phone class 

parentphone=com_samsung_packet.Phone
class Phone(parentphone):
    "Talk to a Samsung SPH-A840 phone (Telus)"

    __read_timeout=0.5
    __cal_end_datetime_value=None
    __cal_alarm_values={0: -1, 1: 0, 2: 10, 3: 30, 4: 60 }
    __cal_max_name_len=32
    _cal_max_events_per_day=5

    desc="SPH-A840 (Telus)"
    helpid=helpids.ID_PHONE_SAMSUNGOTHERS
    protocolclass=p_samsungspha840_telus
    serialsname='spha840T'
    
    builtin_ringtones=(
        (0, ['Default Tone']),
        (1, ['Ring %02d'%x for x in range(1, 6)]),
        (6, ['Melody %02d'%x for x in range(1, 6)]),
        )

# wallpaper values 
# 8 = no image
# 3 = human  1-20
# 4 = animal 1-15
# 5 = others 1-10
# 2 = gallery - and wallpaper_pic_path points to the file name
# 7 = image clips 

# wallpaper_modifier   
# selects specific image in human, animal, others
# selects offset in file for image clips
# must be 0 if no image
# value ignored if gallery image

    builtin_pictures=(
        (0, ['Human %02d'%x for x in range(1, 21)]),
        (30, ['Animal %02d'%x for x in range(1, 16)]),
        (60, ['Other %02d'%x for x in range(1, 11)]),
        (80, ['On Phone Image']),
        )

    def __init__(self, logtarget, commport):
        com_samsung_packet.Phone.__init__(self, logtarget, commport)
        self.numbertypetab=numbertypetab
        self.mode=self.MODENONE

    def getfundamentals(self, results):
        """Gets information fundamental to interoperating with the phone and UI."""
    # use a hash of ESN and other stuff (being paranoid)
        self.log("Retrieving fundamental phone information")
        self.log("Phone serial number")
        self.setmode(self.MODEMODEM)
        results['uniqueserial']=sha.new(self.get_esn()).hexdigest()
    # getting ringtone-index
        self.log("Setting up Built in Ring Tone index")
        results['ringtone-index']=self._get_builtin_index(self.builtin_ringtones)
    # getting wallpaper-index
        self.log("Setting up Built in Wallpaper index")
        results['wallpaper-index']=self.get_wallpaper_index()
        self.log("Ignoring Corrupted Phone group information")
    # groups are hard coded since this phone corrupts the read of groups
        results['groups']=self.read_groups()
        self.log("Fundamentals retrieved")
        return results
        
    def _get_builtin_index(self, builtin_list):
        _res={}
        for _starting_idx,_list in builtin_list:
            _idx=_starting_idx
            for _entry in _list:
                _res[_idx]={ 'name': _entry,
                             'origin': 'builtin' }
                _idx+=1
        return _res

    def get_wallpaper_index(self):
        _res=self._get_builtin_index(self.builtin_pictures)
        return _res

    def pblinerepair(self, line):
        "Extend incomplete lines"
        nfields=24                      # Can we get this from packet def?
        ncommas=self.countcommas(line)
        if ncommas<0:                   # Un terminated quote
            line+='"'
            ncommas = -ncommas
        if nfields-ncommas>1:
            line=line+","*(nfields-ncommas-1)
        return line

    def countcommas(self, line):
        inquote=False
        ncommas=0
        for c in line:
            if c == '"':
                inquote = not inquote
            elif not inquote and c == ',':
                ncommas+=1
        if inquote:
            ncommas = -ncommas
        return ncommas
        
    def savewallpapers(self, result):
        raise NotImplementedError()

    def saveringtones(self, result):
        raise NotImplementedError()
        
    def getringtones(self, results):
        raise NotImplementedError()
        
    def getwallpapers(self, results):
        raise NotImplementedError()

    def read_groups(self):
  # This phone returns crap for group names which causes an assertion error in the database
  # because of duplicate "blank" names in the groups. 
  # so to bypass I have set the group names manually
        g={}
        g[0]={'name': "Friends"}
        g[1]={'name': "Business"}
        g[2]={'name': "Family"}
        g[3]={'name': "General"}
        g[4]={'name': "No Group"}
	return g


    def savegroups(self, data):
        """This phone doesn't save or read groups properly
        so we are skipping the save"""
        return



#
#
# Called by extractphonebookentry to extract wallpaper from phone entry data 
#
#
    def _extract_wallpaper(self, res, entry, fundamentals):
# wallpaper values 
# 8 = no image
# 3 = human  1-20 res index 1-20
# 4 = animal 1-15 res index 30-45
# 5 = others 1-10 res index 60-70
# 2 = gallery - and wallpaper_pic_path points to the file name
# 6 or 7 = image clips - modifier selects offset in image file
# 1 = I assume downloaded - never downloaded a wallpaper
# gallery and images and downloads are treated separately as index 80
#   - save just keeps whatever wallpaper data the phone already has and is not managed by bitpim

# wallpaper_modifier   
# selects specific image in human, animal, others
# selects offset in file for image clips
# must be 0 if no image
# value ignored if gallery image file name
        _wp_index=fundamentals.get('wallpaper-index', {})
        if entry.wallpaper==8:
            return # no image  
        if entry.wallpaper in (0,1,2,6,7):
            wallpaper_index=80  # use "on phone" dict entry name in bitpim and recycle current phone data
        if entry.wallpaper==3:
            wallpaper_index=entry.wallpaper_modifier
        if entry.wallpaper==4:
            wallpaper_index=30+entry.wallpaper_modifier
        if entry.wallpaper==5:
            wallpaper_index=60+entry.wallpaper_modifier
   # get the name out of the dict  
        _wp_name=_wp_index.get(wallpaper_index, {}).get('name', None)
        if _wp_name:
            res['wallpapers']=[{ 'wallpaper': _wp_name,  'use': 'call' }]

#
#
# Called by extractphonebookentry to extract ringtone from phone entry data 
#
#
    def _extract_ringtone(self, res, entry, fundamentals):
        _rt_index=fundamentals.get('ringtone-index', {})
        _rt_name=_rt_index.get(entry.ringtone, {}).get('name', None)
        if _rt_name:
            res['ringtones']=[{ 'ringtone': _rt_name, 'use': 'call' }]

#
#
# Called by getphonebook to extract single phone entry data 
#
#
    def extractphonebookentry(self, entry, fundamentals):
        res={}
        res['serials']=[ {'sourcetype': self.serialsname,
                          'slot': entry.slot,
                          'sourceuniqueid': fundamentals['uniqueserial']} ]
    # only one name
        res['names']=[ {'full': entry.name} ]
    # only one category
        cat=fundamentals['groups'].get(entry.group, {'name': "Unassigned"})['name']
        if cat!="Unassigned":
            res['categories']=[ {'category': cat} ]
    # only one email
        if len(entry.email):
            res['emails']=[ {'email': entry.email} ]
    # only one url
        if len(entry.url):
            res['urls']=[ {'url': entry.url} ]
        res['numbers']=[]
        secret=0
        speeddialtype=entry.speeddial
        speeddial_has_been_set=0 # need this for fix for bad phonebook data
        numberindex=0
        for type in self.numbertypetab:
            if len(entry.numbers[numberindex].number):
                numhash={'number': entry.numbers[numberindex].number, 'type': type }
#                if entry.numbers[numberindex].secret==1:
#                    secret=1
                self.log("ENTRY -speeddial : "+str(speeddialtype)+" -index : "+str(numberindex)+" -uslot : "+str(entry.slot))
           # fix possible bad phone data - always force dial entry to first number as safety measure
           # Otherwise we will lose the uslot data completely
                if speeddial_has_been_set==0:
                    numhash['speeddial']=entry.uslot
                    speeddial_has_been_set=1
                if speeddialtype==numberindex:
                    numhash['speeddial']=entry.uslot
                    speeddial_has_been_set=1
                self.log("EXIT -speeddial : "+str(speeddialtype)+" -index : "+str(numberindex)+" -uslot : "+str(entry.slot))
                res['numbers'].append(numhash)
            numberindex+=1

    # Field after each number is secret flag.  Setting secret on
    # phone sets secret flag for every defined phone number
        res['flags']=[ {'secret': secret} ]
        _args=(res, entry, fundamentals)
        self._extract_wallpaper(*_args)
        self._extract_ringtone(*_args)
        return res

#
#
# Get the phone book
#
#
    def getphonebook(self, result):
        """Read the phonebook data."""
        pbook={}
        self.setmode(self.MODEPHONEBOOK)

        count=0
        req=self.protocolclass.phonebookslotrequest()
        lastname=""
        for slot in range(1,self.protocolclass.NUMPHONEBOOKENTRIES+1):
            req.slot=slot
            res=self.sendpbcommand(req, self.protocolclass.phonebookslotresponse, fixup=self.pblinerepair)
            if len(res) > 0:
                lastname=res[0].entry.name
                if len(lastname)>0: 
                   self.log(`slot`+": "+lastname+" uSlot : "+str(res[0].entry.uslot))
                entry=self.extractphonebookentry(res[0].entry, result)
                pbook[count]=entry
                count+=1
            self.progress(slot, self.protocolclass.NUMPHONEBOOKENTRIES, lastname)
        result['phonebook']=pbook
        cats=[]
        for i in result['groups']:
            if result['groups'][i]['name']!='Unassigned':
                cats.append(result['groups'][i]['name'])
        result['categories']=cats
        self.setmode(self.MODEMODEM)
        return pbook

#
#
# Called by savephonebook to create an initial phone book entry
#
#
    def makeentry(self, entry, data):
        e=self.protocolclass.pbentry()
        for k in entry:
         # special treatment for lists
            if k=='numbertypes' or k=='secrets':
                continue
         # get a phone index for the ring tone name
            if k=='ringtone':
                _rt_index=data.get('ringtone-index', {})
                for rgt in _rt_index.keys():
                  _rt_name=_rt_index.get(rgt, {}).get('name', None)
                  if _rt_name==entry['ringtone']:
                      e.ringtone=rgt # and save it for the phonebook entry 
                continue
        # get a a pair of indexs for the wallpaper name - wallpaper and wallpaper_modifier
            elif k=='wallpaper':
        # setup default values - no image
                e.wallpaper=8
                e.wallpaper_modifier=0
                e.wallpaper_file=""
        # now see if we have anything stored in the database
                _wp_index=data.get('wallpaper-index', {})
                for wpn in _wp_index.keys():
                    _wp_name=_wp_index.get(wpn, {}).get('name', None)
                    if _wp_name==entry['wallpaper']: # found the name, now convert to a pair of phone indexes
                         if wpn<30:                   # built in Human type, modifier is wpn
                             e.wallpaper=3
                             e.wallpaper_modifier=wpn
                         if wpn>29 and wpn<60:        # built in Animals type, modifier is wpn-30
                             e.wallpaper=4
                             e.wallpaper_modifier=wpn-30
                         if wpn>59 and wpn<80:        # built in Others type, modifier is wpn-60
                             e.wallpaper=5
                             e.wallpaper_modifier=wpn-60
                         if wpn==80:                   # on phone - special processing in caller code
                             e.wallpaper=8
                             e.wallpaper_modifier=8   # will not be stored on phone just a sig
                continue
            elif k=='numbers':
                for numberindex in range(self.protocolclass.NUMPHONENUMBERS):
                    enpn=self.protocolclass.phonenumber()
                    e.numbers.append(enpn)
                for i in range(len(entry[k])):
                    numberindex=entry['numbertypes'][i]
                    e.numbers[numberindex].number=entry[k][i]
#                    e.numbers[numberindex].secret=entry['secrets'][i]
                    e.numbers[numberindex].secret=0
                continue
          # everything else we just set
            setattr(e, k, entry[k])

        return e

#
#
# Save the phone book
#
#
    def savephonebook(self, data):
        "Saves out the phonebook"

        pb=data['phonebook']
        keys=pb.keys()
        keys.sort()
        keys=keys[:self.protocolclass.NUMPHONEBOOKENTRIES]

        self.setmode(self.MODEPHONEBOOK)
  # 1- Read the existing phonebook so that we cache birthday field and wallpaper file path and stuff
  # 2- Erase all entries. 
        uslots={}
        names={}
        birthdays={}
        wallpaper_s={}
        wallpaper_files={}
        wallpaper_modifiers={}
        req=self.protocolclass.phonebookslotrequest()

        self.log('Erasing '+self.desc+' phonebook')
        progressmax=self.protocolclass.NUMPHONEBOOKENTRIES+len(keys)
        for slot in range(1,self.protocolclass.NUMPHONEBOOKENTRIES+1):
            req.slot=slot
            self.progress(slot,progressmax,"Erasing  "+`slot`)
            try:
                res=self.sendpbcommand(req,self.protocolclass.phonebookslotresponse, fixup=self.pblinerepair)
                if len(res) > 0:
                    self.log("Starting capture data for : "+res[0].entry.name)
                    names[slot]=res[0].entry.name
                    birthdays[slot]=res[0].entry.birthday
                    wallpaper_s[slot]=res[0].entry.wallpaper
                    wallpaper_files[slot]=res[0].entry.wallpaper_file
                    wallpaper_modifiers[slot]=res[0].entry.wallpaper_modifier
                    self.log("Captured data for : "+res[0].entry.name)
                    self.log("User Slot from phone: "+str(res[0].entry.uslot))
                else:
                    names[slot]=""
            except:
                names[slot]=""
                self.log("Slot "+`slot`+" Empty slot or read failed")
            reqerase=self.protocolclass.phonebooksloterase()
            reqerase.slot=slot
            self.sendpbcommand(reqerase, self.protocolclass.phonebookslotupdateresponse)
  # Skip this.. the group save commands don't work
  #      self.savegroups(data)

        for i in range(len(keys)):
            slot=keys[i]
            req=self.protocolclass.phonebookslotupdaterequest()
            req.entry=self.makeentry(pb[slot],data)
  # groups are not handled through the phonebook data on this phone
            req.entry.group=self.protocolclass.DEFAULT_GROUP 

  # force a single space into email and url if they are zero length
            if len(req.entry.email)==0:
                req.entry.email=" "
            if len(req.entry.url)==0: 
                req.entry.url=" "
  # restore the stuff we may not have in the database
            if names[slot]==req.entry.name:
                req.entry.birthday=birthdays[slot] # no analogy on bitpim database, just keep with entry
            # test for internal sig and keep whatever wallpaper is already on the phone
                if req.entry.wallpaper==self.protocolclass.DEFAULT_WALLPAPER and req.entry.wallpaper_modifier==8: # yup, keep previous stuff
                     req.entry.wallpaper=wallpaper_s[slot]
                     req.entry.wallpaper_file=wallpaper_files[slot]
                     req.entry.wallpaper_modifier=wallpaper_modifiers[slot]
  # make sure the default wallpaper has no modifier applied
            if req.entry.wallpaper==self.protocolclass.DEFAULT_WALLPAPER:  
                req.entry.wallpaper_modifier=self.protocolclass.DEFAULT_WALLPAPER_MODIFIER
            self.log('Writing entry '+`slot`+" - "+req.entry.name+" uSlot : "+str(req.entry.uslot))
            self.log('Request: '+str(req))
            self.progress(i+self.protocolclass.NUMPHONEBOOKENTRIES,progressmax,"Writing "+req.entry.name)
            self.sendpbcommand(req, self.protocolclass.phonebookslotupdateresponse)
        self.progress(progressmax+1,progressmax+1, "Phone book write completed")
        self.setmode(self.MODEMODEM)
        return data
#
#
# Get the phone Calendar
#
#
    def getcalendar(self, result):
        entries = {}
        self.log("Getting calendar entries")
        self.setmode(self.MODEPHONEBOOK)
        req=self.protocolclass.eventrequest()
        cal_cnt=0
        for slot in range(self.protocolclass.NUMCALENDAREVENTS):
            req.slot=slot
            res=self.sendpbcommand(req,self.protocolclass.eventresponse)
            if len(res) > 0:
                self.progress(slot+1, self.protocolclass.NUMCALENDAREVENTS,
                              res[0].eventname)
                # build a calendar entry
                entry=bpcalendar.CalendarEntry()
                # start time date
                entry.start=res[0].start[0:5]
                if res[0].end:
                    # valid end time
                    entry.end=res[0].start[0:5]
                else:
                    entry.end=entry.start
                # description
                entry.description=res[0].eventname
                try:
                    alarm=self.__cal_alarm_values[res[0].alarm]
                except:
                    alarm=None
                entry.alarm=alarm
                # update calendar dict
                entries[entry.id]=entry
                cal_cnt += 1
        result['calendar']=entries
        self.setmode(self.MODEMODEM)
        return result

#
#
# Save the phone Calendar
#
#
    def savecalendar(self, dict, merge):
        self.log("Sending calendar entries")
        cal=self.process_calendar(dict['calendar'])
        # testing
        if __debug__:
            print 'processed calendar: ', len(cal), ' items'
            for c in cal:
                print c.description,':', c.start
        self.setmode(self.MODEPHONEBOOK)
        self.log("Saving calendar entries")
        cal_cnt=0
        req=self.protocolclass.eventupdaterequest()
        l = self.protocolclass.NUMCALENDAREVENTS
        for c in cal:
      # Save this entry to phone
            # self.log('Item %d' %k)
      # pos
            req.slot=cal_cnt
      # start date time
            # print "Start ",c.start
            req.start=list(c.start)+[0]
      # end date time must be the same as start time for this phone write
            req.end=req.start
      # time stamp
            req.timestamp=list(time.localtime(time.time())[0:6])
            # print "Alarm ",c.alarm
            req.alarm=c.alarm
      # Name, check for bad char & proper length
            # name=c.description.replace('"', '')
            name=c.description
            if len(name)>self.__cal_max_name_len:
                name=name[:self.__cal_max_name_len]
            req.eventname=name
      # and save it
            self.progress(cal_cnt+1, l, "Updating "+name)
            self.sendpbcommand(req,self.protocolclass.eventupdateresponse)
            cal_cnt += 1
      # delete the rest of the calendar slots
        self.log('Deleting unused entries')
        for k in range(cal_cnt, l):
            self.progress(k, l, "Deleting entry %d" % k)
            reqerase=self.protocolclass.eventsloterase()
            reqerase.slot=k
            self.sendpbcommand(reqerase, self.protocolclass.eventupdateresponse)
        self.setmode(self.MODEMODEM)

        return dict

#### Profile class 
 
parentprofile=com_samsung_packet.Profile
class Profile(parentprofile):
    deviceclasses=("modem",)

    BP_Calendar_Version=3
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SAMSUNG ELECTRONICS CO.,LTD.'
    phone_model='SCH-A850 /180'

    def __init__(self):
        parentprofile.__init__(self)
        self.numbertypetab=numbertypetab
        
    _supportedsyncs=(
 	('phonebook', 'read', None),  # all phonebook reading
 	('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE')   # only overwriting calendar
  	)

    # fill in the list of ringtone/sound origins on your phone
    ringtoneorigins=('ringers')
    #e.g.
    #ringtoneorigins=('ringers', 'sounds')

class Samsung_Calendar:
    _cal_alarm_values={
        10: 2, 30: 3, 60: 4, -1: 0, 0: 1 }
    
    def __init__(self, calendar_entry, new_date=None):
        self._start=self._end=self._alarm=self._desc=None
        self._extract_cal_info(calendar_entry, new_date)

    def _extract_cal_info(self, cal_entry, new_date):
        s=cal_entry.start
        if new_date is not None:
            s=new_date[:3]+s[3:]
        self._start=s
        self._end=cal_entry.end
        self._desc=cal_entry.description
    # approximate the alarm value
        self._alarm=0
        alarm=cal_entry.alarm
        _keys=self._cal_alarm_values.keys()
        _keys.sort()
        _keys.reverse()
        for k in _keys:
            if alarm>=k:
                self._alarm=self._cal_alarm_values[k]
                break

    def __lt__(self, rhs):
        return self.start<rhs.start
    def __le__(self, rhs):
        return self.start<=rhs.start
    def __eq__(self, rhs):
        return self.start==rhs.start
    def __ne__(self, rhs):
        return self.start!=rhs.start
    def __gt__(self, rhs):
        return self.start>rhs.start
    def __ge__(self, rhs):
        return self.start>=rhs.start
    
    def _get_start(self):
        return self._start
    start=property(fget=_get_start)

    def _get_end(self):
        return self._end
    end=property(fget=_get_end)

    def _get_desc(self):
        return self._desc
    description=property(fget=_get_desc)

    def _get_alarm(self):
        return self._alarm
    alarm=property(fget=_get_alarm)
