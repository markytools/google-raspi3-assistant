#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from enum import Enum
from word2number import w2n

KeywordCheckerFeedback = Enum('KeywordCheckerFeedback', 'MATCH MISMATCH PASS')

#~ def getNumberKeyword(specialVars, varName, keywords, triggers, startInd):
    #~ """Special function that parses a given list of detected words and tries to convert it into a numberic value.
    #~ Args:
    #~ specialVars -- list from the response
    #~ varName     -- the string key of the specialVar
    #~ keywords    -- the list of words detected from the STT Engine (not the keywords from the sript.d)
    #~ startInd    -- starting index of the detected <number:varName> format from the keywords list
    #~ """
    #~ numberStr = ""
    #~ end = len(keywords) - 1
    #~ currentInd = startInd
    #~ if startInd == len(keywords) - 1: numberStr = keywords[currentInd]
    #~ else:
        #~ nextStr = keywords[]
    #~ return NumberChecker(start, end, numberStr)
    
def find_between_r(s, first, last):
    try:
        start = s.rindex(first) + len(first)
        end = s.rindex(last, start)
        return s[start:end]
    except ValueError:
        return ""
        
class NumberChecker(object):
    def __init__(self, start, end, strVal):
        """Stores the details after checking a string using word2num. It stores the start and end index, and the decoded number in int or float format.
        
        Args:
        start  -- start index of the word list decoded (not the keyword list)
        end    -- end index of the word list decoded (not the keyword list)
        strVal -- the string that will be decoded using the word2num
        """
        self.start = start
        self.end = end
        try:
            self.number = w2n.word_to_num(strVal)
        except ValueError:
            self.number = None
    
    def getDecodedNumber(self):
        return self.number

def changeWordsToNumber(words):
    try:
        realNum = w2n.word_to_num(words)
    except ValueError:
        realNum = None
    return realNum
        
class Node(object):
    def __init__(self, word=None, val=None):
        self.word = word
        self.val = val
        self.nodes = {}
        self.hasNumber = False
        self.hasAny = False
        self.numWords = ""
        self.anyWords = ""
        self.numVar = ""
    
    def addNode(self, word):
        if "<number:" in word:
            self.hasNumber = True
            self.nodes["<number>"] = Node("<number>")
            self.numVar = find_between_r(word, ":", ">")
        elif "<any:" in word:
            self.hasAny = True
            self.nodes["<any>"] = Node("<any>")
            self.anyVar = find_between_r(word, ":", ">")
        else: self.nodes[word] = Node(word)   #TODO
        
    def getNode(self, word):
        if "<number:" in word:
            if self.hasNumber: return self.nodes["<number>"]
        elif "<any:" in word:
            if self.hasAny: return self.nodes["<any>"]
        return self.nodes[word]
    
    def addToNumWordsAndValidate(self, specialVars, word, nextTrigger):
        """Adds the word to the total string that will be parsed into a number.
        Args:
        word        -- the word to be added that will be decoded
        specialVars -- the specialVars list that assigned to the Response object that will be fetched right after
        nextTrigger -- the word on the next trigger list after the <number:key> trigger or None (end reached or another special word)
        
        Returns the number node to be traversed.
        """
        self.numWords += (word + " ")
        if nextTrigger is not None:
            if self.nodes["<number>"].hasNode(nextTrigger):
                val = changeWordsToNumber(self.numWords)
                specialVars[self.numVar] = val
                if val: return self.nodes["<number>"]
                else: return self
            else: return self
        else:
            val = changeWordsToNumber(self.numWords)
            specialVars[self.numVar] = val
            if val: return self.nodes["<number>"]
            else: return self
            
    def addToAnyWords(self, specialVars, word, nextTrigger):
        self.anyWords += (word + " ")
        if nextTrigger is not None:
            if self.nodes["<any>"].hasNode(nextTrigger):
                specialVars[self.anyVar] = self.anyWords
                if self.anyWords: return self.nodes["<any>"]
                else: return self
            else: return self
        else:
            specialVars[self.anyVar] = self.anyWords
            if self.anyWords: return self.nodes["<any>"]
            else: return self
            
    def hasNode(self, word=None):
        if "<number:" in word:
            return self.nodes.has_key("<number>")
        elif "<any:" in word:
            return self.nodes.has_key("<any>")
        return self.nodes.has_key(word)
        
    def reset(self):
        self.numWords = ""
        self.anyWords = ""
        
    def __repr__(self):
        return 'Node(word=%s, val=%s, numvar=%s, \nnodes=%s)\n' % (self.word, self.val, self.numVar, self.nodes)
        
class ResponseTrie(object):
    def __init__(self):
        self.root = Node(None, None)
        self.size = 0
        self.collectedNodes = []
    
    def insert(self, keywords, val):
        """Insert keywords from index 0 to N-1 into the top of the trie until the bottom, respectively.
        
        Args:
        keywords -- list of words
        val -- value for the keywords (any object type)
        """
        node = self.root
        for word in keywords:
            if not node.hasNode(word):
                node.addNode(word)
            node = node.getNode(word)
        if node.val is None: self.size += 1
        node.val = val
            
    def get(self, keywords):
        """Returns the value with keywords as the key.
        
        Args:
        keywords -- list of words; the key
        
        Returns None if nothing was found.
        """
        specialVars = {}
        node = self.root
        for idx, word in enumerate(keywords):
            if (node.hasNode(word)):
                self.collectedNodes.append(node)
                node = node.nodes[word]
            elif node.hasNumber:
                if idx == len(keywords) - 1:
                    numWordsValidation = node.addToNumWordsAndValidate(specialVars, word, None)
                    if node != numWordsValidation:
                        self.collectedNodes.append(node)
                    if numWordsValidation: node = numWordsValidation
                else:
                    numWordsValidation = node.addToNumWordsAndValidate(specialVars, word, keywords[idx + 1])
                    if node != numWordsValidation:
                        self.collectedNodes.append(node)
                    if numWordsValidation: node = numWordsValidation
            elif node.hasAny:
                if idx == len(keywords) - 1:
                    anyWordsNode = node.addToAnyWords(specialVars, word, None)
                    if node != anyWordsNode:
                        self.collectedNodes.append(node)
                        if anyWordsNode: node = anyWordsNode
                else:
                    anyWordsNode = node.addToAnyWords(specialVars, word, keywords[idx + 1])
                    if node != anyWordsNode:
                        self.collectedNodes.append(node)
                        if anyWordsNode: node = anyWordsNode
        val = node.val
        for nodeVal in self.collectedNodes:
            nodeVal.reset()
        if val is not None:
            #~ if specialVars.has_key("addend1") and specialVars.has_key("addend2"):
                #~ print("addend1 value:" + str(specialVars["addend1"]) + "   addend2 value:" + str(specialVars["addend2"]))
            #~ else: print("no addend keys")
            if val.specialVars is not None:
                val.specialVars.clear()
                for key, value in specialVars.iteritems():
                    val.specialVars[key] = value
            return val
        return None
        
    def hasKeywords(self, keywords):
        node = self.root
        for word in keywords:
            if not node.hasNode(word): return False
            node = node.nodes[word]
        if node.val is None: return False
        return True
    
    def size(self):
        return self.size
        
    def __repr__(self):
        return 'ResponseTrie(root=%s, size=%d)' % (self.root, self.size)
    
    def checkKeyword(self, word, keywords, ind):
        if word[0] == '<':
            return None
        else: return KeywordCheckerFeedback

if __name__ == "__main__":
    print(find_between_r("hello", "h", "l"))
    
    #~ trie = ResponseTrie()
    #~ trie.insert(["hello", "world"], "worldVal")
    #~ trie.insert(["hello", "assholse"], "assholeVal")
    #~ trie.insert(["playground", "hi"], "hiVal")
    #~ trie.insert(["hello"], "helloVal")
    #~ trie.insert(["playground", "hi"], "hiVal2")
    #~ print(trie)
    #~ print(trie.hasKeywords(["playground", "hi"]))
    #~ print(trie.get((" hello the worldsay hi assholse hi").split()))
