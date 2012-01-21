### BITPIM
###
### Copyright (C) 2005 Andrew Zitnay <drew@zitnay.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_lgvi125.py 4365 2007-08-17 21:11:59Z djpham $

"""Communicate with the LG VI125 cell phone"""

# standard modules
import datetime
import re
import time
import cStringIO
import sha

# my modules
import bpcalendar
import common
import commport
import copy
import p_lgvi125
import p_brew
import com_brew
import com_phone
import com_lg
import prototypes
import fileinfo
import call_history
import sms

class Phone(com_phone.Phone,com_brew.BrewProtocol,com_lg.LGPhonebook,com_lg.LGIndexedMedia):
    "Talk to the LG VI125 cell phone"

    desc="LG-VI125"
    wallpaperindexfilename="dloadindex/brewImageIndex.map"
    ringerindexfilename="dloadindex/brewRingerIndex.map"
    protocolclass=p_lgvi125
    serialsname='lgvi125'

    imagelocations=(
        # offset, index file, files location, type, maximumentries
        ( 10, "dloadindex/brewImageIndex.map", "brew/shared", "images", 30),
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries
        ( 50, "dloadindex/brewRingerIndex.map", "user/sound/ringer", "ringers", 30),
        )

    builtinimages=('Balloons', 'Soccer', 'Basketball', 'Bird',
                   'Sunflower', 'Puppy', 'Mountain House', 'Beach')

    builtinringtones=( 'Ring 1', 'Ring 2', 'Ring 3', 'Ring 4', 'Ring 5',
                       'Ring 6', 'Alert 1', 'Alert 2', 'Alert 3', 'Alert 4', 'Alert 5',
                       'Alert 6', 'Moon light', 'Bumble Bee', 'Latin', 'Baroque',
                       'Lovable baby', 'LG sound', 'Love Song', 'Badinerie', 'Follow Me',
                       'Head & Shoulder', 'Lake Trance', 'Beethovan', 'Lets Play',
                       'Piano Concerto No.1', 'Pleasure', 'Leichte Kavallerie',
                       'Up & Down Melody', 'Vivaldi - Winter' )

    
    def __init__(self, logtarget, commport):
        "Calls all the constructors and sets initial modes"
        com_phone.Phone.__init__(self, logtarget, commport)
	com_brew.BrewProtocol.__init__(self)
        com_lg.LGPhonebook.__init__(self)
        com_lg.LGIndexedMedia.__init__(self)
        self.log("Attempting to contact phone")
        self.mode=self.MODENONE
        self._cal_has_voice_id=hasattr(self.protocolclass, 'cal_has_voice_id') \
                                and self.protocolclass.cal_has_voice_id

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
        self.log("Phone serial number")
        results['uniqueserial']=sha.new(self.getfilecontents("nvm/$SYS.ESN")).hexdigest()
        # now read groups
        self.log("Reading group information")
        buf=prototypes.buffer(self.getfilecontents("pim/pbookgroup.dat"))
        g=self.protocolclass.pbgroups()
        g.readfrombuffer(buf)
        self.logdata("Groups read", buf.getdata(), g)
        groups={}
        for i in range(len(g.groups)):
            if len(g.groups[i].name) and g.groups[i].number!=255: # sometimes have zero length names
                groups[g.groups[i].number]={ 'ring': g.groups[i].ring, 'name': g.groups[i].name }
        results['groups']=groups
        self.getwallpaperindices(results)
        self.getringtoneindices(results)
        self.log("Fundamentals retrieved")
        return results

    def savesms(self, result, merge):
        self._setquicktext(result)
        result['rebootphone']=True
        return result

    def _setquicktext(self, result):
        sf=self.protocolclass.sms_quick_text()
        quicktext=result.get('canned_msg', [])
        count=0
        for entry in quicktext:
            if count < self.protocolclass.SMS_CANNED_MAX_ITEMS:
                sf.msgs.append(entry['text'][:self.protocolclass.SMS_CANNED_MAX_LENGTH-1])
                count+=1
            else:
                break
        if count!=0:
            # don't create the file if there are no entries 
            buf=prototypes.buffer()
            sf.writetobuffer(buf)
            self.logdata("Writing calendar", buf.getvalue(), sf)
            self.writefile(self.protocolclass.SMS_CANNED_FILENAME, buf.getvalue())
        return

    def getsms(self, result):
        # get the quicktext (LG name for canned messages)
        result['canned_msg']=self._getquicktext()
        result['sms']=self._readsms()
        return result

    def _readsms(self):
        res={}
        # go through the sms directory looking for messages
        for item in self.getfilesystem("sms").values():
            if item['type']=='file':
                folder=None
                for f,pat in self.protocolclass.SMS_PATTERNS.items():
                    if pat.match(item['name']):
                        folder=f
                        break
                if folder:
                    buf=prototypes.buffer(self.getfilecontents(item['name'], True))
                    self.logdata("SMS message file " +item['name'], buf.getdata())
                if folder=='Inbox':
                    sf=self.protocolclass.sms_in()
                    sf.readfrombuffer(buf)
                    entry=self._getinboxmessage(sf)
                    res[entry.id]=entry
                elif folder=='Sent':
                    sf=self.protocolclass.sms_out()
                    sf.readfrombuffer(buf)
                    entry=self._getoutboxmessage(sf)
                    res[entry.id]=entry
                elif folder=='Saved':
                    sf=self.protocolclass.sms_saved()
                    sf.readfrombuffer(buf)
                    if sf.outboxmsg:
                        entry=self._getoutboxmessage(sf.outbox)
                    else:
                        entry=self._getinboxmessage(sf.inbox)
                    entry.folder=entry.Folder_Saved
                    res[entry.id]=entry
        return res 

    def _getquicktext(self):
        quicks=[]
        try:
            buf=prototypes.buffer(self.getfilecontents("sms/mediacan000.dat"))
            sf=self.protocolclass.sms_quick_text()
            sf.readfrombuffer(buf)
            self.logdata("SMS quicktext file sms/mediacan000.dat", buf.getdata(), sf)
            for rec in sf.msgs:
                if rec.msg!="":
                    quicks.append({ 'text': rec.msg, 'type': sms.CannedMsgEntry.user_type })
        except com_brew.BrewNoSuchFileException:
            pass # do nothing if file doesn't exist
        return quicks

    def _getinboxmessage(self, sf):
        entry=sms.SMSEntry()
        entry.folder=entry.Folder_Inbox
        entry.datetime="%d%02d%02dT%02d%02d%02d" % (sf.GPStime)
        entry._from=self._getsender(sf.sender, sf.sender_length)
        entry.subject=sf.subject
        entry.locked=sf.locked
        if sf.priority==0:
            entry.priority=sms.SMSEntry.Priority_Normal
        else:
            entry.priority=sms.SMSEntry.Priority_High
        entry.read=sf.read
        txt=""
        if sf.num_msg_elements==1 and sf.bin_header1==0:
            txt=self._get_text_from_sms_msg_without_header(sf.msgs[0].msg, sf.msglengths[0].msglength)
        else:
            for i in range(sf.num_msg_elements):
                txt+=self._get_text_from_sms_msg_with_header(sf.msgs[i].msg, sf.msglengths[i].msglength)
        entry.text=unicode(txt, errors='ignore')
        entry.callback=sf.callback
        return entry

    def _getoutboxmessage(self, sf):
        entry=sms.SMSEntry()
        entry.folder=entry.Folder_Sent
        entry.datetime="%d%02d%02dT%02d%02d00" % ((sf.timesent))
        # add all the recipients
        for r in sf.recipients:
            if r.number:
                confirmed=(r.status==5)
                confirmed_date=None
                if confirmed:
                    confirmed_date="%d%02d%02dT%02d%02d00" % r.timereceived
                entry.add_recipient(r.number, confirmed, confirmed_date)
        entry.subject=sf.subject
        txt=""
        if sf.num_msg_elements==1 and not sf.messages[0].binary:
            txt=self._get_text_from_sms_msg_without_header(sf.messages[0].msg, sf.messages[0].length)
        else:
            for i in range(sf.num_msg_elements):
                txt+=self._get_text_from_sms_msg_with_header(sf.messages[i].msg, sf.messages[i].length)
        entry.text=unicode(txt, errors='ignore')
        if sf.priority==0:
            entry.priority=sms.SMSEntry.Priority_Normal
        else:
            entry.priority=sms.SMSEntry.Priority_High
        entry.locked=sf.locked
        entry.callback=sf.callback
        return entry

    def _get_text_from_sms_msg_without_header(self, msg, num_septets):
        out=""
        for i in range(num_septets):
            tmp = (msg[(i*7)/8].byte<<8) | msg[((i*7)/8) + 1].byte
            bit_index = 9 - ((i*7) % 8)
            out += chr((tmp >> bit_index) & 0x7f)
        return out

    def _get_text_from_sms_msg_with_header(self, msg, num_septets):
        data_len = ((msg[0].byte+1)*8+6)/7
        seven_bits={}
        raw={}
        out={}
        # re-order the text into the correct order for separating into
        # 7-bit characters
        for i in range(0, (num_septets*7)/8+8, 7):
            for k in range(7):
                raw[i+6-k]=msg[i+k].byte
        # extract the 7-bit chars
        for i in range(num_septets+7):
            tmp = (raw[(i*7)/8]<<8) | raw[((i*7)/8) + 1]
            bit_index = 9 - ((i*7) % 8)
            seven_bits[i] = (tmp >> bit_index) & 0x7f
        # correct the byte order and remove the data portion of the message
        i=0
        for i in range(0, num_septets+7, 8):
            for k in range(8):
                if(i+7-k-data_len>=0):
                    if i+k<num_septets+7:
                        out[i+7-k-data_len]=seven_bits[i+k]
        res=""
        for i in range(num_septets-data_len):
            res+=chr(out[i])
        return res

    def _getsender(self, raw, len):
        result=""
        for i in range(len):
            if(raw[i].byte==10):
                result+="0"
            else:
                result+="%d" % raw[i].byte
        return result

    def getcallhistory(self, result):
        res={}
        # read the incoming call history file
        self._readhistoryfile("pim/missed_log.dat", 'Missed', res)
        self._readhistoryfile("pim/outgoing_log.dat", 'Outgoing', res)
        self._readhistoryfile("pim/incoming_log.dat", 'Incoming', res)
        result['call_history']=res
        return result

    def _readhistoryfile(self, fname, folder, res):
        try:
            buf=prototypes.buffer(self.getfilecontents(fname))
            ch=self.protocolclass.callhistory()
            ch.readfrombuffer(buf)
            self.logdata("Call History", buf.getdata(), ch)
            for call in ch.calls:
                if call.number=='' and call.name=='':
                        continue
                entry=call_history.CallHistoryEntry()
                entry.folder=folder
                if call.duration:
                    entry.duration=call.duration
                entry.datetime=((call.GPStime))
                if call.number=='': # restricted calls have no number
                    entry.number=call.name
                else:
                    entry.number=call.number
                res[entry.id]=entry
        except com_brew.BrewNoSuchFileException:
            pass # do nothing if file doesn't exist
        return

    def getwallpaperindices(self, results):
        return self.getmediaindex(self.builtinimages, self.imagelocations, results, 'wallpaper-index')

    def getringtoneindices(self, results):
        return self.getmediaindex(self.builtinringtones, self.ringtonelocations, results, 'ringtone-index')

    def getphonebook(self,result):
        """Reads the phonebook data.  The L{getfundamentals} information will
        already be in result."""

        pbook={}
        # Bug in the phone.  if you repeatedly read the phone book it starts
        # returning a random number as the number of entries.  We get around
        # this by switching into brew mode which clears that.
        self.mode=self.MODENONE
        self.setmode(self.MODEBREW)
        self.log("Reading number of phonebook entries")
        req=self.protocolclass.pbinforequest()
        res=self.sendpbcommand(req, self.protocolclass.pbinforesponse)
        numentries=res.numentries
        if numentries<0 or numentries>1000:
            self.log("The phone is lying about how many entries are in the phonebook so we are doing it the hard way")
            numentries=0
            firstserial=None
            loop=xrange(0,1000)
            hardway=True
        else:
            self.log("There are %d entries" % (numentries,))
            loop=xrange(0, numentries)
            hardway=False
        # reset cursor
        self.sendpbcommand(self.protocolclass.pbinitrequest(), self.protocolclass.pbinitresponse)
        problemsdetected=False
        dupecheck={}
        for i in loop:
            if hardway:
                numentries+=1
            req=self.protocolclass.pbreadentryrequest()
            res=self.sendpbcommand(req, self.protocolclass.pbreadentryresponse)
            self.log("Read entry "+`i`+" - "+res.entry.name)
            entry=self.extractphonebookentry(res.entry, result)
            if hardway and firstserial is None:
                firstserial=res.entry.serial1
            pbook[i]=entry
            if res.entry.serial1 in dupecheck:
                self.log("Entry %s has same serial as entry %s.  This will cause problems." % (`entry`, dupecheck[res.entry.serial1]))
                problemsdetected=True
            else:
                dupecheck[res.entry.serial1]=entry
            self.progress(i, numentries, res.entry.name)
            #### Advance to next entry
            req=self.protocolclass.pbnextentryrequest()
            res=self.sendpbcommand(req, self.protocolclass.pbnextentryresponse)
            if hardway:
                # look to see if we have looped
                if res.serial==firstserial or res.serial==0:
                    break

        self.progress(numentries, numentries, "Phone book read completed")

        if problemsdetected:
            self.log("There are duplicate serial numbers.  See above for details.")
            raise common.IntegrityCheckFailed(self.desc, "Data in phonebook is inconsistent.  There are multiple entries with the same serial number.  See the log.")

        result['phonebook']=pbook
        cats=[]
        for i in result['groups']:
            if result['groups'][i]['name']!='No Group':
                cats.append(result['groups'][i]['name'])
        result['categories']=cats
        print "returning keys",result.keys()
        return pbook

    def savegroups(self, data):
        groups=data['groups']
        keys=groups.keys()
        keys.sort()

        g=self.protocolclass.pbgroups()
        sg=self.protocolclass.pbseqgroups()
        for k in keys:
            e=self.protocolclass.pbgroup()
            e.number=k
            e.unknown1=48
            e.ring=groups[k]['ring']
            e.unknown7=0
            e.unknown8=0
            e.name=groups[k]['name']
            g.groups.append(e)

            e=self.protocolclass.pbseqgroup()
            e.number=k
            e.unknown=48
            sg.seqgroups.append(e)

        for k in xrange(k+1,20):
		    e=self.protocolclass.pbseqgroup()
		    e.number=0
		    e.unknown=0
		    sg.seqgroups.append(e)

        groupnums=[]
        for k in range(self.protocolclass.NUMMAPGROUPS):
            groupnums.append(-1);

        for k in data['phonebook'].keys():
            groupnums[data['phonebook'][k]['serial1']]=data['phonebook'][k]['group']
            
        mg=self.protocolclass.pbmapgroups()
        for k in range(len(groupnums)):
            e=self.protocolclass.pbmapgroup()
            if (groupnums[k]==-1):
                e.number=255
                e.unknown=255
            else:
                e.number=groupnums[k]
                e.unknown=48
            mg.mapgroups.append(e)

        buffer=prototypes.buffer()
        g.writetobuffer(buffer)
        self.logdata("New group file", buffer.getvalue(), g)
        self.writefile("pim/pbookgroup.dat", buffer.getvalue())
        
        buffer=prototypes.buffer()
        sg.writetobuffer(buffer)
        self.logdata("New seqgroup file", buffer.getvalue(), sg)
        self.writefile("pim/pbookseqgroup.dat", buffer.getvalue())
        
        buffer=prototypes.buffer()
        mg.writetobuffer(buffer)
        self.logdata("New mapgroup file", buffer.getvalue(), mg)
        self.writefile("pim/pbookmapgroup.dat", buffer.getvalue())

    def savephonebook(self, data):
        "Saves out the phonebook"
        self.savegroups(data)
 
        progressmax=len(data['phonebook'].keys())

        # To write the phone book, we scan through all existing entries
        # and record their record number and serial.
        # We then delete any entries that aren't in data
        # We then write out our records, using overwrite or append
        # commands as necessary
        serialupdates=[]
        existingpbook={} # keep track of the phonebook that is on the phone
        self.mode=self.MODENONE
        self.setmode(self.MODEBREW) # see note in getphonebook() for why this is necessary
        self.setmode(self.MODEPHONEBOOK)
        # similar loop to reading
        req=self.protocolclass.pbinforequest()
        res=self.sendpbcommand(req, self.protocolclass.pbinforesponse)
        numexistingentries=res.numentries
        if numexistingentries<0 or numexistingentries>1000:
            self.log("The phone is lying about how many entries are in the phonebook so we are doing it the hard way")
            numexistingentries=0
            firstserial=None
            loop=xrange(0,1000)
            hardway=True
        else:
            self.log("There are %d existing entries" % (numexistingentries,))
            progressmax+=numexistingentries
            loop=xrange(0, numexistingentries)
            hardway=False
        progresscur=0
        # reset cursor
        self.sendpbcommand(self.protocolclass.pbinitrequest(), self.protocolclass.pbinitresponse)
        for i in loop:
            ### Read current entry
            if hardway:
                numexistingentries+=1
                progressmax+=1
            req=self.protocolclass.pbreadentryrequest()
            res=self.sendpbcommand(req, self.protocolclass.pbreadentryresponse)
            
            entry={ 'number':  res.entry.serial1, 'serial1':  res.entry.serial1,
                    'serial2': res.entry.serial2, 'name': res.entry.name}
            assert entry['serial1']==entry['serial2'] # always the same
            self.log("Reading entry "+`i`+" - "+entry['name'])
            if hardway and firstserial is None:
                firstserial=res.entry.serial1
            existingpbook[i]=entry 
            self.progress(progresscur, progressmax, "existing "+entry['name'])
            #### Advance to next entry
            req=self.protocolclass.pbnextentryrequest()
            res=self.sendpbcommand(req, self.protocolclass.pbnextentryresponse)
            progresscur+=1
            if hardway:
                # look to see if we have looped
                if res.serial==firstserial or res.serial==0:
                    break
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
            req.entrynumber=ii['serial1']
            req.serial1=ii['serial1']
            req.serial2=ii['serial2']
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
            print "looking for "+`ii['serial1']`+" "+`ii['name']`
            if ii['serial1'] in existingserials:
                continue # already wrote this one out
            print "found new"
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
        data["serialupdates"]=serialupdates

        return data
        

    def _findserial(self, serial, dict):
        """Searches dict to find entry with matching serial.  If not found,
        returns None"""
        for i in dict:
            if dict[i]['serial1']==serial:
                return i
        return None
            
    def _normaliseindices(self, d):
        "turn all negative keys into positive ones for index"
        res={}
        keys=d.keys()
        keys.sort()
        keys.reverse()
        for k in keys:
            if k<0:
                for c in range(999999):
                    if c not in keys and c not in res:
                        break
                res[c]=d[k]
            else:
                res[k]=d[k]
        return res

    def extractphonebookentry(self, entry, fundamentals):
        """Return a phonebook entry in BitPim format.  This is called from getphonebook."""
        res={}
        # serials
        res['serials']=[ {'sourcetype': self.serialsname, 'serial1': entry.serial1, 'serial2': entry.serial2,
                          'sourceuniqueid': fundamentals['uniqueserial']} ] 
        # only one name
        res['names']=[ {'full': entry.name} ]
        # only one category
        cat=fundamentals['groups'].get(entry.group, {'name': "No Group"})['name']
        if cat!="No Group":
            res['categories']=[ {'category': cat} ]
        # emails
        res['emails']=[]
        for i in entry.emails:
            if len(i.email):
                res['emails'].append( {'email': i.email} )
        if not len(res['emails']): del res['emails'] # it was empty
        # urls
        if 'url' in entry.getfields() and len(entry.url):
            res['urls']=[ {'url': entry.url} ]
        # memos
        if  'memo' in entry.getfields() and len(entry.memo):
            res['memos']=[ {'memo': entry.memo } ]
            
        # ringtones
        res['ringtones']=[]
        if 'ringtone' in entry.getfields() and entry.ringtone!=self.protocolclass.NORINGTONE:
            try:
                tone=fundamentals['ringtone-index'][entry.ringtone]['name']
                res['ringtones'].append({'ringtone': tone, 'use': 'call'})
            except:
                print "can't find ringtone for index",entry.ringtone
        if len(res['ringtones'])==0:
            del res['ringtones']
        res=self._assignpbtypeandspeeddials(entry, res)
        return res
                    
    def _assignpbtypeandspeeddials(self, entry, res):
        # numbers
        res['numbers']=[]
        for i in range(self.protocolclass.NUMPHONENUMBERS):
            num=entry.numbers[i].number
            type=entry.numbertypes[i].numbertype
            speeddial=entry.numberspeeddials[i].numberspeeddial
            if len(num):
                t=self.protocolclass.numbertypetab[type]
                if t[-1]=='2':
                    t=t[:-1]
                if speeddial==255:
                    res['numbers'].append({'number': num, 'type': t})
                else:
                    res['numbers'].append({'number': num, 'type': t, 'speeddial': speeddial})
        return res

    def _findmediainindex(self, index, name, pbentryname, type):
        if type=="ringtone": default=self.protocolclass.NORINGTONE
        elif type=="message ringtone": default=self.protocolclass.NOMSGRINGTONE
        elif type=="wallpaper": default=self.protocolclass.NOWALLPAPER
        else:
            assert False, "unknown type "+type
            
        if name is None:
            return default
        for i in index:
            if index[i]['name']==name:
                return i
        self.log("%s: Unable to find %s %s in the index. Setting to default." % (pbentryname, type, name))
        return default
                    
    def makeentry(self, counter, entry, data):
        """Creates pbentry object

        @param counter: The new entry number
        @param entry:   The phonebook object (as returned from convertphonebooktophone) that we
                        are using as the source
        @param data:    The main dictionary, which we use to get access to media indices amongst
                        other things
                        """
        e=self.protocolclass.pbentry()
        e.avatar=0
        
        for k in entry:
            # special treatment for lists

            if k in ('emails', 'numbers', 'numbertypes', 'numberspeeddials'):
                l=getattr(e,k)
                for item in entry[k]:
                    l.append(item)
            elif k=='ringtone':
                e.ringtone=self._findmediainindex(data['ringtone-index'], entry['ringtone'], entry['name'], 'ringtone')
            elif k in e.getfields():
                # everything else we just set
                setattr(e,k,entry[k])

        e.unknown7=0
        e.group=0		# couldn't figure out groups; this at least sets it to No Group
        e.unknown12=1	# couldn't figure out ringtone; this at least sets it to Default
        return e

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

    brew_version_txt_key='ams_version.txt'
    brew_version_file='ams/version.txt'
    lgpbinfo_key='lgpbinfo'
    esn_file_key='esn_file'
    esn_file='nvm/$SYS.ESN'
    my_model='VI125'
    def get_detect_data(self, res):
        # get the data needed for detection
        if not res.has_key(self.brew_version_txt_key):
            # read the BREW version.txt file, which may contain phone model info
            print 'reading BREW version.txt'
            try:
                # read this file
                s=self.getfilecontents(self.brew_version_file)
                res[self.brew_version_txt_key]=s
            except com_brew.BrewNoSuchFileException:
                res[self.brew_version_txt_key]=None
            except:
                if __debug__:
                    raise
                res[self.brew_version_txt_key]=None
        # get pbinfo data, which also may include phone model
        if not res.has_key(self.lgpbinfo_key):
            print 'getting pbinfo'
            try:
                req=self.protocolclass.pbinforequest()
                resp=self.sendpbcommand(req, self.protocolclass.pbstartsyncresponse)
                res[self.lgpbinfo_key]=resp.unknown
            except:
                if __debug__:
                    raise
                res[self.lgpbinfo_key]=None
        # attempt the get the ESN
        if not res.has_key(self.esn_file_key):
            print 'reading ESN file: '+`self.esn_file`+' end'
            try:
                s=self.getfilecontents(self.esn_file)
                res[self.esn_file_key]=s
            except:
                res[self.esn_file_key]=None

    def get_esn(self, data=None):
        # return the ESN for this phone
        try:
            if data is None:
                s=self.getfilecontents(self.esn_file)
            else:
                s=data
            if s:
                s=s[85:89]
                return '%02X%02X%02X%02X'%(ord(s[3]), ord(s[2]),
                                           ord(s[1]), ord(s[0]))
        except:
            if __debug__:
                raise

    def eval_detect_data(self, res):
        found=False
        if res.get(self.brew_version_txt_key, None) is not None:
            found=res[self.brew_version_txt_key][:len(self.my_model)]==self.my_model
        if not found and res.get(self.lgpbinfo_key, None):
            found=res[self.lgpbinfo_key].find(self.my_model)!=-1
        if found:
            res['model']=self.my_model
            res['manufacturer']='LG Electronics Inc'
            s=res.get(self.esn_file_key, None)
            if s:
                res['esn']=self.get_esn(s)

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
    
    # Calendar stuff------------------------------------------------------------
    def getcalendar(self,result):
        # Read exceptions file first
        try:
            buf=prototypes.buffer(self.getfilecontents(
                self.protocolclass.cal_exception_file_name))
            ex=self.protocolclass.scheduleexceptionfile()
            ex.readfrombuffer(buf)
            self.logdata("Calendar exceptions", buf.getdata(), ex)
            exceptions={}
            for i in ex.items:
                exceptions.setdefault(i.pos, []).append( (i.year,i.month,i.day) )
        except com_brew.BrewNoSuchFileException:
            exceptions={}

        # Now read schedule
        try:
            buf=prototypes.buffer(self.getfilecontents(
                self.protocolclass.cal_data_file_name))
            if len(buf.getdata())<2:
                # file is empty, and hence same as non-existent
                raise com_brew.BrewNoSuchFileException()
            sc=self.protocolclass.schedulefile()
            self.logdata("Calendar", buf.getdata(), sc)
            sc.readfrombuffer(buf)
            sc.readfrombuffer(buf)
            res=self.get_cal(sc, exceptions, result.get('ringtone-index', {}))
        except com_brew.BrewNoSuchFileException:
            res={}
        result['calendar']=res
        return result

    def savecalendar(self, dict, merge):
        # ::TODO:: obey merge param
        # get the list of available voice alarm files
        voice_files={}
        if self._cal_has_voice_id:
            try:
                file_list=self.getfilesystem(self.protocolclass.cal_dir)
                for k in file_list.keys():
                    if k.endswith(self.protocolclass.cal_voice_ext):
                        voice_files[int(k[8:11])]=k
            except:
                self.log('Failed to list Calendar Voice Files')
        # build the schedule file
        sc=self.protocolclass.schedulefile()
        sc_ex=self.set_cal(sc, dict.get('calendar', {}),
                           dict.get('ringtone-index', {}),
                           voice_files)
        buf=prototypes.buffer()
        sc.writetobuffer(buf)
        self.writefile(self.protocolclass.cal_data_file_name,
                         buf.getvalue())
        # build the exceptions
        exceptions_file=self.protocolclass.scheduleexceptionfile()
        for k,l in sc_ex.items():
            for x in l:
                _ex=self.protocolclass.scheduleexception()
                _ex.pos=k
                _ex.year, _ex.month, _ex.day=x
                exceptions_file.items.append(_ex)
        buf=prototypes.buffer()
        exceptions_file.writetobuffer(buf)
        self.writefile(self.protocolclass.cal_exception_file_name,
                         buf.getvalue())
        # clear out any alarm voice files that may have been deleted
        if self._cal_has_voice_id:
            for k,e in voice_files.items():
                try:
                    self.rmfile(e)
                except:
                    self.log('Failed to delete file '+e)
        return dict

    _repeat_values={
        protocolclass.CAL_REP_DAILY: bpcalendar.RepeatEntry.daily,
        protocolclass.CAL_REP_MONFRI: bpcalendar.RepeatEntry.daily,
        protocolclass.CAL_REP_WEEKLY: bpcalendar.RepeatEntry.weekly,
        protocolclass.CAL_REP_MONTHLY: bpcalendar.RepeatEntry.monthly,
        protocolclass.CAL_REP_YEARLY: bpcalendar.RepeatEntry.yearly
        }

    def _build_cal_repeat(self, event, exceptions):
        rep_val=Phone._repeat_values.get(event.repeat, None)
        if not rep_val:
            return None
        rep=bpcalendar.RepeatEntry(rep_val)
        if event.repeat==self.protocolclass.CAL_REP_MONFRI:
            rep.interval=rep.dow=0
        elif event.repeat!=self.protocolclass.CAL_REP_YEARLY:
            rep.interval=1
            rep.dow=0
        # do exceptions
        cal_ex=exceptions.get(event.pos, [])
        for e in cal_ex:
            rep.add_suppressed(*e)
        return rep

    def _get_voice_id(self, event, entry):
        if event.hasvoice:
            entry.voice=event.voiceid

    def _build_cal_entry(self, event, exceptions, ringtone_index):
        # return a copy of bpcalendar object based on my values
        # general fields
        entry=bpcalendar.CalendarEntry()
        entry.start=event.start
        entry.end=event.end
        entry.description=event.description
        # check for allday event
        if entry.start[3:]==(0, 0) and entry.end[3:]==(23, 59):
            entry.allday=True
        # alarm
        if event.alarmtype:
            entry.alarm=event.alarmhours*60+event.alarmminutes
        # ringtone
        rt_idx=event.ringtone
        # hack to account for the VX4650 weird ringtone setup
        if rt_idx<50:
            # 1st part of builtin ringtones, need offset by 1
            rt_idx+=1
        entry.ringtone=ringtone_index.get(rt_idx, {'name': None} )['name']
        # voice ID if applicable
        if self._cal_has_voice_id:
            self._get_voice_id(event, entry)
        # repeat info
        entry.repeat=self._build_cal_repeat(event, exceptions)
        return entry

    def get_cal(self, sch_file, exceptions, ringtone_index):
        res={}
        for event in sch_file.events:
            if event.pos==-1:   # blank entry
                continue
            cal_event=self._build_cal_entry(event, exceptions, ringtone_index)
            res[cal_event.id]=cal_event
        return res

    _alarm_info={
        -1: (protocolclass.CAL_REMINDER_NONE, 100, 100),
        0: (protocolclass.CAL_REMINDER_ONTIME, 0, 0),
        5: (protocolclass.CAL_REMINDER_5MIN, 5, 0),
        10: (protocolclass.CAL_REMINDER_10MIN, 10, 0),
        60: (protocolclass.CAL_REMINDER_1HOUR, 0, 1),
        1440: (protocolclass.CAL_REMINDER_1DAY, 0, 24),
        2880: (protocolclass.CAL_REMINDER_2DAYS, 0, 48) }
    _default_alarm=(protocolclass.CAL_REMINDER_NONE, 100, 100)    # default alarm is off
    _phone_dow={
        1: protocolclass.CAL_DOW_SUN,
        2: protocolclass.CAL_DOW_MON,
        4: protocolclass.CAL_DOW_TUE,
        8: protocolclass.CAL_DOW_WED,
        16: protocolclass.CAL_DOW_THU,
        32: protocolclass.CAL_DOW_FRI,
        64: protocolclass.CAL_DOW_SAT
        }

    def _set_repeat_event(self, event, entry, exceptions):
        rep_val=self.protocolclass.CAL_REP_NONE
        day_bitmap=0
        rep=entry.repeat
        if rep:
            rep_type=rep.repeat_type
            if rep_type==bpcalendar.RepeatEntry.yearly:
                rep_val=self.protocolclass.CAL_REP_YEARLY
            else:
                rep_interval=rep.interval
                rep_dow=rep.dow
                if rep_type==bpcalendar.RepeatEntry.daily:
                    if rep_interval==0:
                        rep_val=self.protocolclass.CAL_REP_MONFRI
                    elif rep_interval==1:
                        rep_val=self.protocolclass.CAL_REP_DAILY
                elif rep_type==bpcalendar.RepeatEntry.weekly:
                    start_dow=1<<datetime.date(*event.start[:3]).isoweekday()%7
                    if (rep_dow==0 or rep_dow==start_dow) and rep_interval==1:
                        rep_val=self.protocolclass.CAL_REP_WEEKLY
                        day_bitmap=self._phone_dow.get(start_dow, 0)
                elif rep_type==bpcalendar.RepeatEntry.monthly:
                    if rep_dow==0:
                        rep_val=self.protocolclass.CAL_REP_MONTHLY
            if rep_val!=self.protocolclass.CAL_REP_NONE:
                # build exception list
                if rep.suppressed:
                    day_bitmap|=self.protocolclass.CAL_DOW_EXCEPTIONS
                for x in rep.suppressed:
                    exceptions.setdefault(event.pos, []).append(x.get()[:3])
                # this is a repeat event, set the end date appropriately
                if event.end[:3]==entry.no_end_date:
                    event.end=self.protocolclass.CAL_REPEAT_DATE+event.end[3:]
                else:
                    event.end=entry.end
        event.repeat=rep_val
        event.daybitmap=day_bitmap
            
    def _set_alarm(self, event, entry):
        # set alarm value based on entry's value, or its approximation
        keys=Phone._alarm_info.keys()
        keys.sort()
        keys.reverse()
        _alarm_val=entry.alarm
        _alarm_key=None
        for k in keys:
            if _alarm_val>=k:
                _alarm_key=k
                break
        event.alarmtype, event.alarmminutes, event.alarmhours=Phone._alarm_info.get(
            _alarm_key, self._default_alarm)

    def _set_voice_id(self, event, entry, voice_files):
        if entry.voice and \
           voice_files.has_key(entry.voice-self.protocolclass.cal_voice_id_ofs):
            event.hasvoice=1
            event.voiceid=entry.voice
            del voice_files[entry.voice-self.protocolclass.cal_voice_id_ofs]
        else:
            event.hasvoice=0
            event.voiceid=self.protocolclass.CAL_NO_VOICE
        
    def _set_cal_event(self, event, entry, exceptions, ringtone_index,
                       voice_files):
        # desc
        event.description=entry.description
        # start & end times
        if entry.allday:
            event.start=entry.start[:3]+(0,0)
            event.end=entry.start[:3]+(23,59)
        else:
            event.start=entry.start
            event.end=entry.start[:3]+entry.end[3:]
        # make sure the event lasts in 1 calendar day
        if event.end<event.start:
            event.end=event.start[:3]+(23,59)
        # alarm
        self._set_alarm(event, entry)
        # ringtone
        rt=0    # always default to the first bultin ringtone
        if entry.ringtone:
            for k,e in ringtone_index.items():
                if e['name']==entry.ringtone:
                    rt=k
                    break
            if rt and rt<50:
                rt-=1
        event.ringtone=rt
        # voice ID
        if self._cal_has_voice_id:
            self._set_voice_id(event, entry, voice_files)
        # repeat
        self._set_repeat_event(event, entry, exceptions)
            
    def set_cal(self, sch_file, cal_dict, ringtone_index, voice_files):
        sch_file.numactiveitems=len(cal_dict)
        exceptions={}
        _pos=2
        _packet_size=None
##        _today=datetime.date.today().timetuple()[:5]
        for k, e in cal_dict.items():
##            # only send either repeat events or present&future single events
##            if e.repeat or (e.start>=_today):
            event=self.protocolclass.scheduleevent()
            event.pos=_pos
            self._set_cal_event(event, e, exceptions, ringtone_index,
                                voice_files)
            sch_file.events.append(event)
            if not _packet_size:
                _packet_size=event.packetsize()
            _pos+=_packet_size
        return exceptions

    def _get_phone_number(self):
        # return the phone number of this phone
        s=''
        try:
            buf=self.getfilecontents('nvm/nvm/nvm_0000')
            ofs=0xce
            if buf[ofs]=='\x01':
                ofs+=1
                while buf[ofs]!='\x01':
                    s+=buf[ofs]
                    ofs+=1
        except:
            if __debug__:
                raise
        return s
    def getfirmwareinformation(self):
        self.log("Getting firmware information")
        req=p_brew.firmwarerequest()
        res=self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
        return res
    def getphoneinfo(self, phone_info):
        # returning some basic phone info
        # double check if this's the right phone.
        try:
            if self.getfilecontents(self.brew_version_file)[:len(self.my_model)]==self.my_model:
                phone_info.model=self.my_model
                phone_info.manufacturer=Profile.phone_manufacturer
                phone_info.phone_number=self._get_phone_number()
                phone_info.firmware_version=self.getfirmwareinformation().firmwareversion
                phone_info.esn=self.get_esn()
        except:
            if __debug__:
                raise

def phonize(str):
    """Convert the phone number into something the phone understands
    
    All digits, P, T, * and # are kept, everything else is removed"""
    return re.sub("[^0-9PT#*]", "", str)

parentprofile=com_phone.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='VI125'

    WALLPAPER_WIDTH=120
    WALLPAPER_HEIGHT=98
    MAX_WALLPAPER_BASENAME_LENGTH=19
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ."
    WALLPAPER_CONVERT_FORMAT="bmp"
    
    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ."
    
    # which usb ids correspond to us
    usbids_straight=( ( 0x1004, 0x6000, 2), )# VID=LG Electronics, PID=LG VI125 -internal USB diagnostics interface
    usbids_usbtoserial=(
        ( 0x067b, 0x2303, None), # VID=Prolific, PID=USB to serial
        ( 0x0403, 0x6001, None), # VID=FTDI, PID=USB to serial
        ( 0x0731, 0x2003, None), # VID=Susteen, PID=Universal USB to serial
        )
    usbids=usbids_straight+usbids_usbtoserial
    
    # which device classes we are.  not we are not modem!
    deviceclasses=("serial",)

    # nb we don't allow save to camera so it isn't listed here
    imageorigins={}
    imageorigins.update(common.getkv(parentprofile.stockimageorigins, "images"))
    def GetImageOrigins(self):
        return self.imageorigins

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 120, 'height': 98, 'format': "BMP"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "pictureid",
                                      {'width': 120, 'height': 98, 'format': "BMP"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 120, 'height': 133, 'format': "BMP"}))

    def GetTargetsForImageOrigin(self, origin):
        return self.imagetargets
    
    def __init__(self):
        parentprofile.__init__(self)


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
                if k: # ignore key 0 which is 'No Group'
                    name=data['groups'][k]['name']
                    pad.append(name)

        groups=helper.getmostpopularcategories(10, data['phonebook'], ["No Group"], 22, pad)

        # alpha sort
        groups.sort()

        # newgroups
        newgroups={}

        # put in No group
        newgroups[0]={'ring': 0, 'name': 'No Group'}

        # populate
        for name in groups:
            # existing entries remain unchanged
            if name=="No Group": continue
            key,value=self._getgroup(name, data['groups'])
            if key is not None and key!=0:
                newgroups[key]=value
        # new entries get whatever numbers are free
        for name in groups:
            key,value=self._getgroup(name, newgroups)
            if key is None:
                for key in range(1,100000):
                    if key not in newgroups:
                        newgroups[key]={'ring': 0, 'name': name}
                        break
                       
        # yay, done
        if data['groups']!=newgroups:
            data['groups']=newgroups
            data['rebootphone']=True
            
    def convertphonebooktophone(self, helper, data):
        """Converts the data to what will be used by the phone

        @param data: contains the dict returned by getfundamentals
                     as well as where the results go"""
        results={}
        
        self.normalisegroups(helper, data)

        for pbentry in data['phonebook']:
            if len(results)==self.protocolclass.NUMPHONEBOOKENTRIES:
                break
            e={} # entry out
            entry=data['phonebook'][pbentry] # entry in
            try:
                # serial
                serial1=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial1', 0)
                serial2=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial2', serial1)

                e['serial1']=serial1
                e['serial2']=serial2
                for ss in entry["serials"]:
                    if ss["sourcetype"]=="bitpim":
                        e['bitpimserial']=ss
                assert e['bitpimserial']

                # name
                e['name']=helper.getfullname(entry.get('names', []),1,1,22)[0]

                # categories/groups
                cat=helper.makeone(helper.getcategory(entry.get('categories', []),0,1,22), None)
                if cat is None:
                    e['group']=0
                else:
                    key,value=self._getgroup(cat, data['groups'])
                    if key is not None:
                        e['group']=key
                    else:
                        # sorry no space for this category
                        e['group']=0

                # email addresses
                emails=helper.getemails(entry.get('emails', []) ,0,self.protocolclass.NUMEMAILS,48)
                e['emails']=helper.filllist(emails, self.protocolclass.NUMEMAILS, "")

                # url
                e['url']=helper.makeone(helper.geturls(entry.get('urls', []), 0,1,48), "")

                # memo (-1 is to leave space for null terminator - not all software puts it in, but we do)
                e['memo']=helper.makeone(helper.getmemos(entry.get('memos', []), 0, 1, self.protocolclass.MEMOLENGTH-1), "")

                # phone numbers
                # there must be at least one email address or phonenumber
                minnumbers=1
                if len(emails): minnumbers=0
                numbers=helper.getnumbers(entry.get('numbers', []),minnumbers,self.protocolclass.NUMPHONENUMBERS)
                e['numberspeeddials']=[]
                e['numbertypes']=[]
                e['numbers']=[]
                for numindex in range(len(numbers)):
                    num=numbers[numindex]
                    # deal with type
                    b4=len(e['numbertypes'])
                    type=num['type']
                    for i,t in enumerate(self.protocolclass.numbertypetab):
                        if type==t:
                            # some voodoo to ensure the second home becomes home2
                            if i in e['numbertypes'] and t[-1]!='2':
                                type+='2'
                                continue
                            e['numbertypes'].append(i)
                            break
                        if t=='none': # conveniently last entry
                            e['numbertypes'].append(i)
                            break
                    if len(e['numbertypes'])==b4:
                        # we couldn't find a type for the number
                        continue 
                    # deal with number
                    number=phonize(num['number'])
                    if len(number)==0:
                        # no actual digits in the number
                        continue
                    if len(number)>48: # get this number from somewhere sensible
                        # ::TODO:: number is too long and we have to either truncate it or ignore it?
                        number=number[:48] # truncate for moment
                    e['numbers'].append(number)
                    # deal with speed dial
                    sd=num.get("speeddial", -1)
                    if self.protocolclass.NUMSPEEDDIALS:
                        if sd>=self.protocolclass.FIRSTSPEEDDIAL and sd<=self.protocolclass.LASTSPEEDDIAL:
                            e['numberspeeddials'].append(sd)
                        else:
                            e['numberspeeddials'].append(255)

                e['numberspeeddials']=helper.filllist(e['numberspeeddials'], 5, 255)
                e['numbertypes']=helper.filllist(e['numbertypes'], 5, 0)
                e['numbers']=helper.filllist(e['numbers'], 5, "")

                # ringtone
                e['ringtone']=helper.getringtone(entry.get('ringtones', []), 'call', None)

                # flags
                e['secret']=helper.getflag(entry.get('flags',[]), 'secret', False)

                results[pbentry]=e
                
            except helper.ConversionFailed:
                continue

        data['phonebook']=results
        return data

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        #('calendar', 'read', None),   # all calendar reading
        #('wallpaper', 'read', None),  # all wallpaper reading
        #('ringtone', 'read', None),   # all ringtone reading
        #('call_history', 'read', None),# all call history list reading
        #('sms', 'read', None),         # all SMS list reading
        #('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        #('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        #('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        #('wallpaper', 'write', 'OVERWRITE'),
        #('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
        #('ringtone', 'write', 'OVERWRITE'),
        #('sms', 'write', 'OVERWRITE'),        # all SMS list writing
        )

    def QueryAudio(self, origin, currentextension, afi):
        # we don't modify any of these
        if afi.format in ("MIDI", "QCP", "PMD"):
            return currentextension, afi
        # examine mp3
        if afi.format=="MP3":
            if afi.channels==1 and 8<=afi.bitrate<=64 and 16000<=afi.samplerate<=22050:
                return currentextension, afi
        # convert it
        return ("mp3", fileinfo.AudioFileInfo(afi, **{'format': 'MP3', 'channels': 1, 'bitrate': 32, 'samplerate': 22050}))



