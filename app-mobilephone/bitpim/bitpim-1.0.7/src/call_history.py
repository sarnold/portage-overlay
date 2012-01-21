### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: call_history.py 4601 2008-03-04 22:37:48Z djpham $

"""
Code to handle Call History data storage and display.

The format of the Call History is standardized.  It is an object with the
following attributes:

folder: string (where this item belongs)
datetime: string 'YYYYMMDDThhmmss' or (y,m,d,h,m,s)
number: string (the phone number of this call)
name: string (optional name associated with this number)
duration: int (optional duration of the call in minutes)

To implement Call History feature for a phone module:

  Add an entry into Profile._supportedsyncs:
  ('call_history', 'read', None),

  Implement the following method in your Phone class:
  def getcallhistory(self, result, merge):
     ...
     return result

The result dict key is 'call_history'.

"""

# standard modules
from __future__ import with_statement
import copy
import sha
import time

# wx modules
import wx
import wx.lib.scrolledpanel as scrolled

# BitPim modules
import database
import guiwidgets
import guihelper
import helpids
import phonenumber
import pubsub
import today
import widgets

#-------------------------------------------------------------------------------
class CallHistoryDataobject(database.basedataobject):
    _knownproperties=['folder', 'datetime', 'number', 'name', 'duration' ]
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    def __init__(self, data=None):
        if data is None or not isinstance(data, CallHistoryEntry):
            return;
        self.update(data.get_db_dict())
callhistoryobjectfactory=database.dataobjectfactory(CallHistoryDataobject)

#-------------------------------------------------------------------------------
def GetDurationStr(duration):
    """convert duration int into an h:mm:ss formatted string"""
    if duration is None:
        return ''
    else:
        sec=duration%60
        min=duration/60
        hr=min/60
        min=min%60
    return "%d:%02d:%02d" % (hr, min, sec)

#-------------------------------------------------------------------------------
class CallHistoryEntry(object):
    Folder_Incoming='Incoming'
    Folder_Outgoing='Outgoing'
    Folder_Missed='Missed'
    Folder_Data='Data'
    Valid_Folders=(Folder_Incoming, Folder_Outgoing, Folder_Missed, Folder_Data)
    _folder_key='folder'
    _datetime_key='datetime'
    _number_key='number'
    _name_key='name'
    _duration_key='duration'
    _unknown_datetime='YYYY-MM-DD hh:mm:ss'
    _id_index=0
    _max_id_index=999
    def __init__(self):
        self._data={ 'serials': [] }
        self._create_id()

    def __eq__(self, rhs):
        return self.folder==rhs.folder and self.datetime==rhs.datetime and\
               self.number==rhs.number
    def __ne__(self, rhs):
        return self.folder!=rhs.folder or self.datetime!=rhs.datetime or\
               self.number!=rhs.number
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
             "id": '%.3f%03d'%(time.time(), CallHistoryEntry._id_index) })
        if CallHistoryEntry._id_index<CallHistoryEntry._max_id_index:
            CallHistoryEntry._id_index+=1
        else:
            CallHistoryEntry._id_index=0
    def _get_id(self):
        s=self._data.get('serials', [])
        for n in s:
            if n.get('sourcetype', None)=='bitpim':
                return n.get('id', None)
        return None
    def _set_id(self, id):
        s=self._data.get('serials', [])
        for n in s:
            if n.get('sourcetype', None)=='bitpim':
                n['id']=id
                return
        self._data['serials'].append({'sourcetype': 'bitpim', 'id': id } )
    id=property(fget=_get_id, fset=_set_id)

    def _set_or_del(self, key, v, v_list=[]):
        if v is None or v in v_list:
            if self._data.has_key(key):
                del self._data[key]
        else:
            self._data[key]=v

    def _get_folder(self):
        return self._data.get(self._folder_key, '')
    def _set_folder(self, v):
        if v is None:
            if self._data.has_key(self._folder_key):
                del self._data[self._folder_key]
                return
        if not isinstance(v, (str, unicode)):
            raise TypeError,'not a string or unicode type'
        if v not in self.Valid_Folders:
            raise ValueError,'not a valid folder'
        self._data[self._folder_key]=v
    folder=property(fget=_get_folder, fset=_set_folder)

    def _get_number(self):
        return self._data.get(self._number_key, '')
    def _set_number(self, v):
        self._set_or_del(self._number_key, v, [''])
    number=property(fget=_get_number, fset=_set_number)

    def _get_name(self):
        return self._data.get(self._name_key, '')
    def _set_name(self, v):
        self._set_or_del(self._name_key, v, ('',))
    name=property(fget=_get_name, fset=_set_name)

    def _get_duration(self):
        return self._data.get(self._duration_key, None)
    def _set_duration(self, v):
        if v is not None and not isinstance(v, int):
            raise TypeError('duration property is an int arg')
        self._set_or_del(self._duration_key, v)
    def _get_durationstr(self):
        return GetDurationStr(self.duration)
    duration=property(fget=_get_duration, fset=_set_duration)
    durationstr=property(fget=_get_durationstr)
    

    def _get_datetime(self):
        return self._data.get(self._datetime_key, '')
    def _set_datetime(self, v):
        # this routine supports 2 formats:
        # (y,m,d,h,m,s) and 'YYYYMMDDThhmmss'
        # check for None and delete manually
        if v is None:
            if self._data.has_key(self._datetime_key):
                del self._data[self._datetime_key]
            return
        if isinstance(v, (tuple, list)):
            if len(v)!=6:
                raise ValueError,'(y, m, d, h, m, s)'
            s='%04d%02d%02dT%02d%02d%02d'%tuple(v)
        elif isinstance(v, (str, unicode)):
            # some primitive validation
            if len(v)!=15 or v[8]!='T':
                raise ValueError,'value must be in format YYYYMMDDThhmmss'
            s=v
        else:
            raise TypeError
        self._data[self._datetime_key]=s
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
    def summary(self, name=None):
        # return a short summary for this entry in the format of
        # MM/DD hh:mm <Number/Name>
        s=self.datetime
        if s:
            s=s[4:6]+'/'+s[6:8]+' '+s[9:11]+':'+s[11:13]+' '
        else:
            s='**/** **:** '
        if name:
            s+=name
        elif self.name:
            s+=self.name
        else:
            s+=phonenumber.format(self.number)
        return s

#-------------------------------------------------------------------------------
class CallHistoryWidget(scrolled.ScrolledPanel, widgets.BitPimWidget):
    _data_key='call_history'
    stat_list=("Data", "Missed", "Incoming", "Outgoing", "All")
    def __init__(self, mainwindow, parent):
        super(CallHistoryWidget, self).__init__(parent, -1)
        self._main_window=mainwindow
        self.call_history_tree_nodes={}
        self._parent=parent
        self.read_only=False
        self.historical_date=None
        self._data={}
        self._name_map={}
        pubsub.subscribe(self._OnPBLookup, pubsub.RESPONSE_PB_LOOKUP)
        self.list_widget=CallHistoryList(self._main_window, self._parent, self)
        # main box sizer
        vbs=wx.BoxSizer(wx.VERTICAL)
        # data date adjuster
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        static_bs=wx.StaticBoxSizer(wx.StaticBox(self, -1,
                                                 'Historical Data Status:'),
                                    wx.VERTICAL)
        self.historical_data_label=wx.StaticText(self, -1, 'Current Data')
        static_bs.Add(self.historical_data_label, 1, wx.EXPAND|wx.ALL, 5)
        hbs.Add(static_bs, 1, wx.EXPAND|wx.ALL, 5)
        vbs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)
        # main stats display
        self.total_calls=today.HyperLinkCtrl(self, -1, '  Total Calls: 0')
        today.EVT_HYPERLINK_LEFT(self, self.total_calls.GetId(),
                                 self.OnNodeSelection)
        self.total_in=today.HyperLinkCtrl(self, -1, '  Incoming Calls: 0')
        today.EVT_HYPERLINK_LEFT(self, self.total_in.GetId(),
                                 self.OnNodeSelection)
        self.total_out=today.HyperLinkCtrl(self, -1, '  Outgoing Calls: 0')
        today.EVT_HYPERLINK_LEFT(self, self.total_out.GetId(),
                                 self.OnNodeSelection)
        self.total_missed=today.HyperLinkCtrl(self, -1, '  Missed Calls: 0')
        today.EVT_HYPERLINK_LEFT(self, self.total_missed.GetId(),
                                 self.OnNodeSelection)
        self.total_data=today.HyperLinkCtrl(self, -1, '  Data Calls: 0')
        today.EVT_HYPERLINK_LEFT(self, self.total_data.GetId(),
                                 self.OnNodeSelection)
        self.duration_all=wx.StaticText(self, -1, '  Total Duration(h:m:s): 0')
        self.duration_in=wx.StaticText(self, -1, '  Incoming Duration(h:m:s): 0')
        self.duration_out=wx.StaticText(self, -1, '  Outgoing Duration(h:m:s): 0')
        self.duration_data=wx.StaticText(self, -1, '  Data Duration(h:m:s): 0')
        self._id_dict={
            self.total_calls.GetId(): self.stat_list[4],
            self.total_in.GetId(): self.stat_list[2],
            self.total_out.GetId(): self.stat_list[3],
            self.total_missed.GetId(): self.stat_list[1],
            self.total_data.GetId(): self.stat_list[0],
            }
        vbs.Add(wx.StaticText(self, -1, ''), 0, wx.ALIGN_LEFT|wx.ALL, 2)
        vbs.Add(self.total_calls, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        vbs.Add(self.total_in, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        vbs.Add(self.total_out, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        vbs.Add(self.total_missed, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        vbs.Add(self.total_data, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        vbs.Add(wx.StaticText(self, -1, ''), 0, wx.ALIGN_LEFT|wx.ALL, 2)
        vbs.Add(self.duration_all, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        vbs.Add(self.duration_in, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        vbs.Add(self.duration_out, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        vbs.Add(self.duration_data, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        # all done
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)
        self.SetupScrolling()
        self.SetBackgroundColour(wx.WHITE)
        # populate data
        self._populate()

    def OnNodeSelection(self, evt):
        # Request to select a subnode
        _node=self._id_dict.get(evt.GetId(), None)
        if _node and self.call_history_tree_nodes.get(_node, None):
            self.ActivateSelf(self.call_history_tree_nodes[_node])

    def populate(self, dict, force=False):
        if self.read_only and not force:
            # historical data, bail
            return
        self._data=dict.get(self._data_key, {})
        self._populate()

    def OnInit(self):
        for stat in self.stat_list:
            self.call_history_tree_nodes[stat]=self.AddSubPage(self.list_widget, stat, self._tree.calls)

    def GetRightClickMenuItems(self, node):
        result=[]
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EXPORT_CSV_CALL_HISTORY, "Export to CSV ...", "Export the call history to a csv file"))
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_DATAHISTORICAL, "Historical Data ...", "Display Historical Data"))
        return result

    def HasHistoricalData(self):
        return True

    def OnHistoricalData(self):
        """Display current or historical data"""
        if self.read_only:
            current_choice=guiwidgets.HistoricalDataDialog.Historical_Data
        else:
            current_choice=guiwidgets.HistoricalDataDialog.Current_Data
        with guihelper.WXDialogWrapper(guiwidgets.HistoricalDataDialog(self,
                                                                       current_choice=current_choice,
                                                                       historical_date=self.historical_date,
                                                                       historical_events=\
                                                                       self._main_window.database.getchangescount(self._data_key)),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                with guihelper.MWBusyWrapper(self._main_window):
                    current_choice, self.historical_date=dlg.GetValue()
                    r={}
                    if current_choice==guiwidgets.HistoricalDataDialog.Current_Data:
                        self.read_only=False
                        msg_str='Current Data'
                        self.getfromfs(r)
                    else:
                        self.read_only=True
                        msg_str='Historical Data as of %s'%\
                                 str(wx.DateTimeFromTimeT(self.historical_date))
                        self.getfromfs(r, self.historical_date)
                    self.populate(r, True)
                    self.historical_data_label.SetLabel(msg_str)
                    self.list_widget.historical_data_label.SetLabel(msg_str)

    def _publish_today_data(self):
        keys=[(x.datetime, k) for k,x in self._data.items()]
        keys.sort()
        keys.reverse()
        today_event_in=today.TodayIncomingCallsEvent()
        today_event_miss=today.TodayMissedCallsEvent()
        for _,k in keys:
            if self._data[k].folder==CallHistoryEntry.Folder_Incoming:
                today_event_in.append(self._data[k].summary(self._name_map.get(self._data[k].number, None)), {'id':k})
            if self._data[k].folder==CallHistoryEntry.Folder_Missed:
                today_event_miss.append(self._data[k].summary(self._name_map.get(self._data[k].number, None)), {'id':k})
        today_event_in.broadcast()
        today_event_miss.broadcast()

    def _populate(self):
        # lookup phone book for names
        for k,e in self._data.items():
            if e.name:
                if not self._name_map.has_key(e.number):
                    self._name_map[e.number]=e.name
            else:
                if not self._name_map.has_key(e.number):
                    pubsub.publish(pubsub.REQUEST_PB_LOOKUP,
                                   { 'item': e.number } )
        self.list_widget.populate()
        #update stats
        self.CalculateStats()
        # tell today 'bout it
        self._publish_today_data()

    def CalculateStats(self):
        total=inc=out=miss=data=0
        total_d=in_d=out_d=data_d=0
        for k, e in self._data.items():
            total+=1
            if e.duration==None:
                dur=0
            else:
                dur=e.duration
            total_d+=dur
            if e.folder==CallHistoryEntry.Folder_Incoming:
                inc+=1
                in_d+=dur
            elif e.folder==CallHistoryEntry.Folder_Outgoing:
                out+=1
                out_d+=dur
            elif e.folder==CallHistoryEntry.Folder_Missed:
                miss+=1
            elif e.folder==CallHistoryEntry.Folder_Data:
                data+=1
                data_d+=dur
        self.total_calls.SetLabel('  Total Calls: '+`total`)
        self.total_in.SetLabel('  Incoming Calls: '+`inc`)
        self.total_out.SetLabel('  Outgoing Calls: '+`out`)
        self.total_missed.SetLabel('  Missed Calls: '+`miss`)
        self.total_data.SetLabel('  Data Calls: '+`data`)
        self.duration_all.SetLabel('  Total Duration(h:m:s): '+GetDurationStr(total_d))
        self.duration_in.SetLabel('  Incoming Duration(h:m:s): '+GetDurationStr(in_d))
        self.duration_out.SetLabel('  Outgoing Duration(h:m:s): '+GetDurationStr(out_d))
        self.duration_data.SetLabel('  Data Duration(h:m:s): '+GetDurationStr(data_d))
            
    def _OnPBLookup(self, msg):
        d=msg.data
        k=d.get('item', None)
        name=d.get('name', None)
        if k is None:
            return
        self._name_map[k]=name

    def getdata(self, dict, want=None):
        dict[self._data_key]=copy.deepcopy(self._data)

    def _save_to_db(self, dict):
        if self.read_only:
            return
        db_rr={}
        for k,e in dict.items():
            db_rr[k]=CallHistoryDataobject(e)
        database.ensurerecordtype(db_rr, callhistoryobjectfactory)
        self._main_window.database.savemajordict(self._data_key, db_rr)

    def populatefs(self, dict):
        if self.read_only:
            wx.MessageBox('You are viewing historical data which cannot be changed or saved',
                             'Cannot Save Call History Data',
                             style=wx.OK|wx.ICON_ERROR)
        else:
            self._save_to_db(dict.get(self._data_key, {}))
        return dict

    def getfromfs(self, result, timestamp=None):
        dict=self._main_window.database.\
                   getmajordictvalues(self._data_key,
                                      callhistoryobjectfactory,
                                      at_time=timestamp)
        r={}
        for k,e in dict.items():
            ce=CallHistoryEntry()
            ce.set_db_dict(e)
            r[ce.id]=ce
        result.update({ self._data_key: r})
        return result

    def merge(self, dict):
        if self.read_only:
            wx.MessageBox('You are viewing historical data which cannot be changed or saved',
                             'Cannot Save Call History Data',
                             style=wx.OK|wx.ICON_ERROR)
            return
        d=dict.get(self._data_key, {})
        l=[e for k,e in self._data.items()]
        for k,e in d.items():
            if e not in l:
                self._data[e.id]=e
        self._save_to_db(self._data)
        self._populate()

    def get_selected_data(self):
        # return a dict of selected items
        res={}
        for sel_idx in self.list_widget._item_list.GetSelections():
            k=self.list_widget._item_list.GetItemData(sel_idx)
            if k:
                res[k]=self._data[k]
        return res

    def get_data(self):
        return self._data

#-------------------------------------------------------------------------------
class CallHistoryList(wx.Panel, widgets.BitPimWidget):
    _by_type=0
    _by_date=1
    _by_number=2
    def __init__(self, mainwindow, parent, stats):
        super(CallHistoryList, self).__init__(parent, -1)
        self._main_window=mainwindow
        self._stats=stats
        self.nodes={}
        self.nodes_keys={}
        self._display_filter="All"
        # main box sizer
        vbs=wx.BoxSizer(wx.VERTICAL)
        # data date adjuster
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        static_bs=wx.StaticBoxSizer(wx.StaticBox(self, -1,
                                                 'Historical Data Status:'),
                                    wx.VERTICAL)
        self.historical_data_label=wx.StaticText(self, -1, 'Current Data')
        static_bs.Add(self.historical_data_label, 1, wx.EXPAND|wx.ALL, 5)
        hbs.Add(static_bs, 1, wx.EXPAND|wx.ALL, 5)
        vbs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)
        # main list
        column_info=[]
        column_info.append(("Call Type", 80, False))
        column_info.append(("Date", 120, False))
        column_info.append(("Number", 100, False))
        column_info.append(("Duration", 80, False))
        column_info.append(("Name", 130, False))
        self._item_list=guiwidgets.BitPimListCtrl(self, column_info)
        self._item_list.ResetView(self.nodes, self.nodes_keys)
        vbs.Add(self._item_list, 1, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticText(self, -1, '  Note: Click column headings to sort data'), 0, wx.ALIGN_CENTRE|wx.BOTTOM, 10)
        # all done
        today.bind_notification_event(self.OnTodaySelectionIncoming,
                                      today.Today_Group_IncomingCalls)
        today.bind_notification_event(self.OnTodaySelectionMissed,
                                      today.Today_Group_MissedCalls)
        self.today_data=None
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

    def OnSelected(self, node):
        for stat in self._stats.stat_list:
            if self._stats.call_history_tree_nodes[stat]==node:
                if self._display_filter!=stat:
                    self._display_filter=stat
                    # for some reason GetTopItem return 0 (instead of -1)
                    # when the list is empty
                    if self._item_list.GetItemCount():
                        item=self._item_list.GetTopItem()
                        # deselect all the items when changing view
                        while item!=-1:
                            self._item_list.Select(item, 0)
                            item=self._item_list.GetNextItem(item)
                    self.populate()
                self._on_today_selection()
                return

    def OnTodaySelectionIncoming(self, evt):
        node=self._stats.call_history_tree_nodes["Incoming"]
        self.today_data=evt.data
        self.ActivateSelf(node)

    def OnTodaySelectionMissed(self, evt):
        node=self._stats.call_history_tree_nodes["Missed"]
        self.today_data=evt.data
        self.ActivateSelf(node)

    def _on_today_selection(self):
        if self.today_data and self._item_list.GetItemCount():
            item=self._item_list.GetTopItem()
            while item!=-1:
                if self.today_data['id']==self._item_list.GetItemData(item):
                    self._item_list.Select(item, 1)
                    self._item_list.EnsureVisible(item)
                else:
                    self._item_list.Select(item, 0)
                item=self._item_list.GetNextItem(item)
        self.today_data=None

    def GetRightClickMenuItems(self, node):
        result=[]
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EDITSELECTALL, "Select All", "Select All Items"))
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EDITDELETEENTRY, "Delete Selected", "Delete Selected Items"))
        result.append((widgets.BitPimWidget.MENU_SPACER, 0, "", ""))
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_EXPORT_CSV_CALL_HISTORY, "Export to CSV ...", "Export the call history to a csv file"))
        result.append((widgets.BitPimWidget.MENU_NORMAL, guihelper.ID_DATAHISTORICAL, "Historical Data ...", "Display Historical Data"))
        return result

    def CanSelectAll(self):
        if self._item_list.GetItemCount():
            return True
        return False

    def OnSelectAll(self, _):
        item=self._item_list.GetTopItem()
        while item!=-1:
            self._item_list.Select(item)
            item=self._item_list.GetNextItem(item)

    def HasHistoricalData(self):
        return self._stats.HasHistoricalData()

    def OnHistoricalData(self):
        return self._stats.OnHistoricalData()

    def populate(self):
        self.nodes={}
        self.nodes_keys={}
        index=0
        for k,e in self._stats._data.items():
            if self._display_filter=="All" or e.folder==self._display_filter:
                name=e.name
                if name==None or name=="":
                    temp=self._stats._name_map.get(e.number, None)
                    if temp !=None:
                        name=temp
                    else:
                        name=""
                self.nodes[index]=(e.folder, e.get_date_time_str(),
                                   phonenumber.format(e.number),
                                   e.durationstr, name)
                self.nodes_keys[index]=k
                index+=1
        self._item_list.ResetView(self.nodes, self.nodes_keys)

    def CanDelete(self):
        if self._stats.read_only:
            return False
        sels_idx=self._item_list.GetFirstSelected()
        if sels_idx==-1:
            return False
        return True

    def GetDeleteInfo(self):
        return wx.ART_DEL_BOOKMARK, "Delete Call Record"

    def OnDelete(self, _):
        if self._stats.read_only:
            return
        sels_idx=self._item_list.GetSelections()
        if len(sels_idx):
            # delete them from the data list
            for i,item in sels_idx.items():
                del self._stats._data[self._item_list.GetItemData(item)]
                self._item_list.Select(item, 0)
            self.populate()
            self._stats._save_to_db(self._stats._data)
            self._stats.CalculateStats()
    def GetHelpID(self):
        return helpids.ID_TAB_CALLHISTORY
