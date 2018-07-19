#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os, sys
import random
from threading import Timer
from multiprocessing import Process, Manager

import pafy
from math import log10

sys.path.append('/home/pi/Documents/typiremote')
os.environ['DJANGO_SETTINGS_MODULE'] = 'typiremote.settings'
import django
django.setup()
from django.db import connection, connections
from settings.models import UserSettings
from media.models import Audio, Playlist

f = os.popen('cat /tmp/omxplayerdbus.${USER:-root}')
os.environ["DBUS_SESSION_BUS_ADDRESS"] = f.read().rstrip()

def playURL(d, url):
    os.system("omxplayer -o local '" + url + "' --vol " + str(int(defaultRangeToMillibels(d["volumemedia"] / 10.0))))

def playURLLoop(d, url):
    os.system("omxplayer -o local --loop '" + url + "' --vol " + str(int(defaultRangeToMillibels(d["volumemedia"] / 10.0))))

def playAudio(d):
    while True:
        if d["audioPlaying"] == 1:
            if not connection.in_atomic_block: connection.close()
            d["audioPlaying"] == 0
            a = Audio.objects.get(name=d["audioPlayingName"])
            playURL(d, "/" + a.audio_file.url)
    
def playPlaylist(d, lock):
    while True:
        if d["playlistPlaying"] == 1:
            if lock.acquire():
                if not connection.in_atomic_block: connection.close()
                lastInt = -1
                p = Playlist.objects.get(name=d["playlistPlayingName"])
                lock.release()
                totalMusicCount = p.audiolist.count()
                while d["playlistPlaying"] == 1:
                    randomInd = random.randint(0, totalMusicCount - 1)
                    if totalMusicCount == 1:
                        playURL(d, "/" + p.audiolist.all()[randomInd].audio_file.url)
                        continue
                    elif randomInd != lastInt:
                        lastInt = randomInd
                        playURL(d, "/" + p.audiolist.all()[lastInt].audio_file.url)

def playLoopContinuously(d):
    while True:
        if d["playloop"] == 1:
            playURL(d, d["loopURL"])
    
def stopPlaying(d, lock):
    while True:
        if d["stopmedia"] == 1:
            d["stopmedia"] = 0
            d["playlistPlaying"] = 0
            d["playlistPlayingName"] = None
            d["audioPlaying"] = 0
            d["audioPlayingName"] = None
            d["playloop"] = 0
            os.system("/home/pi/Documents/YoutubeAPI/omxplayer/dbuscontrol.sh stop")
        elif d["pausemedia"] == 1:
            d["pausemedia"] = 0
            os.system("/home/pi/Documents/YoutubeAPI/omxplayer/dbuscontrol.sh pause")
            
def changeVolumeProcess(d, lock):
    while True:
        if d["changevolume"] == 1:
            if lock.acquire():
                if not connection.in_atomic_block: connection.close()
                d["changevolume"] = 0
                dbusSendCommand = 'dbus-send --print-reply --session --reply-timeout=500 --dest=org.mpris.MediaPlayer2.omxplayer /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Set string:"org.mpris.MediaPlayer2.Player" string:"Volume" double:' + str(int(d["volumemedia"]) / 10.0)
                os.system(dbusSendCommand)
                currentUser = UserSettings.objects.get(name="current")
                currentUser.volume = d["volumemedia"]
                currentUser.save()
                lock.release()
            
def playAnother(url):
    stopPlaying()
    playURL(None, url)

def millibelsToDefaultRange(m):
    return 10 ** (m / 2000.0)

def defaultRangeToMillibels(r):
    if r < 0.1: return -6000
    return 2000 * (log10(r))

def run():
    #~ def playURL("", url):
        #~ os.system("omxplayer -o local '" + url + "'")

    def stopPlaying():
        print("Hello!!!!")
        os.system("/home/pi/Documents/YoutubeAPI/omxplayer/dbuscontrol.sh stop")
    
    url = "https://www.youtube.com/watch?v=kRj4toENrnA"
    video = pafy.new(url)
    best = video.getbest()
    
    url2 = 'https://www.youtube.com/watch?v=Hh9yZWeTmVM'
    video2 = pafy.new(url2)
    best2 = video2.getbest()

    #~ Timer(20, stopPlaying).start()
    Timer(10, playURL, [None, best.url]).start()
    Timer(20, stopPlaying).start()
    Timer(40, playURL, [None, best2.url]).start()
    Timer(60, stopPlaying).start()
    #~ playURL(best.url)
    
    
    
       #~ def playURL(url):
        #~ os.system("sudo omxplayer -o local '" + url + "'")
#~ 
    #~ def stopPlaying():
        #~ os.system("sudo pkill omxplayer")
    #~ 
    #~ url = "https://www.youtube.com/watch?v=kRj4toENrnA"
    #~ video = pafy.new(url)
    #~ best = video.getbest()
    #~ 
    #~ url2 = 'https://www.youtube.com/watch?v=ktc8XDBq93k'
    #~ video2 = pafy.new(url2)
    #~ best2 = video2.getbest()
#~ 
    #~ Timer(20, stopPlaying).start()
    #~ Timer(20, stopPlaying).start()
    #~ Timer(40, playURL, [best.url]).start()
    #~ Timer(60, stopPlaying).start()
    #~ playURL(best.url)
