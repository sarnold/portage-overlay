### BITPIM
###
### Copyright (C) 2005 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: rangedslider.py 2249 2005-03-22 07:13:19Z rogerb $

"A ranged slider that has a current position and a start/end"


import wx
import wx.lib.newevent

import guihelper

PosChangedEvent, EVT_POS_CHANGED = wx.lib.newevent.NewCommandEvent()
ChangingEvent, EVT_CHANGING = wx.lib.newevent.NewCommandEvent()

class RangedSlider(wx.PyWindow):

    THICKNESS=7

    def __init__(self, parent, id=-1, size=wx.DefaultSize, pos=wx.DefaultPosition, style=0):
        wx.PyWindow.__init__(self, parent, id=id, size=size, pos=pos, style=style|wx.FULL_REPAINT_ON_RESIZE)

        self.bg=wx.Brush(parent.GetBackgroundColour())

        self.imgcurrent=guihelper.getimage("ranged-slider-current")
        self.bmpcurrent=self.imgcurrent.ConvertToBitmap()
        self.imgstart=guihelper.getimage("ranged-slider-start")
        self.bmpstart=self.imgstart.ConvertToBitmap()
        self.imgend=guihelper.getimage("ranged-slider-end")
        self.bmpend=self.imgend.ConvertToBitmap()

        # first coord is added to desired x to get where to draw x
        # second is added to centre of line to get where to draw y
        self.hotcurrent=-self.imgcurrent.GetWidth()/2, -self.imgcurrent.GetHeight()+2
        self.hotstart=-13, -20
        self.hotend=-7,-20

        self.pickers=(self.imgcurrent, self.bmpcurrent,self.hotcurrent), \
                      (self.imgstart, self.bmpstart, self.hotstart), \
                      (self.imgend, self.bmpend, self.hotend)

        self.padleft=2+max([0]+[-h[0] for _,_,h in self.pickers])
        self.padright=2+max([0]+[i.GetWidth()+h[0] for i,_,h in self.pickers])

        assert self.padleft>=2
        assert self.padright>=2
        self.padleft=max(self.padleft,self.padright)
        self.padright=self.padleft

        self.poscurrent=0.5
        self.posstart=0.0
        self.posend=1.0

        self._bufbmp=None

        self.pen=wx.Pen(wx.NamedColour("LIGHTSTEELBLUE3"), self.THICKNESS)
        self.pen.SetCap(wx.CAP_BUTT)

        self.clickinfo=None

        wx.EVT_ERASE_BACKGROUND(self, lambda evt: None)
        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_LEFT_DOWN(self, self.OnLeftDown)
        wx.EVT_LEFT_UP(self, self.OnLeftUp)
        wx.EVT_MOTION(self, self.OnMotion)

    def DoGetBestSize(self):
        sz=self.GetClientSize()
        halfheight=self.THICKNESS
        for i,_,h  in self.pickers:
            halfheight=max(halfheight, abs(h[1]), abs(h[1]+i.GetHeight()))

        return min(100,sz.width),halfheight*2
            
            

    def OnPaint(self, _):
        sz=self.GetClientSize()
        if self._bufbmp is None or sz.width>self._bufbmp.GetWidth() or sz.height>self._bufbmp.GetHeight():
            self._bufbmp=wx.EmptyBitmap((sz.width+64)&~8, (sz.height+64)&~8)
        dc=wx.BufferedPaintDC(self, self._bufbmp, style=wx.BUFFER_VIRTUAL_AREA)
        dc.SetBackground(self.bg)
        dc.Clear()
        dc.SetPen(self.pen)
        y=sz.height/2
        dc.DrawLine(self.padleft,y, sz.width-self.padright, y)
        dc.SetPen(wx.NullPen)
        start=self.padleft
        width=sz.width-self.padleft-self.padright

        dc.DrawBitmap(self.bmpcurrent, start+int(width*self.poscurrent)+self.hotcurrent[0], y+self.hotcurrent[1], True)
        dc.DrawBitmap(self.bmpstart, start+int(width*self.posstart)+self.hotstart[0], y+self.hotstart[1], True)
        dc.DrawBitmap(self.bmpend, start+int(width*self.posend)+self.hotend[0], y+self.hotend[1], True)

    def _isinimage(self, image, relx, rely):
        "Works out if click is in image, and not transparent area of image"
        if image.HasAlpha():
            return image.GetAlpha(relx, rely)>0
        if image.HasMask():
            return not (image.GetRed(relx, rely)==image.GetMaskRed() and
                        image.GetGreen(relx, rely)==image.GetMaskGreen() and
                        image.GetBlue(relx, rely)==image.GetMaskBlue())
        # we have no way of telling, so say yes
        return True

    def OnLeftDown(self, evt):
        x,y=evt.GetX(), evt.GetY()
        sz=self.GetClientSize()
        liney=sz.height/2
        start=self.padleft
        width=sz.width-self.padleft-self.padright
        # now try to work out what was clicked on
        xx,yy=start+int(width*self.poscurrent)+self.hotcurrent[0], liney+self.hotcurrent[1]
        if xx<=x<xx+self.imgcurrent.GetWidth() and yy<=y<yy+self.imgcurrent.GetHeight():
            relx,rely=x-xx,y-yy
            if self._isinimage(self.imgcurrent, relx, rely):
                print "oncurrent"
                self.clickinfo=0,x,self.poscurrent
                return
        xx,yy=start+int(width*self.posstart)+self.hotstart[0], liney+self.hotstart[1]
        if xx<=x<xx+self.imgstart.GetWidth() and yy<=y<yy+self.imgstart.GetHeight():
            relx,rely=x-xx,y-yy
            if self._isinimage(self.imgstart, relx, rely):
                print "onstart"
                self.clickinfo=1,x,self.posstart
                return
        xx,yy=start+int(width*self.posend)+self.hotend[0], liney+self.hotend[1]
        if xx<=x<xx+self.imgend.GetWidth() and yy<=y<yy+self.imgend.GetHeight():
            relx,rely=x-xx,y-yy
            if self._isinimage(self.imgend, relx, rely):
                print "onend"
                self.clickinfo=2,x,self.posend
                return
        if start<=x<start+width and liney-self.THICKNESS/2<=y<=liney+self.THICKNESS/2:
            self.poscurrent=(x-start)/float(width)
            self.Refresh(False)
            self.clickinfo=0,x,y
            return
        self.clickinfo=None

    def OnMotion(self, evt):
        if self.clickinfo is None or not evt.Dragging():
            return
        x,y=evt.GetX(), evt.GetY()
        sz=self.GetClientSize()
        liney=sz.height/2
        start=self.padleft
        width=sz.width-self.padleft-self.padright

        origpos=self.clickinfo[2]
        origx=self.clickinfo[1]
        delta=origx-x
        newpos=origpos-delta/float(width)
        if newpos<0: newpos=0.0
        elif newpos>1: newpos=1.0
        if self.clickinfo[0]==0:  self.poscurrent=newpos
        elif self.clickinfo[0]==1: self.posstart=min(newpos,self.posend)
        elif self.clickinfo[0]==2: self.posend=max(newpos, self.posstart)
        if newpos!=origpos:
            wx.PostEvent(self, ChangingEvent(self.GetId()))
            self.Refresh(False)

    def OnLeftUp(self, evt):
        if self.clickinfo is not None and self.clickinfo[0]==0:
            wx.PostEvent(self, PosChangedEvent(self.GetId(), poscurrent=self.poscurrent))

    # main API
    def GetCurrent(self):
        return self.poscurrent
    def SetCurrent(self, pos):
        assert 0<=pos<=1
        self.poscurrent=pos
        self.Refresh(False)
    def GetStart(self):
        return self.posstart
    def SetStart(self, pos):
        assert 0<=pos<=1
        self.posstart=pos
        self.Refresh(False)
    def GetEnd(self):
        return self.posend
    def SetEnd(self, pos):
        assert 0<=pos<=1
        self.posend=pos
        self.Refresh(False)


if __name__=='__main__':
    app=wx.PySimpleApp()

    import sys
    import common
    sys.excepthook=common.formatexceptioneh

    f=wx.Frame(None, title="Ranged Slider Tester")
    rs=RangedSlider(f)
    f.Show()

    app.MainLoop()
