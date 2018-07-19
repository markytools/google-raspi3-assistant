#!/usr/bin/env python

import linphone
import logging
import signal
import time
from threading import Timer

class LinphoneBase:
    def __init__(self, username='', password='', whitelist=[], camera='', snd_capture='', snd_playback=''):
        self.quit = False
        self.whitelist = whitelist
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
        if len(camera):
            self.core.video_device = camera
        if len(snd_capture):
            self.core.capture_device = snd_capture
        if len(snd_playback):
            self.core.playback_device = snd_playback
            
        #~ print 'List of Sound Devices' 
        #~ sound_devices = self.core.sound_devices
        #~ total_sound_devices = len(sound_devices)
        #~ for i in range(0, total_sound_devices):
        #~ print str(i) + sound_devices[i] + '  can be capture: ' + str(self.core.sound_device_can_capture(sound_devices[i]))
        #~ print 'End List of Sound Devices'

        self.configure_sip_account(username, password)
        
    def signal_handler(self, signal, frame):
        self.core.terminate_all_calls()
        self.quit = True
        
    def log_handler(self, level, msg):
        method = getattr(logging, level)
        method(msg)
    
    def call_state_changed(self, core, call, state, message):
        print()
        print()
        print()
        print("CHANGED")
        print("call state change: " + str(state))
        print()
        print()
        print()
        if state == linphone.CallState.IncomingReceived:
           if call.remote_address.as_string_uri_only() in self.whitelist:
            params = core.create_call_params(call)
            core.accept_call_with_params(call, params)
        else:
            core.decline_call(call, linphone.Reason.Declined)
            chat_room = core.get_chat_room_from_uri(self.whitelist[0])
            msg = chat_room.create_message(call.remote_address_as_string + ' tried to call')
            chat_room.send_chat_message(msg)
            
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
        print(str(type(self.core)))
        self.core.invite('sip:markaty@sip.linphone.org')
    
    def callLinphoneSIP(self, sipAccount):
        """Call this function to call a specific Linphone SIP Account.
        Args:
        sipAccount -- the SIP Account to be called
        """
        self.core.invite('sip:' + sipAccount)
    
    def run(self):
        #~ Timer(5, self.startTestCall).start()
        #~ self.core.invite('sip:markaty@sip.linphone.org')
        while not self.quit:
            self.core.iterate()
            time.sleep(0.03)

def getLinphoneBase():
    return LinphoneBase(username='markytools', password='password', whitelist=['sip:markytools@sip.linphone.org', 'sip:markaty@sip.linphone.org', 'sip:slylilytestacct@sip.linphone.org'], camera='', snd_capture='ALSA: default device', snd_playback='ALSA: default device')

def runLinphoneBase(d, linphoneQueue, linphoneBase):
    linphoneBase.run()
    
#~ def runLinphoneBase():
    #~ linphoneBase = LinphoneBase(username='markytools', password='password', whitelist=['sip:markytools@sip.linphone.org', 'sip:markaty@sip.linphone.org', 'sip:slylilytestacct@sip.linphone.org'], camera='', snd_capture='ALSA: default device', snd_playback='ALSA: default device')
    #~ linphoneBase.run()

if __name__ == '__main__':
    getLinphoneBase().run()
