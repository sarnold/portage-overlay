### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@netzero.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: wpl_file.py 3542 2006-08-31 03:40:06Z djpham $

"""Handle MS Windows Media Player Play List (wpl) files"""

# System modules
import xml.dom.minidom as dom

class WPL(object):
    def __init__(self, data=None, filename=None):
        self.title=''
        self.songs=[]
        try:
            if data:
                self._decode(data)
            elif filename:
                self._decode(file(filename, 'rt').read())
        except (IndexError, IOError):
            pass

    def _node_value(self, node, name):
        try:
            return node.getElementsByTagName(name)[0].firstChild.data
        except IndexError:
            # the tag does not exist
            return None
        except:
            if __debug__: raise
            return None

    def _decode(self, data):
        # decode the xml stream
        _wpl=dom.parseString(data)
        _head=_wpl.getElementsByTagName('head')[0]
        self.title=self._node_value(_head, 'title')
        _seq=_wpl.getElementsByTagName('seq')[0]
        _media=_seq.getElementsByTagName('media')
        for _item in _media:
            self.songs.append(_item.getAttribute('src'))
