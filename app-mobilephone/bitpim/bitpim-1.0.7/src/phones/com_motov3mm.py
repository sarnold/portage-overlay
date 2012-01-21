### BITPIM
###
### Copyright (C) 2007 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_motov3mm.py 4541 2008-01-04 03:41:51Z djpham $

"""Communicate with Motorola phones using AT commands"""
import time

import common
import com_motov710m as v710m
import com_motov3m as v3m
import prototypes
import p_motov3m
import helpids

parentphone=v710m.Phone
class Phone(parentphone):
    """ Talk to a Motorola V3mM phone"""
    desc='Moto-V3mM'
    helpid=helpids.ID_PHONE_MOTOV3MM
    protocolclass=p_motov3m
    serialsname='motov3mm'
    MODEOBEX='modeobex'

    builtinringtones=(
        (0, ('Silent',)),
        (5, ('Vibe Dot', 'Vibe Dash', 'Vibe Dot Dot', 'Vibe Dot Dash',
             'Vibe Pulse')),
        )

    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)
        self.obex=None

    def _get_wallpaper_index(self):
        res={}
        _files=self.listfiles(self.protocolclass.WP_PATH).keys()
        _files.sort()
        for _index,_filename in enumerate(_files):
            _name=common.basename(_filename)
            if self.protocolclass.valid_wp_filename(_name):
                res[_index]={ 'name': _name,
                              'filename': _filename,
                              'origin': 'images' }
        return res

    def _get_ringtone_index(self):
        res={}
        # first the builtin ones
        for _l in self.builtinringtones:
            _idx=_l[0]
            for _e in _l[1]:
                res[_idx]={ 'name': _e, 'origin': 'builtin' }
                _idx+=1
        # now the custome one
        _buf=prototypes.buffer(self.getfilecontents(
            self.protocolclass.RT_INDEX_FILE))
        _idx_file=self.protocolclass.ringtone_index_file()
        _idx_file.readfrombuffer(_buf, logtitle='Read ringtone index file')
        for _entry in _idx_file.items:
            _filename=self.decode_utf16(_entry.name)
            _name=common.basename(_filename)
            if self.protocolclass.valid_rt_filename(_name):
                res[_entry.index]={ 'name': _name,
                                    'filename': _filename,
                                    'type': _entry.ringtone_type,
                                    'origin': 'ringers' }
        return res

    def getringtones(self, fundamentals):
        """Retrieve ringtones data"""
        self.log('Reading ringtones')
        self.setmode(self.MODEOBEX)
        _res={}
        _rt_index=fundamentals.get('ringtone-index', {})
        for _entry in _rt_index.values():
            if _entry.has_key('filename'):
                try:
                    _res[_entry['name']]=self.obex.getfilecontents(
                        self.protocolclass.OBEXName(_entry['filename']))
                except:
                    self.log('Failed to read media file %s'%_entry['filename'])
        fundamentals['ringtone']=_res
        self.setmode(self.MODEMODEM)
        return fundamentals

    def saveringtones(self, fundamentals, merge):
        """Save ringtones to the phone"""
        self.log('Writing ringtones to the phone')
        try:
            _del_list, _new_list=self._get_del_new_list('ringtone-index',
                                                        'ringtone',
                                                        merge,
                                                        fundamentals,
                                                        frozenset(['ringers']))
            # delete files, need to be in OBEX mode
            self.setmode(self.MODEOBEX)
            self._del_files('ringtone-index', 'audio',
                            _del_list, fundamentals)
            # and add new files, need to be in OBEX mode
            self._add_files('ringtone-index', 'ringtone', 'audio',
                            _new_list, fundamentals)
        except:
            if __debug__:
                self.setmode(self.MODEMODEM)
                raise
        self.setmode(self.MODEMODEM)
        return fundamentals

    def savewallpapers(self, fundamentals, merge):
        """Save wallpapers to the phone"""
        self.log('Writing wallpapers to the phone')
        try:
            _del_list, _new_list=self._get_del_new_list('wallpaper-index',
                                                        'wallpapers',
                                                        merge,
                                                        fundamentals,
                                                        frozenset(['images']))
            # delete files, need to be in OBEX mode
            self.setmode(self.MODEOBEX)
            self._del_files('wallpaper-index', 'picture',
                            _del_list, fundamentals)
            # and add new files, need to be in OBEX mode
            self._add_files('wallpaper-index', 'wallpapers', 'picture',
                                    _new_list, fundamentals)
        except:
            if __debug__:
                self.setmode(self.MODEMODEM)
                raise
        self.setmode(self.MODEMODEM)
        return fundamentals

#-------------------------------------------------------------------------------
parentprofile=v3m.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    phone_model='V3mM'

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('ringtone', 'read', None),   # all ringtone reading
        ('ringtone', 'write', None),
        ('ringtone', 'write', 'OVERWRITE'),
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', None),
        ('wallpaper', 'write', 'OVERWRITE'),
        ('sms', 'read', None),
        )
