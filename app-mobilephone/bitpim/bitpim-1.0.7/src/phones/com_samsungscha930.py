### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungscha930.py 4174 2007-04-01 19:13:48Z djpham $

"""Communicate with the Samsung SCH-A930 Phone"""

# System Models
import fnmatch

# BitPim modules
import common
import com_samsungscha950 as com_a950
import p_samsungscha950 as p_a950
import p_samsungscha930 as p_a930
import helpids

class Phone(com_a950.Phone):
    desc='SCH-A930'
    helpid=helpids.ID_PHONE_SAMSUNGSCHA930
    protocolclass=p_a930
    serialsname='scha930'

    # Detection stuff
    my_model='SCH-A930/DM'
    my_manufacturer='SAMSUNG'
    detected_model='A930'

    ringtone_noring_range='range_tones_preloaded_el_15'
    ringtone_default_range='range_tones_preloaded_el_01'
    builtin_ringtones={
        'VZW Default Tone': ringtone_default_range,
        'Melody 1': 'range_tones_preloaded_el_05',
        'Melody 2': 'range_tones_preloaded_el_06',
        'Melody 3': 'range_tones_preloaded_el_07',
        'Melody 4': 'range_tones_preloaded_el_08',
        'Melody 5': 'range_tones_preloaded_el_09',
        'Melody 6': 'range_tones_preloaded_el_10',
        'Bell 1': 'range_tones_preloaded_el_02',
        'Bell 2': 'range_tones_preloaded_el_03',
        'Bell 3': 'range_tones_preloaded_el_04',
        'Beep Once': 'range_tones_preloaded_el_11',
        'No Ring': ringtone_noring_range,
        }
    builtin_sounds={
        'Birthday': 'range_sound_preloaded_el_birthday',
        'Clapping': 'range_sound_preloaded_el_clapping',
        'Crowd Roar': 'range_sound_preloaded_el_crowed_roar',
        'Rainforest': 'range_sound_preloaded_el_rainforest',
        'Train': 'range_sound_preloaded_el_train',
        # same as ringtones ??
        'Sound Beep Once': 'range_sound_preloaded_el_beep_once',
        'Sound No Ring': 'range_sound_preloaded_el_no_rings',
        }
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

# adding video to the wallpaper stuff
    def _get_video_index(self, idx, result):
        # just scan the dir for *.3g2 files
        _files=self.listfiles(self.protocolclass.FLIX_PATH)
        for _,_f in _files.items():
            _filename=_f['name']
            _name=common.basename(_filename)
            if fnmatch.fnmatch(_name, '*.3g2'):
                result[idx]= { 'name': _name,
                               'filename': _filename,
                               'origin': 'video',
                               }
                idx+=1
        return idx
        
    def get_wallpaper_index(self):
        _res={}
        _idx=self._get_file_wallpaper_index(0, _res)
        self._get_video_index(_idx, _res)
        return _res

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

#-------------------------------------------------------------------------------
parentprofile=com_a950.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    # For phone detection
    phone_manufacturer=Phone.my_manufacturer
    phone_model=Phone.my_model
    # "Warning" media size limit
    RINGTONE_LIMITS= {
        'MAXSIZE': 290000
    }

    # fill in the list of ringtone/sound origins on your phone
    ringtoneorigins=('ringers',)
    # all dumped in "images"
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 186, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 128, 'height': 96, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))
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
