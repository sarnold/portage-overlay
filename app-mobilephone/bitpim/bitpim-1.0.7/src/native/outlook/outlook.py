### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: outlook.py 3022 2006-03-31 03:21:24Z djpham $

"Be at one with Outlook"

# Reject if not on Windows
import sys
if sys.platform!="win32":
   raise ImportError()

import common

# See this recipe on ASPN for how this code started
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/173216
# Chris Somerlot also gave some insights

import outlook_com

import pywintypes

# This is the complete list of field names available
##    Account
##    AssistantName
##    AssistantTelephoneNumber
##    BillingInformation
##    Body
##    Business2TelephoneNumber
##    BusinessAddress
##    BusinessAddressCity
##    BusinessAddressCountry
##    BusinessAddressPostOfficeBox
##    BusinessAddressPostalCode
##    BusinessAddressState
##    BusinessAddressStreet
##    BusinessFaxNumber
##    BusinessHomePage
##    BusinessTelephoneNumber
##    CallbackTelephoneNumber
##    CarTelephoneNumber
##    Categories
##    Children
##    Class
##    Companies
##    CompanyAndFullName
##    CompanyLastFirstNoSpace
##    CompanyLastFirstSpaceOnly
##    CompanyMainTelephoneNumber
##    CompanyName
##    ComputerNetworkName
##    ConversationIndex
##    ConversationTopic
##    CustomerID
##    Department
##    Email1Address
##    Email1AddressType
##    Email1DisplayName
##    Email1EntryID
##    Email2Address
##    Email2AddressType
##    Email2DisplayName
##    Email2EntryID
##    Email3Address
##    Email3AddressType
##    Email3DisplayName
##    Email3EntryID
##    EntryID
##    FTPSite
##    FileAs
##    FirstName
##    FullName
##    FullNameAndCompany
##    Gender
##    GovernmentIDNumber
##    Hobby
##    Home2TelephoneNumber
##    HomeAddress
##    HomeAddressCity
##    HomeAddressCountry
##    HomeAddressPostOfficeBox
##    HomeAddressPostalCode
##    HomeAddressState
##    HomeAddressStreet
##    HomeFaxNumber
##    HomeTelephoneNumber
##    ISDNNumber
##    Importance
##    Initials
##    InternetFreeBusyAddress
##    JobTitle
##    Journal
##    Language
##    LastFirstAndSuffix
##    LastFirstNoSpace
##    LastFirstNoSpaceCompany
##    LastFirstSpaceOnly
##    LastFirstSpaceOnlyCompany
##    LastName
##    LastNameAndFirstName
##    MailingAddress
##    MailingAddressCity
##    MailingAddressCountry
##    MailingAddressPostOfficeBox
##    MailingAddressPostalCode
##    MailingAddressState
##    MailingAddressStreet
##    ManagerName
##    MessageClass
##    MiddleName
##    Mileage
##    MobileTelephoneNumber
##    NetMeetingAlias
##    NetMeetingServer
##    NickName
##    NoAging
##    OfficeLocation
##    OrganizationalIDNumber
##    OtherAddress
##    OtherAddressCity
##    OtherAddressCountry
##    OtherAddressPostOfficeBox
##    OtherAddressPostalCode
##    OtherAddressState
##    OtherAddressStreet
##    OtherFaxNumber
##    OtherTelephoneNumber
##    OutlookInternalVersion
##    OutlookVersion
##    PagerNumber
##    PersonalHomePage
##    PrimaryTelephoneNumber
##    Profession
##    RadioTelephoneNumber
##    ReferredBy
##    Saved
##    SelectedMailingAddress
##    Sensitivity
##    Size
##    Spouse
##    Subject
##    Suffix
##    TTYTDDTelephoneNumber
##    TelexNumber
##    Title
##    UnRead
##    User1
##    User2
##    User3
##    User4
##    UserCertificate
##    WebPage
##    YomiCompanyName
##    YomiFirstName
##YomiLastName

def getcontacts(folder, keys=None):
    """Returns a list of dicts"""

    # There is a gross hack to only return email addresses if they are for SMTP

    res=[]
    for oc in range(folder.Items.Count):
        contact=folder.Items.Item(oc+1)
        if contact.Class == outlook_com.constants.olContact:
            record={}
            if keys is None:
                keys=[]
                for key in contact._prop_map_get_:
                    # work out if it is a property or a method (last field is None for properties)
                    if contact._prop_map_get_[key][-1] is None:
                        keys.append(key)
            for key in keys:
                v=getattr(contact, key)
                if v not in (None, "", "\x00\x00"):
                    if isinstance(v, pywintypes.TimeType): # convert from com time
                        try:
                            v=int(v)
                        except ValueError:
                            # illegal time value
                            continue
                    if key=="Categories":
                       # for some idiotic reason Outlook uses comma
                       # space seperators for this field despite using
                       # semi-colon elsewhere for the same field so we
                       # munge the data
                       v=";".join([x.strip() for x in v.split(",")])
                    if key.startswith("Email") and key.endswith("Address"):
                       keytype=key+"Type"
                       if keytype not in keys:
                          if getattr(contact, keytype)!="SMTP":
                             continue
                          
                    record[key]=v
            res.append(record)
    return res

def getitemdata(item, record, keys, client):
    for k, k_out, convertor_func in keys:
        v=getattr(item, k)
        if v is None or v=="\x00\x00":
            v=''
        if convertor_func is not None:
            # run through convertor func
            try:
                v=convertor_func(record, v, client)
            except:
                # failed conversion, skip this field
                raise
        # assign in dict if specified
        if k_out is not None:
            record[k_out]=v
    return record

def getdata(folder, keys=None, preset_dict={}, client=None, post_func=None):
    """Returns a list of dicts"""
    res=[]
    import_errors=[]
    if not folder.Items.Count:
        # empty folder, just return
        return res, import_errors
    # prefill keys if necessary
    if keys is None:
        keys=[]
        item=folder.Items.Item(1)
        for k in item._prop_map_get_:
            if item._prop_map_get_[k][-1] is None:
                keys.append((k, k, None))
    # go through the folder and read the data
    for i in range(folder.Items.Count):
        item=folder.Items.Item(i+1)
        record=preset_dict.copy()
        try:
            getitemdata(item, record, keys, client)
            if post_func is None or post_func(item, record, client):
                res.append(record)
        except:
            import_errors.append(record)
    return res, import_errors

def getfolderfromid(id, default=False, default_type='contacts'):
    """Returns a folder object from the supplied id

    @param id: The id of the folder
    @param default: If true and the folder can't be found, then return the default"""
    onMAPI = getmapinamespace()
    try:
        folder=onMAPI.GetFolderFromID(id)
    except pywintypes.com_error,e:
        folder=None
        
    # ::TODO:: should be supplied default type (contacts, calendar etc)
    if default and not folder:
        if default_type=='calendar':
            default_folder=outlook_com.constants.olFolderCalendar
        elif default_type=='notes':
            default_folder=outlook_com.constants.olFolderNotes
        elif default_type=='tasks':
            default_folder=outlook_com.constants.olFolderTasks
        else:
            # default to contacts, works as before
            default_folder=outlook_com.constants.olFolderContacts
        folder=onMAPI.GetDefaultFolder(default_folder)
    return folder

def getfoldername(folder):
    n=[]
    while folder:
        try:
            n=[folder.Name]+n
        except AttributeError:
            break # namespace object has no 'Name'
        folder=folder.Parent
    return " / ".join(n)

def getfolderid(folder):
    return str(folder.EntryID) # de-unicodify it

def pickfolder():
    return getmapinamespace().PickFolder()

_outlookappobject=None
def getoutlookapp():
    global _outlookappobject
    if _outlookappobject is None:
        _outlookappobject=outlook_com.Application()
    return _outlookappobject

_mapinamespaceobject=None
def getmapinamespace():
    global _mapinamespaceobject
    if _mapinamespaceobject is None:
        _mapinamespaceobject=getoutlookapp().GetNamespace("MAPI")
    return _mapinamespaceobject

def releaseoutlook():
    global _mapinamespaceobject
    global _outlookappobject
    _mapinamespaceobject=None
    _outlookappobject=None


if __name__=='__main__':
    oOutlookApp=outlook_com.Application()
    onMAPI = oOutlookApp.GetNamespace("MAPI")

    import guihelper # needed for common.strorunicode symbol

    res=onMAPI.PickFolder()
    print res

    contacts=getcontacts(res)
    keys={}
    for item in contacts:
        for k in item.keys():
            keys[k]=1
    keys=keys.keys()
    keys.sort()

    # Print out keys so they can be pasted in elsewhere
    for k in keys:
        print "   ('%s',  )," % (k,)

    import wx
    import wx.grid

    app=wx.PySimpleApp()
    import wx.lib.colourdb
    wx.lib.colourdb.updateColourDB()

    
    f=wx.Frame(None, -1, "Outlookinfo")
    g=wx.grid.Grid(f, -1)
    g.CreateGrid(len(contacts)+1,len(keys))
    g.SetColLabelSize(0)
    g.SetRowLabelSize(0)
    g.SetMargins(1,0)
    g.BeginBatch()
    attr=wx.grid.GridCellAttr()
    attr.SetBackgroundColour(wx.GREEN)
    attr.SetFont(wx.Font(10,wx.SWISS, wx.NORMAL, wx.BOLD))
    attr.SetReadOnly(True)
    for k in range(len(keys)):
        g.SetCellValue(0, k, keys[k])
    g.SetRowAttr(0,attr)
    # row attributes
    oddattr=wx.grid.GridCellAttr()
    oddattr.SetBackgroundColour("OLDLACE")
    oddattr.SetReadOnly(True)
    evenattr=wx.grid.GridCellAttr()
    evenattr.SetBackgroundColour("ALICE BLUE")
    evenattr.SetReadOnly(True)
    for row in range(len(contacts)):
        item=contacts[row]
        for col in range(len(keys)):
            key=keys[col]
            v=item.get(key, "")
            v=common.strorunicode(v)
            g.SetCellValue(row+1, col, v)
        g.SetRowAttr(row+1, (evenattr,oddattr)[row%2])

    g.AutoSizeColumns()
    g.AutoSizeRows()
    g.EndBatch()

    f.Show(True)
    app.MainLoop()
