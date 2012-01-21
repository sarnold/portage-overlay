### BITPIM
###
### Copyright (C) 2003 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2003 Scott Craig <scott.craig@shaw.ca>
### Copyright (C) 2003 Alan Gonzalez <agonzalez@yahoo.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgtm520.py 4543 2008-01-04 23:44:24Z djpham $

"Talk to the LG TM520/VX10 cell phone"

# standard modules
import re
import time
import cStringIO
import sha

# my modules
import common
import p_lgtm520
import com_brew
import com_phone
import com_lg
import prototypes

typemap = {
	    'fwd': ( 'home', 'office', 'cell', 'pager', 'data' ),
	    'rev': { 'home': 0, 'office': 1, 'cell': 2, 'pager': 3, 'data': 4, 'fax': 4 }
	  }

class Phone(com_phone.Phone,com_brew.BrewProtocol,com_lg.LGPhonebook):
    "Talk to the LG TM520/VX10 cell phone"
    desc="LG-TM520/VX10"
    protocolclass=p_lgtm520
    serialsname='lgtm520'

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries
        # There really isn't an index file
        ( 0, "", "ringer", "ringers", 5),
	# phonebook linkage
        #( 0, "pim/midiringer.dat", "ringer", "ringers", 199),
	# main ringer
        #( 0, "pim/ringtitle.dat", "ringer", "ringers", 1),
        )

    builtinringtones=( 'Standard1', 'Standard2', 'Standard3', 'Standard4',
                       'Standard5', 'Radetzky March', 'Nocturn', 'Carmen',
                       'La Traviata', 'Liberty Bell', 'Semper Fidelis',
                       'Take Me Out', 'Turkey In The Straw', 'We Wish...',
                       'Csikos Post', 'Bumble Bee Twist', 'Badinerie',
                       'Silken Ladder', 'Chestnut' )

    # phone uses Jan 1, 1980 as epoch.  Python uses Jan 1, 1970.  This is difference
    # plus a fudge factor of 5 days, 20 hours for no reason I can find
    _tm520epochtounix=315532800+460800
    _brewepochtounix=315532800+460800  # trying to override inherited entry
    _calrepeatvalues={ 0: None, 1: None, 2: 'daily' }

    getwallpapers=None
    
    def __init__(self, logtarget, commport):
        com_phone.Phone.__init__(self, logtarget, commport)
	com_brew.BrewProtocol.__init__(self)
        com_lg.LGPhonebook.__init__(self)
        self.log("Attempting to contact phone")
        self.mode=self.MODENONE

    def getfundamentals(self, results):
        """Gets information fundamental to interopating with the phone and UI."""

        # use a hash of ESN and other stuff (being paranoid)
        self.log("Retrieving fundamental phone information")
        self.log("Phone serial number")
        results['uniqueserial']=sha.new(self.getfilecontents("nvm/$SYS.ESN")).hexdigest()
	results['ringtone-index'] = {}
	ringcount = 1
	for r in self.builtinringtones:
	    results['ringtone-index'][ringcount] = {'name': r, 'origin': 'builtin'}
	    ringcount += 1

	try:
	    ringers=self.getfilesystem('ringer')
	    for r in ringers.keys():
		results['ringtone-index'][ringcount] = {'name': r[len('ringer/'):], 'origin': 'ringers'}
		ringcount +=1
	except com_brew.BrewNoSuchDirectoryException:
	    self.log("Ringer directory doesn't exist, firmware might not be download capable")
        self.log("Fundamentals retrieved")
        return results

    def pbinit(self):
	self.mode = self.MODEPHONEBOOK
        self.sendpbcommand(self.protocolclass.pbstartsyncrequest(), self.protocolclass.pbstartsyncresponse)
        
	self.mode = self.MODEBREW
        res=self.sendpbcommand(self.protocolclass.pbinforequest(), self.protocolclass.pbinforesponse)

	return res.numentries

    def pbend(self):
	req=self.protocolclass.pbendsyncrequest()
	self.sendpbcommand(req, self.protocolclass.pbendsyncresponse)

    def pregetpb(self, result):
        index={}
        try:
            buf=prototypes.buffer(self.getfilecontents("pim/midiringer.dat"))
        except com_brew.BrewNoSuchFileException:
            # file may not exist
            result['intermediate'] = index
	    return
        g=self.protocolclass.ringindex()
        g.readfrombuffer(buf, logtitle="ringer index")
        for i in g.items:
            if i.name != "default":
                index[i.index+1]=i.name[len('ringer/'):]
        result['intermediate'] = index

    def postgetdb(self, result):
        #cats=[]
        #for i in result['groups']:
        #    if result['groups'][i]['name']!='No Group':
	#	cats.append(result['groups'][i]['name'])
        #result['categories'] = cats
	del result['intermediate']

    def getphonebook(self,result):
        """Reads the phonebook data.  The L{getfundamentals} information will
        already be in result."""
        pbook={}
        # Bug in the phone.  if you repeatedly read the phone book it starts
        # returning a random number as the number of entries.  We get around
        # this by switching into brew mode which clears that.
        #self.mode=self.MODENONE
        #self.setmode(self.MODEBREW)

	self.pregetpb(result)
        self.log("Reading number of phonebook entries")

        numentries=self.pbinit()
        self.log("There are %d entries" % (numentries,))
        for i in range(0, numentries):
            ### Read current entry
            req=self.protocolclass.pbreadentryrequest()
            res=self.sendpbcommand(req, self.protocolclass.pbreadentryresponse)
            self.log("Read entry "+`i`+" - "+res.entry.name)
            entry=self.extractphonebookentry(res.entry, result)
            pbook[i]=entry 
            self.progress(i, numentries, res.entry.name)
            #### Advance to next entry
            req=self.protocolclass.pbnextentryrequest()
            self.sendpbcommand(req, self.protocolclass.pbnextentryresponse)

        self.progress(numentries, numentries, "Phone book read completed")
        result['phonebook']=pbook
	self.pbend()
	self.postgetdb(result)

        print "returning keys",result.keys()
        return pbook

    def extractphonebookentry(self, entry, fundamentals):
        """Return a phonebook entry in BitPim format"""
        res={}
        # serials
        res['serials']=[ {'sourcetype': self.serialsname, 'serial1': entry.serial1, 'serial2': entry.serial2,
                          'sourceuniqueid': fundamentals['uniqueserial']} ]
        # only one name
        res['names']=[ {'full': entry.name} ]
        # only one email
	if len(entry.email) > 0: res['emails']=[ {'email': entry.email} ]
	res['flags'] = []
	# we only supply secret/voicetag if it is true
        if entry.secret: res['flags'].append({'secret': entry.secret })
	if entry.voicetag: res['flags'].append({'voicetag': entry.voicetag })

        # ringtones
        res['ringtones'] = []
        if entry.ringtone > 0:
            # individual ringtone
            if entry.ringtone > len(self.builtinringtones):
                # custom individual ringtone
		try:
                    res['ringtones'].append({'ringtone': fundamentals['intermediate'][entry.entrynumber], 'use': 'call'})
		except:
		    self.log('Custom ringtone not properly assigned for '+entry.name)
            else:
                # stock individual ringtone
                res['ringtones'].append({'ringtone': fundamentals['ringtone-index'][entry.ringtone]['name'], 'use': 'call'})
        # 5 phone numbers
        res['numbers']=[]
        numbernumber=0
        for type in typemap['fwd']:
	    item = entry.numbers[numbernumber]
	    if len(item.number) > 0:
		res['numbers'].append({'number': item.number, 'type': type, 'sum': item.chksum })
		if numbernumber == entry.default: res['numbers'][-1]['speeddial'] = entry.entrynumber
            numbernumber+=1
        return res

    def savegroups(self, data): pass

    def savephonebook(self, data):
        self.savegroups(data)
        # To write the phone book, we scan through all existing entries
        # and record their record number and serials.
        # We then delete any entries that aren't in data
        # We then write out our records, usng overwrite or append
        # commands as necessary
        serialupdates=[]
        existingpbook={} # keep track of the phonebook that is on the phone
	ringindex = {}

	# Ringtones
	pbook = data['phonebook']
	for i in pbook.keys():
	    if not 'ringtone' in pbook[i]: continue
	    if not pbook[i]['ringtone'] is None and not pbook[i]['ringtone'] in self.builtinringtones:
		ringindex[pbook[i]['entrynumber']] = pbook[i]['ringtone'];

	ringidxfile=self.protocolclass.ringindex()
	for i in range(1, 200):
	    ringerentry = self.protocolclass.ringentry()
	    ringerentry.index = i
	    ringerentry.name = ''
	    if i in ringindex: ringerentry.name = 'ringer/'+ringindex[i]
	    ringidxfile.items.append(ringerentry)
	buf=prototypes.buffer()
	ringidxfile.writetobuffer(buf, logtitle="Custom ringer index")

        # ::TODO:: this code looks wrong.  Why isn't the if before the loop above?
        # and if the user deleted all ringers then shouldn't the file be truncated
        # rather than ignored?
	if len(ringindex) > 0:
	    self.writefile("pim/midiringer.dat", buf.getvalue())

        #self.mode=self.MODENONE
        #self.setmode(self.MODEBREW) # see note in getphonebook() for why this is necessary
        #self.setmode(self.MODEPHONEBOOK)
        # similar loop to reading
        numexistingentries=self.pbinit()
        progressmax=numexistingentries+len(data['phonebook'].keys())
        progresscur=0
        self.log("There are %d existing entries" % (numexistingentries,))
        for i in range(0, numexistingentries):
            ### Read current entry
            req=self.protocolclass.pbreadentryrequest()
            res=self.sendpbcommand(req, self.protocolclass.pbreadentryresponse)
            
            entry={ 'number':  res.entry.entrynumber, 'serial1':  res.entry.serial1,
                    'serial2': res.entry.serial2, 'name': res.entry.name}
            assert entry['serial1']==entry['serial2'] # always the same
            self.log("Reading entry "+`i`+" - "+entry['name'])            
            existingpbook[i]=entry 
            self.progress(progresscur, progressmax, "existing "+entry['name'])
            #### Advance to next entry
            req=self.protocolclass.pbnextentryrequest()
            self.sendpbcommand(req, self.protocolclass.pbnextentryresponse)
            progresscur+=1
        # we have now looped around back to begining

        # Find entries that have been deleted
        pbook=data['phonebook']
        dellist=[]
        for i in range(0, numexistingentries):
            ii=existingpbook[i]
            serial=ii['serial1']
            item=self._findserial(serial, pbook)
            if item is None:
                dellist.append(i)

        progressmax+=len(dellist) # more work to do

        # Delete those entries
        for i in dellist:
            progresscur+=1
            numexistingentries-=1  # keep count right
            ii=existingpbook[i]
            self.log("Deleting entry "+`i`+" - "+ii['name'])
            req=self.protocolclass.pbdeleteentryrequest()
            req.serial1=ii['serial1']
            req.serial2=ii['serial2']
            req.entrynumber=ii['number']
            self.sendpbcommand(req, self.protocolclass.pbdeleteentryresponse)
            self.progress(progresscur, progressmax, "Deleting "+ii['name'])
            # also remove them from existingpbook
            del existingpbook[i]

        # counter to keep track of record number (otherwise appends don't work)
        counter=0
        # Now rewrite out existing entries
        keys=existingpbook.keys()
        existingserials=[]
        keys.sort()  # do in same order as existingpbook
        for i in keys:
            progresscur+=1
            ii=pbook[self._findserial(existingpbook[i]['serial1'], pbook)]
            self.log("Rewriting entry "+`i`+" - "+ii['name'])
            self.progress(progresscur, progressmax, "Rewriting "+ii['name'])
            entry=self.makeentry(counter, ii, data)
            counter+=1
            existingserials.append(existingpbook[i]['serial1'])
            req=self.protocolclass.pbupdateentryrequest()
            req.entry=entry
            res=self.sendpbcommand(req, self.protocolclass.pbupdateentryresponse)
            serialupdates.append( ( ii["bitpimserial"],
                                    {'sourcetype': self.serialsname, 'serial1': res.serial1, 'serial2': res.serial1,
                                     'sourceuniqueid': data['uniqueserial']})
                                  )
            assert ii['serial1']==res.serial1 # serial should stay the same

        # Finally write out new entries
        keys=pbook.keys()
        keys.sort()
        for i in keys:
            ii=pbook[i]
            if ii['serial1'] in existingserials:
                continue # already wrote this one out
            progresscur+=1
            entry=self.makeentry(counter, ii, data)
            counter+=1
            self.log("Appending entry "+ii['name'])
            self.progress(progresscur, progressmax, "Writing "+ii['name'])
            req=self.protocolclass.pbappendentryrequest()
            req.entry=entry
            res=self.sendpbcommand(req, self.protocolclass.pbappendentryresponse)
            serialupdates.append( ( ii["bitpimserial"],
                                     {'sourcetype': self.serialsname, 'serial1': res.newserial, 'serial2': res.newserial,
                                     'sourceuniqueid': data['uniqueserial']})
                                  )

	self.pbend()
        data["serialupdates"]=serialupdates
	if len(ringindex) == 0: return


    def _findserial(self, serial, dict):
        """Searches dict to find entry with matching serial.  If not found,
        returns None"""
        for i in dict:
            if dict[i]['serial1']==serial:
                return i
        return None

    def getcalendar(self,result):
        res={}
        # Now read schedule
        buf=prototypes.buffer(self.getfilecontents("sch/sch_00.dat"))
        sc=self.protocolclass.schedulefile()
        sc.readfrombuffer(buf, logtitle="Calendar")
        self.logdata("Calendar", buf.getdata(), sc)
        for event in sc.events:
            entry={}
            if event.state == 0 or event.repeat == 0: continue    # deleted entry
            if event.date == 0x11223344: continue  # blanked entry
            date = event.date
            date += self._tm520epochtounix
            entry['start'] = self.decodedate(date)
            entry['end'] = self.decodedate(date)
            entry['pos']=event.pos
            entry['description'] = event.description
            if event.pos == 0: entry['description'] = 'Wake Up'
            entry['alarm'] = 0
            if event.alarm & 0xB0 == 0xB0: entry['alarm'] = 1
            entry['ringtone'] = 0
            entry['changeserial'] = 0
            entry['repeat'] = self._calrepeatvalues[event.repeat]

	    # Hack - using snoozedelay to store the DST flag
            entry['snoozedelay'] = time.localtime(date)[8]
            res[event.pos]=entry

        result['calendar']=res
        return result

    def savecalendar(self, dict, merge):
        # ::TODO:: obey merge param
        # what will be written to the files
        eventsf=self.protocolclass.schedulefile()

        # what are we working with
        cal=dict['calendar']
        newcal={}
        keys=cal.keys()
        keys.sort()

        # number of entries
        numactiveitems=len(keys)
        self.log("There are %d calendar entries" % (numactiveitems,))
        counter = 1

        # Write out alarm entry - see below for special handling
        alarm=self.protocolclass.scheduleevent()
        alarm.pos = 0
        alarm.date = 0x11223344
        alarm.state = 0
        alarm.alarm = 0x80
        alarm.repeat = 0
        alarm.description = " NO ENTRY        NO ENTRY      "

        eventsf.events.append(dummy)
        # play with each entry
        for k in keys:
            # entry is what we will return to user
            entry=cal[k]
            data=self.protocolclass.scheduleevent()
            if counter >= 50:
                self.log("More than 49 entries in calendar, only writing out the first 49")
                break
            data.pos=counter
            counter+=1
            entry['pos']=data.pos
            # simple copy of these fields
            for field in 'start','description':
                setattr(data,field,entry[field])

	    data.state = 2
	    data.alarm = 0
	    data.repeat = 1

            dst = -1
            if entry['snoozedelay']: dst = entry['snoozedelay']
            data.date = self.encodedate(entry['start'],dst)-self._tm520epochtounix

            # Special alarm handling - TM520 is not capable of having an alarmed
	    # entry, so we will only alarm on the earliest entry
            if entry['alarm'] > 0 and ( alarm.date == 0x11223344 or data.date < alarm.date ):
		alarm.date = data.date
		alarm.state = 1
		alarm.alarm = 0xB0
		alarm.repeat = 1
		if entry['repeat'] > 0: alarm.repeat = 2

            # put entry in nice shiny new dict we are building
            newcal[data.pos]=entry
            eventsf.events.append(data)

        if counter < 50:
            for i in range(counter, 50):
                dummy=self.protocolclass.scheduleevent()
                dummy.pos = i
                dummy.date = 0x11223344
                dummy.state = 0
                dummy.alarm = 0x80
                dummy.repeat = 0
                dummy.description = " NO ENTRY        NO ENTRY      "
                eventsf.events.append(dummy)

        # scribble everything out
        buf=prototypes.buffer()
        eventsf.writetobuffer(buf, logtitle="Writing calendar")
        self.writefile("sch/sch_00.dat", buf.getvalue())

        # fix passed in dict
        dict['calendar']=newcal

        return dict

    def getringtones(self, result):
	media = {}
	try:
	    ringers=self.getfilesystem('ringer')
	    for r in ringers:
		name = r[len('ringer/'):]
		media[name] = self.getfilecontents(r)
	except com_brew.BrewNoSuchDirectoryException: pass
	result['ringtone'] = media
	return result
	
    def saveringtones(self, results, merge):
	try:
	    ringers=self.getfilesystem('ringer')
	    for r in ringers.keys():
		ringers[r[len('ringer/'):]] = ringers[r]
		del ringers[r]
	except com_brew.BrewNoSuchDirectoryException:
	    self.log("Ringer directory doesn't exist, firmware might not be download capable")
	    return results

	index={}
	for r in results['ringtone-index']:
	    if r['origin'] == 'ringers': index.append(r['name'])

	for r in ringers.keys():
	    # it is in the original index, are we writing it back out?
	    if r in index and ringers[r]['size'] == len(results['ringtone'][r]): continue
	    else:
		if not merge or r in index:
		    # go ahead and delete unwanted files
		    print "deleting",r
		    self.rmfile("ringer/"+r)
		    if r in index: self.writefile("ringer/"+r, results['ringtone'][r])

    def decodedate(self,val):
        """Unpack 32 bit value into date/time

        @rtype: tuple
        @return: (year, month, day, hour, minute)
        """
        return time.localtime(val)[:5]

    def encodedate(self,val,dst):
        tmp = []
        for i in val: tmp.append(i)
        tmp += [0, 0, 0, dst]
        return time.mktime(tmp)

    def _findringtoneindex(self, index, name, pbentryname):
	if name is None: return 0
	for i in index:
	    if index[i]['name'] == name:
		return i
	self.log("%s: Unable to find ringtone %s in the index. Setting to default." % (pbentryname, name))
	return 0

    def _calcnumsum(self, entry, number):
	sumtbl = { '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
		   'H': 24, 'T': 36, '#': -13, '*': -6 }
	entry.number = number
	entry.chksum = 0
	lastseven = number
	if len(lastseven) > 7: lastseven = lastseven[len(lastseven)-7:]
	if len(lastseven) > 0:
	    for i in lastseven:
		entry.chksum += sumtbl[i]
	else: entry.chksum = 255

    def makeentry(self, counter, entry, dict):
        e=self.protocolclass.pbentry()
        e.entrynumber=counter
        
        for k in entry:
            # special treatment for lists
            if k == 'numbers':
                l=getattr(e,k)
                for item in entry[k]:
		    num=self.protocolclass.numentry()
		    self._calcnumsum(num, item)
                    l.append(num)
	    elif k == 'ringtone':
		e.ringtone = self._findringtoneindex(dict['ringtone-index'], entry[k], entry['name'])
            else:
                # everything else we just set
                setattr(e,k,entry[k])

        return e

def phonize(str):
    """Convert the phone number into something the phone understands
    
    All digits, P, H, T, * and # are kept, everything else is removed"""
    return re.sub("[^0-9HPT#*]", "", str)


class Profile(com_phone.Profile):
    serialsname='lgtm520'
    WALLPAPER_WIDTH=100
    WALLPAPER_HEIGHT=100
    MAX_WALLPAPER_BASENAME_LENGTH=19
    MAX_RINGTONE_BASENAME_LENGTH=19
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ."
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ."
    WALLPAPER_CONVERT_FORMAT="bmp"
    
    usbids = ( )
    deviceclasses = ("serial", )
    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('ringtone', 'write', 'MERGE'),
        ('ringtone', 'write', 'OVERWRITE'),
        )

    def convertphonebooktophone(self, helper, data):
	"Converts the data to what will be used by the phone"

	results = {}
	speeddial = {}
	entrynumber = 1

	for pbentry in data['phonebook']:
	    e = {}	# entry out
	    entry = data['phonebook'][pbentry]	# entry in

	    try:
		try:
		    e['name'] = helper.getfullname(entry.get('names', []),1,1,16)[0]
		except IndexError: raise helper.ConversionFailed("No name assigned to entry")
		try:
		    e['email']= helper.getemails(entry.get('emails', []),0,1,48)[0]
		except IndexError: e['email'] = ""
		e['ringtone'] = helper.getringtone(entry.get('ringtones', []), 'call', None)
		e['secret'] = helper.getflag(entry.get('flags',[]), 'secret', False)
		e['voicetag'] = helper.getflag(entry.get('flags',[]), 'voicetag', False)
		e['default'] = 0

		numbers = entry.get('numbers', [])
		if len(numbers) < 1: raise helper.ConversionFailed("Too few numbers. Need at least 1 number")
                e['numbers']=[ '', '', '', '', '' ]
		available = 5
		deferred = []
		for num in numbers:
		    number=phonize(num['number'])
		    if len(number) == 0: continue	# no actual digits in number
		    if len(number) > 32: number = number[:32]	# truncate long number
		    if available == 0: break	# all slots filled
		    if not 'type' in num:
			deferred.append(num)
			continue
		    elif not num['type'] in typemap['rev']:
			deferred.append(num)
			continue
		    else:
			typeidx = typemap['rev'][num['type']]
			if len(e['numbers'][typeidx]) == 0:
			    e['numbers'][typeidx] = number
			    if 'speeddial' in num and not 'entrynumber' in e:
				if not num['speeddial'] in speeddial:
				    e['entrynumber'] = num['speeddial']
				    e['default'] = typeidx
			    available -= 1
		if available > 0 and len(deferred) > 0:
		    for num in deferred:
			if available == 0: break
			number=phonize(num['number'])
			if len(number) > 32: number = number[:32]	# truncate long number
			for slot in range(0, 5):
			    if len(e['numbers'][slot]) > 0: continue
			    e['numbers'][slot] = number
			    if 'speeddial' in num and not 'entrynumber' in e:
				if not num['speeddial'] in speeddial:
				    e['entrynumber'] = num['speeddial']
				    e['default'] = slot
			    available -= 1
		if available == 5:
		    raise helper.ConversionFailed("The phone numbers didn't have any digits for this entry")
		if not 'entrynumber' in e:
		    while entrynumber in speedial:
			entrynumber += 1
		    if entrynumber > 199:
			self.log("Too many entries in phonebook, only 199 entries supported")
			break
		    e['entrynumber'] = entrynumber
		speeddial[e['entrynumber']] = pbentry

		serial1 = helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial1', 0)
		serial2 = helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial2', serial1)

		e['serial1'] = serial1
		e['serial2'] = serial2
		for ss in entry["serials"]:
		    if ss["sourcetype"]=="bitpim":
			e['bitpimserial']=ss
		assert e['bitpimserial']

		results[pbentry] = e

	    except helper.ConversionFailed: continue

	data['phonebook'] = results
	return data
