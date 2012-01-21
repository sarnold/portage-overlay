### BITPIM
###
### Copyright (C) 2004 Joe Pham <djpham@netzero.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_samsungscha650.py 4365 2007-08-17 21:11:59Z djpham $


"""Communicate with a Samsung SCH-A650"""

# lib modules
import copy
import re
import sha

# my modules

import common
import commport
import com_brew
import com_samsung
import com_phone
import conversions
import fileinfo
import memo
import nameparser
import p_samsungscha650
import prototypes

import call_history

#-------------------------------------------------------------------------------
class Phone(com_samsung.Phone):

    "Talk to the Samsung SCH-A650 Cell Phone"

    desc="SCH-A650"
    serialsname='scha650'
    protocolclass=p_samsungscha650
    parent_phone=com_samsung.Phone

    __groups_range=xrange(5)
    __phone_entries_range=xrange(1,501)
    __pb_max_entries=25
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
    __pb_email=21
    __pb_four=22
    __pb_blanks=(19, 20)
    __pb_date_time_stamp=24
    __pb_numbers= ({'home': __pb_home_num},
                    {'office': __pb_office_num},
                    {'cell': __pb_mobile_num},
                    {'pager': __pb_pager_num},
                    {'fax': __pb_fax_num})
    __pb_max_name_len=22
    __pb_max_number_len=32
    __pb_max_emails=1

    # 'type name', 'type index name', 'origin', 'dir path', 'max file name length', 'max file name count'    
    __ringtone_info=('ringtone', 'ringtone-index', 'ringtone', 'user/sound/ringer', 17, 20)
    __wallpaper_info=('wallpapers', 'wallpaper-index', 'images', 'nvm/brew/shared', 17, 10)
        
    def __init__(self, logtarget, commport):

        "Calls all the constructors and sets initial modes"
        com_samsung.Phone.__init__(self, logtarget, commport)
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

    def getphonebook(self,result):
        """Reads the phonebook data.  The L{getfundamentals} information will
        already be in result."""
        self.setmode(self.MODEBREW)
        pb=PhoneBook(self)
        pb.read()
        pb_book=pb.get_dict(result)
        result['phonebook']=pb_book
        self.setmode(self.MODEMODEM)
        return pb_book

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
        self.setmode(self.MODEBREW)
        phone_book=PhoneBook(self)
        phone_book.read()
        current_pb=phone_book.get_dict(data)
        self.setmode(self.MODEMODEM)
    
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
                         nameparser.getfullname(e['names'][0])+\
                         ", s1: "+`loc_idx`+", s2: "+`mem_index`)
                serials_update.append((self._bitpim_serials(e), s1))
            self.progress(progresscur, progressmax, "Updating "+\
                          nameparser.getfullname(e['names'][0]))
            if not self._write_phone_entry(e, pb_groups, ringtone_index,
                                           phone_book):
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
            # validate name & alias
            name=nameparser.getfullname(pb_entry['names'][0]).replace('"', '')
            if len(name)>self.__pb_max_name_len:
                name=name[:self.__pb_max_name_len]
            pb_entry['names'][0].setdefault('full', name)
            if pb_entry['names'][0].has_key('nickname'):
                name=re.sub('[,"]', '', pb_entry['names'][0]['nickname'])
                if len(name)>self.__pb_max_name_len:
                    name=name[:self.__pb_max_name_len]
                if pb_entry['names'][0]['nickname']!=name:
                    pb_entry['names'][0]['nickname']=name
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
                if len(email)>self.__pb_max_number_len:
                    email=email[:self.__pb_max_number_len]
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
                # can only set to builtin-ringtone
                for k, rt in ringtone_index.items():
                    if pb_rt==rt['name']:
                        found=True
                        break
            if not found:
                rt=ringtone_index[0]['name']
                self.log(name+': ringtone set to '+rt)
                pb_entry['ringtones']=[{'ringtone': rt,
                                        'use': 'call' }]
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


    def _write_phone_entry(self, pb_entry, groups, ringtone_index, phone_book):

        # setting up a list to send to the phone, all fields preset to '0'
        e=['0']*self.__pb_max_entries

        # setting the entry # and memory location #
        serials=self._my_serials(pb_entry)
        e[self.__pb_entry]=serials['serial1']
        e[self.__pb_mem_loc]=serials['serial2']

        # groups/categories
        grp=0
        try:
            grp_name=pb_entry['categories'][0]['category']
            for k in range(len(groups)):
                if groups[k]['name']==grp_name:
                    grp=k
                    break

        except:
            # invalid group or no group specified, default to group 0
            grp, pb_entry['categories']=0, [{'category': groups[0]['name']}]
        e[self.__pb_group]=`grp`

        # ringtones
        e[self.__pb_ringtone]='0'   # default to Inactive
        try:
            rt=pb_entry['ringtones'][0]['ringtone']
            for k, n in ringtone_index.items():
                if rt==n['name']:
                    e[self.__pb_ringtone]=`k`
                    break
        except:
            pass

        # name & alias
        e[self.__pb_name]='"'+nameparser.getfullname(pb_entry['names'][0])+'"'
        nick_name=''
        try:
            nick_name=pb_entry['names'][0]['nickname']
        except:
            pass

        e[self.__pb_alias]=nick_name
        if len(nick_name):
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
        e[self.__pb_four]='4'
        for k in self.__pb_blanks:
            e[k]=''

        e[self.__pb_date_time_stamp]=self.get_time_stamp()

        # final check to determine if this entry has changed.
        # if it has not then do nothing and just return
        ee=self.get_phone_entry(int(e[self.__pb_entry]),
                                self.__pb_alias, self.__pb_max_entries)
        if len(ee)==self.__pb_max_entries:
            # DSV took the " out, need to put them back in for comparison
            ee[self.__pb_name]='"'+ee[self.__pb_name]+'"'
            ee[self.__pb_email]='"'+ee[self.__pb_email]+'"'
            # set the correct ringtone index
            ee[self.__pb_ringtone]=str(phone_book.get_ringtone(\
                int(e[self.__pb_mem_loc])))
            k=self.__pb_max_entries-2
            if e[0:k]==ee[0:k]:
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
        r=m.get_media(result, img_info)
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

#-------------------------------------------------------------------------------
class Profile(com_samsung.Profile):

    serialsname='scha650'

    WALLPAPER_WIDTH=128
    WALLPAPER_HEIGHT=160
    MAX_WALLPAPER_BASENAME_LENGTH=17
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_*[]=<>;|?:% ."
    WALLPAPER_CONVERT_FORMAT="png"
   
    MAX_RINGTONE_BASENAME_LENGTH=17
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789_*[]=<>;|?:% ."
    RINGTONE_LIMITS= {
        'MAXSIZE': 30000
    }
    # use for auto-detection
    phone_manufacturer='SAMSUNG ELECTRONICS'
    phone_model='SCH-A650/163'
    
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

    __audio_ext={ 'MIDI': 'mid', 'QCP': 'qcp', 'PMD': 'pmd' }
    def QueryAudio(self, origin, currentextension, afi):
        # we don't modify any of these
        if afi.format in ("MIDI", "QCP", "PMD"):
            for k,n in self.RINGTONE_LIMITS.items():
                setattr(afi, k, n)
            return currentextension, afi
        d=self.RINGTONE_LIMITS.copy()
        d['format']='QCP'
        return ('qcp', fileinfo.AudioFileInfo(afi, **d))

    # fill in your own image origins using these
    # use this temorarily until the stock one is finalized
    imageorigins={}
    imageorigins.update(common.getkv(com_samsung.Profile.stockimageorigins, "images"))
  
    imagetargets={}
    imagetargets.update(common.getkv(com_samsung.Profile.stockimagetargets, "wallpaper",
                                      {'width': 128, 'height': 128, 'format': "PNG"}))
    imagetargets.update(common.getkv(com_samsung.Profile.stockimagetargets, "fullscreen",
                                      {'width': 128, 'height': 160, 'format': "PNG"}))
    
    def GetImageOrigins(self):
        # Note: only return origins that you can write back to the phone
        return self.imageorigins

    def GetTargetsForImageOrigin(self, origin):
        if origin=='images':
            return self.imagetargets

#-------------------------------------------------------------------------------
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
            file_list=self.__phone.getfilesystem(self.__path, 0)
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
        for k, m in media_index.items():
            file_key=m.get('name', None)
            file_name=rt_info.get(file_key, None)
            if file_key is not None and file_name is not None:
                try :
                    media[file_key]=self.__phone.getfilecontents(file_name, True)
                except:
                    self.__phone.log('Failed to read file '+file_name)
        result[self.__file_type]=media
        return result

    def save_media(self, result, dl_info):
        self.__phone.log('Saving media for type '+self.__file_type)
        media, idx=result[self.__file_type], result[self.__index_type]
        # check for files selected for deletion
        media_names=[media[k]['name'] for k in media]
        dl_info_keys=dl_info.keys()
        deleted_keys=[k for k in dl_info_keys if k not in media_names]
        new_keys=[k for k in media if media[k]['name'] not in dl_info_keys]
        # deleting files
        for k in deleted_keys:
            file_name=dl_info[k]
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
            file_name=self.__path+'/'+n['name']
            if self.__origin=='images':
                # try to optimize it if it's a png image file
                file_contents=conversions.convertto8bitpng_joe(n['data'])
            else:
                file_contents=n['data']
            self.__phone.log('Writing file: '+file_name)
            try:
                self.__phone.writefile(file_name, file_contents)
            except:
                self.__phone.log('Failed to write file: '+file_name)
            media[k]['origin']=self.__origin

        return result

#-------------------------------------------------------------------------------
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
            rt_idx.readfrombuffer(buf, logtitle="Read ringtone index file")
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

#-------------------------------------------------------------------------------
class ImageIndex:
    __builtin_images=( 'Clock1', 'Dual Clock', 'Calendar', 'Aquarium',
                      'Landscape', 'Water Drop' )

    def __init__(self, phone):
        self.__phone=phone

    def get_builtin_index(self):
        r={}
        for k, n in enumerate(self.__builtin_images):
            r[k]={ 'name': n, 'origin': 'builtin' }
        return r

    def get_download_index(self):
        r={}
        try:
            img_idx=self.__phone.protocolclass.images()
            buf=prototypes.buffer(self.__phone.getfilecontents( \
                self.__phone.protocolclass.image_index_file_name))
            img_idx.readfrombuffer(buf, logtitle="Read image download index")
            idx=len(self.__builtin_images)
            l=len(self.__phone.protocolclass.image_file_path)+1
            for i in range(self.__phone.protocolclass.max_image_entries):
                e=img_idx.entry[i]
                if e.name_len:
                    r[idx+i]={ 'name': e.file_name[l:e.file_name_len],
                               'origin': 'images' }
        except:
            raise
        return r

    def get(self):
        r=self.get_builtin_index()
        r.update(self.get_download_index())
        return r

    def get_download_info(self):
        r={}
        try:
            img_idx=self.__phone.protocolclass.images()
            buf=prototypes.buffer(self.__phone.getfilecontents( \
                self.__phone.protocolclass.image_index_file_name))
            img_idx.readfrombuffer(buf, logtitle="Read image download index")
            l=len(self.__phone.protocolclass.image_file_path)+1
            for i in range(self.__phone.protocolclass.max_image_entries):
                e=img_idx.entry[i]
                if e.name_len:
                    r[e.file_name[l:e.file_name_len]]=e.file_name[:e.file_name_len]
        except:
            pass
        return r

#-------------------------------------------------------------------------------
class PhoneNumbers:
    def __init__(self, phone):
        self.__phone=phone
        self.__numbers=None

    def read(self):
        try:
            buf=prototypes.buffer(self.__phone.getfilecontents(\
                self.__phone.protocolclass.number_file_name))
            self.__numbers=self.__phone.protocolclass.numbers()
            self.__numbers.readfrombuffer(buf, logtitle="Read number file "+self.__phone.protocolclass.number_file_name)
        except:
            self.__phone.log('Failed to read numbers file')
            self.__numbers=[]

    def get(self, index, default=None):
        if index>=self.__phone.protocolclass.max_number_entries:
            return default
        e=self.__numbers.entry[index]
        if e.valid:
            return e.name[:e.length]
        return default
    
#-------------------------------------------------------------------------------
class PhoneBook:

    __pb_numbers= ({'home': 'home_num_index' },
                    {'office': 'office_num_index' },
                    {'cell': 'mobile_num_index' },
                    {'pager': 'pager_num_index' },
                    {'fax': 'fax_num_index' })
    def __init__(self, phone):
        self.__phone=phone
        self.__pb=None
        self.__numbers=None
        self.__groups=None
        self.__rt_index=None
        self.__id=None
        self.__slots=None

    def read(self):
        try:
            buf=prototypes.buffer(self.__phone.getfilecontents(\
                self.__phone.protocolclass.pb_file_name))
            self.__pb=self.__phone.protocolclass.pbbook()
            self.__pb.readfrombuffer(buf, logtitle="Read "+self.__phone.protocolclass.pb_file_name)
        except:
            self.__pb=[]
            self.__phone.log('Failed to read phonebook')

    def get_ringtone(self, index):
        """
        Return the ringtone index of this entry.
        """
        if self.__pb is None:
            self.read()
        rt=self.__pb.entry[index].ringer_type
        if rt:
            rt-=71
        return rt

    def __extract_entry(self, e, pb_cnt, mem_index):
        res={}
        # serials
        res['serials']=[ {'sourcetype': self.__phone.serialsname,
                          'sourceuniqueid': self.__id,
                          'serial1': `pb_cnt`,
                          'serial2': `mem_index` }]
        # only one name
        res['names']=[ {'full': e.name } ]
        if e.alias_num_index:
            res['names'][0]['nickname']=self.__numbers.get(e.alias_num_index, '')

        # only one category
        res['categories']=[ {'category': self.__groups[e.group_num]['name'] } ]

        # emails
        if e.email_index:
            res['emails']=[ { 'email': self.__numbers.get(e.email_index, '') } ]

        # urls: N/A
        # private: N/A
        # memos: N/A
        # wallpapers: N/A

        # ringtones
        rt=e.ringer_type
        if rt:
            rt-=71
        res['ringtones']=[ { 'ringtone': self.__rt_index[rt]['name'],
                             'use': 'call' } ]

        # numbers
        speed_dial=e.speed_dial_index
        res['numbers']=[]
        for k, a in enumerate(self.__pb_numbers):
            for key, attr in a.items():
                idx=getattr(e, attr, 0)
                if idx:
                    num=self.__numbers.get(idx, '')
                    if idx==speed_dial:
                        res['numbers'].append({ 'number': num,
                                        'type': key,
                                        'speeddial': mem_index  } )
                    else:
                        res['numbers'].append({ 'number': num,
                                        'type': key })
        # done
        return res
        
    def get_dict(self, result):
        # read the phonebook if not already done so
        if self.__pb is None:
            self.read()
        # read the phone numbers
        if self.__numbers is None:
            self.__numbers=PhoneNumbers(self.__phone)
            self.__numbers.read()
        # read the slot entries
        if self.__slots is None:
            self.__slots=PBSlot(self.__phone)
            self.__slots.read()
        # get fundamental info
        self.__groups=result.get('groups', {})
        self.__rt_index=result.get('ringtone-index', {})
        self.__id=result.get('uniqueserial', '')
        # loop through the phonebook and extract each entry
        r={}
        for pb_cnt, i in enumerate(self.__slots):
            if i==0:
                # empty slot
                continue
            e=self.__pb.entry[i]
            if e.mem_index:
                if i != e.mem_index:
                    self.__phone.log('i: %d, mem_index: %d'%(i, e.mem_index))
                r[pb_cnt]=self.__extract_entry(e, pb_cnt, i)
        return r

#-------------------------------------------------------------------------------
class PBSlot:
    """ Class to handle Phonebook entry slot -> memory slot """
    def __init__(self, phone):
        self.__phone=phone
        self.__slots=None

    def read(self):
        try:
            buf=prototypes.buffer(self.__phone.getfilecontents(\
                self.__phone.protocolclass.slot_file_name))
            self.__slots=self.__phone.protocolclass.pbslots()
            self.__slots.readfrombuffer(buf, logtitle="Read slots file "+self.__phone.protocolclass.slot_file_name)
        except:
            self.__slots=[]
            self.__phone.log('Failed to read slot file')

    def __getitem__(self, key):
        if type(key) is not int:
            raise KeyError
        if key<0 or key>=self.__phone.protocolclass.max_pb_slots:
            raise IndexError
        if self.__slots is None:
            self.read()
        return self.__slots.slot[key].pbbook_index
