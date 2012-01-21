#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: imp_cal_preset.py 4380 2007-08-29 00:17:07Z djpham $

""" Handle Import Calendar Preset feature
"""

# System
from __future__ import with_statement
import calendar
import copy
import datetime
import random
import sha

# wx
import wx
import wx.wizard as wiz

# BitPim
import common_calendar
import database
import guihelper
import imp_cal_wizard
import importexport
import setphone_wizard

# modules constants
IMP_OPTION_REPLACEALL=0
IMP_OPTION_ADD=1
IMP_OPTION_PREVIEW=2
IMP_OPTION_MERGE=3

#-------------------------------------------------------------------------------
class ImportCalendarDataObject(common_calendar.FilterDataObject):
    _knownproperties=common_calendar.FilterDataObject._knownproperties+\
                      ['name', 'type', 'source_id', 'option' ]
    _knownlistproperties=common_calendar.FilterDataObject._knownlistproperties
    allproperties=_knownproperties+\
                    [x for x in _knownlistproperties]+\
                    [x for x in common_calendar.FilterDataObject._knowndictproperties]
importcalendarobjectfactory=database.dataobjectfactory(ImportCalendarDataObject)

#-------------------------------------------------------------------------------
class ImportCalendarEntry(dict):
    # a dict class that automatically generates an ID for use with
    # BitPim database.

    def __init__(self, data=None):
        super(ImportCalendarEntry, self).__init__()
        if data:
            self.update(data)

    _persistrandom=random.Random()
    def _create_id(self):
        "Create a BitPim serial for this entry"
        rand2=random.Random() # this random is seeded when this function is called
        num=sha.new()
        num.update(`self._persistrandom.random()`)
        num.update(`rand2.random()`)
        return num.hexdigest()
    def _get_id(self):
        s=self.get('serials', [])
        _id=None
        for n in s:
            if n.get('sourcetype', None)=='bitpim':
                _id=n.get('id', None)
                break
        if not _id:
            _id=self._create_id()
            self._set_id(_id)
        return _id
    def _set_id(self, id):
        s=self.get('serials', [])
        for n in s:
            if n.get('sourcetype', None)=='bitpim':
                n['id']=id
                return
        self.setdefault('serials', []).append({'sourcetype': 'bitpim', 'id': id } )
    id=property(fget=_get_id, fset=_set_id)

    def validate_properties(self):
        # validate and remove non-persistent properties as defined in
        # ImportCalendarDataObject class
        _del_keys=[x for x in self \
                   if not x in ImportCalendarDataObject.allproperties]
        for _key in  _del_keys:
            del self[_key]

#-------------------------------------------------------------------------------
class FilterDialog(common_calendar.FilterDialog):
    def __init__(self, parent, id, caption, data):
        super(FilterDialog, self).__init__(parent, id, caption, [])
        self.set(data)

    def _get_from_fs(self):
        pass
    def _save_to_fs(self, data):
        pass

#-------------------------------------------------------------------------------
class PresetNamePage(setphone_wizard.MyPage):
    def __init__(self, parent):
        super(PresetNamePage, self).__init__(parent,
                                             'Calendar Import Preset Name')

    def GetMyControls(self):
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(wx.StaticText(self, -1, 'Preset Name:'), 0,
                wx.ALL|wx.EXPAND, 5)
        self._name=wx.TextCtrl(self, -1, '')
        vbs.Add(self._name, 0, wx.ALL|wx.EXPAND, 5)
        return vbs

    def ok(self):
        return bool(self._name.GetValue())
    def get(self, data):
        data['name']=self._name.GetValue()
    def set(self, data):
        self._name.SetValue(data.get('name', ''))

#-------------------------------------------------------------------------------
class PresetFilterPage(setphone_wizard.MyPage):
    def __init__(self, parent):
        self._data={}
        super(PresetFilterPage, self).__init__(parent,
                                               'Calendar Preset Filter')
    _col_names=({ 'label': 'Start Date:', 'attr': '_start' },
                { 'label': 'End Date:', 'attr': '_end' },
                { 'label': 'Preset Duration:', 'attr': '_preset' },
                { 'label': 'Repeat Events:', 'attr': '_repeat' },
                { 'label': 'Alarm Setting:', 'attr': '_alarm' },
                { 'label': 'Alarm Vibrate:', 'attr': '_vibrate' },
                { 'label': 'Alarm Ringtone:', 'attr': '_ringtone' },
                { 'label': 'Alarm Value:', 'attr': '_alarm_value' },
                )
    def GetMyControls(self):
        gs=wx.GridBagSizer(5, 10)
        gs.AddGrowableCol(1)
        for _row, _col in enumerate(PresetFilterPage._col_names):
            gs.Add(wx.StaticText(self, -1, _col['label']),
                   pos=(_row, 0), flag=wx.ALIGN_CENTER_VERTICAL)
            _w=wx.StaticText(self, -1, _col['attr'])
            setattr(self, _col['attr'], _w)
            gs.Add(_w, pos=(_row, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        _btn=wx.Button(self, -1, 'Modify')
        wx.EVT_BUTTON(self, _btn.GetId(), self._OnFilter)
        gs.Add(_btn, pos=(_row+1, 0))
        return gs

    def _OnFilter(self, _):
        with guihelper.WXDialogWrapper(FilterDialog(self, -1, 'Filtering Parameters', self._data),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self._data.update(dlg.get())
                self._populate()

    def _display(self, key, attr, fmt):
        # display the value field of this key
        _v=self._data.get(key, None)
        getattr(self, attr).SetLabel(_v is not None and eval(fmt) or '')
    def _populate(self):
        # populate the display with the filter parameters
        if self._data.get('preset_date', None) is None:
            _fmt="'%04d/%02d/%02d'%(_v[0], _v[1], _v[2])"
        else:
            _fmt="'<Preset>'"
        self._display('start', '_start', _fmt)
        self._display('end', '_end', _fmt)
        self._display('preset_date', '_preset',
                      "['This Week', 'This Month', 'This Year', 'Next 7 Days'][_v]")
        self._display('rpt_events', '_repeat',
                      "{ True: 'Import as mutil-single events', False: ''}[_v]")
        if self._data.get('no_alarm', None):
            _s='Disable All Alarms'
        elif self._data.get('alarm_override', None):
            _s='Set Alarm on All Events'
        else:
            _s='Use Alarm Settings from Import Source'
        self._alarm.SetLabel(_s)
        self._display('vibrate', '_vibrate',
                      "{ True: 'Enable Vibrate for Alarms', False: ''}[_v]")
        self._display('ringtone', '_ringtone', "'%s'%((_v != 'Select:') and _v or '',)")
        self._display('alarm_value', '_alarm_value', "'%d'%_v")
    def get(self, data):
        data.update(self._data)
    def set(self, data):
        self._data=data
        self._populate()

#-------------------------------------------------------------------------------
class ImportOptionPage(imp_cal_wizard.ImportOptionPage):
    _choices=('Replace All', 'Add', 'Preview', 'Merge')

#-------------------------------------------------------------------------------
class ImportCalendarPresetWizard(wiz.Wizard):
    ID_ADD=wx.NewId()
    def __init__(self, parent, entry,
                 id=-1, title='Calendar Import Preset Wizard'):
        super(ImportCalendarPresetWizard, self).__init__(parent, id, title)
        self._data=entry
        _import_name_page=PresetNamePage(self)
        _import_type_page=imp_cal_wizard.ImportTypePage(self)
        _import_source_page=imp_cal_wizard.ImportSourcePage(self)
        _import_filter_page=PresetFilterPage(self)
        _import_option=ImportOptionPage(self)

        wiz.WizardPageSimple_Chain(_import_name_page, _import_type_page)
        wiz.WizardPageSimple_Chain(_import_type_page, _import_source_page)
        wiz.WizardPageSimple_Chain(_import_source_page, _import_filter_page)
        wiz.WizardPageSimple_Chain(_import_filter_page, _import_option)
        self.first_page=_import_name_page
        self.GetPageAreaSizer().Add(self.first_page, 1, wx.EXPAND|wx.ALL, 5)
        wiz.EVT_WIZARD_PAGE_CHANGING(self, self.GetId(), self.OnPageChanging)
        wiz.EVT_WIZARD_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)

    def RunWizard(self, firstPage=None):
        return super(ImportCalendarPresetWizard, self).RunWizard(firstPage or self.first_page)

    def OnPageChanging(self, evt):
        pg=evt.GetPage()
        if not evt.GetDirection() or pg.ok():
            pg.get(self._data)
        else:
            evt.Veto()

    def OnPageChanged(self, evt):
        evt.GetPage().set(self._data)

    def get(self):
        return self._data

    def GetActiveDatabase(self):
        return self.GetParent().GetActiveDatabase()

    def get_categories(self):
        if self._data.get('data_obj', None):
            return self._data['data_obj'].get_category_list()
        return []

#-------------------------------------------------------------------------------
class CalendarPreviewDialog(wx.Dialog):
    ID_ADD=wx.NewId()
    ID_REPLACE=wx.NewId()
    ID_MERGE=wx.NewId()
    def __init__(self, parent, data):
        super(CalendarPreviewDialog, self).__init__(parent, -1,
                                                    'Calendar Import Preview')
        _vbs=wx.BoxSizer(wx.VERTICAL)
        _lb=wx.ListBox(self, -1, style=wx.LB_SINGLE|wx.LB_HSCROLL|wx.LB_NEEDED_SB,
                       choices=['%04d/%02d/%02d %02d:%02d - '%x.start+x.description\
                                for _,x in data.items()])
        _vbs.Add(_lb, 0, wx.EXPAND|wx.ALL, 5)
        _vbs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        _hbs=wx.BoxSizer(wx.HORIZONTAL)
        _btn=wx.Button(self, self.ID_REPLACE, 'Replace All')
        wx.EVT_BUTTON(self, self.ID_REPLACE, self._OnButton)
        _hbs.Add(_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        _btn=wx.Button(self, self.ID_ADD, 'Add')
        wx.EVT_BUTTON(self, self.ID_ADD, self._OnButton)
        _hbs.Add(_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        _btn=wx.Button(self, self.ID_MERGE, 'Merge')
        wx.EVT_BUTTON(self, self.ID_MERGE, self._OnButton)
        _hbs.Add(_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        _hbs.Add(wx.Button(self, wx.ID_CANCEL, 'Cancel'), 0,
                 wx.ALIGN_CENTRE|wx.ALL, 5)
        _vbs.Add(_hbs, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(_vbs)
        self.SetAutoLayout(True)
        _vbs.Fit(self)

    def _OnButton(self, evt):
        self.EndModal(evt.GetId())

#-------------------------------------------------------------------------------
class ImportCalendarPresetDialog(wx.Dialog):
    ID_ADD=wx.NewId()
    ID_MERGE=wx.NewId()

    def __init__(self, parent, id, title):
        self._parent=parent
        self._data={}
        self._import_data=None
        self._buttons=[]
        super(ImportCalendarPresetDialog, self).__init__(parent, id,
                                                         title,
                                                         size=(500, 500))
        _vbs=wx.BoxSizer(wx.VERTICAL)
        _static_bs=wx.StaticBoxSizer(wx.StaticBox(self, -1,
                                                  'Available Presets:'),
                                     wx.VERTICAL)
        self._name_lb=wx.ListBox(self, -1, style=wx.LB_SINGLE|wx.LB_NEEDED_SB)
        wx.EVT_LISTBOX(self, self._name_lb.GetId(), self._set_button_states)
        _static_bs.Add(self._name_lb, 0, wx.EXPAND|wx.ALL, 5)
        _vbs.Add(_static_bs, 0, wx.EXPAND|wx.ALL, 5)
        _vbs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        _hbs=wx.BoxSizer(wx.HORIZONTAL)
        _btn=wx.Button(self, -1, 'Import')
        wx.EVT_BUTTON(self, _btn.GetId(), self._OnRun)
        self._buttons.append(_btn)
        _hbs.Add(_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        _btn=wx.Button(self, wx.ID_NEW)
        wx.EVT_BUTTON(self, _btn.GetId(), self._OnNew)
        _hbs.Add(_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        _btn=wx.Button(self, -1, 'Edit')
        wx.EVT_BUTTON(self, _btn.GetId(), self._OnEdit)
        self._buttons.append(_btn)
        _hbs.Add(_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        _btn=wx.Button(self, wx.ID_DELETE)
        self._buttons.append(_btn)
        wx.EVT_BUTTON(self, _btn.GetId(), self._OnDel)
        _hbs.Add(_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        _hbs.Add(wx.Button(self, wx.ID_CANCEL),
                 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        _vbs.Add(_hbs, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.SetSizerAndFit(_vbs)
        if guihelper.IsGtk():
            # On Linux, without this, the dialog clips the buttons
            self.SetSizeHints(-1, 175)
        self._get_from_fs()
        self._populate()

    def _set_button_states(self, _=None):
        # set the appropriate states of the buttons depending on whether a
        # listbox item is selected or not
        _flg=self._name_lb.GetSelection()!=wx.NOT_FOUND
        [x.Enable(_flg) for x in self._buttons]

    def _preview_data(self):
        # Display a preview of data just imported
        with guihelper.WXDialogWrapper(CalendarPreviewDialog(self, self._import_data.get()),
                                       True) as (_dlg, _ret_code):
            if _ret_code==CalendarPreviewDialog.ID_REPLACE:
                return wx.ID_OK
            elif _ret_code==CalendarPreviewDialog.ID_ADD:
                return self.ID_ADD
            elif _ret_code==CalendarPreviewDialog.ID_MERGE:
                return self.ID_MERGE
            return wx.ID_CANCEL

    def _get_preset_thisweek(self):
        # return the dates of (today, Sat)
        _today=datetime.date.today()
        _dow=_today.isoweekday()%7  #Sun=0, Sat=6
        _end=_today+datetime.timedelta(6-_dow)
        return ((_today.year, _today.month, _today.day),
                (_end.year, _end.month, _end.day))

    def _get_preset_thismonth(self):
        # return the dates of (today, end-of-month)
        _today=datetime.date.today()
        _end=_today.replace(day=calendar.monthrange(_today.year,_today.month)[1])
        return ((_today.year, _today.month, _today.day),
                (_end.year, _end.month, _end.day))

    def _get_preset_thisyear(self):
        # return the dates of (today, end-of-year)
        _today=datetime.date.today()
        _end=_today.replace(month=12, day=31)
        return ((_today.year, _today.month, _today.day),
                (_end.year, _end.month, _end.day))

    def _get_preset_next7(self):
        # return the dates of (today, today+6)
        _today=datetime.date.today()
        _end=_today+datetime.timedelta(days=6)
        return ((_today.year, _today.month, _today.day),
                (_end.year, _end.month, _end.day))

    def _adjust_filter_dates(self, entry):
        # Adjust the start/end dates of the filter
        _preset_date=entry.get('preset_date', None)
        if _preset_date is None:
            # No Preset date, bail
            return
        entry['start'], entry['end']=getattr(self,
                                             ['_get_preset_thisweek',
                                              '_get_preset_thismonth',
                                              '_get_preset_thisyear',
                                              '_get_preset_next7'][_preset_date])()
    @guihelper.BusyWrapper
    def _OnRun(self, _):
        _idx=self._name_lb.GetSelection()
        if _idx==wx.NOT_FOUND:
            return
        _entry=self._data[self._name_lb.GetClientData(_idx)]
        _my_type=_entry['type']
        _info=[x for x in importexport.GetCalendarImports() \
               if x['type']==_my_type]
        if not _info:
            return
        _info=_info[0]
        self._import_data=_info['data']()
        _source=_info['source']()
        _source.id=_entry['source_id']
        with guihelper.WXDialogWrapper(wx.ProgressDialog('Calendar Data Import',
                                                         'Importing data, please wait ...',
                                                         parent=self)) as _dlg:
            self._import_data.read(_source.get(), _dlg)
            self._adjust_filter_dates(_entry)
            self._import_data.set_filter(_entry)
        global IMP_OPTION_PREVIEW, IMP_OPTION_REPLACEALL, IMP_OPTION_ADD, IMP_OPTION_MERGE
        _option=_entry.get('option', IMP_OPTION_PREVIEW)
        if _option==IMP_OPTION_PREVIEW:
            _ret_code=self._preview_data()
        elif _option==IMP_OPTION_ADD:
            _ret_code=self.ID_ADD
        elif _option==IMP_OPTION_MERGE:
            _ret_code=self.ID_MERGE
        else:
            _ret_code=wx.ID_OK
        self.EndModal(_ret_code)

    def _OnNew(self, _):
        _entry=ImportCalendarEntry()
        with guihelper.WXDialogWrapper(ImportCalendarPresetWizard(self, _entry)) \
             as _wiz:
            if _wiz.RunWizard():
                _entry=_wiz.get()
                self._data[_entry.id]=_entry
                self._save_to_fs()
                self._populate()
    def _OnEdit(self, _):
        _idx=self._name_lb.GetSelection()
        if _idx==wx.NOT_FOUND:
            return
        _key=self._name_lb.GetClientData(_idx)
        _entry=self._data[_key].copy()
        with guihelper.WXDialogWrapper(ImportCalendarPresetWizard(self, _entry)) \
             as _wiz:
            if _wiz.RunWizard():
                _entry=ImportCalendarEntry(_wiz.get())
                del self._data[_key]
                self._data[_entry.id]=_entry
                self._save_to_fs()
                self._populate()
    def _OnDel(self, _):
        _idx=self._name_lb.GetSelection()
        if _idx==wx.NOT_FOUND:
            return
        _key=self._name_lb.GetClientData(_idx)
        del self._data[_key]
        self._save_to_fs()
        self._populate()

    def _populate(self):
        # populate the listbox with the name of the presets
        self._name_lb.Clear()
        for _key, _entry in self._data.items():
            self._name_lb.Append(_entry['name'], _key)
        self._set_button_states()

    def _expand_item(self, entry):
        item={}
        item.update(entry)
        if item.has_key('categories'):
            del item['categories']
        if item.has_key('start'):
            del item['start']
            if entry['start']:
                item['start']=[{'year': entry['start'][0],
                                'month': entry['start'][1],
                                'day': entry['start'][2] }]
        if item.has_key('end'):
            del item['end']
            if entry['end']:
                item['end']=[{'year': entry['end'][0],
                              'month': entry['end'][1],
                              'day': entry['end'][2] }]
        return item
    def _collapse_item(self, entry):
        item={}
        item.update(entry)
        item['categories']=None
        if item.has_key('start') and item['start']:
            _d0=item['start'][0]
            item['start']=(_d0['year'], _d0['month'], _d0['day'])
        else:
            item['start']=None
        if item.has_key('end') and item['end']:
            _d0=entry['end'][0]
            item['end']=(_d0['year'], _d0['month'], _d0['day'])
        else:
            item['end']=None
        return item

    def _get_from_fs(self):
        # read the presets data from DB
        _data=self._parent.GetActiveDatabase().getmajordictvalues('imp_cal_preset',
                                                                  importcalendarobjectfactory)
        self._data={}
        for _, _val in _data.items():
            _entry=ImportCalendarEntry(self._collapse_item(_val))
            self._data[_entry.id]=_entry
        self._populate()

    def _save_to_fs(self):
        _data={}
        for _key, _entry in self._data.items():
            _entry.validate_properties()
            _data[_key]=self._expand_item(_entry)
        database.ensurerecordtype(_data, importcalendarobjectfactory)
        self._parent.GetActiveDatabase().savemajordict('imp_cal_preset',
                                                       _data)

    def get(self):
        if self._import_data:
            return self._import_data.get()
        return {}

    def get_categories(self):
        if self._import_data:
            return self._import_data.get_category_list()
        return []

    def GetActiveDatabase(self):
        return self._parent.GetActiveDatabase()

#-------------------------------------------------------------------------------
# Testing
if __name__=="__main__":
    app=wx.PySimpleApp()
    f=wx.Frame(None, title='imp_cal_preset')
    _data=ImportCalendarEntry()
    _data.id
    with guihelper.WXDialogWrapper(ImportCalendarPresetWizard(f, _data)) \
         as w:
        print 'RunWizard:',w.RunWizard()
        print 'Data:',w.get()
