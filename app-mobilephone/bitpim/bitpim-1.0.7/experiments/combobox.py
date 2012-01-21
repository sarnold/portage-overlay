import wx

app=wx.PySimpleApp()


f=wx.Frame(None,-1, "test")

choices=[ "5", "1", "3", "2"] # deliberately unsorted

cb1=wx.ComboBox(f, -1, style=wx.CB_DROPDOWN, choices=choices)
cb2=wx.ComboBox(f, -1, "", style=wx.CB_DROPDOWN, choices=choices)
cb3=wx.ComboBox(f, -1,  style=wx.CB_DROPDOWN|wx.CB_READONLY, choices=choices)
cb4=wx.ComboBox(f, -1,  "", style=wx.CB_DROPDOWN|wx.CB_READONLY, choices=choices)
cb5=wx.ComboBox(f, -1,  "3", style=wx.CB_DROPDOWN|wx.CB_READONLY, choices=choices)
cb6=wx.ComboBox(f, -1,  style=wx.CB_DROPDOWN|wx.CB_READONLY|wx.CB_SORT, choices=choices)
cb7=wx.ComboBox(f, -1,  "", style=wx.CB_DROPDOWN|wx.CB_READONLY, choices=choices)
cb8=wx.ComboBox(f, -1,  "3", style=wx.CB_DROPDOWN|wx.CB_READONLY, choices=choices)

all=cb1,cb2,cb3,cb4,cb5,cb6,cb7,cb8

for num,cb in zip(range(1,999), all):
    print "cb%d: GetSelection() = %d" % (num,cb.GetSelection())
    print "cb%d: GetValue() = %s" % (num,`cb.GetValue()`)

vs=wx.BoxSizer(wx.VERTICAL)
for cb in all: vs.Add(cb,0, wx.EXPAND|wx.ALL,5)
f.SetSizer(vs)
vs.Fit(f)
f.Show()
app.MainLoop()
