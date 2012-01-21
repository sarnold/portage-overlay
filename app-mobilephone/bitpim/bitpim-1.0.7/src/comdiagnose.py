#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: comdiagnose.py 4656 2008-08-02 15:57:20Z hjelmn $

"""Generate opinions on the attached com devices"""

# Standard modules
import re
import sys

# My modules
import comscan
import usbscan
import bitflingscan

def diagnose(portlist, phonemodule):
    """Returns data suitable for use in com port settings dialog

    @param portlist: A list of ports as returned by L{comscan.comscan}()
    @return: A list of tuples (whattodisplay, portselected, htmldiagnosis)
    """
    res=[]
    # we sort into 3 lists
    # available
    # not available but active
    # the rest
    available=[]
    bfavailable=[]
    bfrest=[]
    notavailablebutactive=[]
    therest=[]
    for port in portlist:
        if port.has_key("available") and port["available"]:
            if port.has_key("BitFling"):
                bfavailable.append(port)
            else:
                available.append(port)
            continue
        if not port.has_key("BitFling") and (port.has_key("available") and port.has_key("active") and port["active"]):
            notavailablebutactive.append(port)
            continue
        if port.has_key("BitFling"):
            bfrest.append(port)
        else:
            therest.append(port)

    if len(available):
        whattodisplay="===== Available Ports ===== "
        portselected=None
        htmldiagnosis="<p>These ports are open and can be selected"
        res.append( (whattodisplay, portselected, htmldiagnosis) )
        for port in available:
            likely=islikelyport(port, phonemodule)
            whattodisplay=port['description']
            if likely:
                whattodisplay="(*) "+whattodisplay
            portselected=port['name']
            if likely:
                htmldiagnosis="<p>This port is likely to be your phone.  The port is available and can be selected.<p>"+genhtml(port)
            else:
                htmldiagnosis="<p>This port is available and can be selected.<p>"+genhtml(port)
            res.append( (whattodisplay, portselected, htmldiagnosis) )

    if len(notavailablebutactive):
        whattodisplay="===== Ports not available ====="
        portselected=None
        htmldiagnosis="<p>These ports are active, but cannot be used because they are in use by another program or device driver, you do not have permissions to access them, or a device driver is required."
        res.append( (whattodisplay, portselected, htmldiagnosis) )
        for port in notavailablebutactive:
            whattodisplay=port['description']
            portselected=port['name']
            htmldiagnosis="<p>This port is active but not available for use.<p>"+genhtml(port)
            res.append( (whattodisplay, portselected, htmldiagnosis) )
        
    if len(therest):
        whattodisplay="===== Inoperable Ports ====="
        portselected=None
        htmldiagnosis="""<p>These ports are known to your operating system, but cannot be used.  
        This may be because the device is not plugged in (such as on a USB to serial cable) or because 
        you don't have sufficient permissions to use them."""
        res.append( (whattodisplay, portselected, htmldiagnosis) )
        for port in therest:
            whattodisplay=port['description']
            portselected=port['name']
            htmldiagnosis="""<p>This port should not be selected.  If you believe it is the correct
            port, you should cause it to become available such as by plugging in the cable or ensuring
            you have correct permissions.  Press refresh once you have done so and it should be listed
            under available. Note that the name may change as it becomes available.<p>"""+genhtml(port)
            res.append( (whattodisplay, portselected, htmldiagnosis) )

    if len(bfavailable):
        whattodisplay="===== BitFling Available Ports ===== "
        portselected=None
        htmldiagnosis="<p>These BitFling ports are open and can be selected"
        res.append( (whattodisplay, portselected, htmldiagnosis) )
        for port in bfavailable:
            likely=islikelyport(port, phonemodule)
            whattodisplay=port['description']
            if likely:
                whattodisplay="(*) "+whattodisplay
            portselected=port['name']
            if likely:
                htmldiagnosis="<p>This port is likely to be your phone.  The port is available and can be selected.<p>"+genhtml(port)
            else:
                htmldiagnosis="<p>This port is available and can be selected.<p>"+genhtml(port)
            res.append( (whattodisplay, portselected, htmldiagnosis) )

    if len(bfrest):
        whattodisplay="===== BitFling Other Ports ===== "
        portselected=None
        htmldiagnosis="<p>These BitFling ports exist but are not available"
        res.append( (whattodisplay, portselected, htmldiagnosis) )
        for port in bfrest:
            likely=islikelyport(port, phonemodule)
            whattodisplay=port['description']
            if likely:
                whattodisplay="(*) "+whattodisplay
            portselected=port['name']
            if likely:
                htmldiagnosis="<p>This port is likely to be your phone.  The port is available and can be selected.<p>"+genhtml(port)
            else:
                htmldiagnosis="<p>This port is available and can be selected.<p>"+genhtml(port)
            res.append( (whattodisplay, portselected, htmldiagnosis) )


    return res

def htmlify(text):
    text=re.sub("&", "&amp;", text)
    text=re.sub("<", "&lt;", text)
    text=re.sub(">", "&gt;", text)
    return text

def genhtml(port):
    """Returns nice html describing a port dict"""
    sfont='<font size="-1">'
    efont='</font>'
    res='<table width="100%"><tr><th width="20%">Property<th width="40%">Value<th width="40%">Description</tr>\n'
    keys=port.keys()
    keys.sort()
    for k in keys:
        # property
        if k.startswith('usb-') and not k.endswith('string'):
            # ignore these
            continue
        res+='<tr><td valign="top">'+sfont+k+efont+'</td><td valign="top">\n'
        # value
        if k=='active' or k=='available':
            if port[k]:
                res+=sfont+"True"+efont
            else:
                res+=sfont+"False"+efont
        elif k=='driverdate':
            # XML-RPC converts tuples to lists, so we have to convert back again here
            res+=sfont+("%d-%d-%d" % tuple(port[k]))+efont
        elif k=='driverstatus':
            res+=sfont+`port[k]`+efont # should print it nicer at some point
        else:
            if isinstance(port[k], type("")):
                res+=sfont+htmlify(port[k])+efont
            else:
                res+=sfont+`port[k]`+efont
        res+='</td><td valign="top">'
        # description
        if k=='name':
            res+=sfont+"This is the name the port is known to your operating system as"+efont
        elif k=='available':
            if port[k]:
                res+=sfont+"It was possible to open this port"+efont
            else:
                res+=sfont+"It was not possible to open this port"+efont
        elif k=='active':
            if port[k]:
                res+=sfont+"Your operating system shows this driver and port is correctly configured and a device attached"+efont
            else:
                res+=sfont+"This driver/port combination is not currently running"+efont
        elif k=='driverstatus':
            res+=sfont+"""This is low level detail.  If problem is non-zero then you need to look in the
            control panel for an explanation as to why this driver/device is not working."""+efont
        elif k=='hardwareinstance':
            res+=sfont+"""This is how the device is named internally.  For example USB devices include
            the vendor (VID) and product (PID) identities"""+efont
        elif k=="libusb":
            res+=sfont+"""This indicates if the usb library is in use to access this device.  Operating system
            device drivers (if any) are bypassed when BitPim talks to the device"""+efont
        elif k=="driver-required":
            res+=sfont+"""This indicates if you must use a device driver, not direct USB access"""+efont
        elif k=="BitFling":
            res+=sfont+"""This indicates that the port is being accessed from a remote machine via BitFling,"""+efont
        elif k=="protocol":
            res+=sfont+"""This is the protocol the USB device claims to speak"""+efont
        elif k=="class":
            if port[k]=="serial":
                res+=sfont+"""This is a serial connection"""+efont
            elif port[k]=="modem":
                res+=sfont+"""This is a modem connection"""+efont
            else:
                res+=sfont+"""The port type (serial, modem etc)"""+efont
        elif k=='PID':
            res+=sfont+'Product ID'+efont
        elif k=='VID':
            res+=sfont+'Vendor ID'+efont
        else:
            res+="&nbsp;"

        # tail it
        res+="</td></tr>\n"

    res+="\n</table>"

    return res

def islikelyport(port, phonemodule):
    return islikelyportscore(port, phonemodule)>=0

def islikelyportscore(port, phonemodule):
    """Returns a port score.

    @return: -1 if no match, 0 best match, 1 next etc
    """

    usbids=phonemodule.Profile.usbids
    deviceclasses=phonemodule.Profile.deviceclasses

    # it must be the right class
    if port.has_key("class") and port["class"] not in deviceclasses:
        return -1

    score=0
    # check the usbids
    for vid,pid,iface in usbids:
        score+=1
        if port.has_key("libusb"):
            if port['usb-vendor#']==vid and \
                   port['usb-product#']==pid and \
                   port['usb-interface#']==iface:
                return score
        if port.has_key('hardwareinstance'):
            v=port['hardwareinstance'].lower()
            str="vid_%04x&pid_%04x" % (vid,pid)
            if v.find(str)>=0:
                return score

    # LG phones generall have ports named cu.name-BTDIAG-1 or cu.name-SerialPort-1 where name is the bluetooth id of the phone
    if sys.platform=='darwin' and (port['name'].lower().find('btdiag') > 0 or port['name'].lower().find('serialport') > 0):
        return score

    score+=10
    # did it have a usb id that didn't match?
    if port.has_key("libusb"):
        return -1

    # did the hardware instance have usb info?
    if port.has_key("hardwareinstance") and \
       re.search("vid_([0-9a-f]){4}&pid_([0-9a-f]){4}", port['hardwareinstance'], re.I) is not None:
        return -1

    # are we on non-windows platform?  if so, just be happy if 'usb' is in the name or the driver name
    if sys.platform!='win32' and ( \
        port['name'].lower().find('usb')>0 or port.get("driver","").lower().find('usb')>=0):
        return score

    # if we are on windows check to see if this phone supports bluetooth as we may have a bluetooth comport 
    # we check that the bluetooth device contains the manufacturers ID for the phone, this filters
    # other bluetooth devices from the search, on windows the 'hardwareinstance' contains BTHENUM indicating 
    # a bluetooth device and the manufacturer's ID
    if sys.platform=='win32' and (getattr(phonemodule.Profile, 'bluetooth_mfg_id', 0) != 0) and \
        port['hardwareinstance'].find('BTHENUM\\')==0 and \
        port['hardwareinstance'].find(getattr(phonemodule.Profile, 'bluetooth_mfg_id', 'XXX'))>0:
        return score

    # ok, not then
    return -1
            
def autoguessports(phonemodule):
    """Returns a list of ports (most likely first) for finding the phone on"""
    # this function also demonsrates the use of list comprehensions :-)
    res=[]
    # we only care about available ports
    ports=[(islikelyportscore(port, phonemodule), port) for port in comscan.comscan()+usbscan.usbscan()+bitflingscan.flinger.scan() if port['available']]
    # sort on score
    ports.sort()
    # return all ones with score >=0
    return [ (port['name'], port) for score,port in ports if score>=0]




if __name__=='__main__':
    import common
    print autoguessports(common.importas("phones.com_lgvx4400"))
