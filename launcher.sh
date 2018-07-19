#!/bin/sh
# launcher.sh

sleep 5
cd /home/pi/Documents/VoiceAssistant
python -m py_compile voice_assistant.py
python voice_assistant.py
