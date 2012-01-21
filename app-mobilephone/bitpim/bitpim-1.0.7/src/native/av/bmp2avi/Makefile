### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@netzero.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: Makefile 3200 2006-05-05 07:10:08Z rogerb $

# There used to be a fairly elegant makefile.  Replaced with something
# more trivial but easier to use while packaging.  Note that we deliberately
# do not specify $CXX, $LDFLAGS etc as the distro will provide them

SRC=avi_file.cxx bmp_file.cxx b2a.cxx

bmp2avi.lbin bmp2avi.mbin bmp2avi.exe: $(SRC)
	$(CXX) $(EXTRADEFINES) -O2 -o $@ $(SRC)

