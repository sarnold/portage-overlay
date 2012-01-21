### BITPIM
###
### Copyright (C) 2005      Bruce Schurmann <austinbp@schurmann.org>
### Copyright (C) 2003-2005 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvx3200.py 3918 2007-01-19 05:15:12Z djpham $

"""Communicate with the LG VX3200 cell phone

The VX3200 is somewhat similar to the VX4400

"""

# standard modules
import time
import cStringIO
import sha
import re

# my modules
import common
import copy
import helpids
import p_lgvx3200
import com_lgvx4400
import com_brew
import com_phone
import com_lg
import prototypes
import phone_media_codec
import conversions

media_codec=phone_media_codec.codec_name


class Phone(com_lgvx4400.Phone):
    "Talk to the LG VX3200 cell phone"

    desc="LG-VX3200"
    helpid=helpids.ID_PHONE_LGVX3200

    wallpaperindexfilename="download/dloadindex/brewImageIndex.map"
    ringerindexfilename="download/dloadindex/brewRingerIndex.map"

    protocolclass=p_lgvx3200
    serialsname='lgvx3200'

    # more VX3200 indices
    imagelocations=(
        # offset, index file, files location, type, maximumentries
        ( 11, "download/dloadindex/brewImageIndex.map", "download", "images", 3) ,
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries
        ( 27, "download/dloadindex/brewRingerIndex.map", "user/sound/ringer", "ringers", 30),
        )


    builtinimages= ('Sport 1', 'Sport 2', 'Nature 1', 'Nature 2',
                    'Animal', 'Martini', 'Goldfish', 'Umbrellas',
                    'Mountain climb', 'Country road')

    # There are a few more builtins but they cannot be sent to the phone in phonebook
    # entries so I am leaving them out.
    builtinringtones= ('Ring 1', 'Ring 2', 'Ring 3', 'Ring 4', 'Ring 5', 'Ring 6',
                       'Ring 7', 'Ring 8', 'Annen Polka', 'Pachelbel Canon', 
                       'Hallelujah', 'La Traviata', 'Leichte Kavallerie Overture', 
                       'Mozart Symphony No.40', 'Bach Minuet', 'Farewell', 
                       'Mozart Piano Sonata', 'Sting', 'O solemio', 
                       'Pizzicata Polka', 'Stars and Stripes Forever', 
                       'Pineapple Rag', 'When the Saints Go Marching In', 'Latin', 
                       'Carol 1', 'Carol 2') 
                       
    def __init__(self, logtarget, commport):
        com_lgvx4400.Phone.__init__(self,logtarget,commport)
        self.mode=self.MODENONE
        self.mediacache=self.DirCache(self)

    def makeentry(self, counter, entry, dict):
        e=com_lgvx4400.Phone.makeentry(self, counter, entry, dict)
        e.entrysize=0x202
        return e

    def getindex(self, indexfile):
        "Read an index file"
        index={}
        # Hack for LG-VX3200 - wallpaper index file is not real
        if re.search("ImageIndex", indexfile) is not None:
            # A little special treatment for wallpaper related media files
            # Sneek a peek at the file because if it is zero len we do not index it
            ind=0
            for ifile in 'wallpaper', 'poweron', 'poweroff':
                ifilefull="download/"+ifile+".bit"
                try:
                    mediafiledata=self.mediacache.readfile(ifilefull)
                    if len(mediafiledata)!=0:
                        index[ind]=ifile
                        ind = ind + 1
                        self.log("Index file "+indexfile+" entry added: "+ifile)
                except:
                    pass
        else:
            # A little special treatment for ringer related media files
            try:
                buf=prototypes.buffer(self.getfilecontents(indexfile))
            except com_brew.BrewNoSuchFileException:
                # file may not exist
                return index
            g=self.protocolclass.indexfile()
            g.readfrombuffer(buf, logtitle="Read index file "+indexfile)
            for i in g.items:
                if i.index!=0xffff:
                    ifile=re.sub("\.mid|\.MID", "", i.name)
                    self.log("Index file "+indexfile+" entry added: "+ifile)
                    index[i.index]=ifile
        return index
        
    def getmedia(self, maps, result, key):
        """Returns the contents of media as a dict where the key is a name as returned
        by getindex, and the value is the contents of the media"""
        media={}
        # the maps
        type=None
        for offset,indexfile,location,type,maxentries in maps:
            index=self.getindex(indexfile)
            for i in index:
                if type=="images":
                    # Wallpaper media files are all BIT type
                    mediafilename=index[i]+".bit"
                else:
                    # Ringer media files are all MID suffixed
                    mediafilename=index[i]+".mid"
                try:
                    media[index[i]]=self.mediacache.readfile(location+"/"+mediafilename)
                except com_brew.BrewNoSuchFileException:
                    self.log("Missing index file: "+location+"/"+mediafilename)
        result[key]=media
        return result

    def savemedia(self, mediakey, mediaindexkey, maps, results, merge, reindexfunction):
        """Actually saves out the media

        @param mediakey: key of the media (eg 'wallpapers' or 'ringtone')
        @param mediaindexkey:  index key (eg 'wallpaper-index')
        @param maps: list index files and locations
        @param results: results dict
        @param merge: are we merging or overwriting what is there?
        @param reindexfunction: the media is re-indexed at the end.  this function is called to do it
        """
        print results.keys()
        # I humbly submit this as the longest function in the bitpim code ...
        # wp and wpi are used as variable names as this function was originally
        # written to do wallpaper.  it works just fine for ringtones as well
        #
        # LG-VX3200 special notes:
        # The index entries for both the wallpaper and ringers are
        # hacked just a bit AND are hacked in slightly different
        # ways. In addition to that the media for the wallpapers is
        # currently in BMP format inside the program and must be
        # converted to BIT (LG proprietary) on the way out.
        #
        # In the following:
        #   wp has file references that nave no suffixes
        #   wpi has file references that are mixed, i.e. some have file suffixes (comes from UI that way)
        wp=results[mediakey].copy()
        wpi=results[mediaindexkey].copy()
        
        # Walk through wp and remove any suffixes that make their way in via the UI
        for k in wp.keys():
            wp[k]['name']=re.sub("\....$", "", wp[k]['name'])
            
        # remove builtins
        for k in wpi.keys():
            if wpi[k]['origin']=='builtin':
                del wpi[k]
                
        # build up list into init
        init={}
        for offset,indexfile,location,type,maxentries in maps:
            init[type]={}
            for k in wpi.keys():
                if wpi[k]['origin']==type:
                    index=k-offset
                    name=wpi[k]['name']
                    data=None
                    del wpi[k]
                    for w in wp.keys():
                        if wp[w]['name']==name and wp[w]['origin']==type:
                            data=wp[w]['data']
                            del wp[w]
                    if not merge and data is None:
                        # delete the entry
                        continue
                    init[type][index]={'name': name, 'data': data}

        # init now contains everything from wallpaper-index
        print init.keys()
        # now look through wallpapers and see if anything remaining was assigned a particular
        # origin
        for w in wp.keys():
            o=wp[w].get("origin", "")
            if o is not None and len(o) and o in init:
                idx=-1
                while idx in init[o]:
                    idx-=1
                init[o][idx]=wp[w]
                del wp[w]
            
        # we now have init[type] with the entries and index number as key (negative indices are
        # unallocated).  Proceed to deal with each one, taking in stuff from wp as we have space
        for offset,indexfile,location,type,maxentries in maps:
            if type=="camera": break
            index=init[type]
            try:
                dirlisting=self.getfilesystem(location)
            except com_brew.BrewNoSuchDirectoryException:
                self.mkdirs(location)
                dirlisting={}
            # rename keys to basename
            for i in dirlisting.keys():
                dirlisting[i[len(location)+1:]]=dirlisting[i]
                del dirlisting[i]
            # what we will be deleting
            dellist=[]
            if not merge:
                # get existing wpi for this location
                wpi=results[mediaindexkey]
                for i in wpi:
                    entry=wpi[i]
                    if entry['origin']==type:
                        # it is in the original index, are we writing it back out?
                        delit=True
                        for idx in index:
                            if index[idx]['name']==entry['name']:
                                delit=False
                                break
                        if delit:
                            # Add the media file suffixes back to match real filenames on phone
                            if type=="ringers":
                                entryname=entry['name']+".mid"
                            else:
                                entryname=entry['name']+".bit"
                            if entryname in dirlisting:
                                dellist.append(entryname)
                            else:
                                self.log("%s in %s index but not filesystem" % (entryname, type))
            # go ahead and delete unwanted files
            print "deleting",dellist
            for f in dellist:
                self.mediacache.rmfile(location+"/"+f)
            # LG-VX3200 special case:
            # We only keep (upload) wallpaper images if there was a legit
            # one on the phone to begin with. This code will weed out any
            # attempts to the contrary.
            if type=="images":
                losem=[]
                # get existing wpi for this location
                wpi=results[mediaindexkey]
                for idx in index:
                    delit=True
                    for i in wpi:
                        entry=wpi[i]
                        if entry['origin']==type:
                            if index[idx]['name']==entry['name']:
                                delit=False
                                break
                    if delit:
                        self.log("Inhibited upload of illegit image (not originally on phone): "+index[idx]['name'])
                        losem.append(idx)
                # Now actually remove any illegit images from upload attempt
                for idx in losem:
                    del index[idx]
            #  slurp up any from wp we can take
            while len(index)<maxentries and len(wp):
                idx=-1
                while idx in index:
                    idx-=1
                k=wp.keys()[0]
                index[idx]=wp[k]
                del wp[k]
            # normalise indices
            index=self._normaliseindices(index)  # hey look, I called a function!
            # move any overflow back into wp
            if len(index)>maxentries:
                keys=index.keys()
                keys.sort()
                for k in keys[maxentries:]:
                    idx=-1
                    while idx in wp:
                        idx-=1
                    wp[idx]=index[k]
                    del index[k]

            # Now add the proper media file suffixes back to the internal index
            # prior to the finish up steps coming
            for k in index.keys():
                if type=="ringers":
                    index[k]['name']=index[k]['name']+".mid"
                else:
                    index[k]['name']=index[k]['name']+".bit"
                    
            # write out the new index
            keys=index.keys()
            keys.sort()
            ifile=self.protocolclass.indexfile()
            ifile.numactiveitems=len(keys)
            for k in keys:
                entry=self.protocolclass.indexentry()
                entry.index=k
                entry.name=index[k]['name']
                ifile.items.append(entry)
            while len(ifile.items)<maxentries:
                ifile.items.append(self.protocolclass.indexentry())
            buffer=prototypes.buffer()
            ifile.writetobuffer(buffer, autolog=False)
            if type!="images":
                # The images index file on the LG-VX3200 is a noop - don't write
                self.logdata("Updated index file "+indexfile, buffer.getvalue(), ifile)
                self.writefile(indexfile, buffer.getvalue())
                
            # Write out files - we compare against existing dir listing and don't rewrite if they
            # are the same size
            for k in keys:
                entry=index[k]
                entryname=entry['name']
                data=entry.get("data", None)
                # Special test for wallpaper files - LG-VX3200 will ONLY accept these files
                if type=="images":
                    if entryname!="wallpaper.bit" and entryname!="poweron.bit" and entryname!="poweroff.bit":
                        self.log("The wallpaper files can only be wallpaper.bmp, poweron.bmp or poweroff.bmp. "+entry['name']+" does not conform - skipping upload.")
                        continue
                if data is None:
                    if entryname not in dirlisting:
                        self.log("Index error.  I have no data for "+entryname+" and it isn't already in the filesystem - skipping upload.")
                    continue
                # Some of the wallpaper media files came here from the UI as BMP files.
                # These need to be converted to LGBIT files on the way out.
                if type=="images" and data[0:2]=="BM":
                    data=conversions.convertbmptolgbit(data)
                    if data is None:
                        self.log("The wallpaper BMP images must be 8BPP or 24BPP, "+entry['name']+", does not comply - skipping upload.")
                        continue
                # Can only upload 128x128 images
                if type=="images" and (common.LSBUint16(data[0:2])!=128 or common.LSBUint16(data[2:4])!=128):
                        self.log("The wallpaper must be 128x128, "+entry['name']+", does not comply - skipping upload.")
                        continue
                # This following test does not apply to wallpaper - it is always the same size on the LG-VX3200!
                if type!="images":
                    if entryname in dirlisting and len(data)==dirlisting[entryname]['size']:
                        self.log("Skipping writing %s/%s as there is already a file of the same length" % (location,entryname))
                        continue
                self.mediacache.writefile(location+"/"+entryname, data)
                self.log("Wrote media file: "+location+"/"+entryname)
        # did we have too many
        if len(wp):
            for k in wp:
                self.log("Unable to put %s on the phone as there weren't any spare index entries" % (wp[k]['name'],))
                
        # Note that we don't write to the camera area

        # tidy up - reread indices
        del results[mediakey] # done with it
        # This excessive and expensive so do not do
        # self.mediacache.flush()
        # self.log("Flushed ringer cache")
        reindexfunction(results)
        return results

    my_model='AX3200'

parentprofile=com_lgvx4400.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='LG Electronics Inc'
    phone_model='VX3200'

    # use for auto-detection
    phone_manufacturer='LG Electronics Inc.'
    phone_model='VX3200 107'

    # no direct usb interface
    usbids=com_lgvx4400.Profile.usbids_usbtoserial

    def convertphonebooktophone(self, helper, data):
        """Converts the data to what will be used by the phone

        @param data: contains the dict returned by getfundamentals
                     as well as where the results go"""
        results={}

        speeds={}

        self.normalisegroups(helper, data)

        for pbentry in data['phonebook']:
            if len(results)==self.protocolclass.NUMPHONEBOOKENTRIES:
                break
            e={} # entry out
            entry=data['phonebook'][pbentry] # entry in
            try:
                # serials
                serial1=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial1', 0)
                serial2=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial2', serial1)

                e['serial1']=serial1
                e['serial2']=serial2
                for ss in entry["serials"]:
                    if ss["sourcetype"]=="bitpim":
                        e['bitpimserial']=ss
                assert e['bitpimserial']

                # name
                e['name']=helper.getfullname(entry.get('names', []),1,1,22)[0]

                # categories/groups
                cat=helper.makeone(helper.getcategory(entry.get('categories', []),0,1,22), None)
                if cat is None:
                    e['group']=0
                else:
                    key,value=self._getgroup(cat, data['groups'])
                    if key is not None:
                        # lgvx3200 fix
                        if key>5:
                            e['group']=0
                            #self.log("Custom Groups in PB not supported - setting to No Group for "+e['name'])
                            print "Custom Groups in PB not supported - setting to No Group for "+e['name']
                        else:
                            e['group']=key
                    else:
                        # sorry no space for this category
                        e['group']=0

                # email addresses
                emails=helper.getemails(entry.get('emails', []) ,0,self.protocolclass.NUMEMAILS,48)
                e['emails']=helper.filllist(emails, self.protocolclass.NUMEMAILS, "")

                # url
                e['url']=helper.makeone(helper.geturls(entry.get('urls', []), 0,1,48), "")

                # memo (-1 is to leave space for null terminator - not all software puts it in, but we do)
                e['memo']=helper.makeone(helper.getmemos(entry.get('memos', []), 0, 1, self.protocolclass.MEMOLENGTH-1), "")

                # phone numbers
                # there must be at least one email address or phonenumber
                minnumbers=1
                if len(emails): minnumbers=0
                numbers=helper.getnumbers(entry.get('numbers', []),minnumbers,self.protocolclass.NUMPHONENUMBERS)
                e['numbertypes']=[]
                e['numbers']=[]
                for numindex in range(len(numbers)):
                    num=numbers[numindex]
                    # deal with type
                    b4=len(e['numbertypes'])
                    type=num['type']
                    for i,t in enumerate(self.protocolclass.numbertypetab):
                        if type==t:
                            # some voodoo to ensure the second home becomes home2
                            if i in e['numbertypes'] and t[-1]!='2':
                                type+='2'
                                continue
                            e['numbertypes'].append(i)
                            break
                        if t=='none': # conveniently last entry
                            e['numbertypes'].append(i)
                            break
                    if len(e['numbertypes'])==b4:
                        # we couldn't find a type for the number
                        continue 
                    # deal with number
                    number=self.phonize(num['number'])
                    if len(number)==0:
                        # no actual digits in the number
                        continue
                    if len(number)>48: # get this number from somewhere sensible
                        # ::TODO:: number is too long and we have to either truncate it or ignore it?
                        number=number[:48] # truncate for moment
                    e['numbers'].append(number)
                    # deal with speed dial
                    sd=num.get("speeddial", -1)
                    if self.protocolclass.NUMSPEEDDIALS:
                        if sd>=self.protocolclass.FIRSTSPEEDDIAL and sd<=self.protocolclass.LASTSPEEDDIAL:
                            speeds[sd]=(e['bitpimserial'], numindex)

                e['numbertypes']=helper.filllist(e['numbertypes'], 5, 0)
                e['numbers']=helper.filllist(e['numbers'], 5, "")

                # ringtones, wallpaper
                # LG VX3200 only supports writing the first 26 builtin ringers in pb
                ecring=helper.getringtone(entry.get('ringtones', []), 'call', None)
                if ecring is not None:
                    if ecring not in Phone.builtinringtones:
                        #self.log("Ringers past Carol 2 in PB not supported - setting to Default Ringer for "+e['name'])
                        print "Ringers past Carol 2 in PB not supported - setting to Default Ringer for "+e['name']+" id was: "+ecring
                        ecring=None
                e['ringtone']=ecring
                emring=helper.getringtone(entry.get('ringtones', []), 'message', None)
                if emring is not None:
                    if emring not in Phone.builtinringtones:
                        #self.log("Ringers past Carol 2 in PB not supported - setting to Default MsgRinger for "+e['name'])
                        print "Ringers past Carol 2 in PB not supported - setting to Default MsgRinger for "+e['name']+" id was: "+emring
                        emring=None
                e['msgringtone']=emring
                # LG VX3200 does not support writing wallpaper in pb
                ewall=helper.getwallpaper(entry.get('wallpapers', []), 'call', None)
                if ewall is not None:
                    #self.log("Custom Wallpapers in PB not supported - setting to Default Wallpaper for "+e['name'])
                    print "Custom Wallpapers in PB not supported - setting to Default Wallpaper for "+e['name']
                e['wallpaper']=None

                # flags
                e['secret']=helper.getflag(entry.get('flags',[]), 'secret', False)

                results[pbentry]=e
                
            except helper.ConversionFailed:
                continue

        if self.protocolclass.NUMSPEEDDIALS:
            data['speeddials']=speeds
        data['phonebook']=results
        return data

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
     #   ('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),   # merge and overwrite wallpaper
        ('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
        ('ringtone', 'write', 'OVERWRITE'),
        ('call_history', 'read', None),
        ('memo', 'read', None),     # all memo list reading DJP
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing DJP
        ('sms', 'read', None),
        ('sms', 'write', 'OVERWRITE'),
        )

    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=128
    MAX_WALLPAPER_BASENAME_LENGTH=19
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ."
    WALLPAPER_CONVERT_FORMAT="bmp"

    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvxwyz0123456789 ."

    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))

    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 128, 'height': 128, 'format': "BMP"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets
    
    def __init__(self):
        parentprofile.__init__(self)


