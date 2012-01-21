### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2004 Peter Pletcher <peterpl@pacbell.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: evolution.py 1442 2004-07-14 05:14:24Z rogerb $

"Be at one with Evolution"

# Evolution mostly sucks when compared to Outlook.  The UI and functionality
# for the address book is a literal copy.  There is no API as such and we
# just have to delve around the filesystem

# root directory is ~/evolution
# folders are any directory containing a file named folder-metadata.xml
# note that folders can be nested
#
# the folder name is the directory name.  The folder-metadata.xml file
# does contain description tag, but it isn't normally displayed and
# is usually empty for user created folders
#
# if the folder contains any addressbook entries, then there will
# be an addressbook.db file
#
# the file should be opened using bsddb
# import bsddb
# db=bsddb.hashopen("addressbook.db", "r")
# db.keys() lists keys, db[key] gets item
#
# the item contains exactly one field which is a null terminated string
# containing a vcard


import sys
import os
import re

if sys.platform!="linux2":
    raise ImportError()

try:
    import bsddb
except:
    raise ImportError()


userdir=os.path.expanduser("~")
evolutionpath="evolution/local"
evolutionbasedir=os.path.join(userdir, evolutionpath)
evolutionexporter = {
    'command'    : "evolution-addressbook-export",
    'folderid'   : "<Evolution Addressbook Exporter>",
    'name'       : "<Evolution Addressbook Exporter>",
    'type'       : ["address book"]
}

def getcontacts(folder):
    """Returns the contacts as a list of string vcards

    Note that the Windows EOL convention is used"""

    if folder == evolutionexporter['folderid']:
        return getcontacts_evoexporter()
    
    dir=os.path.expanduser(folder)
    p=os.path.join(dir, "addressbook.db")
    if not os.path.isfile(p):
        # ok, this is not an address book folder
        if not os.path.isfile(os.path.join(dir, "folder-metadata.xml")):
            raise ValueError("Supplied folder is not a folder! "+folder)
        raise ValueError("Folder does not contain contacts! "+folder)
    res=[]
    db=bsddb.hashopen(p, 'r')
    for key in db.keys():
        if key.startswith("PAS-DB-VERSION"): # no need for this field
            continue
        data=db[key]
        while data[-1]=="\x00": # often has actual null on the end
            data=data[:-1]  
        res.append(data)
    db.close()
    return res

class EvolutionExportException(Exception):
    pass

def getcontacts_evoexporter():
    """Get the cards by running evolution-addressbook-export

    Note that this code returns all the contacts as a single
    string item.  It seemed silly to split them apart when
    the caller then just puts them back together as one
    string"""
    evo_export = os.popen(evolutionexporter['command'])
    evo_cards = evo_export.read()
    evo_export_status = evo_export.close()
    if evo_export_status is not None:
        raise EvolutionExportException("%s failed with code %s" % (evolutionexporter['command'], `evo_export_status`))
    return [evo_cards]

def getfsfolders(basedir=evolutionbasedir):

    res={}
    children=[]

    for f in os.listdir(basedir):
        p=os.path.join(basedir, f)

        # deal with child folders (depth first)
        if os.path.isdir(p):
            f=getfsfolders(p)
            if len(f):
                children.extend(f)
            continue

    # if we have any children, sort them
    if len(children):
        lc=[ (child['name'], child) for child in children] # decorate
        lc.sort() # sort
        children=[child for _, child in lc] # un-decorate


    # do we have a meta-data file?
    if not os.path.isfile(os.path.join(basedir, "folder-metadata.xml")):
        return children

    # ok, what type is this folder
    t=[]
    for file,type in ( ("mbox", "mailbox"), ("calendar.ics", "calendar"), ("addressbook.db", "address book"),
                               ("tasks.ics", "tasks") ):
        if os.path.isfile(os.path.join(basedir, file)):
            t.append(type)

    entry={}
    entry['dirpath']=basedir
    entry['name']=os.path.basename(basedir)
    entry['folderid']=basedir.replace(userdir, "~", 1)
    entry['type']=t
    if len(children):
        entry['children']=children
        # tell children who their daddy is
        for c in children:
            c['parent']=entry
        
    return [entry]

def getspecialfolders():
    "Return a list of any special folders"

    # the only one we look for currently is evolution-addressbook-export
    # command
    evo_version = os.popen(evolutionexporter['command'] + " --version")
    evo_version_result = evo_version.read()
    evo_version_status = evo_version.close()
    if evo_version_status is not None:
        return []
    # it doesn't work with earlier versions of evolution, so we do a version
    # check
    if evo_version_result.startswith("Gnome evolution 1.4"):
        return [evolutionexporter]
    else:
        return []

def getfolders():
    return getspecialfolders()+getfsfolders()

def pickfolder(selectedid=None, parent=None, title="Select Evolution Folder"):
    # we do the imports etc in the function so that this file won't
    # require gui code unless this function is called

    import wx
    import wx.gizmos

    dlg=wx.Dialog(parent, -1, title, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size=(450,350))
    vbs=wx.BoxSizer(wx.VERTICAL)
    
    tl=wx.gizmos.TreeListCtrl(dlg, -1, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT)

    tl.AddColumn("Name")
    tl.SetMainColumn(0)
    tl.AddColumn("Type")
    tl.SetColumnWidth(0, 300)



    def addnode(parent, item, selected):
        node=tl.AppendItem(parent, item['name'])
        if selected==item['folderid']:
            tl.SelectItem(node)
        tl.SetItemText(node, ", ".join(item['type']), 1)
        tl.SetPyData(node, item)
        if item.has_key("children"):
            for child in item['children']:
                addnode(node, child, selected)
            tl.Expand(node)

    root=tl.AddRoot("?")
    tl.SetPyData(root, None)

    for f in getfolders():
        addnode(root, f, selectedid)

    # select first folder if nothing is selected
    if tl.GetPyData(tl.GetSelection()) is None:
        child,_=tl.GetFirstChild(root, 1234)
        tl.SelectItem(child)

    vbs.Add(tl, 1, wx.EXPAND|wx.ALL, 5)

    vbs.Add(wx.StaticLine(dlg, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL, 5)

    vbs.Add(dlg.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALIGN_CENTRE|wx.ALL, 5)

    dlg.SetSizer(vbs)
    dlg.SetAutoLayout(True)

    if dlg.ShowModal()==wx.ID_OK:
        folderid=tl.GetPyData(tl.GetSelection())['folderid']
    else:
        folderid=None
    dlg.Destroy()
    return folderid

# we use a pathname like "~/evolution/local/Contacts" as the folder id
# and the same as a "folder"

class Match:
    def __init__(self, folder):
        self.folder=folder

def getfolderfromid(id, default=False):
    "Return a folder object given the id"

    f=_findfolder(id)
    if f is not None:
        return f['folderid']
    
    if default:
        # look for a default
        for f in getfolders():
            if "address book" in f['type']:
                return f["folderid"]
        # brute force
        return getfolders()[0]['folderid']

    return None

def __findfolder(node, id):
    "Recursive function to locate a folder, using Match exception to return the found folder"
    if node['folderid']==id:
        raise Match(node)
    for c in node.get("children", []):
        __findfolder(c, id)

def _findfolder(id):
    for f in getfolders():
        try:
            __findfolder(f, id)
        except Match,m:
            return m.folder # we found it
    return None
        
        
def getfoldername(id):
    f=_findfolder(id)
    if f is None:
        raise AttributeError("No such folder "+id)

    n=[]
    while f:
        n=[f['name']]+n
        f=f.get('parent',None)

    return " / ".join(n)

def getfolderid(folder):
    return folder
    

if __name__=="__main__":
    # a folder selector
    import wx
    import wx.gizmos

    app=wx.PySimpleApp()
    
    folder=pickfolder()
    print folder

    print "\n".join(getcontacts(folder))
                     
            
