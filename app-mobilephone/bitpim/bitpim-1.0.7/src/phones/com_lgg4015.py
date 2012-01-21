### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgg4015.py 4365 2007-08-17 21:11:59Z djpham $

"""Communicate with the LG G4015 cell phone
"""

# standard modules
import base64
import sha
import time

# BitPim modules
import bpcalendar
import common
import commport
import com_etsi
import guihelper
import helpids
import memo
import nameparser
import p_lgg4015
import prototypes
import sms

class Phone(com_etsi.Phone):
    """ Talk to the LG G4015 Phone"""

    desc='LG-G4015'
    helpid=helpids.ID_PHONE_LGG4015
    protocolclass=p_lgg4015
    serialsname='lgg4015'

    def __init__(self, logtarget, commport):
        super(Phone,self).__init__(logtarget, commport)
        self.mode=self.MODENONE

    def getfundamentals(self, results):

        """Gets information fundamental to interoperating with the phone and UI.

        Currently this is:

          - 'uniqueserial'     a unique serial number representing the phone
          - 'groups'           the phonebook groups
          - 'wallpaper-index'  map index numbers to names
          - 'ringtone-index'   map index numbers to ringtone names

        This method is called before we read the phonebook data or before we
        write phonebook data.
        """
        # use a hash of ESN and other stuff (being paranoid)
        self.setmode(self.MODEMODEM)
        self.log("Retrieving fundamental phone information")
        self.log("Reading phone serial number")
        results['uniqueserial']=sha.new(self.get_sim_id()).hexdigest()
        # now read groups
        self.log("Reading group information")
        results['groups']=self._get_groups()
        # getting rintone-index
        self.log('Reading Ringtone Index')
        results['ringtone-index']=self._get_ringtone_index()
        # getting wallpaper-index
        self.log('Reading Wallpaper Index')
        results['wallpaper-index']=self._get_wallpaper_index()
        # All done
        self.log("Fundamentals retrieved")
        return results

    def _get_groups(self):
        res={}
        self.charset_ascii()
        _req=self.protocolclass.list_group_req()
        for i in self.protocolclass.GROUP_INDEX_RANGE:
            _req.start_index=i
            _req.end_index=i
            try:
                _res=self.sendATcommand(_req, self.protocolclass.list_group_resp)
                if _res and _res[0].group_name:
                    res[i]={ 'name': _res[0].group_name }
            except:
                if __debug__:
                    raise
        return res

    def _ringtone_mode(self):
        _req=self.protocolclass.media_selector_set()
        _req.media_type=self.protocolclass.MEDIA_RINGTONE
        self.sendATcommand(_req, None)

    def _get_ringtone_index(self):
        """ Return the ringtone index"""
        res={}
        # Set the media type to be sound (ringtone)
        self.charset_ascii()
        self._ringtone_mode()
        # and read the list
        _req=self.protocolclass.media_list_req()
        _req.start_index=self.protocolclass.MIN_RINGTONE_INDEX
        _req.end_index=self.protocolclass.MAX_RINGTONE_INDEX
        _res=self.sendATcommand(_req, self.protocolclass.media_list_resp)
        for i,e in enumerate(_res):
            res[i]={ 'name': e.file_name, 'origin': 'ringtone' }
        return res

    def _wallpaper_mode(self):
        _req=self.protocolclass.media_selector_set()
        _req.media_type=self.protocolclass.MEDIA_WALLPAPER
        self.sendATcommand(_req, None)

    def _get_wallpaper_index(self):
        """ Return the wallpaper index"""
        res={}
        # Set the media type to be pic (wallpaper)
        self.charset_ascii()
        self._wallpaper_mode()
        # and read the list
        _req=self.protocolclass.media_list_req()
        _req.start_index=self.protocolclass.MIN_WALLPAPER_INDEX
        _req.end_index=self.protocolclass.MAX_WALLPAPER_INDEX
        _res=self.sendATcommand(_req, self.protocolclass.media_list_resp)
        for i,e in enumerate(_res):
            res[i]={ 'name': e.file_name, 'origin': 'wallpaper' }
        return res

    # Calendar stuff-----------------------------------------------------------
    cal_repeat_value={
        protocolclass.CAL_REP_DAILY: bpcalendar.RepeatEntry.daily,
        protocolclass.CAL_REP_WEEKLY: bpcalendar.RepeatEntry.weekly,
        protocolclass.CAL_REP_MONTHLY: bpcalendar.RepeatEntry.monthly,
        protocolclass.CAL_REP_YEARLY: bpcalendar.RepeatEntry.yearly }
    cal_repeat_value_r={
        bpcalendar.RepeatEntry.daily: protocolclass.CAL_REP_DAILY,
        bpcalendar.RepeatEntry.weekly: protocolclass.CAL_REP_WEEKLY,
        bpcalendar.RepeatEntry.monthly: protocolclass.CAL_REP_MONTHLY,
        bpcalendar.RepeatEntry.yearly: protocolclass.CAL_REP_YEARLY }

    def _build_bpcalendar_entry(self, phone_entry):
        entry=bpcalendar.CalendarEntry()
        entry.start=phone_entry.date+phone_entry.time
        entry.end=phone_entry.date+phone_entry.time
        entry.description=phone_entry.description
        entry.serials.append({ 'sourcetype': 'phone',
                               'id': phone_entry.index })
        entry.alarm=self.protocolclass.CAL_ALARM_VALUE.get(phone_entry.alarm, -1)
        _rpt_type=self.cal_repeat_value.get(phone_entry.repeat, None)
        if _rpt_type:
            # this is a recurrent event
            rpt=bpcalendar.RepeatEntry(_rpt_type)
            if _rpt_type!=bpcalendar.RepeatEntry.yearly:
                rpt.interval=1
            # repeat forever
            entry.end=bpcalendar.CalendarEntry.no_end_date
            entry.repeat=rpt
        return entry
        
    def getcalendar(self, result):
        self.log("Getting calendar entries")
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        res={}
        _req=self.protocolclass.calendar_read_req()
        _req.start_index=self.protocolclass.CAL_MIN_INDEX
        _req.end_index=self.protocolclass.CAL_MAX_INDEX
        _res=self.sendATcommand(_req, self.protocolclass.calendar_read_resp)
        for e in _res:
            try:
                _entry=self._build_bpcalendar_entry(e)
                res[_entry.id]=_entry
            except:
                if __debug__:
                    raise
        result['calendar']=res
        return result

    def _build_phone_cal_entry(self, entry_count, bpentry):
        entry=self.protocolclass.calendar_write_req()
        entry.index=entry_count
        entry.date=bpentry.start[:3]
        if bpentry.allday:
            entry.time=(0,0)
        else:
            entry.time=bpentry.start[3:]
        entry.description=bpentry.description
        # setting the alarm
        _alarm=self.protocolclass.CAL_ALARM_NONE
        for e in self.protocolclass.CAL_ALARM_LIST:
            if bpentry.alarm>=e[0]:
                _alarm=e[1]
                break
        entry.alarm=_alarm
        # setting repeat value
        if bpentry.repeat:
            _rpt_type=self.cal_repeat_value_r.get(bpentry.repeat.repeat_type,
                                                  self.protocolclass.CAL_REP_NONE)
        else:
            _rpt_type=self.protocolclass.CAL_REP_NONE
        entry.repeat=_rpt_type
        return entry

    def savecalendar(self, dict, merge):
        self.log('Saving calendar entries')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        _cal_dict=dict['calendar']
        _cal_list=[(x.start, k) for k,x in _cal_dict.items()]
        _cal_list.sort()
        _cal_list=_cal_list[:self.protocolclass.CAL_TOTAL_ENTRIES]
        _pre_write=self.protocolclass.calendar_write_check_req()
        for i,e in enumerate(_cal_list):
            _entry=self._build_phone_cal_entry(i, _cal_dict[e[1]])
            self.progress(i, self.protocolclass.CAL_TOTAL_ENTRIES,
                          'Writing entry %d: %s'%(i, _entry.description))
            try:
                try:
                    self.sendATcommand(_entry, None)
                    _success=True
                except:
                    _success=False
                if not _success:
                    try:
                        self.sendATcommand(_pre_write, None)
                    except:
                        pass
                    self.sendATcommand(_entry, None)
            except:
                if __debug__:
                    raise
        _req=self.protocolclass.calendar_del_req()
        for i in range(len(_cal_list), self.protocolclass.CAL_TOTAL_ENTRIES):
            self.progress(i, self.protocolclass.CAL_TOTAL_ENTRIES,
                          'Deleting entry %d'%i)
            _req.index=i
            try:
                self.sendATcommand(_req, None)
            except:
                break
        return dict

    def charset_ascii(self):
        """ Set the phone charset to some form of ascii"""
        _req=self.protocolclass.charset_set_req()
        _req.charset=self.protocolclass.CHARSET_IRA
        self.sendATcommand(_req, None)
    def charset_base64(self):
        """ Set the phone charset to Base64 (for binary transmission)"""
        _req=self.protocolclass.charset_set_req()
        _req.charset=self.protocolclass.CHARSET_BASE64
        self.sendATcommand(_req, None)

    # Detect Phone--------------------------------------------------------------
    def is_mode_modem(self):
        try:
            self.comm.sendatcommand("Z")
            self.comm.sendatcommand('E0V1')
            return True
        except:
            return False

    def get_detect_data(self, r):
        # get detection data
        r['manufacturer']=self.get_manufacturer_id()
        r['model']=self.get_model_id()
        r['firmware_version']=self.get_firmware_version()
        r['esn']=self.get_sim_id()

    @classmethod
    def detectphone(_, coms, likely_ports, res, _module, _log):
        if not len(likely_ports):
            return None
        for port in likely_ports:
            if not res.has_key(port):
                res[port]={ 'mode_modem': None, 'mode_brew': None,
                            'manufacturer': None, 'model': None,
                            'firmware_version': None, 'esn': None,
                            'firmwareresponse': None }
            try:
                if res[port]['mode_modem']==False or \
                   res[port]['model']:
                    continue
                p=Phone(_log, commport.CommConnection(_log, port, timeout=1))
                if p.is_mode_modem():
                    res[port]['mode_modem']=True
                    p.get_detect_data(res[port])
                else:
                    res[port]['mode_modem']=False
            except:
                # this port is not available
                if __debug__:
                    raise

    # Phonebook stuff-----------------------------------------------------------
    def _build_bp_entry(self, entry, groups, in_sim=False):
        res={ 'names': [ { 'full': entry.name } ] }
        _numbers=[]
        if entry.mobile:
            _numbers.append({ 'number': entry.mobile,
                              'type': 'cell' })
        if entry.home:
            _numbers.append({ 'number': entry.home,
                              'type': 'home' })
        if entry.office:
            _numbers.append({ 'number': entry.office,
                              'type': 'office'})
        if _numbers:
            res['numbers']=_numbers
        if entry.email:
            res['emails']=[{ 'email': entry.email }]
        if entry.memo:
            res['memos']=[{ 'memo': entry.memo }]
        _group=groups.get(entry.group, None)
        if _group and _group.get('name', None):
            res['categories']=[{ 'category': _group['name'] }]
        if entry.sim:
            res['flags']=[{ 'sim': in_sim }]
        return res
        
    def _get_main_phonebook(self, groups):
        """return a dict of contacts read off the phone storage area"""
        # switch to the phone storage
        _req=self.protocolclass.select_storage_req()
        _req.storage=self.protocolclass.PB_MEMORY_MAIN
        self.sendATcommand(_req, None)
        # read the entries
        _req=self.protocolclass.read_phonebook_req()
        _req.start_index=self.protocolclass.PB_MAIN_MIN_INDEX
        _req.end_index=self.protocolclass.PB_MAIN_MAX_INDEX
        _res=self.sendATcommand(_req, self.protocolclass.read_phonebook_resp)
        res={}
        for e in _res:
            res[e.index]=self._build_bp_entry(e, groups)
        return res

    def _get_sim_phonebook(self, groups):
        """return a dict of contacts read off the phone SIM card"""
        # switch to the phone storage
        _req=self.protocolclass.select_storage_req()
        _req.storage=self.protocolclass.PB_MEMORY_SIM
        self.sendATcommand(_req, None)
        # read the entries
        _req=self.protocolclass.read_phonebook_req()
        _req.start_index=self.protocolclass.PB_SIM_MIN_INDEX
        _req.end_index=self.protocolclass.PB_SIM_MAX_INDEX
        _res=self.sendATcommand(_req, self.protocolclass.read_sim_phonebook_resp)
        res={}
        for e in _res:
            res[1000+e.index]=self._build_bp_entry(e, groups, in_sim=True)
        return res

    def getphonebook(self,result):
        """Reads the phonebook data.  The L{getfundamentals} information will
        already be in result."""
        self.log('Getting phonebook')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        _groups=result.get('groups', {})
        pb_book=self._get_main_phonebook(_groups)
        pb_book.update(self._get_sim_phonebook(_groups))
        result['phonebook']=pb_book
        return pb_book

    def _in_sim(self, entry):
        """ Return True if this entry has the sim flag set, indicating that
        it should be stored on the SIM card.
        """
        for l in entry.get('flags', []):
            if l.has_key('sim'):
                return l['sim']
        return False

    def _lookup_group(self, entry, groups):
        try:
            _name=entry['categories'][0]['category']
        except:
            return 0
        for k,e in groups.items():
            if e['name']==_name:
                return k
        return 0

    def _build_main_entry(self, entry, groups):
        _req=self.protocolclass.write_phonebook_req()
        _req.group=self._lookup_group(entry, groups)
        _req.name=nameparser.getfullname(entry['names'][0])
        _req.email=entry.get('emails', [{'email': ''}])[0]['email']
        _req.memo=entry.get('memos', [{'memo': ''}])[0]['memo']
        for n in entry.get('numbers', []):
            _type=n['type']
            _number=n['number']
            if _type=='cell':
                _req.mobile=_number
                _req.mobile_type=129
            elif _type=='home':
                _req.home=_number
                _req.home_type=129
            elif _type=='office':
                _req.office=_number
                _req.office_type=129
        return _req

    def _build_sim_entry(self, entry, groups):
        _req=self.protocolclass.write_sim_phonebook_req()
        _req.group=self._lookup_group(entry, groups)
        _req.name=nameparser.getfullname(entry['names'][0])
        _number=entry.get('numbers', [{'number': ''}])[0]['number']
        if _number:
            _req.number=_number
            _req.number_type=129
        return _req

    def _save_main_phonebook(self, entries, groups):
        """ got the the phonebook dict and write them out to the phone"""
        # build the full names & SIM keys
        _pb_list=[(nameparser.getfullname(e['names'][0]), k) \
                  for k,e in entries.items() if not self._in_sim(e)]
        # sort alphabetical order
        _pb_list.sort()
        # switch to the main phone storage
        _req=self.protocolclass.select_storage_req()
        _req.storage=self.protocolclass.PB_MEMORY_MAIN
        self.sendATcommand(_req, None)
        _del_entry=self.protocolclass.del_phonebook_req()
        # send each entry to the phone
        _index=self.protocolclass.PB_MAIN_MIN_INDEX
        for l in _pb_list:
            _del_entry.index=_index
            _index+=1
            self.sendATcommand(_del_entry, None)
            time.sleep(0.2)
            _req=self._build_main_entry(entries[l[1]], groups)
            self.progress(_index, self.protocolclass.PB_MAIN_MAX_INDEX,
                          'Writing entry %d: %s'%(_index, _req.name))
            try:
                self.sendATcommand(_req, None)
                _retry=False
            except:
                _retry=True
            if _retry:
                try:
                    self.sendATcommand(_req, None)
                except:
                    self.log('Failed to write entry %d: %s'%(_index, _req.name))
            time.sleep(0.2)
        # clear out the rest of the phonebook
        for i in range(_index, self.protocolclass.PB_MAIN_MAX_INDEX+1):
            self.progress(i, self.protocolclass.PB_MAIN_MAX_INDEX,
                          'Deleting entry %d'%i)
            try:
                _del_entry.index=i
                self.sendATcommand(_del_entry, None)
                continue
            except:
                self.log('Trying to delete entry %d'%i)
            try:
                self.sendATcommand(_del_entry, None)
            except:
                self.log('Failed to delete entry %d'%i)

    def _save_sim_phonebook(self, entries, groups):
        """ got the the phonebook dict and write them out to the phone"""
        # build the full names & SIM keys
        _pb_list=[(nameparser.getfullname(e['names'][0]), k) \
                  for k,e in entries.items() if self._in_sim(e)]
        # sort alphabetical order
        _pb_list.sort()
        # switch to the main phone storage
        _req=self.protocolclass.select_storage_req()
        _req.storage=self.protocolclass.PB_MEMORY_SIM
        self.sendATcommand(_req, None)
        _del_entry=self.protocolclass.del_phonebook_req()
        # send each entry to the phone
        _index=self.protocolclass.PB_SIM_MIN_INDEX
        for l in _pb_list:
            _del_entry.index=_index
            _index+=1
            self.sendATcommand(_del_entry, None)
            time.sleep(0.2)
            _req=self._build_sim_entry(entries[l[1]], groups)
            self.progress(_index, self.protocolclass.PB_SIM_MAX_INDEX,
                          'Writing SIM entry %d: %s'%(_index, _req.name))
            try:
                self.sendATcommand(_req, None)
                _retry=False
            except:
                _retry=True
            if _retry:
                try:
                    self.sendATcommand(_req, None)
                except:
                    self.log('Failed to write SIM entry %d: %s'%(_index, _req.name))
            time.sleep(0.2)
        # clear out the rest of the phonebook
        for i in range(_index, self.protocolclass.PB_SIM_MAX_INDEX+1):
            self.progress(i, self.protocolclass.PB_SIM_MAX_INDEX,
                          'Deleting SIM entry %d'%i)
            try:
                _del_entry.index=i
                self.sendATcommand(_del_entry, None)
                continue
            except:
                self.log('Trying to delete entry %d'%i)
            try:
                self.sendATcommand(_del_entry, None)
            except:
                self.log('Failed to delete entry %d'%i)

    def savephonebook(self, data):
        "Saves out the phonebook"
        self.log('Writing phonebook')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        
        pb_book=data.get('phonebook', {})
        pb_groups=data.get('groups', {})
        self._save_main_phonebook(pb_book, pb_groups)
        self._save_sim_phonebook(pb_book, pb_groups)
        return data

    # Ringtone stuff------------------------------------------------------------
    def _del_media_files(self, names):
        self.charset_ascii()
        _req=self.protocolclass.del_media_req()
        for n in names:
            self.log('Deleting media %s'%n)
            _req.file_name=n
            try:
                self.sendATcommand(_req, None)
            except:
                self.log('Failed to delete media %s'%n)

    def _add_media_file(self, file_name, media_name, media_code, data):
        """ Add one media ringtone
        """
        if not file_name or not media_name or not data:
            return False
        self.log('Writing media %s'%file_name)
        _media_name=''
        for s in media_name:
            _media_name+=s+'\x00'
        _cmd='AT+DDLW=0,"%s","%s",%d,%d,0,0,0,0\r' % \
              (file_name, base64.encodestring(_media_name), len(data),
               media_code)
        _data64=base64.encodestring(data)
        self.comm.write(str(_cmd))
        if self.comm.read(4)!='\r\n> ':
            return False
        for l in _data64.split('\n'):
            if l:
                self.comm.write(l+'\n')
                time.sleep(0.01)
        self.comm.write(str('\x1A'))
        return self.comm.read(6)=='\r\nOK\r\n'

    def _add_ringtones(self, names, name_dict, media):
        self.charset_base64()
        for n in names:
            _media_key=name_dict[n]
            if not self._add_media_file(n, common.stripext(n), 20,
                                      media[_media_key].get('data', '')):
                self.log('Failed to send ringtone %s'%n)
        self.charset_ascii()
        
    def saveringtones(self, result, merge):
        self.log('Saving ringtones')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        self._ringtone_mode()

        media=result.get('ringtone', {})
        media_index=result.get('ringtone-index', {})
        media_names=[x['name'] for x in media.values()]
        index_names=[x['name'] for x in media_index.values()]
        del_names=[x for x in index_names if x not in media_names]
        new_names=[x for x in media_names if x not in index_names]
        # deleting files
        self._del_media_files(del_names)
        # and add new files
        names_to_keys={}
        for k,e in media.items():
            names_to_keys[e['name']]=k
        self._add_ringtones(new_names, names_to_keys, media)
        return result

    def getringtones(self, result):
        self.log('Reading ringtones index')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        self._ringtone_mode()

        media={}
        media_index=self._get_ringtone_index()
        for e in media_index.values():
            media[e['name']]='dummy data'
        result['ringtone']=media
        result['ringtone-index']=media_index
        return result

    # Wallpaper stuff-----------------------------------------------------------
    def getwallpapers(self, result):
        self.log('Reading wallpaper index')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        self._wallpaper_mode()

        media={}
        media_index=self._get_wallpaper_index()
        _dummy_data=file(guihelper.getresourcefile('wallpaper.png'),'rb').read()
        for e in media_index.values():
            media[e['name']]=_dummy_data
        result['wallpapers']=media
        result['wallpaper-index']=media_index
        return result

    def _add_wallpapers(self, names, name_dict, media):
        self.charset_base64()
        for n in names:
            _media_key=name_dict[n]
            if not self._add_media_file(n, common.stripext(n), 12,
                                      media[_media_key].get('data', '')):
                self.log('Failed to send wallpaper %s'%n)
        self.charset_ascii()
        
    def savewallpapers(self, result, merge):
        self.log('Saving wallpapers')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        self._wallpaper_mode()

        media=result.get('wallpapers', {})
        media_index=result.get('wallpaper-index', {})
        media_names=[x['name'] for x in media.values()]
        index_names=[x['name'] for x in media_index.values()]
        del_names=[x for x in index_names if x not in media_names]
        new_names=[x for x in media_names if x not in index_names]
        # deleting files
        self._del_media_files(del_names)
        # and add new files
        names_to_keys={}
        for k,e in media.items():
            names_to_keys[e['name']]=k
        self._add_wallpapers(new_names, names_to_keys, media)
        return result

    # Memo stuff----------------------------------------------------------------
    def getmemo(self, result):
        self.log('Reading Memo')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        _req=self.protocolclass.memo_read_req()
        _res=self.sendATcommand(_req, self.protocolclass.memo_read_resp)
        res={}
        for e in _res:
            _memo=memo.MemoEntry()
            _memo.text=e.text
            res[_memo.id]=_memo
        result['memo']=res
        return res

    def savememo(self, result, merge):
        self.log('Writing Memo')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        # first, delete all existing memos
        _req=self.protocolclass.memo_del_req()
        for i in range(self.protocolclass.MEMO_MIN_INDEX,
                       self.protocolclass.MEMO_MAX_INDEX+1):
            _req.index=i
            try:
                self.sendATcommand(_req, None)
            except:
                pass
        # then update with new ones
        _memo_dict=result.get('memo', {})
        _keys=_memo_dict.keys()
        _keys.sort()
        _req=self.protocolclass.memo_write_req()
        for k in _keys:
            _req.text=_memo_dict[k].text
            try:
                self.sendATcommand(_req, None)
            except:
                self.log('Failed to write memo %s'%_req.text)
        return _memo_dict

    # SMS Stuff-----------------------------------------------------------------
    def _process_sms(self, _resp, res):
        # extract the SMS messages from the respons string & update the dict
        for i in range(0, len(_resp), 2):
            try:
                _entry=self.protocolclass.sms_msg_list_header()
                _buf=prototypes.buffer(_resp[i])
                _entry.readfrombuffer(_buf, logtitle="SMS #"+i)
                _sms=sms.SMSEntry()
                if _entry.msg_type==self.protocolclass.SMS_MSG_REC_UNREAD or \
                   _entry.msg_type==self.protocolclass.SMS_MSG_REC_READ:
                    # unread/read inbox
                    _sms._from=_entry.address
                    _sms.folder=sms.SMSEntry.Folder_Inbox
                    _sms.read=_entry.msg_type==self.protocolclass.SMS_MSG_REC_READ
                elif _entry.msg_type==self.protocolclass.SMS_MSG_STO_SENT:
                    # outbox
                    _sms.add_recipient(_entry.address)
                    _sms.folder=sms.SMSEntry.Folder_Sent
                elif _entry.msg_type==self.protocolclass.SMS_MSG_STO_UNSENT:
                    # saved
                    _sms.folder=sms.SMSEntry.Folder_Saved
                    _sms.add_recipient(_entry.address)
                else:
                    self.log('Unknown message type: %s'%_entry.msg_type)
                    _sms=None
                if _sms:
                    if _entry.timestamp:
                        _sms.datetime=_entry.timestamp
                    _sms.text=_resp[i+1]
                    res[_sms.id]=_sms
            except:
                if __debug__:
                    raise
        return res

    def getsms(self, result):
        self.log('Getting SMS Messages')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        res={}
        # set format to text
        _req=self.protocolclass.sms_format_req()
        self.sendATcommand(_req, None)
        self.log('Getting SMS messages from the phone memory')
        _sms_mem=self.protocolclass.sms_memory_select_req()
        _sms_mem.list_memory=self.protocolclass.SMS_MEMORY_PHONE
        self.sendATcommand(_sms_mem, None)
        _list_sms=self.protocolclass.sms_msg_list_req()
        _resp=self.sendATcommand(_list_sms, None)
        self._process_sms(_resp, res)
        self.log('Getting SMS message from the SIM card')
        _sms_mem.list_memory=self.protocolclass.SMS_MEMORY_SIM
        self.sendATcommand(_sms_mem, None)
        _resp=self.sendATcommand(_list_sms, None)
        self._process_sms(_resp, res)
        try:
            # this is to clear the next error
            self.sendATcommand(_sms_mem, None)
        except commport.ATError:
            pass
        result['sms']=res
        return result

    # Call History stuff--------------------------------------------------------
    def _get_history_calls(self, log_str, call_type, min_idx, max_idx):
        self.log(log_str)
        _sel_mem=self.protocolclass.select_storage_req()
        _sel_mem.storage=call_type
        self.sendATcommand(_sel_mem, None)
        _list_pb=self.protocolclass.read_phonebook_req()
        _list_pb.start_index=min_idx
        _list_pb.end_index=max_idx
        self.sendATcommand(_list_pb, None)
        
    def getcallhistory(self, result):
        self.log('Getting Call History')
        self.setmode(self.MODEMODEM)
        self.charset_ascii()
        res={}
        for l in self.protocolclass.PB_CALL_HISTORY_INFO:
            self._get_history_calls(*l)
        result['call_history']=res
        return result

#-------------------------------------------------------------------------------
parent_profile=com_etsi.Profile
class Profile(parent_profile):

    serialsname=Phone.serialsname

    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=128
    MAX_WALLPAPER_BASENAME_LENGTH=19
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_ ."
    WALLPAPER_CONVERT_FORMAT="jpg"
    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_ ."
    RINGTONE_LIMITS= {
        'MAXSIZE': 20480
    }
    # use for auto-detection
    phone_manufacturer='LGE'
    phone_model='G4015'

    usbids=( ( 0x10AB, 0x10C5, 1),
        )
    deviceclasses=("serial",)

    imageorigins={}
    imageorigins.update(common.getkv(parent_profile.stockimageorigins, "images"))
  
    imagetargets={}
    imagetargets.update(common.getkv(parent_profile.stockimagetargets, "wallpaper",
                                      {'width': 128, 'height': 128, 'format': "JPEG"}))

    def GetImageOrigins(self):
        # Note: only return origins that you can write back to the phone
        return self.imageorigins

    def GetTargetsForImageOrigin(self, origin):
        # right now, supporting just 'images' origin
        if origin=='images':
            return self.imagetargets

    def __init__(self):
        parent_profile.__init__(self)

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('ringtone', 'read', None),   # all ringtone reading
        ('ringtone', 'write', 'OVERWRITE'),
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', 'OVERWRITE'),
        ('memo', 'read', None),     # all memo list reading DJP
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing DJP
        ('sms', 'read', None),     # all SMS list reading DJP
        ('call_history', 'read', None),
        )

    def convertphonebooktophone(self, helper, data):
        return data
