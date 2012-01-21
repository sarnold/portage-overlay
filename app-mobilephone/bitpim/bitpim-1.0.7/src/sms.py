### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@netzero.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: sms.py 3126 2006-04-20 22:08:45Z djpham $

"""
Code to handle SMS items.

The format for the SMS item is standardized.  It is an object with the following
attributes:

_from: string (email addr or phone #)
_to: string (email addr or phone #) Deprecated, should use add_recipient()
subject: string
text: string
datetime: string "YYYYMMDDThhmmss" or (y,m,d,h,m)
callback: string (optional callback phone #)
folder: string (where this item belongs: 'Inbox', 'Sent', 'Saved')
locked: True/False
msg_id: unique message id (hexstring sha encoded (datetime+text))
priority: (normal/high)
read: (T/F)

available methods:

add_recipient(name, confirmed=None, confirmed_datetime=None)
  - name: email addr or phone # of the recipient
  - confirmed: True/False/None
  - confirmed_datetime: "YYYYMMDDThhmmss" or (y,m,d,h,m)

confirm_recipient(name, confirmed_datetime)
  - name: email addr or phone # of the recipient
  - confirmed_datetime: "YYYYMMDDThhmmss" or (y,m,d,h,m)


The format for the Canned SMS Message item is standard.  It is an object with
the following attributes:

user_list: ['msg1', 'msg2', ...] list of user canned messages.
builtin_list: ['msg1', 'msg2', ...] list of built-in canned messages.
           This attribute is Read-Only.


To implement SMS read for a phone module:
 Add an entry into Profile._supportedsyncs:
        ...
        ('sms', 'read', None),     # sms reading

 Implement the following method in your Phone class: 
    def getsms(self, result):
        ...
        return result

The result dict key for the SMS messages is 'sms', which is a dict of SMSEntry
objetcs.
The result dict key for the canned messages is 'canned_msg', which has the
following format:

result['canned_msg']=[{ 'text': 'Yes', 'type': 'builtin' },
                      { 'text': 'No', 'type': 'user' }, ... ]
"""

# standard modules
import copy
import sha
import time

# wx modules

# BitPim modules
import database

#-------------------------------------------------------------------------------
class SMSDataObject(database.basedataobject):
    _knownproperties=['_from', '_to', 'subject', 'text', 'datetime',
                      'callback', 'folder', 'msg_id', 'read', 'priority' ]
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    _knownlistproperties.update( { 'flags': ['locked', 'read'],
                                   'receivers': ['name', 'confirmed_datetime'] })
    def __init__(self, data=None):
        if data is None or not isinstance(data, SMSEntry):
            return;
        self.update(data.get_db_dict())
smsobjectfactory=database.dataobjectfactory(SMSDataObject)

#-------------------------------------------------------------------------------
class CannedMsgDataObject(database.basedataobject):
    _knownproperties=[]
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    _knownlistproperties.update( { 'canned_msg': ['text', 'type'] })
    def __init__(self, data=None):
        if data is None or not isinstance(data, CannedMsgEntry):
            return;
        self.update(data.get_db_dict())
cannedmsgobjectfactory=database.dataobjectfactory(CannedMsgDataObject)

#-------------------------------------------------------------------------------
class SMSEntry(object):
    Folder_Inbox='Inbox'
    Folder_Sent='Sent'
    Folder_Saved='Saved'
    Valid_Folders=(Folder_Inbox, Folder_Sent, Folder_Saved)
    _id_index=0
    _max_id_index=999
    Priority_Normal=1
    Priority_High=2
    _priority_name={
        Priority_Normal: 'Normal',
        Priority_High: 'High' }
    _unknown_datetime='YYYY-MM-DD hh:mm:ss'

    def __init__(self):
        self._data={ 'serials': [] }
        self._create_id()

    def get(self):
        return copy.deepcopy(self._data, {})
    def set(self, d):
        self._data={}
        self._data.update(d)

    def get_db_dict(self):
        return self.get()
    def set_db_dict(self, d):
        self.set(d)

    def _create_id(self):
        "Create a BitPim serial for this entry"
        self._data.setdefault("serials", []).append(\
            {"sourcetype": "bitpim",
             "id": '%.3f%03d'%(time.time(), SMSEntry._id_index) })
        if SMSEntry._id_index<SMSEntry._max_id_index:
            SMSEntry._id_index+=1
        else:
            SMSEntry._id_index=0
    def _get_id(self):
        s=self._data.get('serials', [])
        for n in s:
            if n.get('sourcetype', None)=='bitpim':
                return n.get('id', None)
        return None
    id=property(fget=_get_id)

    def _set_or_del(self, key, v, v_list=[]):
        if v is None or v in v_list:
            if self._data.has_key(key):
                del self._data[key]
        else:
            self._data[key]=v

    def _get_from(self):
        return self._data.get('_from', '')
    def _set_from(self, v):
        self._set_or_del('_from', v, [''])
    _from=property(fget=_get_from, fset=_set_from)
    def _get_to(self):
        l=self._data.get('receivers', [])
        if l:
            return ','.join([x['name'] for x in l])
        return self._data.get('_to', '')
    def _set_to(self, v):
        self._set_or_del('_to', v, [''])
    _to=property(fget=_get_to, fset=_set_to)
    def _get_subject(self):
        return self._data.get('subject', '<None>')
    def _set_subject(self, v):
        self._set_or_del('subject', v, [''])
    subject=property(fget=_get_subject, fset=_set_subject)
    def _get_text(self):
        return self._data.get('text', '')
    def _set_text(self, v):
        self._set_or_del('text', v, [''])
        self._check_and_create_msg_id()
    text=property(fget=_get_text, fset=_set_text)
    def _get_datetime(self):
        return self._data.get('datetime', '')
    def _set_datetime(self, v):
        if isinstance(v, (list, tuple)) and len(v)==5:
            v='%04d%02d%02dT%02d%02d00'%v
        elif not isinstance(v, (str, unicode)):
            raise TypeError('must be YYYYMMDDThhmmss or (y,m,d,h,m)')
        self._set_or_del('datetime', v, [''])
        self._check_and_create_msg_id()
    datetime=property(fget=_get_datetime, fset=_set_datetime)
    def get_date_time_str(self):
        # return a string representing this date/time in the format of
        # YYYY-MM-DD hh:mm:ss
        s=self.datetime
        if not len(s):
            s=self._unknown_datetime
        else:
            s=s[:4]+'-'+s[4:6]+'-'+s[6:8]+' '+s[9:11]+':'+s[11:13]+':'+s[13:]
        return s
    def _check_and_create_msg_id(self):
        if not len(self.msg_id) and len(self.text) and len(self.datetime):
            self._data['msg_id']=sha.new(self.datetime+self.text).hexdigest()
    def _get_callback(self):
        return self._data.get('callback', '')
    def _set_callback(self, v):
        self._set_or_del('callback', v, [''])
    callback=property(fget=_get_callback, fset=_set_callback)
    def _get_folder(self):
        return self._data.get('folder', '')
    def _set_folder(self, v):
        if v not in self.Valid_Folders:
            raise ValueError
        self._set_or_del('folder', v, [''])
    folder=property(fget=_get_folder, fset=_set_folder)

    def _get_flag_value(self, flag_key, default=None):
        f=self._data.get('flags', [])
        for n in f:
            if n.has_key(flag_key):
                return n[flag_key]
        return default
    def _set_flag_value(self, flag_key, v):
        f=self._data.get('flags', [])
        for i, n in enumerate(f):
            if n.has_key(flag_key):
                if v is None or not v:
                    del f[i]
                    if not len(self._data['flags']):
                        del self._data['flags']
                else:
                    n[flag_key]=v
                return
        if v is not None and v:
            self._data.setdefault('flags', []).append({flag_key: v})

    def _get_locked(self):
        return self._get_flag_value('locked', False)
    def _set_locked(self, v):
        self._set_flag_value('locked', v)
    locked=property(fget=_get_locked, fset=_set_locked)
    def _get_read(self):
        return self._get_flag_value('read', False)
    def _set_read(self, v):
        self._set_flag_value('read', v)
    read=property(fget=_get_read, fset=_set_read)

    def _get_msg_id(self):
        return self._data.get('msg_id', '')
    msg_id=property(fget=_get_msg_id)

    def _get_priority(self):
        return self._data.get('priority', SMSEntry.Priority_Normal)
    def _set_priority(self, v):
        if v not in (SMSEntry.Priority_Normal, SMSEntry.Priority_High):
            raise ValueError('must be SMSEntry.Priority_Normal or SMSEntry.Priority_High')
        self._set_or_del('priority', v, [])
    def _get_priority_str(self):
        return self._priority_name[self.priority]
    priority=property(fget=_get_priority, fset=_set_priority)
    priority_str=property(fget=_get_priority_str)

    def add_recipient(self, name, confirmed=None, confirmed_datetime=None):
        if isinstance(confirmed_datetime, (list, tuple)):
            if len(confirmed_datetime)!=5:
                raise ValueError('must be (y,m,d,h,m)')
            confirmed_datetime='%04d%02d%02dT%02d%02d00'%confirmed_datetime
        r={'name': name }
        if confirmed_datetime:
            r['confirmed_datetime']=confirmed_datetime
        self._data.setdefault('receivers', []).append(r)
    def confirm_recipient(self, name, confirmed_datetime):
        if isinstance(confirmed_datetime, (list, tuple)):
            if len(confirmed_datetime)!=5:
                raise ValueError('must be (y,m,d,h,m)')
            confirmed_datetime='%04d%02d%02dT%02d%02d00'%confirmed_datetime
        for e in self._data.get('receivers', []):
            if e['name']==name:
                e['confirmed_datetime']=confirmed_datetime
                return
        raise Exception('Receiver %s not found'%name)
    def _get_delivery_status(self):
        # return a list of delivery status, one of each recipient
        res=[]
        l=self._data.get('receivers', [])
        for e in l:
            s=e.get('confirmed_datetime', None)
            if s:
                res.append('%s confirmed on %s-%s-%s %s:%s'%
                           (e['name'], s[:4], s[4:6], s[6:8],
                            s[9:11], s[11:13]))
            else:
                res.append('%s not confirmed'%e['name'])
        return res
    delivery_status=property(fget=_get_delivery_status)

#-------------------------------------------------------------------------------
class CannedMsgEntry(object):
    _data_key='canned_msg'
    builtin_type='builtin'
    user_type='user'
    def __init__(self):
        self._data={ 'serials': [] }
        self._create_id()

    def get(self):
        return copy.deepcopy(self._data, {})
    def set(self, d):
        self._data={}
        self._data.update(d)

    def get_db_dict(self):
        return self.get()
    def set_db_dict(self, d):
        self.set(d)

    def _create_id(self):
        "Create a BitPim serial for this entry"
        self._data.setdefault("serials", []).append(\
            {"sourcetype": "bitpim", "id": str(time.time())})
    def _get_id(self):
        s=self._data.get('serials', [])
        for n in s:
            if n.get('sourcetype', None)=='bitpim':
                return n.get('id', None)
        return None
    id=property(fget=_get_id)

    def _get_builtin_list(self):
        return [x['text'] for x in self._data.get(self._data_key, []) \
                if x.get('type', None)==self.builtin_type]
    builtin_list=property(fget=_get_builtin_list)

    def _get_user_list(self):
        return [x['text'] for x in self._data.get(self._data_key, []) \
                if x.get('type', None)==self.user_type]
    def _set_user_list(self, v):
        # first get all the builtin ones
        l=[x for x in self._data.get(self._data_key, []) \
           if x.get('type', None)==self.builtin_type]
        # then add the user ones
        l+=[ { 'text': x, 'type': self.user_type } for x in v]
        self._data[self._data_key]=l
    msg_list=user_list=property(fget=_get_user_list, fset=_set_user_list)

#-------------------------------------------------------------------------------
