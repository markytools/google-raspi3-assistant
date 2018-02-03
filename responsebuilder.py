#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os, sys
import os.path
import functools
import shelve
import inspect
import random
import RPi.GPIO as GPIO
from word2number import w2n
from num2words import num2words
from tools.trie import ResponseTrie
from response import Response, ResponseType, ResponseSwitch, SimpleResponse, speak
from linphonebase import LinphoneBase
import responsebuilder

sys.path.append('/home/pi/Documents/typiremote')
os.environ['DJANGO_SETTINGS_MODULE'] = 'typiremote.settings'
import django
django.setup()

from django.db import connection
from linphoneapp.models import LinphoneAccount
from media.models import Audio, Playlist

#~ Initialize Lights
GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.OUT)    #Colored Bulbs
GPIO.setup(15, GPIO.OUT)    #Large Bulb
GPIO.setup(18, GPIO.OUT)    #Outlet
GPIO.output(14, GPIO.LOW)
GPIO.output(15, GPIO.LOW)
GPIO.output(18, GPIO.LOW)

class ResponseBuilder(object):
    def __init__(self, shelveDict, responsesKey="responses"):
        """This is the base constructor for the builder class. It initializes the ResponseTrie that contains all of the responses.
        An object of type ResponseTrie called responses holds all of the responses of the Voice Assistant."""
        
        self.shelveDict = shelveDict
        self.responsesKey = responsesKey
        if not self.shelveDict.has_key(self.responsesKey): self.shelveDict[self.responsesKey] = ResponseTrie()
        self.responses = self.shelveDict[responsesKey]
        
    def hasResponse(self, keywords):
        return self.responses.hasKeywords(keywords)
        
    def getResponse(self, keywords):
        """Returns the Response value for this list of keywords. Returns None if nothing was found."""
        return self.responses.get(keywords)
        
    def addResponse(self, response):
        """Adds the Response object to the ResponseTrie consisting of responses with the joined string (trigger) as the key. Note that you still need to flush the builder in order to store it into the file."""
        self.responses.insert(response.triggers, response)
        
    def flushResponse(self):
        """Writes the response onto the shelve"""
        self.shelveDict[self.responsesKey] = self.responses
        
    def close(self):
        self.shelveDict.close()
        
def action1(a=10, b=100):
    print("This is action1")
    print("sum: " + str(a + b))
    print("\n")
    
def action2(a=10, b=100):
    print("This is action2")
    print("difference: " + str(a - b))
    print("\n")

def sumOfTwoAction(d):
    a = d["num1"]
    b = d["num2"]
    speak("en-US", "The sum of " + num2words(a) + " and " + num2words(b) + " is " + num2words(a + b))
    
def differenceOfTwoAction(d):
    a = d["num1"]
    b = d["num2"]
    speak("en-US", "The difference of " + num2words(a) + " and " + num2words(b) + " is " + num2words(a - b))
    
def productOfTwoAction(d):
    a = d["num1"]
    b = d["num2"]
    speak("en-US", "The product of " + num2words(a) + " and " + num2words(b) + " is " + num2words(a * b))
    
def quotientOfTwoAction(d):
    a = d["num1"]
    b = d["num2"]
    speak("en-US", "The quotient of " + num2words(a) + " and " + num2words(b) + " is " + num2words(a / b))
    
def powerOfTwoAction(d):
    a = d["num1"]
    b = d["num2"]
    speak("en-US", num2words(a) + " to the power of " + num2words(b) + " is " + num2words(a ** b))  
    
def rootOfTwoAction(d):
    a = d["num1"]
    b = d["num2"]
    speak("en-US", num2words(a) + " to the root of " + num2words(b) + " is " + num2words(a ** float(1 / float(b))))  

def celsiusToFahrenheit(d):
    a = d["num1"]
    speak("en-US", num2words(a) + "degrees celsius to fahrenheit is " + num2words(float((float(a) * float(float(9)/float(5))) + float(32))))  

def fahrenheitToCelsius(d):
    a = d["num1"]
    speak("en-US", num2words(a) + "degrees fahrenheit to celsius is " + num2words(float((float(a) -  float(32)) * float(float(5)/float(9)))))  
    
def speakNameVariable(d):
    name = d["name"]
    speak("en-US", "Ok, your name is " + name)

def linphoneCall(d):
    if not connection.in_atomic_block:
        connection.close()
    
    personToCall = d["linphoneName"]
    if personToCall:
        try:
            l = LinphoneAccount.objects.get(name=personToCall)
        except:
            speak("en-US", "Sorry, I cannot find that person in your contact list.")
        else:
            d["dictionaryproxy"]["sipnametocall"] = str(l.sip_account)

def linphoneEndCall(d):
    d["dictionaryproxy"]["endlinphonecall"] = 1

def playAudioOrPlaylist(d):
    def hasPlaylist(d, playlistName):
        Playlist.objects.get(name=playlistName)
    
    def hasAudio(d, audioName):
        Audio.objects.get(name=audioName)
    
    if not connection.in_atomic_block:
        connection.close()
    audioOrPlaylistName = d["audioOrPlaylistName"]
    if audioOrPlaylistName:
        try:
            hasPlaylist(d, audioOrPlaylistName)
        except:
            try:
                hasAudio(d, audioOrPlaylistName)
            except:
                speak("en-US", "Sorry, I cannot find that music or playlist.")
            else:
                d["dictionaryproxy"]["audioPlaying"] = 1
                d["dictionaryproxy"]["audioPlayingName"] = audioOrPlaylistName
        else:
            d["dictionaryproxy"]["playlistPlaying"] = 1
            d["dictionaryproxy"]["playlistPlayingName"] = audioOrPlaylistName

def stopMediaAction(d):
    d["dictionaryproxy"]["stopmedia"] = 1
    
def pauseMediaAction(d):
    d["dictionaryproxy"]["pausemedia"] = 1

def changeVolumeAction(d):
    volumelevel = d["volumelevel"]
    try:
        volumelevelInt = int(w2n.word_to_num(volumelevel))
    except:
        speak("en-US", "You're volume command is wrong. Try again.")
    else:
        if volumelevelInt >= 0 and volumelevelInt <= 10:
            d["dictionaryproxy"]["volumemedia"] = volumelevelInt
            d["dictionaryproxy"]["changevolume"] = 1
        else: speak("en-US", "You're volume command is wrong. Try again.")

def acceptCall(d):
    if d["dictionaryproxy"]["incomingCall"] == 1: d["dictionaryproxy"]["incomingCall"] = 2
    
def declineCall(d):
    if d["dictionaryproxy"]["incomingCall"] == 1: d["dictionaryproxy"]["incomingCall"] = -1

def stopOutgoingCall(d):
    d["dictionaryproxy"]["stopOugoingCall"] = 1

def rebootSystem():
    os.system("sudo reboot")
    
def poweroffSystem():
    os.system("sudo poweroff")
            
def testResponse(shelveDict):
    print("TEST 1: Basic Response")
    a1 = responsebuilder.action1    #It is important that the MODULE NAME of the function be stated specifically or else the function cannot be pickled into the shelve
    a2 = responsebuilder.action2
    respo = Response(["hello", "world"], [a1, a2], ResponseSwitch.GOOGLE_ONLY, ResponseType.NORMAL)
    respo.actions[0](2, 10)  # Execute the first action (index 0) with the specified arguments
    respo.actions[1]()       # Execute the second action (index 1) with the default arguments
    print(respo)            # Prints the Response class object
    
    lines = inspect.getsourcelines(respo.actions[0])  # This prints out the function's source code
    print("\n")
    print("Print the first action's source code:")
    print("".join(lines[0]))
    
    print("\nExecute all actions of the Response object:")
    respo.executeActions()
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(respo)
    responseBuilder.flushResponse()
    print("\nExecute all actions stored in the shelve:")
    responseBuilder.getResponse(["hello", "world"]).executeActions()
    
def testResponse2(shelveDict):
    print("\nTEST 2: Simple Response")
    simpleresponse = SimpleResponse(["hello"], "hello to you too!", "en-US", ResponseSwitch.GOOGLE_ONLY, ResponseType.NORMAL)
    print(simpleresponse)            # Prints the Response class object
    
    print("\nExecute all actions of the Response object:")
    simpleresponse.executeActions()
    
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(simpleresponse)
    responseBuilder.flushResponse()
    print("\nExecute all actions stored in the shelve:")
    responseBuilder.getResponse(["hello"]).executeActions()

def testResponse3(shelveDict):
    print("\nTEST 3: Numbers - Special Variable")
    specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    a1 = functools.partial(responsebuilder.sumOfTwoAction, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    sumResponse = Response(["<number:num1>", "plus", "<number:num2>"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(sumResponse)
    responseBuilder.flushResponse()
    
def testResponse4(shelveDict):
    print("\nTEST 4: Any - Special Variable")
    specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    a1 = functools.partial(responsebuilder.speakNameVariable, specialVars) #Creates a function object of the function 'speakNameVariable' without executing it
    anyVarsResponse = Response(["my", "name", "is", "<any:name>"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(anyVarsResponse)
    responseBuilder.flushResponse()
    
def testResponse5(shelveDict):
    print("\nTEST 5: Numbers - Special Variable")
    specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    a1 = functools.partial(responsebuilder.differenceOfTwoAction, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    diffResponse = Response(["<number:num1>", "minus", "<number:num2>"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(diffResponse)
    responseBuilder.flushResponse()
    
def testResponse6(shelveDict):
    print("\nTEST 6: Numbers - Special Variable")
    specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    a1 = functools.partial(responsebuilder.productOfTwoAction, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    productResponse = Response(["<number:num1>", "times", "<number:num2>"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(productResponse)
    responseBuilder.flushResponse()
    
def testResponse7(shelveDict):
    print("\nTEST 7: Numbers - Special Variable")
    specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    a1 = functools.partial(responsebuilder.quotientOfTwoAction, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    quotientResponse = Response(["<number:num1>", "divided", "by", "<number:num2>"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(quotientResponse)
    responseBuilder.flushResponse()
    
def testResponse8(shelveDict):
    print("\nTEST 8: Numbers - Special Variable")
    specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    a1 = functools.partial(responsebuilder.powerOfTwoAction, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    powerResponse = Response(["<number:num1>", "power",  "<number:num2>"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(powerResponse)
    responseBuilder.flushResponse()
    
def testResponse9(shelveDict):
    print("\nTEST 9: Numbers - Special Variable")
    specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    a1 = functools.partial(responsebuilder.rootOfTwoAction, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    rootResponse = Response(["<number:num1>", "root",  "<number:num2>"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(rootResponse)
    responseBuilder.flushResponse()
    
#~ def testResponse10(shelveDict): #GOOGLE ONLY
    #~ print("\nTEST 10: Weather Check")
    #~ specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    #~ a1 = functools.partial(responsebuilder.weatherCheck, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    #~ weatherResponse = Response(["how", "is",  "the", "weather", "today"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    #~ 
    #~ print("\nAdd to the shelve dictionary")
    #~ responseBuilder = ResponseBuilder(shelveDict)
    #~ responseBuilder.addResponse(weatherResponse)
    #~ responseBuilder.flushResponse()
    #~ 
#~ def testResponse11(shelveDict): #OFFLINE ONLY
    #~ print("\nTEST 11: Lights On")
    #~ specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    #~ a1 = functools.partial(responsebuilder.lightsOn, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    #~ lightsResponse = Response(["turn", "on", "the", "lights"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    #~ 
    #~ print("\nAdd to the shelve dictionary")
    #~ responseBuilder = ResponseBuilder(shelveDict)
    #~ responseBuilder.addResponse(lightsResponse)
    #~ responseBuilder.flushResponse()

#~ def testResponse12(shelveDict): #OFFLINE ONLY
    #~ print("\nTEST 12: Lights Off")
    #~ specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    #~ a1 = functools.partial(responsebuilder.lightsOff, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    #~ lightsResponse = Response(["turn", "off", "the", "lights"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    #~ 
    #~ print("\nAdd to the shelve dictionary")
    #~ responseBuilder = ResponseBuilder(shelveDict)
    #~ responseBuilder.addResponse(lightsResponse)
    #~ responseBuilder.flushResponse()
    
def testResponse13(shelveDict):
    print("\nTEST 13: Celsius to Fahrenheit Converter")
    specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    a1 = functools.partial(responsebuilder.celsiusToFahrenheit, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    cToFResponse = Response(["celsius", "<number:num1>", "fahrenheit"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(cToFResponse)
    responseBuilder.flushResponse()
    
def testResponse14(shelveDict):
    print("\nTEST 14: Fahrenheit to Celsius Converter")
    specialVars = {} #Create a dictionary object, which will be passed into a function object that will be added as an action to a response
    a1 = functools.partial(responsebuilder.fahrenheitToCelsius, specialVars) #Creates a function object of the function 'sumOfTwoAction' without executing it
    fToCResponse = Response(["fahrenheit", "<number:num1>", "celsius"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(fToCResponse)
    responseBuilder.flushResponse()

def linphoneCallResponse(shelveDict):
    print("\nLinphone Call Command Test")
    specialVars = {}
    a1 = functools.partial(responsebuilder.linphoneCall, specialVars)
    linphoneCommandResponse = Response(["call", "<any:linphoneName>"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.LINPHONE, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(linphoneCommandResponse)
    responseBuilder.flushResponse()
    
def endLinphoneCallResponse(shelveDict):
    print("\nLinphone End Call Command Test")
    specialVars = {}
    a1 = functools.partial(responsebuilder.linphoneEndCall, specialVars)
    linphoneCommandResponse = Response(["end", "call"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.LINPHONE, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(linphoneCommandResponse)
    responseBuilder.flushResponse()
    
def acceptLinphoneCallResponse(shelveDict):
    print("\nLinphone Accept Call Command Test")
    specialVars = {}
    specialVars2 = {}
    a1 = functools.partial(responsebuilder.acceptCall, specialVars)
    linphoneCommandResponse = Response(["except", "call"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.LINPHONE, specialVars)
    linphoneCommandResponse2 = Response(["accept", "call"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.LINPHONE, specialVars2)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(linphoneCommandResponse)
    responseBuilder.addResponse(linphoneCommandResponse2)
    responseBuilder.flushResponse()
    
def declineLinphoneCallResponse(shelveDict):
    print("\nLinphone Decline Call Command Test")
    specialVars = {}
    a1 = functools.partial(responsebuilder.declineCall, specialVars)
    linphoneCommandResponse = Response(["decline", "call"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.LINPHONE, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(linphoneCommandResponse)
    responseBuilder.flushResponse()
    
def stopOutgoingLinphoneCallResponse(shelveDict):
    print("\nLinphone Stop Outgoing Call Command Test")
    specialVars = {}
    a1 = functools.partial(responsebuilder.stopOutgoingCall, specialVars)
    linphoneCommandResponse = Response(["stop", "call"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.LINPHONE, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(linphoneCommandResponse)
    responseBuilder.flushResponse()

def turnLights1On(shelveDict):
    print("Colored Lights On Response")
    a1 = functools.partial(GPIO.output, 14, GPIO.HIGH)
    respo = Response(["first", "lights", "on"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(respo)
    responseBuilder.flushResponse()
    
def turnLights1Off(shelveDict):
    print("Colored Lights Off Response")
    a1 = functools.partial(GPIO.output, 14, GPIO.LOW)
    respo = Response(["first", "lights", "off"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(respo)
    responseBuilder.flushResponse()

def turnLights2On(shelveDict):
    print("Light Bulb On Response")
    a1 = functools.partial(GPIO.output, 15, GPIO.HIGH)
    respo = Response(["second", "lights", "on"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(respo)
    responseBuilder.flushResponse()
    
def turnLights2Off(shelveDict):
    print("Light Bulb Off Response")
    a1 = functools.partial(GPIO.output, 15, GPIO.LOW)
    respo = Response(["second", "lights", "off"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(respo)
    responseBuilder.flushResponse()
    
def turnOutletOn(shelveDict):
    print("Outlet On Response")
    a1 = functools.partial(GPIO.output, 18, GPIO.HIGH)
    respo = Response(["outlet", "on"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(respo)
    responseBuilder.flushResponse()
    
def turnOutletOff(shelveDict):
    print("Outlet Off Response")
    a1 = functools.partial(GPIO.output, 18, GPIO.LOW)
    respo = Response(["outlet", "off"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(respo)
    responseBuilder.flushResponse()

def playMedia(shelveDict):
    print("Play Audio Single / Playlist Shuffle Response")
    specialVars = {}
    a1 = functools.partial(responsebuilder.playAudioOrPlaylist, specialVars)
    playMediaResponse = Response(["play", "<any:audioOrPlaylistName>"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.AUDIO, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(playMediaResponse)
    responseBuilder.flushResponse()

def stopMedia(shelveDict):
    print("Stop Audio/Playlist Response")
    specialVars = {}
    a1 = functools.partial(responsebuilder.stopMediaAction, specialVars)
    stopMediaResponse = Response(["stop", "music"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.AUDIO, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(stopMediaResponse)
    responseBuilder.flushResponse()

def pauseMedia(shelveDict):
    print("Play/Pause Audio/Playlist Response")
    specialVars = {}
    a1 = functools.partial(responsebuilder.pauseMediaAction, specialVars)
    stopMediaResponse = Response(["pause", "music"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.AUDIO, specialVars)
    stopMediaResponse2 = Response(["play", "music"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.AUDIO, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(stopMediaResponse)
    responseBuilder.addResponse(stopMediaResponse2)
    responseBuilder.flushResponse()
    
def changeVolume(shelveDict):
    print("Change Volume Response")
    specialVars = {}
    a1 = functools.partial(responsebuilder.changeVolumeAction, specialVars)
    volumeLevelResponse = Response(["volume", "<any:volumelevel>"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.AUDIO, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(volumeLevelResponse)
    responseBuilder.flushResponse()

def rebootResponse(shelveDict):
    print("Reboot Raspberry Pi Response")
    specialVars = {}
    a1 = responsebuilder.rebootSystem
    rebootSystemResponse = Response(["reboot", "system"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    rebootSystemResponse2 = Response(["restart", "system"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(rebootSystemResponse)
    responseBuilder.addResponse(rebootSystemResponse2)
    responseBuilder.flushResponse()
    
def shutdownResponse(shelveDict):
    print("Shutdown Raspberry Pi Response")
    specialVars = {}
    a1 = responsebuilder.poweroffSystem
    shutdownSystemResponse = Response(["shutdown", "system"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    shutdownSystemResponse2 = Response(["power", "off", "system"], [a1], ResponseSwitch.OFFLINE_ONLY, ResponseType.NORMAL, specialVars)
    
    print("\nAdd to the shelve dictionary")
    responseBuilder = ResponseBuilder(shelveDict)
    responseBuilder.addResponse(shutdownSystemResponse)
    responseBuilder.addResponse(shutdownSystemResponse2)
    responseBuilder.flushResponse()
    
#For Testing/Building the Responses
if __name__ == "__main__":
    """
    List of used shelve dictionary variables (you cannot reuse this keys from the shelve):
    shelveDict["responses"]    -- stores the responses
    shelveDict["previousText"] -- stores the previously recognized words decoded by the STT Engine ((Google Assistant or CMU Sphinx)
    
    List of used specialVars. You cannot use this as a special variable name when creating a Response.
    specialVars["linphoneBase"] -- stores the main LinphoneBase object created upon startup
    specialVars["playlistName"] -- stores the playlist created upon startup
    """
    
    os.system("sudo rm scripts.d")
    
    shelveDict = shelve.open("scripts.d")
    testResponse(shelveDict)
    testResponse2(shelveDict)
    testResponse3(shelveDict)
    testResponse4(shelveDict)
    testResponse5(shelveDict)
    testResponse6(shelveDict)
    testResponse7(shelveDict)
    testResponse8(shelveDict)
    testResponse9(shelveDict)
    #~ testResponse10(shelveDict)
    #~ testResponse11(shelveDict)
    #~ testResponse12(shelveDict)
    testResponse13(shelveDict)
    testResponse14(shelveDict)
    
    #~ LinponeCalls
    linphoneCallResponse(shelveDict)
    endLinphoneCallResponse(shelveDict)
    acceptLinphoneCallResponse(shelveDict)
    declineLinphoneCallResponse(shelveDict)
    stopOutgoingLinphoneCallResponse(shelveDict)
    
    #~ 220 Volt Appliances Responses
    turnLights1On(shelveDict)
    turnLights1Off(shelveDict)
    turnLights2On(shelveDict)
    turnLights2Off(shelveDict)
    turnOutletOn(shelveDict)
    turnOutletOff(shelveDict)
    
    #~ 220 Volt Appliances Responses
    playMedia(shelveDict)
    stopMedia(shelveDict)
    pauseMedia(shelveDict)
    changeVolume(shelveDict)
    
    # OS Command Responses
    rebootResponse(shelveDict)
    shutdownResponse(shelveDict)
