### BITPIM
###
### Copyright (C) 2007 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: bp_config.py 4365 2007-08-17 21:11:59Z djpham $

"""BitPim Config class based on ConfigParser
"""

# system module
import ConfigParser
import os
import os.path

# BitPim module
import guihelper

###
###  BitPim Config class
###
class Config(ConfigParser.ConfigParser):
    """Handle reading and writing various BitPim config values
    """
    _default_config_filename='.bitpim'

    def __init__(self, config_file_name=None):
        """Constructor
        @param config_file_name: (optional) config file name
        """
        ConfigParser.ConfigParser.__init__(self)
        # get/set path & filename
        if config_file_name:
            self._filename=os.path.abspath(config_file_name)
            self._path=os.path.dirname(self._filename)
        else:
            self._path, self._filename=self._getdefaults()
        # read in the config if exist
        if self._filename:
            try:
                self.read([self._filename])
            except:
                # something is wrong with the config file, just bail
                if __debug__:
                    raise
            self.Write('path', self._path)
            self.Write('config', self._filename)

    def _getdefaults(self):
        # return the default path & config file name
        # consistent with the previous BitPim way
        if guihelper.IsMSWindows(): # we want subdir of my documents on windows
            # nice and painful
            from win32com.shell import shell, shellcon
            try:
                path=shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
            except: # it will fail if path doesn't exist.  one example was a user
                # putting my docs on an external usb drive that isn't plugged in
                # when starting bitpim
                path=r"c:\My BitPim Files"
            path=os.path.join(path, "bitpim")
        else:
            path=os.path.expanduser("~/.bitpim-files")
        return path,os.path.join(path, Config._default_config_filename)

    def _expand(self, key):
        # return a tuple of (section, option) based on the key
        _l=key.split('/')
        return ('/'.join(_l[:-1]) if len(_l)>1 else 'DEFAULT', _l[-1])
        
    def _check_section(self, section):
        if section and section!='DEFAULT' and not self.has_section(section):
            self.add_section(section)

    def Read(self, key, default=''):
        """Read the value of keyword key, if that keyword does not exist, return default
        @param key: string key value.
        @param default: default value if key does not exist.
        @returns: the value of key
        """
        try:
            return self.get(*self._expand(key))
        except:
            return default

    def ReadInt(self, key, default=0):
        """Read the value of keyword key, if that keyword does not exist, return default
        @param key: string key value.
        @param default: default value if key does not exist.
        @returns: the value of key
        """
        _section,_option=self._expand(key)
        try:
            # first try for an int value
            return self.getint(_section, _option)
        except:
            pass
        try:
            # then check for a bool value
            return self.getboolean(_section, _option)
        except:
            # none found, return the default
            return default

    def ReadFloat(self, key, default=0.0):
        """Read the value of keyword key, if that keyword does not exist, return default
        @param key: string key value.
        @param default: default value if key does not exist.
        @returns: the value of key
        """
        try:
            return self.getfloat(*self._expand(key))
        except:
            return default

    def Write(self, key, value):
        """Write the value of keyword key.
        @param key: string key value.
        @param value: the value of the key.
        """
        try:
            _section,_option=self._expand(key)
            if not _section:
                _section='DEFAULT'
            self._check_section(_section)
            self.set(_section, _option, str(value))
            self.write(file(self._filename, 'wb'))
            return True
        except:
            return False
    WriteInt=Write
    WriteFloat=Write

    def HasEntry(self, key):
        """Check if the specified key exists.
        @param key: key value
        @returns: True if key exists, False otherwise.
        """
        return self.has_option(*self._expand(key))
    def Flush(self):
        pass
