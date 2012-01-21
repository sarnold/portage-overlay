### BITPIM
###
### Copyright (C) 2003-2007 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo.py 4785 2010-01-15 07:03:24Z hjelmn $

"""Phonebook conversations with Sanyo phones"""

# standard modules
import re
import time
import cStringIO
import sha
import datetime

# BitPim modules
import com_brew
import com_phone
import p_sanyo
import prototypes
import common
import conversions
import bpcalendar
import call_history
import sms
import todo
import helpids

numbertypetab=( 'home', 'office', 'cell', 'pager',
                    'data', 'fax', 'none' )

class SanyoCommandException(Exception):
    def __init__(self, errnum, str=None):
        if str is None:
            str="Sanyo Packet Error 0x%02x" % (errnum,)
        Exception.__init__(self, str)
        self.errnum=errnum

class SanyoPhonebook:
    "Talk to a Sanyo Sprint Phone such as SCP-4900, SCP-5300, or SCP-8100"
    
    # phone uses Jan 1, 1980 as epoch.  Python uses Jan 1, 1970.  This is difference
    # plus a fudge factor of 5 days for no reason I can find
    _sanyoepochtounix=315532800+432000;

    pbterminator="\x7e"
    MODEPHONEBOOK="modephonebook" # can speak the phonebook protocol

    calendar_defaultringtone=0
    calendar_defaultcaringtone=0
    calendar_voicenumber=0
    phonebook_voicenumber=0

    def __init__(self):
        self.numbertypetab=numbertypetab
    
    def get_esn(self):
        req=self.protocolclass.esnrequest()
        res=self.sendpbcommand(req, self.protocolclass.esnresponse)
        return '%08X'%res.esn

    def _setmodephonebook(self):
        self.setmode(self.MODEBREW)
        req=p_sanyo.firmwarerequest()
        respc=p_sanyo.firmwareresponse
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
        
    def getmediaindices(self, results):
        """Get all the media indices

        @param results: places results in this dict
        """
        # Do all media types in one function to avoid having to scan through
        # directories more than once
        ringermedia={}
        imagemedia={}

        c=1
        for name in self.builtinimages:
            if name:
                imagemedia[c]={'name': name, 'origin': 'builtin' }
                # print c,name
            c+=1
        results['wallpaper-index']=imagemedia
        c=1
        for name in self.builtinringtones:
            if name:
                ringermedia[c]={'name': name, 'origin': 'builtin' }
                # print c,name
            c+=1
        results['ringtone-index']=ringermedia

        return

        wallpaper = self.getsanyobuffer(self.protocolclass.wallpaperbuffer)
        for i in range(0, self.protocolclass._NUMPBSLOTS):
            if wallpaper.wallpapers[i].flag:
                print i, wallpaper.wallpapers[i].word1, wallpaper.wallpapers[i].word2

        req=self.protocolclass.bufferpartrequest()

        req.header.command=0xc8
        req.header.packettype=0x0c
        res=self.sendpbcommand(req, self.protocolclass.bufferpartresponse)
        #req.header.command=0x69
        #req.header.packettype=0x0f
        #res=self.sendpbcommand(req, self.protocolclass.bufferpartresponse)
        #req.header.command=0x6a
        #res=self.sendpbcommand(req, self.protocolclass.bufferpartresponse)
        #req.header.command=0x6b
        #res=self.sendpbcommand(req, self.protocolclass.bufferpartresponse)
        
        req.header.packettype=0x0c
        req.header.command=0x49
        res=self.sendpbcommand(req, self.protocolclass.bufferpartresponse)
        req.header.command=0xc8
        res=self.sendpbcommand(req, self.protocolclass.bufferpartresponse)

        if not self.serialsname == 'scp4900':
            # 4900 doesn't like this
            req.header.command=0xc9
            res=self.sendpbcommand(req, self.protocolclass.bufferpartresponse)

        return
        
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
            if name:
                media[c]={'name': name, 'origin': 'builtin' }
                # print c,name
            c+=1

        results[key]=media
        return media

    def getwallpaperindices(self, results):
        return self.getmediaindex(self.builtinimages, self.imagelocations, results, 'wallpaper-index')

    def getringtoneindices(self, results):
        return self.getmediaindex(self.builtinringtones, self.ringtonelocations, results, 'ringtone-index')

    def getsanyobuffer(self, responseclass):
        # Read buffer parts and concatenate them together
        bufres=responseclass()
        desc="Reading "+bufres.comment
        data=cStringIO.StringIO()
        bufp=0
        command=bufres.startcommand
        buffersize=bufres.bufsize
        req=self.protocolclass.bufferpartrequest()
        if command==0xd7:
            req.header.packettype=0x0c # Special Case for 5500 Class phones
        for offset in range(0, buffersize, req.bufpartsize):
            self.progress(data.tell(), buffersize, desc)
            req.header.command=command
            res=self.sendpbcommand(req, self.protocolclass.bufferpartresponse);
            data.write(res.data)
            command+=1

        self.progress(1,1,desc)

        data=data.getvalue()
        self.log("expected size "+`buffersize`+"  actual "+`len(data)`)
        assert buffersize==len(data)
        buffer=prototypes.buffer(data)
        bufres.readfrombuffer(buffer, logtitle="Sanyo buffer response")
        return bufres

    def sendsanyobuffer(self, bufreq):
        comment=bufreq.comment
        buffer=prototypes.buffer()
        bufreq.writetobuffer(buffer, logtitle="Send sanyo buffer")
        buffer=buffer.getvalue()
        self.log("Writing "+comment+" "+` len(buffer) `+" bytes")
        desc="Writing "+comment
        req=self.protocolclass.bufferpartupdaterequest()
        bufpartsize=req.bufpartsize
        numblocks=len(buffer)/bufpartsize
        offset=0
        command=bufreq.startcommand
        if command==0xd7:
            req.header.packettype=0x0c
        for offset in range(0, len(buffer), bufpartsize):
            self.progress(offset/bufpartsize, numblocks, desc)
            req.header.command=command
            block=buffer[offset:]
            l=min(len(block), bufpartsize)
            block=block[:l]
            req.data=block
            command+=1
            self.sendpbcommand(req, self.protocolclass.bufferpartresponse, writemode=True)
        
    def sendpbcommand(self, request, responseclass, callsetmode=True, writemode=False, numsendretry=0, returnerror=False):
        if writemode:
            numretry=3
        else:
            numretry=0
            
        if callsetmode:
            self.setmode(self.MODEPHONEBOOK)
        buffer=prototypes.buffer()

        request.writetobuffer(buffer, logtitle="Sanyo phonebook request")
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
            self.log("Multiple Sanyo packets in data - taking last one starting at "+`d+1`)
            self.logdata("Original Sanyo data", origdata, None)
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

        # use a hash of ESN and other stuff (being paranoid)
        print "HASRINGPICBUF=",self.protocolclass.HASRINGPICBUF
        self.log("Retrieving fundamental phone information")
        self.log("Phone serial number")
        results['uniqueserial']=sha.new(self.getfilecontents("nvm/$SYS.ESN")).hexdigest()

        #self.getwallpaperindices(results)
        #self.getringtoneindices(results)
        self.getmediaindices(results)
        self.log("Fundamentals retrieved")
        return results

    def sanyosort(self, a, b):
        "Sanyo sort order.  Case insensitive, letters first"
        x=a[1]
        y=b[1]
        # This is right only for first column
        if(x[0:1].isalpha() and not y[0:1].isalpha()):
            return -1
        if(y[0:1].isalpha() and not x[0:1].isalpha()):
            return 1
        return cmp(x.lower(), y.lower())
    
    def getsms(self, result):
        gsms = {}
        self.log("Getting sms entries")
        req=self.protocolclass.messagerequest()
        for box in range(2):
            if box==0:
                req=self.protocolclass.messagerequest()
                respc=self.protocolclass.messageresponse
            else:
                req=self.protocolclass.messagesentrequest()
                respc=self.protocolclass.messagesentresponse
            for slot in range(self.protocolclass.NUMMESSAGESLOTS):
                req.slot=slot
                res=self.sendpbcommand(req, respc)
                if res.entry.dunno4==2:
                    entry=sms.SMSEntry()
                    entry.datetime="%04d%02d%02dT%02d%02d%02d" % ((2000 + res.entry.year, res.entry.month, res.entry.day, res.entry.hour,res.entry.minute, res.entry.second))
                    if box==0:
                        entry.folder=entry.Folder_Inbox
                        entry._from=res.entry.phonenum
                    else:
                        entry.folder=entry.Folder_Sent
                        entry._to=res.entry.phonenum
                        #entry.add_recipient(res.entry.phonenum,confirmed=True)
                    if res.entry.read==17:
                        entry.read=1
                    else:
                        entry.read=0
                    entry.callback=res.entry.callback
                    entry.subject=res.entry.message[:12]
                    self.log(res.entry.message[:8])
                    if res.entry.priority==100:
                        entry.priority=sms.SMSEntry.Priority_Normal
                    if res.entry.priority==200:
                        entry.priority=sms.SMSEntry.Priority_High
                    entry.text=res.entry.message
                    gsms[entry.id]=entry
                    result['sms']=gsms
        return result

    def gettodo(self, result):
        gtodo = {}
        self.log("Getting todo entries")
        req=self.protocolclass.todorequest()
        for slot in range(self.protocolclass.NUMTODOSLOTS):
            req.slot=slot
            res=self.sendpbcommand(req, self.protocolclass.todoresponse)
            entry=todo.TodoEntry()
            if res.entry.flag:
                entry.summary=res.entry.todo
                if res.entry.priority==2:
                    entry.status=4
                if res.entry.priority==0:
                    entry.priority=5
                if res.entry.priority==1:
                    entry.priority=1
                gtodo[entry.id]=entry
                result['todo']=gtodo
        return result

    def getphonebook(self,result):
        pbook={}
        # Get Sort buffer so we know which of the 300 phone book slots
        # are in use.
        sortstuff = self.getsanyobuffer(self.protocolclass.pbsortbuffer)

        # Get the ringer and wall paper assignments
        if self.protocolclass.HASRINGPICBUF:
            ringpic = self.getsanyobuffer(self.protocolclass.ringerpicbuffer)

        speedslot=[]
        speedtype=[]
        for i in range(self.protocolclass._NUMSPEEDDIALS):
            speedslot.append(sortstuff.speeddialindex[i].pbslotandtype & 0xfff)
            numtype=(sortstuff.speeddialindex[i].pbslotandtype>>12)-1
            if(numtype >= 0 and numtype <= len(self.numbertypetab)):
                speedtype.append(self.numbertypetab[numtype])
            else:
                speedtype.append("")

        numentries=sortstuff.slotsused
        self.log("There are %d entries" % (numentries,))
        
        count = 0 # Number of phonebook entries
        numcount = 0 # Number of phone numbers
        numemail = 0 # Number of emails
        numurl = 0 # Number of urls
        res=self.protocolclass.phonebookentry()
        usedefaultnum = 'defaultnum' in res.getfields()
        print "usedefaultnum =",usedefaultnum

        req=self.protocolclass.phonebookslotrequest()
        for i in range(0, self.protocolclass._NUMPBSLOTS):
            if sortstuff.usedflags[i].used:
                ### Read current entry
                req.slot = i
                res=self.sendpbcommand(req, self.protocolclass.phonebookslotresponse)
                self.log("Read entry "+`i`+" - "+res.entry.name)

                entry=self.extractphonebookentry(res.entry, result)
                # Speed dials
                for j in range(len(speedslot)):
                    if(speedslot[j]==req.slot):
                        for k in range(len(entry['numbers'])):
                            if(entry['numbers'][k]['type']==speedtype[j]):
                                entry['numbers'][k]['speeddial']=j+2
                                break

                if self.protocolclass.HASRINGPICBUF:
                    # ringtones
                    if ringpic.ringtones[i].ringtone>0:
                        print res.entry.name,ringpic.ringtones[i].ringtone
                        try:
                            tone=result['ringtone-index'][ringpic.ringtones[i].ringtone]['name']
                        except:
                            tone=self.serialsname+"Index_"+`ringpic.ringtones[i].ringtone`
                        entry['ringtones']=[{'ringtone': tone, 'use': 'call'}]

                    # wallpapers
                    if ringpic.wallpapers[i].wallpaper>0:
                        try:
                            paper=result['wallpaper-index'][ringpic.wallpapers[i].wallpaper]['name']
                        except:
                            paper=self.serialsname+"Index_"+`ringpic.wallpapers[i].wallpaper`
                        entry['wallpapers']=[{'wallpaper': paper, 'use': 'call'}]
                    
                # Set default number, swap with first number
                if usedefaultnum:
                    firsttype=res.entry.defaultnum-1
                    if firsttype < len(self.numbertypetab):
                        defaulttype=self.numbertypetab[firsttype]
                        k=0
                        for j in range(len(entry['numbers'])):
                            if entry['numbers'][j]['type'] == defaulttype:
                                k=j
                                break
                        if k>0:
                            exchange=entry['numbers'][k]
                            for kk in range(k,0,-1):
                                entry['numbers'][kk]=entry['numbers'][kk-1]
                            entry['numbers'][0]=exchange
            
                pbook[count]=entry 
                self.progress(count, numentries, res.entry.name)
                count+=1
                numcount+=len(entry['numbers'])
                if entry.has_key('emails'):
                    numemail+=len(entry['emails'])
                if entry.has_key('urls'):
                    numurl+=len(entry['urls'])
        
        self.progress(numentries, numentries, "Phone book read completed")
        self.log("Phone contains "+`count`+" contacts, "+`numcount`+" phone numbers, "+`numemail`+" Emails, "+`numurl`+" URLs")
        result['phonebook']=pbook
        return pbook

    def extractphonebookentry(self, entry, fundamentals):
        """Return a phonebook entry in BitPim format"""
        res={}
        # serials
        res['serials']=[ {'sourcetype': self.serialsname, 'serial1': entry.slot, 'serial2': entry.slotdup,
                          'sourceuniqueid': fundamentals['uniqueserial']} ]
        # only one name
        res['names']=[ {'full': entry.name} ]
        # only one email
        if len(entry.email):
            res['emails']=[ {'email': entry.email} ]
        # only one url
        if len(entry.url):
            res['urls']=[ {'url': entry.url} ]
        # private
        res['flags']=[ {'secret': entry.secret } ]
        # 7 phone numbers
        res['numbers']=[]
        numberindex = 0
        for type in self.numbertypetab:
            if len(entry.numbers[numberindex].number):
                res['numbers'].append({'number': entry.numbers[numberindex].number, 'type': type })
            
            numberindex+=1
        return res

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
        
    def makeentry(self, entry, dict):
        # dict is unused at moment, will be used later to convert string ringtone/wallpaper to numbers??
        # This is stolen from com_lgvx4400 and modified for the Sanyo as
        # we start to develop a vague understanding of what it is for.
        e=self.protocolclass.phonebookentry()
        
        for k in entry:
            # special treatment for lists
            if k=='ringtones' or k=='wallpapers' or k=='numbertypes':
                continue
            if k=='numbers':
                for numberindex in range(self.protocolclass.NUMPHONENUMBERS):
                    enpn=self.protocolclass.phonenumber()
                    e.numbers.append(enpn)
                    
                for i in range(len(entry[k])):
                    numberindex=entry['numbertypes'][i]
                    e.numbers[numberindex].number=entry[k][i]
                    e.numbers[numberindex].number_len=len(e.numbers[numberindex].number)
                continue
            # everything else we just set
            setattr(e,k,entry[k])
        return e

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
        # Overwrite the phonebook in the phone with the data.
        # As we write the phone book slots out, we need to build up
        # the indices in the callerid, ringpic and pbsort buffers.
        # We could save some writing by reading the phonebook slots first
        # and then only writing those that are different, but all the buffers
        # would still need to be written.
        #

        newphonebook={}
        self.mode=self.MODENONE
        self.setmode(self.MODEBREW) # see note in getphonebook in com_lgvx4400 for why this is necessary
        self.setmode(self.MODEPHONEBOOK)

###
### Create Sanyo buffers and Initialize lists
###
        sortstuff=self.protocolclass.pbsortbuffer()
        ringpic=self.protocolclass.ringerpicbuffer()
        callerid=self.protocolclass.calleridbuffer()

        res=self.protocolclass.phonebookentry()
        usedefaultnum = 'defaultnum' in res.getfields()

        for i in range(self.protocolclass._NUMPBSLOTS):
            sortstuff.usedflags.append(0)
            sortstuff.firsttypes.append(0)
            sortstuff.sortorder.append(0xffff)
            sortstuff.sortorder2.append(0xffff)
            sortstuff.emails.append(0xffff)
            sortstuff.urls.append(0xffff)
            ringpic.ringtones.append(0)
            ringpic.wallpapers.append(0)

        for i in range(self.protocolclass._NUMSPEEDDIALS):
            sortstuff.speeddialindex.append(0xffff)

        for i in range(self.protocolclass._NUMLONGNUMBERS):
            sortstuff.longnumbersindex.append(0xffff)
        
            
###
### Initialize mappings
###
        namemap=[]
        emailmap=[]
        urlmap=[]

        callerid.numentries=0
        
        pbook=data['phonephonebook'] # Get converted phonebook
        self.log("Putting phone into write mode")
        req=self.protocolclass.beginendupdaterequest()
        req.beginend=1 # Start update
        res=self.sendpbcommand(req, self.protocolclass.beginendupdateresponse, writemode=True)

        self.writewait()
        
        keys=pbook.keys()
        keys.sort()
        sortstuff.slotsused=len(keys)
        sortstuff.numemail=0
        sortstuff.numurl=0

        progresscur=0
        progressmax=len(keys)
        self.log("Writing %d entries to phone" % (len(keys),))
        nlongphonenumbers=0
        nonumbercount=0
        for ikey in keys:
            ii=pbook[ikey]
            slot=ii['slot'] # Or should we just use i for the slot
            # Will depend on Profile to keep the serial numbers in range
            progresscur+=1
            self.progress(progresscur, progressmax, "Writing "+ii['name'])
            self.log("Writing entry "+`slot`+" - "+ii['name'])
            entry=self.makeentry(ii, data)
            if not usedefaultnum:
                delattr(entry,'defaultnum')
            req=self.protocolclass.phonebookslotupdaterequest()
            req.entry=entry
            res=self.sendpbcommand(req, self.protocolclass.phonebookslotresponse, writemode=True)
            # Put entry into newphonebooks
            entry=self.extractphonebookentry(entry, data)
            entry['ringtones']=[{'ringtone': ii['ringtone'], 'use': 'call'}]
            entry['wallpapers']=[{'wallpaper': ii['wallpaper'], 'use': 'call'}]
            

# Accumulate information in and needed for buffers
            sortstuff.usedflags[slot].used=1
            if(len(ii['numbers'])):
                sortstuff.firsttypes[slot].firsttype=min(ii['numbertypes'])+1
            else:
                if(len(ii['email'])):
                    sortstuff.firsttypes[slot].firsttype=8
                    nonumbercount+=1
                elif(len(ii['url'])):
                    sortstuff.firsttypes[slot].firsttype=9
                    nonumbercount+=1
                else:
                    sortstuff.firsttypes[slot].firsttype=0
                    
# Fill in Caller ID buffer
# Want to move this out of this loop.  Callerid buffer is 500 numbers, but
# can potentially hold 2100 numbers.  Would like to preferentially put the
# first number for each name in this buffer.
# If more than 500 numbers are in phone, the phone won't let you add
# any more. So we should probably respect this limit.
            for i in range(len(ii['numbers'])):
                nindex=ii['numbertypes'][i]
                speeddial=ii['speeddials'][i]
                code=slot+((nindex+1)<<12)
                if(speeddial>=2 and speeddial<=self.protocolclass._NUMSPEEDDIALS+1):
                    sortstuff.speeddialindex[speeddial-2]=code
                    for k in range(len(entry['numbers'])):
                        if(entry['numbers'][k]['type']==nindex):
                            entry['numbers'][k]['speeddial']=speeddial
                            break
                if(callerid.numentries<callerid.maxentries):
                    phonenumber=ii['numbers'][i]
                    cidentry=self.makecidentry(phonenumber,slot,nindex)
                    callerid.items.append(cidentry)
                    callerid.numentries+=1
                    if(len(phonenumber)>self.protocolclass._LONGPHONENUMBERLEN):
                        if(nlongphonenumbers<self.protocolclass._NUMLONGNUMBERS):
                            sortstuff.longnumbersindex[nlongphonenumbers].pbslotandtype=code

            namemap.append((slot,ii['name']))
            if(len(ii['email'])):
                emailmap.append((slot,ii['email']))
                sortstuff.numemail+=1
            if(len(ii['url'])):
                urlmap.append((slot,ii['url']))
                sortstuff.numurl+=1
            # Add ringtone and wallpaper
            ringpic.ringtones[slot].ringtone=self._findmediaindex(data['ringtone-index'], ii['ringtone'],ii['name'],'ringtone')
            ringpic.wallpapers[slot].wallpaper=self._findmediaindex(data['wallpaper-index'], ii['wallpaper'],ii['name'],'wallpaper')

            newphonebook[slot]=entry

        sortstuff.slotsused2=len(keys)-nonumbercount
        # Sort Names, Emails and Urls for the sort buffer
        # The phone sorts case insensitive and puts numbers after the
        # letters.
        i=0
        j=0
        sortstuff.pbfirstletters=""
        namemap.sort(self.sanyosort)
        for (slot, name) in namemap:
            sortstuff.sortorder[i].pbslot=slot
            if sortstuff.firsttypes[slot].firsttype<=7:
                sortstuff.sortorder2[j].pbslot=slot
                j+=1
            if name:
                sortstuff.pbfirstletters+=name[0]
            else:
                sortstuff.pbfirstletters+=chr(0)
            i+=1

        i=0
        sortstuff.emailfirstletters=""
        emailmap.sort(self.sanyosort)
        for (slot, email) in emailmap:
            sortstuff.emails[i].pbslot=slot
            sortstuff.emailfirstletters+=email[0]
            i+=1

        i=0
        sortstuff.urlfirstletters=""
        urlmap.sort(self.sanyosort)
        for (slot, url) in urlmap:
            sortstuff.urls[i].pbslot=slot
            sortstuff.urlfirstletters+=url[0]
            i+=1

        # Now write out the 3 buffers
        self.sendsanyobuffer(sortstuff)

        if self.protocolclass.HASRINGPICBUF:
            self.sendsanyobuffer(ringpic)
        
        self.sendsanyobuffer(callerid)
        
        time.sleep(1.0)

        data['phonebook']=newphonebook
        del data['phonephonebook']
        data['rebootphone'] = 1

    def makecidentry(self, number, slot, nindex):
        "Prepare entry for caller ID lookup buffer"
        
        numstripped=re.sub("[^0-9PT#*]", "", number)
        numonly=re.sub("^(\\d*).*$", "\\1", numstripped)

        cidentry=self.protocolclass.calleridentry()
        cidentry.pbslotandtype=slot+((nindex+1)<<12)
        cidentry.actualnumberlen=len(numonly)
        cidentry.numberfragment=numonly[-10:]

        return cidentry
    

    def savewallpapers(self, results, merge):
        # print "savewallpapers ",results['wallpaper-index']
        return self.savemedia('wallpapers', 'wallpaper-index', 'images', results, merge)
                              
    # Note:  Was able to write 6 ringers to phone.  If there are ringers
    # already on phone, this counts against the 6.  Don't know yet if the limit
    # is a count limit or a byte limit.
    def saveringtones(self, results, merge):
        return self.savemedia('ringtone', 'ringtone-index', 'ringers', results, merge)
    
    def savemedia(self, mediakey, mediaindexkey, mediatype, results, merge):
        """Actually saves out the media

        @param mediakey: key of the media (eg 'wallpapers' or 'ringtones')
                         Index of media in wallpaper or ringer tab
        @param mediaindexkey:  index key (eg 'wallpaper-index')
                         Index of media on the phone
        @param results: results dict
        """

        wp=results[mediakey].copy()
        wpi=results[mediaindexkey].copy()

        # remove builtins
        for k in wpi.keys():
            if wpi[k]['origin']=='builtin':
                del wpi[k]

        # Remove camera pictures
        for w in wp.keys():
            name=wp[w]['name']
            if wp[w].get("origin", "")=='camera':
                self.log("Not transferring camera picture "+name+" to phone")
                del wp[w]
            else:
                for k in wpi.keys():
                    if name==wpi[k]['name']:
                        self.log("Not transferring "+name+" as it is already on the phone")
                        del wp[w]
                        break
        
        init={}
        init[mediatype]={}
        idx=0
        for w in wp.keys():
            idx-=1
            data=wp[w]['data']
            name=wp[w]['name']
            init[mediatype][idx]={'name': name, 'data': data}
        
        index=init[mediatype]

        # write out the content

        ####  index is dict, key is index number, value is dict
        ####  value['name'] = filename
        ####  value['data'] is contents

        errors=False
        for key in index:
            efile=index[key]['name']
            content=index[key]['data']
            if content is None:
                continue # in theory we could rewrite .desc file in case index number has changed
            # dirname=stripext(efile)

            if mediatype=='images':
                content = conversions.convertto8bitpng(content,16383)
            if not self.writesanyofile(efile, content):
                errors=True

        if errors:
            self.log("One or more files were rejected by the phone, due to")
            self.log("invalid file type (only PNG or MIDI are allowed), file")
            self.log("size too big, or too many ringers or wallpaper on the phone")
            self.log("See Sanyo Error Codes section of the Sanyh Phone Notes")
            self.log("in the help for more information")
            
        # Note that we don't write to the camera area

        # tidy up - reread indices
        # del results[mediakey] # done with it
        # reindexfunction(results)
        return results
        

    # Error codes
    # 0x13 Unknown command
    # 0x14 Bad media command
    # 0x6d on sendfileterminator
    # 0x65 not in sync mode on sendfilename
    # 0x6a on sendfilefragment when buffer full, for ringers  6 max?
    # 0x6b ??
    # 0x6c on sendfilefragment when full of pictures         11 max?
    # 0x6d
    # 0x69 on sendfilefragment.  Invalid file type.  PNG works, jpg, bmp don't
    # 0x68 on sendfilefragment.  Bad picture size
    def writesanyofile(self, name, contents):
        start=time.time()
        self.log("Writing file '"+name+"' bytes "+`len(contents)`)
        desc="Writing "+name

        # strip .png and .mid from name because phone will add them
        # back on
        try:
            name=name[:name.index(".mid")]
        except:
            try:
                name=name[:name.index(".png")]
            except:
                pass
        
        # The newer phones can be put in PC Sync mode with these commands
        if hasattr(self.protocolclass,"sanyomediathingyrequest"):
            req=self.protocolclass.sanyomediathingyrequest()
            req.faset = 0x10
            res=self.sendpbcommand(req, self.protocolclass.sanyomediathingyresponse)
            time.sleep(10.0)
            req.faset = 0x13
            res=self.sendpbcommand(req, self.protocolclass.sanyomediathingyresponse)
        
	req=self.protocolclass.sanyosendfilename()
	req.filename=name
        res=self.sendpbcommand(req, self.protocolclass.sanyosendfileresponse, returnerror=True)
        if 'errorcode' in res.getfields():
            if res.errorcode==0x65:
                self.alert("Please put your phone into PC Sync Mode", False)
            else:
                raise SanyoCommandException(res.errorcode)
            # Wait about 5 minutes before giving up
            waitcount=120
            while waitcount>0:
                time.sleep(1.0)
                res=self.sendpbcommand(req, self.protocolclass.sanyosendfileresponse, returnerror=True)
                if not 'errorcode' in res.getfields():
                    break
                waitcount-=1
            if waitcount==0:
                raise SanyoCommandException(res.errorcode)
                
        req=self.protocolclass.sanyosendfilesize()
        req.filesize=len(contents)
        self.sendpbcommand(req, self.protocolclass.sanyosendfileresponse)

        req=self.protocolclass.sanyosendfilefragment()
        packetsize=req.payloadsize

#        time.sleep(1.0)
        offset=0
        count=0
        numblocks=len(contents)/packetsize+1
        for offset in range(0, len(contents), packetsize):
            count+=1
            if count % 5==0:
                self.progress(count,numblocks,desc)
            req.header.command=offset
            req.data=contents[offset:min(offset+packetsize,len(contents))]
            # self.sendpbcommand(req, self.protocolclass.sanyosendfileresponse, numsendretry=2)
            self.sendpbcommand(req, self.protocolclass.sanyosendfileresponse, writemode=True, returnerror=True)
            if 'errorcode' in res.getfields():
                self.log(name+" not written due to error code "+`res.errorcode`)
                return False
                
        req=self.protocolclass.sanyosendfileterminator()
        try:
            res=self.sendpbcommand(req, self.protocolclass.sanyosendfileresponse, writemode=True, returnerror=True)
        # The returned value in res.header.faset may mean something
            if 'errorcode' in res.getfields():
                self.log(name+" not written due to error code "+`res.errorcode`)
                return False
        except:
            self.log("Exception on writing terminator for file "+name)
            self.log("Continuing...")
        
        end=time.time()
        if end-start>3:
            self.log("Wrote "+`len(contents)`+" bytes at "+`int(len(contents)/(end-start))`+" bytes/second")
        return True


    def getcalendar(self,result):
        # Read the event list from the phone.  Proof of principle code.
        # For now, join the event name and location into a single event.
        # description.
        # Todo:
        #   Read Call Alarms (reminder to call someone)
        #   Read call history into calendar.
        #   
        calres={}

        progressmax=self.protocolclass._NUMEVENTSLOTS+self.protocolclass._NUMCALLALARMSLOTS
        req=self.protocolclass.eventrequest()
        count=0

        try:
            reqflag=self.protocolclass.eventslotinuserequest()
        except:
            reqflag=0

        for i in range(0, self.protocolclass._NUMEVENTSLOTS):
            self.progress(i,progressmax,"Events")
            if reqflag:
                reqflag.slot=i
                resflag=self.sendpbcommand(reqflag, self.protocolclass.eventslotinuseresponse)
                if not resflag.flag:
                    continue
            req.slot = i
            res=self.sendpbcommand(req, self.protocolclass.eventresponse)
            if not reqflag:
                if not res.entry.flag:
                    continue
            self.log("Read calendar event "+`i`+" - "+res.entry.eventname+", alarm ID "+`res.entry.ringtone`)
            entry=bpcalendar.CalendarEntry()
            #entry.pos=i
            entry.changeserial=res.entry.serial
            entry.description=res.entry.eventname
            entry.location=res.entry.location
            starttime=res.entry.start
            entry.start=self.decodedate(starttime)
            entry.end=self.decodedate(res.entry.end)
            repeat=self._calrepeatvalues[res.entry.period]
            entry.repeat = self.makerepeat(repeat,entry.start)

            if res.entry.alarm==0xffffffff:
                entry.alarm=res.entry.alarmdiff/60
            else:
                alarmtime=res.entry.alarm
                entry.alarm=(starttime-alarmtime)/60
            ringtone=res.entry.ringtone
            print "ringtone=",ringtone
            if self.calendar_voicenumber and ringtone == self.calendar_voicenumber:
                ringtone=self.phonebook_voicenumber
            if ringtone in self.calendar_tonerange:
                print "Adjusting ringtone by",-self.calendar_toneoffset
                ringtone-=self.calendar_toneoffset
                print "ringtone=",ringtone
            if ringtone!=self.calendar_defaultringtone:
                if result['ringtone-index'].has_key(ringtone):
                    entry.ringtone=result['ringtone-index'][ringtone]['name']

            entry.snoozedelay=0
            calres[entry.id]=entry
            count+=1

        req=self.protocolclass.callalarmrequest()
        for i in range(0, self.protocolclass._NUMCALLALARMSLOTS):
            self.progress(self.protocolclass._NUMEVENTSLOTS,progressmax,"Call Alarms")
            req.slot=i
            res=self.sendpbcommand(req, self.protocolclass.callalarmresponse)
            if res.entry.flag and res.entry.date:
                self.log("Read call alarm entry "+`i`+" - "+res.entry.phonenum+", alarm ID "+`res.entry.ringtone`)
                entry=bpcalendar.CalendarEntry()
                #entry.pos=i+self.protocolclass._NUMEVENTSLOTS # Make unique
                entry.changeserial=res.entry.serial
                entry.description=res.entry.phonenum
                starttime=res.entry.date
                entry.start=self.decodedate(starttime)
                entry.end=entry.start
                repeat=self._calrepeatvalues[res.entry.period]
                entry.repeat = self.makerepeat(repeat,entry.start)
                entry.alarm=0
                if res.entry.ringtone!=self.calendar_defaultcaringtone:
                    entry.ringtone=result['ringtone-index'][res.entry.ringtone]['name']
                entry.snoozedelay=0
                calres[entry.id]=entry
                count+=1

        result['calendar']=calres
        return result

    def makerepeat(self, repeatword, startdate):
        if repeatword is None:
            repeat_entry=None
        else:
            repeat_entry=bpcalendar.RepeatEntry()
            if repeatword=='daily':
                repeat_entry.repeat_type=repeat_entry.daily
                repeat_entry.interval=1
            elif repeatword=='monfri':
                repeat_entry.repeat_type=repeat_entry.daily
                repeat_entry.interval=0
            elif repeatword=='weekly':
                repeat_entry.repeat_type=repeat_entry.weekly
                repeat_entry.interval=1
                dow=datetime.date(*startdate[:3]).isoweekday()%7
                repeat_entry.dow=1<<dow
            elif repeatword=='monthly':
                repeat_entry.repeat_type=repeat_entry.monthly
            else:
                repeat_entry.repeat_type=repeat_entry.yearly

        return repeat_entry
        
    def savecalendar(self, dict, merge):
        # ::TODO:: obey merge param
        # what will be written to the files
        #   Handle Change Serial better.
        #   Advance date on repeating entries to after now so that they
        #     won't all go off when the phone gets turned on.
        #   Sort by date so that that already happened entries don't get
        #     loaded if we don't have room
        #
        cal=dict['calendar']
        newcal={}
        keys=cal.keys()

        # Value to subtract from mktime results since there is no inverse
        # of gmtime
        zonedif=time.mktime(time.gmtime(0))-time.mktime(time.localtime(0))
        save_tonerange = xrange(self.calendar_tonerange[0]-self.calendar_toneoffset,self.calendar_tonerange[-1]-self.calendar_toneoffset+1)

        try:
            reqflag=self.protocolclass.eventslotinuseupdaterequest()
        except:
            reqflag=0

        eventslot=0
        callslot=0
        progressmax=self.protocolclass._NUMEVENTSLOTS+self.protocolclass._NUMCALLALARMSLOTS
        for k in keys:
            entry=cal[k]
            
            descloc=entry.description
            self.progress(eventslot+callslot, progressmax, "Writing "+descloc)

            rp=entry.repeat
            if rp is None:
                repeat=0
            else:
                repeatname=None
                if rp.repeat_type==rp.daily:
                    repeatname='daily'
                elif rp.repeat_type==rp.weekly:
                    repeatname='weekly'
                elif rp.repeat_type==rp.monthly:
                    repeatname='monthly'
                elif rp.repeat_type==rp.yearly:
                    repeatname='yearly'
                for k,v in self._calrepeatvalues.items():
                    if repeatname==v:
                        repeat=k
                        break
                    if repeatname is None:
                        self.log(descloc+": Repeat type "+`entry.repeat`+" not valid for this phone")
                        repeat=0

            phonenum=re.sub("\-","",descloc)
            now=time.mktime(time.localtime(time.time()))-zonedif
            if(phonenum.isdigit()):  # This is a phone number, use call alarm
                self.log("Write calendar call alarm slot "+`callslot`+ " - "+descloc)
                e=self.protocolclass.callalarmentry()
                e.slot=callslot
                e.phonenum=phonenum
                e.phonenum_len=len(e.phonenum)
                

                timearray=list(entry.start)+[0,0,0,0]
                starttimelocal=time.mktime(timearray)-zonedif
                if(starttimelocal<now and repeat==0):
                    e.flag=2 # In the past
                else:
                    e.flag=1 # In the future
                e.date=starttimelocal-self._sanyoepochtounix
                e.datedup=e.date
                e.phonenumbertype=0
                e.phonenumberslot=0
                e.name="" # Could get this by reading phone book
                          # But it would take a lot more time
                e.name_len=len(e.name)
                #e.ringtone=self.calendar_defaultcaringtone
                print "Setting ringtone "+`e.ringtone`

                req=self.protocolclass.callalarmupdaterequest()
                callslot+=1
                respc=self.protocolclass.callalarmresponse
            else: # Normal calender event
                self.log("Write calendar event slot "+`eventslot`+ " - "+descloc)
                e=self.protocolclass.evententry()
                e.slot=eventslot

                e.eventname=descloc
                e.eventname_len=len(e.eventname)
                e.location=entry.location
                e.location_len=len(e.location)

                timearray=list(entry.start)+[0,0,0,0]
                starttimelocal=time.mktime(timearray)-zonedif
                e.start=starttimelocal-self._sanyoepochtounix

                try:
                    timearray=list(entry.end)+[0,0,0,0]
                    endtimelocal=time.mktime(timearray)-zonedif
                    e.end=endtimelocal-self._sanyoepochtounix
                except: # If no valid end date, make end
                    e.end=e.start+60 #  one minute later
                
                alarmdiff=entry.alarm
                if alarmdiff<0:
                    alarmdiff=0
                alarmdiff=max(alarmdiff,0)*60
                e.alarmdiff=alarmdiff
                e.alarm=starttimelocal-self._sanyoepochtounix-alarmdiff

                if reqflag:
                    reqflag.slot=eventslot
                    if(e.alarm+self._sanyoepochtounix<now and repeat==0):
                        reqflag.flag=4 # In the past
                    else:
                        reqflag.flag=1 # In the future
                    res=self.sendpbcommand(reqflag, self.protocolclass.eventslotinuseresponse)
                else:
                    if(starttimelocal<now and repeat==0):
                        e.flag=2 # In the past
                    else:
                        e.flag=1 # In the future

                #timearray=list(entry.get('end', entry['start']))+[0,0,0,0]
                #e.end=time.mktime(timearray)-self._sanyoepochtounix-zonedif
                try:
                    timearray=list(entry.end)+[0,0,0,0]
                    endtimelocal=time.mktime(timearray)-zonedif
                    e.end=endtimelocal-self._sanyoepochtounix
                except: # If no valid end date, make end
                    e.end=e.start+60 #  one minute later 

                ringtoneindex=self._findmediaindex(dict['ringtone-index'],entry.ringtone,'Calendar','ringtone')
                if ringtoneindex==0:
                    e.ringtone=self.calendar_defaultringtone
                else:
                    e.ringtone=ringtoneindex
                    if e.ringtone in save_tonerange:
                        e.ringtone+=self.calendar_toneoffset
                    if self.calendar_voicenumber and e.ringtone==self.phonebook_voicenumber:
                        e.ringtone=self.calendar_voicenumber
                # Use default ringtone for now
                #e.ringtone=self.calendar_defaultringtone
                print "Setting ringtone "+`e.ringtone`

# What we should do is first find largest changeserial, and then increment
# whenever we have one that is undefined or zero.
            
                req=self.protocolclass.eventupdaterequest()
                eventslot+=1
                respc=self.protocolclass.eventresponse

            e.period=repeat
            e.dom=entry.start[2]
            if entry.id>=0 and entry.id<256:
                e.serial=entry.id
            else:
                e.serial=0
            req.entry=e
            res=self.sendpbcommand(req, respc, writemode=True)


            # Blank out unused slots

        if reqflag:
            req=reqflag
            req.flag=0
        else:
            e=self.protocolclass.evententry()
            e.flag=0 # Unused slot
            e.eventname=""
            e.eventname_len=0
            e.location=""
            e.location_len=0
            e.start=0
            e.end=0
            e.period=0
            e.dom=0
            e.ringtone=0
            e.alarm=0
            e.alarmdiff=0
            req=self.protocolclass.eventupdaterequest()
            req.entry=e
            
        for eventslot in range(eventslot,self.protocolclass._NUMEVENTSLOTS):
            self.progress(eventslot+callslot, progressmax, "Writing unused")
            self.log("Write calendar event slot "+`eventslot`+ " - Unused")
            if reqflag:
                req.slot=eventslot
            else:
                req.entry.slot=eventslot
            res=self.sendpbcommand(req, self.protocolclass.eventresponse, writemode=True)

        e=self.protocolclass.callalarmentry()
        e.flag=0 # Unused slot
        e.name=""
        e.name_len=0
        e.phonenum=""
        e.phonenum_len=0
        e.date=0
        e.datedup=0
        e.period=0
        e.dom=0
        e.ringtone=0
        e.phonenumbertype=0
        e.phonenumberslot=0
        req=self.protocolclass.callalarmupdaterequest()
        req.entry=e
        for callslot in range(callslot,self.protocolclass._NUMCALLALARMSLOTS):
            self.progress(eventslot+callslot, progressmax, "Writing unused")
            self.log("Write calendar call alarm slot "+`callslot`+ " - Unused")
            req.entry.slot=callslot
            res=self.sendpbcommand(req, self.protocolclass.callalarmresponse, writemode=True)

        self.progress(progressmax, progressmax, "Calendar write done")

        dict['rebootphone'] = True
        return dict

    def getcallhistory(self, result):
        res={}
        self._readhistory(self.protocolclass.OUTGOING,'Outgoing',res)
        self._readhistory(self.protocolclass.MISSED,'Missed',res)
        self._readhistory(self.protocolclass.INCOMING,'Incoming',res)
        result['call_history']=res
        return result

    def _readhistory(self, type, folder, res):
        req=self.protocolclass.historyrequest()
        req.type=type
        for slot in range(self.protocolclass.NUMCALLHISTORY):
            req.slot=slot
            call=self.sendpbcommand(req, self.protocolclass.historyresponse)
            if call.entry.phonenum=='' and call.entry.name=='':
                continue
            entry=call_history.CallHistoryEntry()
            entry.folder=folder
            entry.name=call.entry.name
            entry.number=call.entry.phonenum
            entry.datetime=((call.entry.date))
            res[entry.id]=entry
    
    def getphoneinfo(self, phone_info):
        self.log('Getting Phone Info')
        try:
            phone_info.append('ESN:', self.get_esn())
            phone_info.append('Manufacturer:', 'Sanyo')
            req=self.protocolclass.lockcoderequest()
            try:
                res=self.sendpbcommand(req, self.protocolclass.lockcoderesponse)
                phone_info.append('Lock Code:', res.lockcode)
            except:
                pass
                
            req=self.protocolclass.sanyofirmwarerequest()
            res=self.sendpbcommand(req, self.protocolclass.sanyofirmwareresponse)
            phone_info.append('Firmware Version:',res.firmware)
            if 'prl' in res.getfields():
                phone_info.append('PRL:', res.prl)
            if 'phonemodel' in res.getfields():
                phone_info.append('Model:', res.phonemodel)
            else:
                phone_info.append('Model:', self.desc)
            req=self.protocolclass.phonenumberrequest()
            res=self.sendpbcommand(req, self.protocolclass.phonenumberresponse)
            phone_info.append('Phone Number:', res.myphonenumber)
           
            req=self.protocolclass.reconditionedrequest()
            res=self.sendpbcommand(req, self.protocolclass.reconditionedresponse)
            if res.reconditioned:
                recon='Yes'
            else:
                recon='No'
            phone_info.append('Reconditioned:',recon)
        except:
            pass

        return

    def decodedate(self,val):
        """Unpack 32 bit value into date/time

        @rtype: tuple
        @return: (year, month, day, hour, minute)
        """
        return list(time.gmtime(val+self._sanyoepochtounix)[:5])

    _calrepeatvalues={
        0: None,
        1: 'daily',
        2: 'weekly',
        3: 'monthly',
        4: 'yearly'
        }


def phonize(str):
    """Convert the phone number into something the phone understands

    All digits, P, T, * and # are kept, everything else is removed"""
    # Note: when looking at phone numbers on the phone, you will see
    # "H" instead of "P".  However, phone saves this internally as "P".
    return re.sub("[^0-9PT#*]", "", str)

class Profile(com_phone.Profile):
    serialsname='sanyo'

    WALLPAPER_WIDTH=120
    WALLPAPER_HEIGHT=128
    OVERSIZE_PERCENTAGE=100
    
    MAX_WALLPAPER_BASENAME_LENGTH=19
    WALLPAPER_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .`~!@#$%^&()-_=+[{]};\'"
    WALLPAPER_CONVERT_FORMAT="png"
    
    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .`~!@#$%^&()-_=+[{]};\'"

    # which usb ids correspond to us
    usbids=( ( 0x0474, 0x0701, 1),  # VID=Sanyo, PID=4900 internal USB interface
        )
    # which device classes we are.
    deviceclasses=("modem",)

    BP_Calendar_Version=3

    def __init__(self):
        self.numbertypetab=numbertypetab
        com_phone.Profile.__init__(self)

    # which sync types we deal with
    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),
        ('ringtone', 'write', 'MERGE'),
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None),
        )
###

    # Processes phone book for writing to Sanyo.  But does not leave phone book
    # in a bitpim compatible format.  Need to understand exactly what bitpim
    # is expecting the method to do.

    def convertphonebooktophone(self, helper, data):
        "Converts the data to what will be used by the phone"
        results={}

        slotsused={}
        for pbentry in data['phonebook']:
            entry=data['phonebook'][pbentry]
            serial1=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial1', -1)
            if(serial1 >= 0 and serial1 < self.protocolclass._NUMPBSLOTS):
                slotsused[serial1]=1

        lastunused=0 # One more than last unused slot
        
        for pbentry in data['phonebook']:
            e={} # entry out
            entry=data['phonebook'][pbentry] # entry in
            try:
                try:
                    e['name']=helper.getfullname(entry.get('names', []),1,1,16)[0]
                except:
                    e['name']=''
                e['name_len']=len(e['name'])

                serial1=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial1', -1)

                if(serial1 >= 0 and serial1 < self.protocolclass._NUMPBSLOTS):
                    e['slot']=serial1
                else:  # A new entry.  Must find unused slot
                    while(slotsused.has_key(lastunused)):
                        lastunused+=1
                        if(lastunused >= self.protocolclass._NUMPBSLOTS):
                            raise helper.ConversionFailed()
                    e['slot']=lastunused
                    slotsused[lastunused]=1
                
                e['slotdup']=e['slot']

                e['email']=helper.makeone(helper.getemails(entry.get('emails', []),0,1,self.protocolclass._MAXEMAILLEN), "")
                e['email_len']=len(e['email'])

                e['url']=helper.makeone(helper.geturls(entry.get('urls', []), 0,1,self.protocolclass._MAXEMAILLEN), "")
                e['url_len']=len(e['url'])
# Could put memo in email or url

                numbers=helper.getnumbers(entry.get('numbers', []),0,7)
                e['numbertypes']=[]
                e['numbers']=[]
                e['speeddials']=[]
                unusednumbers=[] # Hold duplicate types here
                typesused={}
                defaultnum=0
                for num in numbers:
                    typename=num['type']
                    if(typesused.has_key(typename)):
                        unusednumbers.append(num)
                        continue
                    typesused[typename]=1
                    for typenum,tnsearch in enumerate(self.numbertypetab):
                        if typename==tnsearch:
                            if defaultnum==0:
                                defaultnum=typenum+1
                            number=phonize(num['number'])
                            if len(number)>self.protocolclass._MAXNUMBERLEN: # get this number from somewhere sensible
                                # :: TODO:: number is too long and we have to either truncate it or ignore it?
                                number=number[:self.protocolclass._MAXNUMBERLEN]
                            e['numbers'].append(number)
                            if(num.has_key('speeddial')):
                                e['speeddials'].append(num['speeddial'])
                            else:
                                e['speeddials'].append(-1)

                            e['numbertypes'].append(typenum)

                            break

# Now stick the unused numbers in unused types
                trytype=len(self.numbertypetab)
                for num in unusednumbers:
                    while trytype>0:
                        trytype-=1
                        if not typesused.has_key(self.numbertypetab[trytype]):
                            break
                    else:
                        break
                    if defaultnum==0:
                        defaultnum=trytype+1
                    number=phonize(num['number'])
                    if len(number)>self.protocolclass._MAXNUMBERLEN: # get this number from somewhere sensible
                        # :: TODO:: number is too long and we have to either truncate it or ignore it?
                        number=number[:self.protocolclass._MAXNUMBERLEN]
                    e['numbers'].append(number)
                    e['numbertypes'].append(trytype)
                    if(num.has_key('speeddial')):
                        e['speeddials'].append(num['speeddial'])
                    else:
                        e['speeddials'].append(-1)

                if defaultnum==0:
                    if e['url_len'] > 0:
                        defaultnum=8
                    elif e['email_len'] > 0:
                        defaultnum=9

                e['ringtone']=helper.getringtone(entry.get('ringtones', []), 'call', None)
                e['wallpaper']=helper.getwallpaper(entry.get('wallpapers', []), 'call', None)

                e['secret']=helper.getflag(entry.get('flags', []), 'secret', False)
                e['defaultnum']=defaultnum

                results[pbentry]=e
                
            except helper.ConversionFailed:
                #self.log("No Free Slot for "+e['name'])
                print "No Free Slot for "+e['name']
                continue

        data['phonephonebook']=results
        return data


class Phone(SanyoPhonebook,com_phone.Phone,com_brew.BrewProtocol):
    "Talk to a Sanyo Sprint Phone such as SCP-4900, SCP-5300, or SCP-8100"
    desc="Sanyo"
    helpid=helpids.ID_PHONE_SANYOOTHERS
    imagelocations=()
    
    ringtonelocations=()

    builtinimages=()

    builtinringtones=()

    def __init__(self, logtarget, commport):
        "Call all the contructors and sets initial modes"
        com_phone.Phone.__init__(self, logtarget, commport)
        com_brew.BrewProtocol.__init__(self)
        SanyoPhonebook.__init__(self)
        self.log("Attempting to contact phone")
        self.mode=self.MODENONE

    getwallpapers=None
    getringtones=None

