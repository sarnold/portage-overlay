### BITPIM
###
### Copyright (C) 2006 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo6600.py 4531 2007-12-28 04:23:09Z sawecw $

"""Talk to the Sanyo Katana (SCP-6600) cell phone"""
# standard modules
import re
import time
import sha

# my modules
import common
import helpids
import p_brew
import p_sanyo8300
import p_sanyo4930
import p_sanyo6600
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import com_sanyonewer
import com_sanyo3100
import prototypes
import bpcalendar

numbertypetab=( 'cell', 'home', 'office', 'pager',
                    'fax', 'none')

class Phone(com_sanyo3100.Phone):
    "Talk to the Sanyo Katana (SCP-6600) cell phone"

    desc="SCP-6600"
    helpid=helpids.ID_PHONE_SANYOSCP6600

    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=2

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        )
    wallpaperexts=(".jpg", ".png", ".mp4", ".3g2",".JPG")


    protocolclass=p_sanyo6600
    serialsname='scp6600'

    builtinringtones=( 'None', 'Vibrate', '', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8', '', '', '', '', '',
                       '', '', '', '', 
                       'Requiem:Dies Irae', 'Minute Waltz', 'Hungarian Dance',
                       'Military March', 'Ten Little Indians',
                       'Head,Shoulders,Knees&Toes', 'The Moment', 'Asian Jingle',
                       'Kung-fu','','','','','','','','','','','','','','','','','',
                       '','','','','','',
                       'Voice Alarm')


    # f1ff  None    65521
    # FFF2: Vibrate 65522
    #          pb    cal
    # Tone 1:  33    43
    # Requium: 60    60
    # Kung Fu: 68
    # Download: 135
    calendar_defaultringtone=0
    calendar_defaultcaringtone=0
    calendar_toneoffset=33
    calendar_tonerange=xrange(4,100)

    def __init__(self, logtarget, commport):
        com_sanyo3100.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE
        self.numbertypetab=numbertypetab

    def getfundamentals(self, results):
        """Gets information fundamental to interopating with the phone and UI."""
        results['uniqueserial']=sha.new(self.get_esn()).hexdigest()
        self.getmediaindices(results)

        results['groups']=self.read_groups()

        self.log("Fundamentals retrieved")

        return results

    def read_groups(self):
        g={}

        req=self.protocolclass.grouprequest()
        for slot in range(1,self.protocolclass.NUMGROUPS+1):
            req.slot = slot
            res=self.sendpbcommand(req, self.protocolclass.groupresponse)
            if res.entry.groupname_len:
                g[slot]={'name': res.entry.groupname}
        return g

    def savegroups(self, data):
        """Write the groups, sending only those groups that have had
        a name change.  (So that ringers don't get messed up)"""
        groups=data['groups']

        groups_onphone=self.read_groups() # Get groups on phone

        # If groups read doesn't work, don't try to write groups
        if not groups_onphone:
            return

        keys=groups.keys()
        keys.sort()
        print "Bitpim group keys",keys
        print "Onphone group keys",groups_onphone.keys()

        for k in keys:
            if groups[k]['name']!="Unassigned":
                if not groups_onphone.has_key(k) \
                       or groups[k]['name']!=groups_onphone[k]['name']:
                    print "Wrinting ",groups[k]['name']," to ",k
                    req=self.protocolclass.groupupdaterequest()
                    req.slot=k
                    req.entry.slot=k
                    req.entry.groupname=groups[k]['name']
                    req.entry.groupname_len=len(groups[k]['name'])
                    self.sendpbcommand(req, self.protocolclass.groupresponse)
                    groups_onphone[k]=groups[k]
        data['groups']=groups_onphone
        
    def xgetmediaindices(self, results):
        "Just index builtin media for now."

        com_sanyo.SanyoPhonebook.getmediaindices(self, results)
        ringermedia=results['ringtone-index']
        imagemedia=results['wallpaper-index']

        results['ringtone-index']=ringermedia
        results['wallpaper-index']=imagemedia
        return

    def getphonebook(self, result):
        "Code to retrieve packets we have discovered so far so we can work out their formats."
        pbook={}

        sortstuff = self.getsanyobuffer(self.protocolclass.pbsortbuffer)

        speedslot=[]
        for i in range(self.protocolclass._NUMSPEEDDIALS):
            speedslot.append(sortstuff.speeddialindex[i].numslot)

        numentries=sortstuff.slotsused
        self.log("There are %d entries" % (numentries,))

        count = 0 # Number of phonebook entries
        numcount = 0 # Number of phone numbers
        numemail = 0 # Number of emails
        numurl = 0 # Number of urls

        self.log(`sortstuff.groupslotsused`+" Groups")
        self.log(`sortstuff.slotsused`+" Contacts")
        self.log(`sortstuff.nameslotsused`+" Names")
        self.log(`sortstuff.numslotsused`+" Phone numbers")
        self.log(`sortstuff.emailslotsused`+" Email addresses")
        self.log(`sortstuff.urlslotsused`+" URLs")
        self.log(`sortstuff.num_address`+" Addresses")
        self.log(`sortstuff.num_memo`+"  Memos")
        numentries=sortstuff.slotsused

        reqindex=self.protocolclass.contactindexrequest()
        reqname=self.protocolclass.namerequest()
        reqnumber=self.protocolclass.numberrequest()
        reqemail=self.protocolclass.emailrequest()
        requrl=self.protocolclass.urlrequest()
        reqmemo=self.protocolclass.memorequest()
        reqaddress=self.protocolclass.addressrequest()
        for slot in range(self.protocolclass.NUMPHONEBOOKENTRIES):
            if sortstuff.usedflags[slot].used:
                entry={}
                reqindex.slot=slot
                resindex=self.sendpbcommand(reqindex,self.protocolclass.contactindexresponse)
                ringerid = resindex.entry.ringerid
                pictureid = resindex.entry.pictureid
                groupid = resindex.entry.groupid

                if resindex.entry.namep>=0 and resindex.entry.namep<self.protocolclass.NUMPHONEBOOKENTRIES:
                    
                    reqname.slot = resindex.entry.namep
                    resname=self.sendpbcommand(reqname,self.protocolclass.nameresponse)
                    name=resname.entry.name
                    self.log(name)
                else:
                    name=""
                    self.log("No Name")
                print name,ringerid,pictureid

                cat=result['groups'].get(groupid, {'name': "Unassigned"})['name']
                if cat != 'Unassigned':
                    entry['categories']=[ {'category': cat} ]
                entry['serials']=[ {'sourcetype': self.serialsname,

                                    'slot': slot,
                                    'sourceuniqueid': result['uniqueserial']} ]
                entry['names']=[ {'full': name} ]
                if resindex.entry.secret:
                    entry['flags']=[{'secret': True}]
                entry['numbers']=[]
                for numi in range(self.protocolclass.NUMPHONENUMBERS):
                    nump=resindex.entry.numberps[numi].slot
                    if nump < self.protocolclass.MAXNUMBERS:
                        reqnumber.slot=nump
                        resnumber=self.sendpbcommand(reqnumber,self.protocolclass.numberresponse)
                        numhash={'number':resnumber.entry.number, 'type': self.numbertypetab[resnumber.entry.numbertype-1]}
                        for j in range(len(speedslot)):
                            if(speedslot[j]==nump):
                                numhash['speeddial']=j+2
                                break
                        if resindex.entry.defaultnum==numi:
                            entry['numbers'].insert(0,numhash)
                        else:
                            entry['numbers'].append(numhash)

                urlp=resindex.entry.urlp
                if urlp<self.protocolclass.MAXURLS:
                    requrl.slot=urlp
                    resurl=self.sendpbcommand(requrl,self.protocolclass.urlresponse)
                    entry['urls']=[ {'url': resurl.entry.url} ]
                memop=resindex.entry.memop
                if memop<self.protocolclass.MAXMEMOS:
                    reqmemo.slot=memop
                    resmemo=self.sendpbcommand(reqmemo,self.protocolclass.memoresponse)
                    self.log("Memo: "+resmemo.entry.memo)
                    entry['memos']=[ {'memo': resmemo.entry.memo} ]
                addressp=resindex.entry.addressp
                if addressp<self.protocolclass.MAXADDRESSES:
                    reqaddress.slot=addressp
                    resaddress=self.sendpbcommand(reqaddress,self.protocolclass.addressresponse)
                    # Need to parse this address for phonebook.py
                    self.log("Address: "+resaddress.entry.address)
                    entry['addresses']=[ {'street': resaddress.entry.address} ]
                entry['emails']=[]
                for emaili in range(self.protocolclass.NUMEMAILS):
                    emaili=resindex.entry.emailps[emaili].slot
                    if emaili < self.protocolclass.MAXEMAILS:
                        reqemail.slot=emaili
                        resemail=self.sendpbcommand(reqemail,self.protocolclass.emailresponse)
                        self.log("Email: "+resemail.entry.email)
                        entry['emails'].append({'email': resemail.entry.email})
                        
                pbook[count]=entry
                self.progress(count, numentries, name)
                count+=1
                numcount+=len(entry['numbers'])
                if entry.has_key('emails'):
                    numemail+=len(entry['emails'])
                if entry.has_key('urls'):
                    numurl+=len(entry['urls'])
                
                
        self.progress(numentries, numentries, "Phone book read completed")
        self.log("Phone contains "+`count`+" contacts, "+`numcount`+" phone numbers, "+`numemail`+" Emails, "+`numurl`+" URLs")
        result['phonebook']=pbook
        cats=[]
        for i in result['groups']:
            cats.append(result['groups'][i]['name'])
        result['categories']=cats
        return pbook

    def savephonebook(self, data):
        newphonebook={}
        self.setmode(self.MODEBREW)
        self.setmode(self.MODEPHONEBOOK)

        sortstuff=self.protocolclass.pbsortbuffer()

        self.savegroups(data)
        groups=data['groups']

        for i in range(self.protocolclass._NUMSPEEDDIALS):
            sortstuff.speeddialindex.append(0xffff)

        for i in range(self.protocolclass.NUMPHONEBOOKENTRIES):
            sortstuff.usedflags.append(0)
            sortstuff.nameusedflags.append(0)
            sortstuff.sortorder.append(0xffff)
            sortstuff.addressusedflags.append(0)
            sortstuff.memousedflags.append(0)

        for i in range(self.protocolclass.MAXNUMBERS):
            sortstuff.numusedflags.append(0)

        for i in range(self.protocolclass.MAXEMAILS):
            sortstuff.emailusedflags.append(0)

        for i in range(self.protocolclass.MAXURLS):
            sortstuff.urlusedflags.append(0)

        groupslotsused=0
        for i in range(self.protocolclass.NUMGROUPS):
            val=0
            if groups.has_key(i):
                val=1
                groupslotsused+=1
            sortstuff.groupslotusedflags.append(val)

        namep=0
        nump=0
        urlp=0
        memop=0
        addressp=0
        emailp=0
        slotsused=0

        namemap=[]
        contactmap=[]
        urlmap=[]
        
        pbook=data['phonebook'] # Get converted phonebook
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
        
        reqname=self.protocolclass.nameupdaterequest()
        reqnumber=self.protocolclass.numberupdaterequest()
        reqemail=self.protocolclass.emailupdaterequest()
        requrl=self.protocolclass.urlupdaterequest()
        reqmemo=self.protocolclass.memoupdaterequest()
        reqaddress=self.protocolclass.addressupdaterequest()

        for ikey in keys:
            ii=pbook[ikey]
            #slot=ii['slot'] # Just a constant
            slot=slotsused
            slotsused+=1

            reqindex=self.protocolclass.contactindexupdaterequest()
            reqindex.slot=slot
            reqindex.entry.slot=slot

            name=ii['name']
            self.progress(slotsused-1, sortstuff.slotsused, "Writing "+name)
            print "Write "+name+" to "+`slot`
            namemap.append((slot,name))

            reqname.slot=namep
            reqname.entry.contactp=slot
            reqname.entry.name=name
            reqname.entry.name_len=ii['name_len']
            reqname.entry.name_len2=ii['name_len']
            res=self.sendpbcommand(reqname, self.protocolclass.nameresponse)            
            sortstuff.nameusedflags[namep].used=1
            reqindex.entry.namep=namep
            namep+=1

            reqindex.entry.groupid = ii['group']


            # URL
            if ii['url']:
                print urlp,ii['url']
                requrl.slot=urlp
                requrl.entry.contactp=slot
                requrl.entry.url=ii['url']
                requrl.entry.url_len=len(ii['url'])
                res=self.sendpbcommand(requrl, self.protocolclass.urlresponse)
                sortstuff.urlusedflags[urlp].used=1

                reqindex.entry.urlp=urlp
                urlp+=1

            # Memo
            if ii['memo']:
                print memop,ii['memo']
                reqmemo.slot=memop
                reqmemo.entry.contactp=slot
                reqmemo.entry.memo=ii['memo']
                reqmemo.entry.memo_len=len(ii['memo'])
                res=self.sendpbcommand(reqmemo, self.protocolclass.memoresponse)
                sortstuff.memousedflags[memop].used=1
                
                reqindex.entry.memop=memop
                memop+=1

            # Address
            if ii['address']:
                print addressp,ii['address']
                reqaddress.slot=addressp
                reqaddress.entry.contactp=slot
                reqaddress.entry.address=ii['address']
                reqaddress.entry.address_len=len(ii['address'])
                res=self.sendpbcommand(reqaddress, self.protocolclass.addressresponse)
                sortstuff.addressusedflags[addressp].used=1

                reqindex.entry.addressp=addressp
                addressp+=1

            # Email addresses
            for emailindex in range(len(ii['emails'])):
                print emailp,ii['emails'][emailindex]
                reqemail.slot=emailp
                reqemail.entry.contactp=slot
                reqemail.entry.email=ii['emails'][emailindex]
                reqemail.entry.email_len=len(ii['emails'][emailindex])
                res=self.sendpbcommand(reqemail, self.protocolclass.emailresponse)
                sortstuff.emailusedflags[emailp].used=1

                reqindex.entry.emailps.append(emailp)
                emailp+=1

            for numindex in range(len(ii['emails']),self.protocolclass.NUMEMAILS):
                reqindex.entry.emailps.append(0xffff)
                
            for numindex in range(len(ii['numbers'])):
                print nump,ii['numbers'][numindex],ii['numbertypes'][numindex]
                reqnumber.slot=nump
                reqnumber.entry.contactp=slot
                reqnumber.entry.number=ii['numbers'][numindex]
                reqnumber.entry.numberlen=len(ii['numbers'][numindex])
                numbertype=ii['numbertypes'][numindex]
                reqnumber.entry.numbertype=numbertype
                res=self.sendpbcommand(reqnumber, self.protocolclass.numberresponse)
                sortstuff.numusedflags[nump].used=1
                reqindex.entry.numberps.append(nump)
                speeddial=ii['numberspeeds'][numindex]
                if speeddial:
                    sortstuff.speeddialindex[speeddial-2]=nump
                
                nump+=1

            for numindex in range(len(ii['numbers']),self.protocolclass.NUMPHONENUMBERS):
                reqindex.entry.numberps.append(0xffff)
                

            res=self.sendpbcommand(reqindex, self.protocolclass.contactindexresponse)
            print "Setting slot "+`slot`+" to used"
            sortstuff.usedflags[slot].used=1
            
        # Write out the sort buffer
        sortstuff.slotsused=slotsused
        sortstuff.nameslotsused=slotsused
        sortstuff.groupslotsused=groupslotsused
        sortstuff.numslotsused=nump
        sortstuff.emailslotsused=emailp
        sortstuff.num_address=addressp
        sortstuff.num_memo=memop
        sortstuff.pbfirstletters=""
        sortstuff.urlslotsused=urlp
        namemap.sort(self.sanyosort)
        i=0
        for (slot, name) in namemap:
            sortstuff.sortorder[i].pbslot=slot
            if name:
                sortstuff.pbfirstletters+=name[0]
            else:
                sortstuff.pbfirstletters+=chr(0)
            i+=1
        
        self.sendsanyobuffer(sortstuff)
        self.progress(1,1, "Phonebook write completed")
        data['rebootphone']=1

    my_model='SCP6600'
    detected_model='SCP-6600/US'
    my_manufacturer='SANYO'

parentprofile=com_sanyo3100.Profile
class Profile(parentprofile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer=Phone.my_manufacturer
    phone_model=Phone.my_model

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None), # Read sms messages
        ('todo', 'read', None), # Read todos
    )

    def __init__(self):
        parentprofile.__init__(self)
        com_sanyonewer.Profile.__init__(self)
        self.numbertypetab=numbertypetab

    def _getgroup(self, name, groups):
        for key in groups:
            if groups[key]['name']==name:
                return key,groups[key]
        return None,None
        
    def normalisegroups(self, helper, data):
        "Assigns groups based on category data"

        pad=[]
        keys=data['groups'].keys()
        keys.sort()
        for k in keys:
            if k==self.protocolclass.NUMGROUPS: # ignore key 4 which is 'Unassigned'
                name=data['groups'][k]['name']
                pad.append(name)

        groups=helper.getmostpopularcategories(self.protocolclass.NUMGROUPS, data['phonebook'], ["Unassigned"], 16, pad)

        # alpha sort
        groups.sort()

        # newgroups
        newgroups={}

        # Unassigned in 0th group (Need to see what #
        newgroups[0]={'name': 'Unassigned'}

        # populate
        for name in groups:
            # existing entries keep same key
            if name=="Unassigned": continue
            key,value=self._getgroup(name, data['groups'])
            if key is not None:
                newgroups[key]=value
        # new entries get whatever numbers are free
        for name in groups:
            key,value=self._getgroup(name, newgroups)
            if key is None:
                for key in range(1,self.protocolclass.NUMGROUPS+1):
                    if key not in newgroups:
                        newgroups[key]={'name': name, 'icon': 1}
                        break
                       
        # yay, done
        if data['groups']!=newgroups:
            data['groups']=newgroups

    def convertphonebooktophone(self, helper, data):
        "Converts the data to what will be used by the phone"

        self.normalisegroups(helper, data)
        results={}

        
        slotsused={}
        pb=data['phonebook']
        for pbentry in pb:
            entry=pb[pbentry]
            slot=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'slot', -1)
            if(slot >= 0 and slot < self.protocolclass.NUMPHONEBOOKENTRIES):
                slotsused[slot]=1

        lastunused=0 # One more than last unused slot
        
        for pbentry in pb:
            e={} # entry out
            entry=pb[pbentry] # entry in
            try:
                try:
                    e['name']=helper.getfullname(entry.get('names', []),1,1,32)[0]
                except:
                    e['name']=''
                e['name_len']=len(e['name'])
                if len(e['name'])==0:
                    print "Entry with no name"

                cat=helper.makeone(helper.getcategory(entry.get('categories',[]),0,1,16), None)
                if cat is None:
                    e['group']=0
                else:
                    key,value=self._getgroup(cat, data['groups'])
                    if key is not None:
                        e['group']=key
                    else:
                        e['group']=0

                serial1=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'slot', -1)

                if(slot >= 0 and slot < self.protocolclass.NUMPHONEBOOKENTRIES):
                    e['slot']=slot
                else:  # A new entry.  Must find unused slot
                    while(slotsused.has_key(lastunused)):
                        lastunused+=1
                        if(lastunused >= self.protocolclass.NUMPHONEBOOKENTRIES):
                            raise helper.ConversionFailed()
                    e['slot']=lastunused
                    slotsused[lastunused]=1
                
                e['emails']=helper.getemails(entry.get('emails', []),0,self.protocolclass.NUMEMAILS,self.protocolclass.MAXEMAILLEN)

                e['url']=helper.makeone(helper.geturls(entry.get('urls', []), 0,1,self.protocolclass.MAXURLLEN), "")

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
                    sd=num.get("speeddial", 0xFF)
                    if sd>=self.protocolclass.FIRSTSPEEDDIAL and sd<=self.protocolclass.LASTSPEEDDIAL:
                        e['numberspeeds'].append(sd)
                    else:
                        e['numberspeeds'].append(0)
                    
                #e['numberspeeds']=helper.filllist(e['numberspeeds'], self.protocolclass.NUMPHONENUMBERS, 0xFF)
                #e['numbertypes']=helper.filllist(e['numbertypes'], self.protocolclass.NUMPHONENUMBERS, 0)
                #e['numbers']=helper.filllist(e['numbers'], self.protocolclass.NUMPHONENUMBERS, "")
                
                # Need to write a helper
                e['address']=None
                addresses=entry.get('addresses', [])
                if addresses:
                    e['address']=helper.getflag(addresses,'company','')+";"+helper.getflag(addresses,'street','')+";"+helper.getflag(addresses,'street2','')+";"+helper.getflag(addresses,'city','')+";"+helper.getflag(addresses,'state','')+";"+helper.getflag(addresses,'postalcode','')+";"+helper.getflag(addresses,'country','')

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
