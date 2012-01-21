#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx8500.py 4305 2007-07-16 04:05:25Z djpham $

"""
Communicate with the LG VX8500 cell phone
"""
# standard modules
import datetime

# wx modules

# BitPim modules
import common
import com_brew
import com_lg
import com_lgvx8300
import helpids
import fileinfo
import guihelper
import os
import p_brew
import p_lgvx8500
import playlist
import prototypes
import prototypeslg
import t9editor

parentphone=com_lgvx8300.Phone
class Phone(parentphone):
    desc="LG-VX8500"
    helpid=helpids.ID_PHONE_LGVX8500

    protocolclass=p_lgvx8500
    serialsname='lgvx8500'

    my_model='VX8500'
    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'VZW Default Ringtone') + \
                      tuple(['Ringtone '+`n` for n in range(1,13)]) + \
                      ('No Ring',)

    ringtonelocations= (
        #  type          index file            default dir        external dir    max  type Index
        ( 'ringers',    'dload/myringtone.dat','brew/16452/lk/mr','mmc1/ringers', 100, 0x01, 100),
        ( 'sounds',     'dload/mysound.dat',   'brew/16452/ms',   '',             100, 0x02, None),
        ( 'sounds(sd)', 'dload/sd_sound.dat',  'mmc1/my_sounds',  '',             100, 0x02, None),
        ( 'music',      'dload/efs_music.dat', 'my_music',        '',             100, 0x104, None),
        ( 'music(sd)',  'dload/sd_music.dat',  'mmc1/my_music',   '',             100, 0x14, None),
        )

    wallpaperlocations= (
        #  type          index file            default dir     external dir  max  type Index
        ( 'images',     'dload/image.dat',    'brew/16452/mp', '',           100, 0x00, 100),
        ( 'images(sd)', 'dload/sd_image.dat', 'mmc1/my_pix',   '',           100, 0x10, None),
        ( 'video',      'dload/video.dat',    'brew/16452/mf', '',           100, 0x03, None),
        ( 'video(sd)',  'dload/sd_video.dat', 'mmc1/my_flix',  '',           100, 0x13, None),
        )

    def setDMversion(self):
        """Define the DM version required for this phone, default to DMv5"""
        _fw_version=self.get_firmware_version()[-1]
        self._DMv5=self.my_model=='VX8500' and _fw_version>'4'

    # Fundamentals:
    #  - get_esn             - same as LG VX-8300
    #  - getgroups           - same as LG VX-8100
    #  - getwallpaperindices - LGUncountedIndexedMedia
    #  - getrintoneindices   - LGUncountedIndexedMedia
    #  - DM Version          - T85VZV01 - T85VZV04: 4, T85VZV05 - : 5

    # Phonebook stuff-----------------------------------------------------------
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
                msgrt=_info.get('msgringtone', None)
                if msgrt is not None and msgrt!=e.msgringtone:
                    update_flg=True
                    e.msgringtone=msgrt
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

    def savephonebook(self, data):
        "Saves out the phonebook"
        res=parentphone.savephonebook(self, data)
        # retrieve the phonebook entries
        _buf=prototypes.buffer(self.getfilecontents(
            self.protocolclass.pb_file_name))
        _pb_entries=self.protocolclass.pbfile()
        _pb_entries.readfrombuffer(_buf, logtitle="Read phonebook file "+self.protocolclass.pb_file_name)
        _rt_index=data.get('ringtone-index', {})
        _wp_index=data.get('wallpaper-index', {})
        # update info that the phone software failed to do!!
        self._update_pb_info(_pb_entries, data)
        # fix up ringtone index
        self._write_path_index(_pb_entries, 'ringtone',
                               _rt_index,
                               self.protocolclass.RTPathIndexFile,
                               (0xffff,))
        # fix up msg ringtone index
        self._write_path_index(_pb_entries, 'msgringtone',
                               _rt_index,
                               self.protocolclass.MsgRTIndexFile,
                               (0xffff,))
        # fix up wallpaer index
        self._write_path_index(_pb_entries, 'wallpaper',
                               _wp_index,
                               self.protocolclass.WPPathIndexFile,
                               (0, 0xffff,))
        return res

    # Playlist stuff------------------------------------------------------------
    def _get_all_songs(self, fundamentals):
        # return a list of all available songs
        _rt_index=fundamentals.get('ringtone-index', {})
        return [x['name'] for _,x in _rt_index.items() \
                if x.get('origin', None) in ('music', 'music(sd)') ]
    def _read_pl_list(self, filename):
        # read and return the contents of the specified playlist
        _req=self.protocolclass.PLPlayListFile()
        _buf=prototypes.buffer(self.getfilecontents(filename))
        _req.readfrombuffer(_buf, logtitle="Read playlist "+filename)
        _songs=[]
        for _item in _req.items:
            _songs.append(common.basename(_item.pathname))
        _entry=playlist.PlaylistEntry()
        _entry.name=common.stripext(common.basename(filename))
        _entry.songs=_songs
        return _entry
    def getplaylist(self, result):
        # return a list of all available songs and playlists
        # first, retrieve the list of all songs
        result[playlist.masterlist_key]=self._get_all_songs(result)
        # get a list of playlists and their contents
        _pl_list=[]
        try:
            _req=self.protocolclass.PLIndexFile()
            _buf=prototypes.buffer(
                self.getfilecontents(self.protocolclass.PLIndexFileName))
            _req.readfrombuffer(_buf, logtitle='Reading Playlist Index')
            for _item in _req.items:
                try:
                    _pl_list.append(self._read_pl_list(_item.pathname))
                except com_brew.BrewNoSuchFileException:
                    pass
                except:
                    if __debug__:
                        raise
        except com_brew.BrewNoSuchFileException:
            pass
        except:
            if __debug__:
                raise
        result[playlist.playlist_key]=_pl_list
        return result

    def _get_info_from_index(self, filename):
        _res={}
        try:
            _buf=prototypes.buffer(
                self.getfilecontents(filename))
            _req=self.protocolclass.indexfile()
            _req.readfrombuffer(_buf, logtitle='Reading Index File')
            for _item in _req.items:
                _res[common.basename(_item.filename)]={ 'size': _item.size,
                                                        'filename': _item.filename }
        except com_brew.BrewNoSuchFileException:
            pass
        except:
            if __debug__:
                raise
        return _res
    def _get_song_info(self):
        # return a dict of all songs & their info
        _res=self._get_info_from_index('dload/efs_music.dat')
        _res.update(self._get_info_from_index('dload/sd_music.dat'))
        return _res
    def _write_a_playlist(self, filename, pl, song_info):
        # write a single playlist
        _pl_file=self.protocolclass.PLPlayListFile()
        _dt=datetime.datetime.now()
        _onesec=datetime.timedelta(seconds=1)
        _plsize=0
        for _song in pl.songs:
            if song_info.has_key(_song):
                _dt-=_onesec
                _entry=self.protocolclass.PLSongEntry(
                    pathname=song_info[_song]['filename'],
                    date=_dt.timetuple()[:6],
                    size=song_info[_song]['size'])
                _pl_file.items.append(_entry)
                _plsize+=1
                if _plsize>=self.protocolclass.PLMaxSize:
                    # reached max size
                    break
        _buf=prototypes.buffer()
        _pl_file.writetobuffer(_buf,
                               logtitle='Writing Playlist '+pl.name)
        self.writefile(filename, _buf.getvalue())
    def _write_playlists(self, playlists, song_info):
        _pl_index=self.protocolclass.PLIndexFile()
        for _pl in playlists:
            try:
                _filename=self.protocolclass.PLFilePath+'/'+_pl.name+\
                           self.protocolclass.PLExt
                self._write_a_playlist(_filename, _pl, song_info)
                _pl_index.items.append(
                    self.protocolclass.PLIndexEntry(pathname=_filename))
            except:
                self.log('Failed to write playlist '+_pl.name)
                if __debug__:
                    raise
        try:
            _buf=prototypes.buffer()
            _pl_index.writetobuffer(_buf,
                                    logtitle='Writing Playlist Index')
            self.writefile(self.protocolclass.PLIndexFileName,
                           _buf.getvalue())
        except:
            self.log('Failed to write Playlist Index file')
            if __debug__:
                raise
    def saveplaylist(self, result, merge):
        # delete all existing playlists
        _buf=prototypes.buffer(self.getfilecontents(
            self.protocolclass.PLIndexFileName))
        _req=self.protocolclass.PLIndexFile()
        _req.readfrombuffer(_buf, logtitle='Reading Playlist Index')
        for _item in _req.items:
            try:
                self.rmfile(_item.pathname)
            except com_brew. BrewNoSuchFileException:
                pass
            except:
                if __debug__:
                    raise
        # get info on all songs
        _song_info=self._get_song_info()
        # update the new playlists
        self._write_playlists(result.get(playlist.playlist_key, []),
                              _song_info)
        return result

    # T9 DB stuff
    def _get_current_db(self):
        _current_db=None
        try:
            _data=self.getfilecontents(
                self.protocolclass.T9USERDBFILENAME)
            if _data:
                _current_db=self.protocolclass.t9udbfile()
                _current_db.readfrombuffer(prototypes.buffer(_data),
                                           logtitle='Reading T9 User DB File')
        except com_brew.BrewNoSuchFileException:
            pass
        return _current_db
    def _copy_fields(self, old, new):
        for _field in ('unknown1', 'unknown2', 'unknown3', 'unknown4'):
            setattr(new, _field, getattr(old, _field))
    def gett9db(self, result):
        _req=self._get_current_db()
        _t9list=t9editor.T9WordsList()
        if _req:
            for _item in _req.blocks:
                _blk=_item.block
                if _blk['type']==prototypeslg.T9USERDBBLOCK.WordsList_Type:
                    for _word in _blk['value']:
                        _t9list.append_word(_word['word'])
        result[t9editor.dict_key]=_t9list
        return result
    _buffer_data={
        '1': 0x7FA, '2': 0x7FA, '3': 0x7FA, '4': 0x7FA,
        '5': 0x7FA, '6': 0x7FA, '7': 0x7FA, '8': 0x7FA,
        '9': 0x7FA, '0': 0x800 }
    _t9keys=('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')
    def savet9db(self, result, _):
        _new_db=self.protocolclass.t9udbfile()
        try:
            _current_db=self._get_current_db()
            if _current_db:
                self._copy_fields(_current_db, _new_db)
        except:
            _current_db=None
        _t9words={}
        _t9list=result.get(t9editor.dict_key, t9editor.T9WordsList())
        _wordcount=0
        for _key in _t9list.keys:
            for _word in _t9list.get_words(_key):
                _t9words.setdefault(_key[0], []).append(_word)
                _wordcount+=1
        _new_db.word_count=_wordcount
        _total_free_size=0
        for _key in self._t9keys:
            _lst=_t9words.get(_key, [])
            if _lst:
                _val={ 'type': prototypeslg.T9USERDBBLOCK.WordsList_Type,
                       'value': [ { 'word': x } for x in _lst ] }
                _blk=prototypeslg.T9USERDBBLOCK(_val)
                _free_len=self._buffer_data[_key]-_blk.packetsize()
                # ugly hack!
                if _key!='1':
                    _free_len+=1
                _total_free_size+=_free_len
                _new_db.blocks.append(_val)
                _new_db.blocks.append({ 'type': prototypeslg.T9USERDBBLOCK.FreeBlock_Type,
                                        'value': _free_len })
            else:
                if _key!='1':
                    _new_db.blocks.append({ 'type': prototypeslg.T9USERDBBLOCK.A0_Type,
                                            'value': 0xA0 })
                _type=prototypeslg.T9USERDBBLOCK.FreeBlock_Type
                _new_db.blocks.append({ 'type': _type,
                                        'value': self._buffer_data[_key] })
                _total_free_size+=self._buffer_data[_key]
        _new_db.free_space=_total_free_size
        _buf=prototypes.buffer()
        _new_db.writetobuffer(_buf)
        self.writefile(self.protocolclass.T9USERDBFILENAME,
                       _buf.getvalue())
        # Need to reboot the phone to take effect
        result['rebootphone']=True
        return result

    # Misc Stuff----------------------------------------------------------------
    def get_firmware_version(self):
        # return the firmware version
        req=p_brew.firmwarerequest()
        res=self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
        return res.firmware

#-------------------------------------------------------------------------------
parentprofile=com_lgvx8300.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX8500'

    WALLPAPER_WIDTH=240
    WALLPAPER_HEIGHT=320
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

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))
    def GetImageOrigins(self):
        return self.imageorigins

    ringtoneorigins=('ringers', 'sounds', 'sounds(sd)',' music', 'music(sd)')
    excluded_ringtone_origins=('sounds', 'sounds(sd)', 'music', 'music(sd)')

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 240, 'height': 275, 'format': "JPEG"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets


    def __init__(self):
        parentprofile.__init__(self)

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
        ('playlist', 'read', 'OVERWRITE'),
        ('playlist', 'write', 'OVERWRITE'),
        ('t9_udb', 'write', 'OVERWRITE'),
        )
    if __debug__:
        _supportedsyncs+=(
        ('t9_udb', 'read', 'OVERWRITE'),
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
