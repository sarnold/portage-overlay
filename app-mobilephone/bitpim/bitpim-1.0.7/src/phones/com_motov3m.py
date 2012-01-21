### BITPIM
###
### Copyright (C) 2007 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_motov3m.py 4537 2007-12-30 03:32:13Z djpham $

"""Communicate with Motorola phones using AT commands"""

import common
import com_motov710 as v710
import helpids
import fileinfo
import p_motov3m
import prototypes

parentphone=v710.Phone
class Phone(parentphone):
    desc='Moto-V3m'
    helpid=helpids.ID_PHONE_MOTOV3M
    protocolclass=p_motov3m
    serialsname='motov3m'
    builtinringtones=(
        (0, ('Silent',)),
        (5, ('Vibe Dot', 'Vibe Dash', 'Vibe Dot Dot', 'Vibe Dot Dash',
             'Vibe Pulse')),
        )

    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)

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


#-------------------------------------------------------------------------------
parentprofile=v710.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname

    # use for auto-detection
    phone_manufacturer='Motorola'
    phone_model='V3m '
    common_model_name='V3m'
    generic_phone_model='Motorola CDMA V3m Phone'

    # fill in the list of ringtone/sound origins on your phone
    ringtoneorigins=('ringers',)

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 184, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 96, 'height': 72, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', 'OVERWRITE'),
        ('sms', 'read', None),     # all SMS list reading DJP
        )
