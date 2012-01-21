### BITPIM
###
### Copyright (C) 2007 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungsphm300pim.py 4473 2007-11-29 22:36:56Z djpham $

"""Communicate with the Samsung SPH-M300 through the modem port (PIM)"""

import sha

import com_samsung_packet
import helpids
import p_samsungsphm300

parentphone=com_samsung_packet.Phone
class Phone(parentphone):
    "Talk to a Samsung SPH-M300 (PIM) phone"

    desc="SPH-M300"
    helpid=helpids.ID_PHONE_SAMSUNGSPHM300
    protocolclass=p_samsungsphm300
    serialsname='sphm300'

    builtinringtones=tuple(['Ring %d'%x for x in range(1, 11)])+\
                      ('After The Summer', 'Focus on It', 'Get Happy',
                       'Here It Comes', 'In a Circle', 'Look Back',
                       'Right Here', 'Secret Life',  'Shadow of Your Smile',
                       'Sunday Morning', 'Default')

    builtinimages=tuple(['People %d'%x for x in range(1, 11)])+\
                   tuple(['Animal %d'%x for x in range(1, 11)])+\
                   ('No Image',)
    numbertypetab=('cell', 'home', 'office', 'pager', 'fax')

    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE

    def _setmodephonebooktobrew(self):
        raise NotImplementedError('BREW mode not available')
    def _setmodemodemtobrew(self):
        raise NotImplementedError('BREW mode not available')
 
    def _get_ringtone_index(self):
        """Return the ringtone"""
        _res={}
        for _idx,_name in enumerate(self.builtinringtones):
            _res[_idx]={ 'name': _name,
                         'origin': 'builtin' }
        return _res
    def _get_wallpaper_index(self):
        """Return the wallpaper index"""
        _res={}
        for _idx, _name in enumerate(self.builtinimages):
            _res[_idx]={ 'name': _name,
                         'origin': 'builtin' }
        return _res

    def getfundamentals(self, results):
        """Gets information fundamental to interopating with the phone and UI."""

        # use a hash of ESN and other stuff (being paranoid)
        self.log("Retrieving fundamental phone information")
        self.log("Phone serial number")
        self.setmode(self.MODEMODEM)
        results['uniqueserial']=sha.new(self.get_esn()).hexdigest()

        self.log("Reading group information")
        results['groups']=self.read_groups()
        results['ringtone-index']=self._get_ringtone_index()
        results['wallpaper-index']=self._get_wallpaper_index()
        self.log("Fundamentals retrieved")
        return results

    def _extractphonebook_numbers(self, entry, fundamentals, res):
        """Extract and build phone numbers"""
        res['numbers']=[]
        speeddialtype=entry.speeddial
        # This phone supports neither secret nor speed dial
        for numberindex,type in enumerate(self.numbertypetab):
            if len(entry.numbers[numberindex].number):
                numhash={'number': entry.numbers[numberindex].number, 'type': type }
                if speeddialtype==numberindex:
                    # this is the main number
                    res['numbers'].insert(0, numhash)
                else:
                    res['numbers'].append(numhash)

    def _extractphonebook_ringtone(self, entry, fundamentals, res):
        """Extract ringtone info"""
        try:
            res['ringtones']=[{'ringtone': fundamentals['ringtone-index'][entry.ringtone]['name'],
                               'use': 'call'}]
        except KeyError:
            pass
    def _extractphonebook_wallpaper(self, entry, fundamentals, res):
        """Extract wallpaper info"""
        try:
            res['wallpapers']=[{'wallpaper': fundamentals['wallpaper-index'][entry.wallpaper]['name'],
                                'use': 'call'}]
        except KeyError:
            pass

    def makeentry(self, entry, fundamentals):
        e=parentphone.makeentry(self, entry, fundamentals)
        e.writeflg=True
        # this model can only set built-in ringtones and images,
        # everything else would be set to default
        try:
            e.ringtone=list(self.builtinringtones).index(entry['ringtone'])
        except ValueError:
            pass
        try:
            e.wallpaper=list(self.builtinimages).index(entry['wallpaper'])
        except ValueError:
            pass
        return e

    def getsms(self, results):
        """retrieve SMS data"""
        # It's not working for now, used for data recording/collection from
        # users to determine the return format
        self.log('Reading SMS data')
        _req=self.protocolclass.smsinrequest()
        for _cnt in range(self.protocolclass.NUMSMSINENTRIES):
            self.progress(_cnt, self.protocolclass.NUMSMSINENTRIES,
                          'Reading SMS entry %d'%_cnt)
            _req.slot=_cnt
            _resp=self.sendpbcommand(_req, self.protocolclass.smsinresponse)
        results['canned_msg']=[]
        results['sms']={}
        return results

    getwallpapers=NotImplemented
    getringtones=NotImplemented
    getcallhistory=NotImplemented
    getplaylist=NotImplemented
    gett9db=NotImplemented

parentprofile=com_samsung_packet.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_ ."
    RINGTONE_LIMITS= {
        'MAXSIZE': 250000
    }
    phone_manufacturer='SAMSUNG'
    phone_model='SPH-A620/152'
    numbertypetab=Phone.numbertypetab

    imageorigins={}
    imagetargets={}

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('todo', 'read', None),     # all todo list reading
        ('todo', 'write', 'OVERWRITE'),  # all todo list writing
        ('memo', 'read', None),     # all memo list reading
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing
        ('sms', 'read', None),         # all SMS list reading
        )

    __audio_ext={ 'MIDI': 'mid', 'PMD': 'pmd', 'QCP': 'qcp' }
    def QueryAudio(self, origin, currentextension, afi):
        # we don't modify any of these
        print "afi.format=",afi.format
        if afi.format in ("MIDI", "PMD", "QCP"):
            for k,n in self.RINGTONE_LIMITS.items():
                setattr(afi, k, n)
            return currentextension, afi
        d=self.RINGTONE_LIMITS.copy()
        d['format']='QCP'
        return ('qcp', fileinfo.AudioFileInfo(afi, **d))

    field_color_data={
        'phonebook': {
            'name': {
                'first': 1, 'middle': 1, 'last': 1, 'full': 1,
                'nickname': 0, 'details': 1 },
            'number': {
                'type': 5, 'speeddial': 0, 'number': 5, 'details': 5 },
            'email': 1,
            'address': {
                'type': 0, 'company': 0, 'street': 0, 'street2': 0,
                'city': 0, 'state': 0, 'postalcode': 0, 'country': 0,
                'details': 0 },
            'url': 1,
            'memo': 0,
            'category': 1,
            'wallpaper': 1,
            'ringtone': 1,
            'storage': 0,
            },
        'calendar': {
            'description': True, 'location': False, 'allday': False,
            'start': True, 'end': True, 'priority': True,
            'alarm': True, 'vibrate': False,
            'repeat': False,
            'memo': False,
            'category': False,
            'wallpaper': False,
            'ringtone': False,
            },
        'memo': {
            'subject': False,
            'date': False,
            'secret': False,
            'category': False,
            'memo': True,
            },
        'todo': {
            'summary': True,
            'status': False,
            'due_date': True,
            'percent_complete': False,
            'completion_date': False,
            'private': False,
            'priority': True,
            'category': False,
            'memo': False,
            },
        }
