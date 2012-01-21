### BITPIM
###
### Copyright (C) 2006 Simon Capper <skyjunky@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

"""Communicate with the LG PM225 (Sprint) cell phone"""

# standard modules
import re
import time
import cStringIO
import sha

# my modules
import p_lgpm225
import p_brew
import common
import commport
import com_brew
import com_phone
import com_lg
import com_lgvx4400
import helpids
import prototypes
import call_history
import sms
import fileinfo
import memo


class Phone(com_lgvx4400.Phone):
    "Talk to the LG PM225 cell phone"

    desc="LG PM225"
    helpid=helpids.ID_PHONE_LGPM225
    protocolclass=p_lgpm225
    serialsname='lgpm225'

    # read only locations, for regular ringers/wallpaper this phone stores
    # the information in a different location
    imagelocations=(
        # offset, index file, files location, type, maximumentries
        (0x600, "setas/dcamIndex.map", "Dcam/Wallet", "camera", 50, 6),
        )

    ringtonelocations=(
        # offset, index file, files location, type, maximumentries
        (0x1100, "setas/voicememoRingerIndex.map", "VoiceDB/All/Memos", "voice_memo", 50, 11),
        )

    builtinimages=('Spectrum', 'Speed', 'Drops', 'Country Road', 
                   'Houses','Tulip', 'Flower', 'Lines', 'Network', 'Abstract')

    builtinringtones=( 'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5', 'Tone 6',
                       'Alert 1', 'Alert 2', 'Alert 3', 'Alert 4', 'Alert 5', 'Alert 6',
                       'Moonlight', 'Bumble Bee', 'Latin', 'Baroque',
                       'Lovable Baby', 'LG Sound', 'Love Song', 'Badinerie',
                       'Follow Me', 'Head, Shoulders, Knees & Toes', 'Lake Trance', 'Beethoven',
                       'Let''s Play', 'Piano Concerto No.1', 'Pleasure',
                       'Leichte Kavallerie', 'Up & Down Melody', 'Vivaldi - Winter')

    def __init__(self, logtarget, commport):
        "Calls all the constructors and sets initial modes"
        com_phone.Phone.__init__(self, logtarget, commport)
        com_brew.BrewProtocol.__init__(self)
        com_lg.LGPhonebook.__init__(self)
        self.log("Attempting to contact phone")
        self._cal_has_voice_id=hasattr(self.protocolclass, 'cal_has_voice_id') \
                                and self.protocolclass.cal_has_voice_id
        self.mode=self.MODENONE

#----- PhoneBook -----------------------------------------------------------------------

    def getfundamentals(self, results):
        """Gets information fundamental to interoperating with the phone and UI.

        Currently this is:

          - 'uniqueserial'     a unique serial number representing the phone
          - 'groups'           the phonebook groups

        This method is called before we read the phonebook data or before we
        write phonebook data.
        """

        # use a hash of ESN and other stuff (being paranoid)
        self.log("Retrieving fundamental phone information")
        self.log("Phone serial number")
        results['uniqueserial']=sha.new(self.getfilecontents("nvm/$SYS.ESN")).hexdigest()
        self.log(results)

        # now read groups
        self.log("Reading group information")
        buf=prototypes.buffer(self.getfilecontents("pim/pbookgroup.dat"))
        g=self.protocolclass.pbgroups()
        g.readfrombuffer(buf, logtitle="Groups read")
        groups={}
        for i in range(len(g.groups)):
            if len(g.groups[i].name): # sometimes have zero length names
                groups[g.groups[i].group_id]={'name': g.groups[i].name }
        results['groups']=groups
        self.getwallpaperindices(results)
        self.getringtoneindices(results)
        self.log("Fundamentals retrieved")
        return results

    def syncbegin(self):
       self.mode = self.MODEPHONEBOOK
       self.sendpbcommand(self.protocolclass.pbstartsyncrequest(), self.protocolclass.pbstartsyncresponse)

    def syncend(self):
       req=self.protocolclass.pbendsyncrequest()
       self.sendpbcommand(req, self.protocolclass.pbendsyncresponse)

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
        self.mode = self.MODEBREW
        res=self.sendpbcommand(self.protocolclass.pbinforequest(), self.protocolclass.pbinforesponse)
        numentries = res.numentries
        self.log("There are %d entries" % (numentries,))
        for i in range(0, numentries):
            ### Read current entry
            req=self.protocolclass.pbreadentryrequest()
            res=self.sendpbcommand(req, self.protocolclass.pbreadentryresponse)
            self.log("Read entry "+`i`+" - "+res.entry.name)
            entry=self.extractphonebookentry(res.entry, result)
            pbook[res.entry.entrynumber]=entry
            self.progress(i, numentries, res.entry.name)
            #### Advance to next entry
            req=self.protocolclass.pbnextentryrequest()
            self.sendpbcommand(req, self.protocolclass.pbnextentryresponse)

        pbook=self.get_phonebook_media(pbook, result)

        self.progress(numentries, numentries, "Phone book read completed")
        self.log("Phone book read completed")

        result['phonebook']=pbook

        cats=[]
        for i in result['groups']:
            if result['groups'][i]['name']!='No Group':
                cats.append(result['groups'][i]['name'])
        result['categories']=cats
        return pbook

    def get_phonebook_media(self, pbook, fundamentals):
        """This phone does not provide ringtone and image info for contacts in 
        the regular packets so we have to read the filesystem directly """
        buf=prototypes.buffer(self.getfilecontents(self.protocolclass.phonebook_media))
        g=self.protocolclass.pb_contact_media_file()
        g.readfrombuffer(buf, logtitle="PB Media read")
        for i in range(len(g.contacts)):
            # adjust wallpaper for stock
            if (g.contacts[i].wallpaper & 0xFF00)==0x100:
                g.contacts[i].wallpaper-=0x100
            if __debug__:
                tone="None"
                paper="None"
                try:
                    tone=fundamentals['ringtone-index'][g.contacts[i].ringer]['name']
                except:
                    pass
                try:
                    paper=fundamentals['wallpaper-index'][g.contacts[i].wallpaper]['name']
                except:
                    pass
                self.log("media entry "+g.contacts[i].name+" ringer "+`tone`+" ("+`g.contacts[i].ringer`+")")
                self.log("media entry "+g.contacts[i].name+" wallpaper "+`paper`+" ("+`g.contacts[i].wallpaper`+")")
            if g.contacts[i].index in pbook:
                self.log("Index "+`g.contacts[i].index`+" found")
                if g.contacts[i].ringer:
                    try:
                        tone=fundamentals['ringtone-index'][g.contacts[i].ringer]['name']
                        pbook[g.contacts[i].index]['ringtones']=[{'ringtone': tone, 'use': 'call'}]
                    except:
                        self.log("Exception in ringtone assignment")
                if g.contacts[i].wallpaper:
                    try:
                        paper=fundamentals['wallpaper-index'][g.contacts[i].wallpaper]['name']
                        pbook[g.contacts[i].index]['wallpapers']=[{'wallpaper': paper, 'use': 'call'}]                
                    except:
                        self.log("Exception in wallpaper assignment")
            else:
                self.log("Index "+`g.contacts[i].index`+" not found")
        return pbook

    def extractphonebookentry(self, entry, fundamentals):
        """Return a phonebook entry in BitPim format.  This is called from getphonebook."""
        res={}
        # serials
        res['serials']=[ {'sourcetype': self.serialsname, 'serial1': entry.serial1,
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
        # private
        if 'secret' in entry.getfields() and entry.secret:
            # we only supply secret if it is true
            res['flags']=[ {'secret': entry.secret } ]
        # memos
        if  'memo' in entry.getfields() and len(entry.memo):
            res['memos']=[ {'memo': entry.memo } ]

        # numbers
        res['numbers']=[]
        for i in range(self.protocolclass.NUMPHONENUMBERS):
            num=entry.numbers[i].number
            type=entry.numbertypes[i].numbertype
            speeddial=entry.numberspeeds[i].numberspeed
            if len(num):
                t=self.protocolclass.numbertypetab[type]
                if speeddial != 0xFF: # invalid entry
                    res['numbers'].append({'number': num, 'type': t, 'speeddial': speeddial})
                else:
                    res['numbers'].append({'number': num, 'type': t})
        return res

    def makeentry(self, counter, entry, data):
        """Creates pbentry object

        @param counter: The new entry number
        @param entry:   The phonebook object (as returned from convertphonebooktophone) that we
                        are using as the source
        @param data:    The main dictionary, which we use to get access to media indices amongst
                        other things
                        """
        e=self.protocolclass.pbentry()

        e.entrynumber=counter

        for k in entry:
            # special treatment for lists
            if k in ('emails', 'numbers', 'numbertypes', 'numberspeeds'):
                l=getattr(e,k)
                for item in entry[k]:
                    l.append(item)
            elif k=='ringtone':
                try:
                    e.ringtone=self._findmediainindex(data['ringtone-index'], entry['ringtone'], entry['name'], 'ringtone')
                except:
                    pass
            elif k=='msgringtone':
                pass # not supported by phone
                #e.msgringtone=self._findmediainindex(data['ringtone-index'], entry['msgringtone'], entry['name'], 'message ringtone')
            elif k=='wallpaper':
                try:
                    e.wallpaper=self._findmediainindex(data['wallpaper-index'], entry['wallpaper'], entry['name'], 'wallpaper')
                    # adjust for stock wallpaper
                    if e.wallpaper < 0x100:
                        e.wallpaper+=0x100
                except:
                    pass
            elif k in e.getfields():
                # everything else we just set
                setattr(e,k,entry[k])

        return e

    def save_phonebook_media(self, pb_entries):
        """This phone does not provide ringtone and image info for contacts in 
        the regular packets so we have to write the filesystem directly """
        # we read the file, modify it and write it back
        buf=prototypes.buffer(self.getfilecontents(self.protocolclass.phonebook_media))
        g=self.protocolclass.pb_contact_media_file()
        g.readfrombuffer(buf, logtitle="PB Media read")
        rc=False
        for i in range(len(g.contacts)):
            if g.contacts[i].index in pb_entries:
                if g.contacts[i].ringer!=pb_entries[g.contacts[i].index].ringtone:
                    g.contacts[i].ringer=pb_entries[g.contacts[i].index].ringtone
                    rc=True
                if g.contacts[i].wallpaper!=pb_entries[g.contacts[i].index].wallpaper:
                    g.contacts[i].wallpaper=pb_entries[g.contacts[i].index].wallpaper
                    rc=True
        if rc:
            buf=prototypes.buffer()
            g.writetobuffer(buf, logtitle="Writing PB media file")
            self.writefile(self.protocolclass.phonebook_media, buf.getvalue())
        else:
            self.log("PB media file up to date, no write required")
        return rc

    def savegroups(self, data):
        groups=data['groups']
        keys=groups.keys()
        keys.sort()
        g=self.protocolclass.pbgroups()
        for k in keys:
            e=self.protocolclass.pbgroup()
            e.group_id=k
            e.rectype = 0x30
            e.name=groups[k]['name']
            g.groups.append(e)
        buffer=prototypes.buffer()
        g.writetobuffer(buffer, logtitle="New group file")
        self.writefile("pim/pbookgroup.dat", buffer.getvalue())

    def savephonebook(self, data):
        "Saves out the phonebook"
        self.savegroups(data)
        
#        if __debug__:
#            # for testing without a real phone, the packets are stored in a 
#            # file and can be examined
#            counter=0
#            pb_entries={}
#            for i in data['phonebook'].keys():
#                ii=data['phonebook'][i]
#                entry=self.makeentry(counter, ii, data)
#                counter+=1
#                req=self.protocolclass.pbupdateentryrequest()
#                req.entry=entry
#               req.header.sequence=counter
 #               buffer=prototypes.buffer()
#                req.writetobuffer(buffer, logtitle="New contents for pim/pb"+`counter`+".dat")
#                self.writefile("pim/pb"+`counter`+".dat", buffer.getvalue())
#                pb_entries[counter]=entry
#            self.save_phonebook_media(pb_entries)

        # set up progress bar on main window
        progressmax=len(data['phonebook'].keys())

        # To write the phone book, we scan through all existing entries
        # and record their record number and serials.
        # We then delete any entries that aren't in data
        # We then write out our records, using overwrite or append
        # commands as necessary
        serialupdates=[]
        pb_entries={}
        existingpbook={} # keep track of the phonebook that is on the phone
        self.mode=self.MODENONE
        self.setmode(self.MODEBREW) # see note in getphonebook() for why this is necessary
        self.setmode(self.MODEPHONEBOOK)
        # similar loop to reading
        req=self.protocolclass.pbinforequest()
        res=self.sendpbcommand(req, self.protocolclass.pbinforesponse)
        numexistingentries=res.numentries
        self.log("There are %d existing entries" % (numexistingentries,))
        progressmax+=numexistingentries
        loop=xrange(0, numexistingentries)
        progresscur=0

        # reset cursor
        self.sendpbcommand(self.protocolclass.pbinitrequest(), self.protocolclass.pbinitresponse)
        for i in loop:
            ### Read current entry
            req=self.protocolclass.pbreadentryrequest()
            res=self.sendpbcommand(req, self.protocolclass.pbreadentryresponse)

            entry={ 'number':  res.entry.entrynumber, 'serial1':  res.entry.serial1, 'name': res.entry.name}

            self.log("Reading entry "+`i`+" - "+str(entry['serial1'])+" - "+entry['name'])
            existingpbook[i]=entry
            self.progress(progresscur, progressmax, "existing "+entry['name'])
            #### Advance to next entry
            req=self.protocolclass.pbnextentryrequest()
            res=self.sendpbcommand(req, self.protocolclass.pbnextentryresponse)
            progresscur+=1
        # we have now looped around back to begining

        # Find entries that have been deleted
        pbook=data['phonebook']
        dellist=[]
        for i in loop:
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
            self.log("Deleting entry "+`i`+" - "+str(ii['serial1'])+" - "+ii['name'])
            req=self.protocolclass.pbdeleteentryrequest()
            req.serial1=ii['serial1']
            req.serial2=ii['serial1']
            req.entrynumber=ii['number']
            self.sendpbcommand(req, self.protocolclass.pbdeleteentryresponse)
            self.progress(progresscur, progressmax, "Deleting "+ii['name'])
            # also remove them from existingpbook
            del existingpbook[i]

        # Now rewrite out existing entries
        self.log("Rewrite existing entries")
        keys=existingpbook.keys()
        existingserials=[]
        keys.sort()  # do in same order as existingpbook
        for i in keys:
            progresscur+=1
            ii=pbook[self._findserial(existingpbook[i]['serial1'], pbook)]
            self.log("Rewriting entry "+`i`+" - "+ii['name'])
            self.progress(progresscur, progressmax, "Rewriting "+ii['name'])
            entry=self.makeentry(existingpbook[i]['serial1'], ii, data)
            existingserials.append(existingpbook[i]['serial1'])
            req=self.protocolclass.pbupdateentryrequest()
            req.entry=entry
            res=self.sendpbcommand(req, self.protocolclass.pbupdateentryresponse)
            serialupdates.append( ( ii["bitpimserial"],
                                    {'sourcetype': self.serialsname,
                                     'serial1': res.serial1,
                                     'sourceuniqueid': data['uniqueserial']}))
            assert ii['serial1']==res.serial1 # serial should stay the same
            pb_entries[res.serial1]=entry

        # Finally write out new entries
        counter=0
        keys=pbook.keys()
        self.log("Write new entries")
        keys.sort()
        for i in keys:
            ii=pbook[i]
            if ii['serial1'] in existingserials:
                continue # already wrote this one out
            # find an unused serial number
            while True:
                if counter in existingserials:
                    counter+=1
                else:
                    break
            progresscur+=1
            entry=self.makeentry(counter, ii, data)
            self.log("Appending entry "+ii['name'])
            self.progress(progresscur, progressmax, "Writing "+ii['name'])
            req=self.protocolclass.pbappendentryrequest()
            req.entry=entry
            res=self.sendpbcommand(req, self.protocolclass.pbappendentryresponse)
            serialupdates.append( ( ii["bitpimserial"],
                                     {'sourcetype': self.serialsname,
                                      'serial1': res.newserial,
                                     'sourceuniqueid': data['uniqueserial']}))
            pb_entries[res.newserial]=entry
            counter+=1
        # update the media file
        data['serialupdates']=serialupdates

        changed=self.save_phonebook_media(pb_entries)
        if changed:
            data["rebootphone"]=True
        return data

#----- SMS  ---------------------------------------------------------------------------

    def _readsms(self):
        res={}
        # go through the sms directory looking for messages
        for item in self.listfiles("sms").values():
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
                sf.readfrombuffer(buf, logtitle="SMS inbox item")
                entry=self._getinboxmessage(sf)
                res[entry.id]=entry
            elif folder=='Sent':
                sf=self.protocolclass.sms_out()
                sf.readfrombuffer(buf, logtitle="SMS sent item")
                entry=self._getoutboxmessage(sf)
                res[entry.id]=entry
        return res 


    def _setquicktext(self, result):
        sf=self.protocolclass.sms_canned_file()
        quicktext=result.get('canned_msg', [])
        count=0
        for entry in quicktext:
            if count < self.protocolclass.SMS_CANNED_MAX_ITEMS:
                msg_entry=self.protocolclass.sms_quick_text()
                msg_entry.msg=entry['text'][:self.protocolclass.SMS_CANNED_MAX_LENGTH-1]
                sf.msgs.append(msg_entry)
                count+=1
            else:
                break
        if count!=0:
            # don't create the file if there are no entries 
            sf.num_active=count
            buf=prototypes.buffer()
            sf.writetobuffer(buf, logtitle="Writing quicktext")
            self.writefile(self.protocolclass.SMS_CANNED_FILENAME, buf.getvalue())
        return

    def _getquicktext(self):
        quicks=[]
        try:
            buf=prototypes.buffer(self.getfilecontents(self.protocolclass.SMS_CANNED_FILENAME))
            sf=self.protocolclass.sms_canned_file()
            sf.readfrombuffer(buf, logtitle="SMS quicktext file sms/canned_msg.dat")
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
#        if sf.priority==0:
#            entry.priority=sms.SMSEntry.Priority_Normal
#        else:
#            entry.priority=sms.SMSEntry.Priority_High
        entry.read=sf.read
        entry.text=sf.msg
        entry.callback=sf.callback
        return entry

    def _getoutboxmessage(self, sf):
        entry=sms.SMSEntry()
        if not sf.saved:
            entry.folder=entry.Folder_Sent
        else:
            entry.folder=entry.Folder_Saved
        entry.datetime="%d%02d%02dT%02d%02d00" % ((sf.timesent))
        # add all the recipients
        for r in sf.recipients:
            if r.number:
                confirmed=(r.status==2)
                confirmed_date=None
                if confirmed:
                    confirmed_date="%d%02d%02dT%02d%02d00" % r.time
                entry.add_recipient(r.number, confirmed, confirmed_date)
        entry.subject=sf.msg[:28]
        entry.text=sf.msg
#        if sf.priority==0:
#            entry.priority=sms.SMSEntry.Priority_Normal
#        else:
#            entry.priority=sms.SMSEntry.Priority_High
        entry.locked=sf.locked
        entry.callback=sf.callback
        return entry


#----- Media  -----------------------------------------------------------------------

    # this phone can take MP3 files, but you have to use the vnd.qcelp MIME type
    # this makes renaming the files (from the ##.dat format) back to a real
    # name difficult, we assume all vnd.qcelp files are mp3 files as this is the
    # most common format

    __mimetype={ 'mid': 'audio/midi', 'qcp': 'audio/vnd.qcelp', 'jar': 'application/java-archive',
                 'jpg': 'image/jpg', 'jpeg': 'image/jpeg', 'gif': 'image/gif', 
                 'bmp': 'image/bmp', 'png': 'image/png', 'mp3': 'audio/vnd.qcelp'}

    __reverse_mimetype={ 'audio/midi': 'mid', 'audio/vnd.qcelp': 'mp3', 'application/java-archive': 'jar',
                 'image/jpg': 'jpg', 'image/jpeg': 'jpeg', 'image/gif': 'gif', 
                 'image/bmp': 'bmp', 'image/png': 'png', 'audio/mp3': 'mp3'}

    __app_extensions={ 'jar':'' }


    def getwallpaperindices(self, results):
        return self.getmediaindex(self.builtinimages, self.imagelocations, results, 'wallpaper-index')

    def getringtoneindices(self, results):
        return self.getmediaindex(self.builtinringtones, self.ringtonelocations, results, 'ringtone-index')

    def getwallpapers(self, result):
        return self.getmedia(self.imagelocations, result, 'wallpapers')

    def getringtones(self, result):
        return self.getmedia(self.ringtonelocations, result, 'ringtone')

    def savewallpapers(self, results, merge):
        return self.savemedia('wallpapers', 'wallpaper-index', results, merge, self.getwallpaperindices)

    def saveringtones(self, results, merge):
        return self.savemedia('ringtone', 'ringtone-index', results, merge, self.getringtoneindices)

    def getindex(self, indexfile):
        "Read an index file"
        index={}
        try:
            buf=prototypes.buffer(self.getfilecontents(indexfile))
        except com_brew.BrewNoSuchFileException:
            # file may not exist
            return index
        g=self.protocolclass.indexfile()
        g.readfrombuffer(buf, logtitle="Read indexfile "+indexfile)
        for i in g.items:
            if i.index!=0xffff and len(i.name):
                index[i.index]=i.name
        return index

    def get_content_file(self, key):
        index={}
        if key=='ringtone' or key=='ringtone-index':
            type='Ringers'
            index_const=self.protocolclass.ringerconst*0x100
            indexfile=self.getindex(self.protocolclass.ringerindex)
        else:
            type='Screen Savers'
            index_const=self.protocolclass.imageconst*0x100
            indexfile=self.getindex(self.protocolclass.imageindex)
        try:
            buf=prototypes.buffer(self.getfilecontents(self.protocolclass.content_file_name))
            g=self.protocolclass.content_file()
            g.readfrombuffer(buf, logtitle="Content file "+self.protocolclass.content_file_name)
            for i in g.items:
                if i.type=='!C' and i.content_type==type:
                    try:
                        # construct a user friendly filename
                        ext=self.__reverse_mimetype[i.mime_type]
                        # find the "file" in the index file and get it's index
                        # if the index was created by bitpim it will be the same 
                        # as the unfriendly filename, but this is not guarenteed
                        found=False
                        for j in indexfile.keys():
                            # convert to int to strip leading zero
                            try:
                                if int(common.stripext(indexfile[j]))==int(i.index1):
                                    index[j + index_const]=i.name1+'.'+ext
                                    found=True
                                    break;
                            except:
                                pass
                        if not found:
                            self.log("Unable to find index entry for "+i.name1+". Index : "+`i.index1`)
                    except:
                        pass
        except com_brew.BrewNoSuchFileException:
            pass
        return index, indexfile, index_const

    def getmedia(self, maps, result, key):
        """Returns the contents of media as a dict where the key is a name as returned
        by getindex, and the value is the contents of the media"""
        media={}
        # first read the maps
        type=None
        for offset,indexfile,location,type,maxentries,const in maps:
            index=self.getindex(indexfile)
            for i in index:
                try:
                    media[index[i]]=self.getfilecontents(location+"/"+index[i], True)
                except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException,com_brew.BrewNameTooLongException):
                    self.log("It was in the index, but not on the filesystem")
                    
        # secondly read the content file
        index, indexfile, index_const=self.get_content_file(key)
        for i in index:
            try:
                buf=prototypes.buffer(self.getfilecontents(self.protocolclass.media_directory+'/'+indexfile[i-index_const], True))
                _fname=index[i]
                # This would be nice but this will read the entire file which will slow the media retrieval down
#                ext=common.getext(_fname)
#                if ext=='mp3':
#                    # see if it is really an mp3, we will need to rename it
#                    try:
#                        qcp_header=self.protocolclass.qcp_media_header()
#                        qcp_header.readfrombuffer(buf, logtitle="qcp header")
#                    except: # exception will be thrown if header does not match
#                        _fname=common.stripext(index[i])+'.'+'qcp'
                media[_fname]=buf.getdata()
            except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException,com_brew.BrewNameTooLongException):
                self.log("It was in the index, but not on the filesystem")
        self.log("Contents not in the filesystem")

        result[key]=media
        return result

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
            media[c]={'name': name, 'origin': 'builtin' }
            c+=1

        # the maps
        type=None
        for offset,indexfile,location,type,maxentries,const in maps:
            index=self.getindex(indexfile)
            for i in index:
                media[i+offset]={'name': index[i], 'origin': type}

        # secondly read the content file
        if key=='ringtone-index':
            type='ringers'
        else:
            type='images'
        index,_,_=self.get_content_file(key)
        for i in index:
            media[i]={'name': index[i], 'origin': type}
        results[key]=media
        return media

    def savemedia(self, mediakey, mediaindexkey, results, merge, reindexfunction):
        """Actually saves out the media

        @param mediakey: key of the media (eg 'wallpapers' or 'ringtones')
        @param mediaindexkey:  index key (eg 'wallpaper-index')
        @param maps: list index files and locations
        @param results: results dict
        @param merge: are we merging or overwriting what is there?
        @param reindexfunction: the media is re-indexed at the end.  this function is called to do it
        """
        content_changed=False
        media=results[mediakey].copy()


        #figure out if the origin we are interested in
        if mediaindexkey=='ringtone-index':
            type='ringers'
            content_type="Ringers"
            indexfile=self.protocolclass.ringerindex
            index_const=self.protocolclass.ringerconst
            max_media_entries=self.protocolclass.max_ringers
          # remove voice_memos
            for i in media.keys():
                try:
                    if media[i]['origin']=='voice_memo':
                        del media[i]
                except:
                    pass
        else:
            type='images'
            content_type="Screen Savers"
            indexfile=self.protocolclass.imageindex
            index_const=self.protocolclass.imageconst
            max_media_entries=self.protocolclass.max_images
            # remove camera images
            for i in media.keys():
                try:
                    if media[i]['origin']=='camera':
                        del media[i]
                except:
                    pass

        #read content file off the phone
        content={}
        try:
            buf=prototypes.buffer(self.getfilecontents(self.protocolclass.content_file_name))
            g=self.protocolclass.content_file()
            g.readfrombuffer(buf, logtitle="Read content file")
            for i in g.items:
                # type !C always appears first
                if i.type=='!C':
                    content[int(i.index1)]= {'C': i}
                elif i.type=='!E':
                    content[int(i.index2)]['E']=i
        except (com_brew.BrewNoSuchFileException,com_brew.BrewBadPathnameException,com_brew.BrewNameTooLongException):
            pass
        # get a list of files in the media directory so we can figure out what to delete
        # and what needs to be copied onto the phone
        dirlisting=self.getfilesystem(self.protocolclass.media_directory)
        # strip path from directory listing
        for i in dirlisting.keys():
            dirlisting[i[len(self.protocolclass.media_directory)+1:]]=dirlisting[i]
            del dirlisting[i]

        # build up list of existing media items into init, remove missing items from content list
        init={}
        for k in content.keys():
            if content[k]['C'].content_type==content_type:
                index=k
                name=content[k]['C'].name1
                size=int(content[k]['C'].size)
                data=None
                # find the media content file, check that the size matches
                for w in media:
                    if common.stripext(media[w]['name'])==name and media[w]['data']!=None:
                        size_fix=((3024+len(media[w]['data']))/1008)*1008
                        if size_fix==size:
                            data=media[w]['data']
                            del media[w]
                            break
                # remove unused entries from index and filesystem
                if not merge and data is None:
                    # delete the entry
                    del content[k]
                    content_changed=True
                    # we have to remove the data file, the gcd file and the url file
                    _fname='%02d.dat' % k
                    if _fname in dirlisting:
                        self.rmfile(self.protocolclass.media_directory+'/'+_fname)
                        del dirlisting[_fname]
                    gcdname='%02d.gcd' % k
                    if gcdname in dirlisting:
                        self.rmfile(self.protocolclass.media_directory+'/'+gcdname)
                        del dirlisting[gcdname]
                    urlname='%02d.url' % k
                    if urlname in dirlisting:
                        self.rmfile(self.protocolclass.media_directory+'/'+urlname)
                        del dirlisting[urlname]
                    continue
                init[index]={'name': name, 'data': data}

        # go through adding new media not currently on the phone
        # assign these item keys in the content media
        applications={}
        for sp in range(100):
            if len(media.keys()) == 0:
                break
            if sp not in content:
                #found a hole
                for w in media.keys():
                    C,E,add_to_index=self.make_new_media_entry(media[w], sp, type)
                    if add_to_index=='index':
                        content[sp]= {'C': C, 'E': E}
                        init[sp]=media[w]
                        content_changed=True
                    elif add_to_index=='content':
                        content[sp]= {'C': C, 'E': E}
                        applications[sp]=media[w]
                        content_changed=True
                    else:
                        self.log("Unknown media type for "+`media[w]['name']`+". Not written to phone.")
                        sp-=1
                    del media[w]
                    break

        if len(media.keys()):
            self.log("Phone index full, some media not written to phone")

        # write out the new index, there are two files on this phone
        # the content file and the media index, kinda dumb having two copies
        # of the same thing
        # content_file
        content_count=0
        keys=content.keys()
        keys.sort()
        cfile=self.protocolclass.content_file()
        # add in the !C types first
        for k in keys:
            content_count+=1
            cfile.items.append(content[k]['C'])
        for k in keys:
            cfile.items.append(content[k]['E'])
        #terminator
        entry=self.protocolclass.content_entry()
        entry.type='!F'
        cfile.items.append(entry)
        buffer=prototypes.buffer()
        cfile.writetobuffer(buffer, logtitle="Updated content file "+self.protocolclass.content_file_name)
        self.writefile(self.protocolclass.content_file_name, buffer.getvalue())

        countfile=self.protocolclass.content_count()
        countfile.count=`content_count`            
        buffer=prototypes.buffer()
        countfile.writetobuffer(buffer, logtitle="Updated content count file "+self.protocolclass.content_count_file_name)
        self.writefile(self.protocolclass.content_count_file_name, buffer.getvalue())

        # now write out the index file (this is like the verizon LG phones)
        keys=init.keys()
        keys.sort()
        ifile=self.protocolclass.indexfile()
        ifile.numactiveitems=len(keys)
        for k in keys:
            entry=self.protocolclass.indexentry()
            entry.index=k
            entry.const=index_const
            entry.name='%02d.dat' % k
            ifile.items.append(entry)
        # fill the remainder of the entries with unused keys
        for k in range(max_media_entries):
            if k in keys:
                continue
            entry=self.protocolclass.indexentry()
            entry.index=k
            entry.const=index_const
            ifile.items.append(entry)
        buffer=prototypes.buffer()
        ifile.writetobuffer(buffer, logtitle="Updated index file "+indexfile)
        self.writefile(indexfile, buffer.getvalue())

        # Write out files - we compare against existing dir listing and don't rewrite if they
        # are the same size
        for k in keys:
            entry=init[k]
            data=entry.get("data", None)
            _fname='%02d.dat' % k
            gcdname='%02d.gcd' % k
            urlname='%02d.url' % k
            if data is None:
                if _fname not in dirlisting:
                    self.log("Index error.  I have no data for "+entry['name']+" and it isn't already in the filesystem")
                continue
            contentsize=len(data)
            urlcontents='file://'+entry['name']
            gcdcontents=self.makegcd(entry['name'],contentsize)
            if _fname in dirlisting and len(data)==dirlisting[_fname]['size']:
                self.log("Skipping writing %s/%s as there is already a file of the same length" % (self.protocolclass.media_directory,entry['name']))
                # repair gcd and url incase they are missing
                if gcdname not in dirlisting:
                    self.writefile(self.protocolclass.media_directory+"/"+gcdname, gcdcontents)
                if urlname not in dirlisting:
                    self.writefile(self.protocolclass.media_directory+"/"+urlname, urlcontents)
                continue
            self.writefile(self.protocolclass.media_directory+"/"+_fname, data)
            self.writefile(self.protocolclass.media_directory+"/"+gcdname, gcdcontents)
            self.writefile(self.protocolclass.media_directory+"/"+urlname, urlcontents)

        # write out applications
        for k in applications.keys():
            entry=applications[k]
            data=entry.get("data", None)
            _fname='%02d.jar' % k
            jadname='%02d.jad' % k
            urlname='%02d.url' % k
            if data is None:
                if _fname not in dirlisting:
                    self.log("Index error.  I have no data for "+entry['name']+" and it isn't already in the filesystem")
                print "here2"
                continue
            contentsize=len(data)
            urlcontents='file://'+entry['name']
            jadcontents=self.makejad(entry['name'],contentsize)
            print "here3"
            if _fname in dirlisting and len(data)==dirlisting[_fname]['size']:
                self.log("Skipping writing %s/%s as there is already a file of the same length" % (self.protocolclass.media_directory,entry['name']))
                # repair jad and url incase they are missing
                if jadname not in dirlisting:
                    self.writefile(self.protocolclass.media_directory+"/"+jadname, jadcontents)
                if urlname not in dirlisting:
                    self.writefile(self.protocolclass.media_directory+"/"+urlname, urlcontents)
                print "here4"
                continue
            print "here5"
            self.writefile(self.protocolclass.media_directory+"/"+_fname, data)
            self.writefile(self.protocolclass.media_directory+"/"+jadname, jadcontents)
            self.writefile(self.protocolclass.media_directory+"/"+urlname, urlcontents)

        del results[mediakey] # done with it
        reindexfunction(results)
        if content_changed:
            results["rebootphone"]=True
        return results
    
    def make_new_media_entry(self, entry, index, type):
        c=self.protocolclass.content_entry()
        e=self.protocolclass.content_entry()
        name=common.stripext(entry['name'])
        ext=common.getext(entry['name'])
        data=entry.get("data", None)
        add_to_index='index'
        c.type='!C'
        c.index1=index
        c.name1=name
        try:
            c.mime_type=self.__mimetype[ext]
        except:
            # bad file type
            add_to_index='none'
            return c, e, add_to_index
        if c.mime_type=='application/java-archive':
            c.content_type='Games'
            e.location_maybe='midlet:'+name
            add_to_index='content'
        elif type=='ringers':
            c.content_type='Ringers'
        else:
            c.content_type='Screen Savers'
        c.size=`((3024+len(data))/1008)*1008`
        e.type='!E'
        e.index2=index
        e.name2=name
        return c, e, add_to_index

    def makegcd(self,filename,size):
        "Build a GCD file for filename"
        ext=common.getext(filename.lower())
        noextname=common.stripext(filename)
        try:
            mimetype=self.__mimetype[ext]
            gcdcontent="Content-Type: "+mimetype+"\nContent-Name: "+noextname+"\nContent-Version: 1.0\nContent-Vendor: BitPim\nContent-URL: file://"+filename+"\nContent-Size: "+`size`+"\nContent-Description: Content for V10044 LG PM225"+"\n\n\n"
        except:
            gcdcontent="Content-Name: "+noextname+"\nContent-Version: 1.0\nContent-Vendor: BitPim\nContent-URL: file://"+filename+"\nContent-Size: "+`size`+"\n\n\n"
        return gcdcontent

    def makejad(self,filename,size):
        "Build a JAD file for filename"
        ext=common.getext(filename.lower())
        noextname=common.stripext(filename)
        jadcontent="MIDlet-1: "+noextname+", "+noextname+".png, BitPim\nMIDlet-Jar-Size: "+`size`+"\nMIDlet-Jar-URL: "+filename+"\nMIDlet-Name: "+noextname+"\nMIDlet-Vendor: Unknown\nMIDlet-Version: 1.0\nMicroEdition-Configuration: CLDC-1.0\nMicroEdition-Profile: MIDP-1.0\nContent-Folder: Games\n\n\n"
        return jadcontent

#----- Phone Detection -----------------------------------------------------------

    brew_version_file='ams/version.txt'
    brew_version_txt_key='ams_version.txt'
    my_model='PM225' 

    def getphoneinfo(self, phone_info):
        self.log('Getting Phone Info')
        try:
            s=self.getfilecontents('ams/version.txt')
            if s[:5]==self.my_model:
                phone_info.append('Model:', self.my_model)
                phone_info.append('ESN:', self.get_brew_esn())
                req=p_brew.firmwarerequest()
                #res=self.sendbrewcommand(req, self.protocolclass.firmwareresponse)
                #phone_info.append('Firmware Version:', res.firmware)
                txt=self.getfilecontents("nvm/nvm/nvm_0000")[207:217]
                phone_info.append('Phone Number:', txt)
        except:
            pass
        return


parentprofile=com_lgvx4400.Profile
class Profile(parentprofile):
    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    BP_Calendar_Version=3
    phone_manufacturer='LG Electronics Inc'
    phone_model='PM225'      # from Sprint
    brew_required=True
    RINGTONE_LIMITS= {
        'MAXSIZE': 250000
    }

    WALLPAPER_WIDTH=160
    WALLPAPER_HEIGHT=120
    MAX_WALLPAPER_BASENAME_LENGTH=30
    WALLPAPER_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .-_"
    WALLPAPER_CONVERT_FORMAT="jpg"
    
    MAX_RINGTONE_BASENAME_LENGTH=30
    RINGTONE_FILENAME_CHARS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .-_"
    DIALSTRING_CHARS="[^0-9PT#*]"

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 160, 'height': 120, 'format': "JPEG"}))
    # delay auto-detection when the phone is plugged in (in seconds)
    autodetect_delay=3

    def convertphonebooktophone(self, helper, data):
        """Converts the data to what will be used by the phone

        @param data: contains the dict returned by getfundamentals
                     as well as where the results go"""
        results={}

        speeds={}

        for pbentry in data['phonebook']:
            if len(results)==self.protocolclass.NUMPHONEBOOKENTRIES:
                break
            e={} # entry out
            entry=data['phonebook'][pbentry] # entry in
            try:
                # serials, can't use 0 as default as the phone uses this for the first entry
                serial1=helper.getserial(entry.get('serials', []), self.serialsname, data['uniqueserial'], 'serial1', 0xFFFFFFFF)

                e['serial1']=serial1
                for ss in entry["serials"]:
                    if ss["sourcetype"]=="bitpim":
                        e['bitpimserial']=ss
                assert e['bitpimserial']

                # name
                e['name']=helper.getfullname(entry.get('names', []),1,1,32)[0]

                # categories/groups
                cat=helper.makeone(helper.getcategory(entry.get('categories', []),0,1,32), None)
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
                emails=helper.getemails(entry.get('emails', []) ,0,self.protocolclass.NUMEMAILS,72)
                e['emails']=helper.filllist(emails, self.protocolclass.NUMEMAILS, "")

                # url
                e['url']=helper.makeone(helper.geturls(entry.get('urls', []), 0,1,74), "")

                # memo (-1 is to leave space for null terminator - not all software puts it in, but we do)
                e['memo']=helper.makeone(helper.getmemos(entry.get('memos', []), 0, 1, self.protocolclass.MEMOLENGTH-1), "")

                # phone numbers
                # there must be at least one email address or phonenumber
                minnumbers=1
                if len(emails): minnumbers=0
                numbers=helper.getnumbers(entry.get('numbers', []),minnumbers,self.protocolclass.NUMPHONENUMBERS)
                e['numberspeeds']=[]
                e['numbertypes']=[]
                e['numbers']=[]
                for numindex in range(len(numbers)):
                    num=numbers[numindex]
                    # deal with type
                    b4=len(e['numbertypes'])
                    type=num['type']
                    for i,t in enumerate(self.protocolclass.numbertypetab):
                        if type==t:
                            e['numbertypes'].append(i)
                            break
                        if t=='none': # conveniently last entry
                            e['numbertypes'].append(i)
                            break
                    if len(e['numbertypes'])==b4:
                        # we couldn't find a type for the number
                        helper.add_error_message("%s has number %s of type %s, the phone does not support this type" % 
                                                (e['name'], num['number'], num['type']))
                        continue
                    # deal with number
                    number=self.phonize(num['number'])
                    if len(number)==0:
                        # no actual digits in the number
                        continue
                    if len(number)>48: # get this number from somewhere sensible
                        # ::TODO:: number is too long and we have to either truncate it or ignore it?
                        number=number[:48] # truncate for moment
                    e['numbers'].append(number)
                    # deal with speed dial
                    sd=num.get("speeddial", 0xFF)
                    if sd>=self.protocolclass.FIRSTSPEEDDIAL and sd<=self.protocolclass.LASTSPEEDDIAL:
                        e['numberspeeds'].append(sd)
                    else:
                        e['numberspeeds'].append(0xFF)

                e['numberspeeds']=helper.filllist(e['numberspeeds'], 5, 0xFF)
                e['numbertypes']=helper.filllist(e['numbertypes'], 5, 0)
                e['numbers']=helper.filllist(e['numbers'], 5, "")

                # ringtones, wallpaper
                e['ringtone']=helper.getringtone(entry.get('ringtones', []), 'call', None)
                # e['msgringtone']=helper.getringtone(entry.get('ringtones', []), 'message', None)
                e['wallpaper']=helper.getwallpaper(entry.get('wallpapers', []), 'call', None)

                # flags
                e['secret']=helper.getflag(entry.get('flags',[]), 'secret', False)
                results[pbentry]=e

            except helper.ConversionFailed:
                continue

        data['phonebook']=results
        return data

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
        ('memo', 'read', None),        # all memo list reading
        ('sms', 'read', None),         # all SMS list reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'write', 'MERGE'),      # merge and overwrite wallpaper
        ('wallpaper', 'write', 'OVERWRITE'),
        ('ringtone', 'write', 'MERGE'),      # merge and overwrite ringtone
        ('ringtone', 'write', 'OVERWRITE'),
        ('memo', 'write', 'OVERWRITE'),       # all memo list writing
        ('sms', 'write', 'OVERWRITE'),        # all SMS list writing
        )

    def QueryAudio(self, origin, currentextension, afi):
        # we don't modify any of these
        if afi.format in ("MIDI", "QCP"):
            return currentextension, afi
        # examine mp3
        if afi.format=="MP3":
            if afi.channels==1 and 8<=afi.bitrate<=128 and 16000<=afi.samplerate<=44100:
                return currentextension, afi
        # convert it
        return ("mp3", fileinfo.AudioFileInfo(afi, **{'format': 'MP3', 'channels': 1, 'bitrate': 32, 'samplerate': 22050}))


    field_color_data={
        'phonebook': {
            'name': {
                'first': 0, 'middle': 0, 'last': 0, 'full': 1,
                'nickname': 0, 'details': 1 },
            'number': {
                'type': 5, 'speeddial': 5, 'number': 5, 'details': 5 },
            'email': 3,
            'address': {
                'type': 0, 'company': 0, 'street': 0, 'street2': 0,
                'city': 0, 'state': 0, 'postalcode': 0, 'country': 0,
                'details': 0 },
            'url': 1,
            'memo': 1,
            'category': 1,
            'wallpaper': 1,
            'ringtone': 1,
            'storage': 0,
            },
        'calendar': {
            'description': True, 'location': False, 'allday': True,
            'start': True, 'end': True, 'priority': False,
            'alarm': True, 'vibrate': False,
            'repeat': True,
            'memo': False,
            'category': False,
            'wallpaper': False,
            'ringtone': True,
            },
        'memo': {
            'subject': True,
            'date': False,
            'secret': False,
            'category': False,
            'memo': True,
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
