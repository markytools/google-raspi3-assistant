#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import socket
import os
import sys
import psutil
import logging
import shelve
import re
from urllib2 import urlopen, URLError, HTTPError
from num2words import num2words

def is_connected():
    url = 'http://google.com/'
    try:
        response = urlopen(url, timeout=3)
    except HTTPError, e:
        print 'The server couldn\'t fulfill the request. Reason:', str(e.code)
    except URLError, e:
        print 'We failed to reach a server. Reason:', str(e.reason)
    else:
        html = response.read()
        return True
    return False
  
def restart_program(shelveDict):
    """Restarts the current program, with file objects and descriptors
       cleanup
    """
    shelveDict.close()
    try:
        p = psutil.Process(os.getpid())
        for handler in p.get_open_files() + p.connections():
            os.close(handler.fd)
    except Exception, e:
        #~ logging.error(e)
        pass

    python = sys.executable
    os.execl(python, python, *sys.argv)
    
def substringBeforeChar(strVal, char='\n'):
    """Returns the substring before the first character occurence (starting from the left)"""
    return strVal.partition(char)[0]
    
def binarySearch(array, target, low, high, delim):
    """Searches the target string value in the array using binary search.
    Arguments:
    target -- target string
    low -- lower index
    high -- higher index

    NOTE: Strings to be compared are delimeted by one single character (delim). The substring before the delimeter will be used for comparison.
    Returns the index of the array where target was inserted or -1 if target is already in the array.
    """
    middle = (low + high) / 2
    if substringBeforeChar(array[middle], delim) == substringBeforeChar(target, delim): return -1
    elif substringBeforeChar(array[middle], delim) < substringBeforeChar(target, delim):
        if low == middle: return low + 1
        return binarySearch(array, target, middle, high, delim)
    elif substringBeforeChar(array[middle], delim) > substringBeforeChar(target, delim):
        if low == middle: return low
        return binarySearch(array, target, low, middle, delim)
    
def insertLineIntoArray(array, target, delim):
    """Inserts a string line into an array using binary insert
    Arguments:
    line -- the line value in string format
    
    Returns the array with the inserted value
    """
    
    if (len(array) == 0): array.insert(0, target)
    else:
        indToInsert = binarySearch(array, target, 0, len(array), delim)
        if (indToInsert != -1): array.insert(indToInsert, target)
    return array
    
def flattenlist():
    return lambda l: [item for sublist in l for item in sublist]

def removeCharsFromStr(strVal, charsInString):
    """Returns the string without the characters except '-'
    
    Args:
    strVal -- the string to be filtered
    charsInString -- the characters to be filtered out of strVal (e.g. '!@#$')
    """
    
    str1 = re.sub('[!-]', ' ', strVal)
    return re.sub('[' + charsInString + ']', '', str1)
    
def getValidString(strVal):
    if strVal == "+": return "plus"
    if strVal == "-": return "minus"
    if strVal == "*": return "times"
    if not strVal: return None
    if (strHasNumber(strVal)):
        if (strIsOrdinal(strVal)):
            ordinalNum = re.findall('[0-9]+', strVal)[0]
            return num2words(int(ordinalNum), ordinal=True)
        elif is_number(strVal): return num2words(float(strVal))
        else: return None
    else: return strVal

def strHasNumber(strVal):
    for c in strVal:
        if len(re.findall('[0-9]+', c)) > 0: return True
    return False

def strIsOrdinal(strVal):
    return re.compile("[0-9]+[st|nd|rd|th]").match(strVal) != None
        
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        return False
  
if __name__ == '__main__':
    #~ print(str(is_connected()))
    #~ 
    #~ strVal = "word P HO NE ME"
    #~ print substringBeforeChar(strVal)
    #~ 
    #~ 
    #~ 
    #~ # Call readlines once (on initialization)
    #~ count = 0
    #~ with open("test/2670.dic", "r") as f:
        #~ strArr = f.readlines()
    #~ 
    #~ # Call truncate file recursively
    #~ with open("test/2670.dic", "w") as f:
        #~ while count < 10000:
            #~ if count == 100:
                #~ #strArr = insertLineIntoArray(strArr, "HOUSE(2) HA WO S\n", "\n")    #for dictionary
                #~ #strArr = insertLineIntoArray(strArr, "gone\n", "\n                  #for vocabulary
                #~ strVal = "".join(strArr)
                #~ f.write(strVal)
            #~ count += 1
            
            
    #~ print(removeCharsFromStr("hel lo!", "!@$ -"))
    #~ print(strIsOrdinal("-0.52th"))
    print(is_connected())
