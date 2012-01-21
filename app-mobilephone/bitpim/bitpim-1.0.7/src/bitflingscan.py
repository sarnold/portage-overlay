### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: bitflingscan.py 2741 2006-01-09 03:32:08Z sawecw $

"""Scans the available bitfling ports in the same way as comscan and usbscan work
as well as providing the rest of the BitFling interface"""

import sys
import common

try:
    import bitfling.client as bitfling
except ImportError:
    bitfling=None

def IsBitFlingEnabled():
    if bitfling is None:
        return False
    return True

class BitFlingIsNotConfiguredException(Exception): pass

class flinger:

    def __init__(self, certverifier=None):
        self.certverifier=certverifier
        self.unconfigure()

    def isconfigured(self):
        return self.username is not None and \
               self.password is not None and \
               self.host is not None and \
               self.port is not None

    def _configure(self):
        if not self.isconfigured():
            raise BitFlingIsNotConfiguredException("BitFling needs to be configured")
        if self.client is None:
            self.client=bitfling.client(self.username, self.password, self.host, self.port, self.certverifier)
            
    def configure(self, username, password, host, port):
        self.client=None
        self.username=username
        self.password=password
        self.host=host
        self.port=port

    def unconfigure(self):
        self.username=self.password=self.host=self.port=self.client=None

    def getversion(self):
        self._configure()
        return self.client.getversion()

    def SetCertVerifier(self, certverifier):
        self.certverifier=certverifier

    def scan(self):
        if not self.isconfigured():
            return []
        self._configure()
        ports=self.client.scan()
        for p in range(len(ports)):
            ports[p]['BitFling']=True
            ports[p]['name']='bitfling::'+ports[p]['name']
        return ports

    # All the device methods

    def deviceopen(self, port, baud, timeout, hardwareflow, softwareflow):
        self._configure()
        return self.client.deviceopen(port, baud, timeout, hardwareflow, softwareflow)

    def deviceclose(self, handle):
        try:
            self._configure()
            # we don't care about close's failing
            self.client.deviceclose(handle)
        except:
            pass

    def devicesetbaudrate(self, handle, rate):
        self._configure()
        return self.client.devicesetbaudrate(handle, rate)

    def devicesetdtr(self, handle, dtr):
        self._configure()
        return self.client.devicesetdtr(handle, dtr)

    def devicesetrts(self, handle, rts):
        self._configure()
        return self.client.devicesetrts(handle, rts)

    def devicewrite(self, handle, data):
        self._configure()
        return self.client.devicewrite(handle, data)
    
    def devicesendatcommand(self, handle, sendatcommand, ignoreerror):
        self._configure()
        res=self.client.devicesendatcommand(handle, sendatcommand, ignoreerror)
        if res==0:
            raise
        elif res==1:
            res=[]
        return res
                          
    def devicereaduntil(self, handle, char, numfailures):
        self._configure()
        return self.client.devicereaduntil(handle, char, numfailures)

    def deviceread(self, handle, numchars):
        self._configure()
        return self.client.deviceread(handle, numchars)

    def devicereadsome(self, handle, numchars):
        self._configure()
        return self.client.devicereadsome(handle, numchars)

    def devicewritethenreaduntil(self, handle, data, char, numfailures):
        self._configure()
        return self.client.devicewritethenreaduntil(handle, data, char, numfailures)

# ensure there is a singleton
flinger=flinger()

encode=common.obfus_encode
decode=common.obfus_decode

# Unfortunately we have to do some magic to deal with threads
# correctly.  This code is called both from the gui/foreground thread
# (eg when calling the scan function) as well as from the background
# thread (eg when talking to a port over the protocol).  We also have
# to deal with certificate verification issues, since the cert
# verification has to happen in the gui/foreground.

# The way we solve this problem is to have a dedicated thread for
# running the flinger code in.  We hide this from the various callers
# by automatically transferring control to the bitfling thread and
# back again using Queue.Queue's

import thread
import threading
import Queue

class BitFlingWorkerThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.setName("BitFling worker thread")
        self.setDaemon(True)
        self.q=Queue.Queue()
        self.resultqueues={}
        self.eventloops={}

    def run(self):
        while True:
            q,func,args,kwargs=self.q.get()
            try:
                res=func(*args, **kwargs)
                q.put( (res, None) )
            except:
                q.put( (None, sys.exc_info()) )

    def callfunc(self, func, args, kwargs):
        qres=self.getresultqueue()
        self.q.put( (qres, func, args, kwargs) )
        # do we need event loop?
        loopfunc=self.eventloops.get(thread.get_ident(), None)
        if loopfunc is not None:
            while qres.empty():
                loopfunc()
        res, exc = qres.get()
        if exc is not None:
            ex=exc[1]
            ex.gui_exc_info=exc
            raise ex
        return res

    def getresultqueue(self):
        """Return the thread specific result Queue object

        They are automatically allocated on demand"""
        q=self.resultqueues.get(thread.get_ident(), None)
        if q is not None:
            return q
        q=Queue.Queue()
        self.resultqueues[thread.get_ident()]=q
        return q

    def setthreadeventloop(self, eventfunc):
        """Sets the eventloopfunction used for this thread"""
        self.eventloops[thread.get_ident()]=eventfunc

class CallWrapper:
    """Provides proxy method wrappers so that all method calls can be redirected to worker thread

    This works in a very similar way to how xmlrpclib wraps client side xmlrpc
    """

    class MethodIndirect:
        def __init__(self, func):
            self.func=func

        def __call__(self, *args, **kwargs):
            return CallWrapper.worker.callfunc(self.func, args, kwargs)
        
    worker=None
    object=None

    def __init__(self, worker, object):
        CallWrapper.worker=worker
        CallWrapper.object=object

    def __getattr__(self, name):
        if hasattr(self.worker, name):
            return getattr(self.worker, name)
        v=getattr(self.object, name)
        if callable(v):
            return self.MethodIndirect(v)
        return v
    

if IsBitFlingEnabled():
    BitFlingWorkerThread=BitFlingWorkerThread()
    BitFlingWorkerThread.start()

    # wrap it all up
    flinger=CallWrapper(BitFlingWorkerThread, flinger)
else:
    class flinger:
        def __getattr__(self, name):
            if name=="scan": return self.scan
            raise Exception("BitFling is not enabled")
        def __setattr__(self, name, value):
            raise Exception("BitFling is not enabled")
        def scan(self):
            return []
    flinger=flinger()


class CommConnection:
    # The constructor takes the same arguments as commport.CommConnection, but many
    # are ignored
    def __init__(self, logtarget, port, baud=115200, timeout=3, hardwareflow=0,
                 softwareflow=0, autolistfunc=None, autolistargs=None, configparameters=None):
        assert port.startswith("bitfling::")
        self.logtarget=logtarget
        self.port=port
        self.baud=baud
        self.timeout=timeout
        self.hardwareflow=hardwareflow
        self.softwareflow=softwareflow
        self.handle=None
        self._openport()

    def _openport(self):
        if self.handle is not None:
            self.close()
        self.log("Opening port %s, %d baud, timeout %f, hardwareflow %d, softwareflow %d" %
             (self.port, self.baud, float(self.timeout), self.hardwareflow, self.softwareflow) )
        self.handle=flinger.deviceopen(self.port[len("bitfling::"):], self.baud, self.timeout, self.hardwareflow,
                                       self.softwareflow)

    def IsAuto(self):
        return False
    
    def close(self):
        if self.handle is not None:
            flinger.deviceclose(self.handle)
            self.handle=None

    def reset(self):
        self._openport()

    def log(self, str):
        if self.logtarget:
            self.logtarget.log(self.port+": "+str)

    def logdata(self, str, data):
        if self.logtarget:
            self.logtarget.logdata(self.port+": "+str, data)

    def setbaudrate(self, rate):
        res=flinger.devicesetbaudrate(self.handle, rate)
        if res:
            self.baud=rate
        return res

    def setdtr(self, dtr):
        res=flinger.devicesetdtr(self.handle, dtr)
        return res

    def setrts(self, rts):
        res=flinger.devicesetrts(self.handle, rts)
        return res

    def write(self, data, log=True):
        if log:
            self.logdata("Writing", data)
        flinger.devicewrite(self.handle, data)

    def sendatcommand(self, atcommand, ignoreerror=False):
        res=flinger.devicesendatcommand(self.handle, atcommand, ignoreerror)
        return res
        
    def read(self, numchars=1, log=True):
        res=flinger.deviceread(self.handle, numchars)
        if log:
            self.logdata("Reading exact data - requested "+`numchars`, res)
        return res

    def readsome(self, log=True, numchars=-1):
        res=flinger.devicereadsome(self.handle, numchars)
        if log:
            self.logdata("Reading remaining data", res)
        return res

    def readuntil(self, char, log=True, logsuccess=True, numfailures=0):
        res=flinger.devicereaduntil(self.handle, char, numfailures)
        if log:
            pass # ::TODO: something when we get a timeout exception
        if logsuccess:
            self.logdata("Read completed", res)
        return res
            
    # composite methods which reduce round trips
    def writethenreaduntil(self, data, logwrite, char, logreaduntil=True, logreaduntilsuccess=True, numfailures=0):
        if logwrite:
            self.logdata("Writing", data)
        res=flinger.devicewritethenreaduntil(self.handle, data, char, numfailures)
        if logreaduntilsuccess:
            self.logdata("Read completed", res)
        return res
