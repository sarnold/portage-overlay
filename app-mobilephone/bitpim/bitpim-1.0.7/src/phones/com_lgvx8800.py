#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2007 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
### $Id: com_lgvx8800.py 4671 2008-08-11 21:20:21Z djpham $


"""
Communicate with the LG VX8800 cell phone.
"""

# BitPim modules
import common
import com_brew
import prototypes
import com_lgvx8550
import p_lgvx8800
import helpids

#-------------------------------------------------------------------------------
parentphone=com_lgvx8550.Phone
class Phone(parentphone):
    desc="LG-VX8800"
    helpid=helpids.ID_PHONE_LGVX8800
    protocolclass=p_lgvx8800
    serialsname='lgvx8800'

    my_model='VX8800'

    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'Door Bell', 'VZW Default Ringtone') + \
                      tuple(['Ringtone '+`n` for n in range(1,20)]) + \
                      ('No Ring',)

    def setDMversion(self):
        self._DMv6=True
        self._DMv5=False
        self._timeout=5 # The Voyager/Venus time out fast

    # Fundamentals:
    #  - get_esn             - same as LG VX-8300
    #  - getgroups           - same as LG VX-8700
    #  - getwallpaperindices - LGUncountedIndexedMedia
    #  - getringtoneindices  - LGUncountedIndexedMedia
    #  - DM Version          - 5
    #  - phonebook           - same as LG VX-8550

    def _readsms(self):
        res={}
        # The Voyager and Venus use index files to keep track of SMS messages
        for item in self.getindex(self.protocolclass.drafts_index):
                buf=prototypes.buffer(self.getfilecontents(item.filename, True))
                self.logdata("SMS message file " +item.filename, buf.getdata())
                sf=self.protocolclass.sms_saved()
                sf.readfrombuffer(buf, logtitle="SMS saved item")
                entry=self._getoutboxmessage(sf.outbox)
                entry.folder=entry.Folder_Saved
                res[entry.id]=entry
        for item in self.getindex(self.protocolclass.inbox_index):
                buf=prototypes.buffer(self.getfilecontents(item.filename, True))
                self.logdata("SMS message file " +item.filename, buf.getdata())
                sf=self.protocolclass.sms_in()
                sf.readfrombuffer(buf, logtitle="SMS inbox item")
                entry=self._getinboxmessage(sf)
                res[entry.id]=entry
        for item in self.getindex(self.protocolclass.outbox_index):
                buf=prototypes.buffer(self.getfilecontents(item.filename, True))
                self.logdata("SMS message file " +item.filename, buf.getdata())
                sf=self.protocolclass.sms_out()
                sf.readfrombuffer(buf, logtitle="SMS sent item")
                entry=self._getoutboxmessage(sf)
                res[entry.id]=entry
        return res 

    def _scheduleextras(self, data, fwversion):
        data.serial_number = '000000cc-00000000-00000000-' + fwversion
        data.unknown3 = 0x00f9

#-------------------------------------------------------------------------------
parentprofile=com_lgvx8550.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX8800'
    # inside screen resoluation
    WALLPAPER_WIDTH  = 240
    WALLPAPER_HEIGHT = 320
    
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 240, 'height': 320, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 240, 'height': 496, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 120, 'height': 100, 'format': "JPEG"}))

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
##        ('playlist', 'read', 'OVERWRITE'),
##        ('playlist', 'write', 'OVERWRITE'),
        ('t9_udb', 'write', 'OVERWRITE'),
        )
    if __debug__:
        _supportedsyncs+=(
        ('t9_udb', 'read', 'OVERWRITE'),
        )
