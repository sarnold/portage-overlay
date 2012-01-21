### BITPIM
###
### Copyright (C) 2008 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx9100.py 4681 2008-08-14 22:41:27Z djpham $

"""
Communicate with the LG VX9100 (enV2) cell phone.  This is based on the enV model
"""

# BitPim modules
import common
import com_brew
import com_lg
import com_lgvx8550
import p_lgvx9100
import prototypes
import helpids
import sms

DEBUG1=False
DEBUG2=False
#-------------------------------------------------------------------------------
parentphone=com_lgvx8550.Phone
class Phone(parentphone):
    "Talk to the LG VX9100 cell phone"

    desc="LG-VX9100"
    helpid=helpids.ID_PHONE_LGVX9100
    protocolclass=p_lgvx9100
    serialsname='lgvx9100'
    my_model='VX9100'

    # rintones and wallpaper info, copy from VX9900, may need to change to match
    # what the phone actually has
    external_storage_root='mmc1/'
    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'Door Bell', 'VZW Default Tone') + \
                      tuple(['Ringtone '+`n` for n in range(1,17)]) + \
                      ('No Ring',)

    ringtonelocations= (
        #  type          index file            default dir        external dir    max  type Index
        ( 'ringers',    'dload/myringtone.dat','brew/mod/10889/ringtones','mmc1/ringers', 100, protocolclass.INDEX_RT_TYPE, 100),
        ( 'sounds',     'dload/mysound.dat',   'brew/mod/18067',   '',             100, protocolclass.INDEX_SOUND_TYPE, None),
        ( 'sounds(sd)', 'dload/sd_sound.dat',  'mmc1/my_sounds',  '',             100, protocolclass.INDEX_SDSOUND_TYPE, None),
##        ( 'music',      'dload/efs_music.dat', 'my_music',        '',             100, 0x104, None),
##        ( 'music(sd)',  'dload/sd_music.dat',  'mmc1/my_music',   '',             100, 0x14, None),
        )

    wallpaperlocations= (
        #  type          index file            default dir     external dir  max  type Index
        ( 'images',     'dload/image.dat',    'brew/mod/10888', '',          100, protocolclass.INDEX_IMAGE_TYPE, 100),
        ( 'images(sd)', 'dload/sd_image.dat', 'mmc1/my_pix',   '',           100, protocolclass.INDEX_SDIMAGE_TYPE, None),
        ( 'video',      'dload/video.dat',    'brew/mod/10890', '',          100, protocolclass.INDEX_VIDEO_TYPE, None),
        ( 'video(sd)',  'dload/sd_video.dat', 'mmc1/my_flix',  '',           100, protocolclass.INDEX_SDVIDEO_TYPE, None),
        )

    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)

    def setDMversion(self):
        self._DMv6=True
        self._DMv5=False

    # Fundamentals:
    #  - get_esn             - same as LG VX-8300
    #  - getgroups           - same as LG VX-8100
    #  - getwallpaperindices - LGUncountedIndexedMedia
    #  - getrintoneindices   - LGUncountedIndexedMedia
    #  - DM Version          - T99VZV01: N/A, T99VZV02: 5

    # phonebook stuff-----------------------------------------------------------
    # This is essentially the same with the VX-8550 with a few tweaks.
    # These tweaks are probably applicable to the VX-8550 as well, but since
    # I can't test them on an actual VX-8550, I'll leave it alone.

    # groups
    def getgroups(self, results):
        "Read groups"
        # Reads groups that use explicit IDs
        self.log("Reading group information")
        g=self.readobject(self.protocolclass.pb_group_filename,
                          self.protocolclass.pbgroups,
                          'Reading groups data')
        groups={}
        for _group in g.groups:
            if _group.name:
                groups[_group.groupid]= { 'name': _group.name,
                                     'user_added': _group.user_added }
        results['groups'] = groups
        return groups

    def savegroups(self, data):
        groups=data.get('groups', {})
        keys=groups.keys()
        keys.sort()
        keys.reverse()
        g=self.protocolclass.pbgroups()
        # write the No Group entry first
        g.groups.append(self.protocolclass.pbgroup(name='No Group'))
        # now write the rest in reverse ID order
        for k in keys:
            if not k:
                # already wrote this one out
                continue
            g.groups.append(self.protocolclass.pbgroup(name=groups[k]['name'],
                                                       groupid=k,
                                                       user_added=groups[k].get('user_added', 1)))
        self.writeobject(self.protocolclass.pb_group_filename, g,
                         logtitle='Writing phonebook groups',
                         uselocalfs=DEBUG1)

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

    def _build_ice_dict(self):
        # Return an ICE dict for building phone entries
        _res={}
        _ice=self.readobject(self.protocolclass.pb_ice_file_name,
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
                res['wallpapers']=[ {'wallpaper': paper, 'use': 'call'} ]                
            except:
                print "can't find wallpaper for index",entry.wallpaper
            
        # ringtones
        if entry.ringtone != self.protocolclass.NORINGTONE:
            try:
                if entry.ringtone == 0x64:
                    tone = rt_name
                else:
                    tone=fundamentals['ringtone-index'][entry.ringtone]['name']
                if tone:
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
            if entry.numberindices[i].numberindex>=\
               self.protocolclass.NUMPHONENUMBERENTRIES:
                # invalid number
                continue
            _pnentry=numbers.items[entry.numberindices[i].numberindex]
            num=_pnentry.phone_number
            num_type=_pnentry.type
            if len(num):
                t=self.protocolclass.numbertypetab[num_type]
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
            self.log('Entry %d is ICE %d'%(entry.entry_number0,
                                           ices[entry.entry_number0]))
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

        # the pbentry.dat will will be overwritten so there is no need to delete entries
        pbook = data.get('phonebook', {})
        keys = pbook.keys ()
        keys.sort ()

        _rt_index=data.get('ringtone-index', {})
        _wp_index=data.get('wallpaper-index', {})

        entry_num0 = 0
        entry_num1=self._get_next_pb_id()
        pb_entries = self.protocolclass.pbfile()
        pn_entries=self.protocolclass.pnfile()
        ice_entries = self.protocolclass.iceentryfile()
        for i in range(self.protocolclass.NUMEMERGENCYCONTACTS):
            ice_entries.items.append (self.protocolclass.iceentry())
        speeddials={}
        for i in keys:
            pb_entries.items.append(self.make_entry (pn_entries, speeddials, ice_entries,
                                                     entry_num0, entry_num1,
                                                     pbook[i], data,
                                                     ring_pathf,_rt_index,
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
        # write wallpaer index
        self.log('Writing pciture ID')
        self.writeobject(self.protocolclass.WPPathIndexFile,
                         picid_pathf, logtitle='Writing wallpaper paths',
                         uselocalfs=DEBUG1)
        # write ICE index
        self.log('Writing ICE entries')
        self.writeobject(self.protocolclass.pb_ice_file_name,
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
        new_entry.type = number_type
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
                    entry_num0, entry_num1,
                    pb_entry, data, ring_pathf,
                    rt_index, picid_pathf, wp_index):
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


    # Calendar stuff------------------------------------------------------------
    def _scheduleextras(self, data, fwversion):
        data.serial_number = '000000d1-00000000-00000000-' + fwversion
        data.unknown3 = 0x01fc


    # ringtones and wallpapers stuff--------------------------------------------
    def savewallpapers(self, results, merge):
        results['rebootphone']=True
        return self.savemedia('wallpapers', 'wallpaper-index',
                              self.wallpaperlocations, results, merge,
                              self.getwallpaperindices, True)
            
    def saveringtones(self, results, merge):
        # Let the phone rebuild the index file, just need to reboot
        results['rebootphone']=True
        return self.savemedia('ringtone', 'ringtone-index',
                              self.ringtonelocations, results, merge,
                              self.getringtoneindices, True)

    # SMS Stuff-----------------------------------------------------------------
    # Again, this is very similar to the 8800, just make it work with the 9100
    def getindex(self, filename):
        try:
            return self.readobject(filename,
                                   self.protocolclass.indexfile,
                                   logtitle='Reading index file',
                                   uselocalfs=DEBUG2).items
        except:
            return []

    def _readsms(self):
        res={}
        # The Voyager and Venus use index files to keep track of SMS messages
        for item in self.getindex(self.protocolclass.drafts_index):
                sf=self.readobject(item.filename,
                                   self.protocolclass.sms_saved,
                                   logtitle='SMS draft item',
                                   uselocalfs=DEBUG2)
                # The 9100 only has draft messages (saved outgoing messaged)
                entry=self._getoutboxmessage(sf.outbox)
                entry.folder=entry.Folder_Saved
                res[entry.id]=entry
        for item in self.getindex(self.protocolclass.inbox_index):
                sf=self.readobject(item.filename,
                                   self.protocolclass.sms_in,
                                   logtitle='SMS inbox item',
                                   uselocalfs=DEBUG2)
                entry=self._getinboxmessage(sf)
                res[entry.id]=entry
        for item in self.getindex(self.protocolclass.outbox_index):
                sf=self.readobject(item.filename,
                                   self.protocolclass.sms_out,
                                   logtitle='SMS outbox item',
                                   uselocalfs=DEBUG2)
                entry=self._getoutboxmessage(sf)
                res[entry.id]=entry
        return res 

    def _getinboxmessage(self, sf):
        entry=sms.SMSEntry()
        entry.folder=entry.Folder_Inbox
        entry.datetime="%d%02d%02dT%02d%02d%02d" % (sf.GPStime)
        entry._from=sf.sender if sf.sender else sf.sender_name
        entry.subject=sf.subject
        entry.locked=sf.locked
        if sf.priority==0:
            entry.priority=sms.SMSEntry.Priority_Normal
        else:
            entry.priority=sms.SMSEntry.Priority_High
        entry.read=sf.read
        txt=""
        _decode_func=self._get_text_from_sms_msg_with_header if \
                      sf.msgs[1].msg_length else \
                      self._get_text_from_sms_msg_without_header
        for _entry in sf.msgs:
            if _entry.msg_length:
                txt+=_decode_func(_entry.msg_data.msg, _entry.msg_length)
        entry.text=unicode(txt, errors='ignore')
        entry.callback=sf.callback
        return entry


#-------------------------------------------------------------------------------
parentprofile=com_lgvx8550.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX9100'

    WALLPAPER_WIDTH=320
    WALLPAPER_HEIGHT=240
    # outside LCD: 160x64

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))
    def GetImageOrigins(self):
        return self.imageorigins


##    ringtoneorigins=('ringers', 'sounds', 'sounds(sd)',' music', 'music(sd)')
##    excluded_ringtone_origins=('sounds', 'sounds(sd)', 'music', 'music(sd)')
    ringtoneorigins=('ringers', 'sounds', 'sounds(sd)')
    excluded_ringtone_origins=('sounds', 'sounds(sd)')

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 320, 'height': 215, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 160, 'height': 64, 'format': "JPEG"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets

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
##        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'write', 'MERGE'),       # merge and overwrite ringtone
##        ('ringtone', 'write', 'OVERWRITE'),
####        ('sms', 'write', 'OVERWRITE'),        # all SMS list writing
        ('memo', 'write', 'OVERWRITE'),       # all memo list writing
####        ('playlist', 'read', 'OVERWRITE'),
####        ('playlist', 'write', 'OVERWRITE'),
        )

    def normalisegroups(self, helper, data):
        "Assigns groups based on category data"

        pad=[]
        keys=data['groups'].keys()
        keys.sort()
        for k in keys:
                if k: # ignore key 0 which is 'No Group'
                    name=data['groups'][k]['name']
                    pad.append(name)

        groups=helper.getmostpopularcategories(self.protocolclass.MAX_PHONEBOOK_GROUPS, data['phonebook'], ["No Group"], 32, pad)

        # alpha sort
        groups.sort()

        # newgroups
        newgroups={}

        # put in No group
        newgroups[0]={'name': 'No Group', 'user_added': 0}

        # populate
        for name in groups:
            # existing entries remain unchanged
            if name=="No Group": continue
            key,value=self._getgroup(name, data['groups'])
            if key is not None and key!=0:
                newgroups[key]=value
        # new entries get whatever numbers are free
        for name in groups:
            key,value=self._getgroup(name, newgroups)
            if key is None:
                for key in range(1,100000):
                    if key not in newgroups:
                        newgroups[key]={'name': name, 'user_added': 1}
                        break
                       
        # yay, done
        if data['groups']!=newgroups:
            data['groups']=newgroups
            data['rebootphone']=True

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
                    if len(number)>24: # get this number from somewhere sensible
                        # ::TODO:: number is too long and we have to either truncate it or ignore it?
                        number=number[:24] # truncate for moment
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
    # applicable fields for this model
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
            'secret': 0,
            'ICE': 1,
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
