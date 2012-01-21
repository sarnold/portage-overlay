### BITPIM
###
### Copyright (C) 2005 Joe Pham <djpham@bitpim.org>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###

### $Id: phoneinfo.py 2275 2005-04-02 04:58:09Z djpham $

"""
Module to display specific handset info.
This module faciliates individual phones to provide specific phone info to be
displayed.  The PhoneInfo has the following attributes:

model: The phone model.
manufacturer: The phone manufacturer.
phone_number: The phone #.
esn: Phone ESN.
firmware_version: Phone firmware version.
signal_quality: (0-100%) Phone reception quality.
battery_level: (0-100%) Current battery level.

To add (and display) other phone information:

append(label_str, value_str)
  ie. phone_info.append('Analog/Digital:', 'Digital')

For an example of implementing this feature, please see module com_samsung.

"""

# standard modules

# site-packages modules
import wx
import  wx.lib.fancytext as fancytext

# BitPim modules

#-------------------------------------------------------------------------------
class PhoneInfo(object):
    __model_key='model'
    __manuf_key='_manufacturer'
    __phone_num_key='phone_num'
    __esn_key='esn'
    __firm_ver_key='firmware_version'
    __sig_qual_key='signal_quality'
    __battery_key='battery_level'
    standard_keys=(('model', 'Model:'),
                   ('manufacturer', 'Manufacturer:'),
                   ('phone_number', 'Phone Number:'),
                   ('esn', 'ESN:'),
                   ('firmware_version', 'Firmware Version:'),
                   ('signal_quality', 'Signal Quality:'),
                   ('battery_level', 'Battery Level:'))
    def __init__(self):
        self.__data={}
        self.__misc=[]
    def __get_model(self):
        return self.__data.get(self.__model_key, None)
    def __set_model(self, v):
        self.__data[self.__model_key]=v
    model=property(fset=__set_model, fget=__get_model)
    def __get_manufacturer(self):
        return self.__data.get(self.__manuf_key, None)
    def __set_manufacturer(self, v):
        self.__data[self.__manuf_key]=v
    manufacturer=property(fget=__get_manufacturer, fset=__set_manufacturer)
    def __get_phone_num(self):
        return self.__data.get(self.__phone_num_key, None)
    def __set_phone_num(self, v):
        self.__data[self.__phone_num_key]=v
    phone_number=property(fget=__get_phone_num, fset=__set_phone_num)
    def __get_esn(self):
        return self.__data.get(self.__esn_key, None)
    def __set_esn(self, v):
        self.__data[self.__esn_key]=v
    esn=property(fget=__get_esn, fset=__set_esn)
    def __get_firmware_ver(self):
        return self.__data.get(self.__firm_ver_key, None)
    def __set_firmware_ver(self, v):
        self.__data[self.__firm_ver_key]=v
    firmware_version=property(fget=__get_firmware_ver, fset=__set_firmware_ver)
    def __get_sig_qual(self):
        return self.__data.get(self.__sig_qual_key, None)
    def __set_sig_qual(self, v):
        self.__data[self.__sig_qual_key]=v
    signal_quality=property(fget=__get_sig_qual, fset=__set_sig_qual)
    def __get_battery(self):
        return self.__data.get(self.__battery_key, None)
    def __set_battery(self, v):
        self.__data[self.__battery_key]=v
    battery_level=property(fget=__get_battery, fset=__set_battery)
    def append(self, label_str, value_str):
        self.__misc.append((label_str, value_str))
    def __get_misc(self):
        return self.__misc
    misc=property(fget=__get_misc)

#-------------------------------------------------------------------------------
class PhoneInfoDialog(wx.Dialog):
    def __init__(self, parent, phone_info=PhoneInfo()):
        super(PhoneInfoDialog, self).__init__(parent, -1, 'Phone Info Dialog')
        self.__header_font=wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.__info_label_font=wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.__info_item_font=wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        # main vertical box sizer
        vbs=wx.BoxSizer(wx.VERTICAL)
        # the header
        vbs.Add(self.__header('Phone Information'), 0, wx.ALIGN_CENTRE, 10)
        # the info
        gs=wx.FlexGridSizer(-1, 2, 5, 5)
        for k in PhoneInfo.standard_keys:
            v=getattr(phone_info, k[0])
            if v is None:
                continue
            gs.Add(self.__info_label(k[1]), 1, wx.EXPAND|wx.BOTTOM|wx.ALIGN_LEFT, 5)
            gs.Add(self.__info_item(v), 0,  wx.EXPAND|wx.BOTTOM|wx.ALIGN_LEFT, 5)
        l=phone_info.misc
        for k in l:
            gs.Add(self.__info_label(k[0]), 0, wx.EXPAND|wx.BOTTOM|wx.ALIGN_LEFT, 5)
            gs.Add(self.__info_item(k[1]), 0, wx.EXPAND|wx.BOTTOM|wx.ALIGN_LEFT, 5)
        vbs.Add(gs, 1, wx.EXPAND|wx.ALL, 10)
        # the ok button
        vbs.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        vbs.Add(wx.Button(self, wx.ID_OK), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        # all done
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)
    def __header(self, txt):
        static_text=wx.StaticText(self, -1, txt, style=wx.ALIGN_CENTRE)
        static_text.SetFont(self.__header_font)
        return static_text
    def __info_label(self, txt):
        if txt[-1]!=':':
            txt+=':'
        static_text=wx.StaticText(self, -1, txt, style=wx.ALIGN_LEFT)
        static_text.SetFont(self.__info_label_font)
        return static_text
    def __info_item(self, txt):
        static_text=wx.StaticText(self, -1, txt, style=wx.ALIGN_LEFT)
        static_text.SetFont(self.__info_item_font)
        return static_text
