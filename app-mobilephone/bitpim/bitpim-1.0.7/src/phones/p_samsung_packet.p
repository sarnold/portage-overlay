### BITPIM
###
### Copyright (C) 2005 Stephen Wood <sawecw@users.sf.net>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: p_samsung_packet.p 4470 2007-11-28 04:27:52Z djpham $

%{

"""Various descriptions of data specific to Sanyo phones"""

from prototypes import *

# We use LSB for all integer like fields

UINT=UINTlsb
BOOL=BOOLlsb

NUMCALENDAREVENTS=70
NUMTODOENTRIES=9
NUMMEMOENTRIES=9

DEFAULT_RINGTONE=20
DEFAULT_WALLPAPER=20

 %}

PACKET phonenumber:
    * CSVSTRING {'quotechar': None, 'default': ""} +number
    * CSVINT {'default': 0} +secret

PACKET phonebookslotrequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PBOKR='} +command
    * CSVINT {'terminator': None} +slot "Internal Slot"

PACKET phonebooksloterase:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PBOKW='} +command
    * CSVINT {'terminator': None} +slot "Internal Slot"

#PACKET phonebookslotupdaterequest:
#    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PBOKW=0,'} +command
#    * pbentry entry
    
PACKET phonebookslotupdateresponse:
    * UNKNOWN pad
    
PACKET groupnamerequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PBGRR='} +command
    * CSVINT {'terminator': None} +gid "Group #"

PACKET groupnamesetrequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PBGRW='} +command
    * CSVINT +gid "Group #"
    * CSVSTRING +groupname
    * CSVINT {'terminator': None, 'default': 0} +ringtone "Ringtone assignment"
    
PACKET groupnamesetrequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PBGRW='} +command
    * CSVINT +gid "Group #"
    * CSVSTRING +groupname
    * CSVINT {'terminator': None, 'default': 0} +ringtone "Ringtone assignment"
    
PACKET eventrequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PISHR='} +command
    * CSVINT {'terminator': None} +slot

PACKET eventresponse:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'constant': '#PISHR:'} command
    * CSVINT slot
    * CSVTIME start
    * CSVTIME end
    * CSVTIME timestamp
    * CSVINT alarm "0: 10 minutes, 1: 30 minutes, 2: 60 minutes, 3: No Alarm, 4: On Time"
    * CSVSTRING {'quotechar': None} dunno
    * CSVSTRING {'terminator': None} eventname

PACKET eventupdaterequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PISHW='} +command
    * CSVINT slot
    * CSVTIME start
    * CSVTIME end
    * CSVTIME timestamp
    * CSVINT alarm "0: 10 minutes, 1: 30 minutes, 2: 60 minutes, 3: No Alarm, 4: On Time"
    * CSVSTRING {'terminator': None} eventname
    
PACKET eventsloterase:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PISHW='} +command
    * CSVINT {'terminator': None} +slot

PACKET eventupdateresponse:
    * UNKNOWN pad

PACKET todorequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PITDR='} +command
    * CSVINT {'terminator': None} +slot

PACKET todoresponse:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'default': '#PITDR:'} command
    * CSVINT slot
    * CSVINT priority
    * CSVTIME duedate
    * CSVTIME timestamp
    * CSVSTRING {'quotechar': None} status
    * CSVSTRING {'terminator': None} subject
    
PACKET todoupdaterequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PITDW='} +command
    * CSVINT slot
    * CSVINT priority
    * CSVTIME duedate 
    * CSVTIME timestamp
    * CSVSTRING {'terminator': None} subject

PACKET todoerase:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PITDW='} +command
    * CSVINT {'terminator': None} slot

PACKET todoupdateresponse:
    * UNKNOWN pad

PACKET memorequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PIMMR='} +command
    * CSVINT {'terminator': None} +slot

PACKET memoresponse:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'default': '#PIMMR:'} command
    * CSVINT slot
    * CSVTIME timestamp
    * CSVSTRING {'quotechar': None} status
    * CSVSTRING {'terminator': None} text
    
PACKET memoupdaterequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PIMMW='} +command
    * CSVINT slot
    * CSVTIME timestamp
    * CSVSTRING {'terminator': None} text

PACKET memoerase:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '#PIMMW='} +command
    * CSVINT {'terminator': None} slot

PACKET memoupdateresponse:
    * UNKNOWN pad

PACKET esnrequest:
    * CSVSTRING {'quotechar': None, 'terminator': None, 'default': '+GSN'} +command

PACKET esnresponse:
    * CSVSTRING {'quotechar': None, 'terminator': ord(' '), 'default': '+GSN'} command
    * CSVSTRING {'quotechar': None, 'terminator': None} esn

#at#psrmr=?
#PSRMR: (0-93)
 
#OK
#at#psrmr=0
#PSRMR: 0,0,1,20031214T214934,"shortmail@oneboxmail.bulk.sprint: Short Mail: New Short Mail. Select }Go} to read it}-}*http://smwl.uc.sprintpcs.com/sml/wap.do?alert=true",
 
#OK
#at#psrmr=1
#PSRMR: 1,0,1,20031205T091836,"To avoid service interruption, please call Sprint PCS at 800-808-1336.",
 
PACKET manufacturerreq:
    * CSVSTRING { 'quotechar': None,
                  'terminator': None,
                  'default': '+GMI' } +command
PACKET manufacturerresp:
    * CSVSTRING { 'quotechar': None,
                  'terminator': ord(' ') } command
    * STRING {'terminator': None } manufacturer

PACKET modelreq:
    * STRING { 'terminator': None,
               'default': '+GMM' } +command
PACKET modelresp:
    * STRING { 'terminator': ord(' ') } command
    * STRING { 'terminator': None } model

PACKET batterylevelreq:
    * STRING { 'terminator': None,
               'default':'+CBC?' } +command
PACKET batterylevelresp:
    * STRING { 'terminator': ord(' ') } command
    * CSVINT zero
    * CSVINT { 'terminator': None } level
    %{
    def _levelstr(self):
        return '%d%%'%self.level
    levelstr=property(fget=_levelstr)
    %}
