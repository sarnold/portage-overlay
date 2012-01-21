#!/usr/bin/env python

### BITPIM
###
### Copyright (C) 2003-2006 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: bp.py 4436 2007-10-30 23:10:47Z djpham $

"""Main entry point to Bitpim

It invokes BitPim in gui or commandline mode as appropriate

@Note: Only gui mode is supported at the moment
"""
from __future__ import with_statement
import sys
import bp_cli

# only gui mode support at the moment

if __debug__:
    def profile(filename, command):
        import hotshot, hotshot.stats, os
        file=os.path.abspath(filename)
        profile=hotshot.Profile(file)
        profile.run(command)
        profile.close()
        del profile
	howmany=100
        stats=hotshot.stats.load(file)
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats(100)
        stats.sort_stats('cum', 'calls')
        stats.print_stats(100)
        stats.sort_stats('calls', 'time')
        stats.print_stats(100)
        sys.exit(0)
        

if __name__ == '__main__':
    import sys  
    import getopt
    import os.path

    # in production builds we don't need the stupid warnings
    if sys.platform=="darwin" and len(sys.argv)>1 and sys.argv[1].startswith("-psn_"):
	# get rid of the process serial number on mac
	sys.argv=sys.argv[:1]+sys.argv[2:]
    try:
        _options, _args=getopt.gnu_getopt(sys.argv[1:], 'c:d:f:p:')
        _invalid_args=[x for x in _args if x not in ['debug', 'bitfling'] and \
                       not bp_cli.valid_command(x)]
        if _invalid_args:
            raise getopt.GetoptError('Invalid argument(s): '+','.join(_invalid_args))
    except getopt.GetoptError:
        e=sys.exc_info()[1]
        _invalid_args=True
        _error_str=e.msg
    if _invalid_args:
        # invalid/unknown arguments
        try:
            import wx
            import guihelper
            _msg='%s\nUsage: %s [-c config file]|[-d config dir] [-p comm port] [-f phone model] [CLI Command] [debug] [bitfling]\n'%(_error_str, sys.argv[0])
            sys.stderr.write(_msg)
            # try to display an error message box
            _app=wx.PySimpleApp()
            guihelper.MessageDialog(None, _msg, 'BitPim Error',
                                    style=wx.OK|wx.ICON_ERROR)
        finally:
            sys.exit(1)
    _kwargs={}
    # check for debug flag
    _debug=bool(_args and 'debug' in _args)
    # CLI commands present?
    _clicmd=len(_args)==1 and bp_cli.valid_command(_args[0])
    if not _debug and not _clicmd:
        import warnings
        def ignorer(*args, **kwargs): pass
        warnings.showwarning=ignorer

        # on windows we set stdout, stderr to do nothing objects otherwise there
        # is an error after 4kb of output
        class _donowt:
            def __getattr__(self, _):
                return self

            def __call__(self, *args, **kwargs):
                pass
            
        # heck, do it for all platforms
        sys.stdout=_donowt()
        sys.stderr=_donowt()

    for _k,_v in _options:
        if _k=='-d':
            _kwargs['config_filename']=os.path.join(_v, '.bitpim')
        elif _k=='-c':
            _kwargs['config_filename']=_v
        elif _k=='-p':
            _kwargs['comm_port']=_v
        elif _k=='-f':
            _kwargs['phone_model']=_v
    if _args and _clicmd:
        # CLI detected
        _cli=bp_cli.CLI(_args[0], sys.stdin, sys.stdout, sys.stderr,
                        **_kwargs)
        if _cli.OK:
            _cli.run()
    elif _args and 'bitfling' in _args:
        import bitfling.bitfling
        #if True:
        #    profile("bitfling.prof", "bitfling.bitfling.run(sys.argv)")
        #else:
        bitfling.bitfling.run(sys.argv)
    else:
        import gui
        #if True:
        #    profile("bitpim.prof", "gui.run(sys.argv)")
        #else:
        gui.run(sys.argv, _kwargs)
