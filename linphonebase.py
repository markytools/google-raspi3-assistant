#!/usr/bin/env python

import linphone
import logging
import signal
import time
from multiprocessing import Manager
from threading import Timer
from tools.mediaplayer import playURLLoop

class LinphoneBase:
    def __init__(self, username='', password='', whitelist=[], camera='', snd_capture='', snd_playback='', dictProxy=None):
        self.username = username
        self.password = password
        self.whitelist = whitelist
        self.camera = camera
        self.snd_capture = snd_capture
        self.snd_playback = snd_playback
        self.core = None
        self.dictProxy = dictProxy
    
    def setup(self):
        self.quit = False
        callbacks = linphone.Factory.get().create_core_cbs()
        callbacks.call_state_changed = self.call_state_changed

        # Configure the linphone core
        logging.basicConfig(level=logging.INFO)
        signal.signal(signal.SIGINT, self.signal_handler)
        linphone.set_log_handler(self.log_handler)
        self.core = linphone.Factory.get().create_core(callbacks, None, None)
        self.core.max_calls = 1
        self.core.echo_cancellation_enabled = False
        self.core.video_capture_enabled = False
        self.core.video_display_enabled = False
        self.core.nat_policy.stun_server = 'stun.linphone.org'
        self.core.nat_policy.ice_enabled = True
        if len(self.camera):
            self.core.video_device = self.camera
        if len(self.snd_capture):
            self.core.capture_device = self.snd_capture
        if len(self.snd_playback):
            self.core.playback_device = self.snd_playback

        self.configure_sip_account(self.username, self.password)
        
    def signal_handler(self, signal, frame):
        self.core.terminate_all_calls()
        self.quit = True
        
    def log_handler(self, level, msg):
        method = getattr(logging, level)
        method(msg)
    
    def call_state_changed(self, core, call, state, message):
        print("state is: " + str(state))
        if call: self.currentCall = call
        if state == linphone.CallState.IncomingReceived:
            self.dictProxy["loopURL"] = "/home/pi/Documents/VoiceAssistant/sounds/phonering.mp3"
            self.dictProxy["playloop"] = 1
            self.dictProxy["incomingCall"] = 1
        elif state == linphone.CallState.OutgoingRinging:
            self.dictProxy["loopURL"] = "/home/pi/Documents/VoiceAssistant/sounds/phonecall.mp3"
            self.dictProxy["playloop"] = 1
        elif state == linphone.CallState.Connected:
            self.dictProxy["stopmedia"] = 1
            self.dictProxy["incomingCall"] = 0
            self.dictProxy["ongoingCall"] = 1
        elif state == linphone.CallState.End:
            print(call.reason)
        elif state == linphone.CallState.Released:
            self.dictProxy["incomingCall"] = 0
            self.dictProxy["stopmedia"] = 1
            self.dictProxy["ongoingCall"] = 0
            
            try:
                self.core.decline_call(self.currentCall, linphone.Reason.Declined)
                chat_room = self.core.get_chat_room_from_uri(str(self.dictProxy["currentCalledSIP"]))
                msg = chat_room.create_message(self.currentCall.remote_address_as_string + ' tried to call')
                if hasattr(chat_room, 'send_chat_message'): chat_room.send_chat_message(msg)
                del self.currentCall
                del chat_room
                del msg
            finally: pass
        #~ if state == linphone.CallState.IncomingReceived:
           #~ if call.remote_address.as_string_uri_only() in self.whitelist:
            #~ params = core.create_call_params(call)
            #~ core.accept_call_with_params(call, params)
        #~ else:
            #~ core.decline_call(call, linphone.Reason.Declined)
            #~ chat_room = core.get_chat_room_from_uri(self.whitelist[0])
            #~ msg = chat_room.create_message(call.remote_address_as_string + ' tried to call')
            #~ chat_room.send_chat_message(msg)
            
    def configure_sip_account(self, username, password):
        # Configure the SIP account
        proxy_cfg = self.core.create_proxy_config()
        proxy_cfg.identity_address = self.core.create_address('sip:{username}@sip.linphone.org'.format(username=username))
        proxy_cfg.server_addr = 'sip:sip.linphone.org;transport=tls'
        proxy_cfg.register_enabled = True
        self.core.add_proxy_config(proxy_cfg)
        auth_info = self.core.create_auth_info(username, None, password, None, None, 'sip.linphone.org')
        self.core.add_auth_info(auth_info)
    
    def endCall(self):
        """Call this when you want to terminate all calls"""
        self.core.terminate_all_calls()
        
    def startTestCall(self):
        print("starting to call android...")
        self.core.invite('sip:markaty@sip.linphone.org')
    
    def callLinphoneSIP(self, sipAccount):
        """Call this function to call a specific Linphone SIP Account.
        Args:
        sipAccount -- the SIP Account to be called
        """
        self.dictProxy["currentCalledSIP"] = 'sip:' + sipAccount
        self.core.invite(self.dictProxy["currentCalledSIP"])
    
    def run(self):
        #~ Timer(5, self.startTestCall).start()
        #~ self.core.invite('sip:markaty@sip.linphone.org')
        while not self.quit:
            self.core.iterate()
            self.executeCommands()
            time.sleep(0.03)
    
    def executeCommands(self):
        if self.dictProxy["sipnametocall"] != None:
            sipname = self.dictProxy["sipnametocall"]
            self.dictProxy["sipnametocall"] = None
            self.callLinphoneSIP(sipname)
        if self.dictProxy["endlinphonecall"] != None:
            self.dictProxy["endlinphonecall"] = None
            self.endCall()
        if self.dictProxy["incomingCall"] == 2:
            self.dictProxy["incomingCall"] = 0
            self.dictProxy["stopmedia"] = 1
            params = self.core.create_call_params(self.currentCall)
            self.core.accept_call_with_params(self.currentCall, params)
        elif self.dictProxy["incomingCall"] == -1:
            self.dictProxy["incomingCall"] = 0
            self.dictProxy["stopmedia"] = 1
            try:
                self.core.decline_call(self.currentCall, linphone.Reason.Declined)
                chat_room = self.core.get_chat_room_from_uri(str(self.dictProxy["currentCalledSIP"]))
                msg = chat_room.create_message(self.currentCall.remote_address_as_string + ' tried to call')
                if hasattr(chat_room, 'send_chat_message'): chat_room.send_chat_message(msg)
                del self.currentCall
                del chat_room
                del msg
            finally: pass
        if self.dictProxy["stopOugoingCall"] == 1:
            self.dictProxy["stopOugoingCall"] = 0
            self.core.stop_ringing()
            self.endCall()

def runLinphoneBase(d, linphoneQueue, linphoneBase):
    linphoneBase.setup()
    linphoneBase.run()
    
#~ def runLinphoneBase():
    #~ linphoneBase = LinphoneBase(username='markytools', password='password', whitelist=['sip:markytools@sip.linphone.org', 'sip:markaty@sip.linphone.org', 'sip:slylilytestacct@sip.linphone.org'], camera='', snd_capture='ALSA: default device', snd_playback='ALSA: default device')
    #~ linphoneBase.run()

if __name__ == '__main__':
    getLinphoneBase().run()
