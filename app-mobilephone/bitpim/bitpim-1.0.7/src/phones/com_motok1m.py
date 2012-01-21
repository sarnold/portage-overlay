### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_motok1m.py 4529 2007-12-26 18:38:19Z djpham $

"""Communicate with Motorola K1m phones using AT commands"""

# BitPim modules
import common
import com_motov710m
import prototypes
import p_motok1m
import helpids

parentphone=com_motov710m.Phone
class Phone(parentphone):
    desc='Moto-K1m'
    helpid=helpids.ID_PHONE_MOTOK1M
    serialsname='motok1m'
    protocolclass=p_motok1m

    builtinringtones=(
        (0, ('No Ring',)),
        )

    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)

    # Ringtones stuff----------------------------------------------------------
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
            if _filename.startswith(self.protocolclass.RT_PATH):
                _origin='ringers'
            elif _filename.startswith(self.protocolclass.SND_PATH):
                _origin='sounds'
            else:
                # neither ringtone nor sounds, can't use this
                continue
            res[_entry.index]={ 'name': common.basename(_filename),
                                'filename': _filename,
                                'type': _entry.ringtone_type,
                                'origin': _origin }
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
        self.setmode(self.MODEPHONEBOOK)
        self.setmode(self.MODEBREW)
        try:
            _del_list, _new_list=self._get_del_new_list('ringtone-index',
                                                        'ringtone',
                                                        merge,
                                                        fundamentals,
                                                        frozenset(['sounds']))
            # replace files, need to be in BREW mode
            self._replace_files('ringtone-index', 'ringtone',
                                _new_list, fundamentals)
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


#------------------------------------------------------------------------------
parentprofile=com_motov710m.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    usbids=( ( 0x22B8, 0x2A64, 1),)

    # fill in the list of ringtone/sound origins on your phone
    ringtoneorigins=('ringers', 'sounds')
    # ringtone origins that are not available for the contact assignment
    excluded_ringtone_origins=()
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    excluded_wallpaper_origins=()
    # use for auto-detection
    phone_manufacturer='Motorola'
    phone_model='K1m'
    common_model_name='K1m'
    generic_phone_model='Motorola CDMA K1m phone'

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 184, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 96, 'height': 67, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))

    field_color_data=parentprofile.field_color_data
    field_color_data.update({
        'phonebook': {
            'name': {
                'first': 1, 'middle': 1, 'last': 1, 'full': 1,
                'nickname': 0, 'details': 1 },
            'number': {
                'type': 5, 'speeddial': 5, 'number': 5,
                'details': 5,
                'ringtone': 5, 'wallpaper': 5 },
            'email': 2,
            'email_details': {
                'emailspeeddial': 2, 'emailringtone': 2,
                'emailwallpaper': 2 },
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
            }})
