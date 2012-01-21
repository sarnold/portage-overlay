### BITPIM
###
### Copyright (C) 2006 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: field_color.py 4775 2010-01-04 03:44:57Z djpham $

"""
Code to handle setting colors for fields in various BitPim Editor Dialogs.
The idea is to show which fields are supported by the current phone model,
which fields are not, and which fields are unknown (default).

To use/enable this feature for your phone, define a dict value in your phone
profile that specifies the applicability of various fields.  It's probably best
if you copy the default_field_info dict to your phone profile and set
appropriate values.  The value of each key can be either:
None (don't know),
True (applicable),
False (not applicable),
0 (not applicable),
int>0 (number of entries this phone can have).

The name of this dict is 'field_color_data'.  An example is included in module
com_lgvx9800.

"""

import wx

applicable_color=wx.BLUE
notapplicable_color=wx.RED
dunno_color=wx.BLACK

default_field_info={
    'phonebook': {
        'name': {
            'first': None, 'middle': None, 'last': None, 'full': None,
            'nickname': None },
        'number': {
            'type': None, 'speeddial': None, 'number': None,
            'ringtone': None, 'wallpaper': None },
        'email': None,
        'email_details': {
            'emailspeeddial': None, 'emailringtone': None,
            'emailwallpaper': None },
        'address': {
            'type': None, 'company': None, 'street': None, 'street2': None,
            'city': None, 'state': None, 'postalcode': None, 'country': None },
        'url': None,
        'memo': None,
        'category': None,
        'wallpaper': None,
        'ringtone': None,
        'storage': None,
        'secret': None,
        'ICE': None,
        'im': None,
        },
    'calendar': {
        'description': None, 'location': None, 'allday': None,
        'start': None, 'end': None, 'priority': None,
        'alarm': None, 'vibrate': None,
        'repeat': None,
        'memo': None,
        'category': None,
        'wallpaper': None,
        'ringtone': None,
        },
    'memo': {
        'subject': None,
        'date': None,
        'secret': None,
        'category': None,
        'memo': None,
        },
    'todo': {
        'summary': None,
        'status': None,
        'due_date': None,
        'percent_complete': None,
        'completion_date': None,
        'private': None,
        'priority': None,
        'category': None,
        'memo': None,
        },
    }

current_field_info=default_field_info


def build_field_info(widget, name=None):
    """Return the dict info for this widget
    """
    global current_field_info
    _parent=widget.GetParent()
    if name:
        _names=[name]
    else:
        _names=[]
    while _parent:
        if hasattr(_parent, 'color_field_name'):
            if _parent.color_field_name not in _names:
                _names.append(_parent.color_field_name)
        _parent=_parent.GetParent()
    _names.reverse()
    _dict=current_field_info
    for n in _names:
        if not _dict.has_key(n):
            _dict[n]={}
        _dict=_dict[n]
    return _dict

def get_children_count(widget):
    """Return the number of sibblings to this widget
    """
    _parent=widget.GetParent()
    _cnt=0
    if _parent:
        for _w in _parent.GetChildren():
            if isinstance(_w, widget.__class__):
                _cnt+=1
    return _cnt

def get_color_info_from_profile(widget):
    """Walk up the widget chain to find the one that has the phone profile
    """
    global current_field_info
    current_field_info=default_field_info
    _w=widget.GetParent()
    while _w:
        if hasattr(_w, 'phoneprofile'):
            # found it
            current_field_info=_w.phoneprofile.field_color_data
            return
        _w=_w.GetParent()

def color(widget, name, tree=None):
    """Return the appropriate color for this field
    """
    global current_field_info, default_field_info
    if tree:
        _dict=tree
    else:
        # need to build the field info dict
        _dict=build_field_info(widget)
    _val=_dict.get(name, None)
    _cnt=get_children_count(widget)
    if _val is None:
        if current_field_info==default_field_info:
            return dunno_color
        else:
            return notapplicable_color
    elif _val is False or not isinstance(_val, bool) and _cnt>_val:
        return notapplicable_color
    else:
        return applicable_color

def build_color_field(widget, klass, args, name, tree=None):
    """
    instantiate the widget, set the color, and return the widget
    """
    _w=klass(*args)
    if _w:
        _w.SetForegroundColour(color(widget, name, tree))
    return _w

def reload_color_info(widget, widgets):
    get_color_info_from_profile(widget)
    _fc_dict=build_field_info(widget, widget.color_field_name)
    for (_w, name) in widgets:
        _w.SetForegroundColour(color(_w, name, _fc_dict))

