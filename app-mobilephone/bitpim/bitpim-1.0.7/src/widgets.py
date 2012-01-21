#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2006-2006 Simon Capper <skyjnky@sbcglobal.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: widgets.py 3890 2007-01-11 03:28:43Z djpham $

### base class for all widgets

import wx
import re

import helpids
import bphtml

class BitPimWidget:
    MENU_NORMAL=wx.ITEM_NORMAL
    MENU_SPACER=wx.ITEM_SEPARATOR
    MENU_CHECK=wx.ITEM_CHECK

    def __init__(self):
        pass

    def InitialiseWidget(self, tree, id, root, config, help_id=None):
        self.id=id
        self._tree=tree
        self.root=root
        self.config=config
        self.OnInit()
        if help_id==None:
            try:
                id_name=re.sub("[^A-Za-z]", "",self.GetWidgetName().upper())
                self.help_id=getattr(helpids, "ID_TAB_"+id_name)
            except:
                self.help_id=helpids.ID_WELCOME
        else:
            self.help_id=help_id

    def OnInit(self):
        pass

    def AddSubPage(self, page, name, image=None, after=None):
        return self._tree.AddPage(self.id, page, name, image, after)

    def AddNode(self, name, image=None):
        return self._tree.AddNode(self, name, image)

    def OnSelected(self, node):
        """Default does nothing, override to provide specific functionality.
        node equals value returned from AddNode.
        """
        pass

    def OnPopupMenu(self, parent, node, pt):
        menu=self.GetRightClickMenuItems(node)
        if len(menu):
            popup_menu=wx.Menu()
            for menu_item in menu:
                type, id, name, tooltip=menu_item
                if type==self.MENU_SPACER:
                    # using append with a type of separator does not work for some reason?
                    popup_menu.AppendSeparator()
                else:
                    popup_menu.Append(id, name, tooltip, type)
            parent.PopupMenu(popup_menu, pt)
            self.OnRightClickMenuExit()

    def GetWidgetName(self):
        return self._tree.GetItemText(self.id)

    def GetHelpID(self):
        return self.help_id

    def ActivateSelf(self, id=None):
        if id==None:
            id=self.id
        self._tree.SelectItem(id)

    # override these functions to access menu/toolbar items
    # each command has a "Can" function, this controls greying
    # out options that are not supported by the widget

    def GetRightClickMenuItems(self, node):
        """Default does nothing, override to provide specific functionality.
        node equals value returned from AddNode. 
        Return array of (type, ID, name, tootltip) tuples to be used in the popup menu
        Valid types are "menu",
        """
        result=[]
        return result

    def OnRightClickMenuExit(self):
        pass

    def OnKeyDown(self, evt):
        pass

    def OnKeyUp(self, evt):
        pass

    def CanCopy(self):
        return False

    def OnCopy(self, evt):
        pass

    def CanPaste(self):
        return False

    def OnPaste(self, evt):
        pass

    def CanRename(self):
        return False

    def OnRename(self, evt):
        pass

    def CanDelete(self):
        return False

    def GetDeleteInfo(self):
        return wx.ART_DEL_BOOKMARK, "Delete"

    def OnDelete(self, evt):
        pass

    def CanAdd(self):
        return False

    def GetAddInfo(self):
        return wx.ART_ADD_BOOKMARK, "Add"

    def OnAdd(self, evt):
        pass

    def CanPrint(self):
        return False

    def OnPrintDialog(self, mainwindow, config):
        pass

    def CanSelectAll(self):
        return False

    def OnSelectAll(self, evt):
        pass

    def HasHistoricalData(self):
        return False

    def OnHistoricalData(self):
        pass

    def HasPreviewPane(self):
        return False

    def IsPreviewPaneEnabled(self):
        return False
    
    def OnViewPreview(self, on):
        pass

    def HasColumnSelector(self):
        return False

    def OnViewColumnSelector(self):
        pass

    def OnPreActivate(self):
        pass
    def OnPostActivate(self):
        pass

class RootWidget(bphtml.HTMLWindow, BitPimWidget):
    # This page is copied out of the welcome.htm page of the BitPim help
    # Obviously, it needs to be in sync with the BitPim help.
    welcome_text="""
<html>
<head><title>Welcome</title>
</head>
<body>
<h1>Welcome</h1>

<p>Welcome to BitPim.  

<p>If you are new to BitPim, please take the <a href="tour-master.htm">tour</a>.
<p>BitPim's homepage is <a href="http://www.bitpim.org" target="bitpimhelpexternallink">www.bitpim.org</a>.
    The project page is <a href="http://www.sourceforge.net/projects/bitpim" target="bitpimhelpexternallink">www.sourceforge.net/projects/bitpim</a>.

<p>You may be interested in <a href="upgrading.htm">upgrade information</a> or the 
<a href="versionhistory.htm">version history</a>.

<p>If you have any problems or questions please read the <a href="support.htm">information about support</a>.

<p>Praise and <a href="contributing.htm">contributions</a> are always welcome!

<hr> 
</body></html>
"""

    def __init__(self, parent, id):
        wx.html.HtmlWindow.__init__(self, parent, id)
        self.SetPage(self.welcome_text)
    def OnLinkClicked(self, link):
        _ref=link.GetHref()
        if _ref.startswith('http'):
            # web link
            super(RootWidget, self).OnLinkClicked(link)
        else:
            # Help topic
            wx.GetApp().displayhelpid(str(_ref))
