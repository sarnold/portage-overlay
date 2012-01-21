### BITPIM
###
### Copyright (C) 2004, 2005 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyomedia.py 3707 2006-11-29 04:49:48Z sawecw $

"""Common code for Sanyo Media transfers"""

# standard modules

import time
import cStringIO
import re

# BitPim Modules
import com_sanyo
import com_brew
import com_phone
import p_sanyomedia
import prototypes

class SanyoMedia:
    "Download and upload media (ringers/wallpaper) from Sanyo Phones"

    FIRST_MEDIA_DIRECTORY=2
    LAST_MEDIA_DIRECTORY=3
    CAMERA_DIRECTORY=1
    
    # Directories:
    #    1: Camera Pictures and Videos.  MDM - Video
    #                                    V   - Picture
    #    2: Downloads
    #    3: Cable uploads
    #    4: Duplicate of directory 1 ??

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        ( 300, 1, 1, "images", 30),
        ( 300, 1, 0, "camera", 30),
        )

    wallpaperexts=(".jpg", ".png", ".mp4", ".3g2",".JPG")
    ringerexts=(".mid", ".qcp", ".mp3", ".m4a", ".pmd", ".bin")

    def __init__(self):
        pass

    def getmediaindices(self, results):
        com_sanyo.SanyoPhonebook.getmediaindices(self, results)
        ringermedia=results['ringtone-index']
        imagemedia=results['wallpaper-index']

        copypat=re.compile(r"(.*)\.(\d+)$")
        for idir in range(self.FIRST_MEDIA_DIRECTORY, self.LAST_MEDIA_DIRECTORY+1):
            self.log("Indexing directory "+`idir`)
            req=self.protocolclass.sanyochangedir()
            req.dirindex=idir
            res=self.sendpbcommand(req, self.protocolclass.sanyochangedirresponse)
            req=self.protocolclass.sanyonumfilesrequest()
            try:
                res=self.sendpbcommand(req, self.protocolclass.sanyonumfilesresponse)
            except com_sanyo.SanyoCommandException, ex:
                if ex.errnum!=121:
                    raise
                self.log("Skipping directory "+`idir`)
                continue
            
            self.log("Directory "+`idir`+", File Count="+`res.count`)
            nfiles=res.count
            for ifile in range(nfiles):
                req=self.protocolclass.sanyomediafilenamerequest()
                req.index=ifile
                res=self.sendpbcommand(req, self.protocolclass.sanyomediafilenameresponse)
                name=res.filename
                orgname=name
                
                unique=False
                while not unique:
                    unique=True
                    for idx in imagemedia.keys():
                        if name==imagemedia[idx]['name']:
                            matchresult=copypat.match(name)
                            if matchresult:
                                copycount=int(matchresult.group(2))+1
                                name=matchresult.group(1)+"."+str(copycount)
                            else:
                                name=name+".1"
                            # Keep looping until sure we have unique name
                            unique=False
                            break
                if idir==self.CAMERA_DIRECTORY:

                    if res.num3==0:    # Original Camera Picture
                        # Could convert filename to to a date
                        imagemedia[ifile+1000*idir]={'name': name, 'origin': "camera"}
                    else:
                        # Wallet pictures
                        imagemedia[res.num3]={'name': name, 'origin': "images"}
                else:
                    idx=ifile+1000*idir

                    # Make this more elegant later
                    iswallpaper=0
                    for ext in self.wallpaperexts:
                        if orgname.endswith(ext):
                            imagemedia[idx]={'name': name, 'origin': "images"}
                            iswallpaper=1
                            break
                    if not iswallpaper:
                        for ext in self.ringerexts:
                            if orgname.endswith(ext):
                                ringermedia[idx]={'name': name, 'origin': "ringers"}
                                break

        results['ringtone-index']=ringermedia
        results['wallpaper-index']=imagemedia
        return
            
        
    def getmediaindex(self, builtins, maps, results, key):
        media=com_sanyo.SanyoPhonebook.getmediaindex(self, builtins, maps, results, key)
        # the maps
        type=''
        for offset,indexfile,indextype,type,maxentries in maps:
            req=self.protocolclass.sanyochangedir()
            req.dirindex=indexfile
            res=self.sendpbcommand(req, self.protocolclass.sanyochangedirresponse)
            req=self.protocolclass.sanyonumfilesrequest()
            res=self.sendpbcommand(req, self.protocolclass.sanyonumfilesresponse)
            for ifile in range(res.count):
                req=self.protocolclass.sanyomediafilenamerequest()
                req.index=ifile
                res=self.sendpbcommand(req, self.protocolclass.sanyomediafilenameresponse)
                media[ifile+offset]={'name': res.filename, 'origin': "camera"}

        results[key]=media
        return media

    def getindex(self, location):
        "Get an index of files in a Sanyo directory"
        index={}
        req=self.protocolclass.sanyochangedir()
        req.dirindex=location
        res=self.sendpbcommand(req, self.protocolclass.sanyochangedirresponse)

        req=self.protocolclass.sanyonumfilesrequest()
        res=self.sendpbcommand(req, self.protocolclass.sanyonumfilesresponse)
        for ifile in range(res.count):
            req=self.protocolclass.sanyomediafilenamerequest()
            req.index=ifile
            res=self.sendpbcommand(req, self.protocolclass.sanyomediafilenameresponse)
            index[ifile]=res.filename

        return index
        
    def getmedia(self, exts, result, key):
        media={}
        # Essentially duplicating code in getmediaindices
        copypat=re.compile(r"(.*)\.(\d+)$")
        if key=="wallpapers":
            mediaindex=result['wallpaper-index']
        else:
            mediaindex=result['ringtone-index']
            
        for idir in range(self.FIRST_MEDIA_DIRECTORY, self.LAST_MEDIA_DIRECTORY+1):
            self.log("Reading "+key+" from directory "+`idir`)
            req=self.protocolclass.sanyochangedir()
            req.dirindex=idir
            res=self.sendpbcommand(req, self.protocolclass.sanyochangedirresponse)
            req=self.protocolclass.sanyonumfilesrequest()
            try:
                res=self.sendpbcommand(req, self.protocolclass.sanyonumfilesresponse)
            except com_sanyo.SanyoCommandException, ex:
                if ex.errnum!=121:
                    raise
                self.log("Skipping directory "+`idir`)
                continue

            self.log("Directory "+`idir`+", File Count="+`res.count`)
            nfiles=res.count
            for ifile in range(nfiles):
                req=self.protocolclass.sanyomediafilenamerequest()
                req.index=ifile
                res=self.sendpbcommand(req, self.protocolclass.sanyomediafilenameresponse)
                # self.log(res.filename+": "+`res.num1`+" "+`res.num2`+" "+`res.num3`+" "+`res.num4`)

                orgname=res.filename
                if idir==self.CAMERA_DIRECTORY and res.num3!=0:
                    idx=res.num3
                else:
                    idx=ifile+1000*idir

                # Get the file if it has the right extension
                for ext in exts:
                    if orgname.endswith(ext):
                        filename=mediaindex[idx]['name']
                        self.log("Retrieving file: "+orgname+", saving as "+filename)
                        try:
                            media[filename]=self.getsanyofilecontents(idir,ifile)
                        except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException):
                            self.log("It was in the index, but not on the filesystem")
                        break
                    
        result[key]=media
        return result
                

        
    def getmediaold(self, maps, result, key):
        media={}
        for offset,indexfile,indextype,type,maxentries in maps:
            index=self.getindex(indexfile)
            for i in index:
                try:
                    media[index[i]]=self.getsanyofilecontents(indexfile,i)
                except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException):
                    self.log("It was in the index, but not on the filesystem")
                    
        result[key]=media
        return result
        
    def getwallpapers(self, result):
        return self.getmedia(self.wallpaperexts, result, 'wallpapers')

    def getringtones(self, result):
        return self.getmedia(self.ringerexts, result, 'ringtone')

    
    def getsanyofilecontents(self, directory, fileindex):
        "Get file # index from directory # directory"
        start=time.time()
        self.log("Getting file # "+`fileindex`+" from directory "+`directory`)
        desc="Reading "+`directory`+"/"+`fileindex`

        req=self.protocolclass.sanyochangedir()
        req.dirindex=directory

        res=self.sendpbcommand(req, self.protocolclass.sanyochangedirresponse)

        req=self.protocolclass.sanyonumfilesrequest()
        res=self.sendpbcommand(req, self.protocolclass.sanyonumfilesresponse)

        # Should check that fileindex requested does not exceed number
        # of files in directory

        req=self.protocolclass.sanyomediafilenamerequest()
        req.index=fileindex
        res=self.sendpbcommand(req, self.protocolclass.sanyomediafilenameresponse)

        req=self.protocolclass.sanyomediafragmentrequest()
        req.fileindex=fileindex

        # Can't find a way to get the file size so we can show progress

        data=cStringIO.StringIO()
        
        more=1
        counter=0
        filesize=0
        while more==1:
            counter+=1
            if counter%5==0:
                self.progress(counter%250, 250, desc)
                
            res=self.sendpbcommand(req,self.protocolclass.sanyomediafragmentresponse)
            data.write(res.data[0:res.length])
            more=res.more
            filesize+=res.length

        self.progress(1,1,desc)

        data=data.getvalue()
        end=time.time()
        if end-start>3:
            self.log("Read "+`filesize`+" bytes at "+`int(filesize/(end-start))`+" bytes/second")

        return data
    
