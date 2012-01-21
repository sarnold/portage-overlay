### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: com_phone.py 4768 2009-11-06 02:17:29Z hjelmn $


"""Generic phone stuff that all models inherit from"""


import common
import commport
import copy
import field_color
import re
import sys
import time
import prototypes


# when trying to setmode, we ignore various exception types
# since the types are platform specific (eg on windows we get pywintypes.error)
# so we have to construct the list here of which ones we ignore
modeignoreerrortypes=[ commport.CommTimeout,common.CommsDeviceNeedsAttention ]
try:
    import pywintypes
    modeignoreerrortypes.append(pywintypes.error)
except:
    pass

# has to be tuple or it doesn't work
modeignoreerrortypes=tuple(modeignoreerrortypes) 


class Phone(object):
    """Base class for all phones"""
    
    MODENONE="modenone"  # not talked to yet
    MODEMODEM="modemodem" # modem mode

    desc="Someone forget to set desc in derived class"

    def __init__(self, logtarget, commport):
        self.logtarget=logtarget
        self.comm=commport
        self.mode=self.MODENONE
        self.__msg=None

    def close(self):
        self.comm.close()
        self.comm=None

    def log(self, str):
        "Log a message"
        if self.logtarget:
            self.logtarget.log("%s: %s" % (self.desc, str))

    def logdata(self, str, data, klass=None):
        "Log some data with option data object/class for the analyser"
        if self.logtarget:
            self.logtarget.logdata("%s: %s" % (self.desc, str), data, klass)

    def alert(self, message, wait):
        """Raises an alert in the main thread

        @param message: The message to display
        @param wait:  Should this function block until the user confirms the message
        """
        assert not wait
        assert self.logtarget
        self.logtarget.log("<!= alert wait=%s =!>%s: %s" % (`wait`, self.desc, message))

    def progress(self, pos, max, desc):
        "Update the progress meter"
        if self.logtarget:
            self.logtarget.progress(pos, max, desc)

    def raisecommsdnaexception(self, str):
        "Raise a comms DeviceNeedsAttention Exception"
        self.mode=self.MODENONE
        self.comm.shouldloop=True
        raise common.CommsDeviceNeedsAttention( "The phone is not responding while "+str+".\n\nSee the help for troubleshooting tips", self.desc+" on "+self.comm.port)

    def raisecommsexception(self, str, klass):
        self.mode=self.MODENONE
        raise klass(str, self.desc+" on "+self.comm.port)

    def setmode(self, desiredmode):
        "Ensure the phone is in the right mode"
        if self.mode==desiredmode: return

        strmode=None
        strdesiredmode=None
        for v in dir(self):
            if len(v)>len('MODE') and v[:4]=='MODE':
                if self.mode==getattr(self, v):
                    strmode=v[4:]
                if desiredmode==getattr(self,v):
                    strdesiredmode=v[4:]
        if strmode is None:
            raise Exception("No mode for %s" %(self.mode,))
        if strdesiredmode is None:
            raise Exception("No desired mode for %s" %(desiredmode,))
        strmode=strmode.lower()
        strdesiredmode=strdesiredmode.lower()

        for func in ( '_setmode%sto%s' % (strmode, strdesiredmode),
                        '_setmode%s' % (strdesiredmode,)):
            if hasattr(self,func):
                try:
                    res=getattr(self, func)()
                except modeignoreerrortypes:
                    res=False
                if res: # mode changed!
                    self.mode=desiredmode
                    self.log("Now in "+strdesiredmode+" mode")
                    return

        # failed
        self.mode=self.MODENONE
        while self.comm.IsAuto():
            self.comm.NextAutoPort()
            return self.setmode(desiredmode)
        self.raisecommsdnaexception("transitioning mode from %s to %s" \
                                 % (strmode, strdesiredmode))
        

    def _setmodemodem(self):
        for baud in (0, 115200, 38400, 19200, 230400):
            if baud:
                if not self.comm.setbaudrate(baud):
                    continue
            self.comm.write("AT\r\n")
            try:
                self.comm.readsome()
                return True
            except modeignoreerrortypes:
                pass
        return False

    def readobject(self, filename, object_class, logtitle=None,
                   uselocalfs=False):
        """Read the specified filename and bind it to the object class"""
        if uselocalfs:
            self.log('Reading local file: %s'%filename)
            _buf=prototypes.buffer(file(filename, 'rb').read())
        else:
            _buf=prototypes.buffer(self.getfilecontents(filename))
        _obj=object_class()
        _obj.readfrombuffer(_buf, logtitle=logtitle)
        return _obj

    def writeobject(self, filename, obj, logtitle=None,
                    uselocalfs=False):
        """Writhe the object into the file"""
        _buf=prototypes.buffer()
        obj.writetobuffer(_buf, logtitle=logtitle)
        if uselocalfs:
            file(filename, 'wb').write(_buf.getvalue())
        else:
            self.writefile(filename, _buf.getvalue())

    getmemo=NotImplemented
    gettodo=NotImplemented
    getsms=NotImplemented
    getcallhistory=NotImplemented
    getplaylist=NotImplemented
    gett9db=NotImplemented

class Profile(object):

    BP_Calendar_Version=2

    WALLPAPER_WIDTH=100
    WALLPAPER_HEIGHT=100
    MAX_WALLPAPER_BASENAME_LENGTH=64
    WALLPAPER_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ."
    WALLPAPER_CONVERT_FORMAT="bmp"

    MAX_RINGTONE_BASENAME_LENGTH=64
    RINGTONE_FILENAME_CHARS="abcdefghijklmnopqrstuvwxyz0123456789 ."
    DIALSTRING_CHARS="[^0-9PT#*]"

    field_color_data=field_color.default_field_info
    # delay auto-detection when the phone is plugged in (in seconds)
    autodetect_delay=0

    # delay in rebooting the phone after a send data and delay between offline and reboot in seconds.
    reboot_delay=0

    # which usb ids correspond to us
    usbids=( 
        )
    # which device classes we are.
    deviceclasses=("modem", "serial")

    def __init__(self):
        pass

    _supportedsyncs=(
        )

    def SyncQuery(self, source, action, actiontype):
        if actiontype=='EXCLUSIVE':
            # Check for exclusive, shoud not be masked by None
            return (source, action, actiontype) in self._supportedsyncs
        else:
            return (source, action, actiontype) in self._supportedsyncs or \
                   (source, action, None) in self._supportedsyncs

    # fill in the list of ringtone/sound origins on your phone
    ringtoneorigins=()
    #e.g.
    #ringtoneorigins=('ringers', 'sounds')

    # ringtone origins that are not available for the contact assignment
    excluded_ringtone_origins=()

    # wallpaper origins that are not available for the contact assignment
    excluded_wallpaper_origins=('video',)

    # fill in your own image origins using these
    stockimageorigins={
        "images": {'meta-help': 'General images'},
        "mms": {'meta-help': 'Multimedia Messages'},
        "drm": {'meta-help': 'DRM protected images'},
        "camera": {'meta-help': 'Camera images'},
        "camera-fullsize": {'meta-help': 'Fullsize camera images'},
        "video": {'meta-help': 'Video clips'},
        "images(sd)": {'meta-help': 'General images stored on removable media'},
        "video(sd)": {'meta-help': 'Video clips stored on removable media'},
        "picture ids": {'meta-help': 'Images used for contact/group Picture ID'},
        }

    stockimagetargets={
        # You need to override in your GetTargetsForImageOrigin function and update
        # for ImgFileInfo fields
        "wallpaper": {'meta-help': 'Display as wallpaper'},
        "pictureid": {'meta-help': 'Display as picture id for a caller'},
        "outsidelcd": {'meta-help': 'Display on outside screen'},
        "fullscreen": {'meta-help': 'Fullscreen such as startup screen'},
        }


    # Override in derived class - use this template.  Avoid defining new origins -
    # instead add them to the stock list and use that.  That will ensure the
    # same string and description are used for all phones.
    imageorigins={}
    imageorigins.update(common.getkv(stockimageorigins, "images"))
    imageorigins.update(common.getkv(stockimageorigins, "mms"))
    imageorigins.update(common.getkv(stockimageorigins, "camera"))
    imageorigins["<developerneedstoupdate>"]={'meta-help': "The developer needs to update this phone profile"}

    def GetImageOrigins(self):
        # Note: only return origins that you can write back to the phone
        return self.imageorigins

    def GetTargetsForImageOrigin(self, origin):
        if False:
            # this is how you should do it in your derived class.  The update dictionary
            # fields must correspond to what fileinfo.ImgFileInfo uses.  The information
            # is used to save the new file out.
            targets={}
            targets.update(common.getkv(self.stockimagetargets, "wallpaper",
                                      {'width': 77, 'height': 177, 'format': "BMP"}))
            targets.update(common.getkv(self.stockimagetargets, "outsidelcd",
                                      {'width': 77, 'height': 77, 'format': "JPEG"}))
            return targets
        # this code is here to work with the old way we used to do things
        convert_format_map={'bmp': 'BMP',
                            'jpg': 'JPEG',
                            'png': 'PNG'}
        return common.getkv(self.stockimagetargets, "wallpaper",
                                      {'width': self.WALLPAPER_WIDTH,
                                       'height': self.WALLPAPER_HEIGHT,
                                       'format': convert_format_map[self.WALLPAPER_CONVERT_FORMAT]})
               
        

    def QueryAudio(self, origin, currentextension, audiofileinfo):
        """Query for MP3 file support

        Raise an exception if you cannot support the ringtone or any conversion of
        it.

        @param audiofileinfo: A L{fileinfo.AudioFileInfo} object specifying file's audio properties
        @param currentextension: The extension currently used by the file
        
        @return:  ("file extension", audiofile object).  The file extension
                  (excluding the leading dot) to make the file use.  The audiofile
                  object can be what was passed in unaltered meaning the file is
                  fine as is, or make a new one to specify how the file should
                  be converted.  Note there is a MAXSIZE attribute if you need
                  to limit file size.
        """
        # default implementation leaves file unaltered
        return (currentextension, audiofileinfo)

    def phonize(self, str):
        """Convert the phone number into something the phone understands
        uses DIALSTRING_CHARS to compare phone number with and strips
        all other characters from the string
        """
        return re.sub(self.DIALSTRING_CHARS, "", str)


class NoFilesystem:

    def __raisefna(self, desc):
        raise common.FeatureNotAvailable(self.desc+" on "+self.comm.port, desc+" is not available with this model phone")

    def getfirmwareinformation(self):
        self.__raisefna("getfirmwareinformation")

    def offlinerequest(self, reset=False, delay=0):
        self.__raisefna("offlinerequest")

    def modemmoderequest(self):
        self.__raisefna("modemmoderequest")

    def mkdir(self, name):
        self.__raisefna("filesystem (mkdir)")
        
    def mkdirs(self, name):
        self.__raisefna("filesystem (mkdirs)")

    def rmdir(self, name):
        self.__raisefna("filesystem (rmdir)")

    def rmfile(self, name):
        self.__raisefna("filesystem (rmfile)")

    def getfilesystem(self, dir="", recurse=0):
        self.__raisefna("filesystem (getfilesystem)")

    def writefile(self, name, contents):
        self.__raisefna("filesystem (writefile)")

    def getfilecontents(self, name):
        self.__raisefna("filesystem (getfilecontents)")
