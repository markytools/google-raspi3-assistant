#!/usr/bin/env python
from os import environ, path

from pocketsphinx import *
from sphinxbase import *

# Create a decoder with certain model
config = Decoder.default_config()
config.set_string('-hmm', '/home/pi/Documents/VoiceAssistant/acousticadaptation/noadaptation/en-us')
config.set_string('-lm', '/home/pi/Documents/VoiceAssistant/acousticadaptation/noadaptation/8983.lm')
config.set_string('-dict', '/home/pi/Documents/VoiceAssistant/acousticadaptation/noadaptation/8983.dic')
config.set_string('-logfn', '/dev/null')
decoder = Decoder(config)

import pyaudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=7, frames_per_buffer=1024)
stream.start_stream()

in_speech_bf = False
decoder.start_utt()
while True:
    buf = stream.read(1024, exception_on_overflow = False)
    if buf:
        decoder.process_raw(buf, False, False)
        if decoder.get_in_speech() != in_speech_bf:
            # This block activates once audio is acquired form the microphone
            in_speech_bf = decoder.get_in_speech()
            if not in_speech_bf:
                decoder.end_utt()
                # The resulting string can either be found in the dictionary or be blank
                print 'Result:', decoder.hyp().hypstr
                decoder.start_utt()
    else:
        break
stream.close()
decoder.end_utt()
p.terminate()
