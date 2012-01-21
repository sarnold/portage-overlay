### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: aggregatedisplay.py 3298 2006-05-28 03:10:52Z skyjunky $

"Displays a number of sections each with a number of items"

import wx
import sys
import guihelper

ActivateEvent, EVT_ACTIVATE = wx.lib.newevent.NewCommandEvent()

class BufferedPaintDC(wx.BufferedPaintDC):
    def __init__(self, *arg, **karg):
        super(BufferedPaintDC, self).__init__(*arg, **karg)
        self.view_start=(0,0)
        self.pos=(0,0)

class Display(wx.ScrolledWindow):
    "This is the view"

    class HitTestResult:
        "Where a particular point corresponds to"
        IN_BACKGROUND=0
        IN_SECTION=1
        IN_ITEM=2

        def __init__(self, **kwds):
            self.__dict__.update({
                'location': self.IN_BACKGROUND,
                'sectionnum': None,
                'section': None,
                'sectionx': None,
                'sectiony': None,
                'itemnum': None,
                'item': None,
                'itemx': None,
                'itemy': None,
                })
            self.__dict__.update(kwds)

        def __str__(self):
            res="<HitTestResult "
            if self.location==self.IN_BACKGROUND:
                res+="IN_BACKGROUND>"
            elif self.location==self.IN_SECTION:
                res+="IN_SECTION, sectionnum=%d, section=%s, sectionx=%d, sectiony=%d>" % \
                      (self.sectionnum, self.section, self.sectionx, self.sectiony)
            elif self.location==self.IN_ITEM:
                res+="IN_ITEM, sectionnum=%d, section=%s, itemnum=%d, item=%s, itemx=%d, itemy=%d>" % \
                      (self.sectionnum, self.section, self.itemnum, self.item, self.itemx, self.itemy)
            else:
                assert False, "bad location"
                res+="ERROR>"
            return res


    # See the long note in OnPaint before touching this code

    VSCROLLPIXELS=3 # how many pixels we scroll by

    ITEMPADDING=5   # how many pixels we pad items by
    
    def __init__(self, parent, datasource, watermark=None):
        wx.ScrolledWindow.__init__(self, parent, id=wx.NewId(), style=wx.FULL_REPAINT_ON_RESIZE|wx.SUNKEN_BORDER)
        self.exceptioncount=0
        self.EnableScrolling(False, False)
        self.datasource=datasource
        self._bufbmp=None
        self.active_section=None
        self._w, self._h=-1,-1
        self.vheight, self.maxheight=self._h,self._h
        self.sections=[]
        self.sectionheights=[]
        self._scrollbarwidth=wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_ERASE_BACKGROUND(self, self.OnEraseBackground)
        wx.EVT_LEFT_DOWN(self, self.OnLeftDown)
        wx.EVT_LEFT_DCLICK(self, self.OnLeftDClick)
        wx.EVT_RIGHT_DOWN(self, self.OnRightDown)
        if watermark is not None:
            wx.EVT_SCROLLWIN(self, self.OnScroll)

        bgcolour=wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        if guihelper.IsMac():
            bgcolour=wx.WHITE
        self.bgbrush=wx.TheBrushList.FindOrCreateBrush(bgcolour, wx.SOLID)
        if watermark:
            self.watermark=guihelper.getbitmap(watermark)
        else:
            self.watermark=None
        self.UpdateItems()

    def OnScroll(self, evt):
        self.Refresh(False)
        evt.Skip()

    def OnSize(self, evt):
        self.Refresh(False)

    def OnEraseBackground(self, _):
        pass

    def SetActiveSection(self, section):
        if self.active_section!=section:
            self.active_section=section
            self.ReLayout()
            self.Refresh(False)

    def OnPaint(self, event):
        # Getting this drawing right involved hours of fighting wxPython/wxWidgets.
        # Those hours of sweating and cursing reveal the following:
        #
        # - The bufferedpaintdc only allocates a bitmap large enough to cover the
        #   viewable window size.  That is used irrespective of the scroll position
        #   which means you get garbage for any part of your window beyond the
        #   initial physical viewable size
        #
        # - The bufferedpaintdc must have its origin reset back to zero by the time
        #   its destructor is called otherwise it won't draw in the right place
        #
        # - The various other calls are very carefully placed (eg size handler, ReLayout
        #   being a callafter etc).  Otherwise really silly things happen due to the
        #   order that things get displayed in, scrollbars adjustments causing your
        #   window to get cropped behind the scenes and various other annoyances, setting
        #   scrollbars changing size etc
        #
        # - The ReLayout happens very frequently.  It may be possible to optimise out
        #   some calls to it.  Tread very carefully and test on multiple platforms.
        #
        # - wx sometimes misbehaves if the window height isn't set to an exact multiple of the
        #   VSCROLLPIXELS

        sz=self.GetClientSize()
        _relayout=False
        if sz != (self._w,self._h):
            self._w,self._h=sz
            _relayout=True
            self.ReLayout()
            # relayout may change size (scrollbar appearing/going away) so repeat in that case
            if self.GetClientSize()!=sz:
                return self.OnPaint(event)

        if self._bufbmp is None or self._bufbmp.GetWidth()<self._w or self._bufbmp.GetHeight()<self.maxheight:
            self._bufbmp=wx.EmptyBitmap((self._w+64)&~8, (self.maxheight+64)&~8)
        dc=BufferedPaintDC(self, self._bufbmp, style=wx.BUFFER_VIRTUAL_AREA)
        try:
            self.DoPaint(dc, _relayout)
        except:
            # only raise one exception - swallow any more
            self.exceptioncount+=1
            if self.exceptioncount<=1:
                print "raise"
                raise

    def DoPaint(self, dc, relayout=False):
        # we redraw everything that is in the visible area of the screen
        vs=self.GetViewStart()
        dc.view_start=(vs[0], vs[1]*self.VSCROLLPIXELS)
        origin=dc.view_start[1]
        firstvisible=origin
        lastvisible=origin+self._h

        # clear background
        dc.SetBackground(self.bgbrush)
        # only clear area you can see
        dc.SetClippingRegion(0, firstvisible, self._w+1, lastvisible-firstvisible+1)
        dc.Clear()
        # draw watermark
        if self.watermark:
            # place in the middle:
            # dc.DrawBitmap(self.watermark, self._w/2-self.watermark.GetWidth()/2, origin+self._h/2-self.watermark.GetHeight()/2, True)
            # place in bottom right:
            dc.DrawBitmap(self.watermark, self._w-self.watermark.GetWidth(), origin+self._h-self.watermark.GetHeight(), True)

        # draw active section
        cury=0
        for i, section in enumerate(self.sections):
            if self.active_section!=None and section.label!=self.active_section:
                continue
            if relayout or _isvisible(cury, cury+self.sectionheights[i], firstvisible, lastvisible):
                dc.SetDeviceOrigin(0, cury )
                section.Draw(dc, self._w)
            cury+=self.sectionheights[i]
            extrawidth=(self._w-6)-(self.itemsize[i][0]+self.ITEMPADDING)*self.itemsperrow[i]
            extrawidth/=self.itemsperrow[i]
            if extrawidth<0: extrawidth=0
            # now draw items in this section
            num=0
            while num<len(self.items[i]):
                x=(num%self.itemsperrow[i])
                y=(num/self.itemsperrow[i])
                posy=cury+y*(self.itemsize[i][1]+self.ITEMPADDING)
                # skip the entire row if it isn't visible
                if not relayout and \
                   x==0 and \
                   not _isvisible(posy, posy+self.itemsize[i][1], firstvisible, lastvisible):
                    num+=self.itemsperrow[i]
                    continue
                item=self.items[i][num]
                dc.pos=(3+x*(self.itemsize[i][0]+self.ITEMPADDING+extrawidth), posy)
                dc.SetDeviceOrigin(*dc.pos)
                dc.ResetBoundingBox()
                bb=item.Draw(dc, self.itemsize[i][0]+extrawidth, self.itemsize[i][1], self.selected[i][num])
                if bb is None:
                    bb=dc.MinX(), dc.MinY(), dc.MaxX(), dc.MaxY()
                assert len(bb)==4
                try:
                    assert bb[0]>=0 and bb[0]<self.itemsize[i][0]+extrawidth
                    assert bb[1]>=0 and bb[1]<self.itemsize[i][1]
                    assert bb[2]>=bb[0] and bb[2]<=self.itemsize[i][0]+extrawidth
                    assert bb[3]>=bb[1] and bb[3]<=self.itemsize[i][1]
                except:
                    print "bb is",bb
                    print "should be within",(self.itemsize[i][0]+extrawidth,self.itemsize[i][1])
        
                self.boundingboxes[i][num]=bb
                num+=1
            cury+=(len(self.items[i])+self.itemsperrow[i]-1)/self.itemsperrow[i]*(self.itemsize[i][1]+self.ITEMPADDING)
                    
        # must do this or the world ends ...
        dc.SetDeviceOrigin(0,0)

    def OnLeftDown(self, evt):
        self.SetFocus()
        actualx,actualy=self.CalcUnscrolledPosition(evt.GetX(), evt.GetY())
        res=self.HitTest(actualx, actualy)
        if res.item is None:
            if len(self.GetSelection()):
                self.ClearSelection()
            return
        # if neither control or shift is down then clear selection and add this item
        if not evt.ControlDown() and not evt.ShiftDown():
            self.SetSelectedByNumber(res.sectionnum, res.itemnum, False)
            return
        # if control and shift are down then treat as just shift
        if evt.ShiftDown():
            self.SetSelectedByNumber(res.sectionnum, res.itemnum, True)
            return
        assert evt.ControlDown()
        # we toggle the item
        self.selected[res.sectionnum][res.itemnum]=not self.selected[res.sectionnum][res.itemnum]
        self.Refresh(False)

    def OnLeftDClick(self, evt):
        actualx,actualy=self.CalcUnscrolledPosition(evt.GetX(), evt.GetY())
        res=self.HitTest(actualx, actualy)
        if res.item is None:
            if len(self.GetSelection()):
                self.ClearSelection()
            return
        self.SetSelectedByNumber(res.sectionnum, res.itemnum,  False) # make this the only selected item
        wx.PostEvent(self, ActivateEvent(self.GetId(), item=res.item))

    def OnRightDown(self, evt):
        self.SetFocus()
        actualx,actualy=self.CalcUnscrolledPosition(evt.GetX(), evt.GetY())
        res=self.HitTest(actualx, actualy)
        if res.item is None:
            self.ClearSelection()
        else:
            # if item is not in selection then change selection to item
            if not self.IsSelectedByNum(res.sectionnum, res.itemnum):
                self.SetSelectedByNumber(res.sectionnum, res.itemnum)

    def GetAllItems(self):
        """Returns all items

        The return value is a list.  Each item in the list is a tuple of
        (sectionnumber, sectionobject, itemnumber, itemobject)"""
        res=[]
        for s,section in enumerate(self.sections):
            if self.active_section!=None and section.label!=self.active_section:
                continue
            for i,item in enumerate(self.items[s]):
                res.append( (s,section,i,item) )
        return res

    def IsSelectedByNum(self, sectionnum, itemnum):
        "Returns if the itemnum from sectionnum is selected"
        return self.selected[sectionnum][itemnum]

    def IsSelectedByObject(self, itemobj):
        "Returns if the itemobject is selected"
        for s,section in enumerate(self.sections):
            if self.active_section!=None and section.label!=self.active_section:
                continue
            for i,item in enumerate(self.items[s]):
                if item is itemobj:
                    return self.IsSelectedByNum(s,i)
        raise ValueError("no such item "+itemobj)

    def GetSelection(self):
        """Returns the selected items

        The return value is a list.  Each item in the list is a tuple of
        (sectionnumber, sectionobject, itemnumber, itemobject)"""
        res=[]
        for s,section in enumerate(self.sections):
            if self.active_section!=None and section.label!=self.active_section:
                continue
            for i,item in enumerate(self.items[s]):
                if self.selected[s][i]:
                    res.append( (s,section,i,item) )
        return res

    def ClearSelection(self):
        self.selected=[ [False]*len(items) for items in self.items]
        self.Refresh(False)

    def SelectAll(self):
        self.selected=[ [True]*len(items) for items in self.items]
        self.Refresh(False)

    def SetSelectedByNumber(self, sectionnum, itemnum, add=False):
        if not add:
            self.ClearSelection()
        self.selected[sectionnum][itemnum]=True
        self.Refresh(False)

    def SetSelectedByObject(self, itemobj, add=False):
        if not add:
            self.ClearSelection()
        for s,section in enumerate(self.sections):
            if self.active_section!=None and section.label!=self.active_section:
                continue
            for i,item in enumerate(self.items[s]):
                if item is itemobj:
                    self.selected[s][i]=True
                    self.Refresh(False)
                    return
        raise ValueError("no such item "+itemobj)
        
                    
    def HitTest(self, pointx, pointy):
        # work out which item this corresponds to
        origin=self.GetViewStart()[1]*self.VSCROLLPIXELS # used later
        cury=0
        for i, section in enumerate(self.sections):
            if self.active_section!=None and section.label!=self.active_section:
                continue
            if cury<=pointy<=cury+self.sectionheights[i]:
                # in the section
                return self.HitTestResult(location=self.HitTestResult.IN_SECTION,
                                          sectionnum=i, section=section,
                                          sectionx=pointx, sectiony=pointy-cury)
            if cury>pointy:
                return self.HitTestResult()
            cury+=self.sectionheights[i]
            extrawidth=(self._w-6)-(self.itemsize[i][0]+self.ITEMPADDING)*self.itemsperrow[i]
            extrawidth/=self.itemsperrow[i]
            if extrawidth<0: extrawidth=0
            # now find items in this section
            num=0
            while num<len(self.items[i]):
                x=(num%self.itemsperrow[i])
                y=(num/self.itemsperrow[i])
                posy=cury+y*(self.itemsize[i][1]+self.ITEMPADDING)
                # skip the entire row if it isn't in range
                if x==0 and not posy<=pointy<=posy+self.itemsize[i][1]:
                    num+=self.itemsperrow[i]
                    continue
                item=self.items[i][num]
                bbox=self.boundingboxes[i][num]
                if bbox is None:
                    bbox=(0, 0, self.itemsize[i][0]+extrawidth, self.itemsize[i][1])
                startx=3+x*(self.itemsize[i][0]+self.ITEMPADDING+extrawidth)
                startx+=bbox[0]
                endx=startx+bbox[2]-bbox[0]
                starty=posy+bbox[1]
                endy=starty+bbox[3]-bbox[1]
                if startx<=pointx<=endx and starty<=pointy<=endy:
                    ht=self.HitTestResult(location=self.HitTestResult.IN_ITEM,
                                          sectionnum=i, section=section,
                                          itemnum=num, item=item,
                                          itemx=pointx-startx+bbox[0],
                                          itemy=pointy-starty+bbox[1],
                                          itemrect=(startx, starty, endx-startx, endy-starty),
                                          itemrectscrolled=(startx, starty-origin, endx-startx, endy-starty),
                                          )
                    return ht
                num+=1
            cury+=(len(self.items[i])+self.itemsperrow[i]-1)/self.itemsperrow[i]*(self.itemsize[i][1]+self.ITEMPADDING)
        return self.HitTestResult()


    def ReLayout(self):
        self.itemsperrow=[]
        self.vheight=0
        for i,section in enumerate(self.sections):
            self.itemsperrow.append(max((self._w-6)/(self.itemsize[i][0]+self.ITEMPADDING),1))
            if self.active_section!=None and section.label!=self.active_section:
                continue
            self.vheight+=self.sectionheights[-1]
            rows=(len(self.items[i])+self.itemsperrow[i]-1)/self.itemsperrow[i]
            self.vheight+=rows*(self.itemsize[i][1]+self.ITEMPADDING)

        # set the height we want wx to think the window is
        self.maxheight=max(self.vheight,self._h)
        # adjust scrollbar
        self.SetScrollbars(0,1,0,self.vheight,0, self.GetViewStart()[1])
        self.SetScrollRate(0, self.VSCROLLPIXELS)

    def UpdateItems(self):
        "Called if you want the items to be refetched from the model"
        self.sections=self.datasource.GetSections()
        self.items=[]
        self.itemsize=[]
        self.sectionheights=[]
        self.selected=[]
        self.boundingboxes=[]
        for i,section in enumerate(self.sections):
            self.sectionheights.append(section.GetHeight())
            self.itemsize.append(self.datasource.GetItemSize(i,section))
            items=self.datasource.GetItemsFromSection(i,section)            
            self.items.append(items)
            self.boundingboxes.append( [None]*len(items) )
            self.selected.append( [False]*len(items) )
        self._w+=1 # cause a relayout to happen
        self.Refresh(False)


            
def _isvisible(start, end, firstvisible, lastvisible):
    return start <= firstvisible <= end <= lastvisible or \
           (start >= firstvisible and start <= lastvisible) or \
           (start <= firstvisible and end >=lastvisible)


class SectionHeader(object):
    "A generic section header implementation"

    def __init__(self, label):
        self.label=label
        self.InitAttributes()

    def InitAttributes(self):
        "Initialise our font and colours"
        self.font=wx.TheFontList.FindOrCreateFont(20, family=wx.SWISS, style=wx.NORMAL, weight=wx.NORMAL)
        self.font2=wx.TheFontList.FindOrCreateFont(20, family=wx.SWISS, style=wx.NORMAL, weight=wx.LIGHT)
        self.fontcolour=wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT)
        self.font2colour=wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNSHADOW)
        dc=wx.MemoryDC()
        # mac needs a bitmap selected in order to return textextent!
        if guihelper.IsMac():
            dc.SelectObject(wx.EmptyBitmap(100,100))
        w,h,d,l=dc.GetFullTextExtent("I", font=self.font)
        self.height=h+3
        self.descent=d

    def GetHeight(self):
        return self.height

    def Draw(self, dc, width):
        oldc=dc.GetTextForeground()
        oldf=dc.GetFont()
        dc.DrawLine(3, self.height-self.descent, width-3, self.height-self.descent)
        dc.SetTextForeground(self.font2colour)
        dc.SetFont(self.font2)
        for xoff in (0,1,2):
            for yoff in (0,1,2):
                dc.DrawText(self.label, xoff+3, yoff)
        dc.SetTextForeground(self.fontcolour)
        dc.SetFont(self.font)
        dc.DrawText(self.label, 1+3,1)
        dc.SetTextForeground(oldc)
        dc.SetFont(oldf)
                
class Item(object):
    """A generic item implementation.

    You don't need to inherit from this - it is mainly to document what you have to implement."""

    def Draw(self, dc, width, height, selected):
        """Draw yourself into the available space.  0,0 will be your top left.

        Note that the width may be larger than the
        L{DataSource.GetItemSize} method returned because unused space
        is spread amongst the items.  It will never be smaller than
        what was returned.  You should set the clipping region if
        necessary.

        The main display code needs to know the bounding box for each item so that it can tell
        when an item has been clicked on, as opposed to the white space surrounding an item.
        By default it clears the bounding box and looks at what area you draw on in this
        function.  If you return None, then that is what happens.

        Instead you may also return a 4 item tuple of (minx, miny, maxx, maxy) and that
        will be used.

        @param dc:  The device context to draw into
        @param width: maximum space to use
        @param height: maximum space to use
        @param selected: if the item is currently selected"""
        raise NotImplementedError()
    


class DataSource(object):
    """This is the model

    You don't need to inherit from this - it is mainly to document what you have to implement."""

    def GetSections(self):
        "Return a list of section headers"
        raise NotImplementedError()

    def GetItemSize(self, sectionnumber, sectionheader):
        "Return (width, height of each item)"
        return (160, 80)

    def GetItemsFromSection(self,sectionnumber,sectionheader):
        """Return a list of the items for the section.

        @param sectionnumber: the index into the list returned by L{GetSections}
        @param sectionheader: the section header object from that list
        """
        raise NotImplementedError()

if __name__=="__main__":



    def demo():
        import wx
        app=wx.PySimpleApp()

        import sys
        import common
        sys.excepthook=common.formatexceptioneh
        import wx.html
        import os
        import brewcompressedimage
        import wallpaper
        import fileinfo
        import conversions


        # find bitpim wallpaper directory
        config=wx.Config("bitpim", style=wx.CONFIG_USE_LOCAL_FILE)

        p=config.Read("path", "resources")
        pn=os.path.join(p, "wallpaper")
        if os.path.isdir(pn):
            p=pn

        imagespath=p
        images=[name for name in os.listdir(imagespath) if name[-4:] in (".bci", ".bit", ".bmp", ".jpg", ".png")]
        images.sort()
        #images=images[:9]

        print imagespath
        print images

        class WallpaperManager:

            def GetImageStatInformation(self,name):
                return wallpaper.statinfo(os.path.join(imagespath, name))    

            def GetImageConstructionInformation(self,file):
                file=os.path.join(imagespath, file)
                
                if file.endswith(".mp4") or not os.path.isfile(file):
                    return guihelper.getresourcefile('wallpaper.png'), wx.Image
                if self.isBCI(file):
                    return file, lambda name: brewcompressedimage.getimage(brewcompressedimage.FileInputStream(file))
                # LG phones may return a proprietary wallpaper media file, LGBIT
                fi=fileinfo.identify_imagefile(file)
                if fi is not None and fi.format=='LGBIT':
                    return file, conversions.convertfilelgbittobmp
                return file, wx.Image

            def isBCI(self, filename):
                # is it a bci file?
                return open(filename, "rb").read(4)=="BCI\x00"


        wx.FileSystem_AddHandler(wallpaper.BPFSHandler(WallpaperManager()))

        class TestItem(Item):

            def __init__(self, ds, secnum, itemnum, label):
                super(TestItem,self).__init__()
                self.label=label
                self.ds=ds
                self.secnum=secnum
                self.itemnum=itemnum

            def Draw(self, dc, width, height, selected):
                # uncomment to see exactly what size is given
                #dc.DrawRectangle(0,0,width,height)
                us=dc.GetUserScale()
                dc.SetClippingRegion(0,0,width,height)
                hdc=wx.html.HtmlDCRenderer()
                hdc.SetDC(dc, 1)
                hdc.SetSize(9999, 9999) # width is deliberately wide so that no wrapping happens
                hdc.SetHtmlText(self.genhtml(selected), '.', True)
                hdc.Render(0,0)
                del hdc
                # restore scale hdc messes
                dc.SetUserScale(*us)
                dc.DestroyClippingRegion()

                # Linux gets bounding box wrong, so we deliberately return actual size
                if guihelper.IsGtk():
                    return (0,0,width,height)
                elif guihelper.IsMSWindows():
                    return max(0,dc.MinX()), max(0, dc.MinY()), min(width, dc.MaxX()), min(height, dc.MaxY())

            def genhtml(self, selected):
                if selected:
                    selected='bgcolor="blue"'
                else:
                    selected=""
                return """<table %s><tr><td valign=top><p><img src="bpuserimage:%s;width=%d;height=%d;valign=top"><td valign=top><b>%s</b><br>BMP format<br>123x925<br>Camera</tr></table>""" \
                       % (selected, images[self.itemnum], self.ds.IMGSIZES[self.secnum][0], self.ds.IMGSIZES[self.secnum][1], self.label, )

        class TestDS(DataSource):

            SECTIONS=("Camera", "Wallpaper", "Oranges", "Lemons")
            ITEMSIZES=( (240,240), (160,70), (48,48), (160,70) )
            IMGSIZES=[ (w-110,h-20) for w,h in ITEMSIZES]
            IMGSIZES[2]=(16,16)

            def GetSections(self):
                return [SectionHeader(x) for x in self.SECTIONS]

            def GetItemsFromSection(self, sectionnumber, sectionheader):
                return [TestItem(self, sectionnumber, i, "%s-#%d" % (sectionheader.label,i)) for i in range(len(images))]

            def GetItemSize(self, sectionnumber, sectionheader):
                return self.ITEMSIZES[sectionnumber]

        f=wx.Frame(None, title="Aggregate Display Test")
        ds=TestDS()
        d=Display(f,ds, "wallpaper-watermark")
        f.Show()

        app.MainLoop()
    
    
    if __debug__ and True:
        def profile(filename, command):
            import hotshot, hotshot.stats, os
            file=os.path.abspath(filename)
            profile=hotshot.Profile(file)
            profile.run(command)
            profile.close()
            del profile
            howmany=100
            stats=hotshot.stats.load(file)
            stats.strip_dirs()
            stats.sort_stats('time', 'calls')
            stats.print_stats(20)
            stats.sort_stats('cum', 'calls')
            stats.print_stats(20)
            stats.sort_stats('calls', 'time')
            stats.print_stats(20)
            sys.exit(0)

        profile("aggdisplay.prof", "demo()")

    else:
        demo()
        
    
