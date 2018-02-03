#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""response.py: The Response module represents the Assistant's basic response module."""
from enum import Enum
import functools
import response
import ttscontroller
from linphonebase import LinphoneBase
from multiprocessing import Process, Manager
#~ from responsebuilder import ResponseBuilder

ResponseType = Enum('ResponseType', 'NORMAL CHAIN_ONE CHAIN_MANY LINPHONE AUDIO')
ResponseSwitch = Enum('ResponseSwitch', 'GOOGLE_ONLY BOTH OFFLINE_ONLY')

class Response(object):
    """The base Response class template"""
    def __init__(self, triggers=[], actions=None, responseSwitch=ResponseSwitch.BOTH, responseType=ResponseType.NORMAL, specialVars=None):
        """Base Response constructor.
        Arguments:
		triggers         -- a list of string of word(s) that will act as keywords for detection
		actions          -- list of function objects ready to be called when all of the triggers return true
		responseSwitch   -- this corresponds to the execution of the responses by altering the flow of the Google Responses vs the Offline Responses 
        constrain        -- no other words except the keywords from the triggers list will activate this response
		responseType     -- the type of response
        specialVars      -- the dict object that will be updated whenever a special variable has been found
        """
        self.triggers = triggers
        self.actions = actions
        self.responseSwitch = responseSwitch
        self.responseType = responseType
        self.specialVars = specialVars
        self.onErrorActions = []
        self.chainTrie = None
        self.oneTimeResponse = None
    
    @property
    def responseType(self):
        return self._responseType
    
    @responseType.setter
    def responseType(self, responseType):
        if not isinstance(responseType, ResponseType): raise TypeError("Not a ResponseType type")
        self._responseType = responseType
    
    def executeActions(self, d=None, lock=None):
        for idx, action in enumerate(self.actions):
            if self.responseType == ResponseType.NORMAL:
                action()
            elif self.responseType == ResponseType.LINPHONE:
                self.specialVars["dictionaryproxy"] = d
                self.specialVars["managerlock"] = lock
                action()
            elif self.responseType == ResponseType.AUDIO:
                self.specialVars["dictionaryproxy"] = d
                self.specialVars["managerlock"] = lock
                action()
            else:
                action()
    def addSpecialVar(self, key, value):
        self.specialVars[key] = value
    
    def __repr__(self):
        return 'Response(trigger=%s, actions=%s, responseSwitch=%s, responseType=%s)' % (self.triggers, self.actions, self.responseSwitch, self.responseType)
	#~ @property
	#~ def state(self):
		#~ return self._state
	#~ 
	#~ @state.setter
	#~ def state(self, state):
		#~ if not isinstance(state, ResponseState): raise TypeError("Not a ResponseState type")
		#~ self._state = state
		#~ 
	#~ def executeActions(self):
		#~ for action in self.actions:
			#~ action()
#~ 
	#~ def __repr__(self):
		#~ return 'Response(trigger=%s, actions=%s, offlineOnly=%d, state=%s)' % (self.triggers, self.actions, self.offlineOnly, self.state)
    
		
class SimpleResponse(Response):
    """A Simple Response class that takes on a list of keywords as its trigger and a single string as its TTS response."""
    
    def __init__(self, triggers=[], actionWords="", lang="en-US", responseSwitch=ResponseSwitch.BOTH, responseType=ResponseType.NORMAL):
        """Constructor.
        
        Arguments:
		triggers     -- a list of string of word(s) that will act as keywords for detection
		actionsWords -- string comprising of words that will be executed by the TTS engine from the start to the end index
        """
        super(SimpleResponse, self).__init__(triggers, [functools.partial(response.speak, lang, actionWords)], responseSwitch, responseType)
        self.actionWords = actionWords
        self.lang = lang

#~ class ChainResponse(Response):
    #~ def __init__(self, )

def speak(lang="en-US", text=""):
    ttscontroller.speak(lang, text)

#For Testing
if __name__ == "__main__":
    simpleRespo = SimpleResponse(["hello"], "hello", "en-US", ResponseSwitch.BOTH, ResponseType.NORMAL)
    print(simpleRespo.constrain)
