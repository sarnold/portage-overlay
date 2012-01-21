#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2007-2008 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
### $Id: com_lgvx8550.py 4712 2008-10-07 14:00:07Z hjelmn $


"""
Communicate with the LG VX8550 cell phone.
"""

# BitPim modules
import common
import com_brew
import bpcalendar
import prototypes
import com_lgvx8700
import com_lgvx8500
import p_lgvx8550
import p_brew
import helpids
import copy
import time
import os.path

DEBUG1=False
#-------------------------------------------------------------------------------
parentphone=com_lgvx8700.Phone
class Phone(parentphone):
    desc="LG-VX8550"
    helpid=None
    protocolclass=p_lgvx8550
    serialsname='lgvx8550'

    my_model='VX8550'

    calendarringerlocation='sch/toolsRinger.dat'

    def setDMversion(self):
        _fw_version=self.get_firmware_version()[-1]
        if self.my_model=='VX8550' and _fw_version>'3':
            # VX855V04
            self._DMv5 = False
            self._DMv6 = True
        else:
            self._DMv5 = True
            self._DMv6 = False


    # Fundamentals:
    #  - get_esn             - same as LG VX-8300
    #  - getgroups           - same as LG VX-8700
    #  - getwallpaperindices - LGUncountedIndexedMedia
    #  - getringtoneindices  - LGUncountedIndexedMedia
    #  - DM Version          - 5 (VX855V03 or older), 6 (VX855V04)

    def _get_speeddials(self):
        """Return the speed dials dict"""
        speeds={}
        try:
            if self.protocolclass.NUMSPEEDDIALS:
                self.log("Reading speed dials")
                sd=self.readobject(self.protocolclass.speed_file_name,
                                   self.protocolclass.speeddials, 'Reading speed dials')
                for _idx,_entry in enumerate(sd.speeddials):
                    if _entry.valid():
                        speeds.setdefault(_entry.entry, {}).update({ _entry.number: _idx })
        except com_brew.BrewNoSuchFileException:
            pass
        return speeds

    def _build_media_dict(self, fundamentals, media_data, index_name):
        """Build & return a dict with keys being the media filenames and
        values being the name of the index item (index['name'])
        """
        _res={}
        _media_index=fundamentals.get(index_name, {})
        for _item in media_data.items:
            _pathname=_item.pathname
            if _pathname and not _res.has_key(_pathname):
                # not already in dict, look up the name if any
                _res[_pathname]=None
                for _entry in _media_index.values():
                    if _entry.get('filename', None)==_pathname:
                        _res[_pathname]=_entry['name']
                        break
        return _res

    def _get_path_index(self, index_file):
        buf = prototypes.buffer(self.getfilecontents(index_file))
        _path_file=self.protocolclass.PathIndexFile()
        _path_file.readfrombuffer(buf, logtitle="Read path index: " + index_file)
        return _path_file

    def _build_ice_dict(self):
        # Return an ICE dict for building phone entries
        _res={}
        _ice=self.readobject(self.protocolclass.ice_file_name,
                             self.protocolclass.iceentryfile,
                             logtitle='Reading ICE entries')
        for _item in _ice.items:
            if _item.valid():
                _res[_item.pb_index]=_item.entry_number
        return _res

    def getphonebook (self, result):
        """Reads the phonebook data.  The L{getfundamentals} information will
        already be in result."""
        # Read speed dials first -- same file format as the VX-8100
        _speeds=self._get_speeddials()

        # Read the emergency contacts list
        self.log("Reading ICE entries")
        _ices=self._build_ice_dict()

        self.log("Reading phonebook entries")
        pb_entries=self.readobject(self.protocolclass.pb_file_name,
                                   self.protocolclass.pbfile,
                                   logtitle='Reading phonebook entries')

        self.log("Reading phone numbers")
        pb_numbers=self.readobject(self.protocolclass.pn_file_name,
                                   self.protocolclass.pnfile,
                                   logtitle='Reading phonebook numbers')

        self.log("Reading Ringtone IDs")
        ring_pathf=self._get_path_index(self.protocolclass.RTPathIndexFile)
        _rt_ids=self._build_media_dict(result, ring_pathf, 'ringtone-index')

        self.log("Reading Picture IDs")
        picid_pathf=self._get_path_index(self.protocolclass.WPPathIndexFile)
        _wp_ids=self._build_media_dict(result, picid_pathf, 'wallpaper-index')

        pbook={}
        for _cnt in range(self.protocolclass.NUMPHONEBOOKENTRIES):
            pb_entry=pb_entries.items[_cnt]
            if not pb_entry.valid():
                continue
            try:
                self.log("Parse entry "+`_cnt`+" - " + pb_entry.name)
                pbook[_cnt]=self.extractphonebookentry(pb_entry, pb_numbers,
                                                       _speeds, _ices, result,
                                                       _rt_ids.get(ring_pathf.items[_cnt].pathname, None),
                                                       _wp_ids.get(picid_pathf.items[_cnt].pathname, None))

                self.progress(_cnt, self.protocolclass.NUMPHONEBOOKENTRIES, pb_entry.name)
            except common.PhoneBookBusyException:
                raise
            except Exception, e:
                # Something's wrong with this entry, log it and skip
                self.log('Failed to parse entry %d'%_cnt)
                self.log('Exception %s raised'%`e`)
                if __debug__:
                    raise
            
        self.progress(self.protocolclass.NUMPHONEBOOKENTRIES,
                      self.protocolclass.NUMPHONEBOOKENTRIES,
                      "Phone book read completed")

        result['phonebook']=pbook
        cats=[]
        for i in result['groups']:
            if result['groups'][i]['name']!='No Group':
                cats.append(result['groups'][i]['name'])
        result['categories']=cats
        return pbook

    def extractphonebookentry(self, entry, numbers, speeds, ices, fundamentals,
                              rt_name, wp_name):
        """Return a phonebook entry in BitPim format.  This is called from getphonebook."""
        res={}
        # serials
        res['serials']=[ {'sourcetype': self.serialsname,
                          'sourceuniqueid': fundamentals['uniqueserial'],
                          'serial1': entry.entry_number1,
                          'serial2': entry.entry_number1 } ] 

        # only one name
        res['names']=[ {'full': entry.name} ]

        # only one category
        cat=fundamentals['groups'].get(entry.group, {'name': "No Group"})['name']
        if cat!="No Group":
            res['categories']=[ {'category': cat} ]

        # emails
        res['emails']=[]
        for i in entry.emails:
            if len(i.email):
                res['emails'].append( {'email': i.email} )
        if not len(res['emails']): del res['emails'] # it was empty

        # wallpapers
        if entry.wallpaper!=self.protocolclass.NOWALLPAPER:
            try:
                if entry.wallpaper == 0x64:
                    paper = wp_name
                else:
                    paper = fundamentals['wallpaper-index'][entry.wallpaper]['name']

                if paper is None:
                    raise

                res['wallpapers']=[ {'wallpaper': paper, 'use': 'call'} ]                
            except:
                print "can't find wallpaper for index",entry.wallpaper
            
        # ringtones
        if entry.ringtone != self.protocolclass.NORINGTONE:
            try:
                if entry.ringtone == 0x64:
                    tone = rt_name
                else:
                    tone = fundamentals['ringtone-index'][entry.ringtone]['name']

                if tone is None:
                    raise

                res['ringtones']=[ {'ringtone': tone, 'use': 'call'} ]
            except:
                print "can't find ringtone for index",entry.ringtone
        # assume we are like the VX-8100 in this regard -- looks correct
        res=self._assignpbtypeandspeeddialsbytype(entry, numbers, speeds, res)

        # assign the ICE entry to the associated contact to keep them in sync
        res=self._assigniceentry(entry, numbers, ices, res)
  
        return res

    def _assignpbtypeandspeeddialsbytype(self, entry, numbers, speeds, res):
        # for some phones (e.g. vx8100) the speeddial numberindex is really the numbertype (now why would LG want to change this!)
        res['numbers']=[]

        for i in range(self.protocolclass.NUMPHONENUMBERS):
            if entry.numberindices[i].numberindex >= self.protocolclass.NUMPHONENUMBERENTRIES:
                # invalid number
                continue
            _pnentry=numbers.items[entry.numberindices[i].numberindex]
            num=_pnentry.phone_number

            if len(num):
                if _pnentry.malformed():
                    print "malformed phone number entry encountered"

                # use the type from the phonebook entry
                num_type = entry.numbertypes[i].numbertype

                t = self.protocolclass.numbertypetab[num_type]
                if t[-1]=='2':
                    t=t[:-1]
                res['numbers'].append({'number': num, 'type': t})
                # if this is a speeddial number set it
                if speeds.has_key(entry.entry_number0) and \
                   speeds[entry.entry_number0].has_key(num_type):
                    res['numbers'][i]['speeddial']=speeds[entry.entry_number0][num_type]
        return res

    def _assigniceentry(self, entry, numbers, ices, res):
        if ices.has_key(entry.entry_number0):
            # this contact entry is an ICE entry
            res['ice']=[ { 'iceindex': ices[entry.entry_number0] } ]
        return res

    def _get_next_pb_id(self):
        """Return the next available pbentry ID"""
        return self.readobject(self.protocolclass.pb_recordid_filename,
                               self.protocolclass.RecordIdEntry,
                               logtitle='Reading record_id').idnum

    def _save_next_pb_id(self, idnum):
        """Save the next pbentry ID"""
        self.writeobject(self.protocolclass.pb_recordid_filename,
                         self.protocolclass.RecordIdEntry(idnum=idnum),
                         logtitle='Writing record_id',
                         uselocalfs=DEBUG1)

    def savephonebook (self, data):
        "Saves out the phonebook"
        self.savegroups (data)

        ring_pathf=self.protocolclass.PathIndexFile()
        picid_pathf=self.protocolclass.PathIndexFile()

        # the pbentry.dat will be overwritten so there is no need to delete entries
        pbook = data.get('phonebook', {})
        keys = pbook.keys ()
        keys.sort ()

        _rt_index=data.get('ringtone-index', {})
        _wp_index=data.get('wallpaper-index', {})

        entry_num0 = 0
        entry_num1 = self._get_next_pb_id()
        pb_entries = self.protocolclass.pbfile(model_name=self.my_model)
        pn_entries = self.protocolclass.pnfile()

        ice_entries = self.protocolclass.iceentryfile()
        for i in range(self.protocolclass.NUMEMERGENCYCONTACTS):
            ice_entries.items.append (self.protocolclass.iceentry())

        speeddials={}

        for i in keys:
            pb_entries.items.append(self.make_entry (pn_entries, speeddials, ice_entries,
                                                     entry_num0, entry_num1, pbook[i],
                                                     data, ring_pathf,_rt_index,
                                                     picid_pathf, _wp_index))
            entry_num0 += 1
            if entry_num0 >= self.protocolclass.NUMPHONEBOOKENTRIES:
                self.log ("Maximum number of phonebook entries reached")
                break
            if entry_num1==0xffffffff:
                entry_num1=0
            else:
                entry_num1+=1

        # write phonebook entries
        self.log ("Writing phonebook entries")
        self.writeobject(self.protocolclass.pb_file_name,
                         pb_entries,
                         logtitle='Writing phonebook entries',
                         uselocalfs=DEBUG1)
        # write phone numbers
        self.log ("Writing phone numbers")
        self.writeobject(self.protocolclass.pn_file_name,
                         pn_entries, logtitle='Writing phonebook numbers',
                         uselocalfs=DEBUG1)
        # write ringtone index
        self.log('Writing ringtone ID')
        self.writeobject(self.protocolclass.RTPathIndexFile,
                         ring_pathf, logtitle='Writing ringtone paths',
                         uselocalfs=DEBUG1)
        # write wallpaper index
        self.log('Writing picture ID')
        self.writeobject(self.protocolclass.WPPathIndexFile,
                         picid_pathf, logtitle='Writing wallpaper paths',
                         uselocalfs=DEBUG1)

        # write ICE index
        self.log('Writing ICE entries')
        self.writeobject(self.protocolclass.ice_file_name,
                         ice_entries, logtitle='Writing ICE entries',
                         uselocalfs=DEBUG1)

        # update speed dials
        req=self.protocolclass.speeddials()
        # slot 0 is always unused
        req.speeddials.append(self.protocolclass.speeddial())
        # if empty, slot 1 is for voicemail
        if speeddials.has_key(1):
            req.speeddials.append(self.protocolclass.speeddial(entry=speeddials[1]['entry'],
                                                               number=speeddials[1]['type']))
        else:
            req.speeddials.append(self.protocolclass.speeddial(entry=1000,
                                                               number=6))
        for i in range(2, self.protocolclass.NUMSPEEDDIALS):
            sd=self.protocolclass.speeddial()
            if speeddials.has_key(i):
                sd.entry=speeddials[i]['entry']
                sd.number=speeddials[i]['type']
            req.speeddials.append(sd)

        self.log('Writing speed dials')
        self.writeobject(self.protocolclass.speed_file_name,
                         req, logtitle='Writing speed dials data',
                         uselocalfs=DEBUG1)

        # update the next pbentries ID
        self._save_next_pb_id(entry_num1)
        data["rebootphone"]=True

        return data

    def make_pn_entry (self, phone_number, number_type, pn_id, pbpn_id, pe_id):
        """ Create a non-blank pnfileentry frome a phone number string """
        if len(phone_number) == 0:
            raise
        
        new_entry = self.protocolclass.pnfileentry(entry_tag=self.protocolclass.PB_NUMBER_SOR)
        new_entry.pn_id = pn_id
        new_entry.pe_id = pe_id
        new_entry.phone_number = phone_number
        new_entry.ntype = number_type
        new_entry.pn_order = pbpn_id

        return new_entry

    def make_ice_entry (self, ice_id, pb_id):
        """ Create a iceentry from a pb_id and ice_id """
        new_entry = self.protocolclass.iceentry()
        
        new_entry.entry_assigned = 1
        new_entry.entry_number = ice_id
        new_entry.pb_index = pb_id

        return new_entry

    def make_entry (self, pn_entries, speeddials, ice_entries,
                    entry_num0, entry_num1, pb_entry, data,
                    ring_pathf, rt_index, picid_pathf, wp_index):
        """ Create a pbfileentry from a bitpim phonebook entry """
        new_entry = self.protocolclass.pbfileentry(entry_tag=self.protocolclass.PB_ENTRY_SOR)
        # entry IDs
        new_entry.entry_number0 = entry_num0
        new_entry.entry_number1 = entry_num1

        for key in pb_entry:
            if key in ('emails', 'numbertypes'):
                l = getattr (new_entry, key)
                for item in pb_entry[key]:
                    l.append(item)
            elif key == 'numbers':
                l = getattr (new_entry, 'numberindices')
                for i in range(0, self.protocolclass.NUMPHONENUMBERS):
                    new_pn_id = len (pn_entries.items)
                    if new_pn_id == self.protocolclass.NUMPHONENUMBERENTRIES:
                        # this state should not be possible. should this raise an exception?
                        self.log ("Maximum number of phone numbers reached")
                        break

                    try:
                        pn_entries.items.append(self.make_pn_entry (pb_entry[key][i],pb_entry['numbertypes'][i], new_pn_id, i, entry_num0))
                        l.append (new_pn_id)
                    except:
                        l.append (0xffff)
            elif key == 'speeddials':
                for _sd,_num_type in zip(pb_entry['speeddials'], pb_entry['numbertypes']):
                    if _sd is not None:
                        speeddials[_sd]={ 'entry': entry_num0,
                                          'type': _num_type }
            elif key == 'ice':
                # In Case of Emergency
                _ice = pb_entry['ice']
                if _ice is not None and len(_ice) > 0:
                    _ice_entry = _ice[0]['iceindex']
                    ice_entries.items[_ice_entry] = self.make_ice_entry (_ice_entry, entry_num0)
            elif key == 'ringtone':
                new_entry.ringtone = self._findmediainindex(data['ringtone-index'], pb_entry['ringtone'], pb_entry['name'], 'ringtone')
                try:
                    _filename = rt_index[new_entry.ringtone]['filename']
                    ring_pathf.items.append(self.protocolclass.PathIndexEntry(pathname=_filename))
                    new_entry.ringtone = 0x64
                except:
                    ring_pathf.items.append(self.protocolclass.PathIndexEntry())
            elif key == 'wallpaper':
                new_entry.wallpaper = self._findmediainindex(data['wallpaper-index'], pb_entry['wallpaper'], pb_entry['name'], 'wallpaper')
                try:
                    _filename = wp_index[new_entry.wallpaper]['filename']
                    picid_pathf.items.append(self.protocolclass.PathIndexEntry(pathname=_filename))
                    new_entry.wallpaper = 0x64
                except:
                    picid_pathf.items.append(self.protocolclass.PathIndexEntry())
            elif key in new_entry.getfields():
                setattr (new_entry, key, pb_entry[key])

        return new_entry

    def getcalendar(self,result):
        res={}
        # Read exceptions file first
        exceptions = self.getexceptions()

        try:
            buf = prototypes.buffer(self.getfilecontents(self.calendarringerlocation))
            ringersf = self.protocolclass.scheduleringerfile()
            ringersf.readfrombuffer (buf)
        except:
            self.log ("unable to read schedule ringer path file")
        
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
                    self.getcalendarcommon(entry, event)
                except ValueError:
                    continue
                try:
                    if (event.ringtone >= 100):   # MIC Ringer is downloaded to phone or microSD
                        entry.ringtone = common.basename(ringersf.ringerpaths[event.ringtone-100].path)
                    else:                         # MIC Ringer is built-in
                        entry.ringtone=self.builtinringtones[event.ringtone]
                except:
                    self.log ("Setting default ringer for event\n")
                    # hack, not having a phone makes it hard to figure out the best approach
                    if entry.alarm==None:
                        entry.ringtone='No Ring'
                    else:
                        entry.ringtone='Loud Beeps'
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

    def _scheduleextras(self, data, fwversion):
        data.serial_number = '000000ca-00000000-00000000-' + fwversion
        data.unknown3 = 0x01fb
        
    def savecalendar(self, dict, merge):
        # ::TODO::
        # what will be written to the files
        eventsf     = self.protocolclass.schedulefile()
        exceptionsf = self.protocolclass.scheduleexceptionfile()
        ringersf    = self.protocolclass.scheduleringerfile()
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
        ringersf.numringers = 0
        pos = 0
        # get phone firmware version for serial number
        try:
            req = p_brew.firmwarerequest()
            res = self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
            _fwversion = res.firmware
        except:
            _fwversion = '00000000'

        # play with each entry
        for (_,k) in keys:
            # entry is what we will return to user
            entry=cal[k]
            data=self.protocolclass.scheduleevent()
            # using the packetsize() method here will fill the LIST with default entries
            data.pos = pos * data.packet_size + 2
            self._schedulecommon(entry, data)
            alarm_set=self.setalarm(entry, data)
            if alarm_set:
                if entry.ringtone=="No Ring" and not entry.vibrate:
                    alarm_name="Low Beep Once"
                else:
                    alarm_name=entry.ringtone
            else: # set alarm to "No Ring" gets rid of alarm icon on phone
                alarm_name="No Ring"
            for i in dict['ringtone-index']:
                self.log ('ringtone ' + str(i) + ': ' + dict['ringtone-index'][i]['name'] + ' alarm-name = ' + alarm_name)  
                if dict['ringtone-index'][i]['name']==alarm_name:
                    if dict['ringtone-index'][i].get('filename', None):
                        data.ringtone = 100 + ringersf.numringers
                        ringersf.ringerpaths.append(dict['ringtone-index'][i]['filename'])
                        ringersf.numringers = ringersf.numringers + 1
                    else:
                        # builtin ringer
                        data.ringtone=i      # Set to proper index
                    break
            # check for exceptions and add them to the exceptions list
            self._scheduleexceptions(entry, data, exceptionsf)
            self._scheduleextras(data, _fwversion)
            # put entry in nice shiny new dict we are building
            entry=copy.copy(entry)
            newcal[data.pos]=entry
            eventsf.events.append(data)            
            pos = pos + 1

        buf=prototypes.buffer()
        eventsf.writetobuffer(buf, logtitle="New Calendar")
        self.writefile(self.calendarlocation, buf.getvalue())
        self.log("Your phone has to be rebooted due to the calendar changing")
        dict["rebootphone"]=True

        buf=prototypes.buffer()
        exceptionsf.writetobuffer(buf, logtitle="Writing calendar exceptions")
        self.writefile(self.calendarexceptionlocation, buf.getvalue())

        buf = prototypes.buffer()
        ringersf.writetobuffer(buf, logtitle="Writing calendar ringers")
        self.writefile(self.calendarringerlocation, buf.getvalue())

        # fix passed in dict
        dict['calendar']=newcal

        return dict

#-------------------------------------------------------------------------------
parentprofile=com_lgvx8500.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX8550'
    # inside screen resoluation
    WALLPAPER_WIDTH=176
    WALLPAPER_HEIGHT=220

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 238, 'height': 246, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 240, 'height': 274, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 120, 'height': 100, 'format': "JPEG"}))

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
        ('t9_udb', 'write', 'OVERWRITE'),
        )
    if __debug__:
        _supportedsyncs+=(
        ('t9_udb', 'read', 'OVERWRITE'),
        )


    def convertphonebooktophone(self, helper, data):
        """Converts the data to what will be used by the phone

        @param data: contains the dict returned by getfundamentals
                     as well as where the results go"""
        results={}

        self.normalisegroups(helper, data)

        for pbentry in data['phonebook']:
            if len(results)==self.protocolclass.NUMPHONEBOOKENTRIES:
                break
            e={} # entry out
            entry=data['phonebook'][pbentry] # entry in
            try:
                # serials
                serial1=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial1', 0)
                serial2=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial2', serial1)

                e['serial1']=serial1
                e['serial2']=serial2
                for ss in entry["serials"]:
                    if ss["sourcetype"]=="bitpim":
                        e['bitpimserial']=ss
                assert e['bitpimserial']

                # name
                e['name']=helper.getfullname(entry.get('names', []),1,1,32)[0]

                # ice
                e['ice']=entry.get('ice', None)

                # categories/groups
                cat=helper.makeone(helper.getcategory(entry.get('categories', []),0,1,32), None)
                if cat is None:
                    e['group']=0
                else:
                    key,value=self._getgroup(cat, data['groups'])
                    if key is not None:
                        e['group']=key
                    else:
                        # sorry no space for this category
                        e['group']=0

                # email addresses
                emails=helper.getemails(entry.get('emails', []) ,0,self.protocolclass.NUMEMAILS,48)
                e['emails']=helper.filllist(emails, self.protocolclass.NUMEMAILS, "")

                # phone numbers
                # there must be at least one email address or phonenumber
                minnumbers=1
                if len(emails): minnumbers=0
                numbers=helper.getnumbers(entry.get('numbers', []),minnumbers,self.protocolclass.NUMPHONENUMBERS)
                e['numbertypes']=[]
                e['numbers']=[]
                e['speeddials']=[]
                for numindex in range(len(numbers)):
                    num=numbers[numindex]
                    # deal with type
                    b4=len(e['numbertypes'])
                    type=num['type']
                    for i,t in enumerate(self.protocolclass.numbertypetab):
                        if type==t:
                            # some voodoo to ensure the second home becomes home2
                            if i in e['numbertypes'] and t[-1]!='2':
                                type+='2'
                                continue
                            e['numbertypes'].append(i)
                            break
                        if t=='none': # conveniently last entry
                            e['numbertypes'].append(i)
                            break
                    if len(e['numbertypes'])==b4:
                        # we couldn't find a type for the number
                        helper.add_error_message('Number %s (%s/%s) not supported and ignored.'%
                                                 (num['number'], e['name'], num['type']))
                        continue 
                    # deal with number
                    number=self.phonize(num['number'])
                    if len(number)==0:
                        # no actual digits in the number
                        continue
                    if len(number) > 48: # get this number from somewhere sensible
                        # ::TODO:: number is too long and we have to either truncate it or ignore it?
                        number=number[:48] # truncate for moment
                    e['numbers'].append(number)
                    # deal with speed dial
                    sd=num.get("speeddial", None)
                    if sd is not None and \
                       sd>=self.protocolclass.FIRSTSPEEDDIAL and \
                       sd<=self.protocolclass.LASTSPEEDDIAL:
                        e['speeddials'].append(sd)
                    else:
                        e['speeddials'].append(None)

                if len(e['numbers'])<minnumbers:
                    # we couldn't find any numbers
                    # for this entry, so skip it, entries with no numbers cause error
                    helper.add_error_message("Name: %s. No suitable numbers or emails found" % e['name'])
                    continue 
                e['numbertypes']=helper.filllist(e['numbertypes'], self.protocolclass.NUMPHONENUMBERS, 0)
                e['numbers']=helper.filllist(e['numbers'], self.protocolclass.NUMPHONENUMBERS, "")
                e['speeddials']=helper.filllist(e['speeddials'], self.protocolclass.NUMPHONENUMBERS, None)

                # ringtones, wallpaper
                e['ringtone']=helper.getringtone(entry.get('ringtones', []), 'call', None)
                e['wallpaper']=helper.getwallpaper(entry.get('wallpapers', []), 'call', None)

                results[pbentry]=e
                
            except helper.ConversionFailed:
                continue

        data['phonebook']=results
        return data
