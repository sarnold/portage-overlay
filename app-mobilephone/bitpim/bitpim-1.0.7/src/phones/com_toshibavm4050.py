### BITPIM
###
### Copyright (C) 2005 Simon Capper <scapper@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_toshibavm4050.py 4516 2007-12-21 22:00:57Z djpham $

"""Communicate with the toshiba CDM 8900 cell phone"""

# standard modules
import sha
import re
import time

# our modules
import common
import com_phone
import com_brew
import prototypes
import commport
import p_brew
import p_toshibavm4050
import helpids

class Phone(com_phone.Phone, com_brew.BrewProtocol):
    "Talk to Toshiba VM4050 cell phone"

    desc="Toshiba VM4050"
    helpid=helpids.ID_PHONE_TOSHIBAVM4050
    protocolclass=p_toshibavm4050
    serialsname='toshibavm4050'
    
    builtinimages=()

    builtinringtones=( 'Common', 'Ring 1', 'Ring 2', 'Ring 3', 'Ring 4', 'Ring 5',
                       'Ring 6', 'Ring 7', 'Ring 8', 'Ring 9',
                       'Alarm 1', 'Alarm 2', 'Alarm 3', 'Alarm 4', 'Alarm 5',
                       'Alarm 6', 'Alarm 7', 'Alarm 8', 'Alarm 9',
                       'Stars & Stripes', 'When the Saints', 'Bach', 
                       'William Tell', 'Nachtmusik', 'Str Serenade', 'Toccata',
                       'Meistersinger', 'Blue Danube')

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
        self.log("Getting fundamentals")
        # use a hash of ESN and other stuff (being paranoid)
        self.log("Retrieving fundamental phone information")
        self.setmode(self.MODEBREW)
        self.log("Phone serial number")
        results['uniqueserial']=sha.new(self.get_esn()).hexdigest()
        # This phone does not support groups
        results['groups']={}
        #self.getwallpaperindices(results)
        self.getringtoneindices(results)
        self.log("Fundamentals retrieved")
        return results

    def getmediaindex(self, builtins, results, key):
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
            c+=1

        results[key]=media
        return media

    def getwallpaperindices(self, results):
        return self.getmediaindex(self.builtinimages, results, 'wallpaper-index')

    def getringtoneindices(self, results):
        return self.getmediaindex(self.builtinringtones, results, 'ringtone-index')

    def listsubdirs(self, dir='', recurse=0):
        self.log("Getting file system in dir '"+dir+"'")
        res=com_brew.BrewProtocol.listsubdirs(self, dir, recurse)
        # toshiba is bad, they don't list these directories when you query the phone
        # so we add them in ourselves
        if not len(dir):
            res['C']={ 'name': 'C', 'type': 'directory' }
            res['D']={ 'name': 'D', 'type': 'directory' }
            res['G']={ 'name': 'G', 'type': 'directory' }
        return res

    def enable_data_transfer(self):
        req=self.protocolclass.setphoneattribrequest()
        res=self.sendpbcommand(req, self.protocolclass.setphoneattribresponse)
        req=self.protocolclass.tosh_enableswapdatarequest()
        res=self.sendpbcommand(req, self.protocolclass.tosh_enableswapdataresponse)

    def disable_data_transfer(self):
        req=self.protocolclass.tosh_disableswapdatarequest()
        res=self.sendpbcommand(req, self.protocolclass.tosh_disableswapdataresponse)

    def readdatarecord(self):
        return self.getfilecontents("D/APL/SWAP/DIAG_APSWP_MEMORY")

    def writedatarecord(self, record):
        return self.writefile("D/APL/SWAP/DIAG_APSWP_MEMORY", record)

    def get_esn(self, data=None):
        # return the ESN of this phone
        return self.get_brew_esn()

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
        self.enable_data_transfer()
        # no way to read the number of entries, just have to read all
        count=0
       # try:
        for i in range(self.protocolclass.NUMSLOTS):
            entry=self.protocolclass.pbentry()
            self.progress(i, self.protocolclass.NUMSLOTS, "")
            req=self.protocolclass.tosh_getpbentryrequest()
            req.entry_index=i
            res=self.sendpbcommand(req, self.protocolclass.tosh_getpbentryresponse)
            if not res.swap_ok:
                raw=self.readdatarecord()
                if __debug__:
                    open("c:/projects/temp/record_in"+`i`, "wb").write(raw)
                buf=prototypes.buffer(raw)
                entry.readfrombuffer(buf, logtitle="phonebook data record")
            else:
                continue
            self.log("Read entry "+`i`+" - "+entry.name)
            pb_entry=self.extractphonebookentry(entry, result)
            pbook[i]=pb_entry
        #except Exception, e:
            # must disable this to prevent phone problems
        #    self.disable_data_transfer()
        #    raise Exception, e 
        self.disable_data_transfer()
        self.progress(self.protocolclass.NUMSLOTS, self.protocolclass.NUMSLOTS, "Phone book read completed")
        result['phonebook']=pbook
        return result

    _type_map={
        0: 'phone', 
        1: 'home',
        2: 'office',
        3: 'cell',
        4: 'pager',
        5: 'fax',
        }        

    _ringer_pattern1_map={
        0x0100: 'Ring 1',
        0x0101: 'Ring 2',
        0x0102: 'Ring 3',
        0x0103: 'Ring 4',
        0x0104: 'Ring 5',
        0x0105: 'Ring 6',
        0x0106: 'Ring 7',
        0x0107: 'Ring 8',
        0x0108: 'Ring 9',
        }

    _ringer_pattern2_map={
        0x0009: 'Alarm 1',
        0x000A: 'Alarm 2',
        0x000B: 'Alarm 3',
        0x000C: 'Alarm 4',
        0x000D: 'Alarm 5',
        0x000E: 'Alarm 6',
        0x000F: 'Alarm 7',
        0x0010: 'Alarm 8',
        0x0011: 'Alarm 9',
        }

    _ringer_melody_map={
        0x0000: 'Stars & Stripes',
        0x0001: 'When the Saints',
        0x0002: 'Bach',
        0x0003: 'William Tell',
        0x0004: 'Nachtmusik',
        0x0005: 'Str Serenade',
        0x0006: 'Toccata',
        0x0007: 'Meistersinger',
        0x0008: 'Blue Danube',
        }

    def _get_ringtone(self, ringer_group, ringer_index):
        # no idea what values downloaded ringtones use
        # exception handler will take care of any wierd
        # value we do not understand
        try:
            if ringer_group==1:
                return self._ringer_pattern1_map[ringer_index]
            if ringer_group==2:
                return self._ringer_pattern2_map[ringer_index]
            if ringer_group==3:
                return self._ringer_melody_map[ringer_index]
        except:
            pass
        return 'Common'

    def __find_index(self, map, ringer):
        for k, v in map.iteritems():
            if v==ringer:
                return k
        return -1

    def _getringtone_group_index(self, ringtone):
        ringer_index = self.__find_index(self._ringer_pattern1_map,ringtone)
        if ringer_index != -1:
            return 1, ringer_index
        ringer_index = self.__find_index(self._ringer_pattern2_map,ringtone)
        if ringer_index != -1:
            return 2, ringer_index
        ringer_index = self.__find_index(self._ringer_melody_map,ringtone)
        if ringer_index != -1:
            return 3, ringer_index
        return 5, 0

    def extractphonebookentry(self, entry, result):
        """Return a phonebook entry in BitPim format.  This is called from getphonebook."""
        res={}
        # serials
        res['serials']=[ {'sourcetype': self.serialsname, 'serial1': entry.slot,
                          'sourceuniqueid': result['uniqueserial']} ]
        # numbers
        set=False
        secret=False
        ringtone='Common'
        numbers=[]
        for i in range(self.protocolclass.MAXPHONENUMBERS):
            if entry.numbers[i].valid and len(entry.numbers[i].number):
                type=self._type_map[entry.numbers[i].type]
                numbers.append( {'number': entry.numbers[i].number, 'type': type} )
                # secret and ringtone are per number on this phone, bitpim only supports one
                # per phonebook entry, so we set the phone entry to secret if any number is secret
                # and we pick the first ringtone that is not the default and apply to the whole entry
                if not secret and entry.numbers[i].secret:
                    secret=True
                if ringtone=='Common' and entry.numbers[i].ringer_group!=5:
                    ringtone=self._get_ringtone(entry.numbers[i].ringer_group, entry.numbers[i].ringer_index)
        if len(numbers):
            res['numbers']=numbers
        if secret:
            res['flags']=[{'secret': True}]
        res['ringtones']=[{'ringtone': ringtone, 'use': 'call'}]
        # name
        if len(entry.name): # yes, the toshiba can have a blank name!
            res['names']=[{'full': entry.name}]
        # emails (we treat wireless as email addr)
        emails=[]
        for i in range(self.protocolclass.MAXEMAILS):
            if entry.emails[i].valid and len(entry.emails[i].email):
                emails.append( {'email': entry.emails[i].email} )
        if len(emails):
            res['emails']=emails
        # urls
        if len(entry.web_page):
            res['urls']=[ {'url': entry.web_page} ]
        return res

    def makephonebookentry(self, fields):
        e=self.protocolclass.pbentry()
        # some defaults
        secret=False
        if fields['secret']!=None:
            secret=fields['secret']
        ringtone='Common'
        if fields['ringtone']!=None:
            ringtone=fields['ringtone']
        ringer_group, ringer_index=self._getringtone_group_index(ringtone)
        if fields['name']:
            e.name=fields['name']
        else:
            e.name=''
        for i in range(len(fields['numbers'])):
            n=self.protocolclass.pbnumber()
            n.valid=1
            n.number=fields['numbers'][i]
            n.type=fields['numbertypes'][i]
            n.secret=secret
            n.ringer_group=ringer_group
            n.ringer_index=ringer_index
            e.numbers.append(n)
        for i in range(len(fields['emails'])):
            n=self.protocolclass.pbemail()
            n.valid=1
            n.email=fields['emails'][i]
            e.emails.append(n)
        if fields['web_page']:
            e.web_page=fields['web_page']
        e.slot=fields['slot']
        return e

    def savephonebook(self, data):
        # brute force, it is faster, otherwise we would have to 
        # examine each entry to see if it was there and then decide what
        # to do with it, deleting and re-writing is faster and what the user
        # seleted with "OVERWRITE"
        self.log("New phonebook\n"+common.prettyprintdict(data['phonebook']))
        pb=data['phonebook']
        keys=pb.keys()
        keys.sort()
        keys=keys[:self.protocolclass.NUMSLOTS]
        self.enable_data_transfer()
        try:
            # delete the old phonebook
            self.rmfile("D/APL/SWAP/DIAG_APSWP_MEMORY")
            for i in range(self.protocolclass.NUMSLOTS):
                self.deletepbentry(i)
            # create the new phonebook
            for i in range(len(keys)):
                slot=keys[i]
                entry=self.makephonebookentry(pb[slot])
                self.progress(i, len(keys), "Writing "+entry.name)
                self.log('Writing entry '+`slot`+" - "+entry.name)
                self.sendpbentrytophone(entry)
        except Exception, e:
            # must disable this to prevent phone problems
            self.disable_data_transfer()
            raise Exception, e 
        self.disable_data_transfer()
        self.progress(len(keys)+1, len(keys)+1, "Phone book write completed")
        return data
       
    def sendpbentrytophone(self, entry):
        # write out the new one
        buf=prototypes.buffer()
        entry.writetobuffer(buf, logtitle="Sending pbentrytophone")
        data=buf.getvalue()
        self.writedatarecord(data)
        req=self.protocolclass.tosh_setpbentryrequest()
        req.entry_index=entry.slot
        if __debug__:
            open("c:/projects/temp/record_out"+`entry.slot`, "wb").write(data)
        res=self.sendpbcommand(req, self.protocolclass.tosh_setpbentryresponse)
        if res.swap_ok:
            self.log("Error writing phonebook entry")
        
    def deletepbentry(self, slot):
        req=self.protocolclass.tosh_modifypbentryrequest()
        req.entry_index=slot
        res=self.sendpbcommand(req, self.protocolclass.tosh_modifypbentryresponse)
    
    def sendpbcommand(self, request, responseclass):
        self.setmode(self.MODEBREW)
        buffer=prototypes.buffer()
        request.writetobuffer(buffer, logtitle="toshiba vm4050 phonebook request")
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
            raise common.CommsDataCorruption("toshiba phonebook packet failed CRC check", self.desc)
        
        # parse data
        buffer=prototypes.buffer(data)
        res=responseclass()
        res.readfrombuffer(buffer, logtitle="toshiba phonebook response")
        return res

    def get_detect_data(self, res):
        try:
            self.modemmoderequest()
            res['manufacturer']=self.comm.sendatcommand('+GMI')[0]
            res['model']=self.comm.sendatcommand('+GMM')[0]
            res['firmware_version']=self.comm.sendatcommand('+GMR')[0]
            res['esn']=self.comm.sendatcommand('+GSN')[0][2:] # strip off the 0x
        except commport.CommTimeout:
            pass

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
                if res[port]['model']:
                    # is a model has already
                    # been found, not much we can do now
                    continue
                p=_module.Phone(_log, commport.CommConnection(_log, port, timeout=1))
                # because this is a modem port we ignore any existing results for likely ports
                res[port]['mode_brew']=p._setmodebrew()
                if res[port]['mode_brew']:
                    p.get_detect_data(res[port])
                p.comm.close()
            except:
                if __debug__:
                    raise
    
class Profile(com_phone.Profile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname

    # use for auto-detection
    phone_manufacturer='Audiovox Communications Corporation'
    phone_model='VM4050'

    # which usb ids correspond to us
    usbids=((0x05C6, 0x3100, 1), # toshiba modem port direct cable connection
        )
    # which device classes we are.
    deviceclasses=("modem",)

    # what types of syncing we support
    _supportedsyncs=(
        ('phonebook', 'read', None),         # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'), # phonebook overwrite only
        )

    def convertphonebooktophone(self, helper, data):
        """Converts the data to what will be used by the phone

        @param data: contains the dict returned by getfundamentals
                 as well as where the results go"""
        results={}
        slotsused={}
        # generate a list of used slots
        for pbentry in data['phonebook']:
            entry=data['phonebook'][pbentry]
            serial1=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial1', -1)
            if(serial1 >= 0 and serial1 < self.protocolclass.NUMSLOTS):
                slotsused[serial1]=1

        lastunused=0 # One more than last unused slot

        for pbentry in data['phonebook']:
            if len(results)==self.protocolclass.NUMSLOTS:
                break
            e={} # entry out
            entry=data['phonebook'][pbentry] # entry in
            try:
                # name
                e['name']=helper.getfullname(entry.get('names', []),1,1,36)[0]

                serial1=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial1', -1)

                if(serial1 >= 0 and serial1 < self.protocolclass.NUMSLOTS):
                    e['slot']=serial1
                else:  # A new entry.  Must find unused slot
                    while(slotsused.has_key(lastunused)):
                        lastunused+=1
                        if(lastunused >= self.protocolclass.NUMSLOTS):
                            helper.add_error_message("Name: %s. Unable to add, phonebook full" % e['name'])
                            raise helper.ConversionFailed()
                    e['slot']=lastunused
                    slotsused[lastunused]=1

                # email addresses
                emails=helper.getemails(entry.get('emails', []) ,0,self.protocolclass.MAXEMAILS,self.protocolclass.MAXEMAILLEN)
                e['emails']=helper.filllist(emails, self.protocolclass.MAXEMAILS, "")

                # url
                e['web_page']=helper.makeone(helper.geturls(entry.get('urls', []), 0,1,48), "")

                # phone numbers
                numbers=helper.getnumbers(entry.get('numbers', []),0,self.protocolclass.MAXPHONENUMBERS)
                e['numbertypes']=[]
                e['numbers']=[]
                typesused={}
                for num in numbers:
                    type=num['type']
                    if(typesused.has_key(type)):
                        continue
                    typesused[type]=1
                    for typenum,tnsearch in enumerate(self.protocolclass.numbertypetab):
                        if type==tnsearch:
                            number=self.phonize(num['number'])
                            if len(number)==0:
                                # no actual digits in the number
                                continue
                            if len(number)>self.protocolclass.MAXPHONENUMBERLEN: # get this number from somewhere sensible
                                # :: TODO:: number is too long and we have to either truncate it or ignore it?
                                number=number[:self.protocolclass.MAXPHONENUMBERLEN]
                            e['numbers'].append(number)
                            e['numbertypes'].append(typenum)
                            break

                # ringtones
                e['ringtone']=helper.getringtone(entry.get('ringtones', []), 'call', None)

                # flags
                e['secret']=helper.getflag(entry.get('flags',[]), 'secret', False)

                results[pbentry]=e
                
            except helper.ConversionFailed:
                continue
        data['phonebook']=results
        return data
    

    def phonize(self, str):
        """Convert the phone number into something the phone understands

        All digits, P, T, *, #  are kept, everything else is removed.
        In theory the phone can store a dash in the phonebook, but that
        is not normal."""
        return re.sub("[^0-9PT#*]", "", str)[:self.protocolclass.MAXPHONENUMBERLEN]
