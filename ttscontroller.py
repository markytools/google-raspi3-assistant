#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""This is the Text-to-speech engine module. The only core function here is for the Pi to speak out audio given a string."""

import os

def speak(lang="en-US", text=""):
    """Function to make the Pi speak
    
    Arguments:
    lang -- the language (default: English)
    text -- the text string to be spoken
    """
    os.system("pico2wave -w tts-output.wav -l " + lang + " \"" + text + "\" && aplay tts-output.wav")

if __name__ == '__main__':
    lang = "en-US"
    text = "Sorry, please try again.''"
    os.system("pico2wave -w tts-output.wav -l " + lang + " \"" + text + "\" && aplay tts-output.wav")
