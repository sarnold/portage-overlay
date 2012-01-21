### BITPIM
###
### Copyright (C) 2004-2005 Stephen Wood <saw@bitpim.org>
### Copyright (C) 2005 Todd Imboden
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungspha620.py 4371 2007-08-22 04:22:40Z sawecw $

"""Communicate with a Samsung SPH-A620"""

import sha
import re
import struct

import common
import commport
import p_samsungspha620
import p_brew
import com_brew
import com_phone
import com_samsung_packet
import prototypes
import fileinfo
import helpids

numbertypetab=('home','office','cell','pager','fax','none')

class Phone(com_samsung_packet.Phone):
    "Talk to a Samsung SPH-A620 phone"

    desc="SPH-A620"
    helpid=helpids.ID_PHONE_SAMSUNGOTHERS
    protocolclass=p_samsungspha620
    serialsname='spha620'

    # digital_cam/jpeg Remove first 148 characters

    imagelocations=(
        # offset, index file, files location, origin, maximumentries, header offset
        # Offset is arbitrary.  100 is reserved for amsRegistry indexed files
        (400, "digital_cam/wallet", "camera", 100, 148),
        (300, "digital_cam/jpeg", "camera", 100, 148),
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries, header offset
        )
        
    __audio_mimetype={ 'mid': 'audio/midi', 'qcp': 'audio/vnd.qcelp', 'pmd': 'application/x-pmd'}
    __image_mimetype={ 'jpg': 'image/jpg', 'jpeg': 'image/jpeg', 'gif': 'image/gif', 'bmp': 'image/bmp', 'png': 'image/png'}

    def __init__(self, logtarget, commport):
        com_samsung_packet.Phone.__init__(self, logtarget, commport)
        self.numbertypetab=numbertypetab
        self.mode=self.MODENONE

    def getfundamentals(self, results):
        """Gets information fundamental to interopating with the phone and UI."""
        self.amsanalyze(results)

        # use a hash of ESN and other stuff (being paranoid)
        self.log("Retrieving fundamental phone information")
        self.log("Phone serial number")
        self.setmode(self.MODEMODEM)
        results['uniqueserial']=sha.new(self.get_esn()).hexdigest()

        self.log("Reading group information")
        results['groups']=self.read_groups()
        # Comment the next to out if you want to read the phonebook
        #self.getwallpaperindices(results)
        #self.getringtoneindices(results)
        self.log("Fundamentals retrieved")
        return results

    def amsanalyze(self,results):
        buf=prototypes.buffer(self.getfilecontents(self.protocolclass.AMSREGISTRY))
        ams=self.protocolclass.amsregistry()
        ams.readfrombuffer(buf, logtitle="Read AMS registry")
        rt={}   #Todd added for ringtone index
        nrt=0     #Todd added for ringtone index
        wp={}
        nwp=0
        for i in range(ams.nfiles):
            filetype=ams.info[i].filetype
            if filetype:
                dir_ptr=ams.info[i].dir_ptr
                name_ptr=ams.info[i].name_ptr
                mimetype_ptr=ams.info[i].mimetype_ptr
                version_ptr=ams.info[i].version_ptr
                vendor_ptr=ams.info[i].vendor_ptr
                dir=self.getstring(ams.strings,dir_ptr)
                name=self.getstring(ams.strings,name_ptr)
                mimetype=self.getstring(ams.strings,mimetype_ptr)
                version=self.getstring(ams.strings,version_ptr)
                vendor=self.getstring(ams.strings,vendor_ptr)

                #downloaddomain_ptr=ams.info[i].downloaddomain_ptr
                print i, filetype, version, dir, vendor, name, mimetype
                #if downloaddomainptr_ptr:
                # print self.getstring(ams.strings,misc_ptr)
                print ams.info[i].num2, ams.info[i].num7, ams.info[i].num8, ams.info[i].num9, ams.info[i].num12, ams.info[i].num13, ams.info[i].num14, ams.info[i].num15, ams.info[i].num16, ams.info[i].num17
                print " "

        # Todd's added info
                if filetype==12:     #this will add the file extension
                    if mimetype=="audio/vnd.qcelp":
                        filetype='.qcp'
                    elif mimetype=="audio/midi":
                        filetype='.mid'
                    elif mimetype=="application/x-pmd":
                        filetype='.pmd'
                    elif mimetype=="audio/mp3":
                        filetype='.mp3'
                    else:
                        filetype=''
                    rt[100+nrt]={'name':name+filetype,'location':'ams/'+dir,'origin':'ringers'}
                    nrt+=1
                elif filetype==13:
                    if mimetype=="image/jpeg":
                        filetype='.jpg'
                    elif mimetype=="image/png":
                        filetype='.png'
                    elif mimetype=="image/gif":
                        filetype='.gif'
                    elif mimetype=="image/bmp":
                        filetype='.bmp'
                    else:
                        filetype=''
                    wp[100+nwp]={'name':name+filetype,'location':'ams/'+dir,'origin':'images'}
                    nwp+=1
                    
        results['ringtone-index']=rt
        results['wallpaper-index']=wp
        
    def pblinerepair(self, line):
        "Extend incomplete lines"
        # VGA1000 Firmware WG09 doesn't return a full line unless birthday
        # is set.  Add extra commas so packet decoding works
        nfields=26                      # Can we get this from packet def?
        ncommas=self.countcommas(line)
        if ncommas<0:                   # Un terminated quote
            line+='"'
            ncommas = -ncommas
        if nfields-ncommas>1:
            line=line+","*(nfields-ncommas-1)
        return line

    def countcommas(self, line):
        inquote=False
        ncommas=0
        for c in line:
            if c == '"':
                inquote = not inquote
            elif not inquote and c == ',':
                ncommas+=1

        if inquote:
            ncommas = -ncommas
        
        return ncommas
        
    def getringtones(self, results):
        self.getmediaindex(self.ringtonelocations, results,'ringtone-index')
        return self.getmedia(self.ringtonelocations, results, 'ringtone')
    
    def getwallpapers(self, results):
        self.getmediaindex(self.imagelocations, results,'wallpaper-index')
        return self.getmedia(self.imagelocations, results, 'wallpapers')

    
    def getmedia(self, maps, results, key):
        """Returns the contents of media as a dicxt where the key is a name
        returned by getindex, and the value is the contents of the media"""
        
        media={}
        if key=="ringtone":
            index_key="ringtone-index"
            origin="ringers"
        elif key=="wallpapers":
            index_key="wallpaper-index"
            origin="images"
            
        # Read the files indexed in ams Registry
        for k in results[index_key].keys():
            e=results[index_key][k]
            if e['origin']==origin:
                self.log("Reading "+e['name'])
                contents=self.getfilecontents(e['location'])
                media[e['name']]=contents

        # Now read from the directories in the maps array
        for offset,location,type,maxentries, headeroffset in maps:
            for item in self.listfiles(location).values():
                filename=item['name']
                p=filename.rfind("/")
                basefilename=filename[p+1:]+".jpg"
                contents=self.getfilecontents(filename)

                name_len=ord(contents[5])
                new_basefilename=filename[p+1:]+"_"+contents[6:6+name_len]+".jpg"
                duplicate=False
                # Fix up duplicate filenames
                for k in results[index_key].keys():
                    if results[index_key][k]['name']==new_basefilename:
                        duplicate=True
                        break
                    if results[index_key][k]['name']==basefilename:
                        ksave=k
                if duplicate:
                    new_basefilename=basefilename
                else:
                    self.log("Renaming to "+new_basefilename)
                    results[index_key][ksave]['name']=new_basefilename                  
                media[new_basefilename]=contents[headeroffset:]

        results[key]=media

    def getmediaindex(self, maps, results, key):
        """Get the media (wallpaper/ringtone) index for stuff not in amsRegistry

        @param results: places results in this dict
        @param maps: the list of locations
        @param key: key to place results in
        """
        self.log("Reading "+key)

        media=results[key] # Get any existing indices
        for offset,location,origin,maxentries, headeroffset in maps:
            i=0
            for item in self.listfiles(location).values():
                print item
                filename=item['name']
                p=filename.rfind("/")
                filename=filename[p+1:]+".jpg"
                media[offset+i]={'name': filename, 'origin': origin}
                i+=1

        results[key] = media
        return

    def _findmediaindex(self, index, name, pbentryname, type):
        if name is None:
            return 0
        for i in index:
            if index[i]['name']==name:
                return i
        # Not found in index, assume Vision download
        pos=name.find('_')
        if(pos>=0):
            i=int(name[pos+1:])
            return i
        
        return 0
        
    def getstring(self, contents, start):
        "Get a null terminated string from contents"
        i=start
        while contents[i:i+1]!='\0':
            i+=1
        return contents[start:i]

    def makegcd(self, filename,size,mimetable):
        "Build a GCD file for filename"
        ext=common.getext(filename.lower())
        try:
            mimetype=mimetable[ext]
        except:
            return ""
        
        noextname=common.stripext(filename)
        gcdcontent="Content-Type: "+mimetype+"\nContent-Name: "+noextname+"\nContent-Version: 1.0\nContent-Vendor: BitPim\nContent-URL: file:"+filename+"\nContent-Size: "+`size`+"\n\n\n"
        return gcdcontent
        
    def saveringtones(self, result, merge):
        dircache=self.DirCache(self)
        media_prefix=self.protocolclass.RINGERPREFIX
        endtransactionpath=self.protocolclass.ENDTRANSACTION
        media=result.get('ringtone', {})
        media_index=result.get('ringtone-index', {})
        media_names=[x['name'] for x in media.values()]
        index_names=[x['name'] for x in media_index.values()]
        if merge:
            del_names=[]
        else:
            del_names=[common.stripext(x) for x in index_names if x not in media_names]
            gcdpattern=re.compile("[\n\r]Content-Name: +(.*?)[\n\r]")
        new_names=[x for x in media_names if x not in index_names]

        progressmax=len(del_names)+len(new_names)
        progresscur=0
        self.log("Writing ringers")
        self.progress(progresscur, progressmax, "Writing ringers")

        for icnt in range(1,101):
            if not (new_names or del_names):
                break
            fname=media_prefix+`icnt`
            fnamegcd=media_prefix+`icnt`+".gcd"
            fstat=dircache.stat(fnamegcd)
            if del_names and fstat:
                # See if this file is in list of files to delete
                gcdcontents=dircache.readfile(fnamegcd)
                thisfile=gcdpattern.search(gcdcontents).groups()[0]
                if thisfile in del_names:
                    self.log("Deleting ringer "+thisfile)
                    self.progress(progresscur, progressmax, "Deleting ringer "+thisfile)
                    progresscur+=1
                    dircache.rmfile(fname)
                    dircache.rmfile(fnamegcd)
                    del_names.remove(thisfile)
                    fstat=False
            if new_names and not fstat:
                newname=new_names.pop()
                contents=""
                for k in media.keys():
                    if media[k]['name']==newname:
                        contents=media[k]['data']
                        break

                contentsize=len(contents)
                if contentsize:
                    gcdcontents=self.makegcd(newname,contentsize,self.__audio_mimetype)
                    self.log("Writing ringer "+newname)
                    self.progress(progresscur, progressmax, "Deleting ringer "+newname)
                    progresscur+=1
                    dircache.writefile(fname,contents)
                    dircache.writefile(fnamegcd,gcdcontents)

        fstat=dircache.stat(endtransactionpath)
        self.log("Finished writing ringers")
        self.progress(progressmax, progressmax, "Finished writing ringers")
        if fstat:
            dircache.rmfile(endtransactionpath)
        result['rebootphone']=True

        return

    def savewallpapers(self, result, merge):
        dircache=self.DirCache(self)
        media_prefix=self.protocolclass.WALLPAPERPREFIX
        endtransactionpath=self.protocolclass.ENDTRANSACTION
        media=result.get('wallpapers', {})
        for i in media.keys():
            try:
                if media[i]['origin']=='camera':
                    del media[i]
            except:
                pass
        media_index=result.get('wallpaper-index', {})
        media_names=[x['name'] for x in media.values()]
        index_names=[x['name'] for x in media_index.values()]
        if merge:
            del_names=[]
        else:
            del_names=[common.stripext(x) for x in index_names if x not in media_names]
            gcdpattern=re.compile("[\n\r]Content-Name: +(.*?)[\n\r]")
        new_names=[x for x in media_names if x not in index_names]

        progressmax=len(del_names)+len(new_names)
        progresscur=0
        self.log("Writing images")
        self.progress(progresscur, progressmax, "Writing images")

        for icnt in range(1,101):
            if not (new_names or del_names):
                break
            fname=media_prefix+`icnt`
            fnamegcd=media_prefix+`icnt`+".gcd"
            fstat=dircache.stat(fnamegcd)
            if del_names and fstat:
                # See if this file is in list of files to delete
                gcdcontents=dircache.readfile(fnamegcd)
                thisfile=gcdpattern.search(gcdcontents).groups()[0]
                if thisfile in del_names:
                    self.log("Deleting image "+thisfile)
                    self.progress(progresscur, progressmax, "Deleting image "+thisfile)
                    progresscur+=1
                    dircache.rmfile(fname)
                    dircache.rmfile(fnamegcd)
                    del_names.remove(thisfile)
                    fstat=False
            if new_names and not fstat:
                newname=new_names.pop()
                contents=""
                for k in media.keys():
                    if media[k]['name']==newname:
                        contents=media[k]['data']
                        break

                contentsize=len(contents)
                if contentsize:
                    gcdcontents=self.makegcd(newname,contentsize,self.__image_mimetype)
                    self.log("Writing image "+newname)
                    self.progress(progresscur, progressmax, "Deleting image "+newname)
                    progresscur+=1
                    dircache.writefile(fname,contents)
                    dircache.writefile(fnamegcd,gcdcontents)

        fstat=dircache.stat(endtransactionpath)
        self.log("Finished writing images")
        self.progress(progressmax, progressmax, "Finished writing images")
        if fstat:
            dircache.rmfile(endtransactionpath)
        result['rebootphone']=True

        return

        
class Profile(com_samsung_packet.Profile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_ ."
    RINGTONE_LIMITS= {
        'MAXSIZE': 250000
    }
    phone_manufacturer='SAMSUNG'
    phone_model='SPH-A620/152'

    def __init__(self):
        com_samsung_packet.Profile.__init__(self)
        self.numbertypetab=numbertypetab

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', None), # Image conversion needs work
        ('ringtone', 'read', None),   # all ringtone reading
        ('ringtone', 'write', None),
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('todo', 'read', None),     # all todo list reading
        ('todo', 'write', 'OVERWRITE'),  # all todo list writing
        ('memo', 'read', None),     # all memo list reading
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing
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

