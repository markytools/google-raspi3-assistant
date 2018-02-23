#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import print_function
from os import environ, path
from multiprocessing import Process, Manager

MODELDIR = "pocketsphinx/model"
DATADIR = "pocketsphinx/model"

import argparse
import os.path
import json
import sys
import signal
import shelve
import inspect
import time
import RPi.GPIO as GPIO
from threading import Timer
from collections import deque

import pyaudio
import num2words
import google.oauth2.credentials

from pocketsphinx import *
from sphinxbase import *
from g2p_seq2seq import g2p
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file

import utils
import response
import tools.mediaplayer as MediaPlayer
from responsebuilder import ResponseBuilder
from linphonebase import LinphoneBase
from response import ResponseSwitch

from django import db
from django.db import connection
from django.utils import timezone
from settings.models import UserSettings
from console.models import MessageLog

#~ Initialize Lights
GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.OUT)    #Colored Bulbs
GPIO.setup(15, GPIO.OUT)    #Large Bulb
GPIO.setup(18, GPIO.OUT)    #Outlet
GPIO.output(14, GPIO.LOW)
GPIO.output(15, GPIO.LOW)
GPIO.output(18, GPIO.LOW)

#~ Initialize Message Logs
MessageLog.objects.all().delete()

class QueuedWord(object):
    """This class represents a single word queued for the CMU Sphinx Vocabulary"""
    
    def __init__(self, word='', vocab_added=False, dict_added=False, lm_added=False):
        """Base Queued Word class constructor
        Arguments:
        word -- the word in string in LOWERCASE. Word should not contain any newline character.
        vocab_added -- if this word is inserted into the vocabulary file
        dict_added -- if this word is inserted into the dictionary file
        lm_added -- if this word is inserted into the language model file
        
        Note: Make sure to have the word in LOWERCASE only.
        """
        self.word = word
        self.vocab_added = vocab_added
        self.dict_added = dict_added
        self.lm_added = lm_added
        
    def addToVocabulary(self, d, strArr):
        if d["dict_added"] and not d["vocab_added"]:
            with open("google-assistant.vocab", "w") as f:
                strArr = utils.insertLineIntoArray(strArr, self.word + "\n", "\n")
                strVal = "".join(strArr)
                f.write(strVal)
            d["vocab_added"] = True
        
    def addToDictionary(self, d, g2p_model, strArr):
        if not d["dict_added"]:
            phoneme_lines = g2p_model.decode([self.word])
            d["dict_added"] = True
            with open("google-assistant.dic", "w") as f:
                strArr = utils.insertLineIntoArray(strArr, self.word + " " + phoneme_lines[0] + "\n", " ")
                strVal = "".join(strArr)
                f.write(strVal)
        
    def addToLanguageModel(self, d):
        if d["vocab_added"] and not d["lm_added"]:
            with open("google-assistant.vocab", "r") as f:
                filecontents1 = f.readlines();
            with open("customcommands.txt", "r") as f:
                filecontents1 = filecontents1 + f.readlines()
            with open('customvocab.vocab', 'w') as f:
                for item in filecontents1:
                    f.write("%s" % item)
            os.system("sudo ~/Documents/CMUSphinx/SRILM/bin/armv7l/ngram-count -wbdiscount -interpolate -text customvocab.vocab -lm google-assistant.lm")
            
            #~ os.system("sudo ~/Documents/CMUSphinx/SRILM/bin/armv7l/ngram-count -wbdiscount -interpolate -text google-assistant.vocab -lm google-assistant.lm")
            d["lm_added"] = True
        
    def wordAdded(self, d):
        """All three files have been modified"""
        return d["vocab_added"] and d["dict_added"] and d["lm_added"]
    
    def __str__(self):
        return "QueuedWord: " + self.word
    
	def __repr__(self):
		return 'QueuedWord(word=%s, vocab_added=%d, dict_added=%d, lm_added=%d)' % (self.word, self.vocab_added, self.dict_added, self.lm_added)

def process_event(d, lock, li, consoleLogLi, assistantContext, event, shelveDict, responseBuilder):
    """Pretty prints events.

    Prints all events that occur with two spaces between each new
    conversation and a single space between turns of a conversation.

    Args:
        event(event.Event): The current event to process.
    """
    print(event)
    
    if event.type == EventType.ON_MUTED_CHANGED: consoleLogLi.append("Waiting for hotword...")
    elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        consoleLogLi.append("ON_CONVERSATION_TURN_STARTED: Speak now...")
        MediaPlayer.playURL(d, "/home/pi/Documents/VoiceAssistant/sounds/hotword-beep.mp3")
        if d["incomingCall"] != 1 and d["ongoingCall"] == 1:
            assistantContext.stop_conversation()
            d["endlinphonecall"] = 1
    elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED:
        text = event.args['text']
        shelveDict["previousText"] = text
        print("text: " + text)
        consoleLogLi.append("text: " + text)
        if text:
            wordList = text.split()
            filteredWordList = []
            for word in wordList:
                word = utils.getValidString(word)
                if word is not None:
                    word = utils.removeCharsFromStr(word, "!@#$,")
                    word = word.lower()
                    for subword in word.split():
                        filteredWordList.append(subword)
            
            filteredWordList = [x.encode('utf-8') for x in filteredWordList]
            response = responseBuilder.getResponse(filteredWordList)
            if response is not None:
                if response.responseSwitch == ResponseSwitch.GOOGLE_ONLY:
                    pass
                elif response.responseSwitch == ResponseSwitch.BOTH:
                    response.executeActions(d, lock)
                elif response.responseSwitch == ResponseSwitch.OFFLINE_ONLY:
                    assistantContext.stop_conversation()
                    response.executeActions(d, lock)
            for filteredWord in filteredWordList:
                li.append(filteredWord)
    elif event.type == EventType.ON_ASSISTANT_ERROR:
        print("ON_ASSISTANT_ERROR")
        print("event type: " + str(type(event.args['is_fatal'])))
        #~ consoleLogLi.append("ON_ASSISTANT_ERROR")
        #~ consoleLogLi.append("event type: " + str(type(event.args['is_fatal'])))
    elif event.type == EventType.ON_CONVERSATION_TURN_FINISHED: consoleLogLi.append("Waiting for hotword...")
        
def main(offline=0, shelveDict=None):
    
    #~ Initialize Google Assistant credentials
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--credentials', type=existing_file, metavar='OAUTH2_CREDENTIALS_FILE', default=os.path.join(os.path.expanduser('~/.config'),
                            'google-oauthlib-tool', 'credentials.json'), help='Path to store and read OAuth2 credentials')
    args = parser.parse_args()
    with open(args.credentials, 'r') as f: credentials = google.oauth2.credentials.Credentials(token=None, **json.load(f))
    assistantContext = 0
    
    #~ Initialize Responses
    responseBuilder = ResponseBuilder(shelveDict)
    
    def autoExecuteResponses(d, li, lock):
        while True:
            if len(li) > 0:
                response = li.pop(0)
                
    def autoqueueWords(d, li, lock):
        def updateQueuedWord(d, li, lock):
            newQueuedWord = li.pop(0)
            d["queueWord"] = QueuedWord(newQueuedWord)
            d["dict_added"] = False
            d["vocab_added"] = False
            d["lm_added"] = False
        
        while True:
            if len(li) > 0:
                if d.has_key("queueWord"):
                    if d["queueWord"].wordAdded(d):
                        updateQueuedWord(d, li, lock)
                else:
                    updateQueuedWord(d, li, lock)
                    
    
    def newWordsToSphinxVocabularyThread(d, strArr):
        while True:
            if d.has_key("queueWord"):
                d["queueWord"].addToVocabulary(d, strArr)
    
    def newWordsToSphinxDictionaryThread(d, strArr):
        with g2p.tf.Graph().as_default():
            """G2P only receives lowercase words"""
            model_dir = "g2p-seq2seq-cmudict"
            g2p_model = g2p.G2PModel(model_dir)
            g2p_model.load_decode_model()
            print("g2p loading done")
            while True:
                if d.has_key("queueWord"):
                    d["queueWord"].addToDictionary(d, g2p_model, strArr)
    
    def newWordsToSphinxLMThread(d):
        while True:
            pass
            if d.has_key("queueWord"):
                d["queueWord"].addToLanguageModel(d)
        
    def mainThread(d, lock, li, consoleLogLi, offline, shelveDict, responseBuilder):
        if offline == 0:
            #~ Initialize pocketsphinx
            config = Decoder.default_config()
            config.set_string('-hmm', 'acousticadaptation/en-us-adapt')
            config.set_string('-lm', "google-assistant.lm")
            config.set_string('-dict', "google-assistant.dic")
            decoder = Decoder(config)
            
            print("If Offline, Run CMU Sphinx")
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
            
            waitingResponse = [False, False]
            in_speech_bf = False
            
            stream.start_stream()
            decoder.start_utt()
            while True:
                buf = stream.read(1024, exception_on_overflow = False)
                if buf:
                    decoder.process_raw(buf, False, False)
                    if decoder.get_in_speech() != in_speech_bf:
                        in_speech_bf = decoder.get_in_speech()      
                        if not in_speech_bf:
                            decoder.end_utt()
                            result = decoder.hyp().hypstr
                            print('Result:', result)
                            #~ consoleLogLi.append('Result:' + result)
                            shelveDict["previousText"] = result
                            
                            if result:
                                #~ NO HOTWORD
                                #~ wordList = result.split()
                                #~ response = responseBuilder.getResponse(wordList)
                                #~ if response is not None: response.executeActions(d, lock)
                                
                                consoleLogLi.append("Text:" + str(result))
                                #~ WITH HOTWORD
                                if d["incomingCall"] == 1:
                                    if "accept" in result:
                                        d["incomingCall"] = 2
                                    elif "decline" in result:
                                        d["incomingCall"] = -1
                                else:
                                    if d["lastHotwordTime"] == -1:
                                        if ("ok google" in result) or ("hey google" in result):
                                            consoleLogLi.append("WAITING FOR RESPONSE")
                                            print("WAITING FOR RESPONSE")
                                            #~ consoleLogLi.append("WAITING FOR RESPONSE")
                                            MediaPlayer.playURL(d, "/home/pi/Documents/VoiceAssistant/sounds/hotword-beep.mp3")
                                            d["endlinphonecall"] = 1
                                            d["lastHotwordTime"] = int(round(time.time()))
                                    else:
                                        if ("ok google" in result) or ("hey google" in result):
                                            consoleLogLi.append("WAITING FOR RESPONSE")
                                            print("WAITING FOR RESPONSE")
                                            #~ consoleLogLi.append("WAITING FOR RESPONSE")
                                            MediaPlayer.playURL(d, "/home/pi/Documents/VoiceAssistant/sounds/hotword-beep.mp3")
                                            d["endlinphonecall"] = 1
                                            d["lastHotwordTime"] = int(round(time.time()))
                                        else:
                                            d["lastHotwordTime"] = -2
                                            consoleLogLi.append("EXECUTING RESPONSES")
                                            print("EXECUTING RESPONSES")
                                            #~ consoleLogLi.append("EXECUTING RESPONSES")
                                            wordList = result.split()
                                            response = responseBuilder.getResponse(wordList)
                                            if response is not None: response.executeActions(d, lock)
                                            d["lastHotwordTime"] = -1
                            del result
                            decoder.start_utt()
                else:
                    break
            stream.close()
            decoder.end_utt()
            p.terminate()
            
        else:
            print("If Online, Run Google Assistant")
            print("googleAssistant thread")
            retryProgramOnce = 1
            def sig_handler(signum, frame): 
                # Create a decoder with certain model
                
                print("Segmentation Fault Signal")
                #~ consoleLogLi.append("Segmentation Fault Signal")
                #~ utils.restart_program(shelveDict)
                    
            signal.signal(signal.SIGSEGV, sig_handler)
            
            with Assistant(credentials) as assistantContext:
                events = assistantContext.start()
                for event in events:
                    process_event(d, lock, li, consoleLogLi, assistantContext, event, shelveDict, responseBuilder)
 
    #~ Initialize multiprocesses
    with open("google-assistant.vocab", "r") as f:
        vocabStrArr = f.readlines()
    with open("google-assistant.dic", "r") as f:
        dicStrArr = f.readlines()
        
    def initLinphone(d, lock):
        if lock.acquire():
            if not connection.in_atomic_block: connection.close()
            currentAccount = UserSettings.objects.filter(name="current")
            if len(currentAccount) == 0:
                currentAccount = UserSettings(name="current")
                currentAccount.save()
            else:
                currentAccount = currentAccount[0]
            lock.release()
        linphoneBase = LinphoneBase(dictProxy=d, username=str(currentAccount.linphone_sip_acct), password=str(currentAccount.linphone_sip_pwd), whitelist=['sip:markytools@sip.linphone.org', 'sip:markaty@sip.linphone.org', 'sip:slylilytestacct@sip.linphone.org'], camera='', snd_capture='ALSA: default device', snd_playback='ALSA: default device')
        linphoneBase.setup()
        linphoneBase.run()
    
    def initHotwordDetection(d, consoleLogLi):
        while True:
            if d["lastHotwordTime"] != -1 and d["lastHotwordTime"] != -2 and int(round(time.time())) - d["lastHotwordTime"] >= 10:
                consoleLogLi.append("WAITING FOR RESPONSE KILLED")
                print("WAITING FOR RESPONSE KILLED")
                #~ consoleLogLi.append("WAITING FOR RESPONSE KILLED")
                d["lastHotwordTime"] = -1
                
    def pushMessagesProcess(d, lock, consoleLogLi):
        while True:
            if len(consoleLogLi) > 0:
                if lock.acquire():
                    #~ if connection.connection and not connection.is_usable(): del connections._connections.default
                    if not connection.in_atomic_block: connection.close()
                    msg = consoleLogLi.pop(0)
                    m = MessageLog(message=msg, pub_date=timezone.now())
                    m.save()
                    lock.release()
    
    manager = Manager()
    d = manager.dict({})
    li = manager.list([]) # List of string of words (lowercase)
    consoleLogLi = manager.list([]) # List of log messages to push
    lock = manager.Lock()
    
    d["vocab_added"] = False
    d["dict_added"] = False
    d["lm_added"] = False
    d["sipnametocall"] = None
    d["endlinphonecall"] = None
    d["playlistPlaying"] = 0
    d["playlistPlayingName"] = None
    d["audioPlaying"] = 0
    d["audioPlayingName"] = None
    d["stopmedia"] = 0
    d["pausemedia"] = 0
    d["changevolume"] = 0
    if lock.acquire():
        if not connection.in_atomic_block: connection.close()
        d["volumemedia"] = int(UserSettings.objects.get(name="current").volume)
        #~ d["volumemedia"] = 10
        lock.release()
    d["lastHotwordTime"] = -1
    d["playloop"] = 0
    d["loopURL"] = None
    d["incomingCall"] = 0
    d["stopOugoingCall"] = 0
    d["ongoingCall"] = 0
    d["currentCalledSIP"] = 0
    p1 = Process(target=mainThread, args=(d, lock, li, consoleLogLi, offline, shelveDict, responseBuilder,))
    p6 = Process(target=MediaPlayer.playAudio, args=(d,))
    p9 = Process(target=MediaPlayer.playPlaylist, args=(d, lock,))
    p7 = Process(target=MediaPlayer.stopPlaying, args=(d, lock,))
    p11 = Process(target=MediaPlayer.playLoopContinuously, args=(d,))
    #~ Temporarily disable linphone
    p8 = Process(target=initLinphone, args=(d, lock,))
    p10 = Process(target=initHotwordDetection, args=(d, consoleLogLi,))
    p12 = Process(target=pushMessagesProcess, args=(d, lock, consoleLogLi,))
    p13 = Process(target=MediaPlayer.changeVolumeProcess, args=(d, lock,))

    if offline == 1:
        p8.start()
        p1.start()
        p6.start()
        p7.start()
        p9.start()
        p11.start()
        p12.start()
        p13.start()
        
        p8.join()
        p1.join()
        p6.join()
        p7.join()
        p9.join()
        p11.join()
        p12.join()
        p13.join()
    else:
        p1.start()
        p6.start()
        p7.start()
        p9.start()
        p10.start()
        p11.start()
        p12.start()
        
        p1.join()
        p6.join()
        p7.join()
        p9.join()
        p10.join()
        p11.join()
        p12.join()

if __name__ == '__main__':
    shelveDict = shelve.open("scripts.d")
    responseBuilder = ResponseBuilder(shelveDict)
    response = responseBuilder.getResponse(["hello"])
    response.executeActions()
    print(response)
    
    #~ lines = inspect.getsourcelines(response.actions[0])  # This prints out the function's source code
    #~ print("\n")
    #~ print("Print the first action's source code:")
    #~ print("".join(lines[0]))
