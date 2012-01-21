### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungschu470.py 4777 2010-01-07 03:24:27Z djpham $

"""Communicate with the Samsung SCH-U470 (Juke) Phone"""

import common
import com_samsungschu740 as u740
import p_samsungschu470 as p_u470
import helpids

parentphone=u740.Phone
class Phone(parentphone):
    desc='SCH-U470'
    helpid=helpids.ID_PHONE_SAMSUNGSCHU470
    protocolclass=p_u470
    serialsname='schu470'

    ringtone_noring_range='range_tones_preloaded_el_no_rings'
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
##        'Clapping': 'range_sound_preloaded_el_clapping',
##        'Crowd Roar': 'range_sound_preloaded_el_crowed_roar',
##        'Happy Birthday': 'range_sound_preloaded_el_birthday',
##        'Rainforest': 'range_sound_preloaded_el_rainforest',
##        'Train': 'range_sound_preloaded_el_train',
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
        }
    builtin_groups={
        1: 'Business',
        2: 'Colleague',
        3: 'Family',
        4: 'Friends'
        }

    my_model='SCH-U470/Juke'
    my_manufacturer='SAMSUNG'
    detected_model='U470'

    def __init__(self, logtarget, commport):
        "Calls all the constructors and sets initial modes"
        parentphone.__init__(self, logtarget, commport)
        global PBEntry
        self.pbentryclass=PBEntry

    def _read_ringtone_range(self, fundamentals):
        fundamentals['ringtone-range']={}

    def get_ringtone_range(self, name, fundamentals):
        if not name:
            # return No Rings
            return self.ringtone_default_range
        # check the builtin ringtones
        if self.builtin_ringtones.has_key(name):
            return self.builtin_ringtones[name]
        if self.builtin_sounds.has_key(name):
            return self.builtin_sounds[name]
        # check for custom ringtones,
        # this model does not use ranges for custom ringtones, just straight
        # file names instead.
        _rt_index=fundamentals.get('ringtone-index', {})
        for _entry in _rt_index.values():
            if _entry['name']==name:
                _filename=_entry.get('filename', None)
                if _filename:
                    return '/ff/'+_filename

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
        # Again, this model does not use ringtone ranges, just filename
        if range.startswith('/ff/'):
            return common.basename(range)

    # Wallpaper stuff-----------------------------------------------------------
    def _get_file_wallpaper_index(self, idx, result,
                                  path, origin):
        for _filename in self.listfiles(path):
            result[idx]={ 'name': self.basename(_filename),
                          'filename': _filename,
                          'origin': origin }
            idx+=1
        return idx

    def get_wallpaper_index(self):
        _res={}
        _idx=self._get_builtin_wallpaper_index(0, _res)
        _idx=self._get_file_wallpaper_index(_idx, _res,
                                            self.protocolclass.PIC_PATH,
                                            'images')
        return _res

    def savewallpapers(self, fundamentals, merge):
        # send wallpapers to the phone
        """Save wallpapers to the phone"""
        self.log('Writing wallpapers to the phone')
        try:
            _del_list, _new_list=self._get_del_new_list('wallpaper-index',
                                                        'wallpapers',
                                                        merge,
                                                        fundamentals,
                                                        frozenset(['video']))
            if __debug__:
                self.log('Delete list: '+','.join(_del_list))
                self.log('New list: '+','.join(_new_list))
            self._add_files('wallpaper-index', 'wallpapers',
                            _new_list, fundamentals)
            fundamentals['rebootphone']=True
        except:
            if __debug__:
                raise
        return fundamentals

# CalendarEntry class-----------------------------------------------------------
parentcalendarentry=u740.CalendarEntry
class CalendarEntry(parentcalendarentry):
    pass

# PBEntry class-----------------------------------------------------------------
parentpbentry=u740.PBEntry
class PBEntry(parentpbentry):

    def _extract_ringtone(self, entry, p_class):
        if  self.pb.has_ringtone and \
           self.pb.ringtone:
            if self.pb.ringtone.startswith('/ff/'):
                # user's ringtone
                _ringtone=common.basename(self.pb.ringtone)
            else:
                # built-in ringtone
                _ringtone=self.phone.ringtone_name_from_range(
                    self.pb.ringtone, self.fundamentals)
            if _ringtone:
                entry['ringtones']=[{ 'ringtone': _ringtone,
                                      'use': 'call' }]

    def getvalue(self):
        _entry=parentpbentry.getvalue(self)
        self._extract_ringtone(_entry, self.phone.protocolclass)
        return _entry

# Profile class-----------------------------------------------------------------
parentprofile=u740.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    WALLPAPER_WIDTH=176
    WALLPAPER_HEIGHT=220
    autodetect_delay=3
    usbids=( ( 0x04e8, 0x6640, 2),)
    deviceclasses=("serial",)
    BP_Calendar_Version=3
    # For phone detection
    phone_manufacturer=Phone.my_manufacturer
    phone_model=Phone.my_model

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 128, 'height': 164, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 112, 'height': 84, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 128, 'height': 220, 'format': "JPEG"}))
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
