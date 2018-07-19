#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import pyaudio
import wave
 
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 3
START = 6
END = 15
WAVE_OUTPUT_FILENAME = "myrecording.wav"

for k in range(START, END + 1):
    audio = pyaudio.PyAudio()
     
    # start Recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)
    print "recording (" + str(k) + ")..."
    frames = []
     
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow = False)
        frames.append(data)
    print "finished recording"
     
     
    # stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    filename = WAVE_OUTPUT_FILENAME[:-4] + str(k) + WAVE_OUTPUT_FILENAME[-4:]
    waveFile = wave.open(filename, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
