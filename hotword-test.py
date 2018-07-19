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

from pocketsphinx import *
from sphinxbase import *

MODELDIR = "pocketsphinx/model"
DATADIR = "pocketsphinx/model"

import argparse
import os.path
import json
import sys
import signal

import google.oauth2.credentials

from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file


def process_event(event):
    """Pretty prints events.

    Prints all events that occur with two spaces between each new
    conversation and a single space between turns of a conversation.

    Args:
        event(event.Event): The current event to process.
    """
    if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        print()
    
    if event.type == EventType.ON_ASSISTANT_ERROR:
        print("Assistant Error Detected, Fatal: " + str(event.args['is_fatal']))

    print(event)

    if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
            event.args and not event.args['with_follow_on_turn']):
        print()

def restartAssistant(credentials):
    
    with Assistant(credentials) as assistant:
        for event in assistant.start():
            process_event(event)

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--credentials', type=existing_file,
                        metavar='OAUTH2_CREDENTIALS_FILE',
                        default=os.path.join(
                            os.path.expanduser('~/.config'),
                            'google-oauthlib-tool',
                            'credentials.json'
                        ),
                        help='Path to store and read OAuth2 credentials')
    args = parser.parse_args()
    with open(args.credentials, 'r') as f:
        credentials = google.oauth2.credentials.Credentials(token=None,
                                                            **json.load(f))
    
    retryProgramOnce = 1
    def sig_handler(signum, frame): 
        # Create a decoder with certain model
        if retryProgramOnce == 1:
            retryProgramOnce = 0
            config = Decoder.default_config()
            config.set_string('-hmm', path.join(DATADIR, 'en-us/en-us'))
            config.set_string('-lm', path.join(MODELDIR, 'en-us/7267.lm'))
            config.set_string('-dict', path.join(MODELDIR, 'en-us/7267.dic'))
            decoder = Decoder(config)

            import pyaudio
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
            stream.start_stream()

            in_speech_bf = False
            decoder.start_utt()
            while True:
                buf = stream.read(1024, exception_on_overflow = False)
                if buf:
                    decoder.process_raw(buf, False, False)
                    if decoder.get_in_speech() != in_speech_bf:
                        in_speech_bf = decoder.get_in_speech()
                        if not in_speech_bf:
                            decoder.end_utt()
                            print('Result:', decoder.hyp().hypstr)
                            decoder.start_utt()
                else:
                    break
            stream.close()
            decoder.end_utt()
            p.terminate()
    
            
    signal.signal(signal.SIGSEGV, sig_handler)
    
    restartAssistant(credentials)


if __name__ == '__main__':
    main()
