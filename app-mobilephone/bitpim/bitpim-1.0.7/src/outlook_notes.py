### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: outlook_notes.py 2703 2005-12-29 09:21:18Z djpham $

"Deals with Outlook Notes import stuff"

# System modules

# wxPython modules
import wx

# BitPim modules
import common_calendar
import memo
import outlook_calendar

#-------------------------------------------------------------------------------
class OutlookNotesImportData(outlook_calendar.OutlookCalendarImportData):
    _data_keys=[
        # (Outlook field, MemoEntry field, convertor function)
        ('Subject', 'subject', None),
        ('Body', 'text', None),
        ('Categories', 'categories', outlook_calendar.convert_categories),
        ('LastModificationTime', 'date', outlook_calendar.to_bp_date),
        ]
    _default_filter={
        'start': None,
        'end': None,
        'categories': None,
        }
    _data_item_class=memo.MemoEntry
    _default_folder_type='notes'

    def __init__(self, outlook):
        self._outlook=outlook
        self._data=[]
        self._error_list=[]
        self._folder=None
        self._filter=self._default_filter
        self._total_count=0
        self._current_count=0
        self._update_dlg=None

    def _accept(self, e):
        # check for the date
        _date=e['date'][:3]
        if self._filter['start'] is not None and \
           _date<self._filter['start'][:3]:
            return False
        if self._filter['end'] is not None and \
           _date>self._filter['end'][:3]:
            return False
        c=self._filter.get('categories', None)
        if not c:
            # no categories specified => all catefories allowed.
            return True
        if [x for x in e['categories'] if x in c]:
            return True
        return False

    def _populate_entry(self, entry, memo_entry):
        memo_entry.subject=entry.get('subject', None)
        memo_entry.text=entry.get('text', '')
        if entry.get('date', None):
            memo_entry.set_date_isostr('%04d%02d%02dT%02d%02d00'%entry['date'])
        v=[]
        for k in entry.get('categories', []):
            v.append({ 'category': k })
        memo_entry.categories=v

    def get(self):
        res={}
        for k in self._data:
            if self._accept(k):
                _e=self._data_item_class()
                self._populate_entry(k, _e)
                res[_e.id]=_e
        return res

    def get_display_data(self):
        cnt=0
        res={}
        for k in self._data:
            if self._accept(k):
                res[cnt]=k
                cnt+=1
        return res

    def read_update(self, item, dict, data_obj):
        self._current_count += 1
        if self._update_dlg:
            self._update_dlg.Update(100*self._current_count/self._total_count)
        return True

    def read(self, folder=None, update_flg=None):
        # folder from which to read
        if folder is not None:
            self._folder=folder
        if self._folder is None:
            self._folder=self._outlook.getfolderfromid('', True,
                                                       self._default_folder_type)
        self._update_dlg=update_flg
        self._total_count=self._folder.Items.Count
        self._current_count=0
        self._data, self._error_list=self._outlook.getdata(self._folder,
                                                           self._data_keys,
                                                           {}, self,
                                                           self.read_update)

    def set_folder(self, f):
        if f is None:
            # default folder
            self._folder=self._outlook.getfolderfromid('', True,
                                                       self._default_folder_type)
        else:
            self._folder=f

#-------------------------------------------------------------------------------
class FilterDialog(wx.Dialog):

    _has_complete_option=False

    def __init__(self, parent, id, caption, categories,
                 style=wx.DEFAULT_DIALOG_STYLE):
        super(FilterDialog, self).__init__(parent, id, title=caption,
                                           style=style)
        # the main box sizer
        bs=wx.BoxSizer(wx.VERTICAL)
        # the flex grid sizers for the editable items
        main_fgs=wx.FlexGridSizer(0, 1, 0, 0)
        fgs=wx.FlexGridSizer(3, 2, 0, 5)
        fgs1=wx.FlexGridSizer(0, 1, 0, 0)
        fgs2=wx.FlexGridSizer(0, 2, 0, 5)
        # set the date options
        self.SetDateControls(fgs, fgs1)
        # category option
        self.__cat_chkbox=wx.CheckBox(self, id=wx.NewId(), label='Categories:',
                                      style=wx.ALIGN_RIGHT)
        fgs2.Add(self.__cat_chkbox, 0, wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM, 5)
        for i,c in enumerate(categories):
            if not len(c):
                categories[i]='<None>'
        self.__cats=wx.CheckListBox(self, choices=categories, size=(160, 50))
        self.__cats.Disable()
        fgs2.Add(self.__cats, 0, wx.ALIGN_LEFT, 0)
        # completed items only option
        if self._has_complete_option:
            self._complete_chkbox=wx.CheckBox(self, -1, label='',
                                              style=wx.ALIGN_RIGHT)
            fgs2.Add(self._complete_chkbox, 0, wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM, 5)
            fgs2.Add(wx.StaticText(self, -1, 'Non-completed Items Only'),
                     0, wx.ALIGN_LEFT, 0)
        # add everything to the main sizer
        main_fgs.Add(fgs, 1, wx.EXPAND|wx.ALL, 0)
        main_fgs.Add(fgs1, 1, wx.EXPAND|wx.ALL, 0)
        main_fgs.Add(fgs2, 1, wx.EXPAND|wx.ALL, 0)
        bs.Add(main_fgs, 1, wx.EXPAND|wx.ALL, 5)
        # the buttons
        bs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        bs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        # event handles
        wx.EVT_CHECKBOX(self, self._start_date_chkbox.GetId(), self.OnCheckBox)
        wx.EVT_CHECKBOX(self, self._end_date_chkbox.GetId(), self.OnCheckBox)
        wx.EVT_CHECKBOX(self, self.__cat_chkbox.GetId(), self.OnCheckBox)
        # all done
        self.SetSizer(bs)
        self.SetAutoLayout(True)
        bs.Fit(self)

    def _set_cats(self, chk_box, c, data):
        if data is None:
            chk_box.SetValue(False)
            c.Disable()
        else:
            chk_box.SetValue(True)
            c.Enable()
            for i,d in enumerate(data):
                if not len(d):
                    data[i]='<None>'
            for i in range(c.GetCount()):
                c.Check(i, c.GetString(i) in data)

    def OnCheckBox(self, evt):
        evt_id=evt.GetId()
        if evt_id==self._start_date_chkbox.GetId():
            w1,w2=self._start_date_chkbox, self._start_date
        elif evt_id==self._end_date_chkbox.GetId():
            w1,w2=self._end_date_chkbox, self._end_date
        else:
            w1,w2=self.__cat_chkbox, self.__cats
        if w1.GetValue():
            w2.Enable()
        else:
            w2.Disable()

    def SetDateControls(self, fgs, fgs1):
        self._start_date_chkbox=wx.CheckBox(self, id=wx.NewId(), 
                                             label='Start Date:',
                                             style=wx.ALIGN_RIGHT)
        fgs.Add(self._start_date_chkbox, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL, 0)
        self._start_date=wx.calendar.CalendarCtrl(self, -1, wx.DateTime_Now(),
                                          style = wx.calendar.CAL_SUNDAY_FIRST
                                          | wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION)
        self._start_date.Disable()
        fgs.Add(self._start_date, 1, wx.ALIGN_LEFT, 5)
        self._end_date_chkbox=wx.CheckBox(self, id=wx.NewId(),
                                           label='End Date:',
                                           style=wx.ALIGN_RIGHT)
        fgs.Add(self._end_date_chkbox, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL, 0)
        self._end_date=wx.calendar.CalendarCtrl(self, -1, wx.DateTime_Now(),
                                          style = wx.calendar.CAL_SUNDAY_FIRST
                                          | wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION)
        self._end_date.Disable()
        fgs.Add(self._end_date, 1, wx.ALIGN_LEFT, 5)

    def _set_date(self, chk_box, cal, d):
        if d is None:
            chk_box.SetValue(False)
            cal.Disable()
        else:
            chk_box.SetValue(True)
            cal.Enable()
            dt=wx.DateTime()
            dt.Set(d[2], year=d[0], month=d[1]-1)
            cal.SetDate(dt)

    def _set_complete(self, v):
        if self._has_complete_option:
            self._complete_chkbox.SetValue(v)

    def set(self, data):
        self._set_date(self._start_date_chkbox, self._start_date,
                        data.get('start', None))
        self._set_date(self._end_date_chkbox, self._end_date,
                        data.get('end', None))
        self._set_cats(self.__cat_chkbox, self.__cats,
                       data.get('categories', None))
        self._set_complete(data.get('non_completed', False))

    def get(self):
        r={}
        if self._start_date_chkbox.GetValue():
            dt=self._start_date.GetDate()
            r['start']=(dt.GetYear(), dt.GetMonth()+1, dt.GetDay())
        else:
            r['start']=None
        if self._end_date_chkbox.GetValue():
            dt=self._end_date.GetDate()
            r['end']=(dt.GetYear(), dt.GetMonth()+1, dt.GetDay())
        else:
            r['end']=None
        if self.__cat_chkbox.GetValue():
            c=[]
            for i in range(self.__cats.GetCount()):
                if self.__cats.IsChecked(i):
                    s=self.__cats.GetString(i)
                    if s=='<None>':
                        c.append('')
                    else:
                        c.append(s)
            r['categories']=c
        else:
            r['categories']=None
        if self._has_complete_option:
            r['non_completed']=self._complete_chkbox.GetValue()
        return r

#-------------------------------------------------------------------------------

class OutlookImportNotesDialog(outlook_calendar.OutlookImportCalDialog):
    _column_labels=[
        ('date', 'Last Changed Date', 200, common_calendar.bp_date_str),
        ('subject', 'Subject', 400, None),
        ('categories', 'Category', 200, common_calendar.category_str)
        ]

    _config_name='import/notes/outlookdialog'
    _browse_label='Outlook Notes Folder:'
    _progress_dlg_title='Outlook Notes Import'
    _error_dlg_title='Outlook Notes Import Error'
    _error_dlg_text='Outlook Notes Items that failed to import:'
    _data_class=OutlookNotesImportData
    _filter_dlg_class=FilterDialog
