#!/usr/bin/env python
### BITPIM
###
### Copyright (C) 2003 Steve Palm <n9yty@n9yty.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: usb_ids.py 2867 2006-03-05 01:03:55Z djpham $

"""Parse the usb.ids file for quick access to the information contained therein"""

import re

vendor_re = re.compile(r"^([0-9A-Fa-f]{4,4})\s+(.*)$")
device_re = re.compile(r"^\t([0-9A-Fa-f]{4,4})\s+(.*)$")
iface_re = re.compile(r"^\t\t([0-9A-Fa-f]{2,2})\s+(.*)$")
usbclass_re = re.compile(r"^C\s([0-9A-Fa-f]{2,2})\s+(.*)$")
usbsubclass_re = re.compile(r"^\t([0-9A-Fa-f]{2,2})\s+(.*)$")
usbprotocol_re = re.compile(r"^\t\t([0-9A-Fa-f]{2,2})\s+(.*)$")

###
###  USB Info superclass
###
class usbInfoObject:
	""" Super class for all types of USB vendor/device/interface/class/sublcass/protocol
		classes which will be descendants of this. I chose to make and use various children
		of this class, as it's possible they may have unique information of their own some
		time later, as well as allowing a more natural name/syntax based on object use.
	"""
	def __init__(self, id, description):
		""" Set our ID code, description, and prepare to accept children """
		self.id = id
		self.description = description
		self.children = {};
	
	def description(self):
		""" Return the description for this object """
		return self.description

	def id(self):
		""" Return our ID code """
		return self.id

	def addChild(self, child):
		""" Add a child to our list """
		self.children[int(child.id, 16)] = child

	def getChild(self, child):
		""" If we have a child matching the request, return it """
		if child in self.children:
			return self.children[child]
		else:
			return None
	
	def getChildren(self):
		""" Return a list of all our children """
		return self.children.values()

###
###  USB ID file superclass --- This is our master object
###
class usb_ids:
	""" Class that represents the data in the usb.ids file
		It reads/parses the file and creates the objects to match
	"""
	
	def __init__(self, fname=None):
		""" Initialize the class.  This includes reading the supplied file
		    and creating/populating as many related objects as needed.
		"""
		self.vendorlist = VendorList()
		self.usbclasslist = USBClassList()
		self.inVendor = 0
		self.inClass = 0
		if fname is not None:
			self.add_data(fname)

	def add_data(self, fname):
		try:
			ufile = open(fname, "rt")
			try:	
				aline = ufile.readline()
				while aline != "":
					# Remove any EOL characters
					while (aline[:-1] in ["\r", "\n"]):
						aline = aline[:-1]

					# Check for a vendor ID line
					m = vendor_re.match(aline)
					if (m):
						self.inVendor = 1
						self.inClass = 0
						self.curr_vendor = VendorID(m.group(1), m.group(2))
						self.vendorlist.addVendor(m.group(1), self.curr_vendor)

					if (self.inVendor):
						# Check for a device ID line
						m = device_re.match(aline)
						if (m):
							self.curr_device = DeviceID(m.group(1), m.group(2))
							self.curr_vendor.addDevice(self.curr_device)
	
						# Check for a interface ID line
						m = iface_re.match(aline)
						if (m):
							self.curr_device.addInterface(InterfaceID(m.group(1), m.group(2)))

					# Check for a USB Class line
					m = usbclass_re.match(aline)
					if (m):
						self.inClass = 1
						self.inVendor = 0
						self.curr_usbclass = USBClass(m.group(1), m.group(2))
						self.usbclasslist.addClass(m.group(1), self.curr_usbclass)
					
					if (self.inClass):
						# Check for a USB SubClass line
						m = usbsubclass_re.match(aline)
						if (m):
							self.curr_usbsubclass = USBClassSubclass(m.group(1), m.group(2))
							self.curr_usbclass.addSubclass(self.curr_usbsubclass)
	
						# Check for a USB Protocol line
						m = usbprotocol_re.match(aline)
						if (m):
							self.curr_usbsubclass.addProtocol(USBClassProtocol(m.group(1), m.group(2)))

					# Get next line (if it exists)
					aline = ufile.readline()
			except IOError:
				# We'll take a pass on it, live with what (if any) data we get
				pass
				
		except IOError:
			print ("Cannot open the USB ID file: %s" % fname)
			raise

		if (ufile):
			ufile.close()

	def lookupdevice(self, vendor, product=None, interface=None):
		return self.vendorlist.getVendorInfo(vendor, product, interface)		

	def lookupclass(self, klass, subclass=None, protocol=None):
		return self.usbclasslist.getClassInfo(klass, subclass, protocol)

	def getVendorList(self):
		""" Return the object representing the list of vendors """
		return self.vendorlist

	def getUSBClassList(self):
		""" Return the object representing the list of USB Classes """
		return self.usbclasslist

###
###  USB VendorID/DeviceID information related classes
###
class VendorID(usbInfoObject):
	""" This class abstracts USB Vendor ID information
		It holds the description, and a list of Device ID's
	"""
	def addDevice(self, device):
		""" Put this device on our list """
		self.addChild(device)

	def getDevice(self, device):
		""" Return the requested device by ID, if we have it """
		return self.getChild(device)

	def getDevices(self):
		""" Return a list of our devices """
		return self.getChildren()

class DeviceID(usbInfoObject):
	""" This class abstracts USB Device ID information	
	It holds the description and a list of the Interface ID's
	"""	
	def addInterface(self, interface):
		""" Put this interface on our list """
		self.addChild(interface)
	
	def getInterface(self, interface):
		""" Return the requested interface by ID, if we have it """
		return self.getChild(interface)

	def getInterfaces(self):
		""" Return a list of our interfaces """
		return self.getChildren()

class InterfaceID(usbInfoObject):
	""" This class abstracts USB Interface information
		It holds the description
	"""
	pass

class VendorList:
	""" This class is responsible for the collection of vendor data
		It allows you to ask for:
		 - vendor info by VendorID
		 - device info by VendorID/DeviceID
		 - interface """
	def __init__(self):
		""" Prepare a dict to handle all of our children vendor objects """
		self.vendorlist = {}

	def addVendor(self, vID, vDesc):
		""" Put this vendor into our dictionary """
		self.vendorlist[int(vID,16)] = vDesc

	def getVendorInfo(self, vID, dID=None, iID=None):
		""" Lookup info for vendor, device, interface - last two are optional """
		# First things first... Get information if available....
		self.vendor = self.device = self.iface = None
		self.vDesc = self.dDesc = self.iDesc = None

		# --- Vendor
		if vID in self.vendorlist:
			self.vendor = self.vendorlist[vID]
			self.vDesc = self.vendor.description

		# --- Device
		if self.vendor:
			self.device = self.vendor.getDevice(dID)
		if self.device:
			self.dDesc = self.device.description

		# --- Interface
		if self.device:
			self.iface = self.device.getInterface(iID)
		if self.iface:
			self.iDesc = self.iface.description

		# Now, decide how we were called, and return appropriately
		if ((dID is None) and (iID is None)):
			return (self.vDesc,)
		elif (iID is None):
			return (self.vDesc, self.dDesc)
		else:
			return (self.vDesc, self.dDesc, self.iDesc)
	
	def getVendorList(self):
		return self.vendorlist.values()


###
###  USB Class information related classes
###
class USBClass(usbInfoObject):
	""" This class abstracts USB Class information
		It holds the description, and a list of Subclasses
	"""
	def addSubclass(self, subclass):
		""" Put this subclass on our list """
		self.addChild(subclass)

	def getSubclass(self, subclass):
		""" Return subclass by ID, if we have it """
		return self.getChild(subclass)

	def getSubclasses(self):
		""" Return a list of our subclasses """
		return self.getChildren()
	

class USBClassSubclass(usbInfoObject):
	""" This class abstracts USB Device SubClass information	
		It holds the description and a list of the protocols
	"""	
	def addProtocol(self, protocol):
		""" Put this protocol on our list """
		self.addChild(protocol)

	def getProtocol(self, protocol):
		""" Return protocol as ID, if we have it """
		return self.getChild(protocol)

	def getProtocols(self):
		""" Return a list of our protocols """
		return self.getChildren()

class USBClassProtocol(usbInfoObject):
	""" This class abstracts USB Interface information
		It holds the description
	"""
	pass


class USBClassList:
	""" This class is responsible for the collection of USB Class data
		It allows you to ask for:
		 - USB Class info by Class ID
		 - USB SubClass info by ClassID/SubclassID
		 - USB Protocol info by ClassID/SubclassID/ProtocolID
	"""
	def __init__(self):
		self.classlist = {}

	def addClass(self, cID, cDesc):
		self.classlist[int(cID, 16)] = cDesc

	def getClassInfo(self, cID, sID=None, pID=None):
		""" Lookup info for class, subclass, protocol - last two are optional """
		# First things first... Get information if available....
		self.usbclass = self.subclass = self.protocol = None
		self.cDesc = self.sDesc = self.pDesc = None

		# --- USB Class
		if cID in self.classlist:
			self.usbclass = self.classlist[cID]
			self.cDesc = self.usbclass.description

		# --- USB Subclass
		if self.usbclass:
			self.subclass = self.usbclass.getSubclass(sID)
		if self.subclass:
			self.sDesc = self.subclass.description

		# --- USB Protocol
		if self.subclass:
			self.protocol = self.subclass.getProtocol(pID)
		if self.protocol:
			self.pDesc = self.protocol.description

		# Now, decide how we were called, and return appropriately
		if ((sID is None) and (pID is None)):
			return (self.cDesc,)
		elif (pID is None):
			return (self.cDesc, self.sDesc)
		else:
			return (self.cDesc, self.sDesc, self.pDesc)

	def getUSBClassList(self):
		return self.classlist.values()



###
###  Interactive testing code
###
if (__name__ == "__main__"):
    import os, guihelper
    def print_vendor_info(USBids):
            # Print out vendor / device / interface info
            vlist = USBids.getVendorList()
            for v in vlist.getVendorList():
                    print ("VENDOR: %s %s" % (v.id, v.description))
                    for d in v.getDevices():
                            print ("\tDEVICE: %s %s" % (d.id, d.description))
                            for i in d.getInterfaces():
                                    print ("\t\tIFACE: %s %s" % (i.id, i.description))
    
    def print_class_info(USBids):
            # Print out class / subclass / protocol
            clist = USBids.getUSBClassList()
            for c in clist.getUSBClassList():
                    print ("CLASS: %s %s" % (c.id, c.description))
                    for s in c.getSubclasses():
                            print ("\tSUBCLASS: %s %s" % (s.id, s.description))
                            for p in s.getProtocols():
                                    print ("\t\tPROTOCOL: %s %s" % (p.id, p.description))	

    myUSBids = usb_ids(os.path.join(guihelper.resourcedirectory,
                                    "usb.ids"))

    # PRINT OUT THE WHOLE TREE AS A TEST CASE
    # print_vendor_info(myUSBids)
    # print_class_info(myUSBids)

    # Our list is now internally decimal, so to lookup/inquire by hex
    # You must convert to decimal before passing your inquiry in...

    # Test lookup for various bits of USB Vendor/Device/Interface information
    print "Inquire on Vendor 1452, Device 518, Iface 1 using various levels of detail:" 
    vlist = myUSBids.getVendorList()
    print vlist.getVendorInfo(1452)
    print vlist.getVendorInfo(1452, 518)
    print vlist.getVendorInfo(1452, 518, 1)
    print
    
    # Test lookup for various bits of USB Class/Subclass/Protocol information
    print "Inquire on Class 8, Subclass 4, Protocol 0 using various levels of detail:" 
    clist = myUSBids.getUSBClassList()
    print clist.getClassInfo(8)
    print clist.getClassInfo(8, 4)
    print clist.getClassInfo(8, 4, 0)
    print

    # For reference, this is how you'd inquire on hex values
    # print vlist.getVendorInfo(int("05ac", 16))
    # print vlist.getVendorInfo(int("05ac", 16), int("0206", 16))
    # print vlist.getVendorInfo(int("05ac", 16), int("0206", 16), int("01", 16))
    # print clist.getClassInfo(int("08", 16))
    # print clist.getClassInfo(int("08", 16), int("04", 16))
    # print clist.getClassInfo(int("08", 16), int("04", 16), int("00", 16))

    # The following are in hex just becuase that way I can visually match them
    # up with the entries in the test.ids file

    # Now, let's test for something that doesn't exist:
    print "Look up something with little detail in Internet file... 1004/6000/(00..02)"
    print vlist.getVendorInfo(int("1004", 16), int("6000", 16), int("00", 16))
    print vlist.getVendorInfo(int("1004", 16), int("6000", 16), int("01", 16))
    print vlist.getVendorInfo(int("1004", 16), int("6000", 16), int("02", 16))
    print

    # Put the data in from our local copy
    print "Add in our test data to override internet data"
    myUSBids.add_data(os.path.join(guihelper.resourcedirectory,
                                   "test.ids"))
    print
    
    # Now, it should be there
    print "Check it again..."
    print vlist.getVendorInfo(int("1004", 16), int("6000", 16), int("00", 16))
    print vlist.getVendorInfo(int("1004", 16), int("6000", 16), int("01", 16))
    print vlist.getVendorInfo(int("1004", 16), int("6000", 16), int("02", 16))
