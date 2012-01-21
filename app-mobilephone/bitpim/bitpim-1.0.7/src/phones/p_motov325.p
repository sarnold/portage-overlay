### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_motov325.p 4541 2008-01-04 03:41:51Z djpham $

%{

"""Various descriptions of data specific to Motorola V325 phones"""

from prototypes import *
from prototypes_moto import *
from p_etsi import *
from p_moto import *
from p_motov3m import *

import fnmatch

# We use LSB for all integer like fields
UINT=UINTlsb
BOOL=BOOLlsb

PB_TOTAL_ENTRIES=500
PB_RANGE=xrange(1,PB_TOTAL_ENTRIES+1)

MOTO_SHARED_PATH='motorola/shared'

%}
