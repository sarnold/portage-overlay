###
### A wrapper for the libusb wrapper of the libusb library :-)
###
### This code is in the Public Domain.  (libusb and the wrapper
### are LGPL)
###

from __future__ import generators

import sys

if sys.platform=='win32':
    try:
        import win32api
        handle=win32api.LoadLibrary("libusb0.dll")
        win32api.FreeLibrary(handle)
    except:
        raise ImportError("libusb needs to be installed for this module to work")
    
import libusb as usb

# grab some constants and put them in our namespace

for sym in dir(usb):
    if sym.startswith("USB_CLASS_") or sym.startswith("USB_DT"):
        exec "%s=usb.%s" %(sym, sym)
del sym

TRACE=False

class USBException(Exception):
    def __init__(self):
        Exception.__init__(self, usb.usb_strerror())

def UpdateLists():
    """Updates the lists of busses and devices

    @return: A tuple of (change in number of busses, change in number of devices)
    """
    return usb.usb_find_busses(), usb.usb_find_devices()

class USBBus:
    "Wraps a bus"
    
    def __init__(self, usb_bus):
        self.bus=usb_bus

    def name(self):
        return self.bus.dirname

    def devices(self):
        dev=self.bus.devices
        while dev is not None:
            if dev.config is not None:
               yield USBDevice(dev)
            dev=dev.next
        raise StopIteration()

class USBDevice:
    "Wraps a device"

    def __init__(self, usb_device):
        self.usb=usb # save it so that it can't be GC before us
        self.dev=usb_device
        self.handle=usb.usb_open(self.dev)
        if TRACE: print "usb_open(%s)=%s" % (self.dev,self.handle)
        if self.handle is None:
            raise USBException()

    def __del__(self):
        self.close()

    def close(self):
        if self.handle is not None:
            if TRACE: print "usb_close(%s)" % (self.handle,)
            self.usb.usb_close(self.handle)
            self.handle=None
        self.usb=None

    def number(self):
        return self.dev.bInterfaceNumber

    def name(self):
        return self.dev.filename

    def vendor(self):
        return self.dev.descriptor.idVendor

    def vendorstring(self):
        return self._getstring("iManufacturer")

    def productstring(self):
        return self._getstring("iProduct")

    def serialnumber(self):
        return self._getstring("iSerialNumber")

    def _getstring(self, fieldname):
        n=getattr(self.dev.descriptor, fieldname)
        if n:
            res,string=usb.usb_get_string_simple(self.handle, n, 1024)
            if TRACE: print "usb_get_string_simple(%s, %d, %d)=%d,%s" % (self.handle, n, 1024, res, string)
            if res<0:
                raise USBException()
            return string
        return None

    def product(self):
        return self.dev.descriptor.idProduct

    def interfaces(self):
        for i in range(self.dev.config.bNumInterfaces):
            yield USBInterface(self, usb.usb_interface_index(self.dev.config.interface, i))
        raise StopIteration()

    def classdetails(self):
        "returns a tuple of device class, devicesubclass, deviceprotocol (all ints)"
        return self.dev.descriptor.bDeviceClass, \
               self.dev.descriptor.bDeviceSubClass, \
               self.dev.descriptor.bDeviceProtocol

class USBInterface:

    # currently we only deal with first configuration
    def __init__(self, device, iface, alt=None):
        self.iface=iface
        self.device=device
        self.desc=alt or iface.altsetting

    def number(self):
        return self.desc.bInterfaceNumber

    def altnumber(self):
        return self.desc.bAlternateSetting

    def classdetails(self):
        return self.desc.bInterfaceClass, \
               self.desc.bInterfaceSubClass, \
               self.desc.bInterfaceProtocol

    def openbulk(self,epinno=None,epoutno=None):
        "Returns a filelike object you can use to read and write"
        # find the endpoints
        match=lambda ep1, ep2: (ep1 is None) or (ep2 is None) or ((ep1 & 0x7f) == (ep2 & 0x7f))

        epin=None
        epout=None
        for ep in self.endpoints():
            if ep.isbulk():
                if ep.direction()==ep.IN:
                    if (not epin) and match(epinno,ep.address()): epin=ep
                else:
                    if (not epout) and match(epoutno,ep.address()): epout=ep
        assert epin is not None
        assert epout is not None

        # set the configuration
        if TRACE:
            print "getting configvalue"
        v=self.device.dev.config.bConfigurationValue
        if TRACE:
            print "value is",v,"now about to set config"
        res=usb.usb_set_configuration(self.device.handle, v)
        if TRACE:
            print "usb_set_configurationds(%s, %d)=%d" % (self.device.handle,v,res)
            print "config set"
            # grab the interface
            print "claiming",self.number()
        res=usb.usb_claim_interface(self.device.handle, self.number())
        if TRACE: print "usb_claim_interface(%s, %d)=%d" % (self.device.handle, self.number(), res)
        if res<0:
            raise USBException()

        # set the alt setting
        res=usb.usb_set_altinterface(self.device.handle, self.altnumber())
        if TRACE: print "usb_set_alt_interface(%s, %d)=%d" % (self.device.handle, self.altnumber(), res)
        if res<0:
            # Setting the alternate interface causes problems with some phones (VX-10000)
            # reset the device and reclaim the interface if there was problem setting the
            # alternate interface.
            usb.usb_reset(self.device.handle)
            usb.usb_release_interface (self.device.handle, self.number())

            res=usb.usb_claim_interface(self.device.handle, self.number())
            if res<0:
                raise USBException()

        # we now have the file
        return USBFile(self, epin, epout)

    def alternates(self):
       for i in range(self.iface.num_altsetting):
           yield USBInterface(self.device,self.iface,usb.usb_interface_descriptor_index(self.iface.altsetting,i))
    # a generator raises its StopIteration() by itself

    def endpoints(self):
       for i in range(self.desc.bNumEndpoints):
           yield USBEndpoint(usb.usb_endpoint_descriptor_index(self.desc.endpoint, i))
       raise StopIteration()

class USBEndpoint:
    # type of endpoint
    TYPE_CONTROL=usb.USB_ENDPOINT_TYPE_CONTROL
    TYPE_ISOCHRONOUS=usb.USB_ENDPOINT_TYPE_ISOCHRONOUS
    TYPE_BULK=usb.USB_ENDPOINT_TYPE_BULK
    TYPE_INTERRUPT=usb.USB_ENDPOINT_TYPE_INTERRUPT
    # direction for bulk
    IN=usb.USB_ENDPOINT_IN
    OUT=usb.USB_ENDPOINT_OUT
    def __init__(self, ep):
        self.ep=ep

    def type(self):
        return self.ep.bmAttributes&usb.USB_ENDPOINT_TYPE_MASK

    def address(self):
        return self.ep.bEndpointAddress

    def maxpacketsize(self):
        return self.ep.wMaxPacketSize

    def isbulk(self):
        return self.type()==self.TYPE_BULK

    def direction(self):
        assert self.isbulk()
        return self.ep.bEndpointAddress&usb.USB_ENDPOINT_DIR_MASK
        
class USBFile:

    def __init__(self, iface, epin, epout):
        self.usb=usb  # save this so that our destructor can run
        self.claimed=True
        self.iface=iface
        self.epin=epin
        self.epout=epout
        self.addrin=epin.address()
        self.addrout=epout.address()
        self.insize=epin.maxpacketsize()
        self.outsize=epout.maxpacketsize()

    def __del__(self):
        self.close()

    def resetep(self, resetin=True, resetout=True):
        if resetin:
            res=usb.usb_clear_halt(self.iface.device.handle, self.addrin)
            if TRACE: print "usb_clear_halt(%s,%d)=%d" % (self.iface.device.handle, self.addrin, res)
            res=usb.usb_resetep(self.iface.device.handle, self.addrin)
            if TRACE: print "usb_resetep(%s,%d)=%d" % (self.iface.device.handle, self.addrin, res)
        if resetout:
            res=usb.usb_clear_halt(self.iface.device.handle, self.addrout)
            if TRACE: print "usb_clear_halt(%s,%d)=%d" % (self.iface.device.handle, self.addrout, res)
            res=usb.usb_resetep(self.iface.device.handle, self.addrout)
            if TRACE: print "usb_resetep(%s,%d)=%d" % (self.iface.device.handle, self.addrout, res)

    def read(self,howmuch=1024, timeout=1000):
        data=""
        while howmuch>0:
            res,str=usb.usb_bulk_read_wrapped(self.iface.device.handle, self.addrin, self.insize, int(timeout))
            if TRACE: print "usb_bulk_read(%s,%d,%d,%d)=%d,%s" % (self.iface.device.handle, self.addrin, self.insize, timeout, res, `str`)
            if res<0:
                if len(data)>0:
                    return data
                e=USBException()
                raise e
            if res==0:
                return data
            data+=str
            howmuch-=len(str)
            if howmuch and len(str)!=self.insize:
                # short read, no more data
                break

        return data

    def write(self, data, timeout=1000):
        first=True
        while first or len(data):
            first=False
            res=usb.usb_bulk_write(self.iface.device.handle, self.addrout, data[:min(len(data), self.outsize)], timeout)
            if TRACE: print "usb_bulk_write(%s, %d, %d bytes, %d)=%d" % (self.iface.device.handle, self.addrout, min(len(data), self.outsize), timeout, res)
            if res<0:
                raise USBException()
            data=data[res:]

    def close(self):
        if self.claimed:
            self.resetep()
            self.usb.usb_release_interface(self.iface.device.handle, self.iface.number())
        self.usb=None
        self.claimed=False

def OpenDevice(vendorid, productid, interfaceid):
    for bus in AllBusses():
        for device in bus.devices():
            if device.vendor()==vendorid and device.product()==productid:
                for iface in device.interfaces():
                    if iface.number()==interfaceid:
                        return iface.openbulk()
    raise ValueError( "vendor 0x%x product 0x%x interface %d not found" % (vendorid, productid, interfaceid))
        
    
def classtostring(klass):
    "Returns the class as a string"
    for sym in dir(usb):
        if sym.startswith("USB_CLASS_") and klass==getattr(usb, sym):
            return sym
    return `klass`

def eptypestring(type):
    for sym in dir(USBEndpoint):
        if sym.startswith("TYPE_") and type==getattr(USBEndpoint, sym):
            return sym
    return `type`
    
def AllBusses():
    bus=usb.usb_get_busses()
    while bus is not None:
        yield USBBus(bus)
        bus=bus.next
    raise StopIteration()

# initialise
usb.usb_init() # sadly no way to tell if this has failed

if __name__=='__main__':

    bus,dev=UpdateLists()
    print "%d busses, %d devices" % (bus,dev)

    for bus in AllBusses():
        print bus.name()
        for device in bus.devices():
            print "  %x/%x %s" % (device.vendor(), device.product(), device.name())
            klass,subclass,proto=device.classdetails()
            print "  class %s subclass %d protocol %d" % (classtostring(klass), subclass, proto)
            for i in device.vendorstring, device.productstring, device.serialnumber:
                try:
                    print "  "+i()
                except:
                    pass
            for iface in device.interfaces():
                print "      interface number %d" % (iface.number(),)
                klass,subclass,proto=iface.classdetails()
                print "      class %s subclass %d protocol %d" % (classtostring(klass), subclass, proto)
                for ep in iface.endpoints():
                    print "          endpointaddress 0x%x" % (ep.address(),)
                    print "          "+eptypestring(ep.type()),
                    if ep.isbulk():
                        if ep.direction()==ep.IN:
                            print "IN"
                        else:
                            print "OUT"
                    else:
                        print

                print ""
            print ""
        print ""

    print "opening device"
    cell=OpenDevice(0x1004, 0x6000, 2)
    print "device opened, about to write"
    cell.write("\x59\x0c\xc4\xc1\x7e")
    print "wrote, about to read"
    res=cell.read(12)
    print "read %d bytes" % (len(res),)
    print `res`
    cell.close()
