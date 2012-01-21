#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2008 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx9700.py 4678 2008-08-13 23:46:56Z djpham $



"""
Communicate with the LG VX9700 cell phone.
"""

# BitPim modules
import common
import com_brew
import prototypes
import com_lgvx10000
import p_lgvx9700
import helpids
import sms

#-------------------------------------------------------------------------------
parentphone=com_lgvx10000.Phone
class Phone(parentphone):
    desc="LG-VX9700 (Dare)"
    helpid=helpids.ID_PHONE_LGVX9700
    protocolclass=p_lgvx9700
    serialsname='lgvx9700'

    my_model='VX9700'
    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'VZW Default Ringtone',
                       'Home Phone', 'Simple Beep', 'Short Note Beep', 'Old Bell', 'Move Bell', 'Wahwah',
                       'Just Fine', 'Froggy Night', 'Whistling Wizard', 'Like a Movie', 'Deep Blue Sea',
                       'Sweet & Twenty', 'Funky Band', 'Why Not', 'Mystique', 'Evening Grow', 'This Time',
                       'Hawaiian Punch', 'L.O.V.E.', 'Night Sky', 'No Ring',)

    def setDMversion(self):
        self._DMv5=False
        self._DMv6=True
        self._timeout=5 # Assume a quick timeout on newer phones

    # Fundamentals:
    #  - get_esn             - same as LG VX-8300
    #  - getgroups           - same as LG VX-8700
    #  - getwallpaperindices - LGUncountedIndexedMedia
    #  - getringtoneindices  - LGUncountedIndexedMedia
    #  - DM Version          - 6
    #  - phonebook           - same as LG VX-8550
    #  - SMS                 - same dir structure as the VX-8800

    def _getoutboxmessage(self, sf):
        entry=sms.SMSEntry()
        entry.folder=entry.Folder_Sent
        entry.datetime="%d%02d%02dT%02d%02d%02d" % ((sf.timesent))
        # add all the recipients
        for r in sf.recipients:
            if r.number:
                confirmed=(r.status==5)
                confirmed_date=None
                if confirmed:
                    confirmed_date="%d%02d%02dT%02d%02d%02d" % r.timereceived
                entry.add_recipient(r.number, confirmed, confirmed_date)
        entry.subject=sf.subject
        txt=""
        if sf.num_msg_elements==1 and not sf.messages[0].binary:
            txt=self._get_text_from_sms_msg_without_header(sf.messages[0].msg, sf.messages[0].length)
        else:
            for i in range(sf.num_msg_elements):
                txt+=self._get_text_from_sms_msg_with_header(sf.messages[i].msg, sf.messages[i].length)
        entry.text=unicode(txt, errors='ignore')
        if sf.priority==0:
            entry.priority=sms.SMSEntry.Priority_Normal
        else:
            entry.priority=sms.SMSEntry.Priority_High
        entry.locked=sf.locked
        entry.callback=sf.callback
        return entry

    def _getinboxmessage(self, sf):
        entry=sms.SMSEntry()
        entry.folder=entry.Folder_Inbox
        entry.datetime="%d%02d%02dT%02d%02d%02d" % (sf.GPStime)
        entry._from=sf.sender if sf.sender else sf.sender_name
        entry.subject=sf.subject
        entry.locked=sf.locked
        if sf.priority==0:
            entry.priority=sms.SMSEntry.Priority_Normal
        else:
            entry.priority=sms.SMSEntry.Priority_High
        entry.read=sf.read
        txt=""
        _decode_func=self._get_text_from_sms_msg_with_header if \
                      sf.msgs[1].msg_length else \
                      self._get_text_from_sms_msg_without_header
        for _entry in sf.msgs:
            if _entry.msg_length:
                txt+=_decode_func(_entry.msg_data.msg, _entry.msg_length)
        entry.text=unicode(txt, errors='ignore')
        entry.callback=sf.callback
        return entry

#-------------------------------------------------------------------------------
parentprofile=com_lgvx10000.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX9700'
    # inside screen resoluation
    WALLPAPER_WIDTH  = 400
    WALLPAPER_HEIGHT = 240

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 240, 'height': 400, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 400, 'height': 240, 'format': "JPEG"}))
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
