### BITPIM
###
### Copyright (C) 2006 Stephen Wood <saw@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungsphn400.py 3918 2007-01-19 05:15:12Z djpham $

"""Communicate with a Samsung SPH-N400"""

# standard modules
import sha

# Bitpim modules
import p_brew
import p_samsungsphn400
import com_brew
import com_phone
import prototypes
import common
import commport
import helpids

class N400CommandException(Exception):
    def __init__(self, errnum, str=None):
        if str is None:
            str="N400 Packet Error 0x%02x" % (errnum,)
        Exception.__init__(self, str)
        self.errnum=errnum

numbertypetab=( 'home', 'office', 'cell', 'pager', 'fax', 'none' )

class Phone(com_phone.Phone,com_brew.BrewProtocol):
    "Talk to a Samsung SPH-N400 cell phone"

    desc="SPH-N400"
    helpid=helpids.ID_PHONE_SAMSUNGOTHERS
    MODEPHONEBOOK="modephonebook"
    
    protocolclass=p_samsungsphn400
    serialsname='sphn400'

    def __init__(self, logtarget, commport):
        com_phone.Phone.__init__(self, logtarget, commport)
        com_brew.BrewProtocol.__init__(self)
        self.mode=self.MODENONE

    def getfundamentals(self, results):
        self.log("Retrieving fundamental phone information")
        self.log("Phone serial number")

        self.setmode(self.MODEPHONEBOOK)

        req=p_brew.ESN_req()
        res=self.sendpbcommand(req, p_brew.ESN_resp)
        results['uniqueserial']=sha.new('%8.8X' % res.esn).hexdigest()

        return results
 
    def _setmodephonebook(self):
        req=self.protocolclass.firmwarerequest()
        respc=self.protocolclass.firmwareresponse

        for baud in 38400, 57600:
            if not self.comm.setbaudrate(baud):
                continue

            # Perhaps overkill.  Will experiment more
            self.comm.setrts(1)
            self.comm.setdtr(1)

            self.comm.setbaudrate(baud)
            self.comm.setrts(0)
            self.comm.setdtr(1)

            self.comm.setbaudrate(baud)
            self.comm.setrts(0)
            self.comm.setdtr(0)

            self.comm.setbaudrate(baud)
            self.comm.setrts(0)
            self.comm.setdtr(0)

            self.comm.setbaudrate(baud)
            self.comm.setrts(0)
            self.comm.setdtr(0)

            try:
                self.sendpbcommand(req, respc, callsetmode=False)
                return True
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

        request.writetobuffer(buffer, logtitle="N400 phonebook request")
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
            self.log("Multiple N400 packets in data - taking last one starting at "+`d+1`)
            self.logdata("Original N400 data", origdata, None)
            rdata=rdata[d+1:]

        # turn it back to normal
        data=common.pppunescape(rdata)

        # Sometimes there is other crap at the beginning.  But it might
        # be a N400 error byte.  So strip off bytes from the beginning
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
            self.logdata("Original N400 data", origdata, None)
            self.logdata("Working on N400 data", data, None)
            raise common.CommsDataCorruption("N400 packet failed CRC check", self.desc)

        res=responseclass()
        if d>0:
            if d==i:
                self.log("Junk at beginning of N400 packet, data at "+`d`)
                self.logdata("Original N400 data", origdata, None)
                self.logdata("Working on N400 data", data, None)
            else:
                if returnerror:
                    res=self.protocolclass.sanyoerror()
                else:
                    self.log("N400 Error code "+`ord(data[0])`)
                    self.logdata("Samsung phonebook response", data, None)
                    raise N400CommandException(ord(data[0]))
            
        data=trydata

        # parse data
        buffer=prototypes.buffer(data)
        res.readfrombuffer(buffer, logtitle="sanyo phonebook response")
        return res

    def getphonebook(self, result):
        pbook={}

        reqname=self.protocolclass.phonebooknamerequest()
        reqnumbers=self.protocolclass.phonebooknumbersrequest()
        count = 0
        for i in range(2, 251):
            reqname.slot=i
            resname=self.sendpbcommand(reqname, self.protocolclass.phonebooknameresponse)
            if resname.entry.nonzeroifused:
                entry={}
                entry['serials']=[ {'sourcetype': self.serialsname,
                          'slot': i,
                          'sourceuniqueid': result['uniqueserial']} ]
                entry['names']=[{'full': resname.entry.name} ]
                entry['numbers'] = []
                for i in range(7):
                    numptr = resname.entry.numbers[i].pnumber
                    if numptr:
                        reqnumbers.slot=numptr
                        resnumbers=self.sendpbcommand(reqnumbers, self.protocolclass.phonebooknumbersresponse)
                        numhash={'number': resnumbers.entry.number, 'type': numbertypetab[i]}
                        if numptr==resname.entry.pspeed:
                            numhash['speeddial']=i
                        entry['numbers'].append(numhash)

                if resname.entry.pemail:
                    reqnumbers.slot=resname.entry.pemail
                    resnumbers=self.sendpbcommand(reqnumbers, self.protocolclass.phonebooknumbersresponse)
                    entry['emails']=[{'email': resnumbers.entry.number}]

                if resname.entry.purl:
                    reqnumbers.slot=resname.entry.purl
                    resnumbers=self.sendpbcommand(reqnumbers, self.protocolclass.phonebooknumbersresponse)
                    entry['urls']=[{'url': resnumbers.entry.number}]
                
                self.log("Read entry "+`i`+": "+resname.entry.name)
                pbook[count]=entry
                count+=1

        result['phonebook']=pbook
        return result

    def getcalendar(self, result):
        pbook={}
        result['calendar']=pbook
        return result

    def getwallpapers(self, results):
        pass
	
    def getringtones(self, results):
        pass


class Profile(com_phone.Profile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer='SAMSUNG'
    phone_model='SPH-N400'
    usbids_usbtoserial=(
        ( 0x067b, 0x2303, None), # VID=Prolific, PID=USB to serial
        ( 0x0403, 0x6001, None), # VID=FTDI, PID=USB to serial
        ( 0x0731, 0x2003, None), # VID=Susteen, PID=Universal USB to serial
        )
    usbids=usbids_usbtoserial
    
    deviceclasses=("serial",)

    def __init__(self):
        com_phone.Profile.__init__(self)
        
    _supportedsyncs=(
        ('phonebook', 'read', None),
        )

