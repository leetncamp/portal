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
from Tkinter import Tk, BOTH, IntVar, StringVar
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

chunkSize = 1000000
url = "http://localhost:8000/bupload"
verifyurl = "http://localhost:8000/verifyfile"

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
        self.patientName = StringVar()
        self.patientLabel = Label(self, text="Patient Name")
        self.patientLabel.place(x=10, y=10)
        self.entry = Entry(self, textvariable=self.patientName)
        self.entry.place(x=10, y=30)
        self.pb = Progressbar(self, mode='determinate')
        self.pb.place(x=13, y = 80, width=100)
        self.pack(fill=BOTH, expand=1)
        self.fileNames = StringVar()
        self.fileLabel = Label(self, textvariable=self.fileNames)
        self.fileLabel.place(x=13, y=120)
        self.currentFile = StringVar()
        self.currentFileLabel = Label(self, textvariable=self.currentFile)
        self.currentFileLabel.place(x=13, y=60)
        self.goButton = Button(self, command=self.go, text="Upload")
        self.goButton.place(x=10, y = 400)
        self.quitButton = Button(self, text="Quit", command=self.quit)
        self.quitButton.place(x=200, y=400)
        self.pause = False
        self.parent.lift()
    
    def quit(self):
        if self.quitButton['text'] == "Pause":
            self.pause = True
            return
        #Refresh the conf file before exiting.
        #store the current window position
        conf['geometry'] = self.parent.geometry()
        json.dump(conf, file(".uploader.conf", 'wb'))
        sys.exit(0)
    
    def set_filenames(self):
        self.fileNames.set("Files to upload\n=========\n\n" + "\n".join(self.fileGlob))
        self.parent.update()
        
    def go(self):
        if self.patientName.get() == "":
            tkMessageBox.showwarning("Required information is missing", "Patient Name is required.")
            return
        self.quitButton['text'] = "Pause"
        self.goButton['state'] = "disabled"
        self.parent.update()
        folder = "{0}".format(self.patientName.get())
        num = len(self.fileGlob)
        count = 1
        for fn in self.fileGlob:
            #Check for a progress indicator
            self.currentFile.set(fn)
            eegFile = open(fn, 'rb')
            eegFile.seek(0, 2)
            length = eegFile.tell()
            nChunks = int(math.ceil(length / float(chunkSize)))
            eegFile.seek(0)
            #Check to see if this file can be resumed.
            fullMD5 = hashlib.md5(eegFile.read()).hexdigest()
            eegFile.seek(0)
            files = {'fullMD5': ('fullMD5', fullMD5)}
            files['file'] = eegFile.name
            files['chunkSize'] = str(chunkSize)
            req = requests.post(verifyurl, files=files)
            open_req(req)
            verifyResult = json.loads(req.text)
            chunkManifest = verifyResult['conf']
            if verifyResult['status'] == "upload-needed":
                self.pb['value'] = 0
                self.parent.update()
                count = 0
                for chunk in chunks(eegFile):
                    if not self.pause:
                        md5sum = hashlib.md5(chunk).hexdigest()
                        #The keys in conf are converted to str's by json
                        manifestMD5sum = chunkManifest.get(str(count), "")
                        debug()
                        if md5sum != manifestMD5sum:
                            files = {'file': ('fullChunk', chunk ), 'md5sum': ('md5sum', md5sum)}
                            files['filename'] = eegFile.name
                            files['folder'] = folder
                            files['count'] = str(count)
                            req = requests.post(url, files=files)
                            result = json.loads(req.text)
                        else:
                            print("Skipping chunk {0}".format(chunk))
                        self.pb['value'] = (float(count) / nChunks) * 100
                        print (count / nChunks) * 100
                        count += 1
                        self.parent.update()
                    else:
                        self.goButton['state'] = "enabled"
                        self.pause = False
                        return
                #Remove this filename from the list of filenames 
                #that need to be uploaded
            del self.fileGlob[self.fileGlob.index(fn)]
            self.set_filenames()
        self.quitButton['text'] = "Quit"
        self.goButton['text'] = "Done"
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
        conf = json.load(open('.uploader.conf'))
    except IOError:
        conf = {}
    root = Tk()
    ex = Main(root)
    root.geometry(conf.get("geometry", "300x450+100+100"))
    ex.fileGlob = glob.glob("*.txt")
    ex.set_filenames()
    ex.patientName.set("asdf")
    root.lift()
    root.mainloop()  
    print ex.patientName.get()