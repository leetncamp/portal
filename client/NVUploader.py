#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
ZetCode Tkinter tutorial

In this script, we show how to
use the Scale widget.

author: Jan Bodnar
last modified: December 2010
website: www.zetcode.com
"""
from __future__ import division
from ttk import *
from Tkinter import Tk, BOTH, IntVar, StringVar, Text
from pdb import set_trace as debug
import glob
import time
import os
import sys
import math
import requests
import json
import zlib
import hashlib
import tkMessageBox
import datetime
import pytz
mytz=pytz.timezone("America/Los_Angeles")

chunkSize = 1000000
url = "http://localhost:8000/bupload"
verifyurl = "http://localhost:8000/verifyfile"

def now():
    return(datetime.datetime.utcnow().replace(tzinfo=pytz.utc))


logfile = file("upload.log", 'a')
def log(txt):

    logfile.write("{0} : {1}\n".format(now().astimezone(mytz), txt))
    logfile.flush()
    print txt

log("========================")
log(now())

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

class Main(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent)   
        self.parent = parent
        self.parent.title("Neurovigil Uploader")
        self.style = Style()
        self.patientID = StringVar()
        self.patientLabel = Label(self, text="Patient ID")
        self.patientLabel.place(x=10, y=10)
        self.userName = StringVar()
        self.userNameLabel = Label(self, text="User Name")
        self.userNameLabel.place(x=200, y=10)
        self.patientIDEntry = Entry(self, textvariable=self.patientID)
        self.patientIDEntry.place(x=10, y=30)
        self.userNameEntry = Entry(self, textvariable=self.userName)
        self.userNameEntry.place(x=200, y=30)
        self.patientNotes = StringVar()
        self.patientNotesEntry = Text(self)
        self.patientNotesEntry.config(width=50, height=10, bd=1, relief="sunken")
        self.patientNotesEntry.place(x=10, y=100)
        self.pb = Progressbar(self, mode='determinate')
        self.pb.place(x=13, y = 80, width=100)
        self.pack(fill=BOTH, expand=1)
        self.fileNames = StringVar()
        self.fileLabel = Label(self, textvariable=self.fileNames)
        self.fileLabel.place(x=13, y=270)
        self.currentFile = StringVar()
        self.currentFileLabel = Label(self, textvariable=self.currentFile)
        self.currentFileLabel.place(x=13, y=60)
        self.goButton = Button(self, command=self.go, text="Upload")
        self.goButton.place(x=10, y = 400)
        self.quitButton = Button(self, text="Quit", command=self.quit)
        self.quitButton.place(x=290, y=400)
        self.status = StringVar()
        self.statusLabel = Label(self, text="", border=1, relief="sunken", anchor="w", textvariable=self.status)
        self.statusLabel.pack(side="bottom", fill="x")
        self.pause = False
        self.parent.lift()
        self.parent.bind("<FocusOut>", self.saveAppConf)

    def saveAppConf(self, event=None):
        appConf['geometry'] = self.parent.geometry()
        appConf['patientID'] = self.patientID.get()
        appConf['userName'] = self.userName.get()
        json.dump(appConf, file(".uploader.conf", 'wb'))
        log("Wrote " + json.dumps(appConf))
        return()
    
    def widgetLeave(self, event):
        pass
    
    def quit(self):
        #If the quit button's text has been changed to pause.
        if self.quitButton['text'] == "Pause":
            self.pause = True
            return
        else:
            #Refresh the conf file before exiting.
            #store the current window position
            self.saveAppConf()
            log("Quitting")
            sys.exit(0)
    
    def set_filenames(self):
        self.fileNames.set("Files to upload\n=========\n\n" + "\n".join(self.fileGlob))
        self.parent.update()
        
    def go(self):
        self.saveAppConf()
        if self.patientID.get() == "":
            tkMessageBox.showwarning("Required information is missing", "Patient Name is required.")
            return
        self.quitButton['text'] = "Pause"
        self.goButton['state'] = "disabled"
        self.parent.update()
        folder = "{0}".format(self.patientID.get())
        num = len(self.fileGlob)
        count = 1
        for fn in self.fileGlob:
            #Check for a progress indicator
            self.currentFile.set(fn)
            eegFile = open(fn, 'rb')
            eegFile.seek(0, 2)
            length = eegFile.tell()
            eegFile.seek(0)
            nChunks = int(math.ceil(length / float(chunkSize)))
            #Check to see if this file can be resumed.
            self.status.set("Checking for resume information.")
            self.parent.update()
            files = {}
            files['file'] = eegFile.name
            files['chunkSize'] = str(chunkSize)
            req = requests.post(verifyurl, files=files)
            #open_req(req)
            try:
                verifyResult = json.loads(req.text)
            except ValueError:
                open_req(req)
            verifyLength = verifyResult['length']
            chunkManifest = verifyResult['conf']
            lenChunkManifest = len(chunkManifest)
            if lenChunkManifest == 0:
                log("Starting upload for {0}".format(eegFile.name))
            else:
                log("Resuming upload for {0}".format(eegFile.name))
            self.status.set("Uploading {0}".format(eegFile.name))
            self.parent.update()
            if verifyLength != length:
                self.pb['value'] = 0
                self.parent.update()
                count = 0
                for chunk in chunks(eegFile):
                    if not self.pause:
                        md5sum = hashlib.md5(chunk).hexdigest()
                        #The keys in conf are converted to str's by json
                        manifestMD5sum = chunkManifest.get(str(count), "")
                        if md5sum != manifestMD5sum:
                            files = {'file': ('fullChunk', chunk ), 'md5sum': ('md5sum', md5sum)}
                            files['filename'] = eegFile.name
                            files['folder'] = folder
                            files['count'] = str(count)
                            req = requests.post(url, files=files)
                            try:
                                result = json.loads(req.text)
                            except:
                                open_req(req)
                        else:
                            log("Skipping chunk {0}".format(count))
                        self.pb['value'] = (float(count) / nChunks) * 100
                        print((count / nChunks) * 100)
                        count += 1
                        self.parent.update()
                    else:
                        self.goButton['state'] = "enabled"
                        self.pause = False
                        return
            else:
                #Skip this entire file.
                self.pb['value'] = 100
                self.parent.update()
            self.status.set('Verifying...')
            self.parent.update()
            fullMD5 = hashlib.md5(eegFile.read()).hexdigest()
            eegFile.seek(0)
            files = {}
            files['file'] = eegFile.name
            files['fullMD5'] = fullMD5
            req = requests.post(verifyurl, files=files)
            if json.loads(req.text)['verified']:
                log("Verified upload of {0}".format(eegFile.name))
            #open_req(req)
                
            #Remove this filename from the list of filenames 
            #that need to be uploaded
            del self.fileGlob[self.fileGlob.index(fn)]
            self.set_filenames()
        self.quitButton['text'] = "Quit"
        self.goButton['text'] = "Done"
        self.status.set("All files uploaded. Press Quit to exit.")
        self.goButton['command'] = self.quit
        self.parent.update()
            
        
if __name__ == '__main__':
    #Set the current working directory to that of the executable.
    cwd = os.path.dirname(sys.argv[0])
    #If the executable is bundled, we might have to go up a level.
    if cwd.endswith("MacOS"):
        cwd = os.path.dirname(os.path.dirname(os.path.dirname(cwd)))
    #file("/tmp/cwd.txt", 'w').write(cwd)
    os.chdir(cwd)
    #Try to read in a configuration file containing the last window position
    #And any possible information about resuming an existing upload.

    try:
        appConf = json.load(open('.uploader.conf'))
    except IOError:
        appConf = {}
    root = Tk()
    ex = Main(root)
    root.geometry(appConf.get("geometry", "390x450+100+100"))
    ex.fileGlob = glob.glob("*.txt")
    ex.set_filenames()
    ex.patientID.set(appConf.get("patientID", ""))
    ex.userName.set(appConf.get("userName", ""))
    root.lift()
    root.mainloop()  
    log( ex.patientID.get())