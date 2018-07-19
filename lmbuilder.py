#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import os.path

with open("google-assistant.vocab", "r") as f:
    filecontents1 = f.readlines();
with open("customcommands.txt", "r") as f:
    filecontents1 = filecontents1 + f.readlines()
with open('customvocab.vocab', 'w') as f:
    for item in filecontents1:
        f.write("%s" % item)
os.system("sudo ~/Documents/CMUSphinx/SRILM/bin/armv7l/ngram-count -wbdiscount -interpolate -text customvocab.vocab -lm google-assistant.lm")
print "done"
