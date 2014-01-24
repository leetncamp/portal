#!/usr/bin/env python
import os, sys
from pdb import set_trace as debug
import zlib
from MultipartPostHandler import MultipartPostHandler
#pip install requests
import requests
import hashlib
import json
import math


chunkSize = 1000000
url = "http://localhost:8000/bupload"

def chunks(fileObj):
    cont = True
    while cont:
        chunk = "".join(fileObj.readlines(chunkSize))
        cont = chunk != ''
        yield(zlib.compress(chunk))


#Get the length of the EEG file and the number of chunks that will be sent.
eegFile = open("EEG.txt", "r")
eegFile.seek(0, 2)
length = eegFile.tell()
nChunks = int(math.ceil(length / float(chunkSize)))
eegFile.seek(0)

#Tell the server that we are starting so we don't append to an existing file.
files = {'reset': ('reset', "Uploaded-" + eegFile.name )}
req = requests.post(url, files=files)
print json.loads(req.text)['status']

for chunk in chunks(eegFile):
    md5sum = hashlib.md5(chunk).hexdigest()
    files = {'file': ('fullChunk', chunk ), 'md5sum': ('md5sum', md5sum)}
    files['filename'] = "Uploaded-" + eegFile.name
    req = requests.post(url, files=files)
    result = json.loads(req.text)
    print result['status']
    
