#!/usr/bin/env python

import serial.serialwin32
import win32file
import win32event
import time
import win32api

def thetime():
    now=time.time()
    t=time.localtime(now)
    return "%d:%02d:%02d.%03d [GLE=%s]"  % ( t[3], t[4], t[5],  int((now-int(now))*1000), win32api.FormatMessage(0)[:-2])

class Serial(serial.serialwin32.Serial):

    # no __init__ since it is the same

    def readuntil(self, char):
        "read bytes from serial port until char is hit"

        if not self.hComPort: raise portNotOpenError
        print thetime(), "readuntil entered"
        overlapped = win32file.OVERLAPPED()
        overlapped.hEvent = win32event.CreateEvent(None, 1, 0, None)
        dcb=win32file.GetCommState(self.hComPort)
        oldevt=dcb.EvtChar
        dcb.EvtChar=char
        rc=win32file.SetCommState(self.hComPort, dcb)
        print thetime(), "setcommstate returned", rc
        oldmask=win32file.GetCommMask(self.hComPort)
        rc=win32file.SetCommMask(self.hComPort, win32file.EV_RXFLAG)
        print thetime(), "setcommmask returned", rc
        rc,mask=win32file.WaitCommEvent(self.hComPort, overlapped)
        print thetime(),"waitcommevent returned",rc,mask
        rc=win32event.WaitForSingleObject(overlapped.hEvent, 10000)
        print thetime(),"waitforsingleobject returned",rc
        n=win32file.GetOverlappedResult(self.hComPort, overlapped, 0)
        print thetime(), "getoverlappedresult returned", n
        win32file.SetCommMask(self.hComPort, oldmask)
        flags,comstat=win32file.ClearCommError(self.hComPort)
        print thetime(),"clearcommerror",flags,comstat.cbInQue
        rc, buf=win32file.ReadFile(self.hComPort, win32file.AllocateReadBuffer(comstat.cbInQue), overlapped)
        print thetime(),"readfile retrurned", rc
        n=win32file.GetOverlappedResult(self.hComPort, overlapped, 1)
        print thetime(),"getoverlappedresult returned",n
        read=str(buf[:n])
        return read
        
