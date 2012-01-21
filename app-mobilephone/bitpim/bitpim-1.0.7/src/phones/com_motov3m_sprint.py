### BITPIM
###
### Copyright (C) 2007 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_motov3m.py 4537 2007-12-30 03:32:13Z djpham $

"""Communicate with Motorola phones using AT commands"""

import common
import com_motov3m as v3m
import com_moto
import helpids
import fileinfo
import p_motov3m_sprint
import prototypes

parentphone=v3m.Phone
class Phone(parentphone):
    desc='Moto-V3m'
    helpid=helpids.ID_PHONE_MOTOV3M
    protocolclass=p_motov3m_sprint
    serialsname='motov3m'
    builtinringtones=(
        (0, ('Silent',)),
        (5, ('Vibe Dot', 'Vibe Dash', 'Vibe Dot Dot', 'Vibe Dot Dash',
             'Vibe Pulse')),
        )

    def __init__(self, logtarget, commport):
        parentphone.__init__(self, logtarget, commport)

    def _ensure_speeddials(self, fundamentals):
        """Make sure that each and every number/email/mail list has a
        speed dial, which is being used as the slot/index number
        """
        _pb_book=fundamentals.get('phonebook', {})
        _sd_slots=[False]*(self.protocolclass.PB_TOTAL_ENTRIES+1)
        _sd_slots[0:self.protocolclass.PB_FIRST_ENTRY]=[True]*self.protocolclass.PB_FIRST_ENTRY
        # go through the first round and mark the slots being used
        for _key,_pb_entry in _pb_book.items():
            self._mark_used_slots(_pb_entry.get('numbers', []), _sd_slots,
                                  'number')
            self._mark_used_slots(_pb_entry.get('emails', []), _sd_slots,
                                  'email')
            self._mark_used_slots(_pb_entry.get('maillist', []), _sd_slots,
                                  'entry')
        # go through the 2nd time and populate unknown speed dials
        for _key, _pb_entry in _pb_book.items():
            self._get_sd_slot(_pb_entry.get('numbers', []), _sd_slots,
                              'number')
            self._get_sd_slot(_pb_entry.get('emails', []), _sd_slots,
                              'email')
            self._get_sd_slot(_pb_entry.get('maillist', []), _sd_slots,
                              'entry')
        return _sd_slots

    def getphonebook(self, result):
        """Reads the phonebook data.  The L{getfundamentals} information will
        already be in result."""
        self.log('Getting phonebook')
        self.setmode(self.MODEPHONEBOOK)
        # pick the main phonebook
        self.select_phonebook()
        # setting up
        pb_book={}
        result['pb_list']=[]
        result['sd_dict']={}
        # loop through and read 10 entries at a timer
        _total_entries=self.protocolclass.PB_TOTAL_ENTRIES
        _first_entry=self.protocolclass.PB_FIRST_ENTRY
        _req=self.protocolclass.read_pb_req()
        for _start_idx in range(_first_entry, _total_entries+1, 10):
            _end_idx=min(_start_idx+9, _total_entries)
            _req.start_index=_start_idx
            _req.end_index=_end_idx
            for _retry_cnt in range(2):
                try:
                    self.progress(_end_idx, _total_entries,
                                  'Reading contact entry %d to %d'%(_start_idx, _end_idx))
                    _res=self.sendATcommand(_req, self.protocolclass.read_pb_resp)
                    for _entry in _res:
                        self._build_pb_entry(_entry, pb_book, result)
                    break
                except:
                    if _retry_cnt:
                        self.log('Failed to read phonebook data')
                    else:
                        self.log('Failed to read phonebook data, retrying...')
        self._update_mail_list(pb_book, result)
        self.setmode(self.MODEMODEM)
        del result['pb_list'], result['sd_dict']
        _keys=result['groups'].keys()
        result['categories']=[x['name'] for _,x in result['groups'].items()]
        result['phonebook']=pb_book
        return pb_book

    def savephonebook(self, result):
        result=com_moto.Phone.savephonebook(self,result)
        result['rebootphone']=True
        return result

    def _populate_pb_entry(self, pb_entry, entry, fundamentals):
        """Populate a BitPim phonebook entry with one from the phone
        """
        # extract the number, email, or mailing list
        _num_type=entry.number_type
        if _num_type in self.protocolclass.NUMBER_TYPE:
            self._populate_pb_number(pb_entry, entry, fundamentals)
        elif _num_type in self.protocolclass.EMAIL_TYPE:
            self._populate_pb_email(pb_entry, entry, fundamentals)
        elif _num_type in self.protocolclass.WWW_TYPE:
            self._populate_pb_www(pb_entry, entry, fundamentals)
        elif _num_type in self.protocolclass.MEMO_TYPE:
            self._populate_pb_memo(pb_entry, entry, fundamentals)
        # this is a mail list, which is not currently supported
##        else:
##            self._populate_pb_maillist(pb_entry, entry, fundamentals)
        
    def _populate_pb_www(self, pb_entry, entry, fundamentals):
        """Extract the www component"""
        _www={ 'url': entry.number }
        self._populate_pb_misc(pb_entry, _www, 'urls', entry,
                               fundamentals)
        # and mark it
        fundamentals['sd_dict'][entry.index]=entry.number

    def _populate_pb_memo(self, pb_entry, entry, fundamentals):
        """Extract the memo component"""
        _www={ 'memo': entry.number }
        self._populate_pb_misc(pb_entry, _www, 'memos', entry,
                               fundamentals)
        # and mark it
        fundamentals['sd_dict'][entry.index]=entry.number


#-------------------------------------------------------------------------------
parentprofile=v3m.Profile
class Profile(parentprofile):
    serialsname=Phone.serialsname

    usbids=( ( 0x22B8, 0x2A64, 0),)
    deviceclasses=("serial")

    # use for auto-detection
    phone_manufacturer='Motorola'
    phone_model='+GMM: Motorola V3m-Sprint Phone'
    common_model_name='V3m'
    generic_phone_model='Motorola CDMA V3m Phone'

    # fill in the list of ringtone/sound origins on your phone
    ringtoneorigins=('ringers',)

    # our targets are the same for all origins
    imagetargets={}
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "wallpaper",
                                      {'width': 176, 'height': 184, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "outsidelcd",
                                      {'width': 96, 'height': 72, 'format': "JPEG"}))
    imagetargets.update(common.getkv(parentprofile.stockimagetargets, "fullscreen",
                                      {'width': 176, 'height': 220, 'format': "JPEG"}))

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'read', None),   # all calendar reading
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('wallpaper', 'write', 'OVERWRITE'),
        ('sms', 'read', None),     # all SMS list reading DJP
        )
