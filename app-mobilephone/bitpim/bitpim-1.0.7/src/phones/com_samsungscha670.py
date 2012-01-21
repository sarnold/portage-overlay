### BITPIM
###
### Copyright (C) 2004 Vic Heintz <vheintz@rochester.rr.com>
### Copyright (C) 2004 Joe Pham <djpham@netzero.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

### $Id: com_samsungscha670.py 4365 2007-08-17 21:11:59Z djpham $

### The bulk of this code was borrowed from com_samsungscha650.py
### and modified so that operations work with the sch-a670.

"""Communicate with a Samsung SCH-A670"""

# lib modules
import re
import sha
import time

# my modules
import common
import commport
import com_brew
import com_samsung
import com_phone
import conversions
import fileinfo
import nameparser
import p_samsungscha670
import prototypes


class Phone(com_samsung.Phone):
    "Talk to the Samsung SCH-A670 Cell Phone"

    desc="SCH-A670"
    serialsname='scha670'
    protocolclass=p_samsungscha670
    parent_phone=com_samsung.Phone

    __groups_range=xrange(5)
    __phone_entries_range=xrange(1,501)
    __pb_atpbokw_field_count=26		# This is a rename from __pb_max_entries in a650 code
					# which I found confusing
    __pb_max_speeddials=500
    __pb_entry=0
    __pb_mem_loc=1
    __pb_group=2
    __pb_ringtone=3
    __pb_name=4
    __pb_speed_dial=5
    __pb_home_num=7
    __pb_office_num=9
    __pb_mobile_num=11
    __pb_pager_num=13
    __pb_fax_num=15
    __pb_alias=17
    __pb_blanks=(19, 20)
    __pb_email=21
    __pb_image_assign=22		# 3, 4 or 5 depending on if picture ID assigned
    __pb_image_id=23			# when above is 4, has caller-id wallpaper id
    __pb_contact_image=24		# Path to "Picture ID" image
    __pb_date_time_stamp=25
    __pb_numbers= ({'home': __pb_home_num},
                    {'office': __pb_office_num},
                    {'cell': __pb_mobile_num},
                    {'pager': __pb_pager_num},
                    {'fax': __pb_fax_num})
    __pb_max_name_len=22
    __pb_max_number_len=32
    __pb_max_emails=1
    __pb_max_email_chars=48	# Not currently used, but shouldn't it be?
    __pb_max_alias_chars=48	# Not currently used, but shouldn't it be?
    __wp_photo_dir="digital_cam"
    __wp_header_bytes=96	# Extra bytes in front of jpg
    __wp_ts_offset=47 		# Timestamp in yyyymmddHHMMSS format starts here
    __wp_index_file = "nvm/nvm/brew_image"
    __rt_index_file = "nvm/nvm/brew_melody"
    __rt_dir = "brew/ringer"
    __wp_dir = "brew/shared"

    # The extra "User" entries are a temporary fix to allow round trip integrity of user
    # assigned ringtones for caller ID. Need to read /nvm/nvm/brew_melody to get true names
    # of ringtones.   
    builtinringtones=( 'Inactive',
                       'Bell 1', 'Bell 2', 'Bell 3', 'Bell 4', 'Bell 5',
                       'Melody 1', 'Melody 2', 'Melody 3', 'Melody 4', 'Melody 5',
                       'Melody 6', 'Melody 7', 'Melody 8', 'Melody 9', 'Melody 10', 	
		       'User 00', 'User 01', 'User 02', 'User 03', 'User 04', 'User 05',
		       'User 06', 'User 07', 'User 08', 'User 09', 'User 10', 'User 11',
		       'User 12', 'User 13', 'User 14', 'User 15', 'User 16', 'User 17',
		       'User 18', 'User 19')
    allringtones={}

    # 'type name', 'type index name', 'origin', 'dir path', 'max file name length', 'max file name count'
    __ringtone_info=('ringtone', 'ringtone-index', 'ringtone', 'brew/ringer', 19, 20)
    __wallpaper_info=('wallpapers', 'wallpaper-index', 'images', 'mms_image', 19, 10)
##    __wallpaper_info=('wallpapers', 'wallpaper-index', 'wallpapers', 'brew/shared', 19, 10)
    __camerapix_info=('wallpapers', 'wallpaper-index', 'camera', 'digital_cam', 19, 40)
    __video0_info=('wallpapers', 'wallpaper-index', 'video', 'camcoder0', None, None)
    __video1_info=('wallpapers', 'wallpaper-index', 'video', 'camcoder1', None, None)
       
    def __init__(self, logtarget, commport):

        "Calls all the constructors and sets initial modes"
        com_samsung.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE

    def getfundamentals(self, results):

        """Gets information fundamental to interoperating with the phone and UI.

        Currently this is:

          - 'uniqueserial'     a unique serial number representing the phone
          - 'groups'           the phonebook groups
          - 'wallpaper-index'  map index numbers to names
          - 'ringtone-index'   map index numbers to ringtone names

        This method is called before we read the phonebook data or before we
        write phonebook data.
        """
        
        self.setmode(self.MODEPHONEBOOK)

        # use a hash of ESN and other stuff (being paranoid)

        self.log("Retrieving fundamental phone information")
        self.log("Reading phone serial number")
        results['uniqueserial']=sha.new(self.get_esn()).hexdigest()

        # now read groups

        self.log("Reading group information")
        g=self.get_groups(self.__groups_range)
        groups={}
        for i, g_i in enumerate(g):
            if len(g_i):
                groups[i]={ 'name': g_i }
        results['groups']=groups

        # getting rintone-index
        self.setmode(self.MODEBREW)
        rt_index=RingtoneIndex(self)
        results['ringtone-index']=rt_index.get()
        
        # getting wallpaper-index
        img_index=ImageIndex(self)
        results['wallpaper-index']=img_index.get()
        
        self.setmode(self.MODEMODEM)
        self.log("Fundamentals retrieved")

        return results

    def get_builtin_ringtone_index(self):	# Joe's version
        r={}
        for k, n in enumerate(self.builtinringtones):
            r[k]={ 'name': n, 'origin': 'builtin' }
        return r

    def ATget_builtin_ringtone_index(self): 	# Vic's version using AT command
        r={}
	s=self.comm.sendatcommand("#PUGSN?")
	for rt in s[1:]:
	    this_r = rt.split(",")
	    r[int(this_r[0])] = { 'name': this_r[2], 'origin': 'builtin' }
	    self.allringtones[int(this_r[0])] = this_r[2]
	return r

    def get_user_rt_index(self, r):		# IDs on phone needed for caller-ID
	bi_cnt = len(r)
	rtlist = self.getfilecontents(self.__rt_index_file)
	offset=0
        while offset < (40 * 77):
	    rtid = ord(rtlist[offset+1])
	    rtlen = ord(rtlist[offset+74])
	    rtname = rtlist[offset+23:offset+23+rtlen][len(self.__rt_dir)+1:]
	    if rtlen > 0:
		r[rtid + bi_cnt] = { 'name': rtname, 'origin': 'ringtone' }
	    	self.allringtones[rtid + bi_cnt] = rtname
	    offset+=77
	return r

    def get_wallpaper_index(self):		# IDs on phone needed for caller-ID
	wpi = {}
	imglist = self.getfilecontents(self.__wp_index_file)
	offset=0
        while offset < (30 * 76):
	    imgid = ord(imglist[offset+1])
	    imglen = ord(imglist[offset+73])
	    imgname = imglist[offset+22:offset+22+imglen][len(self.__wp_dir)+1:]
	    if imglen > 0:
		wpi[imgid] = { 'name': imgname, 'origin': 'wallpaper' }	    
	    offset+=76
	return wpi

    def _get_phonebook(self, result, show_progress=True):
        """Reads the phonebook data.  The L{getfundamentals} information will
        already be in result."""

        self.setmode(self.MODEPHONEBOOK)
        c=len(self.__phone_entries_range)
        k=0
        pb_book={}
        for j in self.__phone_entries_range:
            # print "Getting entry: ", j
            pb_entry=self.get_phone_entry(j)
            if len(pb_entry)==self.__pb_atpbokw_field_count:
                pb_book[k]=self._extract_phone_entry(pb_entry, result)
                k+=1
                # print pb_book[k], i
                if show_progress:
                    self.progress(j, c, 'Reading '+pb_entry[self.__pb_name])
            else:
                if show_progress:
                    self.progress(j, c, 'Blank entry: %d' % j)
        self.setmode(self.MODEMODEM)

        return pb_book

    def getphonebook(self,result):
        """Reads the phonebook data.  The L{getfundamentals} information will
        already be in result."""
        pb_book=self._get_phonebook(result)
        result['phonebook']=pb_book
        return pb_book

    def _extract_phone_entry(self, entry, fundamentals):

        res={}
        # serials
        res['serials']=[ {'sourcetype': self.serialsname,
                          'sourceuniqueid': fundamentals['uniqueserial'],
                          'serial1': entry[self.__pb_entry],
                          'serial2': entry[self.__pb_mem_loc] }]
        # only one name
        res['names']=[ {'full': unicode(entry[self.__pb_name].replace('"', ''),
                                        errors='ignore') } ]
        if len(entry[self.__pb_alias]):
            res['urls']=[ {'url': entry[self.__pb_alias] } ]

        # only one category
        g=fundamentals['groups']
        i=int(entry[self.__pb_group])
        res['categories']=[ {'category': g[i]['name'] } ]

        # emails
        s=entry[self.__pb_email].replace('"', '')
        if len(s):
               res['emails']=[ { 'email': s } ]

        # urls
        # private
        # memos
        
        # wallpapers
        if entry[self.__pb_image_assign]=='3':
            # the image is 'Gallery' with the string 'digital_cam/Imagexxx'
            res['wallpapers']=[ { 'wallpaper': entry[self.__pb_contact_image].split( "/")[1]+".jpg",
                                  'use': 'call' } ]
        elif entry[self.__pb_image_assign]=='4':
            # the entry is an index into wallpaper-index
            wp_index=fundamentals.get('wallpaper-index', {})
            try:
                res['wallpapers']=[{ 'wallpaper': wp_index[int(entry[self.__pb_image_id])]['name'],
                                    'use': 'call'} ]
            except:
                pass
            
        # ringtones
        try:
            rt_index=fundamentals.get('ringtone-index', {})
            res['ringtones']=[ { 'ringtone': rt_index[int(entry[self.__pb_ringtone])]['name'],
                             'use': 'call' } ]
        except:
            res['ringtones']=[ { 'ringtone': self.builtinringtones[0],
                                'use': 'call' } ]


        # numbers
        speed_dial=int(entry[self.__pb_speed_dial])
        res['numbers']=[]
        for k, n in enumerate(self.__pb_numbers):
            for key in n:
                if len(entry[n[key]]):
                    if speed_dial==k:
                        res['numbers'].append({ 'number': entry[n[key]],
                                        'type': key,
                                        'speeddial': int(entry[self.__pb_mem_loc])})
                    else:
                        res['numbers'].append({ 'number': entry[n[key]],
                                        'type': key })	
	# done
        return res

    def savephonebook(self, data):
        "Saves out the phonebook"

        pb_book=data['phonebook']
        pb_groups=data['groups']
        ringtone_index=data.get('ringtone-index', {})
        self.log('Validating phonebook entries.')
        del_entries=[]
        for k in pb_book:
            if not self.__validate_entry(pb_book[k], pb_groups, ringtone_index):
                self.log('Invalid entry, entry will be not be sent.')
                del_entries.append(k)
        for k in del_entries:
            self.log('Deleting entry '+\
                     nameparser.getfullname(pb_book[k]['names'][0]))
            del pb_book[k]
        self._has_duplicate_speeddial(pb_book)
        self.log('All entries validated')

        pb_locs=[False]*(len(self.__phone_entries_range)+1)
        pb_mem=[False]*len(pb_locs)

        # get existing phonebook from the phone
        self.log("Getting current phonebook from the phone")
        current_pb=self._get_phonebook(data)
    
        # check and adjust for speeddial changes
        self.log("Processing speeddial data")
        for k in pb_book:
            self._update_speeddial(pb_book[k])

        # check for deleted entries and delete them
        self.setmode(self.MODEPHONEBOOK)
        self.log("Processing deleted entries")

        for k1 in current_pb:
            s1=current_pb[k1]['serials'][0]['serial1']
            found=False
            for k2 in pb_book:
                if self._same_serial1(s1, pb_book[k2]):
                    found=True
                    break
            if found:
                pb_locs[int(current_pb[k1]['serials'][0]['serial1'])]=True
                pb_mem[int(current_pb[k1]['serials'][0]['serial2'])]=True
            else:
                self.log("Deleted item: "+\
                         nameparser.getfullname(current_pb[k1]['names'][0]))
                # delete the entries from data and the phone
                self.progress(0, 10, "Deleting "+\
                              nameparser.getfullname(\
                                  current_pb[k1]['names'][0]))
                self._del_phone_entry(current_pb[k1])
        mem_idx, loc_idx = self.__pb_max_speeddials, 1
        
        # check for new entries & update serials
        self.log("Processing new & updated entries")
        serials_update=[]
        progresscur, progressmax=1,len(pb_book)
        for k in pb_book:
            if progresscur>len(self.__phone_entries_range):
                self.log('Max phone entries exceeded: '+str(progresscur))
                break
            e=pb_book[k]
            if not self._has_serial1(e):
                while pb_locs[loc_idx]:
                    loc_idx += 1
                pb_locs[loc_idx]=True
                sd=self._get_speeddial(e)
                if sd:
                    mem_index=sd
                    pb_mem[sd]=True
                else:
                    while pb_mem[mem_idx]:
                        mem_idx -= 1
                    pb_mem[mem_idx]=True
                    mem_index=mem_idx
                    self._set_speeddial(e, mem_idx)
                s1={ 'sourcetype': self.serialsname,
                          'sourceuniqueid': data['uniqueserial'],
                          'serial1': `loc_idx`,
                          'serial2': `mem_index` }
                e['serials'].append(s1)
                self.log("New entries: Name: "+\
                         nameparser.getfullname(e['names'][0])+", s1: "+`loc_idx`+", s2: "+`mem_index`)
                serials_update.append((self._bitpim_serials(e), s1))
            self.progress(progresscur, progressmax, "Updating "+\
                          nameparser.getfullname(e['names'][0]))
            if not self._write_phone_entry(e, data):
                self.log("Failed to save entry: "+\
                         nameparser.getfullname(e['names'][0]))
            progresscur += 1

        data["serialupdates"]=serials_update
        self.log("Done")
        self.setmode(self.MODEMODEM)
        return data

    # validate a phonebook entry, return True if good, False otherwise
    def __validate_entry(self, pb_entry, pb_groups, ringtone_index):
        try:
            # validate name
            name=nameparser.getfullname(pb_entry['names'][0]).replace('"', '')
            if len(name)>self.__pb_max_name_len:
                name=name[:self.__pb_max_name_len]
            pb_entry['names'][0].setdefault('full', name)
            # validate url/alias
            url=pb_entry.get('urls', [{}])[0].get('url', None)
            if url is not None:
                url=re.sub('[,"]', '', url)
                if len(url)>self.__pb_max_alias_chars:
                    url=url[:self.__pb_max_alias_chars]
                pb_entry['urls']=[ { 'url': url } ]
            # validate numbers
            has_number_or_email=False
            if pb_entry.has_key('numbers'):
                for n in pb_entry['numbers']:
                    num=self.phonize(n['number'])
                    if len(num)>self.__pb_max_number_len:
                        num=num[:self.__pb_max_number_len]
                    if num != n['number']:
                        self.log('Updating number from '+n['number']+' to '+num)
                        n['number']=num
                    try:
                        self._get_number_type(n['type'])
                    except:
                        self.log(n['number']+': setting type to home.')
                        n['type']='home'
                    has_number_or_email=True
            # validate emails
            if pb_entry.has_key('emails'):
                if len(pb_entry['emails'])>self.__pb_max_emails:
                    self.log(name+': Each entry can only have %s emails.  The rest will be ignored.'%str(self.__pb_max_emails))
                email=pb_entry['emails'][0]['email'].replace('"', '')
                if len(email)>self.__pb_max_email_chars:
                    email=email[:self.__pb_max_email_chars]
                if email!=pb_entry['emails'][0]['email']:
                    pb_entry['emails'][0]['email']=email
                has_number_or_email=True
            if not has_number_or_email:
                self.log(name+': Entry has no numbers or emails')
                # return False so this entry can be deleted from the dict
                return False
            # validate groups
            found=False
            if pb_entry.has_key('categories') and len(pb_entry['categories']):
                pb_cat=pb_entry['categories'][0]['category']
                for k in pb_groups:
                    if pb_groups[k]['name']==pb_cat:
                        found=True
                        break
            if not found:
                self.log(name+': category set to '+pb_groups[0]['name'])
                pb_entry['categories']=[{'category': pb_groups[0]['name']}]
            # validate ringtones
            found=False
            if pb_entry.has_key('ringtones') and len(pb_entry['ringtones']):
                pb_rt=pb_entry['ringtones'][0]['ringtone']
                for k, rt in ringtone_index.items():
                    if pb_rt==rt['name']:
                        found=True
                        break
            if not found:
                rt=ringtone_index[0]['name']
                self.log(name+': ringtone set to '+rt)
                pb_entry['ringtones']=[{'ringtone': rt,
                                        'use': 'call' }]
            # to to: validate wallpaper
                
            # everything's cool
            return True
        except:
            raise
        
    def _has_duplicate_speeddial(self, pb_book):
        b=[False]*(self.__pb_max_speeddials+1)
        for k in pb_book:
            try:
                for  k1, kk in enumerate(pb_book[k]['numbers']):
                    sd=kk['speeddial']
                    if sd and b[sd]:
                        # speed dial is in used, remove this one
                        del pb_book[k]['numbers'][k1]['speeddial']
                        self.log('speeddial %d exists, deleted'%sd)
                    else:
                        b[sd]=True
            except:
                pass
        return False

    def _update_speeddial(self, pb_entry):
        try:
            s=self._my_serials(pb_entry)
            s1=int(s['serial2'])
            sd=self._get_speeddial(pb_entry)
            if not sd:
                # speed dial not set, set it to current mem slot
                self._set_speeddial(pb_entry, s1)
            elif sd!=s1:
                # speed dial set to a different slot, mark it
                self._del_my_serials(pb_entry)
        except:
            pass

    def _get_speeddial(self, pb_entry):
        n=pb_entry.get('numbers', [])
        for k in n:
            try:
               if k['speeddial']:
                   return k['speeddial']
            except:
                pass
        return 0

    def _set_speeddial(self, pb_entry, sd):
        if not pb_entry.has_key('numbers'):
            # no numbers key, just return
            return
        for k in pb_entry['numbers']:
            if k.has_key('speeddial'):
                k['speeddial']=sd
                return
        pb_entry['numbers'][0]['speeddial']=sd

    def _del_phone_entry(self, pb_entry):
        try:
            return self.save_phone_entry(self._my_serials(pb_entry)['serial1'])
        except:
            return False

    def _same_serial1(self, s1, pb_entry):
        for k in pb_entry['serials']:
            if k['sourcetype']==self.serialsname and k.has_key('serial1'):
                return k['serial1']==s1
        return False

    def _has_serial1(self, pb_entry):
        for k in pb_entry['serials']:
            if k['sourcetype']==self.serialsname and k.has_key('serial1'):
                return True
        return False

    def _bitpim_serials(self, pb_entry):
        for k in pb_entry['serials']:
            if k['sourcetype']=="bitpim":
                return k
        return {}

    def _del_my_serials(self, pb_entry):
        for k in range(len(pb_entry['serials'])):
            if pb_entry['serials'][k]['sourcetype']==self.serialsname:
                del pb_entry['serials'][k]
                return

    def _my_serials(self, pb_entry):
        for k in pb_entry['serials']:
            if k['sourcetype']==self.serialsname:
                return k
        return {}

    def _get_number_type(self, type):
        n=self.__pb_numbers
        for k in range(len(n)):
            if n[k].has_key(type):
                return k, n[k][type]
        raise common.IntegrityCheckFailed(self.desc, "Invalid Number Type")

    def _write_phone_entry(self, pb_entry, data):

        # setting up a list to send to the phone, all fields preset to '0'
        e=['0']*self.__pb_atpbokw_field_count	

        # setting the entry # and memory location #
        serials=self._my_serials(pb_entry)
        e[self.__pb_entry]=serials['serial1']
        e[self.__pb_mem_loc]=serials['serial2']

        # groups/categories
        groups=data.get('groups', {})
        e[self.__pb_group]='0'
        try:
            grp_name=pb_entry['categories'][0]['category']
            for k, n in groups.items():
                if n.get('name', None)==grp_name:
                    e[self.__pb_group]=`k`
                    break
        except:
            pass

        # ringtones
        ringtone_index=data.get('ringtone-index', {})
        e[self.__pb_ringtone]='0'
        try:
            rt=pb_entry['ringtones'][0]['ringtone']
            for k, n in ringtone_index.items():
                if rt==n.get('name', None):
                    e[self.__pb_ringtone]=`k`
                    break
        except:
            pass

        # name & alias/url
        e[self.__pb_name]='"'+nameparser.getfullname(\
            pb_entry['names'][0])+'"'
	url=''
        try:
            url=pb_entry['urls'][0]['url']
        except:
            pass
        e[self.__pb_alias]=url
        if len(url):
            e[self.__pb_alias+1]='0'
        else:
            e[self.__pb_alias+1]=''

        # numbers & speed dial
        # preset to empty
        for k in range(len(self.__pb_numbers)):
            for kk in self.__pb_numbers[k]:
                e[self.__pb_numbers[k][kk]]=''
                e[self.__pb_numbers[k][kk]+1]=''
        speed_dial='0'
        n=pb_entry.get('numbers', [])
        for k in range(len(n)):
            try:
                nk=n[k]
                kkk, kk=self._get_number_type(nk['type'])
            except:
                # invalid type, default to 'home'
                nk['type']='home'
                kkk, kk=0, self.__pb_home_num
            e[kk],e[kk+1]=self.phonize(nk['number']),'0'
            try:
                if nk['speeddial']:
                    speed_dial=`kkk`
            except:
                pass
        e[self.__pb_speed_dial]=speed_dial

        # email
        email=''
        try:
            email=pb_entry['emails'][0]['email']
        except:
            pass
        e[self.__pb_email]='"'+email+'"'

	# wallpaper: phonebook entry "caller id" image
        # Default: No image assigned
        e[self.__pb_image_assign]='5'
        e[self.__pb_image_id]='0'
        e[self.__pb_contact_image]='""'
	try:
            imgName = pb_entry['wallpapers'][0]['wallpaper']
            image_index=data.get('wallpaper-index', {})
            for k, n in image_index.items():
                if imgName==n.get('name', None):
                    if k>self.protocolclass.max_image_entries:
                        # this is a 'Gallery' entry
                        e[self.__pb_image_assign]='3'
                        e[self.__pb_contact_image]='"'+self.__wp_photo_dir+'/'+imgName.split('.')[0]+'"'
                        e[self.__pb_image_id]='0'
                    else:
                        # 'My Image' entry
                        e[self.__pb_image_assign]='4'
                        e[self.__pb_image_id]=`k`
                        e[self.__pb_contact_image]='""'
                    break
	except:
            pass

        for k in self.__pb_blanks:
            e[k]=''

        e[self.__pb_date_time_stamp]=self.get_time_stamp()

        # final check to determine if this entry has changed.
        # if it has not then do nothing an just return
        ee=self.get_phone_entry(int(e[self.__pb_entry]))
        if len(ee)==self.__pb_atpbokw_field_count:
            # DSV took the " out, need to put them back in for comparison
            ee[self.__pb_name]='"'+ee[self.__pb_name]+'"'
            ee[self.__pb_email]='"'+ee[self.__pb_email]+'"'
            ee[self.__pb_contact_image]='"'+ee[self.__pb_contact_image]+'"'
            # exclude the timestamp field
            k=self.__pb_atpbokw_field_count-1
            if e[:k]==ee[:k]:
                return True
        return self.save_phone_entry('0,'+','.join(e))

    def getringtones(self, result):
        self.setmode(self.MODEBREW)
        m=FileEntries(self, self.__ringtone_info)
        rt_info=RingtoneIndex(self).get_download_info()
        r=m.get_media(result, rt_info)
        self.setmode(self.MODEMODEM)
        return r

    def saveringtones(self, result, merge):
        self.setmode(self.MODEBREW)
        m=FileEntries(self, self.__ringtone_info)
        result['rebootphone']=1 # So we end up back in AT mode
        r=m.save_media(result, RingtoneIndex(self).get_download_info())
        self.setmode(self.MODEMODEM)
        return r

    def getwallpapers(self, result):
        self.setmode(self.MODEBREW)
        m=FileEntries(self, self.__wallpaper_info)
        img_info=ImageIndex(self).get_download_info()
        m.get_media(result, img_info)
        FileEntries(self, self.__video0_info).get_video(result, 'Video001.avi')
        r=FileEntries(self, self.__video1_info).get_video(result, 'Video002.avi')
        self.setmode(self.MODEMODEM)
        return r

    def savewallpapers(self, result, merge):
        self.setmode(self.MODEBREW)
        m=FileEntries(self, self.__wallpaper_info)
        r=m.save_media(result, ImageIndex(self).get_download_info())
        result['rebootphone']=1
        self.setmode(self.MODEMODEM)
        return r

    getmemo=parent_phone._getmemo
    savememo=parent_phone._savememo

    gettodo=parent_phone._gettodo
    savetodo=parent_phone._savetodo
    
    getsms=parent_phone._getsms
    savesms=parent_phone._savesms

    getphoneinfo=parent_phone._getphoneinfo

    getmedia=None

class Profile(com_samsung.Profile):

    serialsname='scha670'

    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=128
    MAX_WALLPAPER_BASENAME_LENGTH=19
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_ ."
##    WALLPAPER_CONVERT_FORMAT="bmp"
    WALLPAPER_CONVERT_FORMAT="jpg"
    MAX_RINGTONE_BASENAME_LENGTH=19
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_ ."
    RINGTONE_LIMITS= {
        'MAXSIZE': 30000
    }
    # use for auto-detection
    phone_manufacturer='SAMSUNG ELECTRONICS'
    phone_model='SCH-A670/164'

    def __init__(self):
        com_samsung.Profile.__init__(self)

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('ringtone', 'read', None),   # all ringtone reading
        ('ringtone', 'write', 'OVERWRITE'),
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', 'OVERWRITE'),
        ('memo', 'read', None),     # all memo list reading DJP
        ('memo', 'write', 'OVERWRITE'),  # all memo list writing DJP
        ('todo', 'read', None),     # all todo list reading DJP
        ('todo', 'write', 'OVERWRITE'),  # all todo list writing DJP
        ('sms', 'read', None),     # all SMS list reading DJP
        )

    if __debug__:
        _supportedsyncs+=(('sms', 'write', 'OVERWRITE'),)

    def convertphonebooktophone(self, helper, data):
        return data
    
    __audio_ext={ 'MIDI': 'mid', 'PMD': 'pmd', 'QCP': 'pmd' }
    def QueryAudio(self, origin, currentextension, afi):
        # we don't modify any of these
        if afi.format in ("MIDI", "PMD", "QCP"):
            for k,n in self.RINGTONE_LIMITS.items():
                setattr(afi, k, n)
            return currentextension, afi
        d=self.RINGTONE_LIMITS.copy()
        d['format']='QCP'
        return ('pmd', fileinfo.AudioFileInfo(afi, **d))

    imageorigins={}
    imageorigins.update(common.getkv(com_samsung.Profile.stockimageorigins, "images"))
  
    imagetargets={}
    imagetargets.update(common.getkv(com_samsung.Profile.stockimagetargets, "wallpaper",
                                      {'width': 128, 'height': 128, 'format': "PNG"}))
    imagetargets.update(common.getkv(com_samsung.Profile.stockimagetargets, "fullscreen",
                                      {'width': 128, 'height': 160, 'format': "PNG"}))
    imagetargets.update(common.getkv(com_samsung.Profile.stockimagetargets, "pictureid",
                                      {'width': 96, 'height': 96, 'format': "JPEG"}))

    def GetImageOrigins(self):
        # Note: only return origins that you can write back to the phone
        return self.imageorigins

    def GetTargetsForImageOrigin(self, origin):
        # right now, supporting just 'images' origin
        if origin=='images':
            return self.imagetargets

class FileEntries:
    def __init__(self, phone, info):
        self.__phone=phone
        self.__file_type, self.__index_type, self.__origin, self.__path, self.__max_file_len, self.__max_file_count=info

    def get_media(self, result, download_info=None):
        self.__phone.log('Getting media for type '+self.__file_type)
        if download_info is None:
            return self.__get_media_by_dir(result)
        else:
            return self.__get_media_by_index(result, download_info)

    def __get_media_by_dir(self, result):
        media=result.get(self.__file_type, {})
        idx=result.get(self.__index_type, {})
        file_cnt, idx_k=0, len(idx)
        path_len=len(self.__path)+1
        try:
            file_list=self.__phone.listfiles(self.__path)
            for k in file_list:
                try:
                    index=k[path_len:]
                    # print k, index
                    media[index]=self.__phone.getfilecontents(k, True)
                    idx[idx_k]={ 'name': index, 'origin': self.__origin }
                    idx_k+=1
                    file_cnt += 1
                except:
                    self.__phone.log('Failed to read file '+k)
        except:
            self.__phone.log('Failed to read dir '+self.__path)
        result[self.__file_type]=media
        result[self.__index_type]=idx
        if file_cnt > self.__max_file_count:
            self.__phone.log('This phone only supports %d %s.  %d %s read, weird things may happen.' % \
                                (self.__max_file_count, self.__file_type,
                                 file_cnt, self.__file_type))
        return result

    def __get_media_by_index(self, result, rt_info):
        media=result.get(self.__file_type, {})
        media_index=result.get(self.__index_type, {})
        mms_img_path=self.__phone.protocolclass.mms_image_path
        mms_img_len=len(mms_img_path)
        for k, m in media_index.items():
            file_key=m.get('name', None)
            file_name=rt_info.get(file_key, None)
            if file_key is not None and file_name is not None:
                try :
                    contents=self.__phone.getfilecontents(file_name, True)
                    img_origin=m.get('origin', None)
                    if img_origin=='images':
                        if file_name[:mms_img_len]==mms_img_path:
                            # mms image file, skip the header
                            contents=contents[52:]
                    elif img_origin=='camera':
                        # Camera pix file, need to be touched up
                        # patch code to make it work right now, need to recode
                        m['date']=\
                        ( int(contents[47:51]), int(contents[51:53]),
                          int(contents[53:55]), int(contents[55:57]),
                          int(contents[57:59]))
                        contents=contents[96:]
                        if contents[-1]=='\xff':
                            contents+='\x00'
                    media[file_key]=contents
                except:
                    self.__phone.log('Failed to read file '+file_name)
                    if __debug__: raise
        result[self.__file_type]=media
        return result

    def get_video(self, result, video_file_name):
        if not conversions.helperavailable('bmp2avi'):
            # helper not available , just bail
            self.__phone.log('Helper bmp2avi not found, cannot retrieve '+\
                             video_file_name)
            return result
        self.__phone.log('Getting video file '+video_file_name)
        media=result.get(self.__file_type, {})
        idx=result.get(self.__index_type, {})
        tmp_avi_name=common.gettempfilename("avi")
        try:
            file_list=self.__phone.listfiles(self.__path)
        except com_brew.BrewNoSuchDirectoryException:
            file_list={}
        except:
            file_list={}
            if __debug__: raise

        if not len(file_list):
            # empty directory
            return result
        file_keys=file_list.keys()
        file_keys.sort();
        for k in file_keys:
            try:
                conversions.convertjpgtoavi(self.__phone.getfilecontents(k, True)[96:],
                                            tmp_avi_name)
            except:
                self.__phone.log('Failed to read video files')
                if __debug__: raise
        # got the avi file, now prep to send it back
        if len(idx):
            idx_k=max(idx.keys())+1
        else:
            idx_k=0
        media[video_file_name]=open(tmp_avi_name, 'rb').read()
        idx[idx_k]={ 'name': video_file_name, 'origin': 'video' }
        result[self.__file_type]=media
        result[self.__index_type]=idx
        try:
            os.remove(tmp_avi_name)
        except:
            pass
        return result
                
    __mms_max_file_name_len=35
    def __mms_header(self, img_name, img_type, img_data_len):
        if len(img_name)>=self.__mms_max_file_name_len:
            name=img_name[:self.__mms_max_file_name_len-1]
        else:
            name=img_name
        return str('\x06'+str(name)+\
                   '\x00'*(self.__mms_max_file_name_len-len(name))+\
                   common.LSBstr32(img_data_len)+chr(img_type)+\
                   '\x00'*11)
    def __mms_file_name(self):
        now = time.localtime(time.time())
        return '%02d%02d%02d%02d%02d%02d'%((now[0]%2000,)+now[1:6])
    def _to_mms_JPEG(self, img_name, img_data_len):
        return (self.__mms_file_name(),
                self.__mms_header(img_name, 0, img_data_len))
    def _to_mms_BMP(self, img_name, img_data_len):
        return (self.__mms_file_name(),
                self.__mms_header(img_name, 1, img_data_len))
    def _to_mms_PNG(self, img_name, img_data_len):
        return (self.__mms_file_name(),
                self.__mms_header(img_name, 2, img_data_len))
    def _to_mms_GIF(self, img_name, img_data_len):
        return (self.__mms_file_name(),
                self.__mms_header(img_name, 3, img_data_len))
       
    def save_media(self, result, dl_info):
        self.__phone.log('Saving media for type '+self.__file_type)
        media, idx=result[self.__file_type], result[self.__index_type]
        # check for files selected for deletion
        media_names=[media[k]['name'] for k in media]
        dl_info_keys=dl_info.keys()
        deleted_keys=[k for k in dl_info_keys if k not in media_names]
        new_keys=[k for k in media if media[k]['name'] not in dl_info_keys]
        # deleting files
        campix_file_path=self.__phone.protocolclass.cam_pix_file_path
        campix_file_len=len(campix_file_path)
        for k in deleted_keys:
            file_name=dl_info[k]
            if file_name[:campix_file_len]==campix_file_path:
                # campera pix, do nothing
                continue
            self.__phone.log('Deleting file: '+file_name)
            try:
                self.__phone.rmfile(file_name)
            except:
                self.__phone.log('Failed to delete file: '+file_name)
        # writing new files
        # make sure dir exists to write new files
        if len(new_keys):
            try:
                self.__phone.mkdirs(self.__path)
                # yet another hack
                self.__phone.mkdirs('brew/shared')
            except:
                pass
        file_count=0
        for k in new_keys:
            n=media[k]
            origin=n.get('origin', None)
            if origin is not None and origin != self.__origin:
                continue
            if len(n['name']) > self.__max_file_len:
                self.__phone.log('%s %s name is too long and not sent to phone'% \
                                 (self.__file_type, n['name']))
                continue
            file_count+=1
            if file_count>self.__max_file_count:
                # max # of files reached, bailing out
                self.__phone.log('This phone only supports %d %s.  Save operation stopped.'%\
                                    (self.__max_file_count, self.__file_type))
                break
            if self.__origin=='images':
                file_info=fileinfo.identify_imagestring(n['data'])
                if file_info.format in ('JPEG', 'GIF', 'BMP'):
                    # jpeg/gif/bmp file/picture ID files
                    (mms_file_name, file_hdr)=\
                                    getattr(self, '_to_mms_'+file_info.format)(
                                        n['name'], len(n['data']))
                    file_name=self.__path+'/'+mms_file_name
                    file_contents=file_hdr+n['data']
                elif file_info.format=='PNG':
                    # wallpaper files
                    file_name='brew/shared/'+n['name']
                    # try to optimize png image files
                    file_contents=conversions.convertto8bitpng_joe(n['data'])
                else:
                    # unknown file type, skip it
                    continue
            else:
                file_name=self.__path+'/'+n['name']
                file_contents=n['data']
            self.__phone.log('Writing file: '+file_name)
            try:
                self.__phone.writefile(file_name, file_contents)
            except:
                self.__phone.log('Failed to write file: '+file_name)
            media[k]['origin']=self.__origin

        return result

class RingtoneIndex:
    __builtin_ringtones=( 'Inactive',
                       'Bell 1', 'Bell 2', 'Bell 3', 'Bell 4', 'Bell 5',
                       'Melody 1', 'Melody 2', 'Melody 3', 'Melody 4', 'Melody 5',
                       'Melody 6', 'Melody 7', 'Melody 8', 'Melody 9', 'Melody 10')

    def __init__(self, phone):
        self.__phone=phone

    def get_builtin_index(self):
        r={}
        for k, n in enumerate(self.__builtin_ringtones):
            r[k]={ 'name': n, 'origin': 'builtin' }
        return r

    def get_download_index(self):
        r={}
        try:
            rt_idx=self.__phone.protocolclass.ringtones()
            buf=prototypes.buffer(self.__phone.getfilecontents( \
                self.__phone.protocolclass.ringtone_index_file_name))
            rt_idx.readfrombuffer(buf, logtitle="Read ringtone download index")
            idx=len(self.__builtin_ringtones)
            l=len(self.__phone.protocolclass.ringtone_file_path)+1
            for i in range(self.__phone.protocolclass.max_ringtone_entries):
                e=rt_idx.entry[i]
                if e.name_len:
                    r[idx+i]={ 'name': e.file_name[l:e.file_name_len],
                               'origin': 'ringtone' }
        except:
            pass
        return r

    def get(self):
        r=self.get_builtin_index()
        r.update(self.get_download_index())
        return r

    def get_download_info(self):
        r={}
        try:
            rt_idx=self.__phone.protocolclass.ringtones()
            buf=prototypes.buffer(self.__phone.getfilecontents( \
                self.__phone.protocolclass.ringtone_index_file_name))
            rt_idx.readfrombuffer(buf, logtitle="Read ringtone download index")
            l=len(self.__phone.protocolclass.ringtone_file_path)+1
            for i in range(self.__phone.protocolclass.max_ringtone_entries):
                e=rt_idx.entry[i]
                if e.name_len:
                    r[e.file_name[l:e.file_name_len]]=e.file_name[:e.file_name_len]
        except:
            pass
        return r

class ImageIndex:

    def __init__(self, phone):
        self.__phone=phone

    def get_download_index(self):
        r={}
        try:
            # first, read 'My Image' index
            img_idx=self.__phone.protocolclass.images()
            buf=prototypes.buffer(self.__phone.getfilecontents( \
                self.__phone.protocolclass.image_index_file_name))
            img_idx.readfrombuffer(buf, logtitle="Read image download index")
            l=len(self.__phone.protocolclass.image_file_path)+1
            mms_img_path=self.__phone.protocolclass.mms_image_path
            mms_img_len=len(mms_img_path)
            for i in range(self.__phone.protocolclass.max_image_entries):
                e=img_idx.entry[i]
                if e.name_len and e.file_name_len:
                    if e.file_name[:mms_img_len]==mms_img_path:
                        # this is an mms_image file
                        idx_name=e.name[:e.name_len]
                    else:
                        # other image files
                        idx_name=e.file_name[l:e.file_name_len]
                    r[i]={ 'name': idx_name,
                           'origin': 'images' }
            # then read the camera pix image index ('Gallery')
            # starting index should be max_image_entries+1
            idx=self.__phone.protocolclass.max_image_entries+1
            try:
                dir_l=self.__phone.listfiles(\
                    self.__phone.protocolclass.cam_pix_file_path)
            except com_brew.BrewNoSuchDirectoryException:
                dir_l={}
            l=len(self.__phone.protocolclass.cam_pix_file_path)+1
            for f in dir_l:
                r[idx]={ 'name': f[l:]+'.jpg', 'origin': 'camera' }
                idx += 1
        except:
            raise
        return r

    def get(self):
        return self.get_download_index()

    def get_download_info(self):
        r={}
        try:
            # first, 'My Image' entries
            img_idx=self.__phone.protocolclass.images()
            buf=prototypes.buffer(self.__phone.getfilecontents( \
                self.__phone.protocolclass.image_index_file_name))
            img_idx.readfrombuffer(buf, logtitle="Read image download index")
            l=len(self.__phone.protocolclass.image_file_path)+1
            mms_img_path=self.__phone.protocolclass.mms_image_path
            mms_img_len=len(mms_img_path)
            for i in range(self.__phone.protocolclass.max_image_entries):
                e=img_idx.entry[i]
                if e.name_len and e.file_name_len:
                    if e.file_name[:mms_img_len]==mms_img_path:
                        idx_name=e.name[:e.name_len]
                    else:
                        idx_name=e.file_name[l:e.file_name_len]
                    r[idx_name]=e.file_name[:e.file_name_len]
            # then 'Gallery' entries
            try:
                dir_l=self.__phone.listfiles(\
                    self.__phone.protocolclass.cam_pix_file_path)
            except com_brew.BrewNoSuchDirectoryException:
                dir_l={}
            l=len(self.__phone.protocolclass.cam_pix_file_path)+1
            for f in dir_l:
                r[f[l:]+'.jpg']=f
        except:
            pass
        return r
