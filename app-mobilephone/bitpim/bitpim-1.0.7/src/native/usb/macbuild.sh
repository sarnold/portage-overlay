PYTHONVER=python2.5
INCLUDEDIR=/System/Library/Frameworks/Python.framework/Versions/2.5/include/$PYTHONVER

swig -version 2>&1 | grep Version

swig -python `libusb-config --cflags` libusb.i

gcc -Wall -O2  -bundle -undefined suppress -flat_namespace -I $INCLUDEDIR -I /usr/local/include -o _libusb.so libusb_wrap.c `libusb-config --libs` `libusb-config --cflags` -framework Python -arch i386

