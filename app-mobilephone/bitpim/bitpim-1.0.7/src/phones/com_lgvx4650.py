### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx4650.py 4370 2007-08-21 21:39:36Z djpham $

"""Communicate with the LG VX4650 cell phone

The VX4600 is substantially similar to the VX4400.

"""

# standard modules
from __future__ import with_statement
import contextlib
import datetime
import time
import cStringIO
import re
import sha

# my modules
import bpcalendar
import call_history
import common
import conversions
import copy
import p_brew
import p_lgvx4650
import com_lgvx4400
import com_brew
import com_phone
import com_lg
import commport
import helpids
import memo
import prototypes
import sms

class Phone(com_lgvx4400.Phone):
    "Talk to the LG VX4650 cell phone"

    desc="LG-VX4650"
    helpid=helpids.ID_PHONE_LGVX4650
    protocolclass=p_lgvx4650
    serialsname='lgvx4650'

    # 4650 index files
    imagelocations=(
        # offset, index file, files location, type, maximumentries
        ( 30, "download/dloadindex/brewImageIndex.map", "dload/img", "images", 30),
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries
        ( 50, "download/dloadindex/brewRingerIndex.map", "user/sound/ringer", "ringers", 30),
        )

    builtinimages={ 80: ('Large Pic. 1', 'Large Pic. 2', 'Large Pic. 3',
                         'Large Pic. 4', 'Large Pic. 5', 'Large Pic. 6',
                         'Large Pic. 7', 'Large Pic. 8', 'Large Pic. 9', 
                         'Large Pic. 10', 'Large Pic. 11', 'Large Pic. 12',
                         'Large Pic. 13', 'Large Pic. 14', 'Large Pic. 15', 
                         'Large Pic. 16', 'Large Pic. 17', 'Large Pic. 18',
                         'Large Pic. 19', 'Large Pic. 20', 'Large Pic. 21', 
                         'Large Pic. 22', 'Large Pic. 23', 'Large Pic. 24',
                         'Large Pic. 25', 'Large Pic. 26', 'Large Pic. 27', 
                         'Large Pic. 28', 'Large Pic. 29', 'Large Pic. 30',
                         'Large Pic. 31', 'Large Pic. 32', 'Large Pic. 33' ) }

    builtinringtones={ 1: ('Ring 1', 'Ring 2', 'Ring 3', 'Ring 4', 'Ring 5',
                           'VZW Default Tone', 'Arabesque', 'Piano Sonata',
                           'Latin', 'When the saints go', 'Bach Cello suite',
                           'Speedy Way', 'CanCan', 'Grand Waltz', 'Toccata and Fugue',
                           'Bumble Bee', 'March', 'Circus Band',
                           'Sky Garden', 'Carmen Habanera', 'Hallelujah',
                           'Sting', 'Farewell', 'Pachelbel Canon', 'Carol 1',
                           'Carol 2'), # 'Vibrate', 'Lamp' ),
                       100: ( 'Chimes high', 'Chimes low', 'Ding', 'TaDa',
                              'Notify', 'Drum', 'Claps', 'FanFare', 'Chord high',
                              'Chord low' )
                       }
    VoiceMemoDir='VoiceDB/All/Memos'

    def __init__(self, logtarget, commport):
        com_lgvx4400.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE

    def getfirmwareinformation(self):
        self.log("Getting firmware information")
        req=self.protocolclass.firmwarerequest()
        res=self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
        return res

    def getmediaindex(self, builtins, maps, results, key):
        """Gets the media (wallpaper/ringtone) index

        @param builtins: the builtin list on the phone
        @param results: places results in this dict
        @param maps: the list of index files and locations
        @param key: key to place results in
        """
        media=com_lgvx4400.Phone.getmediaindex(self, (), maps, results, key)

        # builtins
        for k,e in builtins.items():
            c=k
            for name in e:
                media[c]={ 'name': name, 'origin': 'builtin' }
                c+=1
        # voice memos index
        if key=='ringtone-index':
            try:
                vmemo_files=self.listfiles(self.VoiceMemoDir)
                keys=vmemo_files.keys()
                keys.sort()
                _idx_cnt=210
                for k in keys:
                    if k.endswith('.qcp'):
                        num_str=k[-8:-4]
                        media[_idx_cnt]={ 'name': 'VoiceMemo'+num_str,
                                                  'origin': 'voicememo' }
                        _idx_cnt+=1
            except:
                if __debug__:
                    raise
        return media

    # Ringtone stuff------------------------------------------------------------
    def getringtones(self, result):
        result=com_lgvx4400.Phone.getringtones(self, result)
        if not conversions.helperavailable('pvconv'):
            return result
        media=result['ringtone']
        # get& convert the voice memo files
        with contextlib.nested(common.usetempfile('qcp'),
                               common.usetempfile('wav')) as (_qcp_file, _wav_file):
            try:
                vmemo_files=self.listfiles(self.VoiceMemoDir)
                keys=vmemo_files.keys()
                for k in keys:
                    if k.endswith('.qcp'):
                        key_name='VoiceMemo'+k[-8:-4]
                        file(_qcp_file, 'wb').write(self.getfilecontents(k, True))
                        conversions.convertqcptowav(_qcp_file, _wav_file)
                        media[key_name]=file(_wav_file, 'rb').read()
            except:
                if __debug__:
                    raise
        result['ringtone']=media
        return result

    def saveringtones(self, results, merge):
        _new_ringtones=results.get('ringtone', {})
        _rt_index=results.get('ringtone-index', {})
        # list of voicememo names
        _voice_memo_l=[x['name'] for k,x in _rt_index.items() \
                       if x.get('origin', '')=='voicememo']
        # list of media to delete
        _del_keys=[k for k,x in _new_ringtones.items() \
                   if x.get('name', None) in _voice_memo_l]
        for k in _del_keys:
            del _new_ringtones[k]
        results['ringtone']=_new_ringtones
        return com_lgvx4400.Phone.saveringtones(self, results, merge)

    # Phonebook stuff-----------------------------------------------------------
    def savephonebook(self, data):
        "Saves out the phonebook"
        res=com_lgvx4400.Phone.savephonebook(self, data)
        # build a dict to manually update the wp index
        pbook=res.get('phonebook', {})
        wallpaper_index=res.get('wallpaper-index', {})
        r1={}
        for k,e in pbook.items():
            r1[e['bitpimserial']['id']]={ 'wallpaper': \
                                          self._findmediainindex(wallpaper_index,
                                                                 e['wallpaper'],
                                                                 e['name'],
                                                                 'wallpaper'),
                                          'group': e['group'] }
        serialupdates=data.get("serialupdates", [])
        r2={}
        for bps, serials in serialupdates:
            r2[serials['serial1']]=r1[bps['id']]
        if self._update_wallpaper_index(r2):
            data["rebootphone"]=True
        return res

    def _update_wallpaper_index(self, wpi):
        # manually update wallpaper indices since the normal update process
        # does not seem to work
        buf=prototypes.buffer(self.getfilecontents(
            self.protocolclass.pb_file_name))
        pb=self.protocolclass.pbfile()
        pb.readfrombuffer(buf, logtitle="Read "+self.protocolclass.pb_file_name)
        update_flg=False
        for e in pb.items:
            _info=wpi.get(e.serial1, None)
            if _info:
                wp=_info.get('wallpaper', None)
                if wp is not None and wp!=e.wallpaper:
                    update_flg=True
                    e.wallpaper=wp
                gr=_info.get('group', None)
                if gr is not None and gr!=e.group:
                    update_flg=True
                    e.group=gr
        if update_flg:
            self.log('Updating wallpaper index')
            buf=prototypes.buffer()
            pb.writetobuffer(buf, logtitle="Updated index "+self.protocolclass.pb_file_name)
            self.writefile(self.protocolclass.pb_file_name, buf.getvalue())
        return update_flg

    # Calendar stuff------------------------------------------------------------
    # all taken care by the VX4400

    # Text Memo stuff-----------------------------------------------------------
    # all taken care by the VX4400

    # Call History stuff--------------------------------------------------------
    _call_history_info={
        call_history.CallHistoryEntry.Folder_Incoming: protocolclass.incoming_call_file,
        call_history.CallHistoryEntry.Folder_Outgoing: protocolclass.outgoing_call_file,
        call_history.CallHistoryEntry.Folder_Missed: protocolclass.missed_call_file
        }
    def getcallhistory(self, result):
        # read the call history files
        res={}
        for _folder, _file_name in Phone._call_history_info.items():
            try:
                buf=prototypes.buffer(self.getfilecontents(_file_name))
                hist_file=self.protocolclass.callhistoryfile()
                hist_file.readfrombuffer(buf, logtitle="Read call history")
                for i in range(hist_file.itemcount):
                    hist_call=hist_file.items[i]
                    entry=call_history.CallHistoryEntry()
                    entry.folder=_folder
                    entry.datetime=hist_call.datetime
                    entry.number=hist_call.number
                    entry.name=hist_call.name
                    if _folder!=call_history.CallHistoryEntry.Folder_Missed:
                        entry.duration=hist_call.duration
                    res[entry.id]=entry
            except com_brew.BrewNoSuchFileException:
                pass
        result['call_history']=res
        return result

    # SMS stuff-----------------------------------------------------------------
    def _setquicktext(self, result):
        canned_file=Phone.SMSCannedFile()
        canned_file.set_sms_canned_data(result.get('canned_msg', []))
        buf=prototypes.buffer()
        canned_file.writetobuffer(buf, logtitle="Updated "+self.protocolclass.sms_canned_file)
        self.writefile(self.protocolclass.sms_canned_file, buf.getvalue())

    def _getquicktext(self):
        try:
            buf=prototypes.buffer(self.getfilecontents(
                self.protocolclass.sms_canned_file))
            canned_file=Phone.SMSCannedFile()
            canned_file.readfrombuffer(buf, logtitle="Read SMS canned text")
            return canned_file.get_sms_canned_data()
        except:
            if __debug__:
                raise
            return []

    my_model='VX4650'

    class SMSCannedFile(protocolclass.SMSCannedFile):
        def __init__(self, *args, **kwargs):
            Phone.protocolclass.SMSCannedFile.__init__(self, *args, **kwargs)

        def get_sms_canned_data(self):
            return [{ 'text': e.text,
                      'type': sms.CannedMsgEntry.user_type } for e in self.items]

        def set_sms_canned_data(self, canned_list):
            msg_lst=[x['text'] for x in canned_list \
                     if x['type']==sms.CannedMsgEntry.user_type]
            item_count=min(Phone.protocolclass.SMS_CANNED_MAX_ITEMS, len(msg_lst))
            for i in range(item_count):
                entry=Phone.protocolclass.SMSCannedMsg()
                entry.text=msg_lst[i]
                self.items.append(entry)
            entry=Phone.protocolclass.SMSCannedMsg()
            entry.text=''
            for i in range(item_count, Phone.protocolclass.SMS_CANNED_MAX_ITEMS):
                self.items.append(entry)

    # Phone Info stuff----------------------------------------------------------
    def _get_phone_number(self):
        # return the phone number of this phone
        s=''
        try:
            buf=self.getfilecontents('nvm/nvm/nvm_0000')
            ofs=0x240
            if buf[ofs]=='\x01':
                ofs+=1
                while buf[ofs]!='\x01':
                    s+=buf[ofs]
                    ofs+=1
        except:
            if __debug__:
                raise
        return s
    def getphoneinfo(self, phone_info):
        # returning some basic phone info
        # double check if this's the right phone.
        try:
            if self.getfilecontents(self.brew_version_file)[:len(self.my_model)]==self.my_model:
                phone_info.model=self.my_model
                phone_info.manufacturer=Profile.phone_manufacturer
                phone_info.phone_number=self._get_phone_number()
                phone_info.firmware_version=self.getfirmwareinformation().firmwareversion
                phone_info.esn=self.get_esn()
        except:
            if __debug__:
                raise

#------------------------------------------------------------------------------
parentprofile=com_lgvx4400.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=128
    MAX_WALLPAPER_BASENAME_LENGTH=19
    WALLPAPER_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ."
    WALLPAPER_CONVERT_FORMAT="bmp"

    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ."

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX4650'

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 128, 'height': 114, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 128, 'height': 128, 'format': "JPEG"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
        ('ringtone', 'write', 'OVERWRITE'),
        ('memo', 'read', None),     # all memo list reading DJP
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing DJP
        ('call_history', 'read', None),
        ('sms', 'read', None),
        ('sms', 'write', 'OVERWRITE'),
       )

    def __init__(self):
        parentprofile.__init__(self)
