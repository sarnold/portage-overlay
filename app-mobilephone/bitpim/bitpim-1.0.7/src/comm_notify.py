### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: comm_notify.py 4219 2007-05-09 02:15:50Z djpham $

"""Handle notification of comm ports availability using DNOTIFY"""

import fcntl
import os
import signal
import sys

import wx

bpCOMM_NOTIFICATION_EVENT = wx.NewEventType()
COMM_NOTIFICATION_EVENT = wx.PyEventBinder(bpCOMM_NOTIFICATION_EVENT, 0)
default_port=5002

class CommNotificationEvent(wx.PyEvent):
    add=0
    remove=1
    def __init__(self):
        super(CommNotificationEvent, self).__init__()
        self.SetEventType=bpCOMM_NOTIFICATION_EVENT
        self.type=None
        self.comm=None

class CommNotification(object):
    def __init__(self, mainwindow):
        self.mw=mainwindow
        self.evt=CommNotificationEvent()

    def add(self, comm):
        # a new comm has just been added
        self.evt.type=CommNotificationEvent.add
        if comm.startswith('/proc/bus/usb/') or \
           comm.startswith('/dev/bus/usb/'):
            # this is a Linux hotplug USB port, which may have many interfaces.
            # can't figure which one so scan for all ports.
            self.evt.comm=None
        else:
            self.evt.comm=comm
        self.mw.OnCommNotification(self.evt)
        return True

    def remove(self, comm):
        # a new comm has just been deleted
        if comm.startswith('/proc/bus/usb/') or \
           comm.startswith('/dev/bus/usb/'):
            # This is a Linux hotplug USB port, just ignore it
            return False
        self.evt.type=CommNotificationEvent.remove
        self.evt.comm=comm
        self.mw.OnCommNotification(self.evt)
        return True

NotificationPath='/var/bitpim'
NotificationFile='/var/bitpim/dnotify.log'

def _process_notification(commobj):
    # read the log file & process its content
    # expecting a line: add|del <port>
    global NotificationFile
    try:
        _s=file(NotificationFile, 'rt').read()
        _tkns=_s.split(' ')
        if len(_tkns)==2:
            if _tkns[0]=='add':
                commobj.add(_tkns[1])
            else:
                commobj.remove(_tkns[1])
    except:
        if __debug__:
            raise

_global_fd=None
_global_obj=None

def _sigio_handler(*args, **kwargs):
    global _global_obj
    if _global_obj:
        wx.CallAfter(_process_notification, _global_obj)

def run_server(mainwindow):
    global NotificationPath, _global_fd, _global_obj
    _global_obj=CommNotification(mainwindow)
    try:
        _global_fd=os.open(NotificationPath, os.O_RDONLY)
    except OSError:
        # Something's wrong with the dir, bail
        mainwindow.log('Failed to open dir '+NotificationPath)
        return False
    except:
        if __debug__:
            raise
        return False
    fcntl.fcntl(_global_fd, fcntl.F_NOTIFY,
                fcntl.DN_MODIFY|fcntl.DN_CREATE|fcntl.DN_MULTISHOT)
    mainwindow.log('USB Comm Watch started')
    return True

def start_server(mainwindow):
    signal.signal(signal.SIGIO, _sigio_handler)
    return run_server(mainwindow)
