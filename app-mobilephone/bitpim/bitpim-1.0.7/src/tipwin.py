#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2006 Joe Pham<djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: tipwin.py 3676 2006-11-14 03:25:45Z djpham $

"""
A TipWindow class that can properly handle tab(\t) characters.
Limitation: This class does not do text wrapping!
"""

import wx

space_count=4   # expand a tab by the # of spaces
TEXT_MARGIN_X=3
TEXT_MARGIN_Y=3
parentclass=wx.TipWindow
class TipWindow(parentclass):
    def __init__(self, parent, text, maxwidth=100, rectbound=None):
        global TEXT_MARGIN_X
        super(TipWindow, self).__init__(parent, text, maxwidth, rectbound)
        _children_wins=self.GetChildren()
        if len(_children_wins)!=1:
            # can't find the view window, bail
            return
        self._view=_children_wins[0]
        self._text=text
        self._max_w=maxwidth
        self._line_h=0
        self._col_x=[TEXT_MARGIN_X]
        self.adjust()
        wx.EVT_PAINT(self._view, self.OnPaintView)

    def adjust(self):
        # adjust the width of this window if there tabs
        global space_count
        if self._text.find('\t')==-1:
            # no tab, bail
            return
        _dc=wx.ClientDC(self._view)
        _dc.SetFont(self._view.GetFont())
        for _line in self._text.split('\n'):
            _cnt=0
            for _col in _line.split('\t'):
                _cnt+=1
                if _cnt>=len(self._col_x):
                    self._col_x.append(0)
                _w, _h=_dc.GetTextExtent(_col)
                self._col_x[_cnt]=max(_w, self._col_x[_cnt])
                self._line_h=max(self._line_h, _h)
        _space_w=_dc.GetTextExtent(' '*space_count)[0]
        for _cnt in range(1, len(self._col_x)):
            self._col_x[_cnt]+=self._col_x[_cnt-1]+_space_w
        _w, _h=self.GetClientSizeTuple()
        _w=min(self._col_x[-1]-_space_w+self._col_x[0], self._max_w)
        self.SetClientSizeWH(_w, _h)
        self._view.SetDimensions(0, 0, _w, _h)

    def OnPaintView(self, _):
        global TEXT_MARGIN_Y
        _dc=wx.PaintDC(self._view)
        # First, fill the background
        _background=self._view.GetBackgroundColour()
        _foreground=self._view.GetForegroundColour()
        _dc.SetBrush(wx.Brush(_background, wx.SOLID))
        _dc.SetPen(wx.Pen(_foreground, 1, wx.SOLID))
        _dc.DrawRectangle(0, 0, *self._view.GetClientSizeTuple())
        # and then draw the text line by line
        _dc.SetTextBackground(_background)
        _dc.SetTextForeground(_foreground)
        _dc.SetFont(self._view.GetFont())
        _y=TEXT_MARGIN_Y
        for _line in self._text.split('\n'):
            for _idx, _col in enumerate(_line.split('\t')):
                _dc.DrawText(_col, self._col_x[_idx], _y)
            _y+=self._line_h
