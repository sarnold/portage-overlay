### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: importexport.py 4377 2007-08-27 04:58:33Z djpham $

"Deals with importing and exporting stuff"

# System modules
from __future__ import with_statement
import contextlib
import string
import re
import StringIO
import os

# wxPython modules
import wx
import wx.grid
import wx.html

# Others
from thirdparty import DSV

# My modules
import common
import guihelper
import vcard
import phonenumber
import guiwidgets
import nameparser
import phonebook
import pubsub
import guihelper
import csv_calendar
import vcal_calendar
import ical_calendar
import gcal_calendar as gcal
import playlist
import wpl_file

# control
def GetPhonebookImports():
    res=[]
    # Calendar Wizard
    res.append( (guihelper.ID_CALENDAR_WIZARD, 'Import Calendar Wizard...',
                 'Import Calendar Wizard', OnCalendarWizard) )
    res.append( (wx.NewId(), 'Calendar Import Preset...',
                'Calendar Import Preset...', OnCalendarPreset) )
    res.append( (wx.NewId(), 'Auto Calendar Import',
                 'Auto Calendar Import',
                 ( (guihelper.ID_AUTOSYNCSETTINGS, 'Settings',
                    'Configure Auto Calendar Import', None),
                   (guihelper.ID_AUTOSYNCEXECUTE, 'Execute',
                    'Perform Auto Calendar Import', None))
                 ))
    # CSV - always possible
    res.append( (guihelper.ID_IMPORT_CSV_CONTACTS,"CSV Contacts...", "Import a CSV file for the phonebook", OnFileImportCSVContacts) )
    res.append( (guihelper.ID_IMPORT_CSV_CALENDAR,"CSV Calendar...", "Import a CSV file for the calendar", OnFileImportCSVCalendar) )
    # Vcards - always possible
    res.append( (guihelper.ID_IMPORT_VCARDS,"vCards...", "Import vCards for the phonebook", OnFileImportVCards) )
    # Vcal - always possible
    res.append((guihelper.ID_IMPORT_VCALENDAR,'vCalendar...', 'Import vCalendar data for the calendar', OnFileImportVCal))
    # iCal - always possible
    res.append((guihelper.ID_IMPORT_ICALENDAR, 'iCalendar...',
                'Import iCalendar data for the calendar',
                OnFileImportiCal))
    # Google Calendar - always possible
    res.append((guihelper.ID_IMPORT_GCALENDAR, 'Google Calendar...',
                'Import Google Calendar data for the calendar',
                OnFileImportgCal))
    # Outlook
    try:
        import native.outlook
        res.append( (guihelper.ID_IMPORT_OUTLOOK_CONTACTS,"Outlook Contacts...", "Import Outlook contacts for the phonebook", OnFileImportOutlookContacts) )
        res.append( (guihelper.ID_IMPORT_OUTLOOK_CALENDAR,"Outlook Calendar...", "Import Outlook calendar for the calendar", OnFileImportOutlookCalendar) )
        res.append( (guihelper.ID_IMPORT_OUTLOOK_NOTES,"Outlook Notes...", "Import Outlook notes for the memo", OnFileImportOutlookNotes) )
        res.append( (guihelper.ID_IMPORT_OUTLOOK_TASKS,"Outlook Tasks...", "Import Outlook tasks for the todo", OnFileImportOutlookTasks) )
    except:
        pass
    # Evolution
    try:
        import native.evolution
        res.append( (guihelper.ID_IMPORT_EVO_CONTACTS,"Evolution Contacts...", "Import Evolution contacts for the phonebook", OnFileImportEvolutionContacts) )
    except ImportError:
        pass
    # Qtopia Desktop - always possible
    res.append( (guihelper.ID_IMPORT_QTOPIA_CONTACTS,"Qtopia Desktop...", "Import Qtopia Desktop contacts for the phonebook", OnFileImportQtopiaDesktopContacts) )
    # eGroupware - always possible
    res.append( (guihelper.ID_IMPORT_GROUPWARE_CONTACTS,"eGroupware...", "Import eGroupware contacts for the phonebook", OnFileImporteGroupwareContacts) )
    # WPL Playlist, always possible
    res.append( (guihelper.ID_IMPORT_WPL, 'WPL Play List...',
                 'Import WPL Play List',
                 OnWPLImport))
    return res
    
def GetCalenderAutoSyncImports():
    res=[]
    # CSV - always possible
    res.append( ("CSV Calendar", AutoConfCSVCalender, AutoImportCSVCalendar) )
    # Vcal - always possible
    res.append(('vCalendar', AutoConfVCal, AutoImportVCal))
    # Outlook
    try:
        import native.outlook
        res.append( ("Outlook", AutoConfOutlookCalender, AutoImportOutlookCalendar) )
    except:
        print "Failed to get outlook"
        pass
    # Evolution
    
    return res

def GetCalendarImports():
    # return a list of calendar types data objects
    res=[]
    res.append({ 'type': 'CSV Calendar',
                 'source': csv_calendar.ImportDataSource,
                 'data': csv_calendar.CSVCalendarImportData })
    res.append({ 'type': 'vCalendar',
                 'source': vcal_calendar.ImportDataSource,
                 'data': vcal_calendar.VCalendarImportData })
    res.append({ 'type': 'iCalendar',
                 'source': ical_calendar.ImportDataSource,
                 'data': ical_calendar.iCalendarImportData })
    res.append({ 'type': 'Google Calendar',
                 'source': gcal.ImportDataSource,
                 'data': gcal.gCalendarImportData })
    try:
        import native.outlook
        import outlook_calendar
        res.append({ 'type': 'Outlook Calendar',
                     'source': outlook_calendar.ImportDataSource,
                     'data': outlook_calendar.OutlookCalendarImportData })
    except:
        pass
    return res

def TestOutlookIsInstalled():
    import native.outlook
    try:
        native.outlook.getmapinamespace()
    except:
        guihelper.MessageDialog(None, 'Unable to initialise Outlook, Check that it is installed correctly.',
                                'Outlook Error', wx.OK|wx.ICON_ERROR)
        return False
    return True

class PreviewGrid(wx.grid.Grid):

    def __init__(self, parent, id):
        wx.grid.Grid.__init__(self, parent, id, style=wx.WANTS_CHARS)
        wx.grid.EVT_GRID_CELL_LEFT_DCLICK(self, self.OnLeftDClick)

    # (Taken from the demo) I do this because I don't like the default
    # behaviour of not starting the cell editor on double clicks, but
    # only a second click.
    def OnLeftDClick(self, evt):
        if self.CanEnableCellControl():
            self.EnableCellEditControl()

class ImportDialog(wx.Dialog):
    "The dialog for importing phonebook stuff"


    # these are presented in the UI and are what the user can select.  additional
    # column names are available but not specified 
    possiblecolumns=["<ignore>", "First Name", "Last Name", "Middle Name",
                     "Name", "Nickname", "Email Address", "Web Page", "Fax", "Home Street",
                     "Home City", "Home Postal Code", "Home State",
                     "Home Country/Region",  "Home Phone", "Home Fax", "Mobile Phone", "Home Web Page",
                     "Business Street", "Business City", "Business Postal Code",
                     "Business State", "Business Country/Region", "Business Web Page",
                     "Business Phone", "Business Fax", "Pager", "Company", "Notes", "Private",
                     "Category", "Categories"]
    bp_columns=[
                     # BitPim CSV fields
                     'names_title', 'names_first', 'names_middle', 'names_last',
                     'names_full', 'names_nickname',
                     'addresses_type', 'addresses_company', 'addresses_street',
                     'addresses_street2', 'addresses_city',
                     'addresses_state', 'addresses_postalcode',
                     'addresses_country',
                     'numbers_number', 'numbers_type', 'numbers_speeddial',
                     'emails_email', 'emails_type',
                     'urls_url', 'urls_type',
                     'categories_category',
                     'ringtones_ringtone', 'ringtones_use',
                     'wallpapers_wallpaper', 'wallpapers_use',
                     'memos_memo', 'flags_secret'
                     ]
    
    # used for the filtering - any of the named columns have to be present for the data row
    # to be considered to have that type of column
    filternamecolumns=["First Name", "Last Name", "Middle Name", "Name", "Nickname"]
    
    filternumbercolumns=["Home Phone", "Home Fax", "Mobile Phone", "Business Phone",
                         "Business Fax", "Pager", "Fax", "Phone"]

    filterhomeaddresscolumns=["Home Street", "Home City", "Home Postal Code", "Home State",
                          "Home Country/Region"]

    filterbusinessaddresscolumns=["Business Street", "Business City",
                                  "Business Postal Code", "Business State", "Business Country/Region"]

    filteraddresscolumns=filterhomeaddresscolumns+filterbusinessaddresscolumns+["Address"]

    filteremailcolumns=["Email Address", "Email Addresses"]
                          
    # used in mapping column names above into bitpim phonebook fields
    addressmap={
        'Street': 'street',
        'City':   'city',
        'Postal Code': 'postalcode',
        'State':      'state',
        'Country/Region': 'country',
       }

    namemap={
        'First Name': 'first',
        'Last Name': 'last',
        'Middle Name': 'middle',
        'Name': 'full',
        'Nickname': 'nickname'
        }

    numbermap={
        "Home Phone": 'home',
        "Home Fax":   'fax',
        "Mobile Phone": 'cell',
        "Business Phone": 'office',
        "Business Fax":  'fax',
        "Pager": 'pager',
        "Fax": 'fax'
        }


    def __init__(self, parent, id, title, style=wx.CAPTION|wx.MAXIMIZE_BOX|\
                 wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        wx.Dialog.__init__(self, parent, id=id, title=title, style=style)
        self.possiblecolumns+=self.bp_columns
        self.merge=True
        vbs=wx.BoxSizer(wx.VERTICAL)
        t,sz=self.gethtmlhelp()
        w=wx.html.HtmlWindow(self, -1, size=sz, style=wx.html.HW_SCROLLBAR_NEVER)
        w.SetPage(t)
        vbs.Add(w, 0, wx.EXPAND|wx.ALL,5)

        self.getcontrols(vbs)

        cfg=lambda key: wx.GetApp().config.ReadInt("importdialog/filter"+key, False)
        

        # Only records with ... row
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.StaticText(self, -1, "Only rows with "), 0, wx.ALL|wx.ALIGN_CENTRE,2)
        self.wname=wx.CheckBox(self, wx.NewId(), "a name")
        self.wname.SetValue(cfg("name"))
        hbs.Add(self.wname, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTRE,7)
        self.wnumber=wx.CheckBox(self, wx.NewId(), "a number")
        self.wnumber.SetValue(cfg("phonenumber"))
        hbs.Add(self.wnumber, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTRE,7)
        self.waddress=wx.CheckBox(self, wx.NewId(), "an address")
        self.waddress.SetValue(cfg("postaladdress"))
        hbs.Add(self.waddress, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTRE,7)
        self.wemail=wx.CheckBox(self, wx.NewId(), "an email")
        self.wemail.SetValue(cfg("emailaddress"))
        hbs.Add(self.wemail, 0, wx.LEFT|wx.ALIGN_CENTRE,7)
        cats=wx.GetApp().config.Read("importdialog/filtercategories", "")
        if len(cats):
            self.categorieswanted=cats.split(";")
        else:
            self.categorieswanted=None
        self.categoriesbutton=wx.Button(self, wx.NewId(), "Categories...")
        hbs.Add(self.categoriesbutton, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTRE, 10)
        self.categorieslabel=wx.StaticText(self, -1, "")
        if self.categorieswanted is None:
            self.categorieslabel.SetLabel("*ANY*")
        else:
            self.categorieslabel.SetLabel("; ".join(self.categorieswanted))
        hbs.Add(self.categorieslabel, 1, wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL|wx.LEFT, 5)
        vbs.Add(hbs,0, wx.EXPAND|wx.ALL,5)
        # Full name options: Full Name, First M Last, or Last, First M
        self._name_option=wx.RadioBox(self, -1, 'Name Reformat',
                                      choices=['No Reformat', 'First M Last', 'Last, First M'])
        wx.EVT_RADIOBOX(self, self._name_option.GetId(),
                        self.DataNeedsUpdate)
        vbs.Add(self._name_option, 0, wx.ALL, 5)
        # Preview grid row
        self.preview=PreviewGrid(self, wx.NewId())
        self.preview.CreateGrid(10,10)
        self.preview.SetColLabelSize(0)
        self.preview.SetRowLabelSize(0)
        self.preview.SetMargins(1,0)

        vbs.Add(self.preview, 1, wx.EXPAND|wx.ALL, 5)
        # Static line and buttons
        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL,5)
        _button_sizer=self.CreateButtonSizer(wx.CANCEL|wx.HELP)
        _btn=wx.Button(self, -1, 'Merge')
        _button_sizer.Add(_btn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        wx.EVT_BUTTON(self, _btn.GetId(), self.OnOk)
        _btn=wx.Button(self, -1, 'Replace All')
        _button_sizer.Add(_btn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        wx.EVT_BUTTON(self, _btn.GetId(), self.OnReplaceAll)
        vbs.Add(_button_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        self.SetSizer(vbs)
        for w in self.wname, self.wnumber, self.waddress, self.wemail:
            wx.EVT_CHECKBOX(self, w.GetId(), self.DataNeedsUpdate)

        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
        wx.EVT_CLOSE(self, self.OnClose)
        wx.EVT_BUTTON(self, self.categoriesbutton.GetId(), self.OnCategories)

        guiwidgets.set_size("importdialog", self, 90)
        
        self.DataNeedsUpdate()

    def DataNeedsUpdate(self, _=None):
        "The preview data needs to be updated"
        self.needsupdate=True
        wx.CallAfter(self.UpdateData)

    def OnGridCellChanged(self, event):
        "Called when the user has changed one of the columns"
        self.columns[event.GetCol()]=self.preview.GetCellValue(0, event.GetCol())
        self.wcolumnsname.SetValue("Custom")
        if self.wname.GetValue() or self.wnumber.GetValue() or self.waddress.GetValue() or self.wemail.GetValue():
            self.DataNeedsUpdate()

    def OnClose(self, event=None):
        # save various config pieces
        guiwidgets.save_size("importdialog", self.GetRect())
        cfg=lambda key, value: wx.GetApp().config.WriteInt("importdialog/filter"+key, value)
        cfg("name", self.wname.GetValue())
        cfg("phonenumber", self.wnumber.GetValue())
        cfg("postaladdress", self.waddress.GetValue())
        cfg("emailaddress", self.wemail.GetValue())
        if self.categorieswanted is None:
            cats=""
        else:
            cats=";".join(self.categorieswanted)
        wx.GetApp().config.Write("importdialog/filtercategories", cats)
        wx.GetApp().config.Flush()
        if event is not None:
            event.Skip()

    def OnOk(self,_):
        "Ok button was pressed"
        if self.preview.IsCellEditControlEnabled():
            self.preview.HideCellEditControl()
            self.preview.SaveEditControlValue()
        self.OnClose()  # for some reason this isn't called automatically
        self.EndModal(wx.ID_OK)

    def OnReplaceAll(self, evt):
        "ReplaceAll button was pressed"
        self.merge=False
        self.OnOk(evt)

    def _reformat_name_firstmiddlelast(self, entry):
        # reformat the full name to be First Middle Last
        _name=entry.get('names', [None])[0]
        if not _name:
            return entry
        _s=nameparser.formatsimplefirstlast(_name)
        if _s:
            _name['full']=_s
            entry['names']=[_name]
        return entry
    def _reformat_name_lastfirtsmiddle(self, entry):
        # reformat the full name to be Last, First Middle
        _name=entry.get('names', [None])[0]
        if not _name:
            return entry
        _s=nameparser.formatsimplelastfirst(_name)
        if _s:
            _name['full']=_s
            entry['names']=[_name]
        return entry
    _reformat_name_func=(lambda self, entry: entry,
                         _reformat_name_firstmiddlelast,
                         _reformat_name_lastfirtsmiddle)
    def __build_entry(self, rec):
        entry={}
        # emails
        emails=[]
        if rec.has_key('Email Address'):
            for e in rec['Email Address']:
                if isinstance(e, dict):
                    emails.append(e)
                else:
                    emails.append({'email': e})
            del rec['Email Address']
        if rec.has_key("Email Addresses"):
            for e in rec['Email Addresses']:
                emails.append({'email': e})
            del rec["Email Addresses"]
        if len(emails):
            entry['emails']=emails
        # addresses
        for prefix,fields in \
                ( ("Home", self.filterhomeaddresscolumns),
                  ("Business", self.filterbusinessaddresscolumns)
                  ):
            addr={}
            for k in fields:
                if k in rec:
                    # it has a field for this type
                    shortk=k[len(prefix)+1:]
                    addr['type']=prefix.lower()
                    addr[self.addressmap[shortk]]=rec[k]
                    del rec[k]
            if len(addr):
                if prefix=="Business" and rec.has_key("Company"):
                    # fill in company info
                    addr['type']=prefix.lower()
                    addr['company']=rec["Company"]
                if not entry.has_key("addresses"):
                    entry["addresses"]=[]
                entry["addresses"].append(addr)
        # address (dict form of addresses)
        if rec.has_key("Address"):
            # ensure result key exists
            if not entry.has_key("addresses"):
                entry["addresses"]=[]
            # find the company name
            company=rec.get("Company", None)
            for a in rec["Address"]:
                if a["type"]=="business": a["company"]=company
                addr={}
                for k in ("type", "company", "street", "street2", "city", "state", "postalcode", "country"):
                    v=a.get(k, None)
                    if v is not None: addr[k]=v
                entry["addresses"].append(addr)
            del rec["Address"]
        # numbers
        numbers=[]
        for field in self.filternumbercolumns:
            if field!="Phone" and rec.has_key(field):
                for val in rec[field]:
                    numbers.append({'type': self.numbermap[field], 'number': phonenumber.normalise(val)})
                del rec[field]
        # phones (dict form of numbers)
        if rec.has_key("Phone"):
            mapping={"business": "office", "business fax": "fax", "home fax": "fax"}
            for val in rec["Phone"]:
                number={"type": mapping.get(val["type"], val["type"]),
                        "number": phonenumber.normalise(val["number"])}
                sd=val.get('speeddial', None)
                if sd is not None:
                    number.update({ 'speeddial': sd })
                numbers.append(number)
            del rec["Phone"]
        if len(numbers):
            entry["numbers"]=numbers
                
        # names
        name={}
        for field in self.filternamecolumns:
            if field in rec:
                name[self.namemap[field]]=rec[field]
                del rec[field]
        if len(name):
            entry["names"]=[name]
        # notes
        if rec.has_key("Notes"):
            notes=[]
            for note in rec["Notes"]:
                notes.append({'memo': note})
            del rec["Notes"]
            entry["memos"]=notes
        # web pages
        urls=[]
        for type, key in ( (None, "Web Page"),
                          ("home", "Home Web Page"),
                          ("business", "Business Web Page")
                          ):
            if rec.has_key(key):
                for url in rec[key]:
                    if isinstance(url, dict):
                        u=url
                    else:
                        u={'url': url}
                        if type is not None:
                            u['type']=type
                    urls.append(u)
                del rec[key]
        if len(urls):
            entry["urls"]=urls
        # categories
        cats=[]
        if rec.has_key("Category"):
            cats=rec['Category']
            del rec["Category"]
        if rec.has_key("Categories"):
            # multiple entries in the field, semi-colon seperated
            if isinstance(rec['Categories'], list):
                cats+=rec['Categories']
            else:
                for cat in rec['Categories'].split(';'):
                    cats.append(cat)
            del rec['Categories']
        _cats=[]
        if self.categorieswanted is not None:
            for c in self.categorieswanted:
                if c in cats:
                    _cats.append({'category': c })
        if _cats:
            entry["categories"]=_cats
        # wallpapers
        l=[]
        r=rec.get('Wallpapers', None)
        if r is not None:
            if isinstance(r, list):
                l=[{'wallpaper': x, 'use': 'call' } for x in r]
            else:
                l=[{'wallpaper': x, 'use': 'call' } for x in r.split(';')]
            del rec['Wallpapers']
        if len(l):
            entry['wallpapers']=l
        # ringtones
        l=[]
        r=rec.get('Ringtones', None)
        if r is not None:
            if isinstance(r, list):
                l=[{'ringtone': x, 'use': 'call'} for x in r]
            else:
                l=[{'ringtone': x, 'use': 'call'} for x in r.split(';')]
            del rec['Ringtones']
        if len(l):
            entry['ringtones']=l
        # flags
        flags=[]
        if rec.has_key("Private"):
            private=True
            # lets see how they have done false
            if rec["Private"].lower() in ("false", "no", 0, "0"):
                private=False
            flags.append({'secret': private})
            del rec["Private"]
            
        if len(flags):
            entry["flags"]=flags

        # unique serials
        serial={}
        for k in rec.keys():
            if k.startswith("UniqueSerial-"):
                v=rec[k]
                del rec[k]
                k=k[len("UniqueSerial-"):]
                serial[k]=v
        if len(serial):
            assert serial.has_key("sourcetype")
            if len(serial)>1: # ie more than just sourcetype
                entry["serials"]=[serial]
        # Did we forget anything?
        # Company is part of other fields
        if rec.has_key("Company"): del rec["Company"]
        if len(rec):
            raise Exception(
                "Internal conversion failed to complete.\nStill to do: %s" % rec)
        return entry

    def __build_bp_entry(self, rec):
        entry={}
        for idx,col in enumerate(self.columns):
            # build the entry from the colum data
            key=col[:col.find('_')]
            field=col[col.find('_')+1:]
            v=rec[idx]
            if not len(v):
                v=None
            if not entry.has_key(key):
                entry[key]=[]
            done=False
            for field_idx,n in enumerate(entry[key]):
                if not n.has_key(field):
                    entry[key][field_idx][field]=v
                    done=True
                    break
            if not done:
                entry[key].append({ field: v })
        # go through and delete all blanks fields/dicts
        for k,e in entry.items():
            for i1,d in enumerate(e):
                for k2,item in d.items():
                    if item is None:
                        del entry[k][i1][k2]
                    else:
                        if k2=='speeddial':
                            d[k2]=int(item)
                        elif k2=='secret':
                            d[k2]=True
                            if item.lower() in ("false", "no", 0, "0"):
                                d[k2]=False
            l=[x for x in entry[k] if len(x)]
            if len(l):
                entry[k]=l
            else:
                del entry[k]
        return entry
        
    def GetFormattedData(self):
        "Returns the data in BitPim phonebook format"
        bp_csv=True
        for c in self.columns:
            if c=="<ignore>":
                continue
            if c not in self.bp_columns:
                bp_csv=False
                break
        res={}
        count=0
        for record in self.data:
            if bp_csv:
                _entry=self.__build_bp_entry(record)
            else:                
                # make a dict of the record
                rec={}
                for n in range(len(self.columns)):
                    c=self.columns[n]
                    if c=="<ignore>":
                        continue
                    if record[n] is None or len(record[n])==0:
                        continue
                    if c not in self.bp_columns:
                        bp_csv=False
                    if c in self.filternumbercolumns or c in \
                       ["Category", "Notes", "Business Web Page", "Home Web Page", "Web Page", "Notes", "Phone", "Address", "Email Address"]:
                        # these are multivalued
                        if not rec.has_key(c):
                            rec[c]=[]
                        rec[c].append(record[n])
                    else:
                        rec[c]=record[n]
                # entry is what we are building.  fields are removed from rec as we process them
                _entry=self.__build_entry(rec)
            res[count]=self._reformat_name_func[self._name_option.GetSelection()](self,
                                                                                  _entry)
            count+=1
        return res

    def GetExtractCategoriesFunction(self):
        res=""
        for col,name in enumerate(self.columns):
            if name=="Categories":
                res+="_getpreviewformatted(row[%d], %s).split(';') + " % (col, `name`)
            elif name=="Category":
                res+="_getpreviewformatted(row[%d], %s) + " % (col, `name`)
        res+="[]"
        fn=compile(res, "_GetExtractCategoriesFunction_", 'eval')
        return lambda row: eval(fn, globals(), {'row': row})


    def OnCategories(self, _):
        # find all categories in current unfiltered data
        savedcolumns,saveddata=self.columns, self.data
        if self.categorieswanted is not None:
            # we have to re-read the data if currently filtering categories!  This is
            # because it would contain only the currently selected categories.
            self.ReReadData()  
        catfn=self.GetExtractCategoriesFunction()
        cats=[]
        for row in self.data:
            for c in catfn(row):
                if c not in cats:
                    cats.append(c)
        cats.sort()
        if len(cats) and cats[0]=="":
            cats=cats[1:]
        self.columns,self.data=savedcolumns, saveddata
        with guihelper.WXDialogWrapper(CategorySelectorDialog(self, self.categorieswanted, cats),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.categorieswanted=dlg.GetCategories()
                if self.categorieswanted is None:
                    self.categorieslabel.SetLabel("*ALL*")
                else:
                    self.categorieslabel.SetLabel("; ".join(self.categorieswanted))
                self.DataNeedsUpdate()

    @guihelper.BusyWrapper
    def UpdateData(self):
        "Actually update the preview data"
        if not self.needsupdate:
            return
        self.needsupdate=False
        # reread the data
        self.ReReadData()
        # category filtering
        if self.categorieswanted is not None:
            newdata=[]
            catfn=self.GetExtractCategoriesFunction()
            for row in self.data:
                for cat in catfn(row):
                    if cat in self.categorieswanted:
                        newdata.append(row)
                        break
            self.data=newdata

        # name/number/address/email filtering
        if self.wname.GetValue() or self.wnumber.GetValue() or self.waddress.GetValue() or self.wemail.GetValue():
            newdata=[]
            for rownum in range(len(self.data)):
                # generate a list of fields for which this row has data
                fields=[]
                # how many filters are required
                req=0
                # how many are present
                present=0
                for n in range(len(self.columns)):
                    v=self.data[rownum][n]
                    if v is not None and len(v):
                        fields.append(self.columns[n])
                for widget,filter in ( (self.wname, self.filternamecolumns),
                                       (self.wnumber, self.filternumbercolumns),
                                       (self.waddress, self.filteraddresscolumns),
                                       (self.wemail, self.filteremailcolumns)
                                       ):
                    if widget.GetValue():
                        req+=1
                        for f in fields:
                            if f in filter:
                                present+=1
                                break
                    if req>present:
                        break
                if present==req:
                    newdata.append(self.data[rownum])
            self.data=newdata

        self.FillPreview()

    def _preview_format_name_none(self, row, col, names_col):
        # no format needed
        return row[col]
    def _preview_format_name_lastfirtmiddle(self, row, col, names_col):
        # reformat to Last, First Middle
        _last=names_col.get('Last Name',
                            names_col.get('names_last', None))
        _first=names_col.get('First Name',
                             names_col.get('names_first', None))
        _middle=names_col.get('Middle Name',
                              names_col.get('names_middle', None))
        _full=names_col.get('Name',
                            names_col.get('names_full', None))
        _name_dict={}
        for _key,_value in (('full', _full), ('first', _first),
                            ('middle', _middle), ('last', _last)):
            if _value is not None and row[_value]:
                _name_dict[_key]=row[_value]
        return nameparser.formatsimplelastfirst(_name_dict)
    def _preview_format_name_firstmiddlelast(self, row, col, names_col):
        # reformat to First Middle Last
        _last=names_col.get('Last Name',
                            names_col.get('names_last', None))
        _first=names_col.get('First Name',
                             names_col.get('names_first', None))
        _middle=names_col.get('Middle Name',
                              names_col.get('names_middle', None))
        _full=names_col.get('Name',
                            names_col.get('names_full', None))
        _name_dict={}
        for _key,_value in (('full', _full), ('first', _first),
                            ('middle', _middle), ('last', _last)):
            if _value is not None and row[_value]:
                _name_dict[_key]=row[_value]
        return nameparser.formatsimplefirstlast(_name_dict)
    _preview_format_names_func=(_preview_format_name_none,
                                _preview_format_name_firstmiddlelast,
                                _preview_format_name_lastfirtmiddle)
        
    def FillPreview(self):
        self.preview.BeginBatch()
        if self.preview.GetNumberCols():
            self.preview.DeleteCols(0,self.preview.GetNumberCols())
        self.preview.DeleteRows(0,self.preview.GetNumberRows())
        self.preview.ClearGrid()
        
        numrows=len(self.data)
        if numrows:
            numcols=max(map(lambda x: len(x), self.data))
        else:
            numcols=len(self.columns)
        # add header row
        editor=wx.grid.GridCellChoiceEditor(self.possiblecolumns, False)
        self.preview.AppendRows(1)
        self.preview.AppendCols(numcols)
        _names_col={}
        for col in range(numcols):
            if 'Name' in self.columns[col] or \
               'names_' in self.columns[col]:
                _names_col[self.columns[col]]=col
            self.preview.SetCellValue(0, col, self.columns[col])
            self.preview.SetCellEditor(0, col, editor)
        attr=wx.grid.GridCellAttr()
        attr.SetBackgroundColour(wx.GREEN)
        attr.SetFont(wx.Font(10,wx.SWISS, wx.NORMAL, wx.BOLD))
        attr.SetReadOnly(not self.headerrowiseditable)
        self.preview.SetRowAttr(0,attr)
        # add each row
        oddattr=wx.grid.GridCellAttr()
        oddattr.SetBackgroundColour("OLDLACE")
        oddattr.SetReadOnly(True)
        evenattr=wx.grid.GridCellAttr()
        evenattr.SetBackgroundColour("ALICE BLUE")
        evenattr.SetReadOnly(True)
        _format_name=self._preview_format_names_func[self._name_option.GetSelection()]
        for row in range(numrows):
            self.preview.AppendRows(1)
            for col in range(numcols):
                if self.columns[col] in ('Name', 'names_full'):
                    s=_format_name(self, self.data[row], col, _names_col)
                else:
                    s=_getpreviewformatted(self.data[row][col], self.columns[col])
                if len(s):
                    self.preview.SetCellValue(row+1, col, s)
            self.preview.SetRowAttr(row+1, (evenattr,oddattr)[row%2])
        self.preview.AutoSizeColumns()
        self.preview.AutoSizeRows()
        self.preview.EndBatch()

def _getpreviewformatted(value, column):
    if value is None: return ""
    if isinstance(value, dict):
        if column=="Email Address":
            value="%s (%s)" %(value["email"], value["type"])
        elif column=="Web Page":
            value="%s (%s)" %(value["url"], value["type"])
        elif column=="Phone":
            value="%s (%s)" %(phonenumber.format(value["number"]), value["type"])
        elif column=="Address":
            v=[]
            for f in ("company", "pobox", "street", "street2", "city", "state", "postalcode", "country"):
                vv=value.get(f, None)
                if vv is not None:
                    v.append(vv)
            assert len(v)
            v[0]=v[0]+"  (%s)" %(value['type'],)
            value="\n".join(v)
        else:
            print "don't know how to convert dict",value,"for preview column",column
            assert False
    elif isinstance(value, list):
        if column=="Email Addresses":
            value="\n".join(value)
        elif column=="Categories":
            value=";".join(value)
        else:
            print "don't know how to convert list",value,"for preview column",column
            assert False
    return common.strorunicode(value)


class CategorySelectorDialog(wx.Dialog):

    def __init__(self, parent, categorieswanted, categoriesavailable):
        wx.Dialog.__init__(self, parent, title="Import Category Selector", style=wx.CAPTION|wx.MAXIMIZE_BOX|\
                 wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER) #, size=(640,480))
        vbs=wx.BoxSizer(wx.VERTICAL)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        self.selected=wx.RadioButton(self, wx.NewId(), "Selected Below", style=wx.RB_GROUP)
        self.any=wx.RadioButton(self, wx.NewId(), "Any/All")
        hbs.Add(self.selected, 0, wx.ALL, 5)
        hbs.Add(self.any, 0, wx.ALL, 5)
        _up=wx.BitmapButton(self, -1,
                            wx.ArtProvider.GetBitmap(guihelper.ART_ARROW_UP, wx.ART_TOOLBAR,
                                                     wx.Size(16, 16)))
        _dn=wx.BitmapButton(self, -1,
                            wx.ArtProvider.GetBitmap(guihelper.ART_ARROW_DOWN, wx.ART_TOOLBAR,
                                                     wx.Size(16, 16)))
        hbs.Add(_up, 0, wx.ALL, 5)
        wx.EVT_BUTTON(self, _up.GetId(), self.OnMoveUp)
        wx.EVT_BUTTON(self, _dn.GetId(), self.OnMoveDown)
        hbs.Add(_dn, 0, wx.ALL, 5)
        vbs.Add(hbs, 0, wx.ALL, 5)

        self.categoriesavailable=categoriesavailable
        self.cats=wx.CheckListBox(self, wx.NewId(), choices=categoriesavailable)
        vbs.Add(self.cats, 1, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL,5)
        vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALIGN_CENTER|wx.ALL, 5)

        if categorieswanted is None:
            self.any.SetValue(True)
            self.selected.SetValue(False)
        else:
            self.any.SetValue(False)
            self.selected.SetValue(True)
            for c in categorieswanted:
                try:
                    self.cats.Check(categoriesavailable.index(c))
                except ValueError:
                    pass # had one selected that wasn't in list

        wx.EVT_CHECKLISTBOX(self, self.cats.GetId(), self.OnCatsList)

        self.SetSizer(vbs)
        vbs.Fit(self)

    def OnCatsList(self, _):
        self.any.SetValue(False)
        self.selected.SetValue(True)

    def GetCategories(self):
        if self.any.GetValue():
            return None
        return [self.cats.GetString(x) for x in range(len(self.categoriesavailable)) if self.cats.IsChecked(x)]

    def _populate(self):
        _sel_str=self.cats.GetStringSelection()
        _chk=self.GetCategories()
        if _chk is None:
            _chk=[]
        self.cats.Clear()
        for s in self.categoriesavailable:
            i=self.cats.Append(s)
            if s==_sel_str:
                self.cats.SetSelection(i)
            self.cats.Check(i, s in _chk)

    def OnMoveUp(self, _):
        _sel_idx=self.cats.GetSelection()
        if _sel_idx==wx.NOT_FOUND or not _sel_idx:
            # no selection or top item
            return
        # move the selected item one up
        self.categoriesavailable[_sel_idx], self.categoriesavailable[_sel_idx-1]=\
        self.categoriesavailable[_sel_idx-1], self.categoriesavailable[_sel_idx]
        self._populate()

    def OnMoveDown(self, _):
        _sel_idx=self.cats.GetSelection()
        if _sel_idx==wx.NOT_FOUND or \
           _sel_idx==len(self.categoriesavailable)-1:
            # no selection or bottom item
            return
        # move the selected item one up
        self.categoriesavailable[_sel_idx], self.categoriesavailable[_sel_idx+1]=\
        self.categoriesavailable[_sel_idx+1], self.categoriesavailable[_sel_idx]
        self._populate()

class ImportCSVDialog(ImportDialog):

    delimiternames={
        '\t': "Tab",
        ' ': "Space",
        ',': "Comma"
        }

    def __init__(self, filename, parent, id, title):
        self.headerrowiseditable=True
        self.filename=filename
        self.UpdatePredefinedColumns()
        ImportDialog.__init__(self, parent, id, title)

    def gethtmlhelp(self):
        "Returns tuple of help text and size"
        bg=self.GetBackgroundColour()
        return '<html><body BGCOLOR="#%02X%02X%02X">Importing %s.  BitPim has guessed the delimiter seperating each column, and the text qualifier that quotes values.  You need to select what each column is by clicking in the top row, or select one of the predefined sets of columns.</body></html>' % (bg.Red(), bg.Green(), bg.Blue(), self.filename), \
                (600,100)

    def getcontrols(self, vbs):
        data=common.opentextfile(self.filename).read()
        # turn all EOL chars into \n and then ensure only one \n terminates each line
        data=data.replace("\r", "\n")
        oldlen=-1
        while len(data)!=oldlen:
            oldlen=len(data)
            data=data.replace("\n\n", "\n")
            
        self.rawdata=data

        self.qualifier=DSV.guessTextQualifier(self.rawdata)
        if self.qualifier is None or len(self.qualifier)==0:
            self.qualifier='"'
        self.data=DSV.organizeIntoLines(self.rawdata, textQualifier=self.qualifier)
        self.delimiter=DSV.guessDelimiter(self.data)
        # sometimes it picks the letter 'w'
        if self.delimiter is not None and self.delimiter.lower() in "abcdefghijklmnopqrstuvwxyz":
            self.delimiter=None
        if self.delimiter is None:
            if self.filename.lower().endswith("tsv"):
                self.delimiter="\t"
            else:
                self.delimiter=","
        # complete processing the data otherwise we can't guess if first row is headers
        self.data=DSV.importDSV(self.data, delimiter=self.delimiter, textQualifier=self.qualifier, errorHandler=DSV.padRow)
        # Delimter and Qualifier row
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.StaticText(self, -1, "Delimiter"), 0, wx.EXPAND|wx.ALL|wx.ALIGN_CENTRE, 2)
        self.wdelimiter=wx.ComboBox(self, wx.NewId(), self.PrettyDelimiter(self.delimiter), choices=self.delimiternames.values(), style=wx.CB_DROPDOWN|wx.WANTS_CHARS)
        hbs.Add(self.wdelimiter, 1, wx.EXPAND|wx.ALL, 2)
        hbs.Add(wx.StaticText(self, -1, "Text Qualifier"), 0, wx.EXPAND|wx.ALL|wx.ALIGN_CENTRE,2)
        self.wqualifier=wx.ComboBox(self, wx.NewId(), self.qualifier, choices=['"', "'", "(None)"], style=wx.CB_DROPDOWN|wx.WANTS_CHARS)
        hbs.Add(self.wqualifier, 1, wx.EXPAND|wx.ALL, 2)
        vbs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)
        # Pre-set columns, save and header row
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.StaticText(self, -1, "Columns"), 0, wx.EXPAND|wx.ALL|wx.ALIGN_CENTRE, 2)
        self.wcolumnsname=wx.ComboBox(self, wx.NewId(), "Custom", choices=self.predefinedcolumns+["Custom"], style=wx.CB_READONLY|wx.CB_DROPDOWN|wx.WANTS_CHARS)
        hbs.Add(self.wcolumnsname, 1, wx.EXPAND|wx.ALL, 2)
        self.wfirstisheader=wx.CheckBox(self, wx.NewId(), "First row is header")
        self.wfirstisheader.SetValue(DSV.guessHeaders(self.data))
        hbs.Add(self.wfirstisheader, 0, wx.EXPAND|wx.ALL|wx.ALIGN_CENTRE, 5)
        vbs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)

        # event handlers
        wx.EVT_CHECKBOX(self, self.wfirstisheader.GetId(), self.OnHeaderToggle)
        wx.grid.EVT_GRID_CELL_CHANGE(self, self.OnGridCellChanged)
        wx.EVT_TEXT(self, self.wdelimiter.GetId(), self.OnDelimiterChanged)
        wx.EVT_TEXT(self, self.wqualifier.GetId(), self.OnQualifierChanged)
        wx.EVT_TEXT(self, self.wcolumnsname.GetId(), self.OnColumnsNameChanged)

    def PrettyDelimiter(self, delim):
        "Returns a pretty version of the delimiter (eg Tab, Space instead of \t, ' ')"
        assert delim is not None
        if delim in self.delimiternames:
            return self.delimiternames[delim]
        return delim
        
    def UpdatePredefinedColumns(self):
        """Updates the list of pre-defined column names.

        We look for files with an extension of .pdc in the resource directory.  The first
        line of the file is the description, and each remaining line corresponds to a
        column"""
        self.predefinedcolumns=[]
        for i in guihelper.getresourcefiles("*.pdc"):
            with contextlib.closing(common.opentextfile(i)) as f:
                self.predefinedcolumns.append(f.readline().strip())

    def OnHeaderToggle(self, _):
        self.columns=None
        self.DataNeedsUpdate()

    def OnDelimiterChanged(self, _):
        "Called when the user has changed the delimiter"
        text=self.wdelimiter.GetValue()
        if hasattr(self, "lastwdelimitervalue") and self.lastwdelimitervalue==text:
            print "on delim changed ignored"
            return

        if len(text)!=1:
            if text in self.delimiternames.values():
                for k in self.delimiternames:
                    if self.delimiternames[k]==text:
                        text=k
            else:
                if len(text)==0:
                    text="Comma"
                else:
                    text=text[-1]
                    if text in self.delimiternames:
                        text=self.delimiternames[text]
                self.wdelimiter.SetValue(text)
        self.delimiter=text
        self.columns=None
        self.DataNeedsUpdate()
        # these calls cause another OnDelimiterChanged callback to happen, so we have to stop the loop
        self.lastwdelimitervalue=self.wdelimiter.GetValue()
        wx.CallAfter(self.wdelimiter.SetInsertionPointEnd)
        wx.CallAfter(self.wdelimiter.SetMark, 0,len(self.wdelimiter.GetValue()))

    def OnQualifierChanged(self,_):
        "Called when the user has changed the qualifier"
        # Very similar to the above function
        text=self.wqualifier.GetValue()
        if hasattr(self, "lastwqualifiervalue") and self.lastwqualifiervalue==text:
            return
        if len(text)!=1:
            if text=='(None)':
                text=None
            else:
                if len(text)==0:
                    self.wqualifier.SetValue('(None)')
                    text=None
                else:
                    text=text[-1]
                    self.wqualifier.SetValue(text)
        self.qualifier=text
        self.columns=None
        self.DataNeedsUpdate()
        self.lastwqualifiervalue=self.wqualifier.GetValue()
        wx.CallAfter(self.wqualifier.SetInsertionPointEnd)
        wx.CallAfter(self.wqualifier.SetMark, 0,len(self.wqualifier.GetValue()))
        
    def OnColumnsNameChanged(self,_):
        if self.wcolumnsname.GetValue()=="Custom":
            return
        str=self.wcolumnsname.GetValue()
        for file in guihelper.getresourcefiles("*.pdc"):
            with contextlib.closing(common.opentextfile(file)) as f:
                desc=f.readline().strip()
                if desc==str:
                    self.columns=map(string.strip, f.readlines())
                    for i in range(len(self.columns)):
                        if self.columns[i] not in self.possiblecolumns:
                            print self.columns[i],"is not a valid column name!"
                            self.columns[i]="<ignore>"
                    self.DataNeedsUpdate()
                    return
        print "didn't find pdc for",str

    def ReReadData(self):
        self.data=DSV.organizeIntoLines(self.rawdata, textQualifier=self.qualifier)
        self.data=DSV.importDSV(self.data, delimiter=self.delimiter, textQualifier=self.qualifier, errorHandler=DSV.padRow)
        self.FigureOutColumns()

    def FigureOutColumns(self):
        "Initialize the columns variable, using header row if there is one"
        numcols=max(map(lambda x: len(x), self.data))
        # normalize number of columns
        for row in self.data:
            while len(row)<numcols:
                row.append('')
        guesscols=False
        if not hasattr(self, "columns") or self.columns is None:
            self.columns=["<ignore>"]*numcols
            guesscols=True
        while len(self.columns)<numcols:
            self.columns.append("<ignore>")
        self.columns=self.columns[:numcols]
        if not self.wfirstisheader.GetValue():
            return
        headers=self.data[0]
        self.data=self.data[1:]
        if not guesscols:
            return
        mungedcolumns=[]
        for c in self.possiblecolumns:
            mungedcolumns.append("".join(filter(lambda x: x in "abcdefghijklmnopqrstuvwxyz0123456789", c.lower())))
        # look for header in possible columns
        for col,header in zip(range(numcols), headers):
            if header in self.possiblecolumns:
                self.columns[col]=header
                continue
            h="".join(filter(lambda x: x in "abcdefghijklmnopqrstuvwxyz0123456789", header.lower()))
            
            if h in mungedcolumns:
                self.columns[col]=self.possiblecolumns[mungedcolumns.index(h)]
                continue
            # here is where we would do some mapping

class ImportOutlookDialog(ImportDialog):
    # the order of this mapping matters ....
    importmapping=(
        # first column is field in Outlook
        # second column is field in dialog (ImportDialog.possiblecolumns)
        ('FirstName',            "First Name" ),
        ('LastName',             "Last Name"),
        ('MiddleName',           "Middle Name"),
        # ('FullName',  ),       -- this includes the prefix (aka title in Outlook) and the suffix
        # ('Title',  ),          -- the prefix (eg Dr, Mr, Mrs)
        ('Subject',              "Name"),  # this is first middle last suffix - note no prefix!
        # ('Suffix',  ),         -- Jr, Sr, III etc
        ('NickName',             "Nickname"),
        ('Email1Address',        "Email Address"),
        ('Email2Address',        "Email Address"),
        ('Email3Address',        "Email Address"),
        # Outlook is seriously screwed over web pages.  It treats the Business Home Page
        # and Web Page as the same field, so we can't really tell the difference.
        ('WebPage',              "Web Page"),
        ('OtherFaxNumber',       "Fax"  ),
        ('HomeAddressStreet',    "Home Street"),
        ('HomeAddressCity',      "Home City" ),
        ('HomeAddressPostalCode',"Home Postal Code"  ),
        ('HomeAddressState',     "Home State"),
        ('HomeAddressCountry',   "Home Country/Region" ),
        ('HomeTelephoneNumber',  "Home Phone"),
        ('Home2TelephoneNumber', "Home Phone"),
        ('HomeFaxNumber',        "Home Fax"),
        ('MobileTelephoneNumber',"Mobile Phone"),
        ('PersonalHomePage',     "Home Web Page"),

        ('BusinessAddressStreet',"Business Street"),
        ('BusinessAddressCity',  "Business City"),
        ('BusinessAddressPostalCode', "Business Postal Code"),
        ('BusinessAddressState', "Business State"),
        ('BusinessAddressCountry', "Business Country/Region"),
        # ('BusinessHomePage',), -- no use, see Web Page above
        ('BusinessTelephoneNumber', "Business Phone"),        
        ('Business2TelephoneNumber',"Business Phone"),
        ('BusinessFaxNumber',    "Business Fax"),
        ('PagerNumber',          "Pager"),
        ('CompanyName',          "Company"),
        
        ('Body',                 "Notes"),  # yes, really

        ('Categories',           "Categories"),


        ('EntryID',              "UniqueSerial-EntryID"),
        
        )

    
    # These are all the fields we do nothing about
##           ('Anniversary',  ),
##           ('AssistantName',  ),
##           ('AssistantTelephoneNumber',  ),
##           ('Birthday',  ),
##           ('BusinessAddress',  ),
##           ('BusinessAddressPostOfficeBox',  ),
##           ('CallbackTelephoneNumber',  ),
##           ('CarTelephoneNumber',  ),
##           ('Children',  ),
##           ('Class',  ),
##           ('CompanyAndFullName',  ),
##           ('CompanyLastFirstNoSpace',  ),
##           ('CompanyLastFirstSpaceOnly',  ),
##           ('CompanyMainTelephoneNumber',  ),
##           ('ComputerNetworkName',  ),
##           ('ConversationIndex',  ),
##           ('ConversationTopic',  ),
##           ('CreationTime',  ),
##           ('CustomerID',  ),
##           ('Department',  ),
##           ('FTPSite',  ),
##           ('FileAs',  ),
##           ('FullNameAndCompany',  ),
##           ('Gender',  ),
##           ('GovernmentIDNumber',  ),
##           ('Hobby',  ),
##           ('HomeAddress',  ),
##           ('HomeAddressPostOfficeBox',  ),
##           ('ISDNNumber',  ),
##           ('Importance',  ),
##           ('Initials',  ),
##           ('InternetFreeBusyAddress',  ),
##           ('JobTitle',  ),
##           ('Journal',  ),
##           ('Language',  ),
##           ('LastFirstAndSuffix',  ),
##           ('LastFirstNoSpace',  ),
##           ('LastFirstNoSpaceCompany',  ),
##           ('LastFirstSpaceOnly',  ),
##           ('LastFirstSpaceOnlyCompany',  ),
##           ('LastModificationTime',  ),
##           ('LastNameAndFirstName',  ),
##           ('MAPIOBJECT',  ),
##           ('MailingAddress',  ),
##           ('MailingAddressCity',  ),
##           ('MailingAddressCountry',  ),
##           ('MailingAddressPostalCode',  ),
##           ('MailingAddressState',  ),
##           ('MailingAddressStreet',  ),
##           ('ManagerName',  ),
##           ('MessageClass',  ),
##           ('Mileage',  ),
##           ('NetMeetingAlias',  ),
##           ('NetMeetingServer',  ),
##           ('NoAging',  ),
##           ('OfficeLocation',  ),
##           ('OrganizationalIDNumber',  ),
##           ('OtherAddress',  ),
##           ('OtherAddressCity',  ),
##           ('OtherAddressCountry',  ),
##           ('OtherAddressPostOfficeBox',  ),
##           ('OtherAddressPostalCode',  ),
##           ('OtherAddressState',  ),
##           ('OtherAddressStreet',  ),
##           ('OtherTelephoneNumber',  ),
##           ('OutlookInternalVersion',  ),
##           ('OutlookVersion',  ),
##           ('Parent',  ),
##           ('PrimaryTelephoneNumber',  ),
##           ('Profession',  ),
##           ('RadioTelephoneNumber',  ),
##           ('ReferredBy',  ),
##           ('Saved',  ),
##           ('SelectedMailingAddress',  ),
##           ('Sensitivity',  ),
##           ('Size',  ),
##           ('Spouse',  ),
##           ('TTYTDDTelephoneNumber',  ),
##           ('TelexNumber',  ),
##           ('UnRead',  ),
##           ('User1',  ),
##           ('User2',  ),
##           ('User3',  ),
##           ('User4',  ),
 
    importmappingdict={}
    for o,i in importmapping: importmappingdict[o]=i

    def __init__(self, parent, id, title, outlook):
        self.headerrowiseditable=False
        self.outlook=outlook
        ImportDialog.__init__(self, parent, id, title)

    def gethtmlhelp(self):
        "Returns tuple of help text and size"
        bg=self.GetBackgroundColour()
        return '<html><body BGCOLOR="#%02X%02X%02X">Importing Outlook Contacts.  Select the folder to import, and do any filtering necessary.</body></html>' % (bg.Red(), bg.Green(), bg.Blue()), \
                (600,30)

    def getcontrols(self, vbs):
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        # label
        hbs.Add(wx.StaticText(self, -1, "Folder"), 0, wx.ALL|wx.ALIGN_CENTRE, 2)
        # where the folder name goes
        self.folderctrl=wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        hbs.Add(self.folderctrl, 1, wx.EXPAND|wx.ALL, 2)
        # browse button
        self.folderbrowse=wx.Button(self, wx.NewId(), "Browse ...")
        hbs.Add(self.folderbrowse, 0, wx.EXPAND|wx.ALL, 2)
        vbs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)
        wx.EVT_BUTTON(self, self.folderbrowse.GetId(), self.OnBrowse)

        # sort out folder
        id=wx.GetApp().config.Read("outlook/contacts", "")
        self.folder=self.outlook.getfolderfromid(id, True)
        wx.GetApp().config.Write("outlook/contacts", self.outlook.getfolderid(self.folder))
        self.folderctrl.SetValue(self.outlook.getfoldername(self.folder))

    def OnBrowse(self, _):
        p=self.outlook.pickfolder()
        if p is None: return # user hit cancel
        self.folder=p
        wx.GetApp().config.Write("outlook/contacts", self.outlook.getfolderid(self.folder))
        self.folderctrl.SetValue(self.outlook.getfoldername(self.folder))
        self.DataNeedsUpdate()

    def ReReadData(self):
        # this can take a really long time if the user doesn't spot the dialog
        # asking for permission to access email addresses :-)
        items=self.outlook.getcontacts(self.folder, self.importmappingdict.keys())

        # work out what keys are actually present
        keys={}
        for item in items:
            for k in item.keys():
                keys[k]=1

        # We now need to produce columns with BitPim names not the Outlook ones.
        # mappings are in self.importmapping
        want=[]
        for o,i in self.importmapping:
            if o in keys.keys():
                want.append(o)
        # want now contains list of Outlook keys we want, and the order we want them in
        
        self.columns=[self.importmappingdict[k] for k in want]
        # deal with serials
        self.columns.append("UniqueSerial-FolderID")
        self.columns.append("UniqueSerial-sourcetype")
        moredata=[ self.outlook.getfolderid(self.folder), "outlook"]

        # build up data
        self.data=[]
        for item in items:
            row=[]
            for k in want:
                v=item.get(k, None)
                v=common.strorunicode(v)
                row.append(v)
            self.data.append(row+moredata)


class ImportVCardDialog(ImportDialog):
    keymapper={
        "name": "Name",
        "notes": "Notes",
        "uid": "UniqueSerial-uid",
        "last name": "Last Name",
        "first name": "First Name",
        "middle name": "Middle Name",
        "nickname": "Nickname",
        "categories": "Categories",
        "email": "Email Address",
        "url": "Web Page",
        "phone": "Phone",
        "address": "Address",
        "organisation": "Company",
        "wallpapers": "Wallpapers",
        "ringtones": "Ringtones"
        }
    def __init__(self, filename, parent, id, title):
        self.headerrowiseditable=False
        self.filename=filename
        self.vcardcolumns,self.vcarddata=None,None
        ImportDialog.__init__(self, parent, id, title)

    def gethtmlhelp(self):
        "Returns tuple of help text and size"
        bg=self.GetBackgroundColour()
        return '<html><body BGCOLOR="#%02X%02X%02X">Importing vCard Contacts.  Verify the data and perform any filtering necessary.</body></html>' % (bg.Red(), bg.Green(), bg.Blue()), \
                (600,30)

    def getcontrols(self, vbs):
        # no extra controls
        return

    def ReReadData(self):
        if self.vcardcolumns is None or self.vcarddata is None:
                self.vcardcolumns,self.vcarddata=self.parsevcards(common.opentextfile(self.filename))
        self.columns=self.vcardcolumns
        self.data=self.vcarddata

    def parsevcards(self, file):
        # returns columns, data
        data=[]
        keys={}
        for vc in vcard.VCards(vcard.VFile(file)):
            v=vc.getdata()
            data.append(v)
            for k in v: keys[k]=1
        keys=keys.keys()
        # sort them into a natural order
        self.sortkeys(keys)
        # remove the ones we have no mapping for
        if __debug__:
            for k in keys:
                if _getstringbase(k)[0] not in self.keymapper:
                    print "vcard import: no map for key "+k
        keys=[k for k in keys if _getstringbase(k)[0] in self.keymapper]
        columns=[self.keymapper[_getstringbase(k)[0]] for k in keys]
        # build up defaults
        defaults=[]
        for c in columns:
            if c in self.possiblecolumns:
                defaults.append("")
            else:
                defaults.append(None)
        # deal with serial/UniqueId
        if len([c for c in columns if c.startswith("UniqueSerial-")]):
            columns.append("UniqueSerial-sourcetype")
            extra=["vcard"]
        else:
            extra=[]
        # do some data munging
        newdata=[]
        for row in data:
            line=[]
            for i,k in enumerate(keys):
                line.append(row.get(k, defaults[i]))
            newdata.append(line+extra)

        # return our hard work
        return columns, newdata

    # name parts, name, nick, emails, urls, phone, addresses, categories, memos
    # things we ignore: title, prefix, suffix, organisational unit
    _preferredorder=["first name", "middle name", "last name", "name", "nickname",
                     "phone", "address", "email", "url", "organisation", "categories", "notes"]

    def sortkeys(self, keys):
        po=self._preferredorder

        def funkycmpfunc(x, y, po=po):
            x=_getstringbase(x)
            y=_getstringbase(y)
            if x==y: return 0
            if x[0]==y[0]: # if the same base, use the number to compare
                return cmp(x[1], y[1])

            # find them in the preferred order list
            # (for some bizarre reason python doesn't have a method corresponding to
            # string.find on lists or tuples, and you only get index on lists
            # which throws an exception on not finding the item
            try:
                pos1=po.index(x[0])
            except ValueError: pos1=-1
            try:
                pos2=po.index(y[0])
            except ValueError: pos2=-1

            if pos1<0 and pos2<0:   return cmp(x[0], y[0])
            if pos1<0 and pos2>=0:  return 1
            if pos2<0 and pos1>=0:  return -1
            assert pos1>=0 and pos2>=0
            return cmp(pos1, pos2)

        keys.sort(funkycmpfunc)


def _getstringbase(v):
    mo=re.match(r"^(.*?)(\d+)$", v)
    if mo is None: return (v,1)
    return mo.group(1), int(mo.group(2))

class ImportEvolutionDialog(ImportVCardDialog):
    def __init__(self, parent, id, title, evolution):
        self.headerrowiseditable=False
        self.evolution=evolution
        self.evocolumns=None
        self.evodata=None
        ImportDialog.__init__(self, parent, id, title)

    def gethtmlhelp(self):
        "Returns tuple of help text and size"
        bg=self.GetBackgroundColour()
        return '<html><body BGCOLOR="#%02X%02X%02X">Importing Evolution Contacts.  Select the folder to import, and do any filtering necessary.</body></html>' % (bg.Red(), bg.Green(), bg.Blue()), \
                (600,30)

    def getcontrols(self, vbs):
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        # label
        hbs.Add(wx.StaticText(self, -1, "Folder"), 0, wx.ALL|wx.ALIGN_CENTRE, 2)
        # where the folder name goes
        self.folderctrl=wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        hbs.Add(self.folderctrl, 1, wx.EXPAND|wx.ALL, 2)
        # browse button
        self.folderbrowse=wx.Button(self, wx.NewId(), "Browse ...")
        hbs.Add(self.folderbrowse, 0, wx.EXPAND|wx.ALL, 2)
        vbs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)
        wx.EVT_BUTTON(self, self.folderbrowse.GetId(), self.OnBrowse)

        # sort out folder
        id=wx.GetApp().config.Read("evolution/contacts", "")
        self.folder=self.evolution.getfolderfromid(id, True)
        print "folder is",self.folder
        wx.GetApp().config.Write("evolution/contacts", self.evolution.getfolderid(self.folder))
        self.folderctrl.SetValue(self.evolution.getfoldername(self.folder))

    def OnBrowse(self, _):
        p=self.evolution.pickfolder(self.folder)
        if p is None: return # user hit cancel
        self.folder=p
        wx.GetApp().config.Write("evolution/contacts", self.evolution.getfolderid(self.folder))
        self.folderctrl.SetValue(self.evolution.getfoldername(self.folder))
        self.evocolumns=None
        self.evodata=None
        self.DataNeedsUpdate()

    def ReReadData(self):
        if self.evocolumns is not None and self.evodata is not None:
            self.columns=self.evocolumns
            self.data=self.evodata
            return

        vcards="\r\n".join(self.evolution.getcontacts(self.folder))

        columns,data=self.parsevcards(StringIO.StringIO(vcards))

        columns.append("UniqueSerial-folderid")
        columns.append("UniqueSerial-sourcetype")
        moredata=[self.folder, "evolution"]

        for row in data:
            row.extend(moredata)

        self.evocolumns=self.columns=columns
        self.evodata=self.data=data

class ImportQtopiaDesktopDialog(ImportDialog):
    # the order of this mapping matters ....
    importmapping=(
        # first column is field in Qtopia
        # second column is field in dialog (ImportDialog.possiblecolumns)
           ('FirstName', "First Name"  ),
           ('LastName',  "Last Name" ),
           ('MiddleName',  "Middle Name"),
           ('Nickname',   "Nickname"),
           ('Emails',   "Email Addresses"),
           ('HomeStreet',   "Home Street"),
           ('HomeCity',   "Home City"),
           ('HomeZip',   "Home Postal Code"),
           ('HomeState',  "Home State" ),
           ('HomeCountry',  "Home Country/Region" ),
           ('HomePhone',  "Home Phone" ),
           ('HomeFax',  "Home Fax" ),
           ('HomeMobile', "Mobile Phone"  ),
           ('BusinessMobile', "Mobile Phone"  ),
           ('HomeWebPage',  "Home Web Page" ),
           ('BusinessStreet',   "Business Street"),
           ('BusinessCity',  "Business City" ),
           ('BusinessZip',  "Business Postal Code" ),
           ('BusinessState',  "Business State" ),
           ('BusinessCountry',  "Business Country/Region", ),
           ('BusinessWebPage',   "Business Web Page"),
           ('BusinessPhone',   "Business Phone"),
           ('BusinessFax',  "Business Fax" ),
           ('BusinessPager', "Pager"  ),
           ('Company',  "Company" ),
           ('Notes',  "Notes" ),
           ('Categories',  "Categories" ),
           ('Uid',  "UniqueSerial-uid" ),
           
           )           

##    # the fields we ignore
        
##           ('Assistant',   )
##           ('Children',   )
##           ('DefaultEmail',   )
##           ('Department',   )
##           ('Dtmid',   )
##           ('FileAs',   )
##           ('Gender',   )
##           ('JobTitle',   )
##           ('Manager',   )
##           ('Office',   )
##           ('Profession',   )
##           ('Spouse',   )
##           ('Suffix',   )
##           ('Title',   )

    importmappingdict={}
    for o,i in importmapping: importmappingdict[o]=i

    def __init__(self, parent, id, title):
        self.headerrowiseditable=False
        self.origcolumns=self.origdata=None
        ImportDialog.__init__(self, parent, id, title)

    def gethtmlhelp(self):
        "Returns tuple of help text and size"
        bg=self.GetBackgroundColour()
        return '<html><body BGCOLOR="#%02X%02X%02X">Importing Qtopia Desktop Contacts..</body></html>' % (bg.Red(), bg.Green(), bg.Blue()), \
                (600,30)

    def getcontrols(self, vbs):
        pass

    def ReReadData(self):
        if self.origcolumns is not None and self.origdata is not None:
            self.columns=self.origcolumns
            self.data=self.origdata
            return

        import native.qtopiadesktop

        filename=native.qtopiadesktop.getfilename()
        if not os.path.isfile(filename):
            wx.MessageBox(filename+" not found.", "Qtopia file not found", wx.ICON_EXCLAMATION|wx.OK)
            self.data={}
            self.columns=[]
            return

        items=native.qtopiadesktop.getcontacts()
        
        # work out what keys are actually present
        keys={}
        for item in items:
            for k in item.keys():
                keys[k]=1

        # We now need to produce columns with BitPim names not the Qtopia ones.
        # mappings are in self.importmapping
        want=[]
        for o,i in self.importmapping:
            if o in keys.keys():
                want.append(o)
        # want now contains list of Qtopia keys we want, and the order we want them in
        
        self.columns=[self.importmappingdict[k] for k in want]
        # deal with serials
        self.columns.append("UniqueSerial-sourcetype")
        moredata=[ "qtopiadesktop"]

        # build up data
        self.data=[]
        for item in items:
            row=[]
            for k in want:
                v=item.get(k, None)
                row.append(v)
            self.data.append(row+moredata)

        self.origdata=self.data
        self.origcolumns=self.columns

# The eGroupware login handling is a bit of a mess.  Feel free to fix it.

class eGroupwareLoginDialog(wx.Dialog):

    __pwdsentinel="\x01\x02\x01\x09\x01\x01\x14\x15"


    def __init__(self, parent, module, title="Login to eGroupware"):
        wx.Dialog.__init__(self, parent, -1,  title, size=(400,-1))
        self.module=module
        gs=wx.GridBagSizer(5,5)
        for row,label in enumerate( ("URL", "Domain", "Username", "Password") ):
            gs.Add(wx.StaticText(self, -1, label), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL, pos=(row,0))
        self.curl=wx.TextCtrl(self, -1)
        self.cdomain=wx.TextCtrl(self, -1)
        self.cuser=wx.TextCtrl(self, -1)
        self.cpassword=wx.TextCtrl(self, -1, style=wx.TE_PASSWORD)
        self.csavepassword=wx.CheckBox(self, -1, "Save")
        for row,widget in enumerate( (self.curl, self.cdomain, self.cuser) ):
            gs.Add(widget, flag=wx.EXPAND, pos=(row,1), span=(1,2))
        gs.Add(self.cpassword, flag=wx.EXPAND, pos=(3,1))
        gs.Add(self.csavepassword, flag=wx.ALIGN_CENTRE, pos=(3,2))
        gs.AddGrowableCol(1)
        self.cmessage=wx.StaticText(self, -1, "Please enter your details")
        gs.Add(self.cmessage, flag=wx.EXPAND, pos=(4,0), span=(1,3))
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(gs, 0, wx.EXPAND|wx.ALL,5)
        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALIGN_CENTER|wx.ALL, 5)

        # set initial values
        cfg=wx.GetApp().config
        self.curl.SetValue(cfg.Read("egroupware/url", "http://server.example.com/egroupware"))
        self.cdomain.SetValue(cfg.Read("egroupware/domain", "default"))
        try:
            import getpass
            defuser=getpass.getuser()
        except:
            defuser="user"
        self.cuser.SetValue(cfg.Read("egroupware/user", defuser))
        p=cfg.Read("egroupware/password", "")
        if len(p):
            self.csavepassword.SetValue(True)
            self.cpassword.SetValue(self.__pwdsentinel)
    
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)
        # make the window a decent width
        self.SetDimensions(-1, -1, 500, -1, wx.SIZE_USE_EXISTING)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
        self.session=None

    def OnOk(self, evt):
        try:
            self.session=self._GetSession()
            evt.Skip() # end modal
            self.OnClose()
            return
        except Exception,e:
            self.cmessage.SetLabel(str(e))
            # go around again

    def GetSession(self, auto=False):
        """Returns the Session object from the eGroupware library
        @param auto: If true then the user interface doesn't have to be shown"""

        if auto:
            try:
                self.session=self._GetSession()
                return self.session
            except Exception,e:
                self.cmessage.SetLabel(str(e))

        self.ShowModal()
        return self.session

    def _GetSession(self):
        # lets see if the user has given us sensible params
        if self.curl.GetValue()=="http://server.example.com/egroupware":
            raise Exception("You must set the URL for the server")
        if len(self.cpassword.GetValue())==0:
            raise Exception("You must fill in the password")
        password=self.cpassword.GetValue()
        if password==self.__pwdsentinel:
            password=common.obfus_decode(wx.GetApp().config.Read("egroupware/password", ""))
        try:
            return self.module.getsession(self.curl.GetValue(), self.cuser.GetValue(), password, self.cdomain.GetValue())
        finally:
            del password

    def OnClose(self, event=None):
        cfg=wx.GetApp().config
        cfg.Write("egroupware/url", self.curl.GetValue())
        cfg.Write("egroupware/domain", self.cdomain.GetValue())
        cfg.Write("egroupware/user", self.cuser.GetValue())
        if self.csavepassword.GetValue():
            p=self.cpassword.GetValue()
            if p!=self.__pwdsentinel:
                cfg.Write("egroupware/password", common.obfus_encode(p))
        else:
            cfg.DeleteEntry("egroupware/password")


                
class ImporteGroupwareDialog(ImportDialog):

    ID_CHANGE=wx.NewId()

    def __init__(self, parent, id, title, module):
        self.headerrowiseditable=False
        self.module=module
        ImportDialog.__init__(self, parent, id, title)
        self.sp=None

    def gethtmlhelp(self):
        "Returns tuple of help text and size"
        bg=self.GetBackgroundColour()
        return '<html><body BGCOLOR="#%02X%02X%02X">Importing eGroupware Contacts..</body></html>' % (bg.Red(), bg.Green(), bg.Blue()), \
                (600,30)

    def getcontrols(self, vbs):
        # need url, username, password and domain fields
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.StaticText(self, -1, "URL"), 0, wx.ALIGN_CENTRE|wx.ALL,2)
        self.curl=wx.StaticText(self, -1)
        hbs.Add(self.curl, 3, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 2)
        hbs.Add(wx.StaticText(self, -1, "Domain"), 0, wx.ALIGN_CENTRE|wx.ALL,2)
        self.cdomain=wx.StaticText(self, -1)
        hbs.Add(self.cdomain, 1, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 2)
        hbs.Add(wx.StaticText(self, -1, "User"), 0, wx.ALIGN_CENTRE|wx.ALL,2)
        self.cuser=wx.StaticText(self, -1)
        hbs.Add(self.cuser, 1, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 2)
        self.cchange=wx.Button(self, self.ID_CHANGE, "Change ...")
        hbs.Add(self.cchange, 0, wx.ALL, 2)
        vbs.Add(hbs,0,wx.ALL,5)
        wx.EVT_BUTTON(self, self.ID_CHANGE, self.OnChangeCreds)
        self.setcreds()

    def OnChangeCreds(self,_):
        dlg=eGroupwareLoginDialog(self, self.module)
        newsp=dlg.GetSession()
        if newsp is not None:
            self.sp=newsp
            self.setcreds()
            self.DataNeedsUpdate()

    def setcreds(self):
        cfg=wx.GetApp().config
        self.curl.SetLabel(cfg.Read("egroupware/url", "http://server.example.com/egroupware"))
        self.cdomain.SetLabel(cfg.Read("egroupware/domain", "default"))
        try:
            import getpass
            defuser=getpass.getuser()
        except:
            defuser="user"
        self.cuser.SetLabel(cfg.Read("egroupware/user", defuser))        

    _preferred=( "Name", "First Name", "Middle Name", "Last Name",
                 "Address", "Address2", "Email Address", "Email Address2",
                 "Home Phone", "Mobile Phone", "Business Fax", "Pager", "Business Phone",
                 "Notes", "Business Web Page", "Categories" )

    def ReReadData(self):
        if self.sp is None:
            self.sp=eGroupwareLoginDialog(self, self.module).GetSession(auto=True)
            self.setcreds()
        self.data=[]
        self.columns=[]
        if self.sp is None:
            self.EndModal(wx.ID_CANCEL)
            return
        # work out what columns we have
        entries=[i for i in self.sp.getcontactspbformat()]
        cols=[]
        for e in entries:
            for k in e:
                if k not in cols:
                    cols.append(k)
        # now put columns in prefered order
        cols.sort()
        self.columns=[]
        for p in self._preferred:
            if p in cols:
                self.columns.append(p)
        cols=[c for c in cols if c not in self.columns]
        self.columns.extend(cols)
        # make data
        self.data=[]
        for e in entries:
            self.data.append([e.get(c,None) for c in self.columns])
        # strip trailing 2 off names in columns
        for i,c in enumerate(self.columns):
            if c.endswith("2"):
                self.columns[i]=c[:-1]


def OnFileImportCSVContacts(parent):
    with guihelper.WXDialogWrapper(wx.FileDialog(parent, "Import CSV file",
                                                 wildcard="CSV files (*.csv)|*.csv|Tab Separated file (*.tsv)|*.tsv|All files|*",
                                                 style=wx.OPEN|wx.HIDE_READONLY|wx.CHANGE_DIR),
                                   True) as (dlg, retcode):
        if retcode==wx.ID_OK:
            path=dlg.GetPath()
        else:
            return

    with guihelper.WXDialogWrapper(ImportCSVDialog(path, parent, -1, "Import CSV file"),
                                   True) as (dlg, retcode):
        if retcode==wx.ID_OK:
            data=dlg.GetFormattedData()
            if data is not None:
                parent.GetActivePhonebookWidget().importdata(data, merge=dlg.merge)

def OnFileImportVCards(parent):
    with guihelper.WXDialogWrapper(wx.FileDialog(parent, "Import vCards file",
                                                 wildcard="vCard files (*.vcf)|*.vcf|All files|*",
                                                 style=wx.OPEN|wx.HIDE_READONLY|wx.CHANGE_DIR),
                                   True) as (dlg, retcode):
        if retcode==wx.ID_OK:
            path=dlg.GetPath()
        else:
            return

    with guihelper.WXDialogWrapper(ImportVCardDialog(path, parent, -1, "Import vCard file"),
                                   True) as (dlg, retcode):
        if retcode==wx.ID_OK:
            data=dlg.GetFormattedData()
            if data is not None:
                parent.GetActivePhonebookWidget().importdata(data, merge=dlg.merge)

def OnFileImportQtopiaDesktopContacts(parent):
    with guihelper.WXDialogWrapper(ImportQtopiaDesktopDialog(parent, -1, "Import Qtopia Desktop Contacts"),
                                   True) as (dlg, retcode):
        if retcode==wx.ID_OK:
            data=dlg.GetFormattedData()
            if data is not None:
                parent.GetActivePhonebookWidget().importdata(data, merge=dlg.merge)
        
def OnFileImportOutlookContacts(parent):
    import native.outlook
    if not TestOutlookIsInstalled():
        return
    with guihelper.WXDialogWrapper(ImportOutlookDialog(parent, -1, "Import Outlook Contacts", native.outlook),
                                   True) as (dlg, retcode):
        if retcode==wx.ID_OK:
            data=dlg.GetFormattedData()
            if data is not None:
                parent.GetActivePhonebookWidget().importdata(data, merge=dlg.merge)
    native.outlook.releaseoutlook()

def OnFileImportEvolutionContacts(parent):
    import native.evolution
    with guihelper.WXDialogWrapper(ImportEvolutionDialog(parent, -1, "Import Evolution Contacts", native.evolution),
                                   True) as (dlg, retcode):
        if retcode==wx.ID_OK:
            data=dlg.GetFormattedData()
            if data is not None:
                parent.GetActivePhonebookWidget().importdata(data, merge=dlg.merge)

def OnFileImporteGroupwareContacts(parent):
    import native.egroupware
    with guihelper.WXDialogWrapper(ImporteGroupwareDialog(parent, -1, "Import eGroupware Contacts", native.egroupware),
                                   True) as (dlg, retcode):
        if retcode==wx.ID_OK:
            data=dlg.GetFormattedData()
            if data is not None:
                parent.GetActivePhonebookWidget().importdata(data, merge=dlg.merge)

def OnFileImportCommon(parent, dlg_class, dlg_title, widget, dict_key):
    with guihelper.WXDialogWrapper(dlg_class(parent, -1, dlg_title),
                                   True) as (dlg, res):
        if res==wx.ID_OK:
            pubsub.publish(pubsub.MERGE_CATEGORIES,
                           dlg.get_categories()[:])
            # and save the new data
            data_dict={ dict_key: dlg.get() }
            widget.populate(data_dict)
            widget.populatefs(data_dict)
        elif res==dlg_class.ID_ADD:
            # ask phonebook to merge our categories
            pubsub.publish(pubsub.MERGE_CATEGORIES,
                           dlg.get_categories()[:])
            # get existing data
            data_res=widget.getdata({}).get(dict_key, {})
            # and add the new imported data
            data_res.update(dlg.get())
            data_dict={ dict_key: data_res }
            # and save it
            widget.populate(data_dict)
            widget.populatefs(data_dict)
        elif res==dlg_class.ID_MERGE:
            # ask phonebook to merge our categories
            pubsub.publish(pubsub.MERGE_CATEGORIES,
                           dlg.get_categories()[:])
            # and merge the data
            widget.mergedata({ dict_key: dlg.get() })

def OnFileImportOutlookCalendar(parent):
    import native.outlook
    if not TestOutlookIsInstalled():
        return
    import outlook_calendar
    import pubsub
    OnFileImportCommon(parent, outlook_calendar.OutlookImportCalDialog,
                       'Import Outlook Calendar', parent.GetActiveCalendarWidget(),
                       'calendar')
    native.outlook.releaseoutlook()

def OnCalendarWizard(parent):
    import imp_cal_wizard
    OnFileImportCommon(parent, imp_cal_wizard.ImportCalendarWizard,
                       'Import Calendar Wizard',
                       parent.GetActiveCalendarWidget(),
                       'calendar')

def OnCalendarPreset(parent):
    import imp_cal_preset
    OnFileImportCommon(parent, imp_cal_preset.ImportCalendarPresetDialog,
                       'Import Calendar Preset',
                       parent.GetActiveCalendarWidget(), 'calendar')

def OnFileImportOutlookNotes(parent):
    import native.outlook
    if not TestOutlookIsInstalled():
        return
    import outlook_notes
    OnFileImportCommon(parent, outlook_notes.OutlookImportNotesDialog,
                       'Import Outlook Notes', parent.GetActiveMemoWidget(),
                       'memo')
    native.outlook.releaseoutlook()

def OnFileImportOutlookTasks(parent):
    import native.outlook
    if not TestOutlookIsInstalled():
        return
    import outlook_tasks
    OnFileImportCommon(parent, outlook_tasks.OutlookImportTasksDialog,
                       'Import Outlook Tasks', parent.GetActiveTodoWidget(),
                       'todo')
    native.outlook.releaseoutlook()

def OnFileImportVCal(parent):
    OnFileImportCommon(parent, vcal_calendar.VcalImportCalDialog,
                       'Import vCalendar', parent.GetActiveCalendarWidget(),
                       'calendar')

def OnFileImportiCal(parent):
    OnFileImportCommon(parent, ical_calendar.iCalImportCalDialog,
                       'Import iCalendar', parent.GetActiveCalendarWidget(),
                       'calendar')

def OnFileImportgCal(parent):
    OnFileImportCommon(parent, gcal.gCalImportDialog,
                       'Import Google Calendar',
                       parent.GetActiveCalendarWidget(),
                       'calendar')

def OnFileImportCSVCalendar(parent):
    OnFileImportCommon(parent, csv_calendar.CSVImportDialog,
                       'Import CSV Calendar', parent.GetActiveCalendarWidget(),
                       'calendar')

###
###   AUTO_SYNC
###

def AutoConfOutlookCalender(parent, folder, filters):
    import native.outlook
    if not TestOutlookIsInstalled():
        return None, None
    import outlook_calendar
    config=()
    dlg=outlook_calendar.OutlookAutoConfCalDialog(parent, -1,
                                                 'Config Outlook Calendar AutoSync Settings',
                                                 folder, filters)
    return AutoConfCommon(dlg)

def AutoConfCSVCalender(parent, folder, filters):
    import csv_calendar
    config=()
    dlg=csv_calendar.CSVAutoConfCalDialog(parent, -1,
                                                 'Config CSV Calendar AutoSync Settings',
                                                 folder, filters)
    return AutoConfCommon(dlg)

def AutoConfVCal(parent, folder, filters):
    import vcal_calendar
    dlg=vcal_calendar.VCalAutoConfCalDialog(parent, -1,
                                                 'Config VCal AutoSync Settings',
                                                 folder, filters)
    return AutoConfCommon(dlg)

def AutoConfCommon(dlg):
    with guihelper.WXDialogWrapper(dlg, True) as (dlg, res):
        if res==wx.ID_OK:
            config=(dlg.GetFolder(), dlg.GetFilter())
        else:
            config=()
    return res, config

def AutoImportOutlookCalendar(parent, folder, filters):
    import native.outlook
    if not TestOutlookIsInstalled():
        return 0
    import outlook_calendar
    calendar_r=outlook_calendar.ImportCal(folder, filters)
    return AutoImportCalCommon(parent, calendar_r)

def AutoImportVCal(parent, folder, filters):
    import vcal_calendar
    calendar_r=vcal_calendar.ImportCal(folder, filters)
    return AutoImportCalCommon(parent, calendar_r)

def AutoImportCSVCalendar(parent, folder, filters):
    import csv_calendar
    calendar_r=csv_calendar.ImportCal(folder, filters)
    return AutoImportCalCommon(parent, calendar_r)

def AutoImportCalCommon(parent, calendar_r):
    parent.calendarwidget.populate(calendar_r)
    parent.calendarwidget.populatefs(calendar_r)
    res=1
    return res

def OnAutoCalImportSettings(parent):
    pass

def OnAutoCalImportExecute(parent):
    pass

# Play list
def OnWPLImport(parent):
    # get the wpl file name
    with guihelper.WXDialogWrapper(wx.FileDialog(parent, "Import wpl file",
                                                 wildcard="wpl files (*.wpl)|*.wpl|All files|*",
                                                 style=wx.OPEN|wx.HIDE_READONLY|wx.CHANGE_DIR),
                                   True) as (_dlg, _retcode):
        # parse & retrieve the data
        if _retcode==wx.ID_OK:
            _wpl=wpl_file.WPL(filename=_dlg.GetPath())
            if not _wpl.title:
                return
            _pl_entry=playlist.PlaylistEntry()
            _pl_entry.name=_wpl.title
            _pl_entry.songs=[common.basename(x) for x in _wpl.songs]
            # populate the new data
            _widget=parent.GetActivePlaylistWidget()
            _pl_data={}
            _widget.getdata(_pl_data)
            _pl_data[playlist.playlist_key].append(_pl_entry)
            _widget.populate(_pl_data)
            _widget.populatefs(_pl_data)

###
###   EXPORTS
###

def GetPhonebookExports():
    res=[]
    # Vcards - always possible
    res.append( (guihelper.ID_EXPORT_VCARD_CONTACTS, "vCards...", "Export the phonebook to vCards", OnFileExportVCards) )
    # eGroupware - always possible
    res.append( (guihelper.ID_EXPORT_GROUPWARE_CONTACTS, "eGroupware...", "Export the phonebook to eGroupware", OnFileExporteGroupware) )
    # CSV - always possible
    res.append( (guihelper.ID_EXPORT_CSV_CONTACTS, 'CSV Contacts...', 'Export the phonebook to CSV', OnFileExportCSV))
    res.append( (guihelper.ID_EXPORT_CSV_CALENDAR, 'CSV Calendar...', 'Export the calendar to CSV', OnFileExportCSVCalendar) )
    # iCal
    res.append( (guihelper.ID_EXPORT_ICALENDAR,
                 'iCalendar...',
                 'Export the calendar to iCalendar',
                 OnFileExportiCalendar) )
    # SMS - always possible
    res.append( (guihelper.ID_EXPORT_SMS, 'SMS...', 'Export SMS Messages', OnFileExportSMS))
    # Call History - always possible
    res.append( (guihelper.ID_EXPORT_CSV_CALL_HISTORY, 'CSV Call History...', 'Export Call History to CSV',
                 OnFileExportCallHistory))
    # Media - always possible
    res.append( (guihelper.ID_EXPORT_MEDIA_TO_DIR, 'Media to Folder...', 'Export Media Files to a Folder on your computer',
                 OnFileExportMediaDir))
    res.append( (guihelper.ID_EXPORT_MEDIA_TO_ZIP, 'Media to Zip File...', 'Export Media Files to a Zip file',
                 OnFileExportMediaZip))
    return res

class BaseExportDialog(wx.Dialog):

    def __init__(self, parent, title, style=wx.CAPTION|wx.MAXIMIZE_BOX|\
             wx.SYSTEM_MENU|wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, id=-1, title=title, style=style)
        self._phonebook_module=parent.GetActivePhonebookWidget()

    def GetSelectionGui(self, parent):
        "Returns a sizer containing the gui for selecting which items and which fields are exported"
        hbs=wx.BoxSizer(wx.HORIZONTAL)

        lsel=len(self._phonebook_module.GetSelectedRows())
        lall=len(self._phonebook_module._data)
        rbs=wx.StaticBoxSizer(wx.StaticBox(self, -1, "Rows"), wx.VERTICAL)
        self.rows_selected=wx.RadioButton(self, wx.NewId(), "Selected (%d)" % (lsel,), style=wx.RB_GROUP)
        self.rows_all=wx.RadioButton(self, wx.NewId(), "All (%d)" % (lall,))
        rbs.Add(self.rows_selected, 0, wx.EXPAND|wx.ALL, 2)
        rbs.Add(self.rows_all, 0, wx.EXPAND|wx.ALL, 2)
        hbs.Add(rbs, 3, wx.EXPAND|wx.ALL, 5)
        self.rows_selected.SetValue(lsel>1)
        self.rows_all.SetValue(not lsel>1)

        vbs2=wx.StaticBoxSizer(wx.StaticBox(self, -1, "Fields"), wx.VERTICAL)
        cb=[]
        for c in ("Everything", "Phone Numbers", "Addresses", "Email Addresses"):
            cb.append(wx.CheckBox(self, -1, c))
            vbs2.Add(cb[-1], 0, wx.EXPAND|wx.ALL, 5)

        for c in cb:
            c.Enable(False)
        cb[0].SetValue(True)

        hbs.Add(vbs2, 4, wx.EXPAND|wx.ALL, 5)

        return hbs

    def GetPhoneBookItems(self, includecount=False):
        """Returns each item in the phonebook based on the settings
        for all vs selected.  The fields are also trimmed to match
        what the user requested.

        @param includecount:  If this is true then the return is
                 a tuple of (item, number, max) and you can use
                 number and max to update a progress bar.  Note
                 that some items may be skipped (eg if the user
                 only wants records with phone numbers and some
                 records don't have them)
        """
        
        data=self._phonebook_module._data
        if self.rows_all.GetValue():
            rowkeys=data.keys()
        else:
            rowkeys=self._phonebook_module.GetSelectedRowKeys()
        for i,k in enumerate(rowkeys[:]): # we use a dup of rowkeys since it can be altered while exporting
            # ::TODO:: look at fields setting
            if includecount:
                yield data[k],i,len(rowkeys)
            else:
                yield data[k]

class ExportVCardDialog(BaseExportDialog):

    dialects=vcard.profiles.keys()
    dialects.sort()
    default_dialect='vcard2'

    def __init__(self, parent, title):
        BaseExportDialog.__init__(self, parent, title)
        # make the ui
        
        vbs=wx.BoxSizer(wx.VERTICAL)

        bs=wx.BoxSizer(wx.HORIZONTAL)

        bs.Add(wx.StaticText(self, -1, "File"), 0, wx.ALL|wx.ALIGN_CENTRE, 5)
        self.filenamectrl=wx.TextCtrl(self, -1, wx.GetApp().config.Read("vcard/export-file", "bitpim.vcf")) 
        bs.Add(self.filenamectrl, 1, wx.ALL|wx.EXPAND, 5)
        self.browsectrl=wx.Button(self, wx.NewId(), "Browse...")
        bs.Add(self.browsectrl, 0, wx.ALL|wx.EXPAND, 5)
        wx.EVT_BUTTON(self, self.browsectrl.GetId(), self.OnBrowse)

        vbs.Add(bs, 0, wx.EXPAND|wx.ALL, 5)

        hbs2=wx.BoxSizer(wx.HORIZONTAL)

        # dialects
        hbs=wx.StaticBoxSizer(wx.StaticBox(self, -1, "Dialect"), wx.VERTICAL)
        self.dialectctrl=wx.ListBox(self, -1, style=wx.LB_SINGLE, choices=[vcard.profiles[d]['description'] for d in self.dialects])
        default=wx.GetApp().config.Read("vcard/export-format", self.default_dialect)
        if default not in self.dialects: default=self.default_dialect
        self.dialectctrl.SetSelection(self.dialects.index(default))
        hbs.Add(self.dialectctrl, 1, wx.ALL|wx.EXPAND, 5)

        hbs2.Add(hbs, 2, wx.EXPAND|wx.ALL, 10)
        hbs2.Add(self.GetSelectionGui(self), 5, wx.EXPAND|wx.ALL, 5)

        vbs.Add(hbs2, 0, wx.EXPAND|wx.ALL, 5)

        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL,5)
        vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALIGN_CENTER|wx.ALL, 5)
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)

    def OnBrowse(self, _):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, defaultFile=self.filenamectrl.GetValue(),
                                                     wildcard="vCard files (*.vcf)|*.vcf", style=wx.SAVE|wx.CHANGE_DIR),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.filenamectrl.SetValue(os.path.join(dlg.GetDirectory(), dlg.GetFilename()))

    def OnOk(self, _):
        # do export
        filename=self.filenamectrl.GetValue()

        dialect=None
        for k,v in vcard.profiles.items():
            if v['description']==self.dialectctrl.GetStringSelection():
                dialect=k
                break

        assert dialect is not None

        # ::TODO:: ask about overwriting existing file
        with file(filename, "wt") as f:
            for record in self.GetPhoneBookItems():
                print >>f, vcard.output_entry(record, vcard.profiles[dialect]['profile'])
        
        # save settings since we were succesful
        wx.GetApp().config.Write("vcard/export-file", filename)
        wx.GetApp().config.Write("vcard/export-format", dialect)
        wx.GetApp().config.Flush()
        self.EndModal(wx.ID_OK)

class ExportCSVDialog(BaseExportDialog):
    __pb_keys=(
        ('names', ('title', 'first', 'middle', 'last', 'full', 'nickname')),
        ('addresses', ('type', 'company', 'street', 'street2', 'city',
                       'state', 'postalcode', 'country')),
        ('numbers', ('number', 'type', 'speeddial')),
        ('emails', ('email', 'type')),
        ('urls', ('url', 'type')),
        ('categories', ('category',)),
        ('ringtones', ('ringtone', 'use')),
        ('wallpapers', ('wallpaper', 'use')),
        ('memos', ('memo',)),
        ('flags', ('secret',))
        )
        
    def __init__(self, parent, title):
        super(ExportCSVDialog, self).__init__(parent, title)
        # make the ui
        vbs=wx.BoxSizer(wx.VERTICAL)
        bs=wx.BoxSizer(wx.HORIZONTAL)
        bs.Add(wx.StaticText(self, -1, "File"), 0, wx.ALL|wx.ALIGN_CENTRE, 5)
        self.filenamectrl=wx.TextCtrl(self, -1, "bitpim.csv")
        bs.Add(self.filenamectrl, 1, wx.ALL|wx.EXPAND, 5)
        self.browsectrl=wx.Button(self, wx.NewId(), "Browse...")
        bs.Add(self.browsectrl, 0, wx.ALL|wx.EXPAND, 5)
        vbs.Add(bs, 0, wx.EXPAND|wx.ALL, 5)
        # selection GUI
        vbs.Add(self.GetSelectionGui(self), 5, wx.EXPAND|wx.ALL, 5)
        # the buttons
        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL,5)
        vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALIGN_CENTER|wx.ALL, 5)
        # event handlers
        wx.EVT_BUTTON(self, self.browsectrl.GetId(), self.OnBrowse)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
        # all done
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

    def OnBrowse(self, _):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, defaultFile=self.filenamectrl.GetValue(),
                                                     wildcard="CSV files (*.csv)|*.csv", style=wx.SAVE|wx.CHANGE_DIR),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.filenamectrl.SetValue(os.path.join(dlg.GetDirectory(), dlg.GetFilename()))
    def OnOk(self, _):
        # do export
        filename=self.filenamectrl.GetValue()
        # find out the length of each key
        key_count={}
        for e in self.__pb_keys:
            key_count[e[0]]=0
        for record in self.GetPhoneBookItems():
            for k in record:
                if key_count.has_key(k):
                    key_count[k]=max(key_count[k], len(record[k]))
        with file(filename, 'wt') as f:
            l=[]
            for e in self.__pb_keys:
                if key_count[e[0]]:
                    ll=[e[0]+'_'+x for x in e[1]]
                    l+=ll*key_count[e[0]]
            f.write(','.join(l)+'\n')
            for record in self.GetPhoneBookItems():
                ll=[]
                for e in self.__pb_keys:
                    key=e[0]
                    if key_count[key]:
                        for i in range(key_count[key]):
                            try:
                                entry=record[key][i]
                            except (KeyError, IndexError):
                                entry={}
                            for field in e[1]:
                                _v=entry.get(field, '')
                                if isinstance(_v, unicode):
                                    _v=_v.encode('ascii', 'ignore')
                                ll.append('"'+str(_v).replace('"', '')+'"')
                f.write(','.join(ll)+'\n')
                f.flush()
        self.EndModal(wx.ID_OK)
        
class ExporteGroupwareDialog(BaseExportDialog):

    ID_REFRESH=wx.NewId()
    ID_CHANGE=wx.NewId()

    _categorymessage="eGroupware doesn't create categories correctly via XML-RPC, so you should manually create them via the web interface.  " \
           "Click to see which ones should be manually created." 


    def __init__(self, parent, title, module):
        BaseExportDialog.__init__(self, parent, title)

        self.module=module
        self.parent=parent
        
        # make the ui
        
        vbs=wx.BoxSizer(wx.VERTICAL)

        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.StaticText(self, -1, "URL"), 0, wx.ALIGN_CENTRE|wx.ALL,2)
        self.curl=wx.StaticText(self, -1)
        hbs.Add(self.curl, 3, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 2)
        hbs.Add(wx.StaticText(self, -1, "Domain"), 0, wx.ALIGN_CENTRE|wx.ALL,5)
        self.cdomain=wx.StaticText(self, -1)
        hbs.Add(self.cdomain, 1, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 2)
        hbs.Add(wx.StaticText(self, -1, "User"), 0, wx.ALIGN_CENTRE|wx.ALL,5)
        self.cuser=wx.StaticText(self, -1)
        hbs.Add(self.cuser, 1, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
        self.cchange=wx.Button(self, self.ID_CHANGE, "Change ...")
        hbs.Add(self.cchange, 0, wx.ALL, 2)
        vbs.Add(hbs,0,wx.ALL,5)
        wx.EVT_BUTTON(self, self.ID_CHANGE, self.OnChangeCreds)
        self.sp=None
        self.setcreds()

        vbs.Add(self.GetSelectionGui(self), 0, wx.EXPAND|wx.ALL, 5)


        # category checker
        
        bs2=wx.StaticBoxSizer(wx.StaticBox(self, -1, "Category Checker"), wx.HORIZONTAL)
        bs2.Add(wx.Button(self, self.ID_REFRESH, "Check"), 0, wx.ALL, 5)
        self.categoryinfo=wx.TextCtrl(self, -1, self._categorymessage, style=wx.TE_MULTILINE|wx.TE_READONLY)
        bs2.Add(self.categoryinfo, 1, wx.EXPAND|wx.ALL, 2)

        vbs.Add(bs2, 0, wx.EXPAND|wx.ALL, 5)

        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL,5)

        bs2=wx.StaticBoxSizer(wx.StaticBox(self, -1, "Export Progress"), wx.VERTICAL)
        self.progress=wx.Gauge(self, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        self.progress_text=wx.StaticText(self, -1, "")
        bs2.Add(self.progress, 0, wx.EXPAND|wx.ALL, 5)
        bs2.Add(self.progress_text, 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(bs2, 0, wx.EXPAND|wx.ALL, 5)

        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL,5)
        vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
        
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        
        # for some reason wx decides to make the dialog way taller
        # than needed.  i can't figure out why.  sometimes wx just
        # makes you go grrrrrrrr
        vbs.Fit(self)

        wx.EVT_BUTTON(self, self.ID_REFRESH, self.CategoryCheck)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
        
    def OnChangeCreds(self,_):
        dlg=eGroupwareLoginDialog(self, self.module)
        newsp=dlg.GetSession()
        if newsp is not None:
            self.sp=newsp
            self.setcreds()

    def setcreds(self):
        cfg=wx.GetApp().config
        self.curl.SetLabel(cfg.Read("egroupware/url", "http://server.example.com/egroupware"))
        self.cdomain.SetLabel(cfg.Read("egroupware/domain", "default"))
        try:
            import getpass
            defuser=getpass.getuser()
        except:
            defuser="user"
        self.cuser.SetLabel(cfg.Read("egroupware/user", defuser))

    def CategoryCheck(self, evt=None):
        if evt is not None:
            evt.Skip()
        if self.sp is None:
            self.sp=eGroupwareLoginDialog(self, self.module).GetSession(auto=True)
            self.setcreds()
        self.FindWindowById(wx.ID_OK).Enable(self.sp is not None)
        self.FindWindowById(self.ID_REFRESH).Enable(self.sp is not None)

        # find which categories are missing
        cats=[]
        for e in self.GetPhoneBookItems():
            for c in e.get("categories", []):
                cc=c["category"]
                if cc not in cats:
                    cats.append(cc)

        cats.sort()
        egcats=[v['name'] for v in self.sp.getcategories()]
        nocats=[c for c in cats if c not in egcats]

        if len(nocats):
            self.categoryinfo.SetValue("eGroupware doesn't have the following categories, which you should manually add:\n\n"+", ".join(nocats))
        else:
            self.categoryinfo.SetValue("eGroupware has all the categories you use")

    def OnOk(self, _):
        if self.sp is None:
            self.sp=eGroupwareLoginDialog(self, self.module).GetSession(auto=True)
            self.setcreds()
        if self.sp is None:
            return


        doesntexistaction=None
        catsmodified=True # load categories 
        # write out each one
        setmax=-1
        for record,pos,max in self.GetPhoneBookItems(includecount=True):
            if catsmodified:
                # get the list of categories
                cats=dict( [(v['name'], v['id']) for v in self.sp.getcategories()] )
            if max!=setmax:
                setmax=max
                self.progress.SetRange(max)
            self.progress.SetValue(pos)
            self.progress_text.SetLabel(nameparser.formatsimplename(record.get("names", [{}])[0]))
            wx.SafeYield()
            catsmodified,rec=self.FormatRecord(record, cats)
            if rec['id']!=0:
                # we have an id, but the record could have been deleted on the eg server, so
                # we check
                if not self.sp.doescontactexist(rec['id']):
                    if doesntexistaction is None:
                        with guihelper.WXDialogWrapper(eGroupwareEntryGoneDlg(self, rec['fn']),
                                                       True) as (dlg, _):
                            action=dlg.GetAction()
                            if dlg.ForAll():
                                doesntexistaction=action
                    else: action=doesntexistaction
                    if action==self._ACTION_RECREATE:
                        rec['id']=0
                    elif action==self._ACTION_IGNORE:
                        continue
                    elif action==self._ACTION_DELETE:
                        found=False
                        for serial in record["serials"]:
                            if serial["sourcetype"]=="bitpim":
                                self.parent.GetActivePhonebookWidget().DeleteBySerial(serial)
                                found=True
                                break
                        assert found
                        continue 

            newid=self.sp.writecontact(rec)
            found=False
            for serial in record["serials"]:
                if serial["sourcetype"]=="bitpim":
                    self.parent.GetActivePhonebookWidget().UpdateSerial(serial, {"sourcetype": "egroupware", "id": newid})
                    found=True
                    break
            assert found
            
            
        self.EndModal(wx.ID_OK)



    def FormatRecord(self, record, categories):
        """Convert record into egroupware fields

        We return a tuple of  (egw formatted record, if we update categories)

        If the second part is True, the categories should be re-read from the server after writing the record."""

        catsmodified=False

        # note that mappings must be carefully chosen to ensure that importing from egroupware
        # and then re-exporting doesn't change anything.
        
        res={'id': 0} # zero means create new record
        # find existing egroupware id
        for i in record.get("serials", []):
            if i['sourcetype']=='egroupware':
                res['id']=i['id']
                break
        # name (nb we don't do prefix or suffix since bitpim doesn't know about them)
        res['n_given'],res['n_middle'],res['n_family']=nameparser.getparts(record.get("names", [{}])[0])
        for nf in 'n_given', 'n_middle', 'n_family':
            if res[nf] is None:
                res[nf]="" # set None fields to blank string
        res['fn']=nameparser.formatsimplename(record.get("names", [{}])[0])
        # addresses
        for t,prefix in ("business", "adr_one"), ("home", "adr_two"):
            a={}
            adr=record.get("addresses", [])
            for i in adr:
                if i['type']==t:
                    for p2,k in ("_street", "street"), ("_locality", "city"), ("_region", "state"), \
                        ("_postalcode", "postalcode"), ("_countryname", "country"):
                        res[prefix+p2]=i.get(k, "")
                    if t=="business":
                        res['org_name']=i.get("company","")
                    break
        # email
        if "emails" in record:
            # this means we ignore emails without a type, but that can't be avoided with
            # how egroupware works
            for t,k in ("business", "email"), ("home", "email_home"):
                for i in record["emails"]:
                    if i.get("type",None)==t:
                        res[k]=i.get("email")
                        res[k+"_type"]="INTERNET"
                        break

        # categories
        cats={}
        for cat in record.get("categories", []):
            c=cat['category']
            v=categories.get(c, None)
            if v is None:
                catsmodified=True
                for i in xrange(0,-999999,-1):
                    if `i` not in cats:
                        break
            else:
                i=`v`
            cats[i]=str(c)
            
        res['cat_id']=cats

        # phone numbers
        # t,k is bitpim type, egroupware type
        for t,k in ("home", "tel_home"), ("cell", "tel_cell"), ('fax','tel_fax'), \
                ('pager', 'tel_pager'), ('office', 'tel_work'):
            if "numbers" in record:
                v=""
                for i in record['numbers']:
                    if i['type']==t:
                        v=i['number']
                        break
                res[k]=phonenumber.format(v)

        # miscellaneous others
        if "memos" in record:
            memos=record.get("memos", [])
            memos+=[{}]
            res['note']=memos[0].get("memo","")
        if "urls" in record:
            urls=record.get("urls", [])
            u=""
            for url in urls:
                if url.get("type", None)=="business":
                    u=url["url"]
                    break
            if len(u)==0:
                urls+=[{'url':""}]
                u=urls[0]["url"]
            res['url']=u

        # that should be everything
        return catsmodified,res

    _ACTION_RECREATE=1
    _ACTION_IGNORE=2
    _ACTION_DELETE=3
    
class eGroupwareEntryGoneDlg(wx.Dialog):

    choices=( ("Re-create entry on server", ExporteGroupwareDialog._ACTION_RECREATE),
              ("Delete the entry in BitPim", ExporteGroupwareDialog._ACTION_DELETE),
              ("Ignore this entry for now", ExporteGroupwareDialog._ACTION_IGNORE)
              )

    def __init__(self, parent, details):
        wx.Dialog.__init__(self, parent, -1, title="Entry deleted on server")
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(wx.StaticText(self, -1, "The entry for \"%s\" has\nbeen deleted on the server." % (details,) ), 0, wx.EXPAND|wx.ALL, 5)
        self.rb=wx.RadioBox(self, -1, "Action to take", choices=[t for t,a in self.choices])
        vbs.Add(self.rb, 0, wx.EXPAND|wx.ALL, 5)
        self.always=wx.CheckBox(self, -1, "Always take this action")
        vbs.Add(self.always, 0, wx.ALL|wx.ALIGN_CENTRE, 5)

        vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL,5)
        vbs.Add(self.CreateButtonSizer(wx.OK|wx.HELP), 0, wx.ALIGN_CENTER|wx.ALL, 5)
        self.SetSizer(vbs)
        vbs.Fit(self)

    def GetAction(self):
        return self.choices[self.rb.GetSelection()][1]

    def ForAll(self):
            return self.always.GetValue()

def OnFileExportVCards(parent):
    with guihelper.WXDialogWrapper(ExportVCardDialog(parent, "Export phonebook to vCards"),
                                   True):
        pass

def OnFileExporteGroupware(parent):
    import native.egroupware
    with guihelper.WXDialogWrapper(ExporteGroupwareDialog(parent, "Export phonebook to eGroupware", native.egroupware),
                                   True):
        pass

def OnFileExportCSV(parent):
    with guihelper.WXDialogWrapper(ExportCSVDialog(parent, "Export phonebook to CSV"),
                                   True):
        pass

def OnFileExportCSVCalendar(parent):
    import csv_calendar
    with guihelper.WXDialogWrapper(csv_calendar.ExportCSVDialog(parent, 'Export Calendar to CSV'),
                                   True):
        pass

def OnFileExportiCalendar(parent):
    with guihelper.WXDialogWrapper(ical_calendar.ExportDialog(parent, 'Export Calendar to iCalendar'),
                                   True):
        pass

def OnFileExportSMS(parent):
    import sms_imexport
    with guihelper.WXDialogWrapper(sms_imexport.ExportSMSDialog(parent, 'Export SMS'),
                                   True):
        pass

def OnFileExportCallHistory(parent):
    import call_history_export
    with guihelper.WXDialogWrapper(call_history_export.ExportCallHistoryDialog(parent, 'Export Call History'),
                                   True):
        pass

def OnFileExportMediaZip(parent):
    import media_root
    with guihelper.WXDialogWrapper(media_root.ExportMediaToZipDialog(parent, 'Export Media to Zip')) as dlg:
        dlg.DoDialog()

def OnFileExportMediaDir(parent):
    import media_root
    with guihelper.WXDialogWrapper(media_root.ExportMediaToDirDialog(parent, 'Media will be copied to selected folder')) as dlg:
        dlg.DoDialog()
