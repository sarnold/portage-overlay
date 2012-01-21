### BITPIM
###
### Copyright (C) 2005 Simon Capper <skyjunky@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

"""
Auto synchronization of calender
This module provides functionality to automatically sync the calender on your PC (outlook etc.)
with your phone. It will do so at a regular interval if the phone is connected and BitPim is running
This feature works with all BitPim calender types and phones that support the writing of calenders

"""

# standard modules
import copy
import sha
import time
import re

# wx modules
import wx

# BitPim modules
import database
import guiwidgets
import common_calendar
import guiwidgets
import gui

_data_key='auto_sync_settings'
_filter_keys=['start_offset', 'end_offset', 'no_alarm', 'rpt_events', "alarm_value",
              'ringtone', 'vibrate', 'categories', 'alarm_override']

def _getsettings(mw, profile):
    settings=AutoSyncSettingsEntry()
    dict=mw.GetActiveDatabase().getmajordictvalues(_data_key, autosyncsettingsobjectfactory)
    if profile in dict:
        settings.set_db_dict(dict[profile])
    return settings

def UpdateOnConnect(mw, profile="Default Autosync"):
    settings=_getsettings(mw, profile)
    return settings.sync_on_connect

class SyncSchedule(object):
    def __init__(self, log=None):
        # get standard commport parameters
        self.__log=log
        self.__data={}

    def log(self, log_str):
        if self.__log is None:
            print log_str
        else:
            self.__log.log(log_str)
    def logdata(self, log_str, log_data):
        if self.__log is None:
            print log_str,log_data
        else:
            self.__log.logdata(log_str, log_data)

    def importcalenderdata(self):
        res=0
        for entry in self.mw.calenders:
            if entry[0]==self.settings.caltype:
                filter={}
                for setting in _filter_keys:
                    if self.settings._data.has_key(setting) and self.settings._data[setting]!=None:
                        # need to convert start and end from scalable values
                        if setting=='start_offset':
                            tm=time.gmtime(time.time()-(self.settings._data[setting]*24*60*60))
                            date=(tm.tm_year, tm.tm_mon, tm.tm_mday)
                            filter['start']=date
                        elif setting=='end_offset':
                            tm=time.gmtime(time.time()+(self.settings._data[setting]*24*60*60))
                            date=(tm.tm_year, tm.tm_mon, tm.tm_mday)
                            filter['end']=date
                        elif setting=="categories":
                            # convert categories into list
                            filter[setting]=self.settings._data[setting].split("||")
                        else:
                             filter[setting]=self.settings._data[setting]
                    else:
                        if setting=='start_offset':
                            filter['start']=None
                        if setting=='end_offset':
                            filter['end']=None
                res=entry[2](self.mw.tree.GetActivePhone(), self.settings.calender_id, filter)
                if res==1:
                    # imported calender OK!!!
                    self.log("Auto Sync: Imported calender OK")
        if not res:
            self.log("Auto Sync: Failed to import calender")
        return res

    def sendcalendertophone(self):
        res=1
        data={}
        todo=[]
        data['calendar_version']=self.mw.phoneprofile.BP_Calendar_Version
        self.mw.GetActiveCalendarWidget().getdata(data)
        todo.append( (self.mw.wt.writecalendar, "Calendar", False) )
        todo.append((self.mw.wt.rebootcheck, "Phone Reboot"))
        self.mw.MakeCall(gui.Request(self.mw.wt.getfundamentals),
                      gui.Callback(self.OnDataSendPhoneGotFundamentals, data, todo))
        return res

    def OnDataSendPhoneGotFundamentals(self, data, todo, exception, results):
        if exception!=None:
            if not self.silent:
                self.mw.HandleException(exception)
            self.log("Auto Sync: Failed, Exception getting phone fundementals")
            self.mw.OnBusyEnd()
            return
        data.update(results)
        # Now scribble to phone
        self.log("Auto Sync: Sending results to phone")
        self.mw.MakeCall(gui.Request(self.mw.wt.senddata, data, todo),
                      gui.Callback(self.OnDataSendCalenderResults))

    def OnDataSendCalenderResults(self, exception, results):
        if exception!=None:
            if not self.silent:
                self.mw.HandleException(exception)
            self.log("Auto Sync: Failed, Exception writing calender to phone")
            self.mw.OnBusyEnd()
            return
        if self.silent==0:
            wx.MessageBox('Phone Synchronized OK',
                          'Synchronize Complete', wx.OK)
        self.log("Auto Sync: Synchronize Completed OK")
        self.mw.OnBusyEnd()

    def sync(self, mw, silent, profile="Default Autosync"):
        self.silent=silent
        # start the autosync process
        # import the calender, find the entry point for the import function
        self.mw=mw
        if mw.config.ReadInt("SafeMode", False):
            self.log("Auto Sync: Disabled, BitPim in safe mode")
            return 0
        if wx.IsBusy():
            self.log("Auto Sync: Failed, BitPim busy")
            return 0
        self.log("Auto Sync: Starting (silent mode=%d)..." % (silent))
        self.mw.OnBusyStart()
        self.mw.GetStatusBar().progressminor(0, 100, 'Auto Calendar Import in progress ...')
        # retrieve the configuration
        self.settings=_getsettings(mw, profile)
        # update BitPims calender
        res=self.importcalenderdata()
        if res==1:
            # send updated calender to the phone
            res=self.sendcalendertophone()
        else:
            self.mw.OnBusyEnd()
            if silent==0:
                wx.MessageBox('Unable to Auto-Import Calendar Data',
                              'Auto Calendar Import failed', wx.OK)
            self.log("Auto Sync: Failed, Unable to synchronize phone schedule")
        return res

#-------------------------------------------------------------------------------
class AutoSyncSettingsobject(database.basedataobject):
    _knownproperties=['caltype', 'calender_id', 'sync_on_connect', 'sync_frequency', \
                      'start_offset', 'end_offset', 'no_alarm', 'rpt_events', 'categories', \
                      'ringtone', 'vibrate', 'alarm_override', 'alarm_value']
    _knownlistproperties=database.basedataobject._knownlistproperties.copy()
    def __init__(self, data=None):
        if data is None or not isinstance(data, AutoSyncSettingsEntry):
            return;
        self.update(data.get_db_dict())
autosyncsettingsobjectfactory=database.dataobjectfactory(AutoSyncSettingsobject)

#-------------------------------------------------------------------------------
class AutoSyncSettingsEntry(object):
    _caltype_key='caltype'
    _calender_id_key='calender_id'
    _sync_on_connect_key='sync_on_connect'
    _sync_frequency_key='sync_frequency'
    #_start_offset_key='start_offset'
    #_end_offset_key='end_offset'
    #_no_alarm_key='no_alarm'
    #_categories_key='categories'
    #_rpt_event_key='rpt_event'
    #_vibrate_key='vibrate'
    def __init__(self):
        self._data={ 'serials': [] }
        # we only expect one record, so the ID is fixed

    def __eq__(self, rhs):
        return self.caltype==rhs.caltype and self.calender_id==rhs.calender_id and\
               self.sync_frequency==rhs.sync_frequency and self.sync_on_connect==rhs.sync_on_connect
    def __ne__(self, rhs):
        return (not __eq__(rhs))
    def get(self):
        return copy.deepcopy(self._data, {})
    def set(self, d):
        self._data={}
        self._data.update(d)

    def get_db_dict(self):
        return self.get()
    def set_db_dict(self, d):
        self.set(d)

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

    def _get_caltype(self):
        return self._data.get(self._caltype_key, 'None')
    def _set_caltype(self, v):
        self._set_or_del(self._caltype_key, v, [''])
    caltype=property(fget=_get_caltype, fset=_set_caltype)

    def _get_calender_id(self):
        return self._data.get(self._calender_id_key, '')
    def _set_calender_id(self, v):
        self._set_or_del(self._calender_id_key, v, [''])
    calender_id=property(fget=_get_calender_id, fset=_set_calender_id)

    def _get_sync_on_connect(self):
        return self._data.get(self._sync_on_connect_key, False)
    def _set_sync_on_connect(self, v):
        self._set_or_del(self._sync_on_connect_key, v, [''])
    sync_on_connect=property(fget=_get_sync_on_connect, fset=_set_sync_on_connect)

    def _get_sync_frequency(self):
        return self._data.get(self._sync_frequency_key, 0)
    def _set_sync_frequency(self, v):
        self._set_or_del(self._sync_frequency_key, v, [''])
    sync_frequency=property(fget=_get_sync_frequency, fset=_set_sync_frequency)

###
###  The autosync settings dialog
###

class AutoSyncSettingsDialog(wx.Dialog):
    ID_CALSETTINGS=wx.NewId()
    def __init__(self, mainwindow, frame, title="Auto Calendar Import Settings", profile="Default Autosync", id=-1):
        t=title+" - "+profile
        wx.Dialog.__init__(self, frame, id, t,
                          style=wx.CAPTION|wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE)
        self.mw=mainwindow
        self.profile=profile

        gs=wx.GridBagSizer(10, 10)
        gs.AddGrowableCol(1)

        # calender type
        gs.Add( wx.StaticText(self, -1, "Calender Type"), pos=(0,0), flag=wx.ALIGN_CENTER_VERTICAL)
        # get a list of the possible calender types supported
        calendertype=('None',)
        # build a list of calender types for the user to select from
        for entry in self.mw.calenders:
            calendertype+=(entry[0], )

        self.caltype=wx.ComboBox(self, -1, calendertype[0], style=wx.CB_DROPDOWN|wx.CB_READONLY,choices=calendertype)
        gs.Add( self.caltype, pos=(0,1), flag=wx.ALIGN_CENTER_VERTICAL)
        gs.Add( wx.Button(self, self.ID_CALSETTINGS, "Calender Settings..."), pos=(0,2), flag=wx.ALIGN_CENTER_VERTICAL)

        # on connect
        gs.Add( wx.StaticText(self, -1, "Update when phone re-connected"), pos=(1,0), flag=wx.ALIGN_CENTER_VERTICAL)
        self.sync_on_connect=wx.CheckBox(self, wx.NewId(), "")
        gs.Add( self.sync_on_connect, pos=(1,1), flag=wx.ALIGN_CENTER_VERTICAL)

        # frequency
        gs.Add( wx.StaticText(self, -1, "Update Frequency (mins) 0=never"), pos=(2,0), flag=wx.ALIGN_CENTER_VERTICAL)
        self.sync_frequency=wx.lib.intctrl.IntCtrl(self, -1, value=0, min=0, max=1440)
        gs.Add( self.sync_frequency, pos=(2,1), flag=wx.ALIGN_CENTER_VERTICAL)

        # crud at the bottom
        bs=wx.BoxSizer(wx.VERTICAL)
        bs.Add(gs, 0, wx.EXPAND|wx.ALL, 10)
        bs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 7)
        
        but=self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP)
        bs.Add(but, 0, wx.CENTER|wx.ALL, 10)

        wx.EVT_BUTTON(self, wx.ID_HELP, self.OnHelp)
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)
        wx.EVT_BUTTON(self, self.ID_CALSETTINGS, self.OnConfigCalender)
        wx.EVT_COMBOBOX(self, self.caltype.GetId(), self.OnCaltypeChange)

        self.settings=AutoSyncSettingsEntry()

        self.SetSizer(bs)
        self.SetAutoLayout(True)
        bs.Fit(self)
        # read initial values from database
        self.getfromfs()
        self.auto_sync_timer_id = wx.NewId()
        self.auto_sync_timer = wx.Timer(self, self.auto_sync_timer_id)
        # start the timer
        self.SetAutoSyncTimer()

        # Retrieve saved settings... (we only care about position)
        guiwidgets.set_size("AutoSyncSettingsDialog", self, screenpct=-1,  aspect=3.5)

        wx.EVT_CLOSE(self, self.OnClose)

    def OnCaltypeChange(self, _):
        #see if the value has changed, if so automatically fire up the configuration for the calender
        if self.settings.caltype!=self.caltype.GetValue():
            self.OnConfigCalender()
        return

    def OnConfigCalender(self, _=None):
        old_folder=self.settings.calender_id
        for entry in self.mw.calenders:
            if entry[0]==self.caltype.GetValue():
                # if the calender type is changing blank out the folder name
                if self.settings.caltype!=self.caltype.GetValue():
                    self.settings.calender_id=''    
                filter={}
                for setting in _filter_keys:
                    if self.settings._data.has_key(setting) and self.settings._data[setting]!=None:
                        if setting=="categories":
                            # convert categories into list
                            filter[setting]=self.settings._data[setting].split("||")
                        else:
                            filter[setting]=self.settings._data[setting]
                res, temp=entry[1](self.mw, self.settings.calender_id, filter)
                if res==wx.ID_OK and res != None:
                    # temp is a tuple of the calender_id and the filter settings
                    self.settings.calender_id=temp[0]
                    for setting in _filter_keys:
                        if(temp[1].has_key(setting) and temp[1][setting]!=None):
                            if setting=="categories":
                                # convert categories into storable type
                                cat_str=""
                                for cat in temp[1][setting]:
                                    #use a || to separate individual categories
                                    if len(cat_str):
                                        cat_str=cat_str+"||"+cat
                                    else:
                                        cat_str=cat
                                self.settings._data[setting]=cat_str
                            else:
                                self.settings._data[setting]=temp[1][setting]
                        else:
                            if self.settings._data.has_key(setting):
                                del self.settings._data[setting]
                    self.settings.caltype=self.caltype.GetValue()
                else: # cancel pressed
                    #revert back to previous value
                    self.caltype.SetValue(self.settings.caltype)
                    self.settings.calender_id=old_folder
                return
        return

    def OnCancel(self, _):
        self.saveSize()
        self.EndModal(wx.ID_CANCEL)
        return

    def OnOK(self, _):
        self.saveSize()
        self.EndModal(wx.ID_OK)
        return

    def OnHelp(self, _):
        #wx.GetApp().displayhelpid(helpids.ID_AUTOSYNC_DIALOG)
        return

    def OnClose(self, evt):
        self.saveSize()
        # Don't destroy the dialong, just put it away...
        self.EndModal(wx.ID_CANCEL)
        return

    def _save_to_db(self):
        db_rr={}
        self.settings.caltype=self.caltype.GetValue()
        self.settings.sync_on_connect=self.sync_on_connect.GetValue()
        self.settings.sync_frequency=self.sync_frequency.GetValue()
        self.settings.id=self.profile
        db_rr[self.settings.id]=AutoSyncSettingsobject(self.settings)
        database.ensurerecordtype(db_rr, autosyncsettingsobjectfactory)
        self.mw.tree.GetActivePhone().GetDatabase().savemajordict(_data_key, db_rr)

    def getfromfs(self):
        self.settings=_getsettings(self.mw, self.profile)
        self.caltype.SetValue(self.settings.caltype)
        self.sync_on_connect.SetValue(int(self.settings.sync_on_connect))
        self.sync_frequency.SetValue(int(self.settings.sync_frequency))
        return

    def IsConfigured(self):
        return self.settings.caltype!='None'

    def updatevariables(self):
        self.mw.auto_save_dict=self.settings

    def ShowModal(self):
        self.getfromfs()
        ec=wx.Dialog.ShowModal(self)
        if ec==wx.ID_OK:
            self._save_to_db()
            self.updatevariables()
            self.SetAutoSyncTimer()
        return ec

    def saveSize(self):
        guiwidgets.save_size("AutoSyncSettingsDialog", self.GetRect())

    def SetAutoSyncTimer(self):
        # stop the previous timer (if any)
        self.auto_sync_timer.Stop()
        oneShot = True
        timeout=self.settings.sync_frequency*60000 # convert msecs
        if timeout:
            self.auto_sync_timer.Start(timeout, oneShot)
            self.Bind(wx.EVT_TIMER, self.OnTimer, self.auto_sync_timer)

    def OnTimer(self, event):
        self.mw.log("Auto Sync: Timed update")
        SyncSchedule(self.mw).sync(self.mw, silent=1)
        self.SetAutoSyncTimer()

