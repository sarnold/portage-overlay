#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: analyser.py 3037 2006-04-03 00:30:28Z rogerb $

"""Graphical view of protocol data and a decode of it"""

import sys
import re
import traceback
import wx
import StringIO
import struct

import common
import prototypes

import hexeditor

class Eventlist(wx.ListCtrl):
    "List control showing the various events"

    def __init__(self, parent, id=-1, events=[]):
        self.events=events
        wx.ListCtrl.__init__(self, parent, id, style=wx.LC_REPORT|wx.LC_VIRTUAL)
        self.InsertColumn(0, "Time")
        self.InsertColumn(1, "Size")
        self.InsertColumn(2, "Class")
        self.InsertColumn(3, "Description")

        self.SetColumnWidth(0, 100)
        self.SetColumnWidth(1, 50)
        self.SetColumnWidth(2, 200)
        self.SetColumnWidth(3, 1000)

        self.SetItemCount(len(events))

    def newdata(self, events):
        self.DeleteAllItems()
        self.events=events
        self.SetItemCount(len(events))

    def OnGetItemText(self, index, col):
        curtime, curdesc, curclass, curdata=self.events[index]
        if col==0:
            return curtime
        if col==1:
            if len(curdata):
                return "%5d" % (len(curdata),)
            return ""
        if col==2:
            return curclass
        if col==3:
            return curdesc
        assert False

    def OnGetItemImage(self, item):
        return -1
        
    

class Analyser(wx.Frame):
    """A top level frame for analysing protocol data"""
    _pane_widths=[-2, -3, -4]
    _pos_pane_index=0
    _sel_pane_index=1
    _val_pane_index=2

    def __init__(self, parent=None, id=-1, title="BitPim Protocol Analyser", data=None):
        """Start the show

        @param data: data to show.  If None, then it will be obtained from the clipboard
        """
        wx.Frame.__init__(self, parent, id, title, size=(800,750),
                         style=wx.DEFAULT_FRAME_STYLE)
        # add a status bar to display various status items
        self.CreateStatusBar(len(self._pane_widths))
        self.SetStatusWidths(self._pane_widths)

        topsplit=wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_LIVE_UPDATE)

        self.list=Eventlist(topsplit, 12)

        botsplit=wx.SplitterWindow(topsplit, -1, style=wx.SP_3D|wx.SP_LIVE_UPDATE)
        topsplit.SplitHorizontally(self.list, botsplit, 300)

        self.tree=wx.TreeCtrl(botsplit, 23, style=wx.TR_DEFAULT_STYLE)
        self.hex=hexeditor.HexEditor(botsplit,
                                     _set_pos=self.set_pos,
                                     _set_sel=self.set_sel,
                                     _set_val=self.set_val)
        botsplit.SplitHorizontally(self.tree, self.hex, 200)
        
        if data is None:
            data=self.getclipboarddata()

        self.newdata(data)

        wx.EVT_LIST_ITEM_SELECTED(self, self.list.GetId(), self.OnListBoxItem)
        wx.EVT_LIST_ITEM_ACTIVATED(self, self.list.GetId(), self.OnListBoxItem)

        wx.EVT_TREE_SEL_CHANGED(self, self.tree.GetId(), self.OnTreeSelection)
        
        self.Show()

    def newdata(self, data):
        "We have new data - the old data is tossed"
        self.parsedata(data)
        self.list.newdata(self.packets)

    def OnListBoxItem(self,evt):
        "The user selected an event in the listbox"
        index=evt.m_itemIndex
        curtime, curdesc, curclass, curdata=self.packets[index]
        self.errorinfo=""
        self.hex.SetData("")
        self.hex.highlightrange(-1,-1)
        if len(curdata):
            self.hex.SetData(curdata)
            # self.hex.ShowPosition(self.hex.XYToPosition(0,0))
        else:
            self.hex.SetData(curdesc)
            # self.hex.ShowPosition(self.hex.XYToPosition(0,0))

        self.tree.DeleteAllItems()
        if len(curclass):
            b=prototypes.buffer(curdata)
            try:
                klass=common.getfullname(curclass)
            except Exception,e:
                self.errorme("Finding class",e)
                wx.TipWindow(self.tree,self.errorinfo)
                return
            try:
                obj=klass()
            except Exception,e:
                self.errorme("Instantiating object",e)
                wx.TipWindow(self.tree,self.errorinfo)
                return

            try:
                obj.readfrombuffer(b, autolog=False)
            except Exception,e:
                self.errorme("Reading from buffer",e)
                # no return, we persevere

            root=self.tree.AddRoot(curclass)
            try:
                self.tree.SetPyData(root, obj.packetspan())
            except:
                self.errorme("Object did not construct correctly")
                # no return, we persevere
            self.addtreeitems(obj, root)
        if len(self.errorinfo):
            wx.TipWindow(self.tree,self.errorinfo)

    def addtreeitems(self, obj, parent):
        "Add fields from obj to parent node"
        try:
            for name,field,desc in obj.containerelements():
                if desc is None:
                    desc=""
                else:
                    desc="      - "+desc
                iscontainer=False
                try:
                    iscontainer=field.iscontainer()
                except:
                    pass
                # Add ourselves
                s=field.__class__.__name__+" "+name
                if iscontainer:
                    c=field.__class__
                    s+=": <%s.%s>" % (c.__module__, c.__name__)
                else:
                    try:
                        v=field.getvalue()
                    except Exception,e:
                        v="<Exception: "+e.__str__()+">"
                    s+=": "
                    if isinstance(v, int) and not isinstance(v, type(True)):
                        s+="%d 0x%x" % (v,v)
                    else:
                        s+=`v`
                    if len(desc):
                        s+=desc
                node=self.tree.AppendItem(parent, s)
                try:
                    self.tree.SetPyData(node, field.packetspan())
                except:
                    pass
                if iscontainer:
                    self.addtreeitems(field, node)
        except Exception,e:
            str="<Exception: "+e.__str__()+">"
            self.tree.AppendItem(parent,str)

    def OnTreeSelection(self, evt):
        "User selected an item in the tree"
        item=evt.GetItem()
        try:
            start,end=self.tree.GetPyData(item)
        except:
            self.hex.highlightrange(-1,-1)
            return
        self.hex.highlightrange(start,end)
        # self.hex.ShowPosition(begin)

    def errorme(self, desc, exception=None):
        "Put exception information into the hex pane and output traceback to console"
        if exception is not None:
            x=StringIO.StringIO()
            print >>x,exception.__str__(),
            self.errorinfo+=x.getvalue()+" : "
            print >>sys.stderr, common.formatexception()
        self.errorinfo+=desc+"\n"

    def getclipboarddata(self):
        """Gets text data on clipboard"""
        do=wx.TextDataObject()
        wx.TheClipboard.Open()
        success=wx.TheClipboard.GetData(do)
        wx.TheClipboard.Close()
        if not success:
            wx.MessageBox("Whatever is in the clipboard isn't text", "No way Dude")
            return ""
        return do.GetText()

    patevent=re.compile(r"^(\d?\d:\d\d:\d\d\.\d\d\d)(.*)")
    patdataevent=re.compile(r"^(\d?\d:\d\d:\d\d\.\d\d\d)(.*)(Data - \d+ bytes.*)")
    patdatarow=re.compile(r"^([0-9A-Fa-f]{8})(.*)")
    patclass=re.compile(r"^<#!\s+(.*)\s+!#>")

    def parsedata(self, data):
        """Fills in our internal data structures based on contents of data"""

        # santise all the data by doing the eol nonsense
        data=data.replace("\r", "\n")
        lastlen=0
        while lastlen!=len(data):
            lastlen=len(data)
            data=data.replace("\n\n", "\n")
        
        self.packets=[]

        curtime=curdesc=curclass=curdata=""

        indata=False
        
        for line in data.split('\n'):
            # ignore blank lines
            if len(line.strip())==0:
                continue
            mo=self.patclass.match(line)
            if mo is not None:
                # found a class description
                curclass=mo.group(1)
                indata=True
                continue
            # if indata, try for some more
            if indata:
                mo=self.patdatarow.match(line)
                if mo is not None:
                    # found another data row
                    pos=int(mo.group(1), 16)
                    assert pos==len(curdata)
                    for i in range(9, min(len(line), 9+16*3), 3): # at most 16 bytes
                        s=line[i:i+2]
                        if len(s)!=2 or s=="  ":
                            # last line with trailing spaces
                            continue
                        b=int(s,16)
                        curdata+=chr(b)
                    continue
                # end of data, save it
                indata=False
                self.packets.append( (curtime, curdesc, curclass, curdata) )
                curtime=curdesc=curclass=curdata=""
                # and move on
            # data event?
            mo=self.patdataevent.match(line)
            if mo is not None:
                self.packets.append( (curtime, curdesc, curclass, curdata) )
                curtime=curdesc=curclass=curdata=""
                curtime=mo.group(1)
                curdesc=mo.group(2)+mo.group(3)
                indata=True
                continue
            # ordinary event?
            mo=self.patevent.match(line)
            if mo is not None:
                self.packets.append( (curtime, curdesc, curclass, curdata) )
                curtime=curdesc=curclass=curdata=""
                curtime=mo.group(1)
                curdesc=mo.group(2)
                indata=True
                continue
            # No idea what it is, just add on end of desc
            if len(curdesc):
                curdesc+="\n"
            curdesc+=line

        # Add whatever is in variables at end
        self.packets.append( (curtime, curdesc, curclass, curdata) )

        # remove all blank lines
        # filter, reduce, map and lambda all in one go!
        self.packets=filter(lambda item: reduce(lambda x,y: x+y, map(len, item)), self.packets)
                    
    def set_pos(self, pos):
        """Display the current buffer offset in the format of
        Pos: 0x12=18
        """
        if pos is None:
            s=''
        else:
            s='Pos: 0x%X=%d'%(pos, pos)
        self.SetStatusText(s, self._pos_pane_index)
    def set_sel(self, sel_start, sel_end):
        if sel_start is None or sel_start==-1 or\
           sel_end is None or sel_end==-1:
            s=''
        else:
            sel_len=sel_end-sel_start
            sel_end-=1
            s='Sel: 0x%X=%d to 0x%X=%d (0x%X=%d bytes)'%(
                sel_start, sel_start, sel_end, sel_end,
                sel_len, sel_len)
        self.SetStatusText(s, self._sel_pane_index)
    def set_val(self, v):
        if v:
            # char
            s='Val: 0x%02X=%d'%(ord(v[0]), ord(v[0]))
            if len(v)>1:
                # short
                u_s=struct.unpack('<H', v[:struct.calcsize('<H')])[0]
                s+=' 0x%04X=%d'%(u_s,  u_s)
            if len(v)>3:
                # int/long
                u_i=struct.unpack('<I', v[:struct.calcsize('<I')])[0]
                s+=' 0x%08X=%d'%(u_i, u_i)
        else:
            s=''
        self.SetStatusText(s, self._val_pane_index)

if __name__=='__main__':
    app=wx.PySimpleApp()
    # Find the data source
    data=None
    if len(sys.argv)==2:
        # From a file
        data=common.opentextfile(sys.argv[1]).read()
    frame=Analyser(data=data)
    app.MainLoop()
