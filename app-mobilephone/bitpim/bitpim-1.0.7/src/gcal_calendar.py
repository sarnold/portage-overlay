### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: gcal_calendar.py 4375 2007-08-25 16:25:22Z djpham $

"Deals with Google Calendar (gCalendar) import stuff"

# system modules
from __future__ import with_statement
import urllib2

# site modules
import wx

# local modules
import common_calendar
import database
import guihelper
import ical_calendar as ical
import vcal_calendar as vcal

module_debug=False

#-------------------------------------------------------------------------------
class ImportDataSource(common_calendar.ImportDataSource):
    # how to define, and retrieve calendar import data source
    message_str='Select a Google Calendar iCal URL'

    def browse(self, parent=None):
        # how to select a source, default to select a file
        if parent is None or not hasattr(parent, 'GetActiveDatabase'):
            # need the database
            return
        with guihelper.WXDialogWrapper(SelectURLDialog(parent, self.message_str,
                                                       parent.GetActiveDatabase()),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self._source=dlg.GetPath()

#-------------------------------------------------------------------------------
URLDictKey='URLs'
URLDictName='gCalURL'
class URLDataObject(database.basedataobject):
    # object to store a list of URLs & names in the DB
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    _knownlistproperties.update( { 'urls': [ 'url', 'name'] })
    def __init__(self, data=None):
        if data:
            self.update(data)
urlobjectfactory=database.dataobjectfactory(URLDataObject)

#-------------------------------------------------------------------------------
class gCalendarServer(vcal.vCalendarFile):

    def _open(self, name):
        return urllib2.urlopen(name)

#-------------------------------------------------------------------------------
parentclass=ical.iCalendarImportData
class gCalendarImportData(parentclass):
    _source_data_class=gCalendarServer
    def read(self, file_name=None, update_dlg=None):
        try:
            super(gCalendarImportData, self).read(file_name, update_dlg)
        except urllib2.URLError:
            raise IOError

#-------------------------------------------------------------------------------
class gCalImportDialog(ical.iCalImportCalDialog):
    _filetype_label='Google Calendar iCal URL:'
    _data_type='Google Calendar'
    _import_data_class=gCalendarImportData
    def __init__(self, parent, id, title):
        self._db=parent.GetActiveDatabase()
        super(gCalImportDialog, self).__init__(parent, id, title)

    def OnBrowseFolder(self, _):
        with guihelper.WXDialogWrapper(SelectURLDialog(self, 'Select a Google Calendar iCal URL', self._db),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.folderctrl.SetValue(dlg.GetPath())

#-------------------------------------------------------------------------------
class SelectURLDialog(wx.Dialog):
    def __init__(self, parent, message, database):
        super(SelectURLDialog, self).__init__(parent, -1, 'URL Selection')
        self._db=database
        self._data=[]
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(wx.StaticText(self, -1, message), 0, wx.EXPAND|wx.ALL, 5)
        self._choices=wx.ListBox(self, -1,
                                 style=wx.LB_SINGLE|wx.LB_HSCROLL|wx.LB_NEEDED_SB)
        wx.EVT_LISTBOX_DCLICK(self, self._choices.GetId(), self.OnOK)
        vbs.Add(self._choices, 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        hbs=self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        _btn=wx.Button(self, -1, 'New')
        wx.EVT_BUTTON(self, _btn.GetId(), self.OnNew)
        hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        _btn=wx.Button(self, -1, 'Delete')
        wx.EVT_BUTTON(self, _btn.GetId(), self.OnDel)
        hbs.Add(_btn, 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)

        self._get_from_fs()
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

    def _get_from_fs(self):
        # retrieve data from the DB
        _db_data=self._db.getmajordictvalues(URLDictName, urlobjectfactory)
        self.set(_db_data.get(URLDictKey, {}).get('urls', []))
    def _save_to_fs(self, data):
        _dict={ URLDictKey: { 'urls': data } }
        database.ensurerecordtype(_dict, urlobjectfactory)
        self._db.savemajordict(URLDictName, _dict)
    def set(self, data):
        self._data=data
        self._choices.Clear()
        for _item in self._data:
            self._choices.Append(_item['name'], _item['url'])
    def OnDel(self, _):
        _idx=self._choices.GetSelection()
        if _idx==wx.NOT_FOUND:
            return
        self._choices.Delete(_idx)
        del self._data[_idx]
        self._save_to_fs(self._data)
    def OnNew(self, _):
        with guihelper.WXDialogWrapper(NewURLDialog(self),
                                       True) as (_dlg, retcode):
            if retcode==wx.ID_OK:
                _name, _url=_dlg.get()
                self._choices.Append(_name, _url)
                self._data.append({ 'name': _name,
                                    'url': _url })
                self._save_to_fs(self._data)
    def OnOK(self, evt):
        self.EndModal(wx.ID_OK)
    def GetPath(self):
        _idx=self._choices.GetSelection()
        if _idx==wx.NOT_FOUND:
            return ''
        return self._choices.GetClientData(_idx)

#-------------------------------------------------------------------------------
class NewURLDialog(wx.Dialog):
    def __init__(self, parent):
        super(NewURLDialog, self).__init__(parent, -1, 'New URL Entry')
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(wx.StaticText(self, -1, 'URL:'), 0, wx.EXPAND|wx.ALL, 5)
        self._url=wx.TextCtrl(self, -1, '')
        vbs.Add(self._url, 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticText(self, -1, 'Name:'), 0, wx.EXPAND|wx.ALL, 5)
        self._name=wx.TextCtrl(self, -1, '')
        vbs.Add(self._name, 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL),
                0, wx.EXPAND|wx.ALL, 5)
        
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

    def get(self):
        return self._name.GetValue(), self._url.GetValue()
