### BITPIM
###
### Copyright (C) 2005 Stephen Wood <saw@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungsphn200.py 2533 2005-09-23 02:49:11Z sawecw $

"""Communicate with a Samsung SPH-N200"""

import sha
import re
import struct

import common
import commport
import time
import p_samsungsphn200
import p_brew
import com_brew
import com_phone
import com_samsung_packet
import prototypes

numbertypetab=('home','office','cell','pager','fax','none')

class Phone(com_samsung_packet.Phone):
    "Talk to a Samsung SPH-N200 phone"

    desc="SPH-N200"

    protocolclass=p_samsungsphn200
    serialsname='sphn200'
    __groups_range=xrange(5)

    imagelocations=()
        # offset, index file, files location, type, maximumentries
    
    __ams_index_file="ams/AmsRegistry"

    def __init__(self, logtarget, commport):
        com_samsung_packet.Phone.__init__(self, logtarget, commport)
        self.numbertypetab=numbertypetab
        self.mode=self.MODENONE

    def getfundamentals(self, results):
        """Gets information fundamental to interopating with the phone and UI."""

        # use a hash of ESN and other stuff (being paranoid)
        self.log("Retrieving fundamental phone information")
        self.log("Phone serial number")
        print "Calling setmode MODEMODEM"
        self.setmode(self.MODEMODEM)
        print "Getting serial number"
        results['uniqueserial']=sha.new(self.get_esn()).hexdigest()

        self.log("Fundamentals retrieved")
        return results

    def _setmodemodem(self):
        self.log("_setmodemodem")
        
        # Just try waking phone up first
        try:
            self.comm.sendatcommand("Z")
            self.comm.sendatcommand('E0V1')
            return True
        except:
            pass

        # Should be in modem mode.  Wake up the interface
        for baud in (0, 19200, 38400, 115200):
            self.log("Baud="+`baud`)
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue

            try:
                self.comm.sendatcommand("Z")
                self.comm.sendatcommand('E0V1')
                return True
            except:
                pass

        return False

    def getphonebook(self, result):
        """Read the phonebook data."""
        pbook={}
        self.setmode(self.MODEPHONEBOOK)

        count=0
        req=self.protocolclass.phonebookslotrequest()
        for slot in range(2,self.protocolclass.NUMPHONEBOOKENTRIES+1):
            req.slot=slot
            res=self.sendpbcommand(req, self.protocolclass.phonebookslotresponse, fixup=self.pblinerepair)
            if len(res) > 0:
                lastname=res[0].entry.name
                self.log(`slot`+": "+lastname)
                entry=self.extractphonebookentry(res[0].entry, result)
                pbook[count]=entry
                count+=1
            self.progress(slot, self.protocolclass.NUMPHONEBOOKENTRIES, lastname)
        result['phonebook']=pbook

        return pbook
        
    def extractphonebookentry(self, entry, fundamentals):
        res={}

        res['serials']=[ {'sourcetype': self.serialsname,
                          'slot': entry.slot,
                          'sourceuniqueid': fundamentals['uniqueserial']} ]
        # only one name
        res['names']=[ {'full': entry.name} ]

        res['numbers']=[]
        secret=0

        for i in range(len(entry.numbers)):
            type = self.numbertypetab[entry.numbers[i].numbertype - 1]
            numhash = {'number': entry.numbers[i].number, 'type': type }
            res['numbers'].append(numhash)
            
        # Field after each number is secret flag.  Setting secret on
        # phone sets secret flag for every defined phone number
        res['flags']=[ {'secret': secret} ]

        return res

    def savephonebook(self, data):
        "Saves out the phonebook"

        self.setmode(self.MODEPHONEBOOK)
        pb=data['phonebook']
        keys=pb.keys()
        keys.sort()

        keys=keys[:self.protocolclass.NUMPHONEBOOKENTRIES+1]

        #
        # Read the existing phonebook so that we cache birthdays
        # Erase all entries, being carefull to modify entries with
        # with URL's first
        #
        uslots={}
        names={}

        req=self.protocolclass.phonebooksloterase()
        self.log('Erasing '+self.desc+' phonebook')
        progressmax=self.protocolclass.NUMPHONEBOOKENTRIES+len(keys)
        for slot in range(2,self.protocolclass.NUMPHONEBOOKENTRIES+1):
            req.slot = slot
            self.progress(slot,progressmax,"Erasing  "+`slot`)
            res=self.sendpbcommand(req, self.protocolclass.phonebookslotupdateresponse)


        for i in range(len(keys)):
            slot=keys[i]
            req=self.protocolclass.phonebookslotupdaterequest()
            req.entry=self.makeentry(pb[slot],data)
            self.log('Writing entry '+`slot`+" - "+req.entry.name)
            self.progress(i+self.protocolclass.NUMPHONEBOOKENTRIES,progressmax,"Writing "+req.entry.name)
            self.sendpbcommand(req, self.protocolclass.phonebookslotupdateresponse)
        self.progress(progressmax+1,progressmax+1, "Phone book write completed")
        return data
        
    def makeentry(self, entry, data):
        e=self.protocolclass.pbentry()

        for k in entry:
            # special treatment for lists
            if k=='numbertypes' or k=='secrets':
                continue
            if k=='ringtone':
            #    e.ringtone=self._findmediaindex(data['ringtone-index'], entry['ringtone'], entry['name'], 'ringtone')
                continue
            elif k=='wallpaper':
            #    e.wallpaper=self._findmediaindex(data['wallpaper-index'], entry['wallpaper'], entry['name'], 'wallpaper')
                continue
            elif k=='numbers':
                #l=getattr(e,k)
                nnum=len(entry[k])
                for i in range(nnum):
                    enpn=self.protocolclass.phonenumber()
                    if i+1 == nnum:
                        enpn.last_number=True
                    enpn.numbertype=entry['numbertypes'][i]+1
                    enpn.number=entry[k][i]
                    e.numbers.append(enpn)
                continue
            # everything else we just set
            setattr(e, k, entry[k])
        return e


    getwallpapers=None
    getringtones=None

class Profile(com_samsung_packet.Profile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SAMSUNG'
    phone_model='SPH-N200'
    deviceclasses=("serial",)

    def __init__(self):
        com_samsung_packet.Profile.__init__(self)
        self.numbertypetab=numbertypetab

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        )

    def convertphonebooktophone(self, helper, data):
        """Converts the data to what will be used by the phone

        @param data: contains the dict returned by getfundamentals
                     as well as where the results go"""

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
        
        uslotsused={}

        tempslot=0 # Temporarily just pick slots and speed dial in order
        for pbentry,slot in existing+newones:

            if len(results)==self.protocolclass.NUMPHONEBOOKENTRIES:
                break

            try:

                e={} # entry out

                entry=data['phonebook'][pbentry]

                secret=helper.getflag(entry.get('flags', []), 'secret', False)
                if secret:
                    secret=1
                else:
                    secret=0
            
                # name
                e['name']=helper.getfullname(entry.get('names', []),1,1,12)[0]

                cat=helper.makeone(helper.getcategory(entry.get('cagetgories',[]),0,1,12), None)

                # phone numbers
                # there must be at least one phone number
                minnumbers=1
                numbers=helper.getnumbers(entry.get('numbers', []),minnumbers,self.protocolclass.NUMPHONENUMBERS)
                e['numbertypes']=[]
                e['numbers']=[]
                e['secrets']=[]
                unusednumbers=[] # Hold duplicate types here
                typesused={}
                defaulttypenum=0
                for num in numbers:
                    typename=num['type']
                    if typesused.has_key(typename):
                        unusednumbers.append(num)
                        continue
                    typesused[typename]=1
                    for typenum,tnsearch in enumerate(self.numbertypetab):
                        if typename==tnsearch:
                            if defaulttypenum==0:
                                defaulttypenum=typenum
                            number=self.phonize(num['number'])
                            if len(number)>self.protocolclass.MAXNUMBERLEN:
                                # :: TODO:: number is too long and we have to either truncate it or ignore it?
                                number=number[:self.protocolclass.MAXNUMBERLEN]
                            e['numbers'].append(number)
                            if(num.has_key('speeddial')):
                                # Only one number per name can be a speed dial
                                # Should make speed dial be the first that
                                # we come accross
                                e['speeddial']=typenum
                                tryuslot = num['speeddial']
                            e['numbertypes'].append(typenum)
                            e['secrets'].append(secret)

                            break

                # Should print to log when a requested speed dial slot is
                # not available
                if e.has_key('speeddial'):
                    if tryuslot>=1 and tryuslot<=self.protocolclass.NUMPHONEBOOKENTRIES and not uslotsused.has_key(tryuslot):
                        uslotsused[tryuslot]=1
                        e['uslot']=tryuslot
                else:
                    e['speeddial']=defaulttypenum

                # find the right slot
                if slot is None or slot<2 or slot>self.protocolclass.NUMPHONEBOOKENTRIES or slot in results:
                    for i in range(2,100000):
                        if i not in results:
                            slot=i
                            break

                e['slot']=slot

                results[slot]=e
            except helper.ConversionFailed:
                continue

        # Fill in uslot for entries that don't have it.
        
        tryuslot=1
        for slot in results.keys():

            e=results[slot]
            if not e.has_key('uslot'):
                while tryuslot<self.protocolclass.NUMPHONEBOOKENTRIES and uslotsused.has_key(tryuslot):
                    tryuslot += 1
                uslotsused[tryuslot]=1
                e['uslot'] = tryuslot
                results[slot] = e

        data['phonebook']=results
        return data

    def phonize(self,str):
        """Convert the phone number into something the phone understands
        All digits, P, T, * and # are kept, everything else is removed"""

        return re.sub("[^0-9PT#*]", "", str)[:self.protocolclass.MAXNUMBERLEN]

