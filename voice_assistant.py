#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import shelve
import sttcontroller
import atexit
import os, sys

from utils import is_connected
from console.models import MessageLog

#~ Initialize Django
sys.path.append('/home/pi/Documents/typiremote')
os.environ['DJANGO_SETTINGS_MODULE'] = 'typiremote.settings'
import django
django.setup()
from console.models import MessageLog
from settings.models import UserSettings

#~ def restart_program():
    #~ """Restarts the current program.
    #~ Note: this function does not return. Any cleanup action (like
    #~ saving data) must be done before calling this function."""
    #~ python = sys.executable
    #~ os.execl(python, python, * sys.argv)

def runVoiceAssistant(shelveDict):
    speech_source = 1
    isOfflineOnly = 0
    speech_source = int(UserSettings.objects.get(name="current").speech_source)
    if speech_source == 0:
        if is_connected(): isOfflineOnly = 1
        else: isOfflineOnly = 0
    elif speech_source == 1: isOfflineOnly = 1
    elif speech_source == 2: isOfflineOnly = 0
    
    sttcontroller.main(isOfflineOnly, shelveDict)
    
def exit_handler():
    with open("on-exit-file", "w+") as f:
        pass
    
if __name__ == '__main__':
    print("Program restarted main module")
    shelveDict = shelve.open("scripts.d")
    atexit.register(exit_handler)
    runVoiceAssistant(shelveDict)
