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
import glob
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
import pytz
import dateutil
from tzlocal import get_localzone
import traceback as tb

mytz = get_localzone()

chunkSize = 1000000
def now():
    return(datetime.datetime.utcnow().replace(tzinfo=mytz))


server = "https://upload.neurovigil.com"

try:
    if sys.argv[1] == "local":
        server = "http://localhost:8000"
except IndexError:
    pass



url = "{0}/bupload".format(server)
verifyurl = "{0}/verifyfile".format(server)


globRE = re.compile("eeg", re.I)
errors =  ""




#Set the current working directory to that of the executable.
cwd = os.path.dirname(os.path.abspath(sys.argv[0]))
#If the executable is bundled, we might have to go trim the path
cwd = cwd.split("NVU")[0]
os.chdir(cwd)

logfile = file("upload.log", 'a')

def log(txt):
    logfile.write("{0} : {1}\n".format(now().astimezone(mytz), txt))
    logfile.flush()
    #print txt

log("========================")
log(now())
log(cwd)
log(server)

def open_req(req):
    file('delme.html', "wb").write(req.text)
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
            
if __name__ == "__main__":    
    pass
