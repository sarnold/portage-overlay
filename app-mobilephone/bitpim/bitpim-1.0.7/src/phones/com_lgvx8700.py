#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2007 Nathan Hjelm <hjelmn@users.sourceforge.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

"""
Communicate with the LG VX8700 cell phone
"""

# BitPim modules
import common
import com_phone
import com_brew
import prototypes
import commport
import p_brew
import helpids
import com_lgvx8300
import com_lgvx8500
import p_lgvx8700

DEBUG1=False
#-------------------------------------------------------------------------------
parentphone=com_lgvx8500.Phone
class Phone(com_brew.RealBrewProtocol2, parentphone):
    "Talk to LG VX-8700 cell phone"

    desc="LG-VX8700"
    helpid=helpids.ID_PHONE_LGVX8700
    protocolclass=p_lgvx8700
    serialsname='lgvx8700'

    my_model='VX8700'
    builtinringtones= ('Low Beep Once', 'Low Beeps', 'Loud Beep Once', 'Loud Beeps', 'Door Bell', 'VZW Default Ringtone') + \
                      tuple(['Ringtone '+`n` for n in range(1,12)]) + \
                      ('No Ring',)

    ringtonelocations= (
        # type           index file             default dir                 external dir  max  type   index
        ('ringers',     'dload/myringtone.dat','brew/mod/10889/ringtones', '',            100, 0x01,  100),
	( 'sounds',     'dload/mysound.dat',   'brew/mod/18067',           '',            100, 0x02,  None),
        ( 'sounds(sd)', 'dload/sd_sound.dat',  'mmc1/my_sounds',           '',            100, 0x02,  None),
        ( 'music',      'dload/efs_music.dat', 'my_music',                 '',            100, 0x104, None),
        ( 'music(sd)',  'dload/sd_music.dat',  'mmc1/my_music',            '',            100, 0x14,  None),
        )

    wallpaperlocations= (
        #  type          index file            default dir     external dir  max  type Index
        ( 'images',     'dload/image.dat',    'brew/mod/10888', '',          100, 0x00, 100),
        ( 'images(sd)', 'dload/sd_image.dat', 'mmc1/my_pix',    '',          100, 0x10, None),
        ( 'video',      'dload/video.dat',    'brew/mod/10890', '',          100, 0x03, None),
        ( 'video(sd)',  'dload/sd_video.dat', 'mmc1/my_flix',   '',          100, 0x13, None),
        )


    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)

    def setDMversion(self):
        self._DMv5=True

    # Fundamentals:
    #  - get_esn             - same as LG VX-8300
    #  - getringtoneindices  - LGUncountedIndexedMedia
    #  - getwallpaperindices - LGUncountedIndexedMedia

    # phonebook
    def _update_pb_file(self, pb, fundamentals, pbinfo):
        # update the pbentry file
        update_flg=False
        for e in pb.items:
            _info=pbinfo.get(e.serial1, None)
            if _info:
                wp=_info.get('wallpaper', None)
                if wp is not None and wp!=e.wallpaper:
                    update_flg=True
                    e.wallpaper=wp
        if update_flg:
            self.log('Updating wallpaper index')
            buf=prototypes.buffer()
            pb.writetobuffer(buf, logtitle="Updated index "+self.protocolclass.pb_file_name)
            self.writefile(self.protocolclass.pb_file_name, buf.getvalue())

    def savephonebook(self, data):
        "Saves out the phonebook"
        res=com_lgvx8300.Phone.savephonebook(self, data)
        # retrieve the phonebook entries
        _buf=prototypes.buffer(self.getfilecontents(self.protocolclass.pb_file_name))
        _pb_entries=self.protocolclass.pbfile()
        _pb_entries.readfrombuffer(_buf, logtitle="Read phonebook file "+self.protocolclass.pb_file_name)
        _rt_index=data.get('ringtone-index', {})
        _wp_index=data.get('wallpaper-index', {})
        # update info that the phone software failed to do!!
        self._update_pb_info(_pb_entries, data)
        # fix up ringtone index
        self._write_path_index(_pb_entries, 'ringtone',
                               _rt_index,
                               self.protocolclass.RTPathIndexFile,
                               (0xffff,))
        # fix up wallpaer index
        self._write_path_index(_pb_entries, 'wallpaper',
                               _wp_index,
                               self.protocolclass.WPPathIndexFile,
                               (0, 0xffff,))
        return res

    # groups
    def getgroups(self, results):
        "Read groups"
        # Reads groups that use explicit IDs
        self.log("Reading group information")
        g=self.readobject(self.protocolclass.pb_group_filename,
                          self.protocolclass.pbgroups,
                          'Reading groups data')
        groups={}
        for _group in g.groups:
            if _group.name:
                groups[_group.groupid]= { 'name': _group.name,
                                     'user_added': _group.user_added }
        results['groups'] = groups
        return groups

    def savegroups(self, data):
        groups=data.get('groups', {})
        keys=groups.keys()
        keys.sort()
        keys.reverse()
        g=self.protocolclass.pbgroups()
        # write the No Group entry first
        g.groups.append(self.protocolclass.pbgroup(name='No Group'))
        # now write the rest in reverse ID order
        for k in keys:
            if not k:
                # already wrote this one out
                continue
            g.groups.append(self.protocolclass.pbgroup(name=groups[k]['name'],
                                                       groupid=k,
                                                       user_added=groups[k].get('user_added', 1)))
        self.writeobject(self.protocolclass.pb_group_filename, g,
                         logtitle='Writing phonebook groups',
                         uselocalfs=DEBUG1)

    def listsubdirs(self, dir='', recurse=0):
        return com_brew.RealBrewProtocol2.getfilesystem(self, dir, recurse, directories=1, files=0)


    # ringtones and wallpapers stuff--------------------------------------------
    def savewallpapers(self, results, merge):
        results['rebootphone']=True
        return self.savemedia('wallpapers', 'wallpaper-index',
                              self.wallpaperlocations, results, merge,
                              self.getwallpaperindices, True)
            
    def saveringtones(self, results, merge):
        # Let the phone rebuild the index file, just need to reboot
        results['rebootphone']=True
        return self.savemedia('ringtone', 'ringtone-index',
                              self.ringtonelocations, results, merge,
                              self.getringtoneindices, True)

#-------------------------------------------------------------------------------
parentprofile=com_lgvx8500.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX8700'
    # inside screen resoluation
    WALLPAPER_WIDTH=240
    WALLPAPER_HEIGHT=320

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images(sd)"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "video(sd)"))

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 238, 'height': 246, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 240, 'height': 274, 'format': "JPEG"}))
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
        ('t9_udb', 'write', 'OVERWRITE'),
        )
    if __debug__:
        _supportedsyncs+=(
        ('t9_udb', 'read', 'OVERWRITE'),
        )

    # new group file format requires a new normalization routine
    def normalisegroups(self, helper, data):
        self.normalizegroups(helper, data)

    def normalizegroups(self, helper, data):
        "Assigns groups based on category data"

        pad=[]
        keys=data['groups'].keys()
        keys.sort()
        for k in keys:
            if k: # ignore key 0 which is 'No Group'
                name=data['groups'][k]['name']
                pad.append(name)

        groups=helper.getmostpopularcategories(self.protocolclass.MAX_PHONEBOOK_GROUPS, data['phonebook'], ["No Group"], 32, pad)

        # alpha sort
        groups.sort()

        # newgroups
        newgroups={}

        # put in No group
        newgroups[0]={'name': 'No Group', 'user_added': 0}

        # populate
        for name in groups:
            # existing entries remain unchanged
            if name=="No Group": continue
            key,value=self._getgroup(name, data['groups'])
            if key is not None and key!=0:
                newgroups[key]=value
        # new entries get whatever numbers are free
        for name in groups:
            key,value=self._getgroup(name, newgroups)
            if key is None:
                for key in range(1,100000):
                    if key not in newgroups:
                        newgroups[key]={'name': name, 'user_added': 1}
                        break

        # yay, done
        if data['groups']!=newgroups:
            data['groups']=newgroups
            data['rebootphone']=True
