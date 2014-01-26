#!/usr/bin/env python
from __future__ import division


from pdb import set_trace as debug
import Tkinter as tk
import ttk

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
import traceback as tb

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


class Catch():
    def __init__(self, instance):

        self.instance = instance
    def __enter__(self):
        return self.instance
    def __exit__(self, type, value, traceback):
        if type != None:
            self.instance.quitButton['text'] = "Quit"
            log("Caught exception. Enabling the Quit and Upload buttons.")
            self.instance.goButton['state'] = 'enabled'
            self.instance.status.set("Problem uploading. You may press Upload again to retry.")
            log(type)
            log(value)
            log(tb.format_exc(traceback))


class Main(ttk.Frame):
    def __init__(self, root, *args, **kwargs):
        ttk.Frame.__init__(self, root, *args, **kwargs)
        style = ttk.Style()
        print style.theme_use()
        #style.configure("BW.TLabel", foreground="black", background="white")
        
        self.root = root
        ttk.Style()
        self.top = ttk.Frame()
        self.style = ttk.Style()
        self.top.pack(side="top", fill="x", padx=10, pady=10)
        self.patientID = tk.StringVar()
        self.userName = tk.StringVar()
        self.patientIDLabel = ttk.Label(self.top, text="Patient ID:")
        self.userNameLabel = ttk.Label(self.top, text="User Name:")
        self.patientIDLabel.grid(row=0, column=0, padx=10, pady=10)
        self.userNameLabel.grid(row=0, column=4, padx=10, pady=10)
        self.patientIDEntry = tk.Entry(self.top, textvariable=self.patientID)
        self.userNameEntry = tk.Entry(self.top, textvariable=self.userName)
        self.patientIDEntry.grid(row=0, column=2, padx=10, pady=10)
        self.userNameEntry.grid(row=0, column=5, padx=10, pady=10)
        
        self.middle = ttk.Frame(width=200)
        self.middle.pack(fill="y")
        self.patientNotesText = tk.Text(self.middle, height=10)
        self.patientNotesText.pack(padx=10, pady=10)
        
        self.pbFrame = ttk.Frame()
        self.currentFile = tk.StringVar()
        self.currentFileLabel = ttk.Label(self.pbFrame, textvariable=self.currentFile)
        self.currentFileLabel.pack()
        self.pb = ttk.Progressbar(self.pbFrame, mode='determinate')
        self.pb.pack()
        self.fileNames = tk.StringVar()
        self.fileNamesLabel = ttk.Label(self.pbFrame, textvariable=self.fileNames)
        self.fileNamesLabel.pack()
        self.pbFrame.pack()
        
        self.bottom = ttk.Frame()
        self.bottom.pack(side='bottom', fill="x")
        self.status = tk.StringVar()
        self.statusLabel = ttk.Label(self.bottom, text="", border=1, relief="sunken", textvariable=self.status, justify=tk.LEFT)
        self.statusLabel.configure(background="gray", relief="sunken")
        self.statusLabel.pack(side="bottom", fill="x", padx=2, pady=2)
        
        self.buttons = ttk.Frame()
        self.goButton = ttk.Button(self.buttons, text="Upload", command=self.go)
        self.goButton.pack(side="left")
        self.pb.pack()
        self.quitButton = ttk.Button(self.buttons, text="Quit", command=self.quit)
        self.quitButton.pack(side="right")
        self.buttons.pack(side="bottom", fill="x", padx=10, pady=10)
        
        self.pause = False
        self.root.bind("<FocusOut>", self.saveAppConf)
        
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
        self.root.update()

    def saveAppConf(self, event=None):
        appConf['geometry'] = self.root.geometry()
        appConf['patientID'] = self.patientID.get()
        appConf['userName'] = self.userName.get()
        appConf['patientNotes'] = self.patientNotesText.get(0.0, tk.END)
        json.dump(appConf, file(".metadata.json", 'wb'))
        log("Wrote " + json.dumps(appConf))
        return()
    
    def go(self):
        self.saveAppConf()
        if self.patientID.get() == "" or sel.userName.get() == "":
            tkMessageBox.showwarning("Required information is missing", "Patient Name and Patient ID are required.")
            return
        self.quitButton['text'] = "Pause"
        self.goButton['state'] = "disabled"
        self.root.update()
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
            #And send the metada for this file.
            self.status.set("Checking for resume information.")
            self.root.update()
            files = {}
            files['file'] = eegFile.name
            files['chunkSize'] = str(chunkSize)
            files['metadata'] = json.dumps(appConf)
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
            self.root.update()
            if verifyLength != length:
                self.pb['value'] = 0
                self.root.update()
                count = 0
                for chunk in chunks(eegFile):
                    if not self.pause:
                        md5sum = hashlib.md5(chunk).hexdigest()
                        #The keys in conf are converted to str's by json
                        manifestMD5sum = chunkManifest.get(str(count), "")
                        if md5sum != manifestMD5sum:
                            files = {'file': ('fullChunk', chunk ), 'md5sum': ('md5sum', md5sum)}
                            files['filename'] = eegFile.name
                            files['metadata'] = json.dumps(appConf)
                            files['count'] = str(count)
                            with Catch(self):
                                #if this fails, the Catch will re-enable
                                #Quit button
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
                        self.root.update()
                    else:
                        self.goButton['state'] = "enabled"
                        self.pause = False
                        self.quitButton['text'] = "Quit"
                        return
                
            else:
                #Skip this entire file.
                self.pb['value'] = 100
                self.root.update()
            self.status.set('Verifying...')
            self.root.update()
            eegFile.seek(0)
            fullMD5 = hashlib.md5(eegFile.read()).hexdigest()
            eegFile.seek(0)
            files = {}
            files['file'] = eegFile.name
            files['fullMD5'] = fullMD5
            req = requests.post(verifyurl, files=files)
            if json.loads(req.text)['verified']:
                log("Verified upload of {0}".format(eegFile.name))
            else:
                log("Verification of {0} failed!".format(eegFile.name))
                self.status.set("Verification of {0} failed!".format(eegFile.name))
                self.quitButton['text'] = "Quit"
                self.goButton['text'] = "Done"
                return
            #open_req(req)
                
            #Remove this filename from the list of filenames 
            #that need to be uploaded
            del self.fileGlob[self.fileGlob.index(fn)]
            self.set_filenames()
        self.quitButton['text'] = "Quit"
        self.goButton['text'] = "Done"
        self.status.set("All files uploaded. Press Quit to exit.")
        self.goButton['command'] = self.quit
        self.root.update()
    
    


if __name__ == "__main__":

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
        appConf = json.load(open('.metadata.json'))
    except IOError:
        appConf = {}
    root = tk.Tk()
    root.configure(background = "#eaeaea")
    root.resizable(width=0, height=1)
    main= Main(root)
    root.geometry(appConf.get("geometry", "589x461+30+45"))
    root.title("Neurovigil Uploader")
    main.fileGlob = glob.glob("*.txt")
    main.set_filenames()
    main.patientID.set(appConf.get("patientID", ""))
    main.userName.set(appConf.get("userName", ""))
    main.patientNotesText.delete(1.0, tk.END)
    main.patientNotesText.insert(tk.END, appConf.get("patientNotes").strip(), "")
    root.lift()
    if len(sys.argv) > 1:
        debug()
    root.mainloop()  
    log( main.patientID.get())

