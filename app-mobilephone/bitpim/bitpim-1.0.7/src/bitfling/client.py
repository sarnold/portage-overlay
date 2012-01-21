### BITPIM
###
### Copyright (C) 2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: client.py 2741 2006-01-09 03:32:08Z sawecw $

"""Code if you want to be a client of BitFling"""

# Standard imports
import sys
from xmlrpclib import Binary

# My imports
import xmlrpcstuff

class client:
    "A BitFling client"

    # Although we could just inherit straight from ServerProxy, this
    # code is here to help ensure calling convention, and in the
    # future deal with backwards compatibility issues.  We also deal
    # with XMLRPC specific issues such as marshalling binary data
    
    def __init__(self, username, password, host, port, certverifier=None):
        "The URL should include username and password if any"
        self.server=xmlrpcstuff.ServerProxy(username, password, host, port, certverifier)

    def getversion(self):
        return self.server.getversion()

    def scan(self):
        return self.server.scan()

    def deviceopen(self, port, baud, timeout, hardwareflow, softwareflow):
        return self.server.deviceopen(port, baud, timeout, hardwareflow, softwareflow)

    def deviceclose(self, handle):
        return self.server.deviceclose(handle)

    def devicesetbaudrate(self, handle, rate):
        return self.server.devicesetbaudrate(handle, rate)

    def devicesetdtr(self, handle, dtr):
        return self.server.devicesetdtr(handle, dtr)

    def devicesetrts(self, handle, rts):
        return self.server.devicesetrts(handle, rts)

    def devicewrite(self, handle, data):
        return self.server.devicewrite(handle, Binary(data))

    def devicesendatcommand(self, handle, atcommand, ignoreerror):
        return self.server.devicesendatcommand(handle, Binary(atcommand), ignoreerror)
    
    def devicereaduntil(self, handle, char, numfailures):
        return self.server.devicereaduntil(handle, Binary(char), numfailures).data

    def deviceread(self, handle, numchars):
        return self.server.deviceread(handle, numchars).data

    def devicereadsome(self, handle, numchars):
        return self.server.devicereadsome(handle, numchars).data

    def devicewritethenreaduntil(self, handle, data, char, numfailures):
        return self.server.devicewritethenreaduntil(handle, Binary(data), Binary(char), numfailures).data
