#!/usr/bin/env python
from __future__ import division
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
        print "Instance already running"
        sys.exit(1)
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

server = "http://localhost:8000"

if len(sys.argv) >= 2 and now().month < 3:
    if sys.argv[1] == "u":
        server = "https://upload.neurovigil.com"



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


class Main(ttk.Frame):
    def __init__(self, root, *args, **kwargs):
        ttk.Frame.__init__(self, root, *args, **kwargs)
        style = ttk.Style()
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
        ttk.Label(self.middle, text="Notes").pack()
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
        self.root.bind("<FocusOut>", self.saveMetaData)
        
    def quit(self):
        #If the quit button's text has been changed to pause.
        if self.quitButton['text'] == "Pause":
            self.pause = True
            return
        else:
            #Refresh the conf file before exiting.
            #store the current window position
            self.saveMetaData()
            log("Quitting")
            sys.exit(0)

    def set_filenames(self):
        files = [ "{0} : {1}".format(datetime.datetime.fromtimestamp(os.stat(x)[8]).strftime("%Y-%m-%d"), x) for x in self.fileGlob]
        fileStr = "\n".join(files)
        self.fileNames.set("                       Files to upload\n==========================\n" + fileStr)
        self.root.update()
        return(fileStr)

    def saveMetaData(self, event=None):
        appMeta['geometry'] = self.root.geometry()
        appMeta['patientID'] = self.patientID.get()
        appMeta['userName'] = self.userName.get()
        appMeta['patientNotes'] = self.patientNotesText.get(0.0, tk.END)
        appMeta['localtimepickle'] = pickle.dumps(now)
        appMeta['localtimeString'] = str(now())
        
        json.dump(appMeta, file(".metadata.json", 'wb'))
        #log("Wrote " + json.dumps(appMeta))
        return()
    
    def go(self):
        global errors
        self.saveMetaData()
        if self.patientID.get() == "" or self.userName.get() == "":
            tkMessageBox.showwarning("Required information is missing", "Patient Name and Patient ID are required.")
            return
        self.quitButton['text'] = "Pause"
        self.goButton['state'] = "disabled"
        self.root.update()
        num = len(self.fileGlob)
        count = 1
        for fn in self.fileList:
            #Check for a progress indicator
            self.currentFile.set(fn)
            eegFile = open(fn, 'rb')
            eegFile.seek(0, 2)
            length = eegFile.tell()
            if length == 0:
                #If the file is empty, it will appear as unverified. Skip it.
                errors += "{0} is empty. Skipping.\n".format(eegFile.name)
                break
            eegFile.seek(0)
            nChunks = int(math.ceil(length / float(chunkSize)))
            #Check to see if this file can be resumed.
            #And send the metada for this file.
            self.status.set("Checking for resume information. May take several minutes...")
            self.root.update()
            files = {}
            files['file'] = eegFile.name
            files['chunkSize'] = str(chunkSize)
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(eegFile.name)
            Ctime = datetime.datetime.fromtimestamp(ctime).replace(tzinfo=mytz)
            Mtime = datetime.datetime.fromtimestamp(mtime).replace(tzinfo=mytz)
            appMeta['eegFileCreateDate'] = str(Ctime)
            appMeta['eegFileCreateDatePickle'] = pickle.dumps(Ctime)
            appMeta['eegFileModificationDate'] = str(Mtime)
            appMeta['eegFileModificationDatePickle'] = pickle.dumps(Mtime)
            appMeta['now'] = pickle.dumps(now())
            files['metadata'] = json.dumps(appMeta)
            with Catch(self):
                req = requests.post(verifyurl, files=files, verify=False)
            #open_req(req)
            try:
                verifyResult = json.loads(req.text)
            except ValueError:
                errors += req.text + "\n\n"
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
                            files['chunkSize'] = str(chunkSize)
                            files['metadata'] = json.dumps(appMeta)
                            files['count'] = str(count)
                            with Catch(self):
                                #if this fails, the Catch will re-enable
                                #Quit button
                                req = requests.post(url, files=files, verify=False)
                            try:
                                result = json.loads(req.text)
                            except:
                                open_req(req)
                                errors += req.text + "\n\n"
                        else:
                            log("Skipping chunk {0}".format(count))
                        self.pb['value'] = (float(count) / nChunks) * 100
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
            self.status.set('Verifying ...')
            self.root.update()
            eegFile.seek(0)
            fullMD5 = hashlib.md5(eegFile.read()).hexdigest()
            eegFile.seek(0)
            files = {}
            files['file'] = eegFile.name
            files['metadata'] = json.dumps(appMeta)
            files['fullMD5'] = fullMD5
            req = requests.post(verifyurl, files=files, verify=False)
            if json.loads(req.text)['verified']:
                log("Verified upload of  {0}".format(eegFile.name))
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
        #Upload the errors text thing.
        files = {'errors': ('errors', errors )}
        files['file'] = "errors.txt"
        files['metadata'] = json.dumps(appMeta)
        with Catch(self):
            req = requests.post(verifyurl, files=files, verify=False)
        if len(errors) > 0:
            tkMessageBox.showwarning("ALERT", errors)
        self.status.set("All files uploaded. Press Quit to exit.")
        self.goButton['command'] = self.quit
        archiveFolder = "uploaded-{0}".format(datetime.datetime.now().strftime("%Y-%m-%d_%H_%M"))
        try:
            os.mkdir(archiveFolder)
            log("Setting archive folder to {0}.".format(archiveFolder))
        except OSError:
            pass
        for fn in self.fileList:
            log("Archiving {0}.".format(fn))
            os.rename(fn, os.path.join(archiveFolder, fn))
        self.status.set("All files uploaded and archived to {0}. Press Quit to exit.".format(archiveFolder))
        self.root.update()
    
    


if __name__ == "__main__":
    try:
        appMeta = json.load(open('.metadata.json'))
    except IOError:
        appMeta = {}
    root = tk.Tk()
    root.configure(background = "#eeeeee")
    root.resizable(width=0, height=1)
    main= Main(root)
    root.geometry(appMeta.get("geometry", "589x499+11+36"))
    root.title("Neurovigil Uploader")
    main.fileGlob = [x for x in os.listdir(cwd) if re.match(globRE, x) ]
    main.fileList = [x for x in main.fileGlob]
    main.set_filenames()
    main.status.set("Please note if file dates are wrong.")
    main.patientID.set(appMeta.get("patientID", ""))
    main.userName.set(appMeta.get("userName", ""))
    #main.patientNotesText.delete(1.0, tk.END)
    existingPatientNotes = appMeta.get("patientNotes", "")
    filedateStr = main.set_filenames()
    if len(existingPatientNotes) < 4 and filedateStr !="":
        existingPatientNotes = "If these dates are wrong, please correct them.\n"
        existingPatientNotes += filedateStr
        existingPatientNotes += "\n\nPlease add other notes below as needed.\n\n"
    main.patientNotesText.insert(tk.END, existingPatientNotes)
    root.lift()
    if len(sys.argv) > 2:
        debug()
    root.mainloop()  
    log( main.patientID.get())

