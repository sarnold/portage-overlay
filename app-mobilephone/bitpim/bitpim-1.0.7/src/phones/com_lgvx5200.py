### BITPIM
###
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2005 Simon Capper <skyjunky@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx5200.py 4303 2007-07-13 20:46:53Z djpham $

"""Communicate with the LG VX5200 cell phone


The code in this file mainly inherits from VX8100 code and then extends where
the 5200 has different functionality

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
import p_lgvx5200
import com_lgvx8100
import com_brew
import com_phone
import com_lg
import prototypes
import bpcalendar
import call_history
import sms
import memo
import helpids

class Phone(com_lgvx8100.Phone):
    "Talk to the LG VX5200 cell phone"

    desc="LG-VX5200"
    helpid=helpids.ID_PHONE_LGVX5200
    protocolclass=p_lgvx5200
    serialsname='lgvx5200'

    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'VZW Default Ringtone') + \
                      tuple(['Ringtone '+`n` for n in range(1,11)]) + \
                      ('No Ring',)

    ringtonelocations= (
        # type       index-file   size-file directory-to-use lowest-index-to-use maximum-entries type-major icon idx_offset
        ( 'ringers', 'dload/ringtone.dat', '', 'user/sound/ringer', 100, 150, 0x201, 1, 0),
        ( 'sounds', 'dload/sound.dat', 'dload/soundsize.dat', 'dload/snd', 100, 150, 0x402, 0, 151),
        )

    calendarlocation="sch/schedule.dat"
    calendarexceptionlocation="sch/schexception.dat"
    calenderrequiresreboot=1
    memolocation="sch/memo.dat"

    builtinwallpapers = () # none

    wallpaperlocations= (
        ( 'images', 'dload/image.dat', 'dload/imagesize.dat', 'dload/img', 100, 50, 0, 0, 0),
        )
    
    def __init__(self, logtarget, commport):
        com_lgvx4400.Phone.__init__(self,logtarget,commport)
        self.mode=self.MODENONE

    def __del__(self):
        pass

    my_model='VX5200'

    # Media stuff---------------------------------------------------------------
    # Bypassing the 8100/9800 specific stuff
    def getmedia(self, maps, results, key):
        return com_lg.LGNewIndexedMedia2.getmedia(self, maps, results, key)
    def savemedia(self, mediakey, mediaindexkey, maps, results, merge, reindexfunction):
        return com_lg.LGNewIndexedMedia2.savemedia(self, mediakey, mediaindexkey, maps, results, merge, reindexfunction)

parentprofile=com_lgvx8100.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX5200'

    WALLPAPER_WIDTH=275
    WALLPAPER_HEIGHT=175
    MAX_WALLPAPER_BASENAME_LENGTH=32
    WALLPAPER_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_() ."
    WALLPAPER_CONVERT_FORMAT="jpg"
   
    # the 5200 uses "W" for wait in the dialstring, it does not support "T"
    DIALSTRING_CHARS="[^0-9PW#*]"

    MAX_RINGTONE_BASENAME_LENGTH=32
    RINGTONE_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_() ."

    # the 5200 doesn't have seperate origins - they are all dumped in "images"
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    def GetImageOrigins(self):
        return self.imageorigins

    ringtoneorigins=('ringers', 'sounds')
    excluded_ringtone_origins=('sounds')

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 275, 'height': 175, 'format': "JPEG"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets

 
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
