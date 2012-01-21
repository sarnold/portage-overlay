### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@netzero.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: update.py 4380 2007-08-29 00:17:07Z djpham $

# system modules
from __future__ import with_statement
import copy
import urllib2
import xml.dom.minidom
import webbrowser

# site-packages
import wx

# BitPim modules
import guihelper
import version

#-------------------------------------------------------------------------------
class Download(object):
    def __init__(self, source, platform, flavor=None):
        self.__src=source
        self.__platform=platform
        self.__flavor=flavor
    def __get_src(self):
        return self.__src
    def __get_platform(self):
        return self.__platform
    def __get_flavor(self):
        return self.__flavor
    source=property(fget=__get_src)
    platform=property(fget=__get_platform)
    flavor=property(fget=__get_flavor)

#-------------------------------------------------------------------------------
class Version(object):
    def __init__(self, name, release_date, change_log):
        self.__name=name
        self.__release_date=release_date
        self.__change_log=change_log
        self.__downloads=[]
    def __get_name(self):
        return self.__name
    def __get_release_date(self):
        return self.__release_date
    def __get_change_log(self):
        return self.__change_log
    name=property(fget=__get_name)
    release_date=property(__get_release_date)
    change_log=property(__get_change_log)

    def add_download(self, download):
        self.__downloads.append(download)
    def get_download(self, platform, flavor=''):
        for n in self.__downloads:
            if n.platform==platform and n.flavor==flavor:
                return n
        return None

#-------------------------------------------------------------------------------
class Update(object):
    def __init__(self, frm, to, priority, alert):
        self.__frm=frm
        self.__to=to
        self.__priority=priority
        self.__alert=alert
    def __get_info(self):
        return (self.__frm, self.__to, self.__priority, self.__alert)
    info=property(fget=__get_info)
    
#-------------------------------------------------------------------------------
class BitPimUpdate(object):
    def __init__(self):
        self.__xml_version='Unknown'
        self.__updates={}
        self.__versions={}
        self.__latest=None
    def __get_xml_version(self):
        return self.__xml_version
    xml_version=property(fget=__get_xml_version)
    def __get_versions(self):
        return copy.deepcopy(self.__versions, {})
    def __get_updates(self):
        return copy.deepcopy(self.__updates, {})
    def __get_latest_version(self):
        return self.__latest
    versions=property(fget=__get_versions)
    updates=property(fget=__get_updates)
    latest_version=property(fget=__get_latest_version)

    def __get_node_value(self, node, name):
        try:
            return node.getElementsByTagName(name)[0].firstChild.data
        except IndexError:
            # the tag does not exist
            return None
        except:
            if __debug__: raise
            return None

    __default_url='http://www.bitpim.org/updates.xml'
    def get_update_info(self, url=__default_url):
        # get the contents of the update file
        dom=xml.dom.minidom.parseString(urllib2.urlopen(url).read())
        # and extract the info
        bp_update=dom.getElementsByTagName('BitPimUpdate')[0]
        self.__xml_version=bp_update.getAttribute('version')
        self.__latest=bp_update.getAttribute('latest')
        
        updates=dom.getElementsByTagName('update')
        for n in updates:
            frm=n.getAttribute('from')
            self.__updates[frm]=Update(frm,
                                       self.__get_node_value(n, 'to'),
                                       self.__get_node_value(n, 'priority'),
                                       self.__get_node_value(n, 'alert'))
        versions=dom.getElementsByTagName('version')
        for n in versions:
            name=n.getAttribute('name')
            v=Version(name, self.__get_node_value(n, 'releasedate'),
                      n.getElementsByTagName('changelog')[0].getAttribute('src'))
            downloads=n.getElementsByTagName('download')
            for d in downloads:
                v.add_download(Download(\
                    d.getAttribute('src'),
                    d.getAttribute('platform'),
                    d.getAttribute('flavor')))
            self.__versions[name]=v

    def display_update_info(self, current_version, platform, flavor):
        # find and display the update info based on current version & platform
        # find if there's a next version
        u=self.__updates.get(current_version, None)
        if u is None:
            # there're no next version, tell the user & bail
            return 'There are no updates to the current version: '+current_version
        # got the update, look for the version
        (frm, next_version, priority, alert)=u.info
        v=self.__versions.get(next_version, None)
        if v is None:
            # No info on this version, tell the user & bail
            return 'No download info on version '+next_version+' available.'
        dl=v.get_download(platform, flavor)
        if dl is None or not len(dl.source):
            # the next version is not available for this plaform, bail
            return 'Load '+next_version+' is not available on platform '+platform+'/'+flavor
        # everything's there, display them to the users
        lines=[]
        lines.append('Current Version: '+current_version)
        s='Platform: '+platform
        if flavor is not None and len(flavor):
            s+='/'+flavor
        lines.append(s)
        lines.append('Available for Upgrade:')
        lines.append('\tVersion: '+next_version)
        lines.append('\tRelease Date: '+v.release_date)
        if priority is not None and len(priority):
            lines.append('\tPriority: '+priority)
        if alert is not None and len(alert):
            lines.append('\tWarning: '+alert)
        lines.append('updates.xml Version: '+self.xml_version)
        lines.append('Latest BitPim Version: '+self.latest_version)
        with guihelper.WXDialogWrapper(UpdateDialog(None, dl.source, v.change_log, lines),
                                       True):
            pass

#-------------------------------------------------------------------------------
class UpdateDialog(wx.Dialog):
    def __init__(self, parent, source_url, change_log_url, lines,
                 _title='BitPim Update'):
        wx.Dialog.__init__(self, parent, -1, _title)
        self.__source_url=source_url
        self.__changelog_url=change_log_url
        vbs=wx.BoxSizer(wx.VERTICAL)
        for l in lines:
            vbs.Add(wx.StaticText(self, -1, l), 0, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        change_log_btn=wx.Button(self, wx.NewId(), 'View Change Log')
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(change_log_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        get_update_btn=wx.Button(self, wx.NewId(), 'Download Update')
        hbs.Add(get_update_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbs.Add(wx.Button(self, wx.ID_CANCEL, 'Quit'), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        vbs.Add(hbs, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        # event handlers
        wx.EVT_BUTTON(self, change_log_btn.GetId(), self.__OnChangelog)
        wx.EVT_BUTTON(self, get_update_btn.GetId(), self.__OnGetUpdate)
        # all done
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)

    def __OnChangelog(self, _):
        webbrowser.open(self.__changelog_url)

    def __OnGetUpdate(self, _):
        webbrowser.open(self.__source_url)

#-------------------------------------------------------------------------------
def check_update(update_url=None, current_version=None,
                 platform=None, flavor=''):
    # get info from current version
    if current_version is None:
        current_version=version.version
    # set flavor to blank for now, should be flavor=version.flavor
    if platform is None:
        if guihelper.IsMSWindows():
            platform='windows'
        elif guihelper.IsGtk():
            platform='linux'
        elif guihelper.IsMac():
            platform='mac'
        else:
            raise ValueError, 'Invalid platform'
    # todo: need to figure out how to do flavor, comment out for now
##    flavor=version.vendor
    # retrieve and parse update info
    print 'Checking update for BitPim ', current_version, ' running on ', \
          platform, '-', flavor
    with guihelper.WXDialogWrapper(wx.ProgressDialog('BitPim Update',
                                                     'Retrieving BitPim Update Information...',
                                                     style=wx.PD_AUTO_HIDE)) as dlg:
        bp_update=BitPimUpdate()
        s=None
        try:
            if update_url is None:
                bp_update.get_update_info()
            else:
                bp_update.get_update_info(update_url)
            dlg.Update(100)
        except:
            s='Failed to get BitPim update info.'
    if s is None:
        s=bp_update.display_update_info(current_version, platform, flavor)
        latest_version=bp_update.latest_version
    else:
        latest_version=''
    if s is not None:
        # error messages being return, display them
        guihelper.MessageDialog(None, s, 'BitPim Update', wx.OK|wx.ICON_INFORMATION)
    return latest_version

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    if len(sys.argv)==2 and (sys.argv[1]=='help' or sys.argv[1]=='-help' \
                             or sys.argv[1]=='-h'):
        print sys.argv[0], '<updates.xml URL> <current BitPim Version> <Platform> <Flavor>'
        sys.exit(0)
    app=wx.PySimpleApp()
    if len(sys.argv)==1:
        s=check_update()
    else:
        s=check_update(*sys.argv[1:])
    print 'The latest version is: ', s
