### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungscha950.py 4784 2010-01-15 01:44:50Z djpham $

"""Communicate with the Samsung SCH-A950 Phone"""

# System Models
import calendar
import datetime
import sha
import time

import wx

# BitPim modules
import bpcalendar
import call_history
import common
import commport
import com_brew
import com_phone
import datetime
import fileinfo
import memo
import nameparser
import prototypes
import pubsub
import p_samsungscha950
import sqlite2_file
import sms
import helpids

class Phone(com_phone.Phone, com_brew.BrewProtocol):
    desc='SCH-A950'
    helpid=helpids.ID_PHONE_SAMSUNGSCHA950
    protocolclass=p_samsungscha950
    serialsname='scha950'

    ringtone_noring_range='range_tones_preloaded_el_15'
    ringtone_default_range='range_tones_preloaded_el_01'
    builtin_ringtones={
        'VZW Default Tone': ringtone_default_range,
        'Melody 1': 'range_tones_preloaded_el_02',
        'Melody 2': 'range_tones_preloaded_el_03',
        'Bell 1': 'range_tones_preloaded_el_04',
        'Bell 2': 'range_tones_preloaded_el_05',
        'Beep Once': 'range_tones_preloaded_el_06',
        'No Ring': ringtone_noring_range,
        }
    builtin_sounds={
        'Birthday': 'range_sound_preloaded_el_birthday',
        'Crowd Roar': 'range_sound_preloaded_el_crowed_roar',
        'Train': 'range_sound_preloaded_el_train',
        'Rainforest': 'range_sound_preloaded_el_rainforest',
        'Clapping': 'range_sound_preloaded_el_clapping',
        # same as ringtones ??
        'Sound Beep Once': 'range_sound_preloaded_el_beep_once',
        'Sound No Ring': 'range_sound_preloaded_el_no_rings',
        }
    builtin_wallpapers={
        'Wallpaper 1': 'range_f_wallpaper_preloaded_el_01',
        'Wallpaper 2': 'range_f_wallpaper_preloaded_el_02',
        'Wallpaper 3': 'range_f_wallpaper_preloaded_el_03',
        'Wallpaper 4': 'range_f_wallpaper_preloaded_el_04',
        'Wallpaper 5': 'range_f_wallpaper_preloaded_el_05',
        'Wallpaper 6': 'range_f_wallpaper_preloaded_el_06',
        'Wallpaper 7': 'range_f_wallpaper_preloaded_el_07',
        'Wallpaper 8': 'range_f_wallpaper_preloaded_el_08',
        'Wallpaper 9': 'range_f_wallpaper_preloaded_el_09',
        }
    builtin_groups={
        1: 'Business',
        2: 'Colleague',
        3: 'Family',
        4: 'Friends'
        }

    def __init__(self, logtarget, commport):
        "Calls all the constructors and sets initial modes"
        com_phone.Phone.__init__(self, logtarget, commport)
	com_brew.BrewProtocol.__init__(self)
	self.pbentryclass=PBEntry
	self.calendarclass=CalendarEntry
	# born to be in BREW mode!
        self.mode=self.MODEBREW

    # common stuff
    def get_esn(self):
        if hasattr(self, '_fs_path'):
            # we're debugging, just return something
            return '12345678'
        _req=self.protocolclass.ESN_req()
        _resp=self.sendbrewcommand(_req, self.protocolclass.ESN_resp)
        return '%08X'%_resp.esn

    def _time_now(self):
        return datetime.datetime.now().timetuple()[:5]

    def get_groups(self):
        _res={ 0: { 'name': 'No Group' } }
        try:
            _file_name=None
            _path_name=self.protocolclass.GROUP_INDEX_FILE_NAME
            for i in range(256):
                _name='%s%d'%(_path_name, i)
                if self.exists(_name):
                    _file_name=_name
                    break
            if not _file_name:
                return _res
            _index_file=self.readobject(_file_name,
                                        self.protocolclass.GroupIndexFile)
            for _entry in _index_file.items[1:]:
                if _entry.name:
                    _res[_entry.index]={ 'name': _entry.name }
                elif self.builtin_groups.get(_entry.index, None):
                    _res[_entry.index]={ 'name': self.builtin_groups[_entry.index] }
        except IndexError:
            pass
        except:
            if __debug__:
                raise
        return _res

    def _get_builtin_ringtone_index(self, idx, result):
        for _entry in self.builtin_ringtones:
            result[idx]= { 'name': _entry,
                           'origin': 'builtin',
                           }
            idx+=1
        for _entry in self.builtin_sounds:
            result[idx]={ 'name': _entry,
                          'origin': 'builtin',
                          }
            idx+=1
        return idx
    def _get_file_ringtone_index(self, idx, result,
                                 index_file_name, index_file_class,
                                 origin):
        try:
            _buf=prototypes.buffer(self.getfilecontents(index_file_name))
        except (com_brew.BrewNoSuchFileException,
                com_brew.BrewBadPathnameException,
                com_brew.BrewFileLockedException,
                com_brew.BrewAccessDeniedException):
            return idx
        except:
            if __debug__:
                raise
            return idx
        _index_file=index_file_class()
        _index_file.readfrombuffer(_buf)
        for _entry in _index_file.items:
            if _entry.pathname.startswith('/ff/'):
                _file_name=_entry.pathname[4:]
            else:
                _file_name=_entry.pathname
            result[idx]= { 'name': common.basename(_entry.pathname),
                           'filename': _file_name,
                           'origin': origin,
                           }
            idx+=1
        return idx
    def get_ringtone_index(self):
        _res={}
        _idx=self._get_builtin_ringtone_index(0, _res)
        _idx=self._get_file_ringtone_index(_idx, _res,
                                  self.protocolclass.RT_INDEX_FILE_NAME,
                                  self.protocolclass.RRingtoneIndexFile,
                                           'ringers')
        _idx=self._get_file_ringtone_index(_idx, _res,
                                           self.protocolclass.SND_INDEX_FILE_NAME,
                                           self.protocolclass.RSoundsIndexFile,
                                           'sounds')
        return _res
    def _get_builtin_wallpaper_index(self, idx, result):
        for _entry in self.builtin_wallpapers:
            result[idx]={ 'name': _entry,
                          'origin': 'builtin',
                          }
            idx+=1
        return idx
    def _get_file_wallpaper_index(self, idx, result):
        try:
            _buf=prototypes.buffer(self.getfilecontents(self.protocolclass.PIC_INDEX_FILE_NAME))
        except (com_brew.BrewNoSuchFileException,
                com_brew.BrewBadPathnameException,
                com_brew.BrewFileLockedException,
                com_brew.BrewAccessDeniedException):
            return idx
        except:
            if __debug__:
                raise
            return idx
        _index_file=self.protocolclass.RPictureIndexFile()
        _index_file.readfrombuffer(_buf)
        for _entry in _index_file.items[1:]:
            if _entry.pathname.startswith('/ff/'):
                _file_name=_entry.pathname[4:]
            else:
                _file_name=_entry.pathname
            result[idx]={ 'name': _entry.name,
                          'filename': _file_name,
                          'origin': 'images',
                          }
            idx+=1
        return idx
    def get_wallpaper_index(self):
        _res={}
        _idx=self._get_file_wallpaper_index(0, _res)
        return _res
    def _read_ringtone_range(self, fundamentals):
        _res={}
        try:
            _data=self.getfilecontents(self.protocolclass.PREF_DB_FILE_NAME)
            _db=sqlite2_file.DBFile(_data)
            for _row in _db.get_table_data('dynamic_range_els'):
                _res[_row[2]]=_row[0]
        except:
            if __debug__:
                raise
        fundamentals['ringtone-range']=_res
        
    def get_ringtone_range(self, name, fundamentals):
        if not name:
            # return No Rings
            return self.ringtone_default_range
        # check the builtin ringtones
        if self.builtin_ringtones.has_key(name):
            return self.builtin_ringtones[name]
        if self.builtin_sounds.has_key(name):
            return self.builtin_sounds[name]
        if not fundamentals.has_key('ringtone-range'):
            self._read_ringtone_range(fundamentals)
        _rt_range=fundamentals['ringtone-range']
        return _rt_range.get(name, None)

    def ringtone_name_from_range(self, range, fundamentals):
        # check for builtin ringtones
        for _key,_value in self.builtin_ringtones.items():
            if range==_value:
                return _key
        # check for builtin sounds
        for _key,_value in self.builtin_sounds.items():
            if range==_value:
                return _key
        # now check for the "custom" ones
        if not fundamentals.has_key('ringtone-range'):
            self._read_ringtone_range(fundamentals)
        for _key,_value in fundamentals['ringtone-range'].items():
            if _value==range:
                return _key

    def getfundamentals(self, results):
        """Gets information fundamental to interopating with the phone and UI.

        Currently this is:

          - 'uniqueserial'     a unique serial number representing the phone
          - 'groups'           the phonebook groups
          - 'wallpaper-index'  map index numbers to names
          - 'ringtone-index'   map index numbers to ringtone names

        This method is called before we read the phonebook data or before we
        write phonebook data.
        """

        # use a hash of ESN and other stuff (being paranoid)
        self.log("Retrieving fundamental phone information")
        self.log("Phone serial number")
        results['uniqueserial']=sha.new(self.get_esn()).hexdigest()
        results['groups']=self.get_groups()
        results['ringtone-index']=self.get_ringtone_index()
        results['wallpaper-index']=self.get_wallpaper_index()
        return results

    # Ringtone Stuff------------------------------------------------------------
    def _get_media_from_index(self, index_key, media_key,
                              fundamentals):
        _index=fundamentals.get(index_key, {})
        _media={}
        for _entry in _index.values():
            if _entry.has_key('filename') and _entry['filename']:
                try:
                    _media[_entry['name']]=self.getfilecontents(_entry['filename'],
                                                                True)
                except:
                    self.log('Failed to read file %s'%_entry['filename'])
        fundamentals[media_key]=_media
        return fundamentals

    def getringtones(self, fundamentals):
        # reading ringers & sounds files
        return self._get_media_from_index('ringtone-index', 'ringtone',
                                          fundamentals)

    def _get_del_new_list(self, index_key, media_key, merge, fundamentals,
                          ignored_origins=()):
        """Return a list of media being deleted and being added"""
        _index=fundamentals.get(index_key, {})
        _media=fundamentals.get(media_key, {})
        _index_file_list=[_entry['name'] for _,_entry in _index.items() \
                          if _entry.has_key('filename') and \
                             _entry.get('origin', None) not in ignored_origins]
        _bp_file_list=[_entry['name'] for _,_entry in _media.items() \
                       if _entry.get('origin', None) not in ignored_origins]
        if merge:
            # just add the new files, don't delete anything
            _del_list=[]
            _new_list=_bp_file_list
        else:
            # Delete specified files and add everything
            _del_list=[x for x in _index_file_list if x not in _bp_file_list]
            _new_list=_bp_file_list
        return _del_list, _new_list

    def _item_from_index(self, name, item_key, index_dict):
        for _key,_entry in index_dict.items():
            if _entry.get('name', None)==name:
                if item_key:
                    # return a field
                    return _entry.get(item_key, None)
                else:
                    # return the key
                    return _key

    def _del_files(self, index_key, _del_list, fundamentals):
        """Delete specified media files, need to be in OBEX mode"""
        _index=fundamentals.get(index_key, {})
        for _file in _del_list:
            _file_name=self._item_from_index(_file, 'filename', _index)
            if _file_name:
                try:
                    self.rmfile(_file_name)
                except Exception, e:
                    self.log('Failed to delete file %s: %s'%(_file_name, str(e)))

    def _replace_files(self, index_key, media_key, new_list, fundamentals):
        """Replace existing files with new contents using BREW"""
        _index=fundamentals.get(index_key, {})
        _media=fundamentals.get(media_key, {})
        for _file in new_list:
            _data=self._item_from_index(_file, 'data', _media)
            if not _data:
                self.log('Failed to write file %s due to no data'%_file)
                continue
            _file_name=self._item_from_index(_file, 'filename', _index)
            if _file_name:
                # existing file, check if the same one
                _stat=self.statfile(_file_name)
                if _stat and _stat['size']!=len(_data):
                    # different size, replace it
                    try:
                        self.writefile(_file_name, _data)
                    except:
                        self.log('Failed to write BREW file '+_file_name)
                        if __debug__:
                            raise
        
    def _add_files(self, index_key, media_key,
                   new_list, fundamentals):
        """Add new file using BREW"""
        _index=fundamentals.get(index_key, {})
        _media=fundamentals.get(media_key, {})
        _res=[]
        for _file in new_list:
            _data=self._item_from_index(_file, 'data', _media)
            if not _data:
                self.log('Failed to write file %s due to no data'%_file)
                continue
            if self._item_from_index(_file, None, _index) is None:
                # new file
                _origin=self._item_from_index(_file, 'origin', _media)
                if _origin=='ringers':
                    _path=self.protocolclass.RT_PATH
                elif _origin=='sounds':
                    _path=self.protocolclass.SND_PATH
                elif _origin=='images':
                    _path=self.protocolclass.PIC_PATH
                else:
                    selg.log('File %s has unknown origin, skip!'%_file)
                    continue
                _file_name=_path+'/'+_file
                try:
                    self.writefile(_file_name, _data)
                    _res.append(_file)
                except:
                    self.log('Failed to write file '+_file_name)
                    if __debug__:
                        raise
        return _res

    def _update_media_index(self, index_file_class, index_entry_class,
                            media_path, excluded_files,
                            index_file_name):
        # Update the index file
        _index_file=index_file_class()
        _filelists={}
        for _path in media_path:
            _filelists.update(self.listfiles(_path))
        _files=_filelists.keys()
        _files.sort()
        for _f in _files:
            _file_name=common.basename(_f)
            if _file_name in excluded_files:
                # do not include this one
                continue
            _entry=index_entry_class()
            _entry.name=_file_name
            _entry.pathname=_f
            _index_file.items.append(_entry)
        _buf=prototypes.buffer()
        _index_file.writetobuffer(_buf)
        self.writefile(index_file_name, _buf.getvalue())
##        file(common.basename(index_file_name), 'wb').write(_buf.getvalue())

    def saveringtones(self, fundamentals, merge):
        """Save ringtones to the phone"""
        self.log('Writing ringtones to the phone')
        try:
            _del_list, _new_list=self._get_del_new_list('ringtone-index',
                                                        'ringtone',
                                                        merge,
                                                        fundamentals)
            if __debug__:
                self.log('Delete list: '+','.join(_del_list))
                self.log('New list: '+','.join(_new_list))
            self._replace_files('ringtone-index', 'ringtone',
                                _new_list, fundamentals)
            self._del_files('ringtone-index',
                            _del_list, fundamentals)
            self._add_files('ringtone-index', 'ringtone',
                            _new_list, fundamentals)
            self._update_media_index(self.protocolclass.WRingtoneIndexFile,
                                     self.protocolclass.WRingtoneIndexEntry,
                                     [self.protocolclass.RT_PATH,
                                      self.protocolclass.RT_PATH2],
                                     self.protocolclass.RT_EXCLUDED_FILES,
                                     self.protocolclass.RT_INDEX_FILE_NAME)
            self._update_media_index(self.protocolclass.WSoundsIndexFile,
                                     self.protocolclass.WSoundsIndexEntry,
                                     [self.protocolclass.SND_PATH,
                                      self.protocolclass.SND_PATH2],
                                     self.protocolclass.SND_EXCLUDED_FILES,
                                     self.protocolclass.SND_INDEX_FILE_NAME)
            fundamentals['rebootphone']=True
        except:
            if __debug__:
                raise
        return fundamentals

    # Wallpaper stuff-----------------------------------------------------------
    def getwallpapers(self, fundamentals):
        # reading pictures & wallpapers
        return self._get_media_from_index('wallpaper-index', 'wallpapers',
                                          fundamentals)

    def savewallpapers(self, fundamentals, merge):
        # send wallpapers to the phone
        """Save ringtones to the phone"""
        self.log('Writing wallpapers to the phone')
        try:
            _del_list, _new_list=self._get_del_new_list('wallpaper-index',
                                                        'wallpapers',
                                                        merge,
                                                        fundamentals)
            if __debug__:
                self.log('Delete list: '+','.join(_del_list))
                self.log('New list: '+','.join(_new_list))
            self._replace_files('wallpaper-index', 'wallpapers',
                                _new_list, fundamentals)
            self._del_files('wallpaper-index',
                            _del_list, fundamentals)
            self._add_files('wallpaper-index', 'wallpapers',
                            _new_list, fundamentals)
            self._update_media_index(self.protocolclass.WPictureIndexFile,
                                     self.protocolclass.WPictureIndexEntry,
                                     [self.protocolclass.PIC_PATH,
                                      self.protocolclass.PIC_PATH2],
                                     self.protocolclass.PIC_EXCLUDED_FILES,
                                     self.protocolclass.PIC_INDEX_FILE_NAME)
            fundamentals['rebootphone']=True
        except:
            if __debug__:
                raise
        return fundamentals

    # Calendar stuff------------------------------------------------------------
    def _read_calendar_index(self):
        return self.readobject(self.protocolclass.CAL_INDEX_FILE_NAME,
                               self.protocolclass.CalIndexFile,
                               'Reading Calendar Index File')
    
    def getcalendar(self, fundamentals):
        self.log('Reading calendar')
        _cal_index=self._read_calendar_index()
        _res={}
        _buf=prototypes.buffer()
        for _cnt in range(_cal_index.numofevents):
            _cal_file_name='%s%04d'%(self.protocolclass.CAL_FILE_NAME_PREFIX,
                                     _cal_index.events[_cnt].index)
            _buf.reset(self.getfilecontents(_cal_file_name))
            _bpcal=self.calendarclass(self, _buf, fundamentals).getvalue()
            _res[_bpcal.id]=_bpcal
        fundamentals['calendar']=_res
        return fundamentals

    def _del_existing_cal_entries(self):
        self.log('Deleting existing calendar entries')
        _cal_index=self._read_calendar_index()
        for _idx in range(_cal_index.numofevents):
            _cal_file_name='%s%04d'%(self.protocolclass.CAL_FILE_NAME_PREFIX,
                                     _cal_index.events[_idx].index)
            try:
                self.rmfile(_cal_file_name)
            except:
                self.log('Failed to delete file: '+_cal_file_name)
        return _cal_index.next_index

    def _write_cal_entries(self, next_index, fundamentals):
        # write each and every calendar entries, each in a separate file
        _cal_dict=fundamentals.get('calendar', {})
        _idx=next_index
        _cnt=0
        for _key,_entry in _cal_dict.items():
            if _cnt>=self.protocolclass.CAL_MAX_EVENTS:
                # enough events already!
                break
            try:
                _cal_entry=self.calendarclass(self, _entry, fundamentals)
                _cal_file_name='%s%04d'%(self.protocolclass.CAL_FILE_NAME_PREFIX,
                                         _idx)
                self.writeobject(_cal_file_name, _cal_entry,
                                 'Writing Calendar Entry')
                _idx+=1
                _cnt+=1
            except:
                self.log('Failed to write calendar entry')
                if __debug__:
                    raise
        return _idx

    def _write_cal_index(self, next_index, fundamentals):
        _cal_index=self._read_calendar_index()
        # clear out the old entries
        for _idx in range(_cal_index.numofevents):
            _cal_index.events[_idx].index=0
        for _idx in range(_cal_index.numofactiveevents):
            _cal_index.activeevents[_idx].index=0
        # update with new info
        _old_next_index=_cal_index.next_index
        _num_entries=next_index-_old_next_index
        _cal_index.next_index=next_index
        _cal_index.numofevents=_num_entries
        _cal_index.numofactiveevents=_num_entries
        _cnt=0
        for _idx in range(_old_next_index, next_index):
            _cal_index.events[_cnt].index=_idx
            _cal_index.activeevents[_cnt].index=_idx
            _cnt+=1
        self.writeobject(self.protocolclass.CAL_INDEX_FILE_NAME,
                         _cal_index,
                         'Writing Calendar Index File')

    def savecalendar(self, fundamentals, merge):
        self.log("Sending calendar entries")
        _next_idx=self._del_existing_cal_entries()
        _next_idx=self._write_cal_entries(_next_idx, fundamentals)
        self._write_cal_index(_next_idx, fundamentals)
        # need to reboot the phone afterward
        fundamentals['rebootphone']=True
        return fundamentals

    # Memo/Notepad stuff--------------------------------------------------------
    def getmemo(self, fundamentals):
        self.log('Reading note pad items')
        _index_file=self._read_calendar_index()
        _res={}
        for _idx in range(_index_file.numofnotes):
            _file_name='%s%04d'%(self.protocolclass.NP_FILE_NAME_PREFIX,
                                 _index_file.notes[_idx].index)
            _note=self.readobject(_file_name,
                                  self.protocolclass.NotePadEntry)
            _memo=memo.MemoEntry()
            _memo.text=_note.text
            _memo.set_date_isostr('%04d%02d%02dT%02d%02d00'%_note.modified[:5])
            _res[_memo.id]=_memo
        fundamentals['memo']=_res
        return fundamentals

    def _del_existing_memo_entries(self):
        self.log('Deleting existing memo entries')
        _file_index=self._read_calendar_index()
        for _idx in range(_file_index.numofnotes):
            _file_name='%s%04d'%(self.protocolclass.NP_FILE_NAME_PREFIX,
                                 _file_index.notes[_idx].index)
            try:
                self.rmfile(_file_name)
            except:
                self.log('Failed to delete file: '+_file_name)
        return _file_index.next_index

    def _write_memo_entries(self, next_index, fundamentals):
        # write each and every memo entries, each in a separate file
        _memo_dict=fundamentals.get('memo', {})
        _idx=next_index
        _cnt=0
        for _key,_entry in _memo_dict.items():
            if _cnt>=self.protocolclass.NP_MAX_ENTRIES:
                # enough memo already!
                break
            try:
                _memo_entry=self.protocolclass.NotePadEntry()
                _text_len=min(self.protocolclass.NP_MAX_LEN,
                              len(_entry.text))
                _memo_entry.textlen=_text_len
                _memo_entry.text=_entry.text[:_text_len]
                _memo_entry.creation=self._time_now()
                _file_name='%s%04d'%(self.protocolclass.NP_FILE_NAME_PREFIX,
                                     _idx)
                self.writeobject(_file_name, _memo_entry,
                                 logtitle='Writing memo entry')
                _idx+=1
                _cnt+=1
            except:
                self.log('Failed to write memo endar entry')
                if __debug__:
                    raise
        return _idx

    def _write_memo_index(self, next_index, fundamentals):
        _file_index=self._read_calendar_index()
        # clear out the old entries
        for _idx in range(_file_index.numofnotes):
            _file_index.notes[_idx].index=0
        # update with new info
        _old_next_index=_file_index.next_index
        _num_entries=next_index-_old_next_index
        _file_index.next_index=next_index
        _file_index.numofnotes=_num_entries
        _cnt=0
        for _idx in range(_old_next_index, next_index):
            _file_index.notes[_cnt].index=_idx
            _cnt+=1
        self.writeobject(self.protocolclass.CAL_INDEX_FILE_NAME,
                         _file_index,
                         logtitle='Writing calendar/memo file index')
        
    def savememo(self, fundamentals, merge):
        self.log('Writing memo/notepad items')
        _next_index=self._del_existing_memo_entries()
        _next_index=self._write_memo_entries(_next_index, fundamentals)
        self._write_memo_index(_next_index, fundamentals)
        fundamentals['rebootphone']=True
        return fundamentals

    # Phone Detection-----------------------------------------------------------
    my_model='SCH-A950/DM'
    my_manufacturer='SAMSUNG'
    detected_model='A950'
    def is_mode_brew(self):
        # Borrowed from the VX4400
        req=self.protocolclass.memoryconfigrequest()
        respc=self.protocolclass.memoryconfigresponse
        for baud in 0, 38400, 115200:
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            try:
                self.sendbrewcommand(req, respc, callsetmode=False)
                return True
            except (com_phone.modeignoreerrortypes,
                    ValueError):
                pass
        return False
    def check_my_phone(self, res):
        # check if this is an A950
        try:
            _req=self.protocolclass.firmwarerequest()
            _resp=self.sendbrewcommand(_req, self.protocolclass.DefaultResponse)
            if _resp.data[31:35]==self.detected_model:
                # yup, this's it!
                res['model']=self.my_model
                res['manufacturer']=self.my_manufacturer
                res['esn']=self.get_esn()
        except:
            if __debug__:
                raise
    @classmethod
    def detectphone(_, coms, likely_ports, res, _module, _log):
        if not likely_ports:
            # cannot detect any likely ports
            return None
        for port in likely_ports:
            if not res.has_key(port):
                res[port]={ 'mode_modem': None, 'mode_brew': None,
                            'manufacturer': None, 'model': None,
                            'firmware_version': None, 'esn': None,
                            'firmwareresponse': None }
            try:
                if res[port]['mode_brew']==False or \
                   res[port]['model']:
                    # either phone is not in BREW, or a model has already
                    # been found, not much we can do now
                    continue
                p=_module.Phone(_log, commport.CommConnection(_log, port, timeout=1))
                if res[port]['mode_brew'] is None:
                    res[port]['mode_brew']=p.is_mode_brew()
                if res[port]['mode_brew']:
                    p.check_my_phone(res[port])
                p.comm.close()
            except:
                if __debug__:
                    raise
    
    #Phonebook stuff------------------------------------------------------------
    def _del_private_dicts(self, fundamentals):
        # delete the stuff that we created
        for _key in ('ringtone-range', 'wallpaper-range'):
            if fundamentals.has_key(_key):
                del fundamentals[_key]

    def _extract_entries(self, filename, res, fundamentals):
        try:
            _buf=prototypes.buffer(self.getfilecontents(filename))
            _rec_file=self.protocolclass.PBFileHeader()
            _rec_file.readfrombuffer(_buf)
            _entry=self.protocolclass.PBEntry()
            for _len in _rec_file.lens:
                if _len.itemlen:
                    _buf_ofs=_buf.offset
                    _entry.readfrombuffer(_buf)
                    _buf.offset=_buf_ofs+_len.itemlen
                    res[len(res)]=self.pbentryclass(self, _entry,
                                                    fundamentals).getvalue()
        except:
            self.log('Failed to read file: %s'%filename)
            if __debug__:
                raise

    def getphonebook(self, fundamentals):
        self.log('Reading phonebook contacts')
        _file_cnt=0
        _res={}
        while True:
            _file_name='%s%04d'%(self.protocolclass.PB_ENTRY_FILE_PREFIX,
                                 _file_cnt)
            if self.exists(_file_name):
                self._extract_entries(_file_name, _res, fundamentals)
                _file_cnt+=1
            else:
                break
        fundamentals['phonebook']=_res
        fundamentals['categories']=[x['name'] for _,x in \
                                    fundamentals.get('groups', {}).items()]
        self._del_private_dicts(fundamentals)
        return fundamentals

    def _get_wp_filename(self, wp, wp_index):
        # return the filename associated with this wallpaper
        for _,_entry in wp_index.items():
            if _entry.get('name', None)==wp:
                return _entry.get('filename', None)

    def _rescale_and_cache(self, wp, filename, idx,
                           fundamentals):
        # rescale the wp and add it to the cache dir
        try:
            _data=self.getfilecontents(filename, True)
            _tmpname=common.gettempfilename('tmp')
            file(_tmpname, 'wb').write(_data)
            _img=wx.Image(_tmpname)
            if not _img.Ok():
                self.log('Failed to understand image: '+filename)
                return
            _img.Rescale(self.protocolclass.PB_WP_CACHE_WIDTH,
                         self.protocolclass.PB_WP_CACHE_HEIGHT)
            _img.SaveFile(_tmpname, wx.BITMAP_TYPE_JPEG)
            _newfilename=self.protocolclass.PB_WP_CACHE_PATH+'/$'+filename.replace('/', '$')
            _data=file(_tmpname, 'rb').read()
            self.writefile(_newfilename, _data)
            return _newfilename
        except:
            if __debug__:
                self.log('Failed to add cache image: '+wp)
                raise

    def _add_wp_cache(self, wp, idx, fundamentals):
        # check to see if it already exists
        _wp_range=fundamentals.get('wallpaper-range', {})
        if _wp_range.has_key(wp):
            # already in there
            return
        # add this wallpaper into the cache dir
        _wp_index=fundamentals.get('wallpaper-index', {})
        # look for the file name
        _filename=self._get_wp_filename(wp, _wp_index)
        if not _filename:
            # couldn't find the filename
            return
        # copy the image file, rescale, and put it in the cache dir
        _newfilename=self._rescale_and_cache(wp, _filename, idx, fundamentals)
        if _newfilename:
            # rescale successful, update the dict
            _wp_range[wp]='/ff/'+_newfilename
            fundamentals['wallpaper-range']=_wp_range

    def get_wallpaper_range(self, wallpaper, fundamentals):
        # return the wallpaper cache name for the specific wallpaper
        return fundamentals.get('wallpaper-range', {}).get(wallpaper, None)

    def savephonebook(self, fundamentals):
        self.log('Writing phonebook contacts')
        self._read_ringtone_range(fundamentals)
        _pb_dict=fundamentals.get('phonebook', {})
        # alphabetize the list based on name
        _pb_list=[(nameparser.getfullname(_entry['names'][0]), _key) \
                  for _key,_entry in _pb_dict.items()]
        _pb_list.sort()
        _req=self.protocolclass.ss_pb_clear_req()
        _rp=self.sendbrewcommand(_req, self.protocolclass.ss_pb_clear_resp)
        if _rp.flg:
            self.log('Failed to clear phonebook')
            self._del_private_dicts(fundamentals)
            return fundamentals
        _req=self.protocolclass.ss_pb_write_req()
        _total_cnt=len(_pb_list)
        _cnt=1
        for _name,_key in _pb_list:
            try:
                _entry=_pb_dict[_key]
                # set up all the picture ID (wallpaper) images
                _wp=_entry.get('wallpapers', [{}])[0].get('wallpaper', None)
                if _wp:
                    self._add_wp_cache(_wp, _cnt, fundamentals)
                # setting up a new contact to send over
                _pbentry=self.pbentryclass(self, _entry, fundamentals)
                _req.entry=_pbentry.pb
                _cnt+=1
                self.progress(_cnt, _total_cnt,
                              'Writing entry" %s'%_req.entry.name)
                _resp=self.sendbrewcommand(_req,
                                           self.protocolclass.ss_pb_write_resp)
            except:
                self.log('Failed to write entry')
                if __debug__:
                    raise
        fundamentals['rebootphone']=True
        self._del_private_dicts(fundamentals)
        return fundamentals

    # Call History stuff--------------------------------------------------------
    def _get_ch_index(self):
        # read the index file and return the number of incoming, outgoing, and
        # missed calls
        try:
            _req=self.readobject(self.protocolclass.CL_INDEX_FILE,
                                 self.protocolclass.cl_index_file,
                                 logtitle='Reading Call Log Index File')
            return ([x.index for x in _req.incoming[:_req.incoming_count]],
                    [x.index for x in _req.outgoing[:_req.outgoing_count]],
                    [x.index for x in _req.missed[:_req.missed_count]])
        except com_brew.BrewNoSuchFileException:
            return ([], [], [])
        except:
            if __debug__:
                raise
            return ([], [], [])
    def _get_ch(self, call_list, folder, res):
        # read the call history files
        _req=self.protocolclass.cl_file()
        _buf=prototypes.buffer()
        for _idx in call_list:
            try:
                _buf.reset(self.getfilecontents(
                    '%s%02d'%(self.protocolclass.CL_PREFIX, _idx)))
                _req.readfrombuffer(_buf, 'Reading Call Log File')
                if _req.valid:
                    _entry=call_history.CallHistoryEntry()
                    _entry.folder=folder
                    _entry.number=_req.number
                    _entry.datetime=_req.datetime
                    if _req.duration:
                        _entry.duration=_req.duration
                    res[_entry.id]=_entry
            except com_brew.BrewNoSuchFileException:
                pass
            except:
                if __debug__:
                    raise

    def getcallhistory(self, fundamentals):
        # retrieve the call history data from the phone
        res={}
        _incoming_list, _outgoing_list, _missed_list=self._get_ch_index()
        self._get_ch(_incoming_list,
                     call_history.CallHistoryEntry.Folder_Incoming, res)
        self._get_ch(_outgoing_list,
                     call_history.CallHistoryEntry.Folder_Outgoing, res)
        self._get_ch(_missed_list,
                     call_history.CallHistoryEntry.Folder_Missed, res)
        fundamentals['call_history']=res

    # SMS Stuff----------------------------------------------------------------
    def _build_common_msg(self, entry, sms_hdr):
        entry.text=sms_hdr.body.msg
        entry.datetime=sms_hdr.body.datetime[:5]
        if sms_hdr.body.has_callback:
            entry.callback=sms_hdr.body.callback
        if sms_hdr.body.has_priority:
            if sms_hdr.body.priority:
                entry.priority=sms.SMSEntry.Priority_High
            else:
                entry.priority=sms.SMSEntry.Priority_Normal

    def _build_locked_field(self, entry, buf):
        _locked=self.protocolclass.UINT(sizeinbytes=4)
        _locked.readfrombuffer(buf)
        entry.locked=bool(_locked.getvalue())

    def _build_in_msg(self, sms_hdr, buf, res):
        _entry=sms.SMSEntry()
        _entry.folder=sms.SMSEntry.Folder_Inbox
        _entry._from=sms_hdr.body.addr0
        self._build_common_msg(_entry, sms_hdr)
        _entry.read=sms_hdr.body.msg_stat[0].status==self.protocolclass.SMS_STATUS_READ
        self._build_locked_field(_entry, buf)
        res[_entry.id]=_entry

    def _build_sent_msg(self, sms_hdr, buf, res):
        _entry=sms.SMSEntry()
        _entry.folder=sms.SMSEntry.Folder_Sent
        self._build_common_msg(_entry, sms_hdr)
        _confirmed_flg=False
        for _stat in sms_hdr.body.msg_stat:
            if _stat.status==self.protocolclass.SMS_STATUS_DELIVERED:
                _confirmed_flg=True
                break
        if _confirmed_flg:
            _datetime_list=self.protocolclass.sms_delivered_datetime()
            _datetime_list.readfrombuffer(buf, 'Reading Confirmed Datetime field')
        for _idx in range(10):
            if getattr(sms_hdr.body, 'addr_len%d'%_idx):
                if sms_hdr.body.msg_stat[_idx].status==self.protocolclass.SMS_STATUS_DELIVERED:
                    _entry.add_recipient(getattr(sms_hdr.body, 'addr%d'%_idx),
                                         True,
                                         _datetime_list.datetime[_idx].datetime[:5])
                else:
                    _entry.add_recipient(getattr(sms_hdr.body, 'addr%d'%_idx))
        self._build_locked_field(_entry, buf)
        res[_entry.id]=_entry

    def _build_draft_msg(self, sms_hdr, buf, res):
        _entry=sms.SMSEntry()
        _entry.folder=sms.SMSEntry.Folder_Saved
        self._build_common_msg(_entry, sms_hdr)
        self._build_locked_field(_entry, buf)
        for _idx in range(10):
            if getattr(sms_hdr.body, 'addr_len%d'%_idx):
                _entry.add_recipient(getattr(sms_hdr.body, 'addr%d'%_idx))
        res[_entry.id]=_entry

    def _read_sms(self, filename, res, fundamentals):
        _buf=prototypes.buffer(self.getfilecontents(filename))
        _sms=self.protocolclass.sms_header()
        _sms.readfrombuffer(_buf, 'Reading SMS File')
        if not _sms.is_txt_msg.value:
            # not a text message
            return
        if _sms.in_msg.value:
            self._build_in_msg(_sms, _buf, res)
        elif _sms.sent_msg.value:
            self._build_sent_msg(_sms, _buf, res)
        else:
            self._build_draft_msg(_sms, _buf, res)

    def getsms(self, fundamentals):
        res={}
        for _filename in self.listfiles(self.protocolclass.SMS_PATH):
            try:
                self._read_sms(_filename, res, fundamentals)
            except:
                self.log('Failed to read SMS File '+_filename)
                if __debug__:
                    raise
        fundamentals['sms']=res
        fundamentals['canned_msg']=[]
        return fundamentals

# CalendarEntry class-----------------------------------------------------------
class CalendarEntry(object):
    """Transient class to handle calendar data being sent to, retrieved from
    the phone.
    """
    # Repeat Constants
    REP_NONE=0
    REP_ONCE=0
    REP_DAILY=2
    REP_WEEKLY=5
    REP_MONTHLY=6
    REP_YEARLY=7
    # Alarm constants
    ALARM_ONTIME=0
    ALARM_5M=1
    ALARM_10M=2
    ALARM_15M=3
    ALARM_30M=4
    ALARM_1HR=5
    ALARM_3HR=6
    ALARM_5HR=7
    ALARM_1D=8
    # Alert
    ALERT_TONE=0
    ALERT_VIBRATE=1
    ALERT_LIGHT=2
    # Timezone
    TZ_EST=0
    TZ_EDT=1
    TZ_CST=2
    TZ_CDT=3
    TZ_MST=4
    TZ_MDT=5
    TZ_PST=6
    TZ_PDT=7
    TZ_AKST=8
    TZ_AKDT=9
    TZ_HAST=10
    TZ_HADT=11
    TZ_GMT=12
    def __init__(self, phone, value, fundamentals):
        self.phone=phone
        self.fundamentals=fundamentals
        self.cal=phone.protocolclass.CalEntry()
        if isinstance(value, bpcalendar.CalendarEntry):
            self._build(value)
        elif isinstance(value, prototypes.buffer):
            self.cal.readfrombuffer(value)
        else:
            raise TypeError('Expecting type bpcalendar.CalendarEntry or prototypes.buffer')

    def writetobuffer(self, buf, logtitle=None):
        self.cal.writetobuffer(buf, logtitle=logtitle)

    # building routines---------------------------------------------------------
    _build_repeat_dict={
        bpcalendar.RepeatEntry.daily: REP_DAILY,
        bpcalendar.RepeatEntry.weekly: REP_WEEKLY,
        bpcalendar.RepeatEntry.monthly: REP_MONTHLY,
        bpcalendar.RepeatEntry.yearly: REP_YEARLY,
        }
    _build_alarm_dict={
        0: ALARM_ONTIME,
        5: ALARM_5M,
        10: ALARM_10M,
        15: ALARM_15M,
        30: ALARM_30M,
        60: ALARM_1HR,
        180: ALARM_3HR,
        300: ALARM_5HR,
        1440: ALARM_1D,
        }
    _build_tz_dict={
        0: TZ_GMT,
        18000: TZ_EST,
        21600: TZ_CST,
        25200: TZ_MST,
        28800: TZ_PST,
        32400: TZ_AKST,
        36000: TZ_HAST,
        }
    def _build_duration(self, entry):
        return (datetime.datetime(*entry.end)-\
                datetime.datetime(*entry.start)).seconds
    def _build_repeat(self, entry):
        rep=entry.repeat
        if not rep:
            return self.REP_ONCE
        return self._build_repeat_dict.get(rep.repeat_type, self.REP_ONCE)
    def _build_alarm(self, entry):
        _keys=self._build_alarm_dict.keys()
        _keys.sort()
        _alarm=entry.alarm
        for k in _keys:
            if _alarm<=k:
                return self._build_alarm_dict[k]
        return self.ALARM_ONTIME
    def _build_alert(self, entry):
        if entry.vibrate:
            return self.ALERT_VIBRATE
        return self.ALERT_TONE
    _tz_code=None
    def _build_tz(self):
        if CalendarEntry._tz_code is None:
            CalendarEntry._tz_code=self._build_tz_dict.get(time.timezone,
                                                           self.TZ_EST)
            if time.localtime()[-1]==1:
                # daylight saving time
                CalendarEntry._tz_code+=1
        return CalendarEntry._tz_code

    def _build(self, entry):
        # populate this object with data from BitPim
        self.cal.titlelen=len(entry.desc_loc)
        self.cal.title=entry.desc_loc
        self.cal.start=entry.start
        self.cal.exptime=entry.end[3:5]
        self.cal.repeat=self._build_repeat(entry)
        self.cal.alarm=self._build_alarm(entry)
        self.cal.alert=self._build_alert(entry)
        self.cal.duration=self._build_duration(entry)
        self.cal.timezone=self._build_tz()
        _now=self.phone._time_now()
        self.cal.creationtime=_now
        self.cal.modifiedtime=_now
        _ringtone=self.phone.get_ringtone_range(entry.ringtone,
                                                self.fundamentals)
        self.cal.ringtonelen=len(_ringtone)
        self.cal.ringtone=_ringtone

    # Extracting routine--------------------------------------------------------
    def _extract_end(self):
        return (datetime.datetime(*self.cal.start)+\
                datetime.timedelta(seconds=self.cal.duration)).timetuple()[:5]
    def _extract_alarm(self):
        for _value,_code in self._build_alarm_dict.items():
            if self.cal.alarm==_code:
                return _value
    def _extract_repeat(self):
        if self.cal.repeat==self.REP_ONCE:
            return None
        _rep_type=None
        for _type, _code in self._build_repeat_dict.items():
            if self.cal.repeat==_code:
                _rep_type=_type
                break
        if not _rep_type:
            return None
        _rep=bpcalendar.RepeatEntry(_rep_type)
        if _rep_type==_rep.daily:
            _rep.interval=1
        elif _rep_type==_rep.weekly:
            _rep.interval=1
        elif _rep_type==_rep.monthly:
            _rep.interval2=1
            _rep.dow=0
        return _rep

    def getvalue(self):
        # return a BitPim calendar entry equivalence
        _entry=bpcalendar.CalendarEntry()
        _entry.desc_loc=self.cal.title
        _entry.start=self.cal.start
        _entry.end=self._extract_end()
        _entry.alarm=self._extract_alarm()
        _entry.repeat=self._extract_repeat()
        if _entry.repeat:
            # forever repeat event
            _entry.end=_entry.no_end_date+_entry.end[3:]
        _entry.ringtone=self.phone.ringtone_name_from_range(self.cal.ringtone,
                                                            self.fundamentals)
        _entry.vibrate=self.cal.alert==self.ALERT_VIBRATE
        return _entry

# PBEntry class-----------------------------------------------------------------
class PBEntry(object):

    def __init__(self, phone, data, fundamentals):
        self.phone=phone
        self.fundamentals=fundamentals
        if isinstance(data, phone.protocolclass.PBEntry):
            self.pb=data
        elif isinstance(data, dict):
            # assume it's a phonebook dict
            self.pb=phone.protocolclass.ss_pb_entry()
            self._build(data)
        else:
            raise TypeError('Should be PBEntry or phone dict')

    def writetobuffer(self, buf, logtitle=None):
        self.pb.writetobuffer(buf, logtitle=logtitle)

    # Building a phonebook rec from a bp phone dict-----------------------------
    _pb_type_dict={
        'home': 'home',
        'office': 'work',
        'cell': 'cell',
        'fax': 'fax',
        }
    def _build_number(self, number, ringtone, primary):
        # build a number rec
        _num_type=self._pb_type_dict.get(number['type'], None)
        if not _num_type:
            # we don's support this type
            return
        # check for cell2
        if _num_type=='cell' and self.pb.cell.number:
            _num_type='cell2'
        # build a number entry
        _entry=self.phone.protocolclass.ss_number_entry()
        _entry.number=number['number']
        _sd=number.get('speeddial', None)
        if ringtone:
            _rt=self.phone.get_ringtone_range(ringtone, self.fundamentals)
        else:
            _rt=None
        if _sd is not None:
            _entry.speeddial=_sd
        if _rt is not None:
            _entry.ringtone=_rt
        if primary:
            _entry.primary=1
        # add it to the contact
        setattr(self.pb, _num_type, _entry)

    def _build_email(self, emails):
        # build an email rec
        if len(emails) and emails[0].get('email', None):
            # at least 1 email
            self.pb.email=emails[0]['email']
        if len(emails)>1 and emails[1].get('email', None):
            # 2 or more emails
            self.pb.email2=emails[1]['email']

    def _build_group(self, cat):
        # set the group if specified
        if not cat:
            return
        _cat_list=self.fundamentals.get('groups', {})
        for _key,_cat in _cat_list.items():
            if _key and _cat.get('name', None)==cat:
                self.pb.group=_key
                break

    def _build_wallpaper(self, wallpaper):
        # set the wallpaper if specified
        if not wallpaper:
            return
        _wp=self.phone.get_wallpaper_range(wallpaper, self.fundamentals)
        if _wp:
            self.pb.wallpaper=_wp
        
    def _build(self, entry):
        # Build a phone dict base on the phone data
        self.pb.name=nameparser.getfullname(entry['names'][0])
        # global ringtone
        _ringtone=entry.get('ringtones', [{}])[0].get('ringtone', None)
        # build the numbers
        _primary=True   # the first number is the primary one
        for _number in entry.get('numbers', []):
            self._build_number(_number, _ringtone, _primary)
            _primary=False
        # build the email
        self._build_email(entry.get('emails', []))
        # group
        self._build_group(entry.get('categories', [{}])[0].get('category', None))
        # wallpaper
        self._build_wallpaper(entry.get('wallpapers', [{}])[0].get('wallpaper', None))

    # Extracting data from the phone--------------------------------------------
    def _extract_emails(self, entry, p_class):
        # extract emails
        if self.pb.has_email:
            entry['emails']=[{ 'email': self.pb.email }]
        if self.pb.has_email2:
            entry.setdefault('emails', []).append({ 'email': self.pb.email2 })
    _number_type_dict={
        'cell': (Phone.protocolclass.PB_FLG_CELL, 'cell'),
        'home': (Phone.protocolclass.PB_FLG_HOME, 'home'),
        'work': (Phone.protocolclass.PB_FLG_WORK, 'office'),
        'fax': (Phone.protocolclass.PB_FLG_FAX, 'fax'),
        'cell2': (Phone.protocolclass.PB_FLG_CELL2, 'cell'),
        }
    def _extract_numbers(self, entry, p_class):
        # extract phone numbers
        entry['numbers']=[]
        for _key,_info_list in self._number_type_dict.items():
            if self.pb.info&_info_list[0]:
                _num_entry=getattr(self.pb, _key)
                _number={ 'number': _num_entry.number,
                          'type': _info_list[1] }
                if _num_entry.has_speeddial:
                    _number['speeddial']=_num_entry.speeddial
                if _num_entry.has_ringtone and \
                   not entry.has_key('ringtones'):
                    _ringtone=self.phone.ringtone_name_from_range(
                        _num_entry.ringtone, self.fundamentals)
                    if _ringtone:
                        entry['ringtones']=[{ 'ringtone': _ringtone,
                                              'use': 'call' }]
                if _num_entry.is_primary:
                    # this is the primary number, insert to the beginning
                    entry['numbers']=[_number]+entry['numbers']
                else:
                    entry['numbers'].append(_number)
    def _extract_group(self, entry, p_class):
        if not self.pb.has_group:
            # no group specified
            return
        _groups=self.fundamentals.get('groups', {})
        if _groups.has_key(self.pb.group):
            entry['categories']=[{ 'category': _groups[self.pb.group]['name'] }]
    def _extract_wallpaper(self, entry, p_class):
        if not self.pb.has_wallpaper:
            return
        _idx=self.pb.wallpaper.rfind('$')+1
        _wp=self.pb.wallpaper[_idx:]
        entry['wallpapers']=[{ 'wallpaper': _wp,
                               'use': 'call' }]
    def getvalue(self):
        _entry={}
        _p_class=self.phone.protocolclass
        _entry['names']=[{ 'full': self.pb.name }]
        self._extract_emails(_entry, _p_class)
        self._extract_numbers(_entry, _p_class)
        self._extract_group(_entry, _p_class)
        self._extract_wallpaper(_entry, _p_class)
        return _entry
        
#-------------------------------------------------------------------------------
parentprofile=com_phone.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    WALLPAPER_WIDTH=176
    WALLPAPER_HEIGHT=220
    # 128x96: outside LCD
    autodetect_delay=3
    usbids=( ( 0x04e8, 0x6640, 2),)
    deviceclasses=("serial",)
    BP_Calendar_Version=3
    # For phone detection
    phone_manufacturer=Phone.my_manufacturer
    phone_model=Phone.my_model
    # arbitrary ringtone file size limit
    RINGTONE_LIMITS= {
        'MAXSIZE': 100000
    }
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ._:"
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ._:"

    def __init__(self):
        parentprofile.__init__(self)

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('ringtone', 'read', None),   # all ringtone reading
        ('ringtone', 'write', 'MERGE'),
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', None),
        ('memo', 'read', None),     # all memo list reading DJP
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing DJP
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None),     # all SMS list reading DJP
        )

    def QueryAudio(self, origin, currentextension, afi):
        _max_size=self.RINGTONE_LIMITS['MAXSIZE']
        setattr(afi, 'MAXSIZE', _max_size)
        # we don't modify any of these
        if afi.format in ("MIDI", "QCP", "PMD"):
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

    # all dumped in "images"
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 186, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 128, 'height': 96, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))
    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets

    def convertphonebooktophone(self, helper, data):
        return data

    field_color_data={
        'phonebook': {
            'name': {
                'first': 1, 'middle': 1, 'last': 1, 'full': 1,
                'nickname': 0, 'details': 1 },
            'number': {
                'type': 5, 'speeddial': 5, 'number': 5,
                'details': 5,
                'ringtone': False, 'wallpaper': False },
            'email': 2,
            'email_details': {
                'emailspeeddial': False, 'emailringtone': False,
                'emailwallpaper': False },
            'address': {
                'type': 0, 'company': 0, 'street': 0, 'street2': 0,
                'city': 0, 'state': 0, 'postalcode': 0, 'country': 0,
                'details': 0 },
            'url': 0,
            'memo': 0,
            'category': 1,
            'wallpaper': 1,
            'ringtone': 1,
            'storage': 0,
            },
        'calendar': {
            'description': True, 'location': True, 'allday': False,
            'start': True, 'end': True, 'priority': False,
            'alarm': True, 'vibrate': True,
            'repeat': True,
            'memo': False,
            'category': False,
            'wallpaper': False,
            'ringtone': True,
            },
        'memo': {
            'subject': False,
            'date': False,
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
