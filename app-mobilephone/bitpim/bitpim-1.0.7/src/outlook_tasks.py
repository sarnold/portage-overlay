### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: outlook_tasks.py 2703 2005-12-29 09:21:18Z djpham $

"Deals with Outlook Tasks import stuff"

# System modules

# wxPython modules
import wx

# BitPim modules
import common_calendar
import native.outlook as ol
import outlook_calendar
import outlook_notes
import todo

#-------------------------------------------------------------------------------
# convertor funcs
_outlook_status={
    ol.outlook_com.constants.olTaskNotStarted: todo.TodoEntry.ST_NotStarted,
    ol.outlook_com.constants.olTaskInProgress: todo.TodoEntry.ST_InProgress,
    ol.outlook_com.constants.olTaskComplete: todo.TodoEntry.ST_Completed,
    ol.outlook_com.constants.olTaskWaiting: todo.TodoEntry.ST_NeedActions,
    ol.outlook_com.constants.olTaskDeferred: todo.TodoEntry.ST_Cancelled }

_outlook_priority={
    ol.outlook_com.constants.olImportanceLow: 10,
    ol.outlook_com.constants.olImportanceNormal: 5,
    ol.outlook_com.constants.olImportanceHigh: 1 }

def _convert_status(dict, v, obj):
    return _outlook_status.get(v, None)
def _convert_priority(dict, v, obj):
    return _outlook_priority.get(v, 5)

def bp_date_str(dict, v):
    try:
        if v[0]>=common_calendar.no_end_date[0]:
            # no-end date, don't display it
            return ''
        return '%04d-%02d-%02d'% v[:3]
    except (ValueError, TypeError):
        return ''
    except:
        if __debug__: raise
        return ''

def status_str(dict, v):
    if v:
        return todo.TodoEntry.ST_Names[v]
    else:
        return ''

#-------------------------------------------------------------------------------
class OutlookTasksImportData(outlook_notes.OutlookNotesImportData):

    _data_keys=[
        # (Outlook field, MemoEntry field, convertor function)
        ('Status', 'status', _convert_status),
        ('DateCompleted', 'completion_date', outlook_calendar.to_bp_date),
        ('Complete', 'complete', None),
        ('Importance', 'priority', _convert_priority),
        ('PercentComplete', 'percent_complete', None),
        ('DueDate', 'due_date', outlook_calendar.to_bp_date),
        ('Subject', 'summary', None),
        ('Body', 'note', None),
        ('Categories', 'categories', outlook_calendar.convert_categories),
        ]

    _default_filter={
        'start': None,
        'end': None,
        'categories': None,
        'non_completed': False,
        }

    _data_item_class=todo.TodoEntry
    _default_folder_type='tasks'

    def __init__(self, outlook):
        outlook_notes.OutlookNotesImportData.__init__(self, outlook)

    def _accept(self, e):
        # check for Completed tasks
        if self._filter['non_completed'] and e['complete']:
            return False
        # check for the due date
        if e['due_date']!=common_calendar.no_end_date:
            _date=e['due_date'][:3]
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

    def _populate_entry(self, entry, new_entry):
        new_entry.status=entry.get('status', todo.TodoEntry.ST_NotStarted)
        if entry['completion_date']!=common_calendar.no_end_date:
            new_entry.completion_date='%04d%02d%02d'%entry['completion_date'][:3]
        new_entry.priority=entry.get('priority', 5)
        new_entry.percent_complete=entry.get('percent_complete', 0)
        if entry['due_date']!=common_calendar.no_end_date:
            new_entry.due_date='%04d%02d%02d'%entry['due_date'][:3]
        new_entry.summary=entry.get('summary', None)
        new_entry.note=entry.get('note', None)
        v=[]
        for k in entry.get('categories', []):
            v.append({ 'category': k })
        new_entry.categories=v

#-------------------------------------------------------------------------------
class FilterDialog(outlook_notes.FilterDialog):
    _has_complete_option=True

#-------------------------------------------------------------------------------
class OutlookImportTasksDialog(outlook_calendar.OutlookImportCalDialog):
    _column_labels=[
        ('due_date', 'Due Date', 200, bp_date_str),
        ('summary', 'Summary', 400, None),
        ('status', 'Status', 200, status_str),
        ('categories', 'Category', 200, common_calendar.category_str)
        ]

    _config_name='import/tasks/outlookdialog'
    _browse_label='Outlook Tasks Folder:'
    _progress_dlg_title='Outlook Tasks Import'
    _error_dlg_title='Outlook Tasks Import Error'
    _error_dlg_text='Outlook Tasks Items that failed to import:'
    _data_class=OutlookTasksImportData
    _filter_dlg_class=FilterDialog
