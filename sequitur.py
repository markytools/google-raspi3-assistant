#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""This is the Text-to-speech engine module. The only core function here is for the Pi to speak out audio given a string."""

import os
import utils

#~ array = ["Adam", "Eiberty", "Flas", "Zero"]
#~ newArray = utils.insertLineIntoArray(array, "Flash")
#~ print array
#~ subprocess.call("ngram-count -wbdiscount -interpolate -text corpus.txt -lm output.lm", shell=True)
#~ subprocess.Popen(["ngram-count","-wbdiscount","-interpolate","-text", "corpus.txt", "-lm", "output.lm"], shell=True, stdout=subprocess.PIPE)

os.system("~/Documents/CMUSphinx/SRILM/bin/armv7l/ngram-count -wbdiscount -interpolate -text corpus.txt -lm output.lm")
