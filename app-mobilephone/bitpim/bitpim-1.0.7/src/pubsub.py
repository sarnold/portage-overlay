### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id: pubsub.py 4768 2009-11-06 02:17:29Z hjelmn $


"""The publish subscribe mechanism used to maintain lists of stuff.

This helps different pieces of code maintain lists of things (eg
wallpapers, categories) and other to express and interest and be
notified when it changes (eg field editors).  The wxPython pubsub
module is the base.  The enhancements are a list of standard topics in
this file.

This code also used to be larger as the wxPython pubsub didn't use
weak references.  It does now, so a whole bunch of code could be
deleted.
"""

from wx.lib.pubsub import Publisher


###
### A list of topics
###


# Maintain the list of categories
REQUEST_GROUP_WALLPAPERS=( 'request', 'groupwps') # no data
GROUP_WALLPAPERS=( 'response', 'groupwps' ) # data is list of groups and their wallpapers
SET_GROUP_WALLPAPERS=( 'request', 'setgroupwps') # data is list of groups and their wallpapers
MERGE_GROUP_WALLPAPERS=( 'request', 'mergegroupwps') # data is list of groups and their wallpapers
REQUEST_CATEGORIES=( 'request', 'categories' ) # no data
ALL_CATEGORIES=( 'response', 'categories') # data is list of strings
SET_CATEGORIES=( 'request', 'setcategories') # data is list of strings
ADD_CATEGORY=( 'request', 'addcategory') # data is list of strings
MERGE_CATEGORIES=( 'request', 'mergecategories') # data is list of strings
ALL_WALLPAPERS=( 'response', 'wallpapers') # data is list of strings
REQUEST_WALLPAPERS=( 'request', 'wallpapers') # no data
ALL_RINGTONES=( 'response', 'ringtones' ) # data is list of strings
REQUEST_RINGTONES=( 'request', 'ringtones') # no data
PHONE_MODEL_CHANGED=( 'notification', 'phonemodelchanged') # data is phone module
REQUEST_RINGTONE_INDEX=('request', 'ringtone-index') # no data
ALL_RINGTONE_INDEX=('response', 'ringtone-index') # data is the ringtone-index dict
REQUEST_PB_LOOKUP=('request', 'phonebook') # Request to lookup a number
RESPONSE_PB_LOOKUP=('response', 'phonebook') # Response to the request
MEDIA_NAME_CHANGED=('notificaion', 'medianamechanged') # notify if name changed
REQUEST_TAB_CHANGED=('notification', 'tabchanges') # request to change the main tab
TODAY_ITEM_SELECTED=('notification', 'todayitemselected') # a Today item was selected
REQUEST_TODAY_DATA=('request', 'todaydata') # request data for Today page
RESPONSE_TODAY_DATA=('response', 'todaydata') # reponse data for Today page
NEW_DATA_AVAILABLE=('notification', 'dataavailable') # new data available
MIDNIGHT=('notification', 'midnight')   # midnight had passed
DR_RECORD=('notification', 'recorddata')    # DR On
DR_PLAY=('notification', 'playdata')        # DR Playback
DR_STOP=('notification', 'stop')            # DR stop
REQUEST_MEDIA_INFO=('request', 'mediainfo')     # Request media item description
RESPONSE_MEDIA_INFO=('response', 'mediainfo')   # Response: list of strings (lines)
REQUEST_MEDIA_OPEN=('request', 'mediaopen')  # Request to open/launch a media item

# MEDIA_NAME_CHANGED keys & types
media_change_type='type'
wallpaper_type='wallpaper'
ringtone_type='ringtone'
media_old_name='old_name'
media_new_name='new_name'

def subscribe(listener, topic):
    Publisher.subscribe(listener, topic)

def unsubscribe(listener):
    Publisher.unsubscribe(listener)

def publish(topic, data=None):
    Publisher.sendMessage(topic, data)
