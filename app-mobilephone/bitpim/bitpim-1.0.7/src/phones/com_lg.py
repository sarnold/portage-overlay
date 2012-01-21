### BITPIM
###
### Copyright (C) 2003-2006 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2006 Michael Cohen <mikepublic@nc.rr.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lg.py 4680 2008-08-14 22:40:38Z djpham $

"""Phonebook conversations with LG phones"""

import functools
import threading

import com_brew
import com_phone
import p_lg
import prototypes
import common
import struct

class LGPhonebook:

    pbterminator="\x7e"
    MODEPHONEBOOK="modephonebook" # can speak the phonebook protocol

    def __init__(self):
        self.pbseq=0
    
    def _setmodelgdmgo(self):
        # see if we can turn on dm mode
        for baud in (0, 115200, 19200, 38400, 230400):
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            try:
                self.comm.write("AT$LGDMGO\r\n")
            except:
                self.mode=self.MODENONE
                self.comm.shouldloop=True
                raise
            try:
                if self.comm.readsome().find("OK")>=0:
                    return True
            except com_phone.modeignoreerrortypes:
                self.log("No response to setting DM mode")
        return False
        

    def _setmodephonebook(self):
        req=p_lg.pbinitrequest()
        respc=p_lg.pbinitresponse

        for baud in 0,38400,115200,230400,19200:
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            try:
                self.sendpbcommand(req, respc, callsetmode=False)
                return True
            except com_phone.modeignoreerrortypes:
                pass

        self._setmodelgdmgo()

        for baud in 0,38400,115200:
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            try:
                self.sendpbcommand(req, respc, callsetmode=False)
                return True
            except com_phone.modeignoreerrortypes:
                pass
        return False
        
    def sendpbcommand(self, request, responseclass, callsetmode=True):
        if callsetmode:
            self.setmode(self.MODEPHONEBOOK)
        buffer=prototypes.buffer()
        request.header.sequence=self.pbseq
        self.pbseq+=1
        if self.pbseq>0xff:
            self.pbseq=0
        request.writetobuffer(buffer, logtitle="lg phonebook request")
        data=buffer.getvalue()
        data=common.pppescape(data+common.crcs(data))+common.pppterminator
        firsttwo=data[:2]
        try:
            data=self.comm.writethenreaduntil(data, False, common.pppterminator, logreaduntilsuccess=False)
        except com_phone.modeignoreerrortypes:
            self.mode=self.MODENONE
            self.raisecommsdnaexception("manipulating the phonebook")
        self.comm.success=True

        origdata=data
        # sometimes there is junk at the begining, eg if the user
        # turned off the phone and back on again.  So if there is more
        # than one 7e in the escaped data we should start after the
        # second to last one
        d=data.rfind(common.pppterminator,0,-1)
        if d>=0:
            self.log("Multiple LG packets in data - taking last one starting at "+`d+1`)
            self.logdata("Original LG data", origdata, None)
            data=data[d+1:]

        # turn it back to normal
        data=common.pppunescape(data)

        # take off crc and terminator
        crc=data[-3:-1]
        data=data[:-3]
        # check the CRC at this point to see if we might have crap at the beginning
        calccrc=common.crcs(data)
        if calccrc!=crc:
            # sometimes there is other crap at the begining
            d=data.find(firsttwo)
            if d>0:
                self.log("Junk at begining of LG packet, data at "+`d`)
                self.logdata("Original LG data", origdata, None)
                self.logdata("Working on LG data", data, None)
                data=data[d:]
                # recalculate CRC without the crap
                calccrc=common.crcs(data)
            # see if the crc matches now
            if calccrc!=crc:
                self.logdata("Original LG data", origdata, None)
                self.logdata("Working on LG data", data, None)
                raise common.CommsDataCorruption("LG packet failed CRC check", self.desc)

        # phone will respond with 0x13 and 0x14 if we send a bad or malformed command        
        if ord(data[0])==0x13:
            raise com_brew.BrewBadBrewCommandException()
        if ord(data[0])==0x14:
            raise com_brew.BrewMalformedBrewCommandException()

        # parse data
        buffer=prototypes.buffer(data)
        res=responseclass()
        res.readfrombuffer(buffer, logtitle="lg phonebook response")
        return res

def cleanupstring(str):
    str=str.replace("\r", "\n")
    str=str.replace("\n\n", "\n")
    str=str.strip()
    return str.split("\n")

class LGIndexedMedia:
    "Implements media for LG phones that use index files"
    
    def __init__(self):
        pass

    def getwallpapers(self, result):
        return self.getmedia(self.imagelocations, result, 'wallpapers')

    def getringtones(self, result):
        return self.getmedia(self.ringtonelocations, result, 'ringtone')

    def savewallpapers(self, results, merge):
        return self.savemedia('wallpapers', 'wallpaper-index', self.imagelocations, results, merge, self.getwallpaperindices)

    def saveringtones(self, results, merge):
        return self.savemedia('ringtone', 'ringtone-index', self.ringtonelocations, results, merge, self.getringtoneindices)

    def getmediaindex(self, builtins, maps, results, key):
        """Gets the media (wallpaper/ringtone) index

        @param builtins: the builtin list on the phone
        @param results: places results in this dict
        @param maps: the list of index files and locations
        @param key: key to place results in
        """

        self.log("Reading "+key)
        media={}

        # builtins
        c=1
        for name in builtins:
            media[c]={'name': name, 'origin': 'builtin' }
            c+=1

        # the maps
        type=None
        for offset,indexfile,location,type,maxentries in maps:
            if type=="camera": break
            index=self.getindex(indexfile)
            for i in index:
                media[i+offset]={'name': index[i], 'origin': type}

        # camera must be last
        if type=="camera":
            index=self.getcameraindex()
            for i in index:
                media[i+offset]=index[i]

        results[key]=media
        return media

    def getindex(self, indexfile):
        "Read an index file"
        index={}
        try:
            buf=prototypes.buffer(self.getfilecontents(indexfile))
        except com_brew.BrewNoSuchFileException:
            # file may not exist
            return index
        g=self.protocolclass.indexfile()
        g.readfrombuffer(buf, logtitle="Index file %s read" % (indexfile,))
        for i in g.items:
            if i.index!=0xffff and len(i.name):
                index[i.index]=i.name
        return index
        
    def getmedia(self, maps, result, key):
        """Returns the contents of media as a dict where the key is a name as returned
        by getindex, and the value is the contents of the media"""
        media={}
        # the maps
        type=None
        for offset,indexfile,location,type,maxentries in maps:
            if type=="camera": break
            index=self.getindex(indexfile)
            for i in index:
                try:
                    media[index[i]]=self.getfilecontents(location+"/"+index[i], True)
                except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException,com_brew.BrewNameTooLongException):
                    self.log("It was in the index, but not on the filesystem")
                    
        if type=="camera":
            # now for the camera stuff
            index=self.getcameraindex()
            for i in index:
                try:
                    media[index[i]['name']]=self.getfilecontents("cam/pic%02d.jpg" % (i,), True)
                except com_brew.BrewNoSuchFileException:
                    self.log("It was in the index, but not on the filesystem")
                    
        result[key]=media
        return result

    def savemedia(self, mediakey, mediaindexkey, maps, results, merge, reindexfunction):
        """Actually saves out the media

        @param mediakey: key of the media (eg 'wallpapers' or 'ringtones')
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
        wp=results[mediakey].copy()
        wpi=results[mediaindexkey].copy()
        # remove builtins
        for k in wpi.keys():
            if wpi[k]['origin']=='builtin':
                del wpi[k]

        # sort results['mediakey'+'-index'] into origin buckets

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
                            if entry['name'] in dirlisting:
                                dellist.append(entry['name'])
                            else:
                                self.log("%s in %s index but not filesystem" % (entry['name'], type))
            # go ahead and delete unwanted files
            print "deleting",dellist
            for f in dellist:
                self.rmfile(location+"/"+f)
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
            ifile.writetobuffer(buffer, logtitle="Updated index file "+indexfile)
            self.writefile(indexfile, buffer.getvalue())
            # Write out files - we compare against existing dir listing and don't rewrite if they
            # are the same size
            for k in keys:
                entry=index[k]
                data=entry.get("data", None)
                if data is None:
                    if entry['name'] not in dirlisting:
                        self.log("Index error.  I have no data for "+entry['name']+" and it isn't already in the filesystem")
                    continue
                if entry['name'] in dirlisting and len(data)==dirlisting[entry['name']]['size']:
                    self.log("Skipping writing %s/%s as there is already a file of the same length" % (location,entry['name']))
                    continue
                self.writefile(location+"/"+entry['name'], data)
        # did we have too many
        if len(wp):
            for k in wp:
                self.log("Unable to put %s on the phone as there weren't any spare index entries" % (wp[k]['name'],))
                
        # Note that we don't write to the camera area

        # tidy up - reread indices
        del results[mediakey] # done with it
        reindexfunction(results)
        return results

class LGNewIndexedMedia:
    "Implements media for LG phones that use the new index format such as the VX7000/8000"

    # tables for minor type number
    _minor_typemap={
        0: {  # images
        ".jpg": 3,
        ".bmp": 1,
        },

        1: { # audio
        ".qcp": 5,
        ".mid": 4,
        },

        2: { # video
        ".3g2": 3,
        }
    }
        
    
    def __init__(self):
        pass

    def getmediaindex(self, builtins, maps, results, key):
        """Gets the media (wallpaper/ringtone) index

        @param builtins: the builtin list on the phone
        @param results: places results in this dict
        @param maps: the list of index files and locations
        @param key: key to place results in
        """

        self.log("Reading "+key)
        media={}

        # builtins
        for i,n in enumerate(builtins): # nb zero based index whereas previous phones used 1
            media[i]={'name': n, 'origin': 'builtin'}

        # maps
        for type, indexfile, sizefile, directory, lowestindex, maxentries, typemajor  in maps:
            for item in self.getindex(indexfile):
                if item.type&0xff!=typemajor:
                    self.log("Entry "+item.filename+" has wrong type for this index.  It is %d and should be %d" % (item.type&0xff, typemajor))
                    self.log("This is going to cause you all sorts of problems.")
                media[item.index]={
                    'name': basename(item.filename),
                    'filename': item.filename,
                    'origin': type,
                    'vtype': item.type,
                    }
                if item.date!=0:
                    media[item.index]['date']=item.date

        # finish
        results[key]=media

    def getindex(self, filename):
        "read an index file"
        try:
            buf=prototypes.buffer(self.getfilecontents(filename))
        except com_brew.BrewNoSuchFileException:
            return []

        g=self.protocolclass.indexfile()
        # some media indexes have crap appended to the end, prevent this error from messing up everything
        # valid entries at the start of the file will still get read OK. 
        try:
            g.readfrombuffer(buf, logtitle="Index file "+filename)
        except:
            self.log("Corrupt index file "+`filename`+", this might cause you all sorts of problems.")
        return g.items

    def getmedia(self, maps, results, key):
        origins={}
        # signal that we are using the new media storage that includes the origin and timestamp
        origins['new_media_version']=1

        for type, indexfile, sizefile, directory, lowestindex, maxentries, typemajor  in maps:
            media={}
            for item in self.getindex(indexfile):
                data=None
                timestamp=None
                try:
                    stat_res=self.statfile(item.filename)
                    if stat_res!=None:
                        timestamp=stat_res['date'][0]
                    data=self.getfilecontents(item.filename, True)
                except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException,com_brew.BrewNameTooLongException):
                    self.log("It was in the index, but not on the filesystem")
                if data!=None:
                    media[common.basename(item.filename)]={ 'data': data, 'timestamp': timestamp}
            origins[type]=media

        results[key]=origins
        return results

    def savemedia(self, mediakey, mediaindexkey, maps, results, merge, reindexfunction):
        """Actually saves out the media

        @param mediakey: key of the media (eg 'wallpapers' or 'ringtones')
        @param mediaindexkey:  index key (eg 'wallpaper-index')
        @param maps: list index files and locations
        @param results: results dict
        @param merge: are we merging or overwriting what is there?
        @param reindexfunction: the media is re-indexed at the end.  this function is called to do it
        """

        # take copies of the lists as we modify them
        wp=results[mediakey].copy()  # the media we want to save
        wpi=results[mediaindexkey].copy() # what is already in the index files

        # remove builtins
        for k in wpi.keys():
            if wpi[k].get('origin', "")=='builtin':
                del wpi[k]

        # build up list into init
        init={}
        for type,_,_,_,lowestindex,_,typemajor in maps:
            init[type]={}
            for k in wpi.keys():
                if wpi[k]['origin']==type:
                    index=k
                    name=wpi[k]['name']
                    fullname=wpi[k]['filename']
                    vtype=wpi[k]['vtype']
                    data=None
                    del wpi[k]
                    for w in wp.keys():
                        # does wp contain a reference to this same item?
                        if wp[w]['name']==name and wp[w]['origin']==type:
                            data=wp[w]['data']
                            del wp[w]
                    if not merge and data is None:
                        # delete the entry
                        continue
                    assert index>=lowestindex
                    init[type][index]={'name': name, 'data': data, 'filename': fullname, 'vtype': vtype}

        # init now contains everything from wallpaper-index
        # wp contains items that we still need to add, and weren't in the existing index
        assert len(wpi)==0
        print init.keys()
        
        # now look through wallpapers and see if anything was assigned a particular
        # origin
        for w in wp.keys():
            o=wp[w].get("origin", "")
            if o is not None and len(o) and o in init:
                idx=-1
                while idx in init[o]:
                    idx-=1
                init[o][idx]=wp[w]
                del wp[w]

        # wp will now consist of items that weren't assigned any particular place
        # so put them in the first available space
        for type,_,_,_,lowestindex,maxentries,typemajor in maps:
            # fill it up
            for w in wp.keys():
                if len(init[type])>=maxentries:
                    break
                idx=-1
                while idx in init[type]:
                    idx-=1
                init[type][idx]=wp[w]
                del wp[w]

        # time to write the files out
        dircache=self.DirCache(self)
        for type, indexfile, sizefile, directory, lowestindex, maxentries,typemajor  in maps:
            # get the index file so we can work out what to delete
            names=[init[type][x]['name'] for x in init[type]]
            for item in self.getindex(indexfile):
                if basename(item.filename) not in names:
                    self.log(item.filename+" is being deleted")
                    try:
                        dircache.rmfile(item.filename)
                    except com_brew.BrewNoSuchFileException:
                        self.log("Hmm, it didn't exist!")
            # fixup the indices
            fixups=[k for k in init[type].keys() if k<lowestindex]
            fixups.sort()
            for f in fixups:
                for ii in xrange(lowestindex, lowestindex+maxentries):
                    # allocate an index
                    if ii not in init[type]:
                        init[type][ii]=init[type][f]
                        del init[type][f]
                        break
            # any left over?
            fixups=[k for k in init[type].keys() if k<lowestindex]
            for f in fixups:
                self.log("There is no space in the index for "+type+" for "+init[type][f]['name'])
                del init[type][f]
            # write each entry out
            for idx in init[type].keys():
                entry=init[type][idx]
                filename=entry.get('filename', directory+"/"+entry['name'])
                entry['filename']=filename
                fstat=dircache.stat(filename)
                if 'data' not in entry:
                    # must be in the filesystem already
                    if fstat is None:
                        self.log("Entry "+entry['name']+" is in index "+indexfile+" but there is no data for it and it isn't in the filesystem.  The index entry will be removed.")
                        del init[type][idx]
                        continue
                # check len(data) against fstat->length
                data=entry['data']
                if data is None:
                    assert merge 
                    continue # we are doing an add and don't have data for this existing entry
                if fstat is not None and len(data)==fstat['size']:
                    self.log("Not writing "+filename+" as a file of the same name and length already exists.")
                else:
                    dircache.writefile(filename, data)
            # write out index
            ifile=self.protocolclass.indexfile()
            idxlist=init[type].keys()
            idxlist.sort()
            idxlist.reverse() # the phone has them in reverse order for some reason so we do the same
            for idx in idxlist:
                ie=self.protocolclass.indexentry()
                ie.index=idx
                vtype=init[type][idx].get("vtype", None)
                if vtype is None:
                    vtype=self._guessvtype(init[type][idx]['filename'], typemajor)
                    print "guessed vtype of "+`vtype`+" for "+init[type][idx]['filename']
                else:
                    print init[type][idx]['filename']+" already had a vtype of "+`vtype`
                ie.type=vtype
                ie.filename=init[type][idx]['filename']
                # ie.date left as zero
                ie.dunno=0 # mmmm
                ifile.items.append(ie)
            buf=prototypes.buffer()
            ifile.writetobuffer(buf, logtitle="Index file "+indexfile)
            self.log("Writing index file "+indexfile+" for type "+type+" with "+`len(idxlist)`+" entries.")
            dircache.writefile(indexfile, buf.getvalue()) # doesn't really need to go via dircache
            # write out size file
            size=0
            for idx in idxlist:
                fstat=dircache.stat(init[type][idx]['filename'])
                size+=fstat['size']
            szfile=self.protocolclass.sizefile()
            szfile.size=size
            buf=prototypes.buffer()
            szfile.writetobuffer(buf, logtitle="size file for "+type)
            self.log("You are using a total of "+`size`+" bytes for "+type)
            dircache.writefile(sizefile, buf.getvalue())
        return reindexfunction(results)
                            
    def _guessvtype(self, filename, typemajor):
        lookin=self._minor_typemap[typemajor]
        for ext,val in lookin.items():
            if filename.lower().endswith(ext):
                return typemajor+(256*val)
        return typemajor # implicit val of zero

    def getwallpaperindices(self, results):
        return self.getmediaindex(self.builtinwallpapers, self.wallpaperlocations, results, 'wallpaper-index')

    def getringtoneindices(self, results):
        return self.getmediaindex(self.builtinringtones, self.ringtonelocations, results, 'ringtone-index')

    def getwallpapers(self, result):
        return self.getmedia(self.wallpaperlocations, result, 'wallpapers')

    def getringtones(self, result):
        return self.getmedia(self.ringtonelocations, result, 'ringtone')

    def savewallpapers(self, results, merge):
        return self.savemedia('wallpapers', 'wallpaper-index', self.wallpaperlocations, results, merge, self.getwallpaperindices)
            
    def saveringtones(self, results, merge):
        return self.savemedia('ringtone', 'ringtone-index', self.ringtonelocations, results, merge, self.getringtoneindices)

class LGNewIndexedMedia2(LGNewIndexedMedia):
    """Implements media for LG phones that use the newer index format such as the VX8100/5200
    Similar ot the other new media type hence the subclassing, but the type field in the
    PACKET has a different meaning so different code is required and it has support for an icon
    field that affects whcih icon is displayed next to the tone on the phone
    """

    # tables for minor type number
    _minor_typemap={
        ".jpg": 3,
        ".bmp": 1,
        ".qcp": 5,
        ".mid": 4,
        ".3g2": 3,
        }

    def _guessvtype(self, filename, typemajor):
        if typemajor > 2: # some index files are hard coded
            return typemajor
        for ext,val in self._minor_typemap.items():
            if filename.lower().endswith(ext):
                return typemajor+(256*val)
        return typemajor # implicit val of zero

    def getmediaindex(self, builtins, maps, results, key):
        """Gets the media (wallpaper/ringtone) index

        @param builtins: the builtin list on the phone
        @param results: places results in this dict
        @param maps: the list of index files and locations
        @param key: key to place results in
        """

        self.log("Reading "+key)
        media={}

        # builtins
        for i,n in enumerate(builtins): # nb zero based index whereas previous phones used 1
            media[i]={'name': n, 'origin': 'builtin'}

        # maps
        for type, indexfile, sizefile, directory, lowestindex, maxentries, typemajor, def_icon, idx_ofs  in maps:
            for item in self.getindex(indexfile):
                if item.type&0xff!=typemajor&0xff:
                    self.log("Entry "+item.filename+" has wrong type for this index.  It is %d and should be %d" % (item.type&0xff, typemajor))
                    self.log("This is going to cause you all sorts of problems.")
                _idx=item.index+idx_ofs
                media[_idx]={
                    'name': basename(item.filename),
                    'filename': item.filename,
                    'origin': type,
                    'vtype': item.type,
                    'icon': item.icon
                    }
                if item.date!=0:
                    media[_idx]['date']=item.date

        # finish
        results[key]=media

    def getmedia(self, maps, results, key):
        origins={}
        # signal that we are using the new media storage that includes the origin and timestamp
        origins['new_media_version']=1

        for type, indexfile, sizefile, directory, lowestindex, maxentries, typemajor, def_icon, idx_ofs  in maps:
            media={}
            for item in self.getindex(indexfile):
                data=None
                timestamp=None
                try:
                    stat_res=self.statfile(item.filename)
                    if stat_res!=None:
                        timestamp=stat_res['date'][0]
                    data=self.getfilecontents(item.filename, True)
                except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException,com_brew.BrewNameTooLongException):
                    self.log("It was in the index, but not on the filesystem")
                except com_brew.BrewAccessDeniedException:
                    # firmware wouldn't let us read this file, just mark it then
                    self.log('Failed to read file: '+item.filename)
                    data=''
                if data!=None:
                    media[common.basename(item.filename)]={ 'data': data, 'timestamp': timestamp}
            origins[type]=media

        results[key]=origins
        return results

    def getmedia(self, maps, results, key):
        media={}

        for type, indexfile, sizefile, directory, lowestindex, maxentries, typemajor, def_icon, idx_ofs in maps:
            for item in self.getindex(indexfile):
                try:
                    media[basename(item.filename)]=self.getfilecontents(item.filename,
                                                                        True)
                except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException,com_brew.BrewNameTooLongException):
                    self.log("It was in the index, but not on the filesystem")

        results[key]=media
        return results
        
    def savemedia(self, mediakey, mediaindexkey, maps, results, merge, reindexfunction):
        """Actually saves out the media

        @param mediakey: key of the media (eg 'wallpapers' or 'ringtones')
        @param mediaindexkey:  index key (eg 'wallpaper-index')
        @param maps: list index files and locations
        @param results: results dict
        @param merge: are we merging or overwriting what is there?
        @param reindexfunction: the media is re-indexed at the end.  this function is called to do it
        """

        # take copies of the lists as we modify them
        wp=results[mediakey].copy()  # the media we want to save
        wpi=results[mediaindexkey].copy() # what is already in the index files

        # remove builtins
        for k in wpi.keys():
            if wpi[k].get('origin', "")=='builtin':
                del wpi[k]

        # build up list into init
        init={}
        for type,_,_,_,lowestindex,_,typemajor,_,idx_ofs in maps:
            init[type]={}
            for k in wpi.keys():
                if wpi[k]['origin']==type:
                    index=k-idx_ofs
                    name=wpi[k]['name']
                    fullname=wpi[k]['filename']
                    vtype=wpi[k]['vtype']
                    icon=wpi[k]['icon']
                    data=None
                    del wpi[k]
                    for w in wp.keys():
                        # does wp contain a reference to this same item?
                        if wp[w]['name']==name and wp[w]['origin']==type:
                            data=wp[w]['data']
                            del wp[w]
                    if not merge and data is None:
                        # delete the entry
                        continue
                    assert index>=lowestindex
                    init[type][index]={'name': name, 'data': data, 'filename': fullname, 'vtype': vtype, 'icon': icon}

        # init now contains everything from wallpaper-index
        # wp contains items that we still need to add, and weren't in the existing index
        assert len(wpi)==0
        print init.keys()
        
        # now look through wallpapers and see if anything was assigned a particular
        # origin
        for w in wp.keys():
            o=wp[w].get("origin", "")
            if o is not None and len(o) and o in init:
                idx=-1
                while idx in init[o]:
                    idx-=1
                init[o][idx]=wp[w]
                del wp[w]

        # wp will now consist of items that weren't assigned any particular place
        # so put them in the first available space
        for type,_,_,_,lowestindex,maxentries,typemajor,def_icon,_ in maps:
            # fill it up
            for w in wp.keys():
                if len(init[type])>=maxentries:
                    break
                idx=-1
                while idx in init[type]:
                    idx-=1
                init[type][idx]=wp[w]
                del wp[w]

        # time to write the files out
        dircache=self.DirCache(self)
        for type, indexfile, sizefile, directory, lowestindex, maxentries,typemajor,def_icon,_  in maps:
            # get the index file so we can work out what to delete
            names=[init[type][x]['name'] for x in init[type]]
            for item in self.getindex(indexfile):
                if basename(item.filename) not in names:
                    self.log(item.filename+" is being deleted")
                    try:
                        dircache.rmfile(item.filename)
                    except com_brew.BrewNoSuchFileException:
                        self.log("Hmm, it didn't exist!")
            # fixup the indices
            fixups=[k for k in init[type].keys() if k<lowestindex]
            fixups.sort()
            for f in fixups:
                for ii in xrange(lowestindex, lowestindex+maxentries):
                    # allocate an index
                    if ii not in init[type]:
                        init[type][ii]=init[type][f]
                        del init[type][f]
                        break
            # any left over?
            fixups=[k for k in init[type].keys() if k<lowestindex]
            for f in fixups:
                self.log("There is no space in the index for "+type+" for "+init[type][f]['name'])
                del init[type][f]
            # write each entry out
            for idx in init[type].keys():
                entry=init[type][idx]
                filename=entry.get('filename', directory+"/"+entry['name'])
                entry['filename']=filename
                fstat=dircache.stat(filename)
                if 'data' not in entry:
                    # must be in the filesystem already
                    if fstat is None:
                        self.log("Entry "+entry['name']+" is in index "+indexfile+" but there is no data for it and it isn't in the filesystem.  The index entry will be removed.")
                        del init[type][idx]
                        continue
                # check len(data) against fstat->length
                data=entry['data']
                if data is None:
                    assert merge 
                    continue # we are doing an add and don't have data for this existing entry
                if fstat is not None and len(data)==fstat['size']:
                    self.log("Not writing "+filename+" as a file of the same name and length already exists.")
                else:
                    dircache.writefile(filename, data)
            # write out index
            ifile=self.protocolclass.indexfile()
            idxlist=init[type].keys()
            idxlist.sort()
            idxlist.reverse() # the phone has them in reverse order for some reason so we do the same
            for idx in idxlist:
                ie=self.protocolclass.indexentry()
                ie.index=idx
                vtype=init[type][idx].get("vtype", None)
                if vtype is None:
                    vtype=self._guessvtype(init[type][idx]['filename'], typemajor)
                ie.type=vtype
                ie.filename=init[type][idx]['filename']
                # ie.date left as zero
                ie.dunno=0 # mmmm
                icon=init[type][idx].get("icon", None)
                if icon is None:
                    icon=def_icon
                ie.icon=icon
                ifile.items.append(ie)
            buf=prototypes.buffer()
            ifile.writetobuffer(buf, logtitle="Index file "+indexfile)
            self.log("Writing index file "+indexfile+" for type "+type+" with "+`len(idxlist)`+" entries.")
            dircache.writefile(indexfile, buf.getvalue()) # doesn't really need to go via dircache
            # write out size file, if it is required
            if sizefile != '':
                size=0
                for idx in idxlist:
                    fstat=dircache.stat(init[type][idx]['filename'])
                    size+=fstat['size']
                szfile=self.protocolclass.sizefile()
                szfile.size=size
                buf=prototypes.buffer()
                szfile.writetobuffer(buf, logtitle="Writing size file "+sizefile)
                self.log("You are using a total of "+`size`+" bytes for "+type)
                dircache.writefile(sizefile, buf.getvalue())
        return reindexfunction(results)
                     


class LGDirectoryMedia:
    """The media is stored one per directory with .desc and body files"""

    def __init__(self):
        pass

    def getmediaindex(self, builtins, maps, results, key):
        """Gets the media (wallpaper/ringtone) index

        @param builtins: the builtin list on the phone
        @param results: places results in this dict
        @param maps: the list of index files and locations
        @param key: key to place results in
        """
        self.log("Reading "+key)
        media={}

        # builtins
        c=1
        for name in builtins:
            media[c]={'name': name, 'origin': 'builtin' }
            c+=1

        # directory
        for offset,location,origin,maxentries in maps:
            index=self.getindex(location)
            for i in index:
                media[i+offset]={'name': index[i], 'origin': origin}

        results[key]=media
        return media

    __mimetoextensionmapping={
        'image/jpg': '.jpg',
        'image/bmp': '.bmp',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/bci': '.bci',
        'audio/mp3': '.mp3',
        'audio/mid': '.mid',
        'audio/qcp': '.qcp'
        }
    
    def _createnamewithmimetype(self, name, mt):
        name=basename(name)
        if mt=="image/jpeg":
            mt="image/jpg"
        try:
            return name+self.__mimetoextensionmapping[mt]
        except KeyError:
            self.log("Unable to figure out extension for mime type "+mt)
            return name
                     
    def _getmimetype(self, name):
        ext=getext(name.lower())
        if len(ext): ext="."+ext
        if ext==".jpeg":
            return "image/jpg" # special case
        for mt,extension in self.__mimetoextensionmapping.items():
            if ext==extension:
                return mt
        self.log("Unable to figure out a mime type for "+name)
        assert False, "No idea what type "+ext+" is"
        return "x-unknown/x-unknown"

    def getindex(self, location, getmedia=False):
        """Returns an index based on the sub-directories of location.
        The key is an integer, and the value is the corresponding name"""
        index={}
        try:
            dirlisting=self.getfilesystem(location)
        except com_brew.BrewNoSuchDirectoryException:
            return index
        
        for item in dirlisting:
            if dirlisting[item]['type']!='directory':
                continue
            try:
                buf=prototypes.buffer(self.getfilecontents(dirlisting[item]['name']+"/.desc"))
            except com_brew.BrewNoSuchFileException:
                self.log("No .desc file in "+dirlisting[item]['name']+" - ignoring directory")
                continue
            desc=self.protocolclass.mediadesc()
            desc.readfrombuffer(buf, logtitle=".desc file %s/.desc read" % (dirlisting[item]['name'],))
            filename=self._createnamewithmimetype(dirlisting[item]['name'], desc.mimetype)
            if not getmedia:
                index[desc.index]=filename
            else:
                try:
                    # try to read it using name in desc file
                    contents=self.getfilecontents(dirlisting[item]['name']+"/"+desc.filename)
                except (com_brew.BrewNoSuchFileException,com_brew.BrewNoSuchDirectoryException):
                    try:
                        # then try using "body"
                        contents=self.getfilecontents(dirlisting[item]['name']+"/body")
                    except (com_brew.BrewNoSuchFileException,com_brew.BrewNoSuchDirectoryException,com_brew.BrewNameTooLongException):
                        self.log("Can't find the actual content in "+dirlisting[item]['name'])
                        continue
                index[filename]=contents
        return index

    def getmedia(self, maps, result, key):
        """Returns the contents of media as a dict where the key is a name as returned
        by getindex, and the value is the contents of the media"""
        media={}
        for offset,location,origin,maxentries in maps:
            media.update(self.getindex(location, getmedia=True))
        result[key]=media
        return result

    def savemedia(self, mediakey, mediaindexkey, maps, results, merge, reindexfunction):
        """Actually saves out the media

        @param mediakey: key of the media (eg 'wallpapers' or 'ringtones')
        @param mediaindexkey:  index key (eg 'wallpaper-index')
        @param maps: list index files and locations
        @param results: results dict
        @param merge: are we merging or overwriting what is there?
        @param reindexfunction: the media is re-indexed at the end.  this function is called to do it
        """
        # this is based on the IndexedMedia function and they are frustratingly similar
        print results.keys()
        # I humbly submit this as the longest function in the bitpim code ...
        # wp and wpi are used as variable names as this function was originally
        # written to do wallpaper.  it works just fine for ringtones as well
        wp=results[mediakey].copy()
        wpi=results[mediaindexkey].copy()
        # remove builtins
        for k in wpi.keys():
            if wpi[k]['origin']=='builtin':
                del wpi[k]

        # sort results['mediakey'+'-index'] into origin buckets

        # build up list into init
        init={}
        for offset,location,type,maxentries in maps:
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
        for offset,location,type,maxentries in maps:
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
                            if stripext(entry['name']) in dirlisting:
                                dellist.append(entry['name'])
                            else:
                                self.log("%s in %s index but not filesystem" % (entry['name'], type))
            # go ahead and delete unwanted directories
            print "deleting",dellist
            for f in dellist:
                self.rmdirs(location+"/"+f)
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
                    
            # write out the content

            ####  index is dict, key is index number, value is dict
            ####  value['name'] = filename
            ####  value['data'] is contents
            listing=self.getfilesystem(location, 1)

            for key in index:
                efile=index[key]['name']
                content=index[key]['data']
                if content is None:
                    continue # in theory we could rewrite .desc file in case index number has changed
                mimetype=self._getmimetype(efile)
                dirname=stripext(efile)
                desc=self.protocolclass.mediadesc()
                desc.index=key
                desc.filename="body"
                desc.mimetype=mimetype
                desc.totalsize=0
                desc.totalsize=desc.packetsize()+len(content)
                buf=prototypes.buffer()
                descfile="%s/%s/.desc" % (location, dirname)
                desc.writetobuffer(buf, logtitle="Desc file at "+descfile)
                try:
                    self.mkdir("%s/%s" % (location,dirname))
                except com_brew.BrewDirectoryExistsException:
                    pass
                self.writefile(descfile, buf.getvalue())
                bodyfile="%s/%s/body" % (location, dirname)
                if bodyfile in listing and len(content)==listing[bodyfile]['size']:
                    self.log("Skipping writing %s as there is already a file of the same length" % (bodyfile,))
                else:
                    self.writefile(bodyfile, content)

        # did we have too many
        if len(wp):
            for k in wp:
                self.log("Unable to put %s on the phone as there weren't any spare index entries" % (wp[k]['name'],))
                
        # Note that we don't write to the camera area

        # tidy up - reread indices
        del results[mediakey] # done with it
        reindexfunction(results)
        return results

class LGUncountedIndexedMedia:
    """Implements media for LG phones that use the new index format with index file with no counters such as the VX8300
    Allow external media to be managed without downloading files, can detect if external media is present.
    Also contains 'hack' for ringtones to allow users to store ringtones on the external media"""

    def __init__(self):
        pass

    def getmediaindex(self, builtins, maps, results, key):
        """Gets the media (wallpaper/ringtone) index

        @param builtins: the builtin list on the phone
        @param results: places results in this dict
        @param maps: the list of index files and locations
        @param key: key to place results in
        """

        self.log("Reading "+key)
        media={}

        # builtins
        index = 0;                      # MIC Initialize counter here, instead of the next stanza
        for i,n in enumerate(builtins): # nb zero based index whereas previous phones used 1
            media[i]={'name': n, 'origin': 'builtin'}
            index+=1;

        # maps
        # index=0                       # MIC Do not want to reset index; builtins start at 0
                                        # Otherwise, the builtins are overwriten by
                                        # these
        for type, indexfile, directory, external_dir, maxentries, typemajor,_idx  in maps:
            if _idx is not None:
                index=_idx
            for item in self.getindex(indexfile):
                media[index]={
                    'name': basename(item.filename),
                    'filename': item.filename,
                    'origin': type,
                    }
                if item.date!=0:
                    media[index]['date']=item.date
                index+=1

        # finish
        results[key]=media

    def getindex(self, filename):
        "read an index file"
        try:
            buf=prototypes.buffer(self.getfilecontents(filename))
        except com_brew.BrewNoSuchFileException:
            return []

        g=self.protocolclass.indexfile()
        # some media indexes have crap appended to the end, prevent this error from messing up everything
        # valid entries at the start of the file will still get read OK. 
        try:
            g.readfrombuffer(buf, logtitle="Index file "+filename)
        except:
            self.log("Corrupt index file "+`filename`+", this might cause you all sorts of problems.")
        return g.items

    def getmedia(self, maps, results, key):
        origins={}
        # signal that we are using the new media storage that includes the origin and timestamp
        origins['new_media_version']=1

        for type, indexfile, directory, external_dir, maxentries, typemajor, _idx  in maps:
            media={}
            for item in self.getindex(indexfile):
                data=None
                # skip files that are not in the actual directory
                # these are external media files that are handled
                # differently, this will prevent them from showing 
                # in the media views
                if not item.filename.startswith(directory):
                    continue
                timestamp=None
                try:
                    stat_res=self.statfile(item.filename)
                    if stat_res!=None:
                        timestamp=stat_res['date'][0]
                    if not self.is_external_media(item.filename):
                        data=self.getfilecontents(item.filename, True)
                    else:
                        # for external memory skip reading it is very slow
                        # the file will show up in bitpim allowing it to 
                        # be managed, files added from bitpim will be 
                        # visible because we will have a copy of the
                        # file we copied to the phone.
                        data=''
                except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException,com_brew.BrewNameTooLongException):
                    self.log("It was in the index, but not on the filesystem")
                except (com_brew.BrewFileLockedException):
                    self.log("Could not read " + item.filename + " possibly due to SD card not being present.")
                except com_brew.BrewAccessDeniedException:
                    # firmware wouldn't let us read this file, just mark it then
                    self.log('Failed to read file: '+item.filename)
                    data=''
                if data!=None:
                    media[common.basename(item.filename)]={ 'data': data, 'timestamp': timestamp}
            origins[type]=media

        results[key]=origins
        return results

    def is_external_media(self, filename):
        return filename.startswith(self.external_storage_root)

    def external_storage_present(self):
        dircache=self.DirCache(self)
        test_name=self.external_storage_root+"bitpim_test"
        try:
            dircache.writefile(test_name, "bitpim_test")
        except:
            return False
        dircache.rmfile(test_name)
        return True

    def savemedia(self, mediakey, mediaindexkey, maps, results, merge,
                  reindexfunction, update_index_file=True):
        """Actually saves out the media

        @param mediakey: key of the media (eg 'wallpapers' or 'ringtones')
        @param mediaindexkey:  index key (eg 'wallpaper-index')
        @param maps: list index files and locations
        @param results: results dict
        @param merge: are we merging or overwriting what is there?
        @param reindexfunction: the media is re-indexed at the end.  this function is called to do it
        """

        # take copies of the lists as we modify them
        wp=results[mediakey].copy()  # the media we want to save
        wpi=results[mediaindexkey].copy() # what is already in the index files

        # remove builtins
        for k in wpi.keys():
            if wpi[k].get('origin', "")=='builtin':
                del wpi[k]

        use_external_media=self.external_storage_present()
        skip_origin=[]
        
        for type, indexfile, directory, external_dir, maxentries, typemajor, _idx  in maps:
            # if no external media is present skip indexes which refer
            # to external media
            if self.is_external_media(directory) and not use_external_media:
                self.log(" No external storage detected. Skipping "+type+" media.")
                skip_origin.append(type)
            else:
                # make sure the media directory exists
                try:
                    self.mkdirs(directory)
                except:
                    pass


        # build up list into init
        init={}
        for type, indexfile, directory, external_dir, maxentries, typemajor, _idx  in maps:
            init[type]={}
            for k in wpi.keys():
                if wpi[k]['origin']==type:
                    name=wpi[k]['name']
                    fullname=wpi[k]['filename']
                    data=None
                    del wpi[k]
                    for w in wp.keys():
                        # does wp contain a reference to this same item?
                        if wp[w]['name']==name and wp[w]['origin']==type:
                            data=wp[w]['data']
                            del wp[w]
                    if not merge and data is None:
                        # delete the entry
                        continue
                    if type in skip_origin:
                        self.log("skipping "+name+" in index "+type+" no external media detected")
                    elif fullname.startswith(directory):
                        # only add in files that are really in the media directory on the phone
                        # fake files will be added in later in this function
                        init[type][name]={'data': data, 'filename': fullname}

        # init now contains what is in the original indexes that should stay on the phone
        # wp contains items that we still need to add, and weren't in the existing index
        assert len(wpi)==0
        
        # now look through the media and see if anything was assigned a particular
        # origin and put it in the indexes, things that were not assigned are dropped
        for w in wp.keys():
            o=wp[w].get("origin", "")
            if o is not None and len(o) and o in init and o not in skip_origin:
                init[o][wp[w]['name']]={'data': wp[w]['data']}
                del wp[w]

        # if external media is specified, add all the extra files to the index
        for type, indexfile, directory, external_dir, maxentries, typemajor, _idx  in maps:
            if type not in skip_origin and len(external_dir):
                if self.is_external_media(external_dir) and not use_external_media:
                    continue
                try:
                    dirlisting=self.listfiles(external_dir)
                except:
                    self.log("Unable to list files in external directory "+external_dir)
                    continue
                for file in dirlisting:
                    init[type][basename(file)]={'data': 'bitpim:)', 'filename': file}


        # time to write the files out
        dircache=self.DirCache(self)
        for type, indexfile, directory, external_dir, maxentries, typemajor, _idx  in maps:
            if type not in skip_origin:
                # get the old index file so we can work out what to delete
                for item in self.getindex(indexfile):
                    # force the name to the correct directory
                    # this will then cleanup fake external files that are
                    # no longer in the index
                    real_filename=directory+"/"+basename(item.filename)
                    if basename(item.filename) not in init[type]:
                        self.log(real_filename+" is being deleted")
                        try:
                            dircache.rmfile(real_filename)
                        except com_brew.BrewNoSuchFileException:
                            self.log("Hmm, it didn't exist!")
                # write each entry out
                for idx in init[type].keys():
                    entry=init[type][idx]
                    # we force the use of the correct directory, regardless of the 
                    # actual path the file is in, the phone requires the file to be in the correct
                    # location or it will rewrite the index file on reboot
                    # the actual index file can point to a different location
                    # as long as the filename exists, allowing a hack.
                    filename=directory+"/"+idx
                    if not entry.has_key('filename'):
                        entry['filename']=filename
                    fstat=dircache.stat(filename)
                    if 'data' not in entry:
                        # must be in the filesystem already
                        if fstat is None:
                            self.log("Entry "+idx+" is in index "+indexfile+" but there is no data for it and it isn't in the filesystem.  The index entry will be removed.")
                            del init[type][idx]
                            continue
                    # check len(data) against fstat->length
                    data=entry['data']
                    if data is None:
                        assert merge 
                        continue # we are doing an add and don't have data for this existing entry
                    if not data:
                        # check for files with no data, probably due to access denied or external media read
                        self.log('Not writing '+filename+', no data available')
                        continue
                    if fstat is not None and len(data)==fstat['size']:
                        self.log("Not writing "+filename+" as a file of the same name and length already exists.")
                    else:
                        dircache.writefile(filename, data)
            # write out index
            if update_index_file:
                ifile=self.protocolclass.indexfile()
                idxlist=init[type].keys()
                idxlist.sort()
                idxlist.reverse()
                for idx in idxlist:
                    ie=self.protocolclass.indexentry()
                    ie.type=typemajor
                    ie.filename=init[type][idx]['filename']
                    fstat=dircache.stat(init[type][idx]['filename'])
                    if fstat is not None:
                        ie.size=fstat['size']
                    else:
                        ie.size=0
                    # ie.date left as zero
                    ifile.items.append(ie)
                buf=prototypes.buffer()
                ifile.writetobuffer(buf, logtitle="Index file "+indexfile)
                self.log("Writing index file "+indexfile+" for type "+type+" with "+`len(idxlist)`+" entries.")
                dircache.writefile(indexfile, buf.getvalue()) # doesn't really need to go via dircache
        return reindexfunction(results)
                            
    def getwallpaperindices(self, results):
        return self.getmediaindex(self.builtinwallpapers, self.wallpaperlocations, results, 'wallpaper-index')

    def getringtoneindices(self, results):
        return self.getmediaindex(self.builtinringtones, self.ringtonelocations, results, 'ringtone-index')

    def getwallpapers(self, result):
        return self.getmedia(self.wallpaperlocations, result, 'wallpapers')

    def getringtones(self, result):
        return self.getmedia(self.ringtonelocations, result, 'ringtone')

    def savewallpapers(self, results, merge):
        return self.savemedia('wallpapers', 'wallpaper-index', self.wallpaperlocations, results, merge, self.getwallpaperindices)
            
    def saveringtones(self, results, merge):
        return self.savemedia('ringtone', 'ringtone-index', self.ringtonelocations, results, merge, self.getringtoneindices)

class EnterDMError(Exception):
    pass

class LGDMPhone:
    """Class to handle getting the phone into Diagnostic Mode (DM) for later
    Lg model phones.  Subclass should set the following in __init__:
        self._timeout: how long (in seconds) before the phone gets kicked out of DM
    Subclass may also override the following methods:
        self.setDMversion(): set self._DMv5 to True or False.
    """

    def _rotate_left(self, value, nbits):
        return ((value << nbits) | (value >> (32-nbits))) & 0xffffffffL

    def get_challenge_response(self, challenge):
        # Reverse engineered and contributed by Nathan Hjelm <hjelmn@users.sourceforge.net>
        # get_challenge_response(challenge):
        #    - Takes the SHA-1 hash of a 16-byte block containing the challenge and returns the proper response.
        #    - The hash used by the vx8700 differs from the standard implementation only in that it does not append a
        #      1 bit before padding the message with 0's.
        #
        #  Return value:
        #    Last three bytes of the SHA-1 hash or'd with 0x80000000.
        # IV = (0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0)
        input_vector = [0x67452301L, 0xefcdab89L, 0x98badcfeL, 0x10325476L, 0xc3d2e1f0L]
        hash_result  = [0x67452301L, 0xefcdab89L, 0x98badcfeL, 0x10325476L, 0xc3d2e1f0L]
        hash_data = []
        hash_data.append(long(challenge))
        # pad message with zeros as well and zero first word of bit length
        # if this were standard SHA-1 then 0x00000080 would be appended here as its a 56-bit message
        for i in range(14):
            hash_data.append(0L)
        # append second word of the bit length (56 bit message?)
        hash_data.append(56L)
        for i in range(80):
            j = i & 0x0f
            if i > 15:
                index1 = (i -  3) & 0x0f
                index2 = (i -  8) & 0x0f
                index3 = (i - 14) & 0x0f
                hash_data[j] = hash_data[index1] ^ hash_data[index2] ^ hash_data[index3] ^ hash_data[j]
                hash_data[j] = self._rotate_left (hash_data[j], 1)
            if i < 20:
                # f = (B and C) or ((not B) and C), k = 0x5a827999
                f = (hash_result[1] & hash_result[2]) | ((~hash_result[1]) & hash_result[3])
                k = 0x5a827999L
            elif i < 40:
                # f = B xor C xor D, k = 0x6ed9eba1
                f = hash_result[1] ^ hash_result[2] ^ hash_result[3]
                k = 0x6ed9eba1L
            elif i < 60:
                # f = (B and C) or (B and D) or (B and C), k = 0x8f1bbcdc
                f = (hash_result[1] & hash_result[2]) | (hash_result[1] & hash_result[3]) | (hash_result[2] & hash_result[3])
                k = 0x8f1bbcdcL
            else:
                # f = B xor C xor D, k = 0xca62c1d6
                f = hash_result[1] ^ hash_result[2] ^ hash_result[3]
                k = 0xca62c1d6L
            # A = E + rotate_left (A, 5) + w[j] + f + k
            newA = (hash_result[4] + self._rotate_left(hash_result[0], 5) + hash_data[j] + f + k) & 0xffffffffL
            # B = oldA, C = rotate_left(B, 30), D = C, E = D
            hash_result = [newA] + hash_result[0:4]
            hash_result[2] = self._rotate_left (hash_result[2], 30)
        for i in range(5):
            hash_result[i] = (hash_result[i] + input_vector[i]) & 0xffffffffL
        return 0x80000000L | (hash_result[4] & 0x00ffffffL)

    def _unlock_key(self):
        _req=self.protocolclass.LockKeyReq(lock=1)
        self.sendbrewcommand(_req, self.protocolclass.data)

    def _lock_key(self):
        _req=self.protocolclass.LockKeyReq()
        self.sendbrewcommand(_req, self.protocolclass.data)

    def _press_key(self, keys):
        # simulate a series of keypress
        if not keys:
            return
        _req=self.protocolclass.KeyPressReq()
        for _k in keys:
            _req.key=_k
            self.sendbrewcommand(_req, self.protocolclass.data)

    def _enter_DMv4(self):
        self._lock_key()
        self._press_key('\x06\x513733929\x51')
        self._unlock_key()

    def _enter_DMv5(self):
        # request the seed
        _req=self.protocolclass.ULReq(unlock_key=0)
        _resp=self.sendbrewcommand(_req, self.protocolclass.ULRes)

        # respond with the key
        _key=self.get_challenge_response(_resp.unlock_key)
        if _key is None:
            self.log('Failed to get the key.')
            raise EnterDMError('Failed to get the key')

        _req=self.protocolclass.ULReq(unlock_code=1, unlock_key=_key)
        _resp=self.sendbrewcommand(_req, self.protocolclass.ULRes)
        if _resp.unlock_ok!=1:
            raise EnterDMError('Bad response - unlock_ok: %d'%_resp.unlock_ok)

    def _DMv6_get_esn(self):
        _req=self.protocolclass.NVReq(field=0x0000)
        _res=self.sendbrewcommand(_req, self.protocolclass.NVRes)

        return struct.unpack_from ('<L', _res.data, 0)[0]

    def _DMv6_get_extra_data(self,data_field):
        _req=self.protocolclass.NVReq(field=data_field)
        _res=self.sendbrewcommand(_req, self.protocolclass.NVRes)

        return struct.unpack_from ('<L', _res.data, 0)[0]

    def _DMv6_get_compile_time(self):
        _req=self.protocolclass.FWInfoReq()
        _res=self.sendbrewcommand(_req, self.protocolclass.FWInfoRes)

        return _res.get_compile_time()

    def _enter_DMv6(self):
        # this loop is a hack -- different LG phones use different commands to get _extra. once
        # the command is figured out we won't have to try every possible shift.
        if self._shift is None:
            _shifts=range(4)
        else:
            _shifts=[self._shift]
        for _shift in _shifts:
            # similar but slightly different from v5, the enV2 started this!
            # request the seed
            _req=self.protocolclass.DMKeyReq()
            _resp=self.sendbrewcommand(_req, self.protocolclass.DMKeyResp)
            _key=self.get_challenge_response(_resp.unlock_key)
            if _key is None:
                self.log('Failed to get the key.')
                raise EnterDMError('Failed to get the key')

            #_esn=self._DMv6_get_esn()
            #_extra=self._DMv6_get_extra_data(0x13d7) # VX-9100 uses data field 0x13d7
            #_ctime=self._DMv6_get_compile_time()

            # determine how many bytes the key needs be be shifted
            #_shift_bytes = (_esn + ((_extra >> 16) & 0xf) + ((_extra >> 11) & 0x1f) + _ctime) % 16
            #_shift = _shift_bytes / 4

            _req=self.protocolclass.DMEnterReq(unlock_key=_key)
            if _resp.unlock_code==0:
                # this response usually occurs in error. rebooting the phone seems to clear it
                _req.unlock_code=1
            elif _resp.unlock_code==2:
                _req.unlock_code=3
                _req.convert_to_key2(_shift)
            else:
                raise EnterDMError('Unknown unlock_code: %d'%_resp.unlock_code)
            _resp=self.sendbrewcommand(_req, self.protocolclass.DMEnterResp)
            if _resp.result == 1:
                if self._shift is None:
                    self._shift=_shift
                    if __debug__:
                        self.log('Shift key: %d'%self._shift)
                return
        raise EnterDMError('Failed to guess the shift/key')

    def enter_DM(self, e=None):
        # do nothing if the phone failed to previously enter DM
        if self._in_DM is False:
            return
        # check for DMv5 applicability
        if self._DMv5 is None:
            self.setDMversion()
        try:
            if self._DMv6:
                # new DM scheme
                self._enter_DMv6()
            elif self._DMv5:
                # enter DMv5
                self._enter_DMv5()
            else:
                # enter DMv4
                self._enter_DMv4()
            self._in_DM=True
        except:
            self.log('Failed to transition to DM')
            self._in_DM=False
            return

    def _OnTimer(self):
        if self._in_DM:
            self.log('Transition out of DM assumed.')
            self._in_DM=None
        del self._timer
        self._timer=None

    def _filefunc(self, func, *args, **kwargs):
        self.enter_DM()
        return func(*args, **kwargs)

    def _sendbrewcommand(self, func, *args, **kwargs):
        # A wrapper function to address the issue of DM timing out in a
        # middle of a file read or write (usually of a large file).
        # Not quite happy with this hack, but couldn't figure out a better way!
        # If you have a better solution, feel free to share.
        try:
            return func(*args, **kwargs)
        except com_brew.BrewAccessDeniedException:
            # DM may have timed out, retry.
            pass
        self.enter_DM()
        return func(*args, **kwargs)

    def setDMversion(self):
        """Define the DM version required for this phone, default to DMv5"""
        self._DMv5=True
        self._DMv6=False

    def __init__(self):
        self._in_DM=None
        self._timer=None
        self._DMv5=None
        self._DMv6=None
        self._timeout=None
        self._shift=None
        # wrap our functions
        self.getfilecontents=functools.partial(self._filefunc,
                                               self.getfilecontents)
        self.writefile=functools.partial(self._filefunc,
                                         self.writefile)
        self.statfile=functools.partial(self._filefunc,
                                        self.statfile)
        self.sendbrewcommand=functools.partial(self._sendbrewcommand,
                                               self.sendbrewcommand)

    def __del__(self):
        if self._timer:
            self._timer.cancel()
            del self._timer

def basename(name):
    if name.rfind('/')>=0:
        pos=name.rfind('/')
        name=name[pos+1:]
    return name

def dirname(name):
    if name.rfind("/")<1:
        return ""
    return name[:name.rfind("/")]

def stripext(name):
    if name.rfind('.')>=0:
        name=name[:name.rfind('.')]
    return name

def getext(name):
    name=basename(name)
    if name.rfind('.')>=0:
        return name[name.rfind('.')+1:]
    return ''
