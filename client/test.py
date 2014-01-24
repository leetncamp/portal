#!/usr/bin/env python
import os, sys
import urllib, urllib2
import re
from pdb import set_trace as debug
import zlib
import array
from MultipartPostHandler import MultipartPostHandler
import fileinput
#pip install requests
import requests
#Readup on FileInput
import md5
import json


RE = re.compile("(\d\d\d\d);")

eeg = open("EEG.txt", "r").read()
numbers = [ int(x) for x in RE.findall(eeg) ]
del eeg
compactArray = array.array("H", numbers)
del numbers
url = "http://localhost:8000/bupload"
compressedStr = zlib.compress(compactArray.tostring())
md5sum =  md5.new(compressedStr).hexdigest()
files = {'file': ('fullChunk', compressedStr ), 'md5sum': ('md5sum', md5sum)}
req = requests.post(url, files=files)
result = json.loads(req.text)
print result['success']


