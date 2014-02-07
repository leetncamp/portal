#!/usr/bin/env python
from __future__ import division

VERSION = 0.9


import platform
import os
import sys
import re
nvRE = re.compile("NVUploader", re.I)

from pdb import set_trace as debug
if platform.uname()[0] == "Windows":
    import subprocess as sp
    #psutil doesn't necessarily have permission in Windows 7. Use tasklist.
    tasklist = sp.check_output("tasklist")
    nvs = nvRE.findall(tasklist)
    if len(nvs) > 1:
        print "Instance of NVUploader.exe already running"
        sys.exit(1)
    #Kill the Windows Splash screen.
else:    
    import psutil
    if len( [ p for p in psutil.process_iter() if "NVUploader" in p.name ] ) > 1:
        print "Instance already running."
        sys.exit(1)


import Tkinter as tk
import ttk
import re
from pdb import set_trace as debug
import time
import os
import math
import requests
import json
import pickle
import zlib
import hashlib
import tkMessageBox
import datetime
import dateutil
import traceback as tb
from dateutil.tz import gettz, tzlocal

localtimezoneStr = datetime.datetime.now(tzlocal()).tzname()



chunkSize = 1000000
def now():
    return(datetime.datetime.now().replace(tzinfo=tzlocal()))


server = "https://upload.neurovigil.com"

try:
    if sys.argv[1] == "local":
        server = "http://localhost:8000"
except IndexError:
    pass



url = "{0}/bupload".format(server)
verifyurl = "{0}/verify/{1}".format(server, VERSION)


globRE = re.compile("eeg", re.I)
errors =  ""




#Set the current working directory to that of the executable.
cwd = os.path.dirname(os.path.abspath(sys.argv[0]))
#If the executable is bundled, we might have to go trim the path
cwd = cwd.split("NVU")[0]
os.chdir(cwd)

logfile = file("upload.log", 'a')

def log(txt):
    logfile.write("{0} : {1}\n".format(now(), txt))
    logfile.flush()
    #print txt

log("========================")
log(now())
log(cwd)
log(server)

def open_req(req):
    debug()
    file('delme.html', "wb").write(req.text.encode('utf-8'))
    os.system("open delme.html")
    return

def chunks(fileObj):
    cont = True
    while cont:
        chunk = "".join(fileObj.readlines(chunkSize))
        cont = chunk != ''
        yield(zlib.compress(chunk))

class Catch():
    def __init__(self, instance):
        self.instance = instance
    def __enter__(self):
        return self.instance
    def __exit__(self, type, value, traceback):
        if type != None:
            global errors
            self.instance.quitButton['text'] = "Quit"
            log("Caught exception. Enabling the Quit and Upload buttons.")
            self.instance.goButton['state'] = 'enabled'
            self.instance.status.set("Problem uploading. You may press Upload again to retry.")
            log(type)
            errors += str(type) + "\n"
            log(value)
            errors += str(value) + "\n"
            log(tb.format_exc(traceback))
            errors += str(value) + "\n"

"""This is a prototype of the data structure that holds metadata about the
upload and about each file. Showing the structure of the file metadata just for
reference.

META = { 
    "uploadInfo": {
        "clinician": "",
        "company": "",
        "VERSION": VERSION
        "localtimezone": "America/Los_Angeles",
    },
    "files": [
        {"EEG.txt": {
            "length": 100,
            "header": "Neurovigil\nFirmwareVersion\n...",
            "uploaded": None,
            "notes": "These are the notes for this file.",
            "uploaded": datetimeobj,
            "md5sum": "string",
            "patientID": "string",
            "ctime": datetimeobj,
            "mtime": datetimeobj,
        }},
        {"EEG1.txt": {
            "length": 100,
            "header": "Neurovigil\nFirmwareVersion\n...",
            "uploaded": None,
            "notes": "These are the notes for this file.",
        }}
    ]
}
"""

"""This is the one that will actually get filled out with real file data"""

defaultMETA = { 
    "uploadInfo": {
        "clinician": "",
        "company": "",
        "VERSION": VERSION,
        "localtimezone": localtimezoneStr,
    },
    "files" : {},
}

def updateMeta(fileName):
    stat = os.stat(fileName)
    ctime = datetime.datetime.fromtimestamp(stat[9])
    mtime = datetime.datetime.fromtimestamp(stat[8])
    f = file(fileName, 'rb')
    #Read in the text header at the top of the file.
    head = f.read(1000)
    header = ""
    for line in head.split("\n"):
        try:
            header += line.encode('ascii') + "\n"
        except:
            #This will fail on the first line with binary data.
            break
    #Get the length of the file
    f.seek(0,2)
    length = f.tell()
    #Update the META object
    thisMeta = META['files'].get(fileName, {})
    thisMeta['ctime'] = ctime
    thisMeta['mtime'] = mtime
    thisMeta['length'] = length
    thisMeta['header'] = header
    META['files'][fileName] = thisMeta

def askCompany():
    from ask import ask_company
    return(ask_company())    
    
    
            
if __name__ == "__main__":
    try:
        META = pickle.load(file("metadata.pickle", "rb"))
    except Exception as e:
        META = defaultMETA
    if not META['uploadInfo'].get('company', ""):
        META['uploadInfo']['company'] = askCompany()
    debug() 
    fileList = [x for x in os.listdir(cwd) if re.match(globRE, x) ]
    for fileName in fileList:
        updateMeta(fileName)
    
    req = requests.post(verifyurl, files={"meta":pickle.dumps(META)})
    try:
        
        meta = pickle.loads(req.text.encode("utf-8"))
        message = meta.get('message', "")
        status = meta.get('status', "")
    except Exception as e:
        message = open_req(req)
        status = "unexpected result from server"
    print message
    print status
    print meta
    pickle.dump(meta, file("metadata.pickle", "wb"))
        
    
    
    
    
