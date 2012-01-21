### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
### Copyright (C) 2003-2004 Steven Palm <n9yty@n9yty.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: ringers.py 4379 2007-08-28 03:06:58Z djpham $

from __future__ import with_statement

import os
import time
import wx
from wx.lib import masked

import fileview
import guihelper
import pubsub
import aggregatedisplay
import wallpaper
import common
import fileinfo
import conversions
import helpids
import guihelper
import rangedslider

###
###  Ringers
###

class DisplayItem(fileview.FileViewDisplayItem):

    datakey='ringtone-index'
    datatype='Audio' # used in the tooltip


class RingerView(fileview.FileView):
    CURRENTFILEVERSION=2

    # this is only used to prevent the pubsub module
    # from being GC while any instance of this class exists
    __publisher=pubsub.Publisher
    media_notification_type=pubsub.ringtone_type
    database_key='ringtone-index'
    media_key='ringtone'
    default_origin="ringers"
    
    def __init__(self, mainwindow, parent, media_root, id=-1):
        self.mainwindow=mainwindow
        self._data={self.database_key: {}}
        fileview.FileView.__init__(self, mainwindow, parent, media_root, "ringtone-watermark")
        self.wildcard="Audio files|*.wav;*.mid;*.qcp;*.mp3;*.pmd;*.wma|Midi files|*.mid|Purevoice files|*.qcp|MP3 files|*.mp3|WMA files|*.wma|PMD/CMX files|*.pmd|All files|*.*"
        self.thedir=self.mainwindow.ringerpath
        self.modified=False
        pubsub.subscribe(self.OnListRequest, pubsub.REQUEST_RINGTONES)
        pubsub.subscribe(self.OnDictRequest, pubsub.REQUEST_RINGTONE_INDEX)
        self._raw_media=self._shift_down=False

    def updateprofilevariables(self, profile):
        self.maxlen=profile.MAX_RINGTONE_BASENAME_LENGTH
        self.filenamechars=profile.RINGTONE_FILENAME_CHARS
        self.excluded_origins=profile.excluded_ringtone_origins
        for o in profile.ringtoneorigins:
            self.media_root.AddMediaNode(o, self)

    def OnListRequest(self, msg=None):
        l=[self._data[self.database_key][x].name \
           for x in self._data[self.database_key] \
               if self._data[self.database_key][x].origin not in self.excluded_origins ]
        l.sort()
        pubsub.publish(pubsub.ALL_RINGTONES, l)

    def OnDictRequest(self, msg=None):
        pubsub.publish(pubsub.ALL_RINGTONE_INDEX, self._data[self.database_key].copy())

    def GetDeleteInfo(self):
        return guihelper.ART_DEL_RINGER, "Delete Ringer"

    def GetAddInfo(self):
        return guihelper.ART_ADD_RINGER, "Add Ringer"

    def OnAdd(self, evt=None):
        self._raw_media=self._shift_down
        super(RingerView, self).OnAdd(evt)
        # reset the fla
        self._shift_down=False

    def GetItemThumbnail(self, item, w, h):
        assert w==self.thumbnail.GetWidth() and h==self.thumbnail.GetHeight()
        return self.thumbnail

    def GetSections(self):
        # work out section and item sizes
        self.thumbnail=wx.Image(guihelper.getresourcefile('ringer.png')).ConvertToBitmap()
        
        dc=wx.MemoryDC()
        dc.SelectObject(wx.EmptyBitmap(100,100)) # unused bitmap needed to keep wxMac happy
        h=dc.GetTextExtent("I")[1]
        itemsize=self.thumbnail.GetWidth()+160, max(self.thumbnail.GetHeight(), h*4+DisplayItem.PADDING)+DisplayItem.PADDING*2
        
        # get all the items
        items=[DisplayItem(self, key) for key in self._data[self.database_key] if self._data[self.database_key][key].mediadata!=None]

        self.sections=[]
        
        if len(items)==0:
            return self.sections
        
        # get the current sorting type
        for sectionlabel, items in self.organizeby_Origin(items):
            self.media_root.AddMediaNode(sectionlabel, self)
            sh=aggregatedisplay.SectionHeader(sectionlabel)
            sh.itemsize=itemsize
            for item in items:
                item.thumbnailsize=self.thumbnail.GetWidth(), self.thumbnail.GetHeight()
            # sort items by name
            items.sort(self.CompareItems)
            self.sections.append( (sh, items) )
        return [sh for sh,items in self.sections]

    def GetItemsFromSection(self, sectionnumber, sectionheader):
        return self.sections[sectionnumber][1]

    def organizeby_Origin(self, items):
        types={}
        for item in items:
            t=item.origin
            if t is None: t="Default"
            l=types.get(t, [])
            l.append(item)
            types[t]=l

        keys=types.keys()
        keys.sort()
        return [ (key, types[key]) for key in types]

    def GetItemSize(self, sectionnumber, sectionheader):
        return sectionheader.itemsize

    def GetFileInfoString(self, string):
        return fileinfo.identify_audiostring(string)

    def GetFileInfo(self, filename):
        return fileinfo.identify_audiofile(filename)

    def ReplaceContents(self, name, origin, new_file_name):
        """Replace the contents of 'file_name' by the contents of
        'new_file_name' by going through the image converter dialog
        """
        file_stat=os.stat(new_file_name)
        mtime=file_stat.st_mtime
        afi=fileinfo.identify_audiofile(new_file_name)
        if afi.size<=0:
            return # zero length file or other issues
        newext,convertinfo=self.mainwindow.phoneprofile.QueryAudio(
            None, common.getext(new_file_name), afi)
        if convertinfo is not afi:
            filedata=None
            try:
                filedata=self.ConvertFormat(new_file_name, convertinfo)
            except:
                pass
            if filedata is None:
                return
        else:
            filedata=open(new_file_name, "rb").read()
        # check for the size limit on the file, if specified
        max_size=getattr(convertinfo, 'MAXSIZE', None)
        if max_size is not None and len(filedata)>max_size:
            # the data is too big
            self.log('ringtone %s is too big!'%common.basename(file))
            with guihelper.WXDialogWrapper(wx.MessageDialog(self,
                                                            'Ringtone %s may be too big.  Do you want to proceed anway?'%common.basename(file),
                                                            'Warning',
                                                            style=wx.YES_NO|wx.ICON_ERROR),
                                           True) as (dlg, dlg_resp):
                if dlg_resp==wx.ID_NO:
                    return
        self.AddToIndex(name, origin, filedata, self._data, mtime)

    @guihelper.BusyWrapper
    def OnAddFiles(self, filenames):
        for file in filenames:
            if file is None: continue  # failed dragdrop?
            file_stat=os.stat(file)
            mtime=file_stat.st_mtime
            if self._raw_media:
                target=self.get_media_name_from_filename(file)
                data=open(file, 'rb').read()
                self.AddToIndex(target, self.active_section, data, self._data, mtime)
            else:
                # do we want to convert file?
                afi=fileinfo.identify_audiofile(file)
                if afi.size<=0: continue # zero length file or other issues
                newext,convertinfo=self.mainwindow.phoneprofile.QueryAudio(None, common.getext(file), afi)
                if convertinfo is not afi:
                    filedata=None
                    wx.EndBusyCursor()
                    try:
                        filedata=self.ConvertFormat(file, convertinfo)
                    finally:
                        # ensure they match up
                        wx.BeginBusyCursor()
                    if filedata is None:
                        continue
                else:
                    filedata=open(file, "rb").read()
                # check for the size limit on the file, if specified
                max_size=getattr(convertinfo, 'MAXSIZE', None)
                if max_size is not None and len(filedata)>max_size:
                    # the data is too big
                    self.log('ringtone %s is too big!'%common.basename(file))
                    with guihelper.WXDialogWrapper(wx.MessageDialog(self,
                                                                    'Ringtone %s may be too big.  Do you want to proceed anway?'%common.basename(file),
                                                                    'Warning',
                                                                    style=wx.YES_NO|wx.ICON_ERROR),
                                                   True) as (dlg, dlg_resp):
                        if dlg_resp==wx.ID_NO:
                            continue
                target=self.get_media_name_from_filename(file, newext)
                self.AddToIndex(target, self.active_section, filedata, self._data, mtime)
        self.OnRefresh()

    def ConvertFormat(self, file, convertinfo):
        with guihelper.WXDialogWrapper(ConvertDialog(self, file, convertinfo),
                                       True) as (dlg, retcode):
            return dlg.newfiledata if retcode==wx.ID_OK else None

    def versionupgrade(self, dict, version):
        """Upgrade old data format read from disk

        @param dict:  The dict that was read in
        @param version: version number of the data on disk
        """

        # version 0 to 1 upgrade
        if version==0:
            version=1  # the are the same

        # 1 to 2 etc
        if version==1:
            print "converting to version 2"
            version=2
            d={}
            input=dict.get(self.database_key, {})
            for i in input:
                d[i]={'name': input[i]}
            dict[self.database_key]=d
        return dict

class ConvertDialog(wx.Dialog):

    ID_CONVERT=wx.NewId()
    ID_PLAY=wx.NewId()
    ID_PLAY_CLIP=wx.NewId()
    ID_STOP=wx.NewId()
    ID_TIMER=wx.NewId()
    ID_SLIDER=wx.NewId()

    # we need to offer all types here rather than using derived classes as the phone may support several
    # alternatives

    PARAMETERS={
        'MP3':  {
        'formats': ["MP3"],
        'samplerates': ["16000", "22050", "24000", "32000", "44100", "48000"],
        'channels': ["1", "2"],
        'bitrates': ["8", "16", "24", "32", "40", "48", "56", "64", "80", "96", "112", "128", "144", "160", "192", "224", "256", "320"],
        'setup': 'mp3setup',
        'convert': 'mp3convert',
        'filelength': 'mp3filelength',
        'final': 'mp3final',
        },

        'QCP': {
        'formats': ["QCP"],
        'samplerates': ["8000"],
        'channels': ["1"],
        'bitrates': ["13000"],
        'optimization': ['0-Best Sound Quality', '1', '2', '3-Smallest File Size'],
        'setup': 'qcpsetup',
        'convert': 'qcpconvert',
        'filelength': 'qcpfilelength',
        'final': 'qcpfinal',
        }
        
        }
       
        

    def __init__(self, parent, file, convertinfo):
        wx.Dialog.__init__(self, parent, title="Convert Audio File", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.SYSTEM_MENU|wx.MAXIMIZE_BOX)
        self.file=file
        self.convertinfo=convertinfo
        self.afi=None
        self.temporaryfiles=[]
        self.wavfile=common.gettempfilename("wav")      # full length wav equivalent
        self.clipwavfile=common.gettempfilename("wav")  # used for clips from full length wav
        self.temporaryfiles.extend([self.wavfile, self.clipwavfile])

        getattr(self, self.PARAMETERS[convertinfo.format]['setup'])()
        
        vbs=wx.BoxSizer(wx.VERTICAL)
        # create the covert controls
        self.create_convert_pane(vbs, file, convertinfo)
        # and the crop controls
        self.create_crop_panel(vbs)

        vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALL|wx.ALIGN_RIGHT, 5)

        self.SetSizer(vbs)
        vbs.Fit(self)

        # diable various things
        self.FindWindowById(wx.ID_OK).Enable(False)
        for i in self.cropids:
            self.FindWindowById(i).Enable(False)
        

        # Events
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
        wx.EVT_TIMER(self, self.ID_TIMER, self.OnTimer)
        wx.EVT_BUTTON(self, wx.ID_HELP, lambda _: wx.GetApp().displayhelpid(helpids.ID_DLG_AUDIOCONVERT))

        # timers and sounds
        self.sound=None
        self.timer=wx.Timer(self, self.ID_TIMER)

        # wxPython wrapper on Mac raises NotImplemented for wx.Sound.Stop() so
        # we hack around that by supplying a zero length wav to play instead
        if guihelper.IsMac():
            self.zerolenwav=guihelper.getresourcefile("zerolen.wav")


    def create_convert_pane(self, vbs, file, convertinfo):
        params=self.PARAMETERS[convertinfo.format]
        # convert bit
        bs=wx.StaticBoxSizer(wx.StaticBox(self, -1, "Convert"), wx.VERTICAL)
        bs.Add(wx.StaticText(self, -1, "Input File: "+file), 0, wx.ALL, 5)
        gs=wx.FlexGridSizer(2, 4, 5, 5)
        gs.Add(wx.StaticText(self, -1, "New Type"), 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        self.type=wx.ComboBox(self, style=wx.CB_DROPDOWN|wx.CB_READONLY, choices=params['formats'])
        gs.Add(self.type, 0, wx.ALL|wx.EXPAND, 5)
        gs.Add(wx.StaticText(self, -1, "Sample Rate (per second)"), 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        self.samplerate=wx.ComboBox(self, style=wx.CB_DROPDOWN|wx.CB_READONLY, choices=params['samplerates'])
        gs.Add(self.samplerate, 0, wx.ALL|wx.EXPAND, 5)
        gs.Add(wx.StaticText(self, -1, "Channels (Mono/Stereo)"), 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        self.channels=wx.ComboBox(self, style=wx.CB_DROPDOWN|wx.CB_READONLY, choices=params['channels'])
        gs.Add(self.channels, 0, wx.ALL|wx.EXPAND, 5)
        gs.Add(wx.StaticText(self, -1, "Bitrate (kbits per second)"), 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        self.bitrate=wx.ComboBox(self, style=wx.CB_DROPDOWN|wx.CB_READONLY, choices=params['bitrates'])
        gs.Add(self.bitrate, 0, wx.ALL|wx.EXPAND, 5)
        if params.has_key('optimization'):
            gs.Add(wx.StaticText(self, -1, 'Optimization'), 0,
                   wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            self.optimization=wx.ComboBox(self,
                                          style=wx.CB_DROPDOWN|wx.CB_READONLY,
                                          choices=params['optimization'])
            self.optimization.SetSelection(1)
            gs.Add(self.optimization, 0, wx.ALL|wx.EXPAND, 5)
        gs.AddGrowableCol(1, 1)
        gs.AddGrowableCol(3, 1)
        bs.Add(gs, 0, wx.EXPAND)

        bs.Add(wx.Button(self, self.ID_CONVERT, "Convert"), 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        vbs.Add(bs, 0, wx.EXPAND|wx.ALL, 5)
        # Fill out fields - we explicitly set even when not necessary due to bugs on wxMac
        if self.type.GetCount()==1:
            self.type.SetSelection(0)
        else:
            self.type.SetStringSelection(convertinfo.format)

        if self.channels.GetCount()==1:
            self.channels.SetSelection(0)
        else:
            self.channels.SetStringSelection(`convertinfo.channels`)

        if self.bitrate.GetCount()==1:
            self.bitrate.SetSelection(0)
        else:
            self.bitrate.SetStringSelection(`convertinfo.bitrate`)

        if self.samplerate.GetCount()==1:
            self.samplerate.SetSelection(0)
        else:
            self.samplerate.SetStringSelection(`convertinfo.samplerate`)
            
        # Events
        wx.EVT_BUTTON(self, self.ID_CONVERT, self.OnConvert)

    def create_crop_panel(self, vbs):
        # crop bit
        bs=wx.StaticBoxSizer(wx.StaticBox(self, -1, "Crop"), wx.VERTICAL)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.StaticText(self, -1, "Current Position"), 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        self.positionlabel=wx.StaticText(self, -1, "0                 ")
        hbs.Add(self.positionlabel, 0, wx.ALL, 5)
        hbs.Add(wx.StaticText(self, -1, "Est. Clip File length"), 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        self.lengthlabel=wx.StaticText(self, -1, "0                   ")
        hbs.Add(self.lengthlabel, 0, wx.ALL, 5)
        bs.Add(hbs, 0, wx.ALL, 5)
        # the start & end manual entry items
        hbs=wx.GridSizer(-1, 2, 0, 0)
        hbs.Add(wx.StaticText(self, -1, 'Clip Start (sec):'), 0, wx.EXPAND|wx.ALL, 5)
        self.clip_start=masked.NumCtrl(self, wx.NewId(), fractionWidth=2)
        hbs.Add(self.clip_start, 1, wx.EXPAND|wx.ALL, 5)
        hbs.Add(wx.StaticText(self, -1, 'Clip Duration (sec):'), 0, wx.EXPAND|wx.ALL, 5)
        self.clip_duration=masked.NumCtrl(self, wx.NewId(), fractionWidth=2)
        hbs.Add(self.clip_duration, 1, wx.EXPAND|wx.ALL, 5)
        hbs.Add(wx.StaticText(self, -1, 'Volume Adjustment (dB):'), 0,
                wx.EXPAND|wx.ALL, 5)
        self.clip_volume=masked.NumCtrl(self, wx.NewId(), fractionWidth=1)
        hbs.Add(self.clip_volume, 1, wx.EXPAND|wx.ALL, 5)
        clip_set_btn=wx.Button(self, wx.NewId(), 'Set')
        hbs.Add(clip_set_btn, 0, wx.EXPAND|wx.ALL, 5)
        bs.Add(hbs, 0, wx.EXPAND|wx.ALL, 5)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        self.slider=rangedslider.RangedSlider(self, id=self.ID_SLIDER, size=(-1, 30))
        hbs.Add(self.slider, 1, wx.EXPAND|wx.ALL, 5)
        bs.Add(hbs, 1, wx.EXPAND|wx.ALL, 5)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.Button(self, self.ID_STOP, "Stop"), 0, wx.ALL, 5)
        hbs.Add(wx.Button(self, self.ID_PLAY, "Play Position"), 0, wx.ALL, 5)
        hbs.Add(wx.Button(self, self.ID_PLAY_CLIP, "Play Clip"), 0, wx.ALL, 5)
        bs.Add(hbs, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
        vbs.Add(bs, 0, wx.EXPAND|wx.ALL, 5)
        wx.EVT_BUTTON(self, self.ID_PLAY, self.OnPlayPosition)
        wx.EVT_BUTTON(self, self.ID_PLAY_CLIP, self.OnPlayClip)
        wx.EVT_BUTTON(self, self.ID_STOP, self.OnStop)
        wx.EVT_BUTTON(self, clip_set_btn.GetId(), self.OnSetClip)

        rangedslider.EVT_POS_CHANGED(self, self.ID_SLIDER, self.OnSliderCurrentChanged)
        rangedslider.EVT_CHANGING(self, self.ID_SLIDER, self.OnSliderChanging)

        self.cropids=[self.ID_SLIDER, self.ID_STOP, self.ID_PLAY,
                      self.ID_PLAY_CLIP, self.clip_start.GetId(),
                      self.clip_duration.GetId(), self.clip_volume.GetId(),
                      clip_set_btn.GetId()]

    @guihelper.BusyWrapper
    def OnConvert(self, _):
        self.OnStop()
        for i in self.cropids:
            self.FindWindowById(i).Enable(False)
        self.FindWindowById(wx.ID_OK).Enable(False)
        getattr(self, self.PARAMETERS[self.convertinfo.format]['convert'])()
        self.wfi=fileinfo.getpcmfileinfo(self.wavfile)
        max_duration=round(self.wfi.duration, 2)+0.01
        self.clip_start.SetParameters(min=0.0, max=max_duration, limited=True)
        self.clip_duration.SetParameters(min=0.0, max=max_duration, limited=True)
        self.UpdateCrop()
        for i in self.cropids:
            self.FindWindowById(i).Enable(True)
        self.FindWindowById(wx.ID_OK).Enable(True)

    def UpdateCrop(self):
        self.positionlabel.SetLabel("%.1f secs" % (self.slider.GetCurrent()*self.wfi.duration),)
        duration=(self.slider.GetEnd()-self.slider.GetStart())*self.wfi.duration
        self.clip_start.SetValue(self.slider.GetStart()*self.wfi.duration)
        self.clip_duration.SetValue(duration)
        v=getattr(self, self.PARAMETERS[self.convertinfo.format]['filelength'])(duration)
        self.lengthlabel.SetLabel("%s" % (v,))



    def OnPlayClip(self,_):
        self._Play(self.slider.GetStart(), self.slider.GetEnd(),
                   self.clip_volume.GetValue())
              
    def OnPlayPosition(self, _):
        self._Play(self.slider.GetCurrent(), 1.0)

    def _Play(self, start, end, volume=None):
        self.OnStop()
        assert start<=end
        self.playstart=start
        self.playend=end
        
        self.playduration=(self.playend-self.playstart)*self.wfi.duration

        conversions.trimwavfile(self.wavfile, self.clipwavfile,
                                self.playstart*self.wfi.duration,
                                self.playduration, volume)
        self.sound=wx.Sound(self.clipwavfile)
        assert self.sound.IsOk()
        res=self.sound.Play(wx.SOUND_ASYNC)
        assert res
        self.starttime=time.time()
        self.endtime=self.starttime+self.playduration
        self.timer.Start(100, wx.TIMER_CONTINUOUS)
        
    def OnTimer(self,_):
        now=time.time()
        if now>self.endtime:
            self.timer.Stop()
            # assert wx.Sound.IsPlaying()==False
            self.slider.SetCurrent(self.playend)
            self.UpdateCrop()
            return
        # work out where the slider should go
        newval=self.playstart+((now-self.starttime)/(self.endtime-self.starttime))*(self.playend-self.playstart)
        self.slider.SetCurrent(newval)
        self.UpdateCrop()            


    def OnStop(self, _=None):
        self.timer.Stop()
        if self.sound is not None:
            if guihelper.IsMac():
                # There is no stop method for Mac so we play a one centisecond wav
                # which cancels the existing playing sound
                self.sound=None
                sound=wx.Sound(self.zerolenwav)
                sound.Play(wx.SOUND_ASYNC)
            else:
                self.sound.Stop()
                self.sound=None

    def OnSliderCurrentChanged(self, evt):
        self.OnStop()
        wx.CallAfter(self.UpdateCrop)
        
    def OnSliderChanging(self, _):
        wx.CallAfter(self.UpdateCrop)

    def _removetempfiles(self):
        for file in self.temporaryfiles:
            if os.path.exists(file):
                os.remove(file)

    @guihelper.BusyWrapper
    def OnOk(self, evt):
        self.OnStop()
        # make new data
        start=self.slider.GetStart()*self.wfi.duration
        duration=(self.slider.GetEnd()-self.slider.GetStart())*self.wfi.duration
        self.newfiledata=getattr(self, self.PARAMETERS[self.convertinfo.format]['final'])(
            start, duration, self.clip_volume.GetValue())
        # now remove files
        self._removetempfiles()
        # use normal handler to quit dialog
        evt.Skip()

    def OnCancel(self, evt):
        self.OnStop()
        self._removetempfiles()
        evt.Skip()

    def OnSetClip(self, _=None):
        s=self.clip_start.GetValue()
        d=self.clip_duration.GetValue()
        e=s+d
        if e<=self.wfi.duration:
            self.slider.SetStart(s/self.wfi.duration)
            self.slider.SetEnd(e/self.wfi.duration)
        self.UpdateCrop()

    ###
    ###  MP3 functions
    ###

    def mp3setup(self):
        self.mp3file=common.gettempfilename("mp3")
        self.tmp_mp3file=common.gettempfilename('mp3')
        self.temporaryfiles.append(self.mp3file)
        self.temporaryfiles.append(self.tmp_mp3file)

    def mp3convert(self):
        # make mp3 to work with
        open(self.mp3file, "wb").write(conversions.converttomp3(self.file, int(self.bitrate.GetStringSelection()), int(self.samplerate.GetStringSelection()), int(self.channels.GetStringSelection())))
        self.afi=fileinfo.getmp3fileinfo(self.mp3file)
        print "result is",len(self.afi.frames),"frames"
        # and corresponding wav to play
        conversions.converttowav(self.mp3file, self.wavfile)

    def mp3filelength(self, duration):
        # mp3 specific file length calculation
        frames=self.afi.frames
        self.beginframe=int(self.slider.GetStart()*len(frames))
        self.endframe=int(self.slider.GetEnd()*len(frames))
        length=sum([frames[frame].nextoffset-frames[frame].offset for frame in range(self.beginframe, self.endframe)])
        return length

    def _trim_mp3(self, start, duration):
        # mp3 writing out
        frames=self.afi.frames
        offset=frames[self.beginframe].offset
        length=frames[self.endframe-1].nextoffset-offset
        with file(self.mp3file, 'rb', 0) as f:
            f.seek(offset)
            return f.read(length)

    def _trim_and_adjust_vol_mp3(self, start, duration, volume):
        # trim, adjust volume, and write mp3 out
        # use the original to make a new wav, not the one that went through foo -> mp3 -> wav
        conversions.converttowav(self.file, self.wavfile,
                                 start=start, duration=duration)
        # adjust the volume
        conversions.adjustwavfilevolume(self.wavfile, volume)
        # convert to mp3
        return conversions.converttomp3(self.wavfile,
                                        int(self.bitrate.GetStringSelection()),
                                        int(self.samplerate.GetStringSelection()),
                                        int(self.channels.GetStringSelection()))

    def mp3final(self, start, duration, volume=None):
        if volume:
            # need to adjust volume
            return self._trim_and_adjust_vol_mp3(start, duration, volume)
        else:
            return self._trim_mp3(start, duration)

    ###
    ###  QCP/PureVoice functions
    ###

    def qcpsetup(self):
        self.qcpfile=common.gettempfilename("qcp")
        self.temporaryfiles.append(self.qcpfile)

    def qcpconvert(self):
        # we verify the pvconv binary exists first
        conversions.getpvconvbinary()
        # convert to wav first
        conversions.converttowav(self.file, self.wavfile, samplerate=8000, channels=1)
        # then to qcp
        conversions.convertwavtoqcp(self.wavfile, self.qcpfile,
                                    self.optimization.GetSelection())
        # and finally the wav from the qcp so we can accurately hear what it sounds like
        conversions.convertqcptowav(self.qcpfile, self.wavfile)

    def qcpfilelength(self, duration):
        # we don't actually know unless we do a conversion as QCP is
        # variable bitrate, so just assume the worst case of 13000
        # bits per second (1625 bytes per second) with an additional
        # 5% overhead due to the file format (I often see closer to 7%)
        return int(duration*1625*1.05) 

    def qcpfinal(self, start, duration, volume=None):
        # use the original to make a new wav, not the one that went through foo -> qcp -> wav
        conversions.converttowav(self.file, self.wavfile, samplerate=8000, channels=1, start=start, duration=duration)
        if volume is not None:
            conversions.adjustwavfilevolume(self.wavfile, volume)
        conversions.convertwavtoqcp(self.wavfile, self.qcpfile,
                                    self.optimization.GetSelection())
        return file(self.qcpfile, "rb").read()
