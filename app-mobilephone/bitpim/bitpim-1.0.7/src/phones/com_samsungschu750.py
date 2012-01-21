### BITPIM
###
### Copyright (C) 2009 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungschu750.py 4778 2010-01-08 04:21:54Z djpham $

"""Communicate with the Samsung SCH-U750 (Alias 2) Phone"""

# System modules

# BitPim modules
import common
import commport
import com_brew
import com_samsungschu470 as schu470
import p_samsungschu750 as p_schu750
import helpids
import prototypes

parentphone=schu470.Phone
class Phone(com_brew.RealBrewProtocol2, parentphone):
    desc='SCH-U750'
    helpid=helpids.ID_PHONE_SAMSUNGSCHU750
    protocolclass=p_schu750
    serialsname='schu750'

    my_model='SCH-U750/DM'
    my_manufacturer='SAMSUNG'
    detected_model='U750'

    ringtone_noring_range='range_tones_preloaded_el_22'
    ringtone_default_range='range_tones_preloaded_el_01'
    builtin_ringtones={
        'VZW Default Tone': ringtone_default_range,
        'Animato': 'range_tones_preloaded_el_02',
        'Belly Dance': 'range_tones_preloaded_el_03',
        'Chair In The Sky': 'range_tones_preloaded_el_04',
        'Classic Bell': 'range_tones_preloaded_el_05',
        "Club In The 80's": 'range_tones_preloaded_el_06',
        'Club Mix': 'range_tones_preloaded_el_07',
        'Crossing Tone': 'range_tones_preloaded_el_08',
        'Fell Groovy': 'range_tones_preloaded_el_09',
        'Fuss & Feathers': 'range_tones_preloaded_el_10',
        'Gutta Tone': 'range_tones_preloaded_el_11',
        'Hip Hop Guy': 'range_tones_preloaded_el_12',
        'Late Night': 'range_tones_preloaded_el_13',
        'Mix Master': 'range_tones_preloaded_el_14',
        'Popple Tone': 'range_tones_preloaded_el_15',
        'Serene Tone': 'range_tones_preloaded_el_16',
        'Sonic Boom': 'range_tones_preloaded_el_17',
        'Spanish Guitar': 'range_tones_preloaded_el_18',
        'The Floor': 'range_tones_preloaded_el_19',
        'Trip To Heaven': 'range_tones_preloaded_el_20',
        'Beep Once': 'range_tones_preloaded_el_21',
        'No Ring': ringtone_noring_range,
        }

    builtin_sounds={
        'Clapping': 'range_sound_preloaded_el_clapping',
        'Crowd Roar': 'range_sound_preloaded_el_crowed_roar',
        'Happy Birthday': 'range_sound_preloaded_el_birthday',
        'Rainforest': 'range_sound_preloaded_el_rainforest',
        'Train': 'range_sound_preloaded_el_train',
        # same as ringtones ??
        'Sound Beep Once': 'range_sound_preloaded_el_beep_once',
        'Sound No Ring': 'range_sound_preloaded_el_no_rings',
        }

    # We can't use bult-in wallpapers for contact ID
    builtin_wallpapers={}

    def __init__(self, logtarget, commport):
        "Calls all the constructors and sets initial modes"
        parentphone.__init__(self, logtarget, commport)
        global PBEntry, CalendarEntry
        self.pbentryclass=PBEntry
        self.calendarclass=CalendarEntry

    # ringtone stuff-----------------------------------------------------------
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
            if not _file_name.startswith(self.protocolclass.SND_PRELOADED_PREFIX):
                result[idx]= { 'name': common.basename(_entry.pathname),
                               'filename': _file_name,
                               'origin': origin,
                               }
                idx+=1
        return idx
    def get_ringtone_index(self):
        _res={}
        _idx=self._get_builtin_ringtone_index(0, _res)
        # Cannot get any of the ringtones (ringers) index
        # get the index of Sounds items
        _idx=self._get_file_ringtone_index(_idx, _res,
                                           self.protocolclass.SND_INDEX_FILE_NAME,
                                           self.protocolclass.RSoundsIndexFile,
                                           'sounds')
        return _res

    def _append_sounds_index_file(self, new_files_list):
        """Update the Sounds index file with new/added files"""
        self.log("Appending Sounds index file")
        # read in existing index entries from index file
        _old_snd=self.readobject(self.protocolclass.SND_INDEX_FILE_NAME,
                                 self.protocolclass.RSoundsIndexFile)
        _new_snd=self.protocolclass.WSoundsIndexFile()
        for _v in _old_snd.items:
            _new_snd.items.append(self.protocolclass.WSoundsIndexEntry(name='',
                                                                       pathname=_v.pathname[4:],
                                                                       eor='|'+_v.misc+'\x0A'))
        # now append new entries
        for _f in new_files_list:
            _new_snd.items.append(self.protocolclass.WSoundsIndexEntry(name='',
                                                                       pathname=self.protocolclass.SND_PATH+'/'+_f))
        # and write it out
        self.writeobject(self.protocolclass.SND_INDEX_FILE_NAME,
                         _new_snd)
        
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
            _added_files_list=self._add_files('ringtone-index', 'ringtone',
                                              _new_list, fundamentals)
            if _added_files_list:
                self._append_sounds_index_file(_added_files_list)
            fundamentals['rebootphone']=True
        except:
            if __debug__:
                raise
        return fundamentals

    # SMS Stuff----------------------------------------------------------------
    def _build_locked_field(self, entry, buf):
        _locked=self.protocolclass.UINT(sizeinbytes=2)
        _locked.readfrombuffer(buf)
        entry.locked=bool(_locked.getvalue() & 0x100)

    # Phone Detection-----------------------------------------------------------
    def is_mode_brew(self):
        # Borrowed from the VX4400
        req=self.protocolclass.testing0crequest()
        respc=self.protocolclass.data
        for baud in 0, 38400, 115200:
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            try:
                self.sendbrewcommand(req, respc, callsetmode=False)
                return True
            except com_phone.modeignoreerrortypes:
                pass
        return False

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
                if res[port]['model']:
                    # been found, not much we can do now
                    continue
                p=_module.Phone(_log, commport.CommConnection(_log, port, timeout=1))
                # Force to check for BREW
                if not res[port]['mode_brew']:
                    res[port]['mode_brew']=p.is_mode_brew()
                if res[port]['mode_brew']:
                    p.check_my_phone(res[port])
                p.comm.close()
            except:
                if __debug__:
                    raise


# CalendarEntry class-----------------------------------------------------------
parentcalendarentry=schu470.CalendarEntry
class CalendarEntry(parentcalendarentry):
    """Transient class to handle calendar data being sent to, retrieved from
    the phone.
    """
    # routines to build phone data from BitPim dict
    def _build(self, entry):
        # populate this object with data from BitPim
        self.cal.titlelen=len(entry.desc_loc)
        self.cal.title=entry.desc_loc
        self.cal.start=entry.start
        self.cal.end=entry.end
        self.cal.repeat=self._build_repeat(entry)
        self.cal.alarm=self._build_alarm(entry)
        self.cal.alert=self._build_alert(entry)
        self.cal.duration=self._build_duration(entry)
        self.cal.timezone=self._build_tz()
        self.cal.creationtime=self.phone._time_now()
        _ringtone=self.phone.get_ringtone_range(entry.ringtone,
                                                self.fundamentals)
        self.cal.ringtonelen=len(_ringtone)
        self.cal.ringtone=_ringtone

    # routines to extract data from the phone into BitPim dict
    def _extract_end(self):
        return self.cal.end[:5]

# PBEntry class-----------------------------------------------------------------
parentpbentry=schu470.PBEntry
class PBEntry(parentpbentry):

    _IM_Type_String={ 1: 'AIM', 2: 'Yahoo!', 3: 'WL Messenger' }
    _IM_Type_Index={ 'AIM': 1, 'Yahoo!': 2, 'WL Messenger': 3 }

    # routines to convert BitPim dict into phone's data
    def _build_address(self, address):
        if address:
            self.pb.address=address

    def _build_IM(self, im):
        if im:
            self.pb.im_type=self._IM_Type_Index.get(im.get('type', ''), 1)
            self.pb.im_name=im.get('username', '')

    def _build(self, entry):
        parentpbentry._build(self, entry)
        self._build_address(entry.get('addresses', [{}])[0])
        self._build_IM(entry.get('ims', [{}])[0])

    # routines to convert phone's data into BitPim dict
    def _extract_group(self, entry, p_class):
        if not self.pb.has_group:
            # no group specified
            return
        _groups=self.fundamentals.get('groups', {})
        _res=[]
        # each group is turned on/off via each bit of the _groups value
        for _index, _item in _groups.items():
            if (1<<_index)&self.pb.group:
                _res.append({ 'category': _item['name'] })
        if _res:
            entry['categories']=_res

    def _extract_wallpaper(self, entry, p_class):
        if not self.pb.has_cached_wp:
            return
        # really ugly hack here !!!
        _wp=self.pb.cached_wp.split('|')[1]
        # BitPim can only deal with non-builtin wallpapers
        if not _wp.startswith('Preloaded'):
            # assume that the name has extension .jpg
            entry['wallpapers']=[{ 'wallpaper': _wp+'.jpg',
                                   'use': 'call' }]

    def _extract_IM(self, entry, p_class):
        if self.pb.has_im_name:
            entry['ims']=[{ 'type': self._IM_Type_String.get(self.pb.im_type, ''),
                            'username': self.pb.im_name }]

    def _extract_address(self, entry, p_class):
        if self.pb.has_address:
            entry['addresses']=[self.pb.address]

    def getvalue(self):
        _entry=parentpbentry.getvalue(self)
        self._extract_IM(_entry, self.phone.protocolclass)
        self._extract_address(_entry, self.phone.protocolclass)
        return _entry

# Profile class-----------------------------------------------------------------
parentprofile=schu470.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname
    WALLPAPER_WIDTH=240
    WALLPAPER_HEIGHT=274
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
    ringtoneorigins=('sounds',)
    # ringtone origins that are not available for the contact assignment
    excluded_ringtone_origins=()

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    # wallpaper origins that are not available for the contact assignment
    excluded_wallpaper_origins=('video',)

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 240, 'height': 274, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 80, 'height': 106, 'format': "JPEG"}))
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
                'type': 0, 'company': 0, 'street': 1, 'street2': 0,
                'city': 1, 'state': 1, 'postalcode': 1, 'country': 1,
                'details': 1 },
            'url': 0,
            'memo': 1,
            'category': 1,
            'wallpaper': 1,
            'ringtone': 1,
            'storage': 0,
            'im': 1,
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
