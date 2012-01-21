### BITPIM
###
### Copyright (C) 2007 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungsphm300media.py 4530 2007-12-28 03:15:46Z djpham $

"""Communicate with the Samsung SPH-M300 through the diag port (Diag)"""

import sha

import common
import commport
import com_brew
import com_phone
import com_samsung_packet
import fileinfo
import helpids
import prototypes
import p_brew
import p_samsungsphm300
import re

class Phone(com_phone.Phone, com_brew.BrewProtocol):
    "Talk to a Samsung SPH-M300 (Diag) phone"

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
    builtingroups=('Unassigned', 'Family', 'Friends', 'Colleagues',
                   'VIPs', None)

    __audio_mimetype={ 'mid': 'audio/midi', 'qcp': 'audio/vnd.qcelp', 'pmd': 'application/x-pmd'}
    __image_mimetype={ 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif', 'bmp': 'image/bmp', 'png': 'image/png'}

    def __init__(self, logtarget, commport):
        com_phone.Phone.__init__(self, logtarget, commport)
	com_brew.BrewProtocol.__init__(self)
        self.mode=self.MODENONE

    def read_groups(self):
        """Read and return the group dict"""
        _buf=prototypes.buffer(self.getfilecontents(self.protocolclass.group_file_name))
        _groups=self.protocolclass.GroupFile()
        _groups.readfrombuffer(_buf, logtitle='Reading Group File')
        _res={}
        for _idx,_item in enumerate(_groups.entry):
            _res[_idx]={ 'name': _item.name if _item.num0 else \
                         self.builtingroups[_idx] }
        return _res
    def getfundamentals(self, results):
        """Gets information fundamental to interopating with the phone and UI."""
        self.log("Retrieving fundamental phone information")
        self.log("Phone serial number")
        results['uniqueserial']=sha.new(self.get_brew_esn()).hexdigest()
        results['groups']=self.read_groups()
        self.getmediaindex(results)
        return results

    def _get_camera_index(self, res):
        """Get the index of images stored in the camera"""
        _cnt=self.protocolclass.camera_index
        for _item in self.listfiles(self.protocolclass.camera_dir).values():
            res[_cnt]={ 'name': self.basename(_item['name']),
                        'location': _item['name'],
                        'origin': self.protocolclass.camera_origin }
            _cnt+=1
    def _get_savedtophone_index(self, res):
        """Get the index of saved-to-phone images"""
        _cnt=self.protocolclass.savedtophone_index
        for _item in self.listfiles(self.protocolclass.savedtophone_dir).values():
            res[_cnt]={ 'name': self.basename(_item['name']),
                        'location': _item['name'],
                        'origin': self.protocolclass.savedtophone_origin }
            _cnt+=1
    def _get_builtin_index(self, rt_index, wp_index):
        """Get the indices of builtin ringtones and wallpapers"""
        for _idx,_item in enumerate(self.builtinringtones):
            rt_index[_idx]={ 'name': _item,
                             'origin': 'builtin' }
        for _idx, _item in enumerate(self.builtinimages):
            wp_index[_idx]={ 'name': _item,
                             'origin': 'builtin' }
    def _get_ams_index(self, rt_index, wp_index):
        """Get the index of ringtones and wallpapers in AmsRegistry"""
        buf=prototypes.buffer(self.getfilecontents(self.protocolclass.AMSREGISTRY))
        ams=self.protocolclass.amsregistry()
        ams.readfrombuffer(buf, logtitle="Read AMS registry")
        _wp_cnt=self.protocolclass.ams_index
        _rt_cnt=self.protocolclass.ams_index
        for i in range(ams.nfiles):
            _type=ams.info[i].filetype
            if _type==self.protocolclass.FILETYPE_RINGER:
                rt_index[_rt_cnt]={ 'name': ams.filename(i),
                                    'location': ams.filepath(i),
                                    'origin': 'ringers' }
                _rt_cnt+=1
            elif _type==self.protocolclass.FILETYPE_WALLPAPER:
                wp_index[_wp_cnt]={ 'name': ams.filename(i),
                                    'location': ams.filepath(i),
                                    'origin': 'images' }
                _wp_cnt+=1

    def getmediaindex(self, results):
        wp_index={}
        rt_index={}
        self._get_builtin_index(rt_index, wp_index)
        self._get_camera_index(wp_index)
        self._get_savedtophone_index(wp_index)
        self._get_ams_index(rt_index, wp_index)
        results['ringtone-index']=rt_index
        results['wallpaper-index']=wp_index

    def getringtones(self, results):
        _media={}
        _rt_index=results.get('ringtone-index', {})
        for _item in _rt_index.values():
            if _item.get('origin', None)=='ringers':
                _media[_item['name']]=self.getfilecontents(_item['location'],
                                                           True)
        results['ringtone']=_media

    def getwallpapers(self, results):
        _media={}
        _wp_index=results.get('wallpaper-index', {})
        for _item in _wp_index.values():
            _origin=_item.get('origin', None)
            _name=_item['name']
            if _origin=='images':
                _media[_name]=self.getfilecontents(_item['location'],
                                                   True)
            elif _origin in (self.protocolclass.camera_origin,
                             self.protocolclass.savedtophone_origin):
                _buf=prototypes.buffer(self.getfilecontents(_item['location'],
                                                            True))
                _cam=self.protocolclass.CamFile()
                _cam.readfrombuffer(_buf, logtitle='Reading CAM file')
                _item['name']=_cam.filename
                _media[_item['name']]=_cam.jpeg
        results['wallpapers']=_media

    # Following code lifted from module com_samsungspha620 
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
        media_names=[x['name'] for x in media.values() \
                     if x.get('origin', None)=='ringers' ]
        index_names=[x['name'] for x in media_index.values() \
                     if x.get('origin', None)=='ringers' ]
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
        media_index=result.get('wallpaper-index', {})
        media_names=[x['name'] for x in media.values() \
                     if x.get('origin', None)=='images' ]
        index_names=[x['name'] for x in media_index.values() \
                     if x.get('origin', None)=='images' ]
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

    # Phone detection stuff-----------------------------------------------------
    def is_mode_brew(self):
        req=p_brew.memoryconfigrequest()
        respc=p_brew.memoryconfigresponse
        
        for baud in 0, 38400, 115200:
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            try:
                self.sendbrewcommand(req, respc, callsetmode=False)
                return True
            except com_phone.modeignoreerrortypes:
                pass
        return False

    def get_detect_data(self, res):
        try:
            req=p_brew.firmwarerequest()
            resp=self.sendbrewcommand(req, p_brew.data)
            res['firmwareresponse']=resp.bytes
        except com_brew.BrewBadBrewCommandException:
            pass

    def eval_detect_data(self, res):
        _fw=res['firmwareresponse']
        if len(_fw)>47 and _fw[39:47]=='SPH-M300':
            # found it
            res['model']=Profile.phone_model
            res['manufacturer']=Profile.phone_manufacturer
            res['esn']=self.get_brew_esn()

    @classmethod
    def detectphone(_, coms, likely_ports, res, _module, _log):
        if not likely_ports:
            # cannot detect any likely ports
            return None
        for port in likely_ports:
            if not res.has_key(port):
                res[port]={ 'mode_modem': None, 'mode_brew': None,
                            'manufacturer': None, 'model': None,
                            'firmware_version': None, 'esn': None,
                            'firmwareresponse': None }
            try:
                if res[port]['mode_brew']==False or \
                   res[port]['model']:
                    # either phone is not in BREW, or a model has already
                    # been found, not much we can do now
                    continue
                p=_module.Phone(_log, commport.CommConnection(_log, port, timeout=1))
                if res[port]['mode_brew'] is None:
                    res[port]['mode_brew']=p.is_mode_brew()
                if res[port]['mode_brew']:
                    p.get_detect_data(res[port])
                p.eval_detect_data(res[port])
                p.comm.close()
            except:
                if __debug__:
                    raise

    getphonebook=NotImplemented
    getcalendar=NotImplemented

parentprofile=com_samsung_packet.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=160

    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_ ."
    RINGTONE_LIMITS= {
        'MAXSIZE': 250000
    }
    phone_manufacturer='SAMSUNG'
    phone_model='SPH-M300MEDIA'
    numbertypetab=Phone.numbertypetab

    usbids=( ( 0x04e8, 0x6640, 2),)
    deviceclasses=("serial",)

    ringtoneorigins=('ringers',)
    excluded_ringtone_origins=('ringers',)

    excluded_wallpaper_origins=('camera', 'camera-fullsize')
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "camera"))
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "camera-fullsize"))
    def GetImageOrigins(self):
        return self.imageorigins

    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 128, 'height': 160, 'format': "JPEG"}))
    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets

    _supportedsyncs=(
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', None), # Image conversion needs work
        ('ringtone', 'read', None),   # all ringtone reading
        ('ringtone', 'write', None),
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
                'first': 0, 'middle': 0, 'last': 0, 'full': 0,
                'nickname': 0, 'details': 0 },
            'number': {
                'type': 0, 'speeddial': 0, 'number': 5, 'details': 0 },
            'email': 0,
            'address': {
                'type': 0, 'company': 0, 'street': 0, 'street2': 0,
                'city': 0, 'state': 0, 'postalcode': 0, 'country': 0,
                'details': 0 },
            'url': 0,
            'memo': 0,
            'category': 0,
            'wallpaper': 0,
            'ringtone': 0,
            'storage': 0,
            },
        'calendar': {
            'description': False, 'location': False, 'allday': False,
            'start': False, 'end': False, 'priority': False,
            'alarm': False, 'vibrate': False,
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
            'memo': False,
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
