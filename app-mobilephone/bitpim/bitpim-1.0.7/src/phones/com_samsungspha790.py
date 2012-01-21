### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungspha790.py 4365 2007-08-17 21:11:59Z djpham $

"""Communicate with a Samsung SPH-A790"""
# System modules
import sha

# BitPim modules
import common
import com_samsung_packet
import p_samsungspha790


parentphone=com_samsung_packet.Phone
class Phone(parentphone):
    desc='SPH-A790'
    protocolclass=p_samsungspha790
    serialsname='spha790'

    builtin_ringtones=(
        (0, ['Default Tone']),
        (68, ['Tone %d'%x for x in range(1, 10)]),
        (95, ['Ring %d'%x for x in range(1, 16)]),
        (110, ['Melody %d'%x for x in range(1, 21)]),
        )
    builtin_pictures=(
        (1, ['People %d'%x for x in range(1, 22)]),
        (23, ['Animal %d'%x for x in range(1, 16)]),
        (38, ['Other %d'%x for x in range(1, 10)]),
        )

    camera_picture_index=100    # starting index of camera picture

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
        self.setmode(self.MODEPHONEBOOK)

        # use a hash of ESN and other stuff (being paranoid)
        self.log("Retrieving fundamental phone information")
        self.log("Reading phone serial number")
        results['uniqueserial']=sha.new(self.get_esn()).hexdigest()

        # now read groups
        self.log("Reading group information")
        results['groups']=self.read_groups()

        # getting rintone-index
        results['ringtone-index']=self._get_builtin_index(self.builtin_ringtones)
        
        # getting wallpaper-index
        results['wallpaper-index']=self.get_wallpaper_index()
        
        self.setmode(self.MODEMODEM)
        self.log("Fundamentals retrieved")

        return results

    def _get_builtin_index(self, builtin_list):
        _res={}
        for _starting_idx,_list in builtin_list:
            _idx=_starting_idx
            for _entry in _list:
                _res[_idx]={ 'name': _entry,
                             'origin': 'builtin' }
                _idx+=1
        return _res

    def read_groups(self):
        g={}
        # Don't crash if phone doesn't accept #PMODE=1 (Canadian phones)
        try:
            self.setmode(self.MODEPHONEBOOK)
        except:
            return g
        req=self.protocolclass.groupnamerequest()
	for i in range(self.protocolclass.NUMGROUPS):
            req.gid=i
            # Don't crash if phone doesn't support groups
            try:
                res=self.sendpbcommand(req, self.protocolclass.groupnameresponse)
                if res[0].entry.groupname and \
                   res[0].entry.groupname!='Empty':
                    g[i]={'name': res[0].entry.groupname}
            except Exception,e:
                return g
	return g

    # phonebook stuff----------------------------------------------------------
    def _extract_misc(self, res, entry, fundamentals):
        _name={ 'full': entry.name }
        if entry.nick:
            _name['nickname']=entry.nick
        res['names']=[_name]
        _grp=fundamentals.get('groups', {}).get(entry.group, None)
        if _grp.get('name', None):
            res['categories']=[{ 'category': _grp['name'] }]
        if entry.email:
            res['emails']=[{ 'email': entry.email }]
        if entry.url:
            res['urls']=[{ 'url': entry.url }]
        if entry.memo:
            res['memos']=[{ 'memo': entry.memo }]

    def _extract_wallpaper(self, res, entry, fundamentals):
        _wp_index=fundamentals.get('wallpaper-index', {})
        _wp_name=_wp_index.get(entry.wallpaper, {}).get('name', None)
        if _wp_name:
            res['wallpapers']=[{ 'wallpaper': _wp_name,  'use': 'call' }]

    def _extract_ringtone(self, res, entry, fundamentals):
        _rt_index=fundamentals.get('ringtone-index', {})
        _rt_name=_rt_index.get(entry.ringtone, {}).get('name', None)
        if _rt_name:
            res['ringtones']=[{ 'ringtone': _rt_name, 'use': 'call' }]

    number_type_dict={
        0: 'cell', 1: 'home', 2: 'office', 3: 'pager', 4: 'fax' }
    def _extract_number(self, res, entry, idx, fundamentals):
        _item=entry.numbers[idx]
        if not _item.number:
            return None
        _res={ 'number': _item.number,
               'type': self.number_type_dict.get(idx, 'none') }
        # TODO: speed dial
        return _res
    def _extract_numbers(self, res, entry, fundamentals):
        _primary=entry.primary-1
        _numbers=[self._extract_number(res, entry, _primary, fundamentals)]
        for i in range(self.protocolclass.NUMPHONENUMBERS):
            if i==_primary:
                continue
            _number=self._extract_number(res, entry, i, fundamentals)
            if _number:
                _numbers.append(_number)
        res['numbers']=_numbers
        
    def extractphonebookentry(self, entry, fundamentals):
        res={}
        res['serials']=[ { 'sourcetype': self.serialsname,
                           'sourceuniqueid': fundamentals['uniqueserial'],
                           'slot': entry.slot,
                           'uslsot': entry.uslot }]
        _args=(res, entry, fundamentals)
        self._extract_misc(*_args)
        self._extract_wallpaper(*_args)
        self._extract_ringtone(*_args)
        self._extract_numbers(*_args)
        return res

    def getphonebook(self, result):
        """Read the phonebook data."""
        pbook={}
        self.setmode(self.MODEPHONEBOOK)

        req=self.protocolclass.phonebookslotrequest()
        lastname=""
        for slot in range(1,self.protocolclass.NUMPHONEBOOKENTRIES+1):
            req.slot=slot
            res=self.sendpbcommand(req, self.protocolclass.phonebookslotresponse, fixup=self.pblinerepair)
            if res:
                self.log(`slot`+": "+res[0].entry.name)
                entry=self.extractphonebookentry(res[0].entry, result)
                pbook[res[0].entry.uslot]=entry
            self.progress(slot, self.protocolclass.NUMPHONEBOOKENTRIES, lastname)
        
        result['phonebook']=pbook
##        cats=[]
##        for i in result['groups']:
##            if result['groups'][i]['name']!='Unassigned':
##                cats.append(result['groups'][i]['name'])
##        result['categories']=cats
        print "returning keys",result.keys()
        
        return pbook


    # wallpaper stuff----------------------------------------------------------
    def get_wallpaper_index(self):
        _res=self._get_builtin_index(self.builtin_pictures)
        self.setmode(self.MODEBREW)
        _files=self.listfiles(self.protocolclass.WP_CAMERA_PATH)
        _idx=self.camera_picture_index
        for _pathname in _files:
            _res[_idx]={ 'name': common.basename(_pathname)+'.jpg',
                         'origin': 'camera' }
            _idx+=1
        self.setmode(self.MODEMODEM)
        return _res

    def getwallpapers(self, fundamentals):
        """Read camera pictures from the phone"""
        self.log('Reading Camera Pictures')
        self.setmode(self.MODEBREW)
        _files=self.listfiles(self.protocolclass.WP_CAMERA_PATH)
        _media={}
        for _pathname in _files:
            _filename=common.basename(_pathname)+'.jpg'
            try:
                _media[_filename]=self.getfilecontents(_pathname, True)
            except Exception,e:
                self.log('Failed to read file %s due to: %s'%(_pathname, str(e)))
        self.setmode(self.MODEMODEM)
        fundamentals['wallpapers']=_media
        return fundamentals

    getringtones=NotImplemented

    @classmethod
    def detectphone(_, coms, likely_ports, res, _module, _log):
        pass

#-------------------------------------------------------------------------------
parentprofile=com_samsung_packet.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    # for phone detection
    phone_manufacturer='SAMSUNG'
    phone_model='SPH-A790/118'

    WALLPAPER_WIDTH=176
    WALLPAPER_HEIGHT=220
    # Outside LCD: 128x96

    def __init__(self):
        parentprofile.__init__(self)

    def convertphonebooktophone(self, helper, data):
        return data

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
##        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('wallpaper', 'read', None),  # all wallpaper reading
##        ('wallpaper', 'write', None), # Image conversion needs work
##        ('ringtone', 'read', None),   # all ringtone reading
##        ('ringtone', 'write', None),
##        ('calendar', 'read', None),   # all calendar reading
##        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
##        ('todo', 'read', None),     # all todo list reading
##        ('todo', 'write', 'OVERWRITE'),  # all todo list writing
##        ('memo', 'read', None),     # all memo list reading
##        ('memo', 'write', 'OVERWRITE'),  # all memo list writing
        )
