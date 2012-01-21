### BITPIM
###
### Copyright (C) 2005 Simon Capper <skyjunky@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

"""Communicate with the LG VX8300 cell phone


The code in this file mainly inherits from VX8100 code and then extends where
the 8300 has different functionality

"""

# standard modules
import time
import cStringIO
import sha

# my modules
import common
import commport
import copy
import com_lgvx4400
import p_brew
import p_lgvx8300
import com_lgvx8100
import com_brew
import com_phone
import com_lg
import prototypes
import bpcalendar
import call_history
import sms
import memo
import fileinfo
import helpids

class Phone(com_lg.LGUncountedIndexedMedia, com_lgvx8100.Phone):
    "Talk to the LG VX8300 cell phone"

    desc="LG-VX8300"
    helpid=helpids.ID_PHONE_LGVX8300
    protocolclass=p_lgvx8300
    serialsname='lgvx8300'

    external_storage_root='mmc1/'

    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'VZW Default Ringtone') + \
                      tuple(['Ringtone '+`n` for n in range(1,11)]) + \
                      ('No Ring',)

    ringtonelocations= (
        #  type          index file            default dir        external dir    max  type Index
        ( 'ringers',    'dload/myringtone.dat','brew/16452/lk/mr','mmc1/ringers', 100, 0x01, None),
        ( 'sounds',     'dload/mysound.dat',   'brew/16452/ms',   '',             100, 0x02, None),
        ( 'mp3',        'dload/my_mp3.dat',    'mmc1/my_mp3',     '',             100, 0x15, None),
       #( 'music',      'dload/sd_music.dat',  'mmc1/my_music',   '',             100, 0x14, None), # .wma files
        )

    calendarlocation="sch/schedule.dat"
    calendarexceptionlocation="sch/schexception.dat"
    calenderrequiresreboot=1
    memolocation="sch/memo.dat"

    builtinwallpapers = () # none

    wallpaperlocations= (
        #  type          index file            default dir     external dir  max  type Index
        ( 'images',     'dload/image.dat',    'brew/16452/mp', '',           100, 0x00, None),
        ( 'images(sd)', 'dload/sd_image.dat', 'mmc1/my_pix',   '',           100, 0x10, None),
        ( 'video',      'dload/video.dat',    'brew/16452/mf', '',           100, 0x03, None),
        ( 'video(sd)',  'dload/sd_video.dat', 'mmc1/my_flix',  '',           100, 0x13, None),
        )

    def __init__(self, logtarget, commport):
        com_lgvx8100.Phone.__init__(self, logtarget, commport)
        p_brew.PHONE_ENCODING=self.protocolclass.PHONE_ENCODING
        self.mode=self.MODENONE

    def get_esn(self, data=None):
        # return the ESN of this phone
        return self.get_brew_esn()

    def setDMversion(self):
        _fw_version=self.get_firmware_version()[-1]
        # T83VZV04 uses DMv5
        self._DMv5=self.my_model=='VX8300' and _fw_version>'3'
        if self._DMv5:
            # assume that it takes about 30 seconds for T83VZV04 to kick out of DM
            self._timeout = 30

    def get_detect_data(self, res):
        com_lgvx8100.Phone.get_detect_data(self, res)
        res[self.esn_file_key]=self.get_esn()

    my_model='VX8300'

    # Fundamentals:
    #  - get_esn             - Brew
    #  - getgroups           - same as LG VX-8100
    #  - getwallpaperindices - LGUncountedIndexedMedia
    #  - getringtoneindices  - LGUncountedIndexedMedia
    #  - DM Version          - 4 to access brew/16452/lk/mr on newer firmwares

parentprofile=com_lgvx8100.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX8300'

    WALLPAPER_WIDTH=275
    WALLPAPER_HEIGHT=175
    MAX_WALLPAPER_BASENAME_LENGTH=32
    WALLPAPER_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_() ."
    WALLPAPER_CONVERT_FORMAT="jpg"

    # the 8300 uses "W" for wait in the dialstring, it does not support "T"
    DIALSTRING_CHARS="[^0-9PW#*]"

    MAX_RINGTONE_BASENAME_LENGTH=32
    RINGTONE_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_() ."

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))
    def GetImageOrigins(self):
        return self.imageorigins

    ringtoneorigins=('ringers', 'sounds', 'mp3')
    excluded_ringtone_origins=('sounds', 'mp3')

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 184, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 96, 'height': 81, 'format': "JPEG"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets

    def QueryAudio(self, origin, currentextension, afi):
        # we don't modify any of these
        if afi.format in ("MIDI", "QCP", "PMD", "WMA"):
            return currentextension, afi
        # examine mp3
        if afi.format=="MP3":
            if afi.channels==1 and 8<=afi.bitrate<=64 and 16000<=afi.samplerate<=22050:
                return currentextension, afi
        # convert it
        return ("mp3", fileinfo.AudioFileInfo(afi, **{'format': 'MP3', 'channels': 1, 'bitrate': 32, 'samplerate': 22050}))

    def __init__(self):
        parentprofile.__init__(self)

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None),         # all SMS list reading
        ('memo', 'read', None),        # all memo list reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
        ('ringtone', 'write', 'OVERWRITE'),
        ('sms', 'write', 'OVERWRITE'),        # all SMS list writing
        ('memo', 'write', 'OVERWRITE'),       # all memo list writing
        )

    field_color_data={
        'phonebook': {
            'name': {
                'first': 1, 'middle': 1, 'last': 1, 'full': 1,
                'nickname': 0, 'details': 1 },
            'number': {
                'type': 5, 'speeddial': 5, 'number': 5, 'details': 5 },
            'email': 2,
            'address': {
                'type': 0, 'company': 0, 'street': 0, 'street2': 0,
                'city': 0, 'state': 0, 'postalcode': 0, 'country': 0,
                'details': 0 },
            'url': 0,
            'memo': 0,
            'category': 1,
            'wallpaper': 0,
            'ringtone': 2,
            'storage': 0,
            },
        'calendar': {
            'description': True, 'location': False, 'allday': False,
            'start': True, 'end': True, 'priority': False,
            'alarm': True, 'vibrate': True,
            'repeat': True,
            'memo': False,
            'category': False,
            'wallpaper': False,
            'ringtone': True,
            },
        'memo': {
            'subject': True,
            'date': True,
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
