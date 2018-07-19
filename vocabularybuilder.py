#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Do not edit any code from this module!

How to use: Edit the corpus.txt file. Do not change the text file's name. Add words to it without symbols. Make sure there are no
whitespaces on every line. After that, just run this file, wait for G2P to load, then watch each words get translated into its phonemes.
"""

from g2p_seq2seq import g2p
import os
import utils

#~ Initialize files
corpusArr = []
with open("google-assistant.vocab", "r") as f:
    vocabStrArr = f.readlines()
with open("google-assistant.dic", "r") as f:
    dicStrArr = f.readlines()
with open("corpus.txt", "r") as f:
    for line in f:
        line = line.replace('\n', '')
        corpusArr.append(line)

print corpusArr

with g2p.tf.Graph().as_default():
    """G2P only receives lowercase words"""
    model_dir = "g2p-seq2seq-cmudict"
    g2p_model = g2p.G2PModel(model_dir)
    g2p_model.load_decode_model()
    
    for word in corpusArr:
        vocabStrArr = utils.insertLineIntoArray(vocabStrArr, word + "\n", "\n")
        strVal1 = "".join(vocabStrArr)
        
        phoneme_lines = g2p_model.decode([word])
        dicStrArr = utils.insertLineIntoArray(dicStrArr, word + " " + phoneme_lines[0] + "\n", " ")
        strVal2 = "".join(dicStrArr)
    
    with open("google-assistant.vocab", "w") as f1:
        f1.write(strVal1)
    
    with open("google-assistant.dic", "w") as f2:
        f2.write(strVal2)
    
    with open("google-assistant.vocab", "r") as f:
        filecontents1 = f.readlines();
    with open("customcommands.txt", "r") as f:
        filecontents1 = filecontents1 + f.readlines()
    with open('customvocab.vocab', 'w') as f:
        for item in filecontents1:
            f.write("%s" % item)
    os.system("sudo ~/Documents/CMUSphinx/SRILM/bin/armv7l/ngram-count -wbdiscount -interpolate -text customvocab.vocab -lm google-assistant.lm")
    #~ os.system("sudo ~/Documents/CMUSphinx/SRILM/bin/armv7l/ngram-count -wbdiscount -interpolate -text google-assistant.vocab -lm google-assistant.lm")
