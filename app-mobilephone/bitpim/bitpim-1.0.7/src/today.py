### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: today.py 4601 2008-03-04 22:37:48Z djpham $

"""
Code to handle BitPim Today tab.

"""

# standard modules

# wx modules
import wx
import wx.lib.scrolledpanel as scrolled
import wx.lib.hyperlink as hl

# BitPim modules
import aggregatedisplay as aggr
import pubsub
import widgets


# Today REQUEST_TAB_CHANGED keys, types, and constants
Tab_Today=0
Tab_PhoneBook=1
Tab_Wallpaper=2
Tab_Ringers=3
Tab_Calendar=4
Tab_Memo=5
Tab_Todo=6
Tab_SMS=7
Tab_CallHistory=8
# TODAY_DATA keys, types, and constants
Today_Section='section'
Today_Groups='groups'
Today_Group_Tab='tab_index'
Today_Items='items'
Today_Item_Name='name'
Today_Item_Data='item_data'
# Sections
Today_Section_Today='Today'
Today_Section_ThisWeek='This Week'
# Groups
Today_Group_Calendar='Calendar:'
Today_Group_Todo='Todo List:'
Today_Group_Memo='Memo:'
Today_Group_IncomingSMS='SMS Inbox:'
Today_Group_IncomingCalls='Incoming Calls:'
Today_Group_MissedCalls='Missed Calls:'

dow_initials=('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', '   ')

EVT_TODAY_ITEM_SELECTED=wx.NewEventType()

#-------------------------------------------------------------------------------
class NotificationEvent(object):
    def __init__(self, evt_handler, client_data=None):
        self._evt_handler=evt_handler
        self.client_data=client_data
        self.data=None
    def send(self):
        self._evt_handler(self)

#-------------------------------------------------------------------------------
class NotificationEventHandler(object):
    def __init__(self):
        self._evt_table={}

    def append(self, evt_handler, group, client_data=None):
        evt=NotificationEvent(evt_handler, client_data)
        self._evt_table.setdefault(group, []).append(evt)

    def process(self, group, evt):
        for e in self._evt_table.get(group, []):
            e.data=evt
            e.send()
        
#-------------------------------------------------------------------------------
evt_handler=None
def bind_notification_event(_evt_handler, group, client_data=None):
    global evt_handler
    if evt_handler is None:
        evt_handler=NotificationEventHandler()
    evt_handler.append(_evt_handler, group, client_data)

#-------------------------------------------------------------------------------
class BaseEvent(object):
    def __init__(self, section, group):
        self.section=section
        self.group=group
        self._items=[]

    def append(self, item_name, item_data=None):
        # append a data item to this event
        self._items.append({ Today_Item_Name: item_name,
                             Today_Item_Data: item_data })

    def _set_names(self, names):
        self._items=[{ Today_Item_Name: x, Today_Item_Data: None } \
                     for x in names]
    def _get_names(self):
        return [x[Today_Item_Name] for x in self._items]
    names=property(fget=_get_names, fset=_set_names)

    def _get_items(self):
        return self._items
    items=property(fget=_get_items)

    def broadcast(self):
        # broadcast this event
        pubsub.publish(pubsub.NEW_DATA_AVAILABLE, data=self)
    @classmethod
    def bind(_, func):
        pubsub.subscribe(func, pubsub.NEW_DATA_AVAILABLE)

#-------------------------------------------------------------------------------
class TodayCalendarEvent(BaseEvent):
    def __init__(self):
        super(TodayCalendarEvent, self).__init__(Today_Section_Today,
                                                 Today_Group_Calendar)
class ThisWeekCalendarEvent(BaseEvent):
    def __init__(self):
        super(ThisWeekCalendarEvent, self).__init__(Today_Section_ThisWeek,
                                                    Today_Group_Calendar)
class TodayTodoEvent(BaseEvent):
    def __init__(self):
        super(TodayTodoEvent, self).__init__(Today_Section_Today,
                                             Today_Group_Todo)
class ThisWeekTodoEvent(BaseEvent):
    def __init__(self):
        super(ThisWeekTodoEvent, self).__init__(Today_Section_ThisWeek,
                                                Today_Group_Todo)
class TodayMemoEvent(BaseEvent):
    def __init__(self):
        super(TodayMemoEvent, self).__init__(Today_Section_Today,
                                             Today_Group_Memo)
class TodaySMSEvent(BaseEvent):
    def __init__(self):
        super(TodaySMSEvent, self).__init__(Today_Section_Today,
                                            Today_Group_IncomingSMS)
class TodayIncomingCallsEvent(BaseEvent):
    def __init__(self):
        super(TodayIncomingCallsEvent, self).__init__(Today_Section_Today,
                                                      Today_Group_IncomingCalls)
class TodayMissedCallsEvent(BaseEvent):
    def __init__(self):
        super(TodayMissedCallsEvent, self).__init__(Today_Section_Today,
                                              Today_Group_MissedCalls)

# Request Today Event-----------------------------------------------------------
def bind_request_event(evt_handler):
    pubsub.subscribe(evt_handler, pubsub.REQUEST_TODAY_DATA)
def send_request_event():
    pubsub.publish(pubsub.REQUEST_TODAY_DATA)

#-------------------------------------------------------------------------------
EVT_HYPERLINK_LEFT=hl.EVT_HYPERLINK_LEFT
class HyperLinkCtrl(hl.HyperLinkCtrl):
    def __init__(self, *args, **kargs):
        super(HyperLinkCtrl, self).__init__(*args, **kargs)
        self.AutoBrowse(False)
        self.DoPopup(False)
        self.client_data=None

    def SetToolTip(self, tip):
        if isinstance(tip, (str, unicode)):
            super(HyperLinkCtrl, self).SetToolTip(wx.ToolTip(tip))
        else:
            super(HyperLinkCtrl, self).SetToolTip(tip)

    def SetLabel(self, label):
        super(HyperLinkCtrl, self).SetLabel(label)
        self.SetToolTip(label)

#-------------------------------------------------------------------------------
class StaticText(wx.StaticText):
    _max_item_len=30
    _postfix='...'
    _max_client_len=_max_item_len-len(_postfix)
    def __init__(self, *args, **kargs):
        super(StaticText, self).__init__(*args, **kargs)
    def SetLabel(self, label):
        if len(label)>self._max_item_len:
            label=label[:self._max_client_len]+self._postfix
        super(StaticText, self).SetLabel(label)

#-------------------------------------------------------------------------------
class ItemHyperLink(HyperLinkCtrl):
    _max_item_len=30
    _postfix='...'
    _max_client_len=_max_item_len-len(_postfix)
    def __init__(self, *args, **kargs):
        super(ItemHyperLink, self).__init__(*args, **kargs)
        self.client_data=None
    def SetLabel(self, label, client_data=None):
        # if label contains linefeed truncate
        if label.find('\n')>-1:
            label=label.split('\n')[0]+self._postfix
        if len(label)>self._max_item_len:
            label=label[:self._max_client_len]+self._postfix
        super(ItemHyperLink, self).SetLabel(label)
        self.client_data=client_data
    
#-------------------------------------------------------------------------------
class GroupWidget(wx.Panel, widgets.BitPimWidget):
    max_total_items=10
    max_items=9
    _title_font=None
    _item_font=None
    _last_item={ Today_Item_Name: '... more ...',
                 Today_Item_Data: None }
    def __init__(self, parent, _name):
        super(GroupWidget, self).__init__(parent, wx.NewId())
        self.name=_name.get('name', '')
        self.tab_index=_name.get('tab_index', None)
        self._data=[]
        self._widgets=[]
        if not self._title_font:
            self._title_font=wx.Font(12, wx.FONTFAMILY_DEFAULT,
                                     wx.FONTSTYLE_NORMAL,
                                     wx.FONTWEIGHT_BOLD)
            self._item_font=wx.Font(10, wx.FONTFAMILY_MODERN,
                                    wx.FONTSTYLE_NORMAL,
                                    wx.FONTWEIGHT_NORMAL)
        bs=wx.StaticBoxSizer(wx.StaticBox(self, -1, ''), wx.VERTICAL)
        title=HyperLinkCtrl(self, -1, self.name)
        if self._title_font.Ok():
            title.SetFont(self._title_font)
        hl.EVT_HYPERLINK_LEFT(self, title.GetId(), self.OnItemSelected)
        bs.Add(title, 0, wx.ALL, 5)
        vbs=wx.BoxSizer(wx.VERTICAL)
        for i in range(self.max_total_items):
            w=ItemHyperLink(self, -1,  '')
            if self._item_font.Ok():
                w.SetFont(self._item_font)
            hl.EVT_HYPERLINK_LEFT(self, w.GetId(), self.OnItemSelected)
            vbs.Add(w, 0, wx.RIGHT|wx.LEFT, 5)
            vbs.Hide(i)
            self._widgets.append(w)
        bs.Add(vbs, 1, wx.LEFT, 10)
        self._vbs=vbs
        bs.Fit(self)
        self.SetSizer(bs)
        self.SetAutoLayout(True)

    def Draw(self, dc, width, height, selected):
        x=dc.pos[0]-dc.view_start[0]
        y=dc.pos[1]-dc.view_start[1]
        self.SetDimensions(x, y, width, height)

    def OnHyperlinkLeft(self, evt):
        if self.tab_index:
            pubsub.publish(pubsub.REQUEST_TAB_CHANGED,
                           data=self.tab_index)

    def OnItemSelected(self, evt):
        if evt_handler:
            self.OnHyperlinkLeft(evt)
            evt_handler.process(self.name, evt.GetEventObject().client_data)

    def Set(self, data):
        data_len=len(data)
        if data_len>self.max_total_items:
            self._data=data[:self.max_items]
            self._data.append(self._last_item)
            data_len=self.max_total_items
        else:
            self._data=data
        for i in range(data_len):
            self._widgets[i].SetLabel(self._data[i].get(Today_Item_Name, ''),
                                      self._data[i].get(Today_Item_Data, None))
            self._vbs.Show(i)
        for i in range(data_len, self.max_total_items):
            self._vbs.Hide(i)
        self._vbs.Layout()
        self.Fit()
        self.Refresh()

    def not_empty(self):
        return self._data

#-------------------------------------------------------------------------------
class SectionHeader(aggr.SectionHeader):
    default_width=10
    default_height=10
    def __init__(self, label):
        super(SectionHeader, self).__init__(label)
        self._items=[]
    def Add(self, item):
        self._items.append(item)
    def GetAllItems(self):
        return self._items
    def GetItems(self):
        l=[]
        for x in self._items:
            if x.not_empty():
                l.append(x)
                x.Show()
            else:
                x.Hide()
        return l
    def GetItemSize(self):
        w=self.default_width
        h=self.default_height
        for e in self._items:
            w1,h1=e.GetSizeTuple()
            w=max(w, w1)
            h=max(h,h1)
        return (w,h)

    def not_empty(self):
        return self.GetItems()


#-------------------------------------------------------------------------------
class TodayWidget(aggr.Display, widgets.BitPimWidget):
    _section_names=('Today','This Week')
    _item_names=(({ 'name': Today_Group_Calendar, 'tab_index': Tab_Calendar },
                  { 'name': Today_Group_Todo, 'tab_index': Tab_Todo },
                  { 'name': Today_Group_Memo, 'tab_index': Tab_Memo },
                  { 'name': Today_Group_IncomingSMS, 'tab_index': Tab_SMS },
                  { 'name': Today_Group_IncomingCalls, 'tab_index': Tab_CallHistory },
                  { 'name': Today_Group_MissedCalls, 'tab_index': Tab_CallHistory }),
                 ({ 'name': Today_Group_Calendar, 'tab_index': Tab_Calendar },
                  { 'name': Today_Group_Todo, 'tab_index': Tab_Todo } ))

    def __init__(self, mainwindow, parent):
        self._sections=[]
        super(TodayWidget, self).__init__(parent, self)
        self._main_window=mainwindow
        # sections & items info
        self._sections=[SectionHeader(s) for s in self._section_names]
        for i,group in enumerate(self._item_names):
            for name in group:
                w=GroupWidget(self, name)
                self._sections[i].Add(w)
        # all done
        # populate data
        self.UpdateItems()
        # register for pubsub events
        BaseEvent.bind(self.OnNewData)
        pubsub.subscribe(self._OnMidnight, pubsub.MIDNIGHT)

    def GetSections(self):
        "Return a list of section headers"
        return [x for x in self._sections if x.not_empty()]

    def GetItemSize(self, sectionnumber, sectionheader):
        "Return (width, height of each item)"
        return sectionheader.GetItemSize()

    def GetItemsFromSection(self,sectionnumber,sectionheader):
        return sectionheader.GetItems()

    def _populate(self, data):
        section_name=data.section
        group_name=data.group
        for s in self._sections:
            if s.label!=section_name:
                continue
            for group in s.GetAllItems():
                if group.name==group_name:
                    group.Set(data.items)
                    break
            break
        self.UpdateItems()
        self.Refresh()

    def OnNewData(self, msg=None):
        if msg is None:
            return
        self._populate(msg.data)

    def _OnMidnight(self, _):
        send_request_event()
