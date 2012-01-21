%module libusb

%{

#include "usb.h"

// deal with data being returned
int usb_bulk_read_wrapped(usb_dev_handle *dev, int ep, char *bytesoutbuffer, int *bytesoutbuffersize, int timeout)
 {
   int res;
   Py_BEGIN_ALLOW_THREADS
   res=usb_bulk_read(dev, ep, bytesoutbuffer, *bytesoutbuffersize, timeout);
   Py_END_ALLOW_THREADS
   if (res<=0)
     *bytesoutbuffersize=0;
   else
     *bytesoutbuffersize=res;
   return res;
 }

int usb_interrupt_read_wrapped(usb_dev_handle *dev, int ep, char *bytesoutbuffer, int *bytesoutbuffersize, int timeout)
 {
   int res;
   Py_BEGIN_ALLOW_THREADS
   res=usb_interrupt_read(dev, ep, bytesoutbuffer, *bytesoutbuffersize, timeout);
   Py_END_ALLOW_THREADS
   if (res<=0)
     *bytesoutbuffersize=0;
   else
     *bytesoutbuffersize=res;
   return res;
 }

// access a pointer as an array
struct usb_interface *usb_interface_index(struct usb_interface *iface, unsigned index) 
  { return iface+index; }
struct usb_endpoint_descriptor *usb_endpoint_descriptor_index(struct usb_endpoint_descriptor *ep, unsigned index) 
  { return ep+index; }
struct usb_interface_descriptor *usb_interface_descriptor_index(struct usb_interface_descriptor *iface, unsigned index)
  { return iface+index; }

%}


// we don't modify any fields
%immutable;

// cstring manipulation
%include cstring.i

// in usb_get_string{,_simple}
%cstring_output_maxsize(char *buf, size_t buflen);

// usb_bulk_write - binary string with length
%apply (char *STRING, int LENGTH) { (char *bytes, int size) }

// usb_interrupt_write - binary string with length
%apply (char *STRING, int LENGTH) { (char *bytes, int size) }

// these types occur in Linux and SWIG doesn't know they are ints unless we tell
typedef unsigned short u_int16_t;
typedef unsigned char u_int8_t;

// Debian's usb.h now uses these type names instead for ANSI compliance,
// but SWIG doesn't automatically recognize them either.
typedef unsigned short uint16_t;
typedef unsigned char uint8_t;

#define __attribute__(x)

%include usb.h

// various wrappers and convenience functions
// these help treat pointers as arrays
struct usb_interface *usb_interface_index(struct usb_interface *iface, unsigned index);
struct usb_endpoint_descriptor *usb_endpoint_descriptor_index(struct usb_endpoint_descriptor *ep, unsigned index);
struct usb_interface_descriptor *usb_interface_descriptor_index(struct usb_interface_descriptor *iface, unsigned index);

// a wrapper so that we can deal with buffer length issues
%cstring_output_withsize(char *bytesoutbuffer, int *bytesoutbuffersize);
int usb_bulk_read_wrapped(struct usb_dev_handle *dev, int ep, char *bytesoutbuffer, int *bytesoutbuffersize, int timeout);
int usb_interrupt_read_wrapped(struct usb_dev_handle *dev, int ep, char *bytesoutbuffer, int *bytesoutbuffersize, int timeout);
