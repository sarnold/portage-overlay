### BITPIM
###
### Copyright (C) 2005 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_sanyo3100.py 4528 2007-12-26 05:51:17Z sawecw $

"""Talk to the Sanyo SCP-3100 cell phone"""
# standard modules
import re
import time
import sha

# my modules
import common
import com_sanyo8300
import p_brew
import p_sanyo8300
import p_sanyo3100
import commport
import com_brew
import com_phone
import com_sanyo
import com_sanyomedia
import com_sanyonewer
import prototypes
import bpcalendar

numbertypetab=( 'cell', 'home', 'office', 'pager',
                    'fax', 'data', 'none' )

class Phone(com_sanyo8300.Phone):
    "Talk to the Sanyo PM3100 cell phone"

    desc="SCP3100"
# WOrking directories 1,2,4
    FIRST_MEDIA_DIRECTORY=1
    LAST_MEDIA_DIRECTORY=2

    imagelocations=(
        # offset, directory #, indexflag, type, maximumentries
        )    

    protocolclass=p_sanyo3100
    serialsname='scp3100'

    builtinringtones=( 'None', 'Vibrate', '', '', '', '', '', '', '', 
                       'Tone 1', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5',
                       'Tone 6', 'Tone 7', 'Tone 8',
                       '', '', '', '', '',
                       '', '', '',
                       '', '', '', '',
                       'Hungarian Dance No.5', 'Asian Jingle',
                       'Ska Big Band', 'Habanera', 'Clair de Lune',
                       'Nocturne', 'Techno Beat', 'Jazz Melody','','','','','','','','','','','','','','','','','','','Ringer & Voice')

    calendar_defaultringtone=4
    calendar_defaultcaringtone=4

    def __init__(self, logtarget, commport):
        com_sanyo8300.Phone.__init__(self, logtarget, commport)
        self.mode=self.MODENONE
        self.numbertypetab=numbertypetab

    # Phone Detection-----------------------------------------------------------
    def is_mode_brew(self):
        # Borrowed from the VX4400
        req=self.protocolclass.firmwarerequest()
        respc=p_brew.testing0cresponse
        for baud in 0, 38400, 115200:
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            try:
                self.sendbrewcommand(req, respc, callsetmode=False)
                return True
            except com_phone.modeignoreerrortypes:
                pass
        return False
    def check_my_phone(self, res):
        # check if this is an 6600
        try:
            _req=self.protocolclass.sanyofirmwarerequest()
            _resp=self.sendbrewcommand(_req, self.protocolclass.sanyofirmwareresponse)
            if _resp.phonemodel[:len(self.detected_model)]==self.detected_model:
                # yup, this's it!
                res['model']=self.my_model
                res['manufacturer']=self.my_manufacturer
                res['esn']=self.get_esn()
        except:
            if __debug__:
                raise

    @classmethod
    def detectphone(_, coms, likely_ports, res, _module, _log):
        if not likely_ports:
            # cannot detect any likely ports
            return None
        for port in likely_ports:
            if not res.has_key(port):
                res[port]={ 'mode_modem': None, 'mode_brew': None,
                            'manufacturer': None, 'model': None,
                            'firmware_version': None, 'esn': None,
                            'firmwareresponse': None }
            try:
                if res[port]['mode_brew']==False or \
                        res[port]['model']:
                    # either phone is not in BREW, or a model has already
                    # been found, not much we can do now
                    continue
                p=_module.Phone(_log, commport.CommConnection(_log, port, timeout=1))
                if res[port]['mode_brew'] is None:
                    res[port]['mode_brew']=p.is_mode_brew()
                if res[port]['mode_brew']:
                    p.check_my_phone(res[port])
                p.comm.close()
            except com_brew.BrewBadBrewCommandException:
                pass
            except:
                if __debug__:
                    raise

    my_model='SCP3100'
    detected_model='SCP-3100/US'
    my_manufacturer='SANYO'

parentprofile=com_sanyo8300.Profile
class Profile(parentprofile):

    protocolclass=Phone.protocolclass
    serialsname=Phone.serialsname
    phone_manufacturer=Phone.my_manufacturer
    phone_model=Phone.my_model

    _supportedsyncs=(
        ('phonebook', 'read', None),  # all phonebook reading
        ('calendar', 'read', None),   # all calendar reading
        ('phonebook', 'write', 'OVERWRITE'),  # only overwriting phonebook
        ('calendar', 'write', 'OVERWRITE'),   # only overwriting calendar
        ('wallpaper', 'read', None),  # all wallpaper reading
        ('ringtone', 'read', None),   # all ringtone reading
        ('call_history', 'read', None),# all call history list reading
        ('sms', 'read', None), # Read sms messages
        ('todo', 'read', None), # Read todos
    )

    # which usb ids correspond to us
    usbids=( ( 0x0474, 0x071F, 1),)  # VID=Sanyo,
    deviceclasses=("serial",)
    
    def __init__(self):
        parentprofile.__init__(self)
        com_sanyonewer.Profile.__init__(self)
        self.numbertypetab=numbertypetab

