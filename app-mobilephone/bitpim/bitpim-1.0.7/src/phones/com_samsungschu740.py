### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungschu740.py 4777 2010-01-07 03:24:27Z djpham $

"""Communicate with the Samsung SCH-U740 Phone"""

# System Modules
import re
import wx

# BitPim Modules

import call_history
import common
import com_brew
import com_samsungscha950 as scha950
import helpids
import prototypes
import p_samsungschu740 as p_schu740

parentphone=scha950.Phone
class Phone(parentphone):
    desc='SCH-U740'
    helpid=helpids.ID_PHONE_SAMSUNGSCHU740
    protocolclass=p_schu740
    serialsname='schu740'

    ringtone_noring_range='range_tones_preloaded_el_13'
    ringtone_default_range='range_tones_preloaded_el_01'
    builtin_ringtones={
        'VZW Default Tone': ringtone_default_range,
        'Bell 1': 'range_tones_preloaded_el_02',
        'Bell 2': 'range_tones_preloaded_el_03',
        'Bell 3': 'range_tones_preloaded_el_04',
        'Melody 1': 'range_tones_preloaded_el_05',
        'Melody 2': 'range_tones_preloaded_el_06',
        'Melody 3': 'range_tones_preloaded_el_07',
        'Melody 4': 'range_tones_preloaded_el_08',
        'Melody 5': 'range_tones_preloaded_el_09',
        'Melody 6': 'range_tones_preloaded_el_10',
        'Beep Once': 'range_tones_preloaded_el_11',
        'No Ring': ringtone_noring_range,
        }
    # can we use Sounds as ringtones?
    builtin_sounds={}
##    builtin_sounds={
##        'Birthday': 'range_sound_preloaded_el_birthday',
##        'Crowd Roar': 'range_sound_preloaded_el_crowed_roar',
##        'Train': 'range_sound_preloaded_el_train',
##        'Rainforest': 'range_sound_preloaded_el_rainforest',
##        'Clapping': 'range_sound_preloaded_el_clapping',
##        # same as ringtones ??
##        'Sound Beep Once': 'range_sound_preloaded_el_beep_once',
##        'Sound No Ring': 'range_sound_preloaded_el_no_rings',
##        }
    builtin_wallpapers={
        'Preloaded1': 'range_f_wallpaper_preloaded_el_01',
        'Preloaded2': 'range_f_wallpaper_preloaded_el_02',
        'Preloaded3': 'range_f_wallpaper_preloaded_el_03',
        'Preloaded4': 'range_f_wallpaper_preloaded_el_04',
        'Preloaded5': 'range_f_wallpaper_preloaded_el_05',
        'Preloaded6': 'range_f_wallpaper_preloaded_el_06',
        'Preloaded7': 'range_f_wallpaper_preloaded_el_07',
        'Preloaded8': 'range_f_wallpaper_preloaded_el_08',
        }
    builtin_groups={
        1: 'Business',
        2: 'Colleague',
        3: 'Family',
        4: 'Friends'
        }

    my_model='SCH-U740/DM'
    my_manufacturer='SAMSUNG'
    detected_model='u740'

    def __init__(self, logtarget, commport):
        "Calls all the constructors and sets initial modes"
        parentphone.__init__(self, logtarget, commport)
        global PBEntry
        self.pbentryclass=PBEntry

    def _get_file_wallpaper_index(self, idx, result,
                                  indexfilename, origin):
        try:
            _buf=prototypes.buffer(self.getfilecontents(indexfilename))
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
        for _entry in _index_file.items:
            if _entry.pictype==self.protocolclass.PIC_TYPE_USERS:
                if _entry.pathname.startswith('/ff/'):
                    _file_name=_entry.pathname[4:]
                else:
                    _file_name=_entry.pathname
                result[idx]={ 'name': common.basename(_entry.pathname),
                              'filename': _file_name,
                              'origin': origin,
                              }
                idx+=1
        return idx
    def get_wallpaper_index(self):
        _res={}
        _idx=self._get_builtin_wallpaper_index(0, _res)
        _idx=self._get_file_wallpaper_index(_idx, _res,
                                            self.protocolclass.PIC_INDEX_FILE_NAME,
                                            'images')
        _idx=self._get_file_wallpaper_index(_idx, _res,
                                            self.protocolclass.VIDEO_INDEX_FILE_NAME,
                                            'video')
        return _res

    # Ringtone stuff
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
            self._add_files('ringtone-index', 'ringtone',
                            _new_list, fundamentals)
            self._update_media_index(self.protocolclass.WRingtoneIndexFile,
                                     self.protocolclass.WRingtoneIndexEntry,
                                     [self.protocolclass.RT_PATH],
                                     self.protocolclass.RT_EXCLUDED_FILES,
                                     self.protocolclass.RT_INDEX_FILE_NAME)
            self._update_media_index(self.protocolclass.WSoundsIndexFile,
                                     self.protocolclass.WSoundsIndexEntry,
                                     [self.protocolclass.SND_PATH],
                                     self.protocolclass.SND_EXCLUDED_FILES,
                                     self.protocolclass.SND_INDEX_FILE_NAME)
            fundamentals['rebootphone']=True
        except:
            if __debug__:
                raise
        return fundamentals

    # Wallpaper stuff-----------------------------------------------------------
    def savewallpapers(self, fundamentals, merge):
        # send wallpapers to the phone
        """Save ringtones to the phone"""
        self.log('Writing wallpapers to the phone')
        try:
            _del_list, _new_list=self._get_del_new_list('wallpaper-index',
                                                        'wallpapers',
                                                        merge,
                                                        fundamentals,
                                                        ('video',))
            if __debug__:
                self.log('Delete list: '+','.join(_del_list))
                self.log('New list: '+','.join(_new_list))
            self._add_files('wallpaper-index', 'wallpapers',
                            _new_list, fundamentals)
            self._update_media_index(self.protocolclass.WPictureIndexFile,
                                     self.protocolclass.WPictureIndexEntry,
                                     [self.protocolclass.PIC_PATH],
                                     self.protocolclass.PIC_EXCLUDED_FILES,
                                     self.protocolclass.PIC_INDEX_FILE_NAME)
            fundamentals['rebootphone']=True
        except:
            if __debug__:
                raise
        return fundamentals

    # Phonebook stuff-----------------------------------------------------------
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
            _newfilename='%(prefix)s/%(index)d.jpg'%\
                          { 'prefix': self.protocolclass.PB_WP_CACHE_PATH,
                            'index': idx }
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
            _wp_range[wp]='/ff/%(filename)s|%(wpname)s'%\
                           { 'filename': _newfilename,
                             'wpname': common.stripext(wp),
                             }
            fundamentals['wallpaper-range']=_wp_range

# CalendarEntry class-----------------------------------------------------------
parentcalendarentry=scha950.CalendarEntry
class CalendarEntry(parentcalendarentry):
    pass


# PBEntry class-----------------------------------------------------------------
parentpbentry=scha950.PBEntry
class PBEntry(parentpbentry):

    def _build_memo(self, memo):
        if memo:
            self.pb.note=memo

    def _build(self, entry):
        parentpbentry._build(self, entry)
        self._build_memo(entry.get('memos', [{}])[0].get('memo', None))

    def _extract_wallpaper(self, entry, p_class):
        if not self.pb.has_wallpaper:
            return
        _idx=self.pb.wallpaper.rfind('|')+1
        # really ugly hack here !!!
        _wp=self.pb.wallpaper[_idx:]
        if not _wp.startswith('Preloaded'):
            # assume that the name has extension .jpg
            _wp+='.jpg'
        
        entry['wallpapers']=[{ 'wallpaper': _wp,
                               'use': 'call' }]

    def _extract_memo(self, entry, p_class):
        # extract the note portion from the phone into BitPim dict
        if self.pb.has_note:
            entry['memos']=[{ 'memo': self.pb.note }]

    def getvalue(self):
        _entry=parentpbentry.getvalue(self)
        self._extract_memo(_entry, self.phone.protocolclass)
        return _entry

# Profile class-----------------------------------------------------------------
parentprofile=scha950.Profile
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

    # fill in the list of ringtone/sound origins on your phone
    ringtoneorigins=('ringers', 'sounds')
    # ringtone origins that are not available for the contact assignment
    excluded_ringtone_origins=('sounds',)

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    # wallpaper origins that are not available for the contact assignment
    excluded_wallpaper_origins=('video',)

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 220, 'height': 184, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 128, 'height': 96, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 128, 'height': 96, 'format': "JPEG"}))
    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets

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
            'memo': 1,
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
