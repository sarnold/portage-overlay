### BITPIM
###
### Copyright (C) 2008 Stephen Wood <saw@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungspha900.py 3918 2007-01-19 05:15:12Z djpham $

"""Communicate with a Samsung SPH-A900"""

import sha
import re
import struct

import common
import commport
import p_brew
import p_samsungspha900
import com_brew
import com_phone
import prototypes
import helpids

numbertypetab=('cell','home','office','pager','none')

class Phone(com_phone.Phone, com_brew.BrewProtocol):
    "Talk to a Samsung SPH-A900 phone"

    desc="SPH-A900"
    helpid=helpids.ID_PHONE_SAMSUNGOTHERS
    protocolclass=p_samsungspha900
    serialsname='spha900'

    MODEPHONEBOOK="modephonebook" # can speak the phonebook protocol

    # jpeg Remove first 124 characters

    imagelocations=(
        # offset, index file, files location, origin, maximumentries, header offset
        # Offset is arbitrary.  100 is reserved for amsRegistry indexed files
        (400, "cam/dldJpeg", "camera", 100, 124),
        (300, "cam/jpeg", "camera", 100, 124),
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries, header offset
        )
        

    def __init__(self, logtarget, commport):
        com_phone.Phone.__init__(self, logtarget, commport)
        com_brew.BrewProtocol.__init__(self)
        self.numbertypetab=numbertypetab
        self.mode=self.MODENONE

    def _setmodephonebook(self):
        self.setmode(self.MODEBREW)
        req=self.protocolclass.firmwarerequest()
        respc=self.protocolclass.firmwareresponse
        try:
            self.sendpbcommand(req, respc, callsetmode=False)
            return 1
        except com_phone.modeignoreerrortypes:
            pass
        try:
            self.comm.setbaudrate(38400)
            self.sendpbcommand(req, respc, callsetmode=False)
            return 1
        except com_phone.modeignoreerrortypes:
            pass
        return 0

    def sendpbcommand(self, request, responseclass, callsetmode=True, writemode=False, numsendretry=0, returnerror=False):
        if writemode:
            numretry=3
        else:
            numretry=0
            
        if callsetmode:
            self.setmode(self.MODEPHONEBOOK)
        buffer=prototypes.buffer()

        request.writetobuffer(buffer, logtitle="Samsung phonebook request")
        data=buffer.getvalue()
        firsttwo=data[:2]
        data=common.pppescape(data+common.crcs(data))+common.pppterminator
        isendretry=numsendretry
        while isendretry>=0:
            try:
                rdata=self.comm.writethenreaduntil(data, False, common.pppterminator, logreaduntilsuccess=False, numfailures=numretry)
                break
            except com_phone.modeignoreerrortypes:
                if isendretry>0:
                    self.log("Resending request packet...")
                    time.sleep(0.3)
                else:
                    self.comm.success=False
                    self.mode=self.MODENONE
                    self.raisecommsdnaexception("manipulating the phonebook")
                isendretry-=1

        self.comm.success=True

        origdata=rdata
        # sometimes there is junk at the beginning, eg if the user
        # turned off the phone and back on again.  So if there is more
        # than one 7e in the escaped data we should start after the
        # second to last one
        d=rdata.rfind(common.pppterminator,0,-1)
        if d>=0:
            self.log("Multiple Samsung packets in data - taking last one starting at "+`d+1`)
            self.logdata("Original Samsung data", origdata, None)
            rdata=rdata[d+1:]

        # turn it back to normal
        data=common.pppunescape(rdata)

        # Sometimes there is other crap at the beginning.  But it might
        # be a Sanyo error byte.  So strip off bytes from the beginning
        # until the crc agrees, or we get to the first two bytes of the
        # request packet.
        d=data.find(firsttwo)
        crc=data[-3:-1]
        crcok=False
        for i in range(0,d+1):
            trydata=data[i:-3]
            if common.crcs(trydata)==crc:
                crcok=True
                break

        if not crcok:
            self.logdata("first two",firsttwo, None)
            self.logdata("Original Sanyo data", origdata, None)
            self.logdata("Working on Sanyo data", data, None)
            raise common.CommsDataCorruption("Sanyo packet failed CRC check", self.desc)

        res=responseclass()
        if d>0:
            if d==i:
                self.log("Junk at beginning of Sanyo packet, data at "+`d`)
                self.logdata("Original Sanyo data", origdata, None)
                self.logdata("Working on Sanyo data", data, None)
            else:
                if returnerror:
                    res=self.protocolclass.sanyoerror()
                else:
                    self.log("Sanyo Error code "+`ord(data[0])`)
                    self.logdata("sanyo phonebook response", data, None)
                    raise SanyoCommandException(ord(data[0]))
            
        data=trydata

        # parse data
        buffer=prototypes.buffer(data)
        res.readfrombuffer(buffer, logtitle="sanyo phonebook response")
        return res

    def getfundamentals(self, results):
        """Gets information fundamental to interopating with the phone and UI."""
        results['uniqueserial']=1
        return results

    def getphonebook(self,result):
        pbook={}

        count = 0
        numcount = 0
        numemail = 0
        numurl = 0

        reqname=self.protocolclass.namerequest()
        reqnumber=self.protocolclass.numberrequest()
        for slot in range(1,self.protocolclass.NUMPHONEBOOKENTRIES+1):
            reqname.slot=slot
            resname=self.sendpbcommand(reqname, self.protocolclass.nameresponse)
            bitmask=resname.entry.bitmask
            if bitmask:
                entry={}
                name=resname.entry.name
                entry['serials']=[ {'sourcetype': self.serialsname,

                                    'slot': slot,
                                    'sourceuniqueid': result['uniqueserial']} ]
                entry['names']=[{'full':name}]
                entry['numbers']=[]
                bit=1
                print resname.entry.p2,name
                for num in range(self.protocolclass.NUMPHONENUMBERS):
                    bit <<= 1
                    if bitmask & bit:
                        numslot=resname.entry.numberps[num].slot
                        reqnumber.slot=numslot
                        resnumber=self.sendpbcommand(reqnumber, self.protocolclass.numberresponse)
                        numhash={'number':resnumber.entry.num, 'type' : self.numbertypetab[resnumber.entry.numbertype-1]}
                        entry['numbers'].append(numhash)

                        print " ",self.numbertypetab[resnumber.entry.numbertype-1]+": ",numslot,resnumber.entry.num
                bit <<= 1
                if bitmask & bit:
                    reqnumber.slot=resname.entry.emailp
                    resnumber=self.sendpbcommand(reqnumber, self.protocolclass.numberresponse)
                    print " Email: ",resname.entry.emailp,resnumber.entry.num
                    entry['emails']=[]
                    entry['emails'].append({'email':resnumber.entry.num})
                bit <<= 1
                if bitmask & bit:
                    reqnumber.slot=resname.entry.urlp
                    resnumber=self.sendpbcommand(reqnumber, self.protocolclass.numberresponse)
                    print " URL:   ",resname.entry.urlp,resnumber.entry.num
                    entry['urls']=[{'url':resnumber.entry.num}]
                if resname.entry.nickname:
                    print " Nick:  ",resname.entry.nickname
                if resname.entry.memo:
                    print " Memo   ",resname.entry.memo
                    entry['memos']=[{'memo':resname.entry.memo}]

                pbook[count]=entry
                self.progress(slot, self.protocolclass.NUMPHONEBOOKENTRIES+1, name)
                count+=1
                numcount+=len(entry['numbers'])
                if entry.has_key('emails'):
                    numemail+=len(entry['emails'])
                if entry.has_key('urls'):
                    numurl+=len(entry['urls'])

        self.progress(slot,slot,"Phonebook read completed")
        self.log("Phone contains "+`count`+" contacts, "+`numcount`+" phone numbers, "+`numemail`+" Emails, "+`numurl`+" URLs")
        result['phonebook']=pbook

        return pbook

    def writewait(self):
        """Loop until phone status indicates ready to write"""
        for i in range(100):
            req=self.protocolclass.statusrequest()
            res=self.sendpbcommand(req, self.protocolclass.statusresponse)
            # print res.flag0, res.ready, res.flag2, res.flag3
            if res.ready==res.readyvalue:
                return
            time.sleep(0.1)

        self.log("Phone did not transfer to ready to write state")
        self.log("Waiting a bit longer and trying anyway")
        return

    def savephonebook(self, data):
        newphonebook={}

        nump=2
        urlp=0
        memop=0
        addressp=0
        emailp=0
        slotsused=1

        namemap=[]
        contactmap=[]
        urlmap=[]

        pbook=data['phonebook']
        self.log("Putting phone into write mode")
        req=self.protocolclass.beginendupdaterequest()
        req.beginend=1 # Start update
        res=self.sendpbcommand(req, self.protocolclass.beginendupdateresponse, writemode=True)
#        self.writewait()

        req=self.protocolclass.writeenable()
        try:
            res=self.sendpbcommand(req, self.protocolclass.writeenableresponse, writemode=True)
        except:
            pass

        keys=pbook.keys()
        keys.sort()
        nnames = len(keys)
        
        reqnumber=self.protocolclass.numberupdaterequest()
        for ikey in keys:
            ii=pbook[ikey]
            slot=slotsused
            slotsused+=1

            reqname=self.protocolclass.nameupdaterequest()
            reqname.slot=slot
            name=ii['name']
            self.progress(slot-1, nnames, "Writing "+name)
            self.log("Writing "+`name`+" to slot "+`slot`)
            namemap.append((slot,name))

            reqname.entry.name=name
            reqname.entry.name_len=ii['name_len']

            bitmask=0
            bit=1
            for numindex in range(len(ii['numbers'])):
                reqnumber.slot=nump
                reqnumber.entry.num=ii['numbers'][numindex]
                reqnumber.entry.numlen=len(ii['numbers'][numindex])
                numbertype=ii['numbertypes'][numindex]
                reqnumber.entry.numbertype=numbertype
                reqnumber.entry.pos=numindex+1

                resnumber=self.sendpbcommand(reqnumber,self.protocolclass.numberresponse)

                reqname.entry.numberps.append(nump)
                bitmask |= bit
                bit <<= 1

                nump+=1
            
            for numindex in range(len(ii['numbers']),self.protocolclass.NUMPHONENUMBERS):
                reqname.entry.numberps.append(0)

            reqname.entry.bitmask=bitmask
            resname=self.sendpbcommand(reqname,self.protocolclass.nameresponse)

        # Zero out unused slots
        for slot in range(nump,self.protocolclass.NUMPHONEBOOKENTRIES+2):
            reqnumber.slot=slot
            reqnumber.entry.num=''
            reqnumber.entry.numlen=0
            reqnumber.entry.numbertype=0
            reqnumber.entry.pos=0
            resnumber=self.sendpbcommand(reqnumber,self.protocolclass.numberresponse)
        for slot in range(slotsused,self.protocolclass.NUMPHONEBOOKENTRIES+1):
            reqname=self.protocolclass.nameupdaterequest()
            reqname.slot=slot
            reqname.entry.name=''
            reqname.entry.name_len=0
            for numindex in range(self.protocolclass.NUMPHONENUMBERS):
                reqname.entry.numberps.append(0)
            reqname.entry.bitmask=0
            resname=self.sendpbcommand(reqname,self.protocolclass.nameresponse)

        self.progress(1,1, "Phonebook write completed")

        req=self.protocolclass.beginendupdaterequest()
        req.beginend=2 # Finish update
        res=self.sendpbcommand(req, self.protocolclass.beginendupdateresponse, writemode=True)
        req=p_brew.setmodemmoderequest()
        res=self.sendpbcommand(req, p_brew.setmoderesponse, writemode=True)
        #data['rebootphone']=1

    def getcalendar(self, results):
        return result

    getwallpapers=None
    getringtones=None


class Profile(com_phone.Profile):
    deviceclasses=("modem",)

    usbids=( ( 0x04e8, 0x6601, 1),  # Samsung internal USB interface
        )
    # which device classes we are.
    deviceclasses=("modem","serial")

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SAMSUNG'
    phone_model='SPH-A900/154'

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
    )
    
    def __init__(self):
        self.numbertypetab=numbertypetab
        com_phone.Profile.__init__(self)

    def convertphonebooktophone(self, helper, data):
        "Converts the data to what will be used by the phone"

        results={}

        slotsused={}
        pb=data['phonebook']
        for pbentry in pb:
            entry=pb[pbentry]
            slot=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'slot', -1)
            if(slot > 0 and slot <= self.protocolclass.NUMPHONEBOOKENTRIES):
                slotsused[slot]=1

        lastunused=0 # One more than last unused slot
        
        for pbentry in pb:
            e={} # entry out
            entry=pb[pbentry] # entry in
            try:
                try:
                    e['name']=helper.getfullname(entry.get('names', []),1,1,20)[0]
                except:
                    e['name']=''
                e['name_len']=len(e['name'])
                if len(e['name'])==0:
                    print "Entry with no name"

#                cat=helper.makeone(helper.getcategory(entry.get('categories',[]),0,1,16), None)
#                if cat is None:
#                    e['group']=0
#                else:
#                    key,value=self._getgroup(cat, data['groups'])
#                    if key is not None:
#                        e['group']=key
#                    else:
#                        e['group']=0
                e['group']=0

                serial1=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'slot', -1)

                if(slot > 0 and slot <= self.protocolclass.NUMPHONEBOOKENTRIES):
                    e['slot']=slot
                else:  # A new entry.  Must find unused slot
                    while(slotsused.has_key(lastunused)):
                        lastunused+=1
                        if(lastunused > self.protocolclass.NUMPHONEBOOKENTRIES):
                            raise helper.ConversionFailed()
                    e['slot']=lastunused
                    slotsused[lastunused]=1

#                e['emails']=helper.getemails(entry.get('emails', []),0,self.protocolclass.NUMEMAILS,self.protocolclass.MAXEMAILLEN)

#                e['url']=helper.makeone(helper.geturls(entry.get('urls', []), 0,1,self.protocolclass.MAXURLLEN), "")

                e['memo']=helper.makeone(helper.getmemos(entry.get('memos', []), 0,1,self.protocolclass.MAXMEMOLEN), "")

                numbers=helper.getnumbers(entry.get('numbers', []),0,self.protocolclass.NUMPHONENUMBERS)
                e['numbertypes']=[]
                e['numbers']=[]
                e['numberspeeds']=[]
                
                for numindex in range(len(numbers)):
                    num=numbers[numindex]
                    type=num['type']
                    numtype=len(self.numbertypetab) # None type is default
                    for i,t in enumerate(self.numbertypetab):
                        if type==t:
                            numtype=i+1
                            break
                    # If type not found, give it "none" type
                    e['numbertypes'].append(numtype)

                    # Need to enforce phone number length limit
                    number=self.phonize(num['number'])
                    e['numbers'].append(number)

                    # deal with speed dial
#                    sd=num.get("speeddial", 0xFF)
#                    if sd>=self.protocolclass.FIRSTSPEEDDIAL and sd<=self.protocolclass.LASTSPEEDDIAL:
#                        e['numberspeeds'].append(sd)
#                    else:
#                        e['numberspeeds'].append(0)
                    
                #e['numberspeeds']=helper.filllist(e['numberspeeds'], self.protocolclass.NUMPHONENUMBERS, 0xFF)
                #e['numbertypes']=helper.filllist(e['numbertypes'], self.protocolclass.NUMPHONENUMBERS, 0)
                #e['numbers']=helper.filllist(e['numbers'], self.protocolclass.NUMPHONENUMBERS, "")
                

                e['ringtone']=helper.getringtone(entry.get('ringtones', []), 'call', None)
                e['wallpaper']=helper.getwallpaper(entry.get('wallpapers', []), 'call', None)

                e['secret']=helper.getflag(entry.get('flags', []), 'secret', False)
                results[pbentry]=e
                
            except helper.ConversionFailed:
                #self.log("No Free Slot for "+e['name'])
                print "No Free Slot for "+e['name']
                continue

        data['phonebook']=results
        return data
