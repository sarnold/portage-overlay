# An attempt to make an HTML label widget that auto-sizes itself (eg gets longer as width is narrowed etc)
# Once this works, it will be added to the BitPim main code

import wx, wx.html

class HtmlLabel(wx.PyControl):

    def __init__(self, parent, id, label, basedirectory="",
                 pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.FULL_REPAINT_ON_RESIZE , name = "HtmlLabel"):
        self.html=label
        self.basedirectory=basedirectory
        wx.PyControl.__init__(self, parent, id, pos, size, style, wx.DefaultValidator, name)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def SetBestSize(self, size=None):
        if size is None:
            wx.PyControl.SetBestFittingSize(self, self.DoGetBestSize())
            return
        w,h=size
        wx.PyControl.SetBestFittingSize(self, self._gethtmlsize(self, w))

    def DoGetBestSize(self):
        return self._gethtmlsize()

    def _gethtmlsize(self, width=99999):
        if self.html is None or self.html=="":
            return wx.Size(1,1)
        bmp=wx.EmptyBitmap(1,1)
        mdc=wx.MemoryDC()
        mdc.SelectObject(bmp)
        hdc=wx.html.HtmlDCRenderer()
        hdc.SetDC(mdc, 1)
        hdc.SetSize(width, 99999)
        hdc.SetHtmlText(self.html, self.basedirectory)
        hdc.Render(0, 0, 0, False)
        print "Returning size of",mdc.MaxX(), mdc.MaxY()
        return wx.Size(mdc.MaxX(), mdc.MaxY())

    def OnPaint(self, event):
        dc=wx.PaintDC(self)
        dc.SetBackgroundMode(wx.SOLID)
        dc.Clear()
        hdc=wx.html.HtmlDCRenderer()
        hdc.SetDC(dc, 1)
        hdc.SetSize(*self.GetClientSizeTuple())
        hdc.SetHtmlText(self.html, self.basedirectory)
        hdc.Render(0, 0, 0, False)


class TestFrame(wx.Frame):

    def __init__(self, parent=None, id=-1, title="Test Frame"):
        wx.Frame.__init__(self, parent, id, title)
        vbs=wx.BoxSizer(wx.VERTICAL)
        vbs.Add(wx.StaticText(self, 0, "Static One"), 0, wx.ALL, 5)
        h=HtmlLabel(self, -1, testhtml)
        vbs.Add(h, 0, wx.ALL, 5)
        vbs.Add(wx.StaticText(self, 0, "Static Two"), 0, wx.ALL, 5)

        self.SetSizer(vbs)
        vbs.Fit(self)

testhtml="""<p>This is a long paragraph that should end up wrapped and make funky things happen to the width and height of the control.
It requires some very long pointless sentences to really get the full effect.
<p>This is a second paragraph.

<p><table>
<tr><th>Column One<th>Column two</tr>
<tr><td>A cell<td>Another cell</tr>
</table>
"""



app=wx.PySimpleApp()
f=TestFrame()
f.Show(True)
app.MainLoop()
