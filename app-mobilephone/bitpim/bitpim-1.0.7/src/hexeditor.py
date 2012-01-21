#!/usr/bin/env python
### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: hexeditor.py 4377 2007-08-27 04:58:33Z djpham $

"""A hex editor widget"""

# system modules
from __future__ import with_statement
import string
import struct

# wx modules
import wx
from wx.lib import masked
from wx.lib import scrolledpanel as scrolled

# bitpim modules
import common
import guihelper

#-------------------------------------------------------------------------------
class DataStruct(object):
    def __init__(self, _name):
        self.name=_name
        self.fields=[]
    def set(self, dict):
        self.name=dict.keys()[0]
        self.fields=[]
        for f in dict[self.name]:
            if f['type']==DataItem.numeric_type:
                item=NumericDataItem(f['name'])
            elif f['type']==DataItem.string_type:
                item=StringDataItem(f['name'])
            else:
                item=DataItem(f['name'], DataItem.struct_type)
            item.set(f)
            self.fields.append(item)
    def get(self):
        l=[]
        for f in self.fields:
            l.append(f.get())
        return { self.name: l }
    def encode(self, data, buffer_offset=0):
        # encode data to each & every fields and return the results
        l=[]
        start=0
        data_len=len(data)
        for f in self.fields:
            s=f.encode(data, start)
            start=f.start+f.len
            l.append( { '[0x%04X=%d]%s'%(f.start+buffer_offset,
                                         f.start+buffer_offset, f.name): `s` })
            if start>=data_len:
                break
        return l

#-------------------------------------------------------------------------------
class DataItem(object):
    """Represent a data item/component with in a record, which is a list of
    these things.
    """
    offset_from_start='From Start'
    offset_from_prev='From Last Field'
    string_type='string'
    numeric_type='numeric'
    struct_type='struct'
    def __init__(self, _name, _type=numeric_type):
        self.name=_name
        self.offset_type=self.offset_from_start
        self.offset=0
        self.size=1
        self.start=self.len=None   # start & length/size of actual data encoded
        # numeric fields
        self.unsigned=True
        self.LE=True
        # string fields
        self.fixed=True
        self.null_terminated=False
        self.type=_type
    def _get_type(self):
        return self._type
    def _set_type(self, _type):
        if _type not in (self.numeric_type, self.string_type, self.struct_type):
            raise TypeError
        self._type=_type
        if _type==self.numeric_type:
            self.__class__=NumericDataItem
        elif _type==self.string_type:
            self.__class__=StringDataItem
    type=property(fget=_get_type, fset=_set_type)
    def get(self):
        return { 'name': self.name, 'offset_type': self.offset_type,
                 'offset': self.offset, 'type': self.type }
    def set(self, d):
        self.name=d.get('name', '<None>')
        self.offset_type=d.get('offset_type', None)
        self.offset=d.get('offset', None)
        self.type=d.get('type', None)
    def encode(self, s, start=None):
        """Encode the value of this item based on the string s"""
        raise NotImplementedError

#-------------------------------------------------------------------------------
class NumericDataItem(DataItem):
    _fmts={ # struct pack/unpack formats
        True: { # unsigned
            True: { # little endian
                1: 'B', 2: '<H', 4: '<I' }, # size
            False: { # big endian
                1: 'B', 2: '>H', 4: '>I' } }, # size
        False: { # signed
            True: { # little endian
                1: 'b', 2: '<h', 4: '<i' }, # size
            False: { # big endian
                1: 'b', 2: '>h', 4: '>i' } } } # size
            
    def __init__(self, name):
        super(NumericDataItem, self).__init__(name, self.numeric_type)
    def get(self):
        r=super(NumericDataItem, self).get()
        r.update(
            { 'unsigned': self.unsigned,
              'little_endian': self.LE,
              'size': self.size })
        return r
    def set(self, d):
        super(NumericDataItem, self).set(d)
        if d.get('type', None)!=self.numeric_type:
            raise TypeError
        self.unsigned=d.get('unsigned', True)
        self.LE=d.get('little_endian', True)
        self.size=d.get('size', 1)
    def encode(self, s, start=None):
        fmt=self._fmts[self.unsigned][self.LE][self.size]
        self.len=struct.calcsize(fmt)
        if self.offset_type==self.offset_from_start:
            self.start=self.offset
        else:
            if start is None:
                raise ValueError
            self.start=start+self.offset
        return struct.unpack(fmt, s[self.start:self.start+self.len])[0]

#-------------------------------------------------------------------------------
class StringDataItem(DataItem):
    def __init__(self, name):
        super(StringDataItem, self).__init__(name, self.string_type)
    def get(self):
        r=super(StringDataItem, self).get()
        r.update({ 'fixed': self.fixed, 'size': self.size,
                   'null_terminated': self.null_terminated })
        return r
    def set(self, d):
        super(StringDataItem, self).set(d)
        if d.get('type', None)!=self.string_type:
            raise TypeError
        self.fixed=d.get('fixed', True)
        self.size=d.get('size', 0)
        self.null_terminated=d.get('null_terminated', False)
    def encode(self, s, start=None):
        if self.offset_type==self.offset_from_start:
            self.start=self.offset
        else:
            if start is None:
                raise ValueError
            self.start=start+self.offset
        if self.fixed:
            # fixed length string
            if self.size==-1:
                # take all available space
                self.len=len(s)-self.offset
                s0=s[self.start:]
            else:
                # fixed size
                s0=s[self.start:self.start+self.size]
                self.len=self.size
        else:
            # pascal style variable string
            self.len=ord(s[self.start])
            s0=s[self.start+1:self.start+1+self.len]
        if self.null_terminated:
            i=s0.find('\x00')
            if i==-1:
                return s0
            else:
                self.len=i
                return s0[:i]
        else:
            return s0

#-------------------------------------------------------------------------------
class GeneralInfoSizer(wx.FlexGridSizer):
    def __init__(self, parent):
        super(GeneralInfoSizer, self).__init__(-1, 2, 5, 5)
        self.AddGrowableCol(1)
        self.Add(wx.StaticText(parent, -1, 'Struct Name:'), 0, wx.EXPAND|wx.ALL, 5)
        self._struct_name=wx.TextCtrl(parent, -1, '')
        self.Add(self._struct_name, 0, wx.EXPAND|wx.ALL, 5)
        self.Add(wx.StaticText(parent, -1, 'Field Name:'), 0, wx.EXPAND|wx.ALL, 5)
        self._name=wx.TextCtrl(parent, -1, '')
        self.Add(self._name, 0, wx.EXPAND|wx.ALL, 5)
        self.Add(wx.StaticText(parent, -1, 'Type:'), 0, wx.EXPAND|wx.ALL, 5)
        self._type=wx.ComboBox(parent, wx.NewId(),
                                choices=[DataItem.numeric_type,
                                         DataItem.string_type],
                                value=DataItem.numeric_type,
                                style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Add(self._type, 0, wx.EXPAND|wx.ALL, 5)
        self.Add(wx.StaticText(parent, -1, 'Offset Type:'), 0, wx.EXPAND|wx.ALL, 5)
        self._offset_type=wx.ComboBox(parent, -1,
                                       value=DataItem.offset_from_start,
                                       choices=[DataItem.offset_from_start,
                                                DataItem.offset_from_prev],
                                       style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Add(self._offset_type, 0, wx.EXPAND|wx.ALL, 5)
        self.Add(wx.StaticText(parent, -1, 'Offset Value:'), 0, wx.EXPAND|wx.ALL, 5)
        self._offset=masked.NumCtrl(parent, wx.NewId(),
                                    allowNegative=False,
                                    min=0)
        self.Add(self._offset, 0, wx.ALL, 5)
        self._fields_group=(self._name, self._type, self._offset_type,
                            self._offset)
    def set(self, data):
        if isinstance(data, DataStruct):
            self._struct_name.SetValue(data.name)
        elif isinstance(data, DataItem):
            self._name.SetValue(data.name)
            self._type.SetValue(data.type)
            self._offset_type.SetValue(data.offset_type)
            self._offset.SetValue(data.offset)
    def get(self, data):
        data.name=self._name.GetValue()
        data.type=self._type.GetValue()
        data.offset_type=self._offset_type.GetValue()
        data.offset=int(self._offset.GetValue())
        return data
    def show(self, show_struct=False, show_field=False):
        self._struct_name.Enable(show_struct)
        for w in self._fields_group:
            w.Enable(show_field)
    def _get_struct_name(self):
        return self._struct_name.GetValue()
    struct_name=property(fget=_get_struct_name)
    def _get_type(self):
        return self._type.GetValue()
    type=property(fget=_get_type)
    def _get_type_id(self):
        return self._type.GetId()
    type_id=property(fget=_get_type_id)
        
#-------------------------------------------------------------------------------
class NumericInfoSizer(wx.FlexGridSizer):
    _sign_choices=['Unsigned', 'Signed']
    _endian_choices=['Little Endian', 'Big Endian']
    _size_choices=['1', '2', '4']
    def __init__(self, parent):
        super(NumericInfoSizer, self).__init__(-1, 2, 5, 5)
        self.AddGrowableCol(1)
        self.Add(wx.StaticText(parent, -1, 'Signed:'), 0, wx.EXPAND|wx.ALL, 5)
        self._sign=wx.ComboBox(parent, -1, value=self._sign_choices[0],
                               choices=self._sign_choices,
                               style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Add(self._sign, 0, wx.EXPAND|wx.ALL, 5)
        self.Add(wx.StaticText(parent, -1, 'Endian:'), 0, wx.EXPAND|wx.ALL, 5)
        self._endian=wx.ComboBox(parent, -1, value=self._endian_choices[0],
                                 choices=self._endian_choices,
                                 style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Add(self._endian, 0, wx.EXPAND|wx.ALL, 5)
        self.Add(wx.StaticText(parent, -1, 'Size:'), 0, wx.EXPAND|wx.ALL, 5)
        self._size=wx.ComboBox(parent, -1, value=self._size_choices[0],
                               choices=self._size_choices,
                               style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Add(self._size, 0, wx.EXPAND|wx.ALL, 5)
    def set(self, data):
        if data.unsigned:
            self._sign.SetValue(self._sign_choices[0])
        else:
            self._sign.SetValue(self._sign_choices[1])
        if data.LE:
            self._endian.SetValue(self._endian_choices[0])
        else:
            self._endian.SetValue(self._endian_choices[1])
        self._size.SetValue(`data.size`)
    def get(self, data):
        data.unsigned=self._sign.GetValue()==self._sign_choices[0]
        data.LE=self._endian.GetValue()==self._endian_choices[0]
        data.size=int(self._size.GetValue())
        return data

#-------------------------------------------------------------------------------
class StringInfoSizer(wx.FlexGridSizer):
    _fixed_choices=['Fixed', 'Pascal']
    def __init__(self, parent):
        super(StringInfoSizer, self).__init__(-1, 2, 5, 5)
        self.AddGrowableCol(1)
        self.Add(wx.StaticText(parent, -1, 'Fixed/Pascal:'), 0, wx.EXPAND|wx.ALL, 5)
        self._fixed=wx.ComboBox(parent, -1, value=self._fixed_choices[0],
                                 choices=self._fixed_choices,
                                 style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Add(self._fixed, 0, wx.EXPAND|wx.ALL, 5)
        self.Add(wx.StaticText(parent, -1, 'Max Length:'), 0, wx.EXPAND|wx.ALL, 5)
        self._max_len=masked.NumCtrl(parent, -1, value=1, min=-1)
        self.Add(self._max_len, 0, wx.EXPAND|wx.ALL, 5)
        self.Add(wx.StaticText(parent, -1, 'Null Terminated:'), 0, wx.EXPAND|wx.ALL, 5)
        self._null_terminated=wx.CheckBox(parent, -1)
        self.Add(self._null_terminated, 0, wx.EXPAND|wx.ALL, 5)
    def set(self, data):
        if data.fixed:
            self._fixed.SetValue(self._fixed_choices[0])
        else:
            self._fixed.SetValue(self._fixed_choices[1])
        self._max_len.SetValue(`data.size`)
        self._null_terminated.SetValue(data.null_terminated)
    def get(self, data):
        data.fixed=self._fixed.GetValue()==self._fixed_choices[0]
        data.size=int(self._max_len.GetValue())
        data.null_terminated=self._null_terminated.GetValue()
        return data
        
#-------------------------------------------------------------------------------
class TemplateDialog(wx.Dialog):
    _type_choices=['Numeric', 'String']
    _struct_type='struct'
    _field_type='field'
    def __init__(self, parent):
        super(TemplateDialog, self).__init__(parent, -1,
                                             'Hex Template Editor',
                                             style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self._data=[]
        self._item_tree=self._numeric_bs=self._string_bs=None
        self._general_bs=None
        self._tree_root=None
        self._field_info=self._field_info_hbs=None
        self._info_sizer={ NumericDataItem.numeric_type: self._numeric_bs,
                           StringDataItem.string_type: self._string_bs }
        main_vbs=wx.BoxSizer(wx.VERTICAL)
        hbs1=wx.BoxSizer(wx.HORIZONTAL)
        hbs1.Add(self._create_tree_pane(), 1, wx.EXPAND|wx.ALL, 5)
        hbs1.Add(self._create_info_pane(), 2, wx.EXPAND|wx.ALL, 5)
        main_vbs.Add(hbs1, 1, wx.EXPAND|wx.ALL, 5)
        main_vbs.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL, 5)
        main_vbs.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.HELP), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.SetSizer(main_vbs)
        self.SetAutoLayout(True)
        main_vbs.Fit(self)

    def _create_tree_pane(self):
        vbs=wx.BoxSizer(wx.VERTICAL)
        sw=scrolled.ScrolledPanel(self, -1)
        self._item_tree=wx.TreeCtrl(sw, wx.NewId(),
                                    style=wx.TR_DEFAULT_STYLE|wx.TR_HAS_BUTTONS)
        wx.EVT_TREE_SEL_CHANGED(self, self._item_tree.GetId(),
                                self._OnTreeSel)
        self._tree_root=self._item_tree.AddRoot('Data Templates')
        sw_bs=wx.BoxSizer(wx.VERTICAL)
        sw_bs.Add(self._item_tree, 1, wx.EXPAND|wx.ALL, 0)
        sw.SetSizer(sw_bs)
        sw.SetAutoLayout(True)
        sw_bs.Fit(sw)
        sw.SetupScrolling()
        vbs.Add(sw, 1, wx.EXPAND|wx.ALL, 5)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        hbs.Add(wx.Button(self, wx.ID_ADD, 'Add'), 0, wx.EXPAND|wx.ALL, 5)
        hbs.Add(wx.Button(self, wx.ID_DELETE, 'Delete'), 0, wx.EXPAND|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_ADD, self._OnAdd)
        wx.EVT_BUTTON(self, wx.ID_DELETE, self._OnDelete)
        vbs.Add(hbs, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
        return vbs
    def _create_info_pane(self):
        # main boxsize
        vbs=wx.BoxSizer(wx.VERTICAL)
        hbs=wx.BoxSizer(wx.HORIZONTAL)
        # Type & offset
        static_bs=wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Field Type'),
                                    wx.VERTICAL)
        self._general_bs=GeneralInfoSizer(self)
        wx.EVT_COMBOBOX(self, self._general_bs.type_id, self._OnTypeChanged)
        static_bs.Add(self._general_bs, 0, wx.EXPAND|wx.ALL, 5)
        hbs.Add(static_bs, 0, wx.ALL, 5)
        # all info
        self._field_info=wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Field Info'),
                                    wx.VERTICAL)
        # numeric info box
        self._numeric_bs=NumericInfoSizer(self)
        self._field_info.Add(self._numeric_bs, 0, wx.EXPAND|wx.ALL, 5)
        self._string_bs=StringInfoSizer(self)
        self._field_info.Add(self._string_bs, 0, wx.EXPAND|wx.ALL, 5)
        hbs.Add(self._field_info, 0, wx.ALL, 5)
        vbs.Add(hbs, 1, wx.EXPAND|wx.ALL, 5)
        hbs1=wx.BoxSizer(wx.HORIZONTAL)
        hbs1.Add(wx.Button(self, wx.ID_SAVE, 'Set'), 0, wx.EXPAND|wx.ALL, 5)
        hbs1.Add(wx.Button(self, wx.ID_REVERT, 'Revert'), 0, wx.EXPAND|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_SAVE, self._OnSave)
        wx.EVT_BUTTON(self, wx.ID_REVERT, self._OnRevert)
        vbs.Add(hbs1, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        self._field_info_hbs=hbs
        return vbs
    def _show_field_info(self, _struct=False, field=False,
                         numeric_field=False, string_field=False):
        # show/hide individual fields
        self._general_bs.show(_struct, field)
        self._field_info.Show(self._numeric_bs, numeric_field)
        self._field_info.Show(self._string_bs, string_field)
        self._field_info.Layout()
        self._field_info_hbs.Layout()
    def _populate(self):
        # clear the tree and repopulate
        self._item_tree.DeleteChildren(self._tree_root)
        for i,e in enumerate(self._data):
            item=self._item_tree.AppendItem(self._tree_root, e.name)
            self._item_tree.SetPyData(item, { 'type': self._struct_type,
                                              'index': i })
            for i1,e1 in enumerate(e.fields):
                field_item=self._item_tree.AppendItem(item, e1.name)
                self._item_tree.SetPyData(field_item, { 'type': self._field_type,
                                                        'index': i,
                                                        'field_index': i1 })
        self.expand()
    def _populate_struct(self, _item_index):
        self._general_bs.set(self._data[_item_index])
        self._show_field_info(True)
    def _populate_each(self, _struct_index, _item_index):
        _struct=self._data[_struct_index]
        _item=_struct.fields[_item_index]
        self._general_bs.set(_item)
        if _item.type==DataItem.numeric_type:
            self._show_field_info(True, True, True)
            self._numeric_bs.set(_item)
        else:
            self._show_field_info(True, True, False, True)
            self._string_bs.set(_item)
    def _OnTypeChanged(self, _):
        new_type=self._general_bs.type
        self._show_field_info(True, True, new_type==DataItem.numeric_type,
                              new_type==DataItem.string_type)
    def _OnAdd(self, _):
        sel_idx=self._item_tree.GetSelection()
        if not sel_idx.IsOk():
            return
        if sel_idx==self._tree_root:
            # add a new structure
            struct_item=DataStruct('New Struct')
            self._data.append(struct_item)
        else:
            # add a new field to the existing structure
            data_item=self._item_tree.GetPyData(sel_idx)
            item=NumericDataItem('New Field')
            self._data[data_item['index']].fields.append(item)
        self._populate()
    def _OnDelete(self, _):
        sel_idx=self._item_tree.GetSelection()
        if not sel_idx.IsOk():
            return
        node_data=self._item_tree.GetPyData(sel_idx)
        if node_data is None:
            return
        if node_data['type']==self._field_type:
            # del this field
            del self._data[node_data['index']].fields[node_data['field_index']]
        else:
            # del this struct and its fields
            del self._data[node_data['index']]
        # and re-populate the tree
        self._populate()
    def _OnSave(self, _):
        sel_idx=self._item_tree.GetSelection()
        if not sel_idx.IsOk():
            return
        node_data=self._item_tree.GetPyData(sel_idx)
        if node_data is None:
            return
        # update the struct name
        self._data[node_data['index']].name=self._general_bs.struct_name
        if node_data['type']==self._field_type:
            data_item=self._data[node_data['index']].\
                       fields[node_data['field_index']]
            data_item=self._general_bs.get(data_item)
            if data_item.type==DataItem.numeric_type:
                data_item=self._numeric_bs.get(data_item)
            else:
                data_item=self._string_bs.get(data_item)
            self._data[node_data['index']].fields[node_data['field_index']]=data_item
            self._item_tree.SetItemText(self._item_tree.GetItemParent(sel_idx),
                                        self._data[node_data['index']].name)
            self._item_tree.SetItemText(sel_idx, data_item.name)
        else:
            self._item_tree.SetItemText(sel_idx, self._data[node_data['index']].name)
            
    def _OnRevert(self, _):
        sel_idx=self._item_tree.GetSelection()
        if not sel_idx.IsOk():
            return
        node_data=self._item_tree.GetPyData(sel_idx)
        if node_data is None:
            self._show_field_info()
        else:
            self._populate_struct(node_data['index'])
            if node_data['type']==self._field_type:
                self._populate_each(node_data['index'], node_data['field_index'])

    def _OnTreeSel(self, evt):
        sel_idx=evt.GetItem()
        if not sel_idx.IsOk():
            # invalid selection
            return
        item_data=self._item_tree.GetPyData(sel_idx)
        if item_data is None:
            self._show_field_info()
        else:
            self._populate_struct(item_data['index'])
            if item_data['type']==self._field_type:
                self._populate_each(item_data['index'], item_data['field_index'])
    def expand(self):
        # expand the tree
        self._item_tree.Expand(self._tree_root)
        (id, cookie)=self._item_tree.GetFirstChild(self._tree_root)
        while id.IsOk():
            self._item_tree.Expand(id)
            (id, cookie)=self._item_tree.GetNextChild(self._tree_root, cookie)
    def set(self, l):
        self._data=l
        self._populate()
    def get(self):
        return self._data
        
#-------------------------------------------------------------------------------
class HexEditor(wx.ScrolledWindow):

    _addr_range=xrange(8)
    _hex_range_start=10
    _hex_range_start2=33
    _hex_range=xrange(_hex_range_start, 58)
    _ascii_range_start=60
    _ascii_range=xrange(60, 76)

    def __init__(self, parent, id=-1, style=wx.WANTS_CHARS,
                 _set_pos=None, _set_sel=None, _set_val=None):
        wx.ScrolledWindow.__init__(self, parent, id, style=style)
        self.parent=parent
        self.data=""
        self.title=""
        self.buffer=None
        self.hasfocus=False
        self.dragging=False
        self.current_ofs=None
        self._module=None
        self._templates=[]
        self._search_string=None
        # ways of displaying status
        self.set_pos=_set_pos or self._set_pos
        self.set_val=_set_val or self._set_val
        self.set_sel=_set_sel or self._set_sel
        # some GUI setup
        self.SetBackgroundColour("WHITE")
        self.SetCursor(wx.StockCursor(wx.CURSOR_IBEAM))
        self.sethighlight(wx.NamedColour("BLACK"), wx.NamedColour("YELLOW"))
        self.setnormal(wx.NamedColour("BLACK"), wx.NamedColour("WHITE"))
        self.setfont(wx.TheFontList.FindOrCreateFont(10, wx.MODERN, wx.NORMAL, wx.NORMAL))
        self.OnSize(None)
        self.highlightrange(None, None)
        # other stuff
        self._create_context_menu()
        self._map_events()

    def _map_events(self):
        wx.EVT_SCROLLWIN(self, self.OnScrollWin)
        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_ERASE_BACKGROUND(self, self.OnEraseBackground)
        wx.EVT_SET_FOCUS(self, self.OnGainFocus)
        wx.EVT_KILL_FOCUS(self, self.OnLoseFocus)
        wx.EVT_LEFT_DOWN(self, self.OnStartSelection)
        wx.EVT_LEFT_UP(self, self.OnEndSelection)
        wx.EVT_MOTION(self, self.OnMakeSelection)
        wx.EVT_RIGHT_UP(self, self.OnRightClick)

    def _create_context_menu(self):
        self._reload_menu_id=self._apply_menu_id=None
        menu_items=(
            ('File', (('Load', self.OnLoadFile),
                      ('Save As', self.OnSaveAs),
                      ('Save Selection As', self.OnSaveSelection),
                      ('Save Hexdump As', self.OnSaveHexdumpAs))),
            ('Set Selection', (('Start', self.OnStartSelMenu),
                               ('End', self.OnEndSelMenu))),
            ('Value', self.OnViewValue),
            ('Search', (('Search', self.OnSearch),
                        ('Search Again', self.OnSearchAgain))),
            ('Import Python Module', self.OnImportModule),
            ('Reload Python Module', self.OnReloadModule, '_reload_menu_id'),
            ('Apply Python Func', self.OnApplyFunc, '_apply_menu_id'),
            ('Template', (('Load', self.OnTemplateLoad),
                          ('Save As', self.OnTemplateSaveAs),
                          ('Edit', self.OnTemplateEdit),
                          ('Apply', self.OnTemplateApply)))
            )
        self._bgmenu=wx.Menu()
        for menu_item in menu_items:
            if isinstance(menu_item[1], tuple):
                # submenu
                sub_menu=wx.Menu()
                for submenu_item in menu_item[1]:
                    id=wx.NewId()
                    sub_menu.Append(id, submenu_item[0])
                    wx.EVT_MENU(self, id, submenu_item[1])
                self._bgmenu.AppendMenu(wx.NewId(), menu_item[0], sub_menu)
            else:
                # regular menu item
                id=wx.NewId()
                self._bgmenu.Append(id, menu_item[0])
                wx.EVT_MENU(self, id, menu_item[1])
                if len(menu_item)>2:
                    # need to save menu ID
                    setattr(self, menu_item[2], id)

    def SetData(self, data):
        self.data=data
        self.needsupdate=True
        self.updatescrollbars()
        self.Refresh()

    def SetTitle(self, title):
        self.title=title

    def SetStatusDisplay(self, _set_pos=None, _set_sel=None, _set_val=None):
        self.set_pos=_set_pos or self._set_pos
        self.set_sel=_set_sel or self._set_sel
        self.set_val=_set_val or self._set_val

    def OnEraseBackground(self, _):
        pass
    def _set_pos(self, pos):
        pass
    def _set_sel(self, sel_start, sel_end):
        pass
    def _set_val(self, v):
        pass

    def _to_char_line(self, x, y):
        """Convert an x,y point to (char, line)
        """
        return x/self.charwidth, y/self.charheight
    def _to_xy(self, char, line):
        return char*self.charwidth, line*self.charheight
    def _to_buffer_offset(self, char, line):
        if char in self._hex_range:
            if char>self._hex_range_start2:
                char-=1
            if ((char-self._hex_range_start)%3)<2:
                return line*16+(char-self._hex_range_start)/3
        elif char in self._ascii_range:
            return line*16+char-self._ascii_range_start
    def _set_and_move(self, evt):
        c,l=self._to_char_line(evt.GetX(), evt.GetY())
        self.GetCaret().Move(self._to_xy(c, l))
        x0, y0=self.GetViewStart()
        char_x=c+x0
        line_y=l+y0
        return self._to_buffer_offset(char_x, line_y)
    _value_formats=(
        ('unsigned char', 'B', struct.calcsize('B')),
        ('signed char', 'b', struct.calcsize('b')),
        ('LE unsigned short', '<H', struct.calcsize('<H')),
        ('LE signed short', '<h', struct.calcsize('<h')),
        ('BE unsigned short', '>H', struct.calcsize('>H')),
        ('BE signed short', '>h', struct.calcsize('>h')),
        ('LE unsigned int', '<I', struct.calcsize('<I')),
        ('LE signed int', '<i', struct.calcsize('<i')),
        ('BE unsigned int', '>I', struct.calcsize('>I')),
        ('BE signed int', '>i', struct.calcsize('>i')),
        )
    def _gen_values(self, _data, _ofs):
        """ Generate the values of various number formats starting at the
        current offset.
        """
        n=_data[_ofs:]
        len_n=len(n)
        s='0x%X=%d'%(_ofs, _ofs)
        res=[{ 'Data Offset': s}, {'':''} ]
        for i,e in enumerate(self._value_formats):
            if len_n<e[2]:
                continue
            v=struct.unpack(e[1], n[:e[2]])[0]
            if i%2:
                s='%d'%v
            else:
                fmt='0x%0'+str(e[2]*2)+'X=%d'
                s=fmt%(v,v)
            res.append({ e[0]: s })
        return res

    def _apply_template(self, template_name):
        # if user specifies a block, encode that,
        if self.highlightstart is None or self.highlightstart==-1 or \
           self.highlightend is None or self.highlightend==-1:
            # no selection
            _data=self.data[self.current_ofs:]
            _ofs=self.current_ofs
        else:
            _data=self.data[self.highlightstart:self.highlightend]
            _ofs=self.highlightstart
        for f in self._templates:
            if f.name==template_name:
                l=[{ 'Template': f.name },
                   { 'Data Offset': '0x%04X=%d'%(_ofs, _ofs) }]
                return l+f.encode(_data, _ofs)
        return []

    def _display_result(self, result):
        """ Display the results from applying a Python routine over the data
        """
        s=''
        for d in result:
            for k,e in d.items():
                s+=k+':\t'+e+'\n'
        guihelper.MessageDialog(self, s, 'Results', style=wx.OK)

    def OnLoadFile(self, _):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, 'Select a file to load',
                                                     style=wx.OPEN|wx.FILE_MUST_EXIST),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self.SetData(file(dlg.GetPath(), 'rb').read())
    def OnSaveAs(self, _):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, 'Select a file to save',
                                                     style=wx.SAVE|wx.OVERWRITE_PROMPT),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                file(dlg.GetPath(), 'wb').write(self.data)
    def hexdumpdata(self):
        res=""
        l=len(self.data)
        if self.title:
            res += self.title+": "+`l`+" bytes\n"
        res += "<#! !#>\n"
        pos=0
        while pos<l:
            text="%08X "%(pos)
            line=self.data[pos:pos+16]
            for i in range(len(line)):
                text+="%02X "%(ord(line[i]))
            text+="   "*(16-len(line))
            text+="    "
            for i in range(len(line)):
                c=line[i]
                if (ord(c)>=32 and string.printable.find(c)>=0):
                    text+=c
                else:
                    text+='.'
            res+=text+"\n"
            pos+=16
        return res
        
    def OnSaveHexdumpAs(self, _):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, 'Select a file to save',
                                                     style=wx.SAVE|wx.OVERWRITE_PROMPT),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                file(dlg.GetPath(), 'wb').write(self.hexdumpdata())
    def OnSaveSelection(self, _):
        if self.highlightstart is None or self.highlightstart==-1 or \
           self.highlightend is None or self.highlightend==-1:
            # no selection
            return
        with guihelper.WXDialogWrapper(wx.FileDialog(self, 'Select a file to save',
                                                     style=wx.SAVE|wx.OVERWRITE_PROMPT),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                file(dlg.GetPath(), 'wb').write(
                    self.data[self.highlightstart:self.highlightend])

    def OnReloadModule(self, _):
        try:
            reload(self._module)
        except:
            self._module=None
            guihelper.MessageDialog(self, 'Failed to reload module',
                                    'Reload Module Error',
                                    style=wx.OK|wx.ICON_ERROR)

    def OnApplyFunc(self, _):
        choices=[x for x in dir(self._module) \
                 if callable(getattr(self._module, x))]
        with guihelper.WXDialogWrapper(wx.SingleChoiceDialog(self, 'Select a function to apply:',
                                                             'Apply Python Func',
                                                             choices),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                try:
                    res=getattr(self._module, dlg.GetStringSelection())(
                        self, self.data, self.current_ofs)
                    self._display_result(res)
                except:
                    guihelper.MessageDialog(self, 'Apply Func raised an exception',
                                            'Apply Func Error',
                                            style=wx.OK|wx.ICON_ERROR)

    def OnImportModule(self, _):
        with guihelper.WXDialogWrapper(wx.TextEntryDialog(self, 'Enter the name of a Python Module:',
                                                          'Module Import'),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                try:
                    self._module=common.importas(dlg.GetValue())
                except ImportError:
                    self._module=None
                    guihelper.MessageDialog(self, 'Failed to import module: '+dlg.GetValue(),
                                            'Module Import Error',
                                             style=wx.OK|wx.ICON_ERROR)

    def OnStartSelMenu(self, evt):
        ofs=self.current_ofs
        if ofs is not None:
            self.highlightstart=ofs
            self.needsupdate=True
            self.Refresh()
        self.set_sel(self.highlightstart, self.highlightend)
            
    def OnEndSelMenu(self, _):
        ofs=self.current_ofs
        if ofs is not None:
            self.highlightend=ofs+1
            self.needsupdate=True
            self.Refresh()
        self.set_sel(self.highlightstart, self.highlightend)

    def OnViewValue(self, _):
        ofs=self.current_ofs
        if ofs is not None:
            self._display_result(self._gen_values(self.data, ofs))

    def OnStartSelection(self, evt):
        self.highlightstart=self.highlightend=None
        ofs=self._set_and_move(evt)
        if ofs is not None:
            self.highlightstart=ofs
            self.dragging=True
            self.set_val(self.data[ofs:])
        else:
            self.set_val(None)
        self.needsupdate=True
        self.Refresh()
        self.set_pos(ofs)
        self.set_sel(self.highlightstart, self.highlightend)
        
    def OnMakeSelection(self, evt):
        if not self.dragging:
            return
        ofs=self._set_and_move(evt)
        if ofs is not None:
            self.highlightend=ofs+1
            self.needsupdate=True
            self.Refresh()
        self.set_pos(ofs)
        self.set_sel(self.highlightstart, self.highlightend)
    def OnEndSelection(self, evt):
        self.dragging=False
        ofs=self._set_and_move(evt)
        self.set_pos(ofs)
        self.set_sel(self.highlightstart, self.highlightend)

    def OnRightClick(self, evt):
        self.current_ofs=self._set_and_move(evt)
        if self.current_ofs is None:
            self.set_val(None)
        else:
            self.set_val(self.data[self.current_ofs:])
        self.set_pos(self.current_ofs)
        self._bgmenu.Enable(self._apply_menu_id, self._module is not None)
        self._bgmenu.Enable(self._reload_menu_id, self._module is not None)
        self.PopupMenu(self._bgmenu, evt.GetPosition())

    def OnTemplateLoad(self, _):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, 'Select a file to load',
                                                     wildcard='*.tmpl',
                                                     style=wx.OPEN|wx.FILE_MUST_EXIST),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                result={}
                try:
                    execfile(dlg.GetPath())
                except UnicodeError:
                    common.unicode_execfile(dlg.GetPath())
                exist_keys={}
                for i,e in enumerate(self._templates):
                    exist_keys[e.name]=i
                for d in result['templates']:
                    data_struct=DataStruct('new struct')
                    data_struct.set(d)
                    if exist_keys.has_key(data_struct.name):
                        self._templates[exist_keys[data_struct.name]]=data_struct
                    else:
                        self._templates.append(data_struct)

    def OnTemplateSaveAs(self, _):
        with guihelper.WXDialogWrapper(wx.FileDialog(self, 'Select a file to save',
                                                     wildcard='*.tmpl',
                                                     style=wx.SAVE|wx.OVERWRITE_PROMPT),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                r=[x.get() for x in self._templates]
                common.writeversionindexfile(dlg.GetPath(),
                                             { 'templates': r }, 1)

    def OnTemplateApply(self, _):
        if not self._templates:
            # no templates to apply
            return
        choices=[x.name for x in self._templates]
        with guihelper.WXDialogWrapper(wx.SingleChoiceDialog(self, 'Select a template to apply:',
                                                             'Apply Data Template',
                                                             choices),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                try:
                    res=self._apply_template(dlg.GetStringSelection())
                    self._display_result(res)
                except:
                    guihelper.MessageDialog(self, 'Apply Template raised an exception',
                                            'Apply Template Error',
                                            style=wx.OK|wx.ICON_ERROR),

    def OnTemplateEdit(self, _):
        dlg=TemplateDialog(self)
        dlg.set(self._templates)
        with guihelper.WXDialogWrapper(dlg, True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                self._templates=dlg.get()

    def OnSearch(self, evt):
        with guihelper.WXDialogWrapper(wx.TextEntryDialog(self, 'Enter data to search (1 0x23 045 ...):',
                                                          'Search Data'),
                                       True) as (dlg, retcode):
            if retcode==wx.ID_OK:
                l=dlg.GetValue().split(' ')
                s=''
                for e in l:
                    if e[0:2]=='0x':
                        s+=chr(int(e, 16))
                    elif e[0]=='0':
                        s+=chr(int(e, 8))
                    else:
                        s+=chr(int(e))
                i=self.data[self.current_ofs:].find(s)
                if i!=-1:
                    self._search_string=s
                    self.highlightstart=i+self.current_ofs
                    self.highlightend=self.highlightstart+len(s)
                    self.needsupdate=True
                    self.Refresh()
                    self.set_sel(self.highlightstart, self.highlightend)
                else:
                    self._search_string=None

    def OnSearchAgain(self, evt):
        if self._search_string is not None:
            i=self.data[self.current_ofs:].find(self._search_string)
            if i==-1:
                return
            self.highlightstart=i+self.current_ofs
            self.highlightend=self.highlightstart+len(self._search_string)
            self.needsupdate=True
            self.Refresh()
            self.set_sel(self.highlightstart, self.highlightend)

    def OnSize(self, evt):
        # uncomment these lines to prevent going wider than is needed
        # if self.width>self.widthinchars*self.charwidth:
        #    self.SetClientSize( (self.widthinchars*self.charwidth, self.height) )
        if evt is None:
            self.width=(self.widthinchars+3)*self.charwidth
            self.height=self.charheight*20
            self.SetClientSize((self.width, self.height))
            self.SetCaret(wx.Caret(self, (self.charwidth, self.charheight)))
            self.GetCaret().Show(True)
        else:
            self.width,self.height=self.GetClientSizeTuple()
        self.needsupdate=True

    def OnGainFocus(self,_):
        self.hasfocus=True
        self.needsupdate=True
        self.Refresh()

    def OnLoseFocus(self,_):
        self.hasfocus=False
        self.needsupdate=True
        self.Refresh()

    def highlightrange(self, start, end):
        self.needsupdate=True
        self.highlightstart=start
        self.highlightend=end
        self.Refresh()
        self.set_pos(None)
        self.set_sel(self.highlightstart, self.highlightend)
        self.set_val(None)

    def _ishighlighted(self, pos):
        return pos>=self.highlightstart and pos<self.highlightend

    def sethighlight(self, foreground, background):
        self.highlight=foreground,background

    def setnormal(self, foreground, background):
        self.normal=foreground,background

    def setfont(self, font):
        dc=wx.ClientDC(self)
        dc.SetFont(font)
        self.charwidth, self.charheight=dc.GetTextExtent("M")
        self.font=font
        self.updatescrollbars()

    def updatescrollbars(self):
        # how many lines are we?
        lines=len(self.data)/16
        if lines==0 or len(self.data)%16:
            lines+=1
        self.datalines=lines
##        lines+=1 # status line
        # fixed width
        self.widthinchars=8+2+3*16+1+2+16
        self.SetScrollbars(self.charwidth, self.charheight, self.widthinchars, lines, self.GetViewStart()[0], self.GetViewStart()[1])

    def _setnormal(self,dc):
        dc.SetTextForeground(self.normal[0])
        dc.SetTextBackground(self.normal[1])

    def _sethighlight(self,dc):
        dc.SetTextForeground(self.highlight[0])
        dc.SetTextBackground(self.highlight[1])    

    def _setstatus(self,dc):
        dc.SetTextForeground(self.normal[1])
        dc.SetTextBackground(self.normal[0])
        dc.SetBrush(wx.BLACK_BRUSH)
        

    def OnDraw(self, dc):
        xd,yd=self.GetViewStart()
        st=0  # 0=normal, 1=highlight
        dc.BeginDrawing()
        dc.SetBackgroundMode(wx.SOLID)
        dc.SetFont(self.font)
        for line in range(yd, min(self.datalines, yd+self.height/self.charheight+1)):
            # address
            self._setnormal(dc)
            st=0
            dc.DrawText("%08X" % (line*16), 0, line*self.charheight)
            # bytes
            for i in range(16):
                pos=line*16+i
                if pos>=len(self.data):
                    break
                hl=self._ishighlighted(pos)
                if hl!=st:
                    if hl:
                        st=1
                        self._sethighlight(dc)
                    else:
                        st=0
                        self._setnormal(dc)
                if hl:
                    space=""
                    if i<15:
                        if self._ishighlighted(pos+1):
                            space=" "
                            if i==7:
                                space="  "
                else:
                    space=""
                c=self.data[pos]
                dc.DrawText("%02X%s" % (ord(c),space), (10+(3*i)+(i>=8))*self.charwidth, line*self.charheight)
                if not (ord(c)>=32 and string.printable.find(c)>=0):
                    c='.'
                dc.DrawText(c, (10+(3*16)+2+i)*self.charwidth, line*self.charheight)

##        if self.hasfocus:
##            self._setstatus(dc)
##            w,h=self.GetClientSizeTuple()
##            dc.DrawRectangle(0,h-self.charheight+yd*self.charheight,self.widthinchars*self.charwidth,self.charheight)
##            dc.DrawText("A test of stuff "+`yd`, 0, h-self.charheight+yd*self.charheight)
                
        dc.EndDrawing()

    def updatebuffer(self):
        if self.buffer is None or \
           self.buffer.GetWidth()!=self.width or \
           self.buffer.GetHeight()!=self.height:
            if self.buffer is not None:
                del self.buffer
            self.buffer=wx.EmptyBitmap(self.width, self.height)

        mdc=wx.MemoryDC()
        mdc.SelectObject(self.buffer)
        mdc.SetBackground(wx.TheBrushList.FindOrCreateBrush(self.GetBackgroundColour(), wx.SOLID))
        mdc.Clear()
        self.PrepareDC(mdc)
        self.OnDraw(mdc)
        mdc.SelectObject(wx.NullBitmap)
        del mdc

    def OnPaint(self, event):
        if self.needsupdate:
            self.needsupdate=False
            self.updatebuffer()
        dc=wx.PaintDC(self)
        dc.BeginDrawing()
        dc.DrawBitmap(self.buffer, 0, 0, False)
        dc.EndDrawing()

    def OnScrollWin(self, event):
        self.needsupdate=True
        self.Refresh() # clear whole widget
        event.Skip() # default event handlers now do scrolling etc

class HexEditorDialog(wx.Dialog):
    _pane_widths=[-2, -3, -4]
    _pos_pane_index=0
    _sel_pane_index=1
    _val_pane_index=2
    def __init__(self, parent, data='', title='BitPim Hex Editor', helpd_id=-1):
        super(HexEditorDialog, self).__init__(parent, -1, title,
                                              size=(500, 500),
                                              style=wx.DEFAULT_DIALOG_STYLE|\
                                              wx.RESIZE_BORDER)
        self._status_bar=wx.StatusBar(self, -1)
        self._status_bar.SetFieldsCount(len(self._pane_widths))
        self._status_bar.SetStatusWidths(self._pane_widths)
        vbs=wx.BoxSizer(wx.VERTICAL)
        self._hex_editor=HexEditor(self, _set_pos=self.set_pos,
                                   _set_val=self.set_val,
                                   _set_sel=self.set_sel)
        self._hex_editor.SetData(data)
        self._hex_editor.SetTitle(title)
        vbs.Add(self._hex_editor, 1, wx.EXPAND|wx.ALL, 5)
        vbs.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        ok_btn=wx.Button(self, wx.ID_OK, 'OK')
        vbs.Add(ok_btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        vbs.Add(self._status_bar, 0, wx.EXPAND|wx.ALL, 0)
        self.SetSizer(vbs)
        self.SetAutoLayout(True)
        vbs.Fit(self)
    def set_pos(self, pos):
        """Display the current buffer offset in the format of
        Pos: 0x12=18
        """
        if pos is None:
            s=''
        else:
            s='Pos: 0x%X=%d'%(pos, pos)
        self._status_bar.SetStatusText(s, self._pos_pane_index)
    def set_sel(self, sel_start, sel_end):
        if sel_start is None or sel_start==-1 or\
           sel_end is None or sel_end ==-1:
            s=''
        else:
            sel_len=sel_end-sel_start
            sel_end-=1
            s='Sel: 0x%X=%d to 0x%X=%d (0x%X=%d bytes)'%(
                sel_start, sel_start, sel_end, sel_end,
                sel_len, sel_len)
        self._status_bar.SetStatusText(s, self._sel_pane_index)
    def set_val(self, v):
        if v:
            # char
            s='Val: 0x%02X=%d'%(ord(v[0]), ord(v[0]))
            if len(v)>1:
                # short
                u_s=struct.unpack('<H', v[:struct.calcsize('<H')])[0]
                s+=' 0x%04X=%d'%(u_s,  u_s)
            if len(v)>3:
                # int/long
                u_i=struct.unpack('<I', v[:struct.calcsize('<I')])[0]
                s+=' 0x%08X=%d'%(u_i, u_i)
        else:
            s=''
        self._status_bar.SetStatusText(s, self._val_pane_index)

    def set(self, data):
        self._hex_editor.SetData(data)

        
if __name__=='__main__':
    import sys

    if len(sys.argv)!=2:
        print 'Usage:',sys.argv[0],'<File Name>'
        sys.exit(1)
    app=wx.PySimpleApp()
    with guihelper.WXDialogWrapper(HexEditorDialog(None, file(sys.argv[1], 'rb').read(),
                                                 sys.argv[1]),
                                   True):
        pass
    sys.exit(0)
