### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
### Copyright (C) 2006 Stephen Wood <saw@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungscha870.py 4569 2008-01-15 01:03:05Z djpham $

"""Communicate with the Samsung SCH-A870 Phone"""

# System Models

# BitPim modules
import bpcalendar
import common
import helpids
import com_samsungscha950 as com_a950
import p_samsungscha950 as p_a950
import p_samsungscha870 as p_a870
import prototypes

parentphone=com_a950.Phone
class Phone(parentphone):
    desc='SCH-A870'
    helpid=helpids.ID_PHONE_SAMSUNGSCHA870
    protocolclass=p_a870
    serialsname='scha870'

    # Detection stuff
    my_model='SCH-A870/187'
    my_manufacturer='SAMSUNG'
    detected_model='A870'

    ringtone_noring_range='range_tones_preloaded_el_15'
    ringtone_default_range='range_tones_preloaded_el_01'
    builtin_ringtones={
        'VZW Default Tone': 0x52,
        'Melody 1': 0x56,
        'Melody 2': 0x57,
        'Melody 3': 0x58,
        'Melody 4': 0x59,
        'Melody 5': 0x5A,
        'Melody 6': 0x5B,
        'Bell 1': 0x53,
        'Bell 2': 0x54,
        'Bell 3': 0x55,
        'Beep Once': 0x93,
        'No Ring': 0xC2,
        'Default': None,
        }
    builtin_sounds={
        'Clapping': 0x5C,
        'Crowd': 0x5D,
        'Happy Birthday': 0x5E,
        'Rain Forest': 0x5F,
        'Train': 0x60,
        # same as ringtones ??
        }
    builtin_wallpapers={
        'No Picture': None,
        }

    def __init__(self, logtarget, commport):
        "Calls all the constructors and sets initial modes"
        parentphone.__init__(self, logtarget, commport)
        global PBEntry, CalendarEntry
        self.pbentryclass=PBEntry
        self.calendarclass=CalendarEntry

    def getfilecontents(self, filename, use_cache=False):
        if filename and filename[0]!='/':
            return parentphone.getfilecontents(self, '/'+filename, use_cache)
        return parentphone.getfilecontents(self, filename, use_cache)

    def get_groups(self):
        _res={}
        _buf=prototypes.buffer(self.getfilecontents(self.protocolclass.GROUP_INDEX_FILE_NAME))
        _index_file=self.protocolclass.GroupIndexFile()
        _index_file.readfrombuffer(_buf)
        for _entry in _index_file.items:
            if _entry.name:
                _res[_entry.index-1]={ 'name': _entry.name }
        return _res

    def _get_dir_index(self, idx, result, pathname, origin, excludenames=()):
        # build the index list by listing contents of the specified dir
        for _path in self.listfiles(pathname):
            _file=common.basename(_path)
            if _file in excludenames:
                continue
            result[idx]={ 'name': _file,
                          'filename': _path,
                          'origin': origin,
                          }
            idx+=1
        return idx

    def get_ringtone_index(self):
        _res={}
        _idx=self._get_builtin_ringtone_index(0, _res)
        _idx=self._get_dir_index(_idx, _res,
                                 self.protocolclass.RT_PATH, 'ringers',
                                 self.protocolclass.RT_EXCLUDED_FILES)
        _idx=self._get_dir_index(_idx, _res,
                                 self.protocolclass.SND_PATH, 'sounds',
                                 self.protocolclass.SND_EXCLUDED_FILES)
        return _res

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
        _index_file=self.protocolclass.PictureIndexFile()
        _index_file.readfrombuffer(_buf)
        for _entry in _index_file.items:
            result[idx]={ 'name': _entry.name,
                          'filename': _entry.pathname,
                          'origin': 'images',
                          }
            idx+=1
        return idx

    def get_wallpaper_index(self):
        _res={}
        _idx=self._get_builtin_wallpaper_index(0, _res)
        _idx=self._get_file_wallpaper_index(_idx, _res)
        return _res

    def _get_del_new_list(self, index_key, media_key, merge, fundamentals,
                          origins):
        """Return a list of media being deleted and being added"""
        _index=fundamentals.get(index_key, {})
        _media=fundamentals.get(media_key, {})
        _index_file_list=[_entry['name'] for _entry in _index.values() \
                          if _entry.has_key('filename') and \
                          _entry.get('origin', None) in origins ]
        _bp_file_list=[_entry['name'] for _entry in _media.values() \
                       if _entry.get('origin', None) in origins ]
        if merge:
            # just add the new files, don't delete anything
            _del_list=[]
            _new_list=_bp_file_list
        else:
            # Delete specified files and add everything
            _del_list=[x for x in _index_file_list if x not in _bp_file_list]
            _new_list=_bp_file_list
        return _del_list, _new_list

    def saveringtones(self, fundamentals, merge):
        """Save ringtones to the phone"""
        self.log('Writing ringtones to the phone')
        try:
            _del_list, _new_list=self._get_del_new_list('ringtone-index',
                                                        'ringtone',
                                                        merge,
                                                        fundamentals,
                                                        frozenset(('ringers', 'sounds')))
            if __debug__:
                self.log('Delete list: '+','.join(_del_list))
                self.log('New list: '+','.join(_new_list))
            self._replace_files('ringtone-index', 'ringtone',
                                _new_list, fundamentals)
            self._add_files('ringtone-index', 'ringtone',
                            _new_list, fundamentals)
            fundamentals['rebootphone']=True
        except:
            if __debug__:
                raise
        return fundamentals

    def _add_files(self, index_key, media_key,
                   new_list, fundamentals):
        """Add new file using BEW"""
        _index=fundamentals.get(index_key, {})
        _media=fundamentals.get(media_key, {})
        _files_added=[]
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
                    _files_added.append({ 'filename': _file,
                                          'filesize': len(_data) })
                except:
                    self.log('Failed to write file '+_file_name)
                    if __debug__:
                        raise
        return _files_added

    def _update_wp_index_file(self, filelist):
        # update the wp/picture index file with list of new files
        if not filelist:
            # no new files to update, bail
            return
        _index_file=self.protocolclass.PictureIndexFile()
        try:
            # read existing index items ...
            _data=self.getfilecontents(self.protocolclass.PIC_INDEX_FILE_NAME)
            if _data:
                _index_file.readfrombuffer(prototypes.buffer(_data))
        except (com_brew.BrewNoSuchFileException,
                com_brew.BrewBadPathnameException,
                com_brew.BrewFileLockedException,
                com_brew.BrewAccessDeniedException):
            pass
        # and append the new files
        for _fileitem in filelist:
            _index_file.items.append(self.protocolclass.PictureIndexEntry(**_fileitem))
        # and write out the new index file
        _buffer=prototypes.buffer()
        _index_file.writetobuffer(_buffer)
        self.writefile(self.protocolclass.PIC_INDEX_FILE_NAME,
                       _buffer.getvalue())

    def savewallpapers(self, fundamentals, merge):
        # send wallpapers to the phone
        """Save ringtones to the phone"""
        self.log('Writing wallpapers to the phone')
        try:
            _del_list, _new_list=self._get_del_new_list('wallpaper-index',
                                                        'wallpapers',
                                                        merge,
                                                        fundamentals,
                                                        frozenset(['images']))
            if __debug__:
                self.log('Delete list: '+','.join(_del_list))
                self.log('New list: '+','.join(_new_list))
            self._replace_files('wallpaper-index', 'wallpapers',
                                _new_list, fundamentals)
            _files_added=self._add_files('wallpaper-index', 'wallpapers',
                                         _new_list, fundamentals)
            self._update_wp_index_file(_files_added)
            fundamentals['rebootphone']=True
        except:
            if __debug__:
                raise
        return fundamentals

    def _read_ringtone_range(self, fundamentals):
        pass
    def _add_wp_cache(self, wp, idx, fundamentals):
        # check to see if it already exists
        pass

# PBEntry class-----------------------------------------------------------------
parentpbentry=com_a950.PBEntry
class PBEntry(parentpbentry):

    # Building a phonebook rec from a bp phone dict-----------------------------
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
        if _sd is not None:
            _entry.speeddial=_sd
        if primary:
            _entry.primary=1
        # add it to the contact
        setattr(self.pb, _num_type, _entry)

    def _build_wallpaper(self, wallpaper):
        # set the wallpaper if specified
        if not wallpaper:
            return
        for _rt in self.fundamentals.get('wallpaper-index', {}).values():
            if _rt.get('name', None)==wallpaper and \
               _rt.get('filename', None):
                self.pb.wallpaper='%(name)s|%(pathname)s'% {
                    'name': _rt['name'],
                    'pathname': _rt['filename'] }
                break

    def _build_ringtone(self, ringtone):
        # set the ringtone if specified
        if not ringtone:
            self.pb.ringtone='Default'
            return
        for _wp in self.fundamentals.get('ringtone-index', {}).values():
            if _wp.get('name', None)==ringtone:
                if _wp.get('filename', None):
                    self.pb.ringtone=_wp['filename'] if _wp['filename'][0]=='/' \
                                      else '/'+_wp['filename']
                elif _wp.get('origin', None)=='builtin':
                    self.pb.ringtone=_wp['name']
                break
        
    def _build(self, entry):
        # Build a phone dict base on the phone data
        super(PBEntry, self)._build(entry)
        self._build_ringtone(entry.get('ringtones', [{}])[0].get('ringtone', None))

    # Extracting data from the phone--------------------------------------------
    def _extract_wallpaper(self, entry, p_class):
        if self.pb.info&p_class.PB_FLG_WP and \
           self.pb.wallpaper:
            entry['wallpapers']=[{ 'wallpaper': self.pb.wallpaper.partition('|')[0],
                                   'use': 'call' }]
    def _extract_ringtone(self, entry, p_class):
        if self.pb.info&p_class.PB_FLG_CRINGTONE and \
           self.pb.ringtone:
            entry['ringtones']=[{ 'ringtone': common.basename(self.pb.ringtone),
                                  'use': 'call' }]
    def getvalue(self):
        _entry=super(PBEntry, self).getvalue()
        self._extract_ringtone(_entry, self.phone.protocolclass)
        return _entry

# CalendarEntry class-----------------------------------------------------------
calendarentryparent=com_a950.CalendarEntry
class CalendarEntry(calendarentryparent):
    """Transient class to handle calendar data being sent to, retrieved from
    the phone.
    """
    # Extracting routine--------------------------------------------------------
    def _extract_ringtone(self):
        # extract the builtin ringtone value, if possible
        for _rt_name, _rt_code in self.phone.builtin_ringtones.items():
            if _rt_code==self.cal.ringtoneindex:
                return _rt_name
        for _rt_name, _rt_code in self.phone.builtin_sounds.items():
            if _rt_code==self.cal.ringtoneindex:
                return _rt_name

    def getvalue(self):
        # return a BitPim calendar entry equivalence
        _entry=bpcalendar.CalendarEntry()
        _entry.desc_loc=self.cal.title
        _entry.start=self.cal.start
        _entry.end=self._extract_end()
        _entry.alarm=self._extract_alarm()
        _entry.ringtone=self._extract_ringtone()
        _entry.vibrate=self.cal.alert==self.ALERT_VIBRATE
        return _entry

    # building routines---------------------------------------------------------
    def _build_ringtone(self, entry):
        _rt_name=entry.ringtone
        if self.phone.builtin_ringtones.get(_rt_name, None):
            return self.phone.builtin_ringtones[_rt_name]
        elif self.phone.builtin_sounds.get(_rt_name, None):
            return self.phone.builtin_sounds[_rt_name]
        else:
            return 0

    def _build(self, entry):
        # populate this object with data from BitPim
        self.cal.titlelen=len(entry.desc_loc)
        self.cal.title=entry.desc_loc
        self.cal.start=entry.start
        self.cal.exptime=entry.end[3:5]
        self.cal.alarm=self._build_alarm(entry)
        self.cal.alert=self._build_alert(entry)
        self.cal.duration=self._build_duration(entry)
        self.cal.ringtoneindex=self._build_ringtone(entry)

#-------------------------------------------------------------------------------
parentprofile=com_a950.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    # main LCD resolution, (external LCD is 96x96)
    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=160
    # For phone detection
    phone_manufacturer=Phone.my_manufacturer
    phone_model=Phone.my_model
    autodetect_delay=5
    # "Warning" media size limit
    RINGTONE_LIMITS= {
        'MAXSIZE': 290000
    }

    # fill in the list of ringtone/sound origins on your phone
    ringtoneorigins=('ringers', 'sounds')
    # ringtone origins that are not available for the contact assignment
    excluded_ringtone_origins=()

    # all dumped in "images"
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 128, 'height': 128, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 96, 'height': 84, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 128, 'height': 160, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 96, 'height': 84, 'format': "JPEG"}))
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
        ('wallpaper', 'write', 'MERGE'),
        ('memo', 'read', None),     # all memo list reading DJP
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing DJP
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None),     # all SMS list reading DJP
        )
