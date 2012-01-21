### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_othercdma.py 2572 2005-10-21 06:07:08Z skyjunky $

"""Communicate with an unsupported Brew phone"""

import com_phone
import com_brew
import commport

class Phone(com_phone.Phone, com_brew.BrewProtocol):
    "Talk to an unsupported CDMA phone"

    desc="Other CDMA Phone"

    protocolclass=None
    
    def __init__(self, logtarget, commport):
        com_phone.Phone.__init__(self, logtarget, commport)
        com_brew.BrewProtocol.__init__(self)

class Profile(com_phone.Profile):
    pass
