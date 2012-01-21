### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_audiovoxcdm8900.py 3037 2006-04-03 00:30:28Z rogerb $

"""Communicate with the Audiovox CDM 8900 cell phone"""

# standard modules
import sha
import re

# our modules
import common
import com_phone
import com_brew
import prototypes
import p_audiovoxcdm8900

class Phone(com_phone.Phone, com_brew.BrewProtocol):
    "Talk to Audiovox CDM 8900 cell phone"

    desc="Audiovox CDM8900"
    protocolclass=p_audiovoxcdm8900
    serialsname='audiovoxcdm8900'
    pbterminator="~"  # packet terminator
    
    def __init__(self, logtarget, commport):
        "Calls all the constructors and sets initial modes"
        com_phone.Phone.__init__(self, logtarget, commport)
	com_brew.BrewProtocol.__init__(self)
        self.log("Attempting to contact phone")
        self.mode=self.MODENONE

    def getfundamentals(self, results):
        """Gets information fundamental to interopating with the phone and UI.

        Currently this is:

          - 'uniqueserial'     a unique serial number representing the phone
          - 'groups'           the phonebook groups
          - 'wallpaper-index'  map index numbers to names
          - 'ringtone-index'   map index numbers to ringtone names

        This method is called before we read the phonebook data or before we
        write phonebook data.
        """
        # use a hash of ESN and other stuff (being paranoid)
        self.log("Retrieving fundamental phone information")
        self.setmode(self.MODEBREW)
        self.log("Phone serial number")
        results['uniqueserial']=sha.new(self.getfilecontents("nvm/$SYS.ESN")).hexdigest()
        
        # now read groups
        self.log("Reading group information")
        groups={}
        for i in range(self.protocolclass._NUMGROUPS):
            req=self.protocolclass.readgroupentryrequest()
            req.number=i
            res=self.sendpbcommand(req, self.protocolclass.readgroupentryresponse)
            if res.number==self.protocolclass._ALLGROUP:
                continue  # ignore the "All" group
            if len(res.name)==0:
                continue  # must be non-blank name
            groups[i]={'name': res.name}

        results['groups']=groups

        self.log("Fundamentals retrieved")
        return results

    def getcalendar(self, result):
        raise NotImplementedError()

    def getwallpapers(self, result):
        raise NotImplementedError()

    def getringtones(self, result):
        raise NotImplementedError()

    def getphonebook(self, result):
        """Reads the phonebook data.  The L{getfundamentals} information will
        already be in result."""
        pbook={}
        req=self.protocolclass.readpbslotsrequest()
        res=self.sendpbcommand(req, self.protocolclass.readpbslotsresponse)
        slots=[x for x in range(len(res.present)) if ord(res.present[x])]
        numentries=len(slots)
        for i in range(numentries):
            req=self.protocolclass.readpbentryrequest()
            req.slotnumber=slots[i]
            res=self.sendpbcommand(req, self.protocolclass.readpbentryresponse)
            self.log("Read entry "+`i`+" - "+res.entry.name)
            self.progress(i, numentries, res.entry.name)
            entry=self.extractphonebookentry(slots[i], res.entry, result)
            pbook[i]=entry
            self.progress(i, numentries, res.entry.name)
        self.progress(numentries, numentries, "Phone book read completed")
        result['phonebook']=pbook

        for i in range(0x1e):
            req=self.protocolclass.dunnorequest()
            req.which=i
            self.sendpbcommand(req, self.protocolclass.dunnoresponse)
        
        return pbook

    def extractphonebookentry(self, slotnumber, entry, result):
        """Return a phonebook entry in BitPim format.  This is called from getphonebook."""
        res={}
        # serials
        res['serials']=[ {'sourcetype': self.serialsname, 'slot': slotnumber,
                          'sourceuniqueid': result['uniqueserial']} ]
        # numbers
        numbers=[]
        for t, v in ( ('cell', entry.mobile), ('home', entry.home), ('office', entry.office),
                      ('pager', entry.pager), ('fax', entry.fax) ):
            if len(v)==0:
                continue
            numbers.append( {'number': v, 'type': t} )
        if len(numbers):
            res['numbers']=numbers
        # name
        if len(entry.name): # yes, the audiovox can have a blank name!
            res['names']=[{'full': entry.name}]
        # emails (we treat wireless as email addr)
        emails=[]
        if len(entry.email):
            emails.append({'email': entry.email})
        if len(entry.wireless):
            emails.append({'email': entry.wireless})
        if len(emails):
            res['emails']=emails
        # memo
        if len(entry.memo):
            res['memos']=[{'memo': entry.memo}]
        # secret
        if entry.secret:
            res['flags']=[{'secret': True}]
        # group
        if entry.group in result['groups']:
            group=result['groups'][entry.group]['name']
            if group!="Etc.": # this is the "bucket" group on the phone, which we treat as no group at all
                res['categories']=[{'category': group}]
        # media
        rt=[]
        if entry.ringtone!=0xffff:
            rt.append({'ringtone': 'avox '+`entry.ringtone`, 'use': 'call'})
        if entry.msgringtone!=0xffff:
            rt.append({'ringtone': 'avox '+`entry.msgringtone`, 'use': 'message'})
        if len(rt):
            res['ringtones']=rt
        if entry.wallpaper!=0xffff:
            res['wallpapers']=[{'wallpaper': 'avox '+`entry.wallpaper`, 'use': 'call'}]
        return res

    def makephonebookentry(self, fields):
        e=self.protocolclass.pbentry()
        # some defaults
        e.secret=0
        e.previous=0xffff
        e.next=0xffff
        e.ringtone=0xffff
        e.msgringtone=0xffff
        e.wallpaper=0xffff
        for f in fields:
            setattr(e, f, fields[f])
        if e.group==0:
            raise Exception("Data error:  The group cannot be zero or the phone crashes")
        return e

    def savephonebook(self, data):
        self.log("Saving group information")

        for gid in range(1, self.protocolclass._NUMGROUPS): # do not save group 0 - All
            name=data['groups'].get(gid, {'name': ''})['name']
            req=self.protocolclass.writegroupentryrequest()
            req.number=gid
            req.anothernumber=gid
            req.name=name
            req.nummembers=data['groups'].get(gid, {'members': 0})['members']
            self.log("Group #%d %s - %d members" % (gid, `name`, req.nummembers))
            self.sendpbcommand(req, self.protocolclass.writegroupentryresponse)

        
        self.log("New phonebook\n"+common.prettyprintdict(data['phonebook']))
    
        # in theory we should offline the phone and wait two seconds first ...

        pb=data['phonebook']
        keys=pb.keys()
        keys.sort()
        keys=keys[:self.protocolclass._NUMSLOTS]
        # work out the bitmap.
        slots=[]
        for i in range(self.protocolclass._NUMSLOTS):
            if i not in keys:
                slots.append(0)
                continue
            bmp=0
            e=pb[i]
            if len(e['mobile']): bmp|=1
            if len(e['home']):   bmp|=2
            if len(e['office']): bmp|=4
            if len(e['pager']):   bmp|=8
            if len(e['fax']):   bmp|=16
            if len(e['email']):   bmp|=32
            if len(e['wireless']):   bmp|=64
            slots.append(bmp)
        slots="".join([chr(x) for x in slots])
        req=self.protocolclass.writepbslotsrequest()
        req.present=slots
        self.sendpbcommand(req, self.protocolclass.writepbslotsresponse)
        # now write out each slot
        for i in range(len(keys)):
            slot=keys[i]
            req=self.protocolclass.writepbentryrequest()
            req.slotnumber=slot
            req.entry=self.makephonebookentry(pb[slot])
            self.log('Writing entry '+`slot`+" - "+req.entry.name)
            self.progress(i, len(keys), "Writing "+req.entry.name)
            self.sendpbcommand(req, self.protocolclass.writepbentryresponse)
        self.progress(len(keys)+1, len(keys)+1, "Phone book write completed - phone will be rebooted")
        data['rebootphone']=True
        return data
       
    
    def sendpbcommand(self, request, responseclass):
        self.setmode(self.MODEBREW)
        buffer=prototypes.buffer()
        request.writetobuffer(buffer, logtitle="audiovox cdm8900 phonebook request")
        data=buffer.getvalue()
        data=common.pppescape(data+common.crcs(data))+common.pppterminator
        first=data[0]
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
            self.log("Multiple PB packets in data - taking last one starting at "+`d+1`)
            self.logdata("Original pb data", origdata, None)
            data=data[d+1:]

        # turn it back to normal
        data=common.pppunescape(data)

        # sometimes there is other crap at the begining
        d=data.find(first)
        if d>0:
            self.log("Junk at begining of pb packet, data at "+`d`)
            self.logdata("Original pb data", origdata, None)
            self.logdata("Working on pb data", data, None)
            data=data[d:]
        # take off crc and terminator
        crc=data[-3:-1]
        data=data[:-3]
        if common.crcs(data)!=crc:
            self.logdata("Original pb data", origdata, None)
            self.logdata("Working on pb data", data, None)
            raise common.CommsDataCorruption("Audiovox phonebook packet failed CRC check", self.desc)
        
        # parse data
        buffer=prototypes.buffer(data)
        res=responseclass()
        res.readfrombuffer(buffer, logtitle="Audiovox phonebook response")
        return res


        
class Profile(com_phone.Profile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=145
    WALLPAPER_CONVERT_FORMAT="jpg"

    MAX_WALLPAPER_BASENAME_LENGTH=16
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ."
    
    MAX_RINGTONE_BASENAME_LENGTH=16
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ."

    # which usb ids correspond to us
    usbids=( (0x106c, 0x2101, 1), # VID=Curitel, PID=Audiovox CDM 8900, internal modem interface
        )
    # which device classes we are.
    deviceclasses=("modem",)

    # what types of syncing we support
    _supportedsyncs=(
        ('phonebook', 'read', None),         # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'), # phonebook overwrite only
        )

    def _getgroup(self, name, groups):
        for key in groups:
            if groups[key]['name']==name:
                return key,groups[key]
        return None,None

    def normalisegroups(self, helper, data):
        "Assigns groups based on category data"

        keys=data['groups'].keys()
        keys.sort()
        pad=[data['groups'][k]['name'] for k in keys if k] # ignore key 0 - All

        groups=helper.getmostpopularcategories(self.protocolclass._NUMGROUPS, data['phonebook'], ["All", "Business", "Personal", "Etc."],
                                               self.protocolclass._MAXGROUPLEN, pad)

        # alpha sort
        groups.sort()

        # newgroups
        newgroups={}

        # put in No group
        newgroups[0]={'name': 'All', 'members': 0}

        # populate
        for name in groups:
            # existing entries remain unchanged
            if name=="All": continue
            key,value=self._getgroup(name, data['groups'])
            if key is not None and key!=0:
                newgroups[key]=value
                newgroups[key]['members']=0
                
        # new entries get whatever numbers are free
        for name in groups:
            key,value=self._getgroup(name, newgroups)
            if key is None:
                for key in range(1,10000):
                    if key not in newgroups:
                        newgroups[key]={'name': name, 'members': 0}
                        break
        # yay, done
        data['groups']=newgroups

    def convertphonebooktophone(self, helper, data):
        """Converts the data to what will be used by the phone

        @param data: contains the dict returned by getfundamentals
                 as well as where the results go"""
        self.normalisegroups(helper, data)
        results={}

        # find which entries are already known to this phone
        pb=data['phonebook']
        # decorate list with (slot, pbkey) tuples
        slots=[ (helper.getserial(pb[pbentry].get("serials", []), self.serialsname, data['uniqueserial'], "slot", None), pbentry)
                for pbentry in pb]
        slots.sort() # numeric order
        # make two lists - one contains known slots, one doesn't
        newones=[(pbentry,slot) for slot,pbentry in slots if slot is None]
        existing=[(pbentry,slot) for slot,pbentry in slots if slot is not None]
        
        for pbentry,slot in newones+existing:
            if len(results)==self.protocolclass._NUMSLOTS:
                break
            try:
                e={} # entry out
                entry=data['phonebook'][pbentry]
                e['mobile']=self.phonize(helper.getnumber(entry.get('numbers', []), 'cell'))
                e['home']=self.phonize(helper.getnumber(entry.get('numbers', []), 'home'))
                e['office']=self.phonize(helper.getnumber(entry.get('numbers', []), 'office'))
                e['pager']=self.phonize(helper.getnumber(entry.get('numbers', []), 'pager'))
                e['fax']=self.phonize(helper.getnumber(entry.get('numbers', []), 'fax'))
                emails=helper.getemails(entry.get('emails', []), 0, 2, self.protocolclass._MAXEMAILLEN)
                e['email']=""
                e['wireless']=""
                if len(emails)>=1:
                    e['email']=emails[0]
                    if len(emails)>=2:
                        e['wireless']=emails[1]

                # must be at least one number or email
                if max([len(e[field]) for field in e])==0:
                    # ::TODO:: log that we are ignoring this entry
                    continue
                        
                e['name']=helper.getfullname(entry.get('names', [ {'full': ''}]), 1, 1, self.protocolclass._MAXNAMELEN)[0]
                e['memo']=helper.getmemos(entry.get('memos', [{'memo': ''}]), 1,1, self.protocolclass._MAXMEMOLEN)[0]

                rt=helper.getringtone(entry.get('ringtones', []), 'call', "")
                if rt.startswith("avox "):
                    e['ringtone']=int(rt[5:])

                rt=helper.getringtone(entry.get('ringtones', []), 'message', "")
                if rt.startswith("avox "):
                    e['msgringtone']=int(rt[5:])

                wp=helper.getwallpaper(entry.get('wallpapers', []), 'call', "")
                if wp.startswith("avox "):
                    e['wallpaper']=int(wp[5:])

                e['secret']=helper.getflag(entry.get('flags',[]), 'secret', False)

                # deal with group
                group=helper.getcategory(entry.get('categories', [{'category': 'Etc.'}]),1,1,self.protocolclass._MAXGROUPLEN)[0]
                gid,_=self._getgroup(group, data['groups'])
                if gid is None or gid==0:
                    gid,_=self._getgroup("Etc.", data['groups'])
                assert gid!=0
                e['group']=gid
                data['groups'][gid]['members']+=1
                # find the right slot
                if slot is None or slot<0 or slot>=self.protocolclass._NUMSLOTS or slot in results:
                    for i in range(100000):
                        if i not in results:
                            slot=i
                            break
                results[slot]=e
            except helper.ConversionFailed:
                continue
        data['phonebook']=results
        return data
    

    def phonize(self, str):
        """Convert the phone number into something the phone understands

        All digits, P, T, *, #  are kept, everything else is removed.
        In theory the phone can store a dash in the phonebook, but that
        is not normal."""
        return re.sub("[^0-9PT#*]", "", str)[:self.protocolclass._MAXPHONENUMBERLEN]
