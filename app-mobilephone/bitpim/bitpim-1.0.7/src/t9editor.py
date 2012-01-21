### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: t9editor.py 4379 2007-08-28 03:06:58Z djpham $
"""
Code to handle T9 Editor

The format of the T9 Words data is standardized.  It is a list of dict that
has the following standard fields:

"words": an ordered list of dicts, each dict has the following fields:
         "word": string value of the actual T9 Word.

To implement T9 Editor feature for your phone, do the following:

1. Add 2 entries into Profile._supportedsyncs:
        ...
        ('t9_udb', 'read', 'OVERWRITE'),
        ('t9_udb', 'write', 'OVERWRITE'),

2. Implement the following 2 methods in your Phone class:
    def gett9db(self, result)
    def savet9db(self, result, _merge)

    The result dict should contain:
    result[t9editor.dict_key]=<instance of t9editor.T9WordsList()>

    See module phones.com_lgxv8500 for an example implementation.

"""

# wx Modules
from __future__ import with_statement
import wx
import wx.gizmos as gizmos

# BitPim modules
import database
import guihelper
import helpids
import widgets

# module constants--------------------------------------------------------------
dict_key='T9 Data'

#-------------------------------------------------------------------------------
class T9WordsDataObject(database.basedataobject):
    _knownproperties=[]
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    _knownlistproperties.update( { 'words': ['word'] })
    def __init__(self, data=None):
        if data and isinstance(data, dict):
            self.update(data)
t9wordsdataobjectfactory=database.dataobjectfactory(T9WordsDataObject)

#-------------------------------------------------------------------------------
class T9WordsList(object):
    _t9_dict={'0': '0', '1': '1',
              'a': '2', 'b': '2', 'c': '2', '2': '2',
              'd': '3', 'e': '3', 'f': '3', '3': '3',
              'g': '4', 'h': '4', 'i': '4', '4': '4',
              'j': '5', 'k': '5', 'l': '5', '5': '5',
              'm': '6', 'n': '6', 'o': '6', '6': '6',
              'p': '7', 'q': '7', 'r': '7', 's': '7', '7': '7',
              't': '8', 'u': '8', 'v': '8', '8': '8',
              'w': '9', 'x': '9', 'y': '9', 'z': '9', '9': '9',
              }
    def __init__(self):
        self._data={}

    def get(self):
        return copy.deepcopy(self._data, {})
    def set(self, d):
        self._data={}
        self._data.update(d)

    def _set_or_del(self, key, v, v_list=[]):
        if v is None or v in v_list:
            if self._data.has_key(key):
                del self._data[key]
        else:
            self._data[key]=v

    def _get_keys(self):
        # return a list of available keys in this list
        _keys=[x for x,y in self._data.items() if y]
        _keys.sort()
        return _keys
    keys=property(fget=_get_keys)

    def _keyof(self, word):
        # return the T9 key of this word
        return ''.join([self._t9_dict.get(x.lower(), '1') for x in word])

    def get_words(self, key=None):
        # return a list of words of group 'key',
        # if key is None, return the whole list
        _res=[]
        if key is None:
            _keys=self.keys
            _keys.sort()
            for _k in _keys:
                _res+=self.get_words(_k)
        else:
            return self._data.get(key, [])

    def del_word(self, word):
        # delete the specified word from the list
        _key=self._keyof(word)
        if self._data.has_key(_key):
            for _idx,_word in enumerate(self._data[_key]):
                if _word==word:
                    del self._data[_key][_idx]
                    if not self._data[_key]:
                        # empty list
                        del self._data[_key]
                    return

    def append_word(self, word):
        # Append this word to our existing list
        self._data.setdefault(self._keyof(word), []).append(word)

    def set_words(self, words, key=None):
        # set the list of words for group 'key'
        # if key is None, set the whole database
        if key is None:
            # set the whole list
            self._data={}
            for _word in words:
                self.append_word(_word)
        else:
            _l=[]
            for _word in words:
                if self._keyof(_word)==key:
                    _l.append(_word)
            self._data[key]=_l

    def clear(self):
        self._data={}

    def save(self, db):
        # save the current list to the database db
        global dict_key
        _rec=[]
        for _,_list in self._data.items():
            _rec+=[ { 'word': x } for x in _list ]
        _dict={ dict_key: { 'words': _rec } }
        database.ensurerecordtype(_dict, t9wordsdataobjectfactory)
        db.savemajordict(dict_key, _dict)
    def load(self, db):
        # load from database db into the current list
        global dict_key
        _dict=db.getmajordictvalues(dict_key, t9wordsdataobjectfactory)
        self.clear()
        for _word in _dict.get(dict_key, {}).get('words', []):
            if _word.get('word', None):
                self.append_word(_word['word'])

#-------------------------------------------------------------------------------
class T9EditorWidget(wx.Panel, widgets.BitPimWidget):
    help_id=helpids.ID_TAB_T9EDITOR
    def __init__(self, mainwindow, parent):
        super(T9EditorWidget, self).__init__(parent, -1)
        self._mw=mainwindow
        self._t9list=T9WordsList()
        self.ignoredirty=False
        self.dirty=False
        # main box sizer
        vbs=wx.BoxSizer(wx.VERTICAL)
        # horizontal sizer for the main contents
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        _svbs=wx.StaticBoxSizer(wx.StaticBox(self, -1, 'T9 Keys'),
                                wx.VERTICAL)
        self._keys_lb=wx.ListBox(self, -1,
                                 style=wx.LB_SINGLE|wx.LB_HSCROLL|wx.LB_NEEDED_SB)
        wx.EVT_LISTBOX(self, self._keys_lb.GetId(), self._OnSelectKey)
        _svbs.Add(self._keys_lb, 1, wx.EXPAND|wx.ALL, 5)
        hbs.Add(_svbs, 1, wx.EXPAND|wx.ALL, 5)
        self._words_w=gizmos.EditableListBox(self, -1, 'T9 Words:', style=0)
        self._words_lb=self._words_w.GetListCtrl()
        wx.EVT_BUTTON(self._words_w, self._words_w.GetUpButton().GetId(),
                      self._OnUpDown)
        wx.EVT_BUTTON(self._words_w, self._words_w.GetDownButton().GetId(),
                      self._OnUpDown)
        hbs.Add(self._words_w, 3, wx.EXPAND|wx.ALL, 5)
        vbs.Add(hbs, 1, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        self._save_btn=wx.Button(self, wx.ID_SAVE)
        hbs.Add(self._save_btn, 0,
                wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs.Add(wx.Button(self, wx.ID_HELP), 0,
                wx.ALIGN_CENTRE|wx.ALL, 5)
        self._revert_btn=wx.Button(self, wx.ID_REVERT_TO_SAVED)
        hbs.Add(self._revert_btn, 0,
                wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_SAVE, self._OnSave)
        wx.EVT_BUTTON(self, wx.ID_REVERT_TO_SAVED, self._OnRevert)
        wx.EVT_BUTTON(self, wx.ID_HELP,
                      lambda _: wx.GetApp().displayhelpid(self.help_id))
        vbs.Add(hbs, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)
        # populate data
        self._populate()
        # turn on dirty flag
        self.setdirty(False)

    def setdirty(self, val):
        if self.ignoredirty:
            return
        self.dirty=val
        self._save_btn.Enable(self.dirty)
        self._revert_btn.Enable(self.dirty)

    def _populate_each(self):
        # populate the word list based on the selected key
        _sel=self._keys_lb.GetStringSelection()
        self._words_lb.DeleteAllItems()
        if _sel:
            self._words_w.SetStrings(self._t9list.get_words(_sel))
    def _populate(self):
        # clear both lists
        self._keys_lb.Clear()
        self._words_lb.DeleteAllItems()
        # populate the keys list
        for _key in self._t9list.keys:
            self._keys_lb.Append(_key)
    def populate(self, dict):
        global dict_key
        self._t9list=dict.get(dict_key, T9WordsList())
        self._populate()
    def populatefs(self, dict):
        global dict_key
        self._t9list=dict.get(dict_key, T9WordsList())
        self._t9list.save(self._mw.database)
        self._populate()
        return dict
    def getfromfs(self, result):
        self._t9list.load(self._mw.database)
        global dict_key
        result[dict_key]=self._t9list
        return result
    # called from various widget update callbacks
    def _re_order(self):
        # update the order of the list
        self._t9list.set_words(self._words_w.GetStrings(),
                               self._keys_lb.GetStringSelection())
    def _OnUpDown(self, evt):
        wx.CallAfter(self._re_order)
        self.OnMakeDirty()
        evt.Skip()
    def OnMakeDirty(self, _=None):
        """A public function you can call that will set the dirty flag"""
        if self.dirty or self.ignoredirty:
            # already dirty, no need to make it worse
            return
        self.setdirty(True)
    def OnDirty(self, _):
        self.setdirty(True)

    def _OnSave(self, _):
        self._t9list.save(self._mw.database)
        self.setdirty(False)
    def _OnRevert(self, _):
        self._t9list.load(self._mw.database)
        self._populate()
        self.setdirty(False)
    def _OnSelectKey(self, _):
        self._populate_each()
    def CanAdd(self):
        return True
    def OnAdd(self, _):
        with guihelper.WXDialogWrapper(wx.TextEntryDialog(self, 'Enter a new word:',
                                                          'T9 User Word'),
                                       True) as (_dlg, _retcode):
            if _retcode==wx.ID_OK:
                if _dlg.GetValue():
                    self.OnMakeDirty()
                    self._t9list.append_word(_dlg.GetValue())
                    self._populate()

    def CanDelete(self):
        return self._words_lb.GetSelectedItemCount()
    def OnDelete(self, _):
        _idx=self._words_lb.GetNextItem(-1, state=wx.LIST_STATE_SELECTED)
        if _idx==-1:
            return
        self._t9list.del_word(self._words_w.GetStrings()[_idx])
        self._words_lb.DeleteItem(_idx)
        # Check if this key is empty, if it is, delete it from the keys LB
        if self._words_lb.GetItemCount()<2:
            # this key is empty, delete it as well
            _idx=self._keys_lb.GetSelection()
            if _idx!=wx.NOT_FOUND:
                self._keys_lb.Delete(_idx)
        self.OnMakeDirty()
        wx.CallAfter(self._re_order)
    def getdata(self, result):
        global dict_key
        result[dict_key]=self._t9list
        return result
