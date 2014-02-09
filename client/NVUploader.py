#!/usr/bin/env python
from __future__ import division
from collections import OrderedDict
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
    nvs      = nvRE.findall(tasklist)
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
import tkFont
import re
from pdb import set_trace as debug
import time
import os
import math
import requests
import threading
import pickle
import zlib
import hashlib
import tkMessageBox
import datetime
import traceback as tb
from dateutil.tz import gettz, tzlocal
import pytz
lajolla = pytz.timezone("America/Los_Angeles")
import platform

localtimezoneStr = datetime.datetime.now(tzlocal()).tzname()

chunkSize = 1000000
def now():
    return(datetime.datetime.now().replace(tzinfo=tzlocal()))


server = "https://upload.neurovigil.com"

try:
    if "local" in sys.argv:
        server = "http://localhost:8000"
except IndexError:
    pass

uploadURL = "{0}/bupload".format(server)
checkstatus = "{0}/checkstatus/{1}".format(server, VERSION)

globRE = re.compile("eeg", re.I)
errors =  ""

#Set the current working directory to that of the executable.
cwd = os.path.dirname(os.path.abspath(sys.argv[0]))
#If the executable is bundled, we might have to go trim the path
cwd = cwd.split("NVU")[0]
os.chdir(cwd)

logfile = file("upload.log", 'a')

positionRE = re.compile(r"(\+\d+\+\d+)")
sizeRE = re.compile(r"(\d+x\d*)")

def log(txt):
    logfile.write("{0} : {1}\n".format(now(), txt))
    logfile.flush()
    #print txt

log("========================")
log(now())
log(cwd)
log(server)


uname = platform.uname()
OS = uname[0]

def open_req(req):
    if OS=="Darwin":
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
            self.clear_buttons_from_upload()
            self.paused = False
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

meta = { 
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

defaultmeta = { 
    "uploadInfo": {
        "clinician": "",
        "company": "",
        "VERSION": VERSION,
        "localtimezone": localtimezoneStr,
    },
    "files" : OrderedDict(),
}

def updateMeta(fileName):
    stat  = os.stat(fileName)
    ctime = datetime.datetime.fromtimestamp(stat[9])
    mtime = datetime.datetime.fromtimestamp(stat[8])
    f     = file(fileName, 'rb')
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
    #Update the meta object
    thisMeta                = meta['files'].get(fileName, {})
    thisMeta['ctime']       = ctime
    thisMeta['mtime']       = mtime
    thisMeta['length']      = length
    thisMeta['header']      = header
    meta['files'][fileName] = thisMeta

def askCompany():
    from ask import ask_company
    return(ask_company())    
    
class UploadWindow(tk.Frame):
    
    def __init__(self, root, *args, **kwargs):
        global meta
        self.root = root
        self.pause = False
        tk.Frame.__init__(self, root, *args, bg="#ffffff", padx=10, pady=10,  **kwargs)
        self.root.title("Neurovigil EEG Uploader")
        self.outsidePad = tk.Frame(self.root, padx=10, pady=10)
        #Company name and clinician name
        self.files      = OrderedDict()
        self.filerow    = 1
        self.top       = tk.LabelFrame(self.outsidePad, bg="#ffffff", text="Upload Information", padx=5, pady=5)
        self.clinician  = tk.StringVar()
        self.clinician.set(meta['uploadInfo'].get('clinician', ""))
        self.clinicianL = tk.Label(self.top, text="Clinician Name")
        #create an underline font using the default font in label
        self.font = tkFont.Font(self.clinicianL, self.clinicianL.cget("font"))
        self.font.configure(underline=True)
        self.clinicianL.grid(row=0, column=0)
        self.clinicianE = tk.Entry(self.top, textvariable=self.clinician, width=30)
        self.clinicianE.grid(row=0, column=1)
        self.company  = tk.StringVar()
        self.company.set(meta['uploadInfo'].get('company', ""))
        self.companyL = tk.Label(self.top, text="Company Name")
        self.companyL.grid(row=0, column=2)
        self.companyE = tk.Entry(self.top, textvariable=self.company, width=30)
        self.companyE.grid(row=0, column=3)
        
        
        #Patient ID

        self.pidCheck    = tk.IntVar()
        self.pidCheck.set(meta['uploadInfo'].get("multiplePatients", 0))
        self.pidCheckbox = tk.Checkbutton(self.top, text="Uploading data for multiple patients", variable=self.pidCheck, command=self.checkbox)
        self.pidCheckbox.grid(row=1, column=1, sticky=tk.W)
        self.patientID   = tk.StringVar()
        self.patientID.set(meta['uploadInfo'].get("patientID", ""))
        self.patientIDL  = tk.Label(self.top, text="Patient ID")
        self.patientIDE  = tk.Entry(self.top, textvariable=self.patientID, width=30)
        self.multipleIDL = tk.Label(self.top, text="Enter patient ID's for each file below.")
        if self.pidCheck.get():
            self.goMultiplePatient()
        else:
            self.goSinglePatient()
        self.top.pack()
        
        #File list
        self.filegroup = tk.LabelFrame(self.outsidePad, bg="#ffffff", text="Files", padx=10, pady=10)
        self.headings = ["File", "Date", "Size MB", "PatientID", "Notes", "Upload", "Server Status", "Upload Progress"]
        self.drawHeadings()
        self.drawFiles()
        self.filegroup.pack(expand=1)

        #Quit/Upload
        self.rowQuit  = tk.Frame(self.outsidePad, bg="#ffffff")
        self.uploadB = tk.Button(self.rowQuit, text="Upload", command=self.upload)
        self.uploadB.grid(row=0, column=0, sticky=tk.W)
        self.quitB = tk.Button(self.rowQuit, text="Quit", command=self.exit)
        self.quitB.grid(row=0, column=1, sticky=tk.E)
        self.paused = False
        self.pauseB = tk.Button(self.rowQuit, text="Pause", command=self.set_paused)
        self.debugB = tk.Button(self.rowQuit, text="Debug", command=self.debugger)
        #self.debugB.grid(row=0, column=3, sticky=tk.E)
        
        #Status bar
        self.rowStatus = tk.Frame(self.root)
        self.status = tk.StringVar()
        self.status.set("Checking for resume information for partially uploaded files. May take a minute...")
        self.statusL = tk.Label(self.rowStatus, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#ddd", padx=10, textvariable=self.status)
        self.statusL.pack(fill=tk.X, padx=0, pady=2)
        
        #Display the all the widgets
        self.rowQuit.pack(fill=tk.X)
        self.outsidePad.pack()
        self.rowStatus.pack(fill=tk.X, side=tk.BOTTOM)
        self.pack()
        self.update()    

        """Send the meta to the server. If company name is missing, there isn't
        any point in trying to check the upload status. In that case, we'll
        check after the upload button is pushed."""
    
        if self.company.get():

            self.status.set("Checking with server for resume information. May take a minute...")
            #Gray out the Upload button while we check with the server.
            self.uploadB['state'] = 'disabled'
            self.quitB['state'] = 'disabled'
            self.update()
            self.check_status()
            self.status_check_needed = False
        else:
            self.status.set("Ready")
            self.status_check_needed = True
    
    def check_status(self):
        global meta
        try:
            req = requests.post(checkstatus, files={"meta":pickle.dumps(meta)})
            self.uploadB['state'] = 'active'
            self.quitB['state'] = 'active'
            try:
                #Replace the meta returned from the server with this one.
                meta    = pickle.loads(req.text.encode("utf-8"))
                message = meta.get('message', "")
                status  = meta.get('status', "")
                
                self.status.set("Updating files with information from server...")
                for fn in self.files:
                    metafile = meta['files'].get(fn, {})
                    serverstatus = metafile.get("serverstatus")
                    self.files[fn]['serverstatus'].set(serverstatus)
                    if serverstatus == "uploaded":
                        self.files[fn]['upload'].set(0)
                self.status.set("Ready")
            except Exception as e:
                open_req(req)
                log(req.text)
                self.status.set("unexpected result from server {0}".format(server))
        except Exception as e:
            if "Connection refused" in str(e):
                message = "Could not connect to the server {0}".format(server)
                log(message)
                self.status.set("SERVER CONNECTION REFUSED!!")
            else:
                self.status.set(str(e))
    

        
    def set_paused(self):
        
        self.paused = not self.paused
        self.check_status()
        self.status.set("Saving resume information...this could take a minute")
        self.root.update()
        return
        
    
    def updateMetaFromForm(self):
        
        """transfer data from the tkinter form widgets into the meta dictionary"""
        
        meta['uploadInfo']['multiplePatients'] = self.pidCheck.get()
        meta['uploadInfo']['clinician'] = self.clinician.get()
        meta['uploadInfo']['company'] = self.company.get()
        meta['uploadInfo']['patientID'] = self.patientID.get()
        if not meta['uploadInfo']['multiplePatients']:
            meta['uploadInfo']['patientID'] = self.patientID.get()
        for fn in self.files:
            meta['files'][fn]['patientID'] = self.files[fn]["patientID"].get()
            meta['files'][fn]['notes'] = self.files[fn]["notes"].get()
    
        
        
    def drawHeadings(self):
        #First remove the ones that are there.
        column = 0
        for heading in self.headings:
            lab = tk.Label(self.filegroup, text=heading)
            lab.configure(font=self.font)
            lab.grid(row=0, column=column, sticky=tk.W, padx=10)
            column += 1
    
    def drawFiles(self):
        
        for fn in meta['files']:
            thisFile                   = {}
            info                       = meta['files'][fn]
            thisFile['nameL']          = tk.Label(self.filegroup, text=fn)
            thisFile['nameL'].configure(font=self.font)
            thisFile['nameL'].grid(row = self.filerow, column=0, sticky=tk.W, padx=10)
            """The file's datestamp is in La Jolla time. Convert it to iBrain's local time"""
            localstamp                 = info['ctime'].replace(tzinfo=lajolla).astimezone(tzlocal())
            thisFile['dateL']          = tk.Label(self.filegroup, text=localstamp.strftime("%b %d, %Y %I:%M %p"))
            thisFile['dateL'].grid(row = self.filerow, column=1, sticky=tk.W, padx=10)
            thisFile['size']           = tk.Label(self.filegroup)
            thisFile['size'].grid(row = self.filerow, column=2, sticky=tk.W, padx=10)
            thisFile['size']['text'] = "{0} MB".format(int(meta['files'][fn]["length"] / 1000000))
            thisFile['patientID']      = tk.StringVar()
            thisFile['patientID'].set(meta['files'][fn].get("patientID", ""))
            thisFile['patientIDE-m']   = tk.Entry(self.filegroup, textvariable=thisFile['patientID'], width=15)
            thisFile['patientIDE']     = tk.Entry(self.filegroup, textvariable=self.patientID, width=15) 
            if self.pidCheck.get():
                #Uploading for multiple patients. Show the Entry widget here.
                thisFile['patientIDE-m'].grid(row=self.filerow, column=3, sticky=tk.W, padx=10)
            else:
                thisFile['patientIDE'].grid(row=self.filerow, column=3, sticky=tk.W, padx=10)
            thisFile['notes'] = tk.StringVar()
            thisFile['notes'].set( meta['files'][fn].get('notes', ""))
            thisFile['notesL'] = tk.Entry(self.filegroup, textvariable = thisFile['notes'], width=25)
            thisFile['notesL'].grid(row=self.filerow, column=4, padx=10)
            thisFile['upload'] = tk.IntVar()
            #Default to true. We will set to false later if needed
            thisFile['upload'].set(1) 
            thisFile['uploadCB'] = tk.Checkbutton(self.filegroup, variable=thisFile['upload'])
            thisFile['uploadCB'].grid(row=self.filerow, column=5, padx=10)
            thisFile['serverstatus'] = tk.StringVar()
            thisFile['serverstatus'].set(meta['files'][fn].get("serverstatus", "?"))
            thisFile['serverstatusL'] = tk.Label(self.filegroup, textvariable=thisFile['serverstatus'])
            thisFile['serverstatusL'].grid(row=self.filerow, column=6, padx=10)
            thisFile['pb'] = ttk.Progressbar(self.filegroup, mode='determinate')
            thisFile['pb'].grid(row=self.filerow, column=7, padx=10)
            self.files[fn] = thisFile
            self.filerow += 1
    
            self.root.protocol("WM_DELETE_WINDOW", self.window_close)

    def window_close(self):
        if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.set_paused()
            self.quit()        

    def goSinglePatient(self):
        
        """In single patient mode, we link all the patientID fields together by
        binding them all to self.patientID"""
        
        self.multipleIDL.grid_forget()
        self.patientIDL.grid(row=1, column=2)
        self.patientIDE.grid(row=1, column=3)
        #If files are showing, we need to replace their entry widget
        row=1
        for fn in self.files:
            self.files[fn]["patientIDE-m"].grid_forget()
            self.files[fn]['patientIDE'].grid(row=row, column=3)
            row += 1
        
    
    def goMultiplePatient(self):
        
        """In multiplepatient mode, each file's patientID's entry widget has
        it's own storage variable. Actually this is always the case, but the 
        linkage changes."""
        
        self.patientIDL.grid_forget()
        self.patientIDE.grid_forget()
        self.multipleIDL.grid(row=1, columnspan=1, column=3, sticky=tk.E)
        row=1
        for fn in self.files:
            self.files[fn]["patientIDE"].grid_forget()
            self.files[fn]['patientIDE-m'].grid(row=row, column=3)
            row += 1
        
        
    def checkbox(self, *args, **kwargs):
        if self.pidCheck.get():
            self.goMultiplePatient()
        else:
            self.goSinglePatient()
            
    def set_buttons_to_upload(self):
        
        """Gray out the Upload button and replace the Quit button with Pause."""
        
        self.quitB.grid_forget()
        self.pauseB.grid(row=0, column=1)
        self.uploadB['state'] = "disabled"

    def clear_buttons_from_upload(self):
        
        """During an upload the Upload button is grayed out and the Pause
        button is displayed. Return to the normal button config."""
        
        self.pauseB.grid_forget()
        self.quitB.grid(row=0, column=1)
        self.uploadB['state'] = "active"
        
    
    def upload(self):
        global errors
        if self.company.get() == "" or self.clinician.get() == "":
            tkMessageBox.showwarning("Required information is missing", "Company and Clinician are required")
            return
            
        if self.status_check_needed:
            self.check_status()
        

        self.updateMetaFromForm()

        if meta['uploadInfo']['multiplePatients'] == 1:
            #Check to make sure there is a patientID per file.
            patientIDsOK = True
            for fn in meta['files']:
                if meta['files'][fn]['patientID'] == "":
                    patientIDsOK = False
                    break
            if not patientIDsOK:
                tkMessageBox.showwarning("Required information is missing", "When uploading data for multiple patients, each file must have a patientID")
                return
        else:
            if meta['uploadInfo']['patientID'] == "":
                tkMessageBox.showwarning("Required information is missing", "A patient ID is required")
                return
                    
        
        
        #remove files that aren't checked.
        uploadFiles = [ fn for fn in self.files if self.files[fn]["upload"].get() ]
        if not uploadFiles:
            self.status.set("Nothing to do.")
            return
        
        self.set_buttons_to_upload()
        
        for fn in uploadFiles:
            thisMeta = meta["files"][fn]
            baseStatus = "Uploading {0}...".format(fn)
            self.status.set(baseStatus)
            eegFile = open(fn, 'rb')
            eegFile.seek(0, 2)
            length = eegFile.tell()
            if length == 0:
                #If the file is empty, it will appear as unverified. Skip it.
                errors += "{0} is empty. Skipping.\n".format(eegFile.name)
                break
            nChunks = int(math.ceil(length / float(chunkSize)))
            data = {}
            data['file'] = eegFile.name
            data['meta'] = meta
            count = 0
            errors = ""
            eegFile.seek(0)
            resume = thisMeta["serverstatus"] == "resume needed"
            for chunk in chunks(eegFile):
                if self.paused:
                    self.clear_buttons_from_upload()
                    self.paused = False
                    self.status.set("Ready")
                    return
                else:
                    chunkMD5 = hashlib.md5(chunk).hexdigest()
                    if resume:
                        try:
                            manifestMD5sum = thisMeta.get('chunkManifest')[count]
                            if chunkMD5 == manifestMD5sum:
                                skip = "Skipping chunk {0} of file {1}. Checksum verified. ".format(count, fn)
                                self.status.set(skip)
                                log(skip)
                                count += 1
                                self.files[fn]['pb']['value'] = (float(count) / nChunks) * 100
                                self.root.update()
                                self.pauseB.update()
                                self.rowQuit.update()
                                continue
                        except KeyError:
                            #There is no chunk, continue
                            pass

                    data['chunk'] = chunk
                    data["chunkMD5"] = chunkMD5
                    #with Catch(self):
                        #if this fails, the Catch will re-enable
                        #Quit button

                    data['count'] = count
                    req = requests.post(uploadURL, files={"data":pickle.dumps(data)}, verify=False)
                    try:
                        result = pickle.loads(req.text)
                        if result['status'] == True:
                            count += 1
                            self.files[fn]['pb']['value'] = (float(count) / nChunks) * 100
                            #Success of chunk upload and write
                            self.root.update()
                            self.pauseB.update()
                            self.rowQuit.update()
                        else:
                            log(result['status'])
                            self.status.set(result['status'])
                            self.update()
                            self.rowQuit.update()
                    except Exception as e:
                        open_req(req)
                        errors += req.text + "\n\n" 
                        open_req(req)                       



            
            #All chunks have been uploaded. Verify
            self.status.set('Verifying {0}'.format(fn))
            self.update()
            try:
                del data['chunk']
                del data['chunkMD5']
            except KeyError:
                pass
            eegFile.seek(0)
            fullMD5 = hashlib.md5(eegFile.read()).hexdigest()
            eegFile.seek(0)
            data["fullMD5"] = fullMD5
            req = requests.post(uploadURL, files={"data":pickle.dumps(data)})

            try:
                result = pickle.loads(req.text)
            except:
                result="not verified"
                open_req(req)
            if result == 'verified':
                self.files[fn]["serverstatus"].set("upload verified")
                meta['files'][fn]['serverstatus'] = "upload verified"
                log("Verified upload of  {0}".format(eegFile.name))
            else:
                log("Verification of {0} failed!".format(eegFile.name))
                self.status.set("Verification of {0} failed!".format(eegFile.name))
                #self.quitButton['text'] = "Quit"
                #self.goButton['text'] = "Done"
                log(req.text)



        
        #Upload the errors text thing.
        try:
            del data['fullMD5']
        except:
            pass
        self.clear_buttons_from_upload()
        self.uploadB['state'] = "disabled"
        self.status.set("")
        self.root.update()
        if len(errors) == 0:
            errorMsg = "No errors reported."
        else:
            errorMsg = errors
        data["errors"] =  errorMsg
        req = requests.post(uploadURL, files={"data":pickle.dumps(data)})
        try:
            result = pickle.loads(req.text)
            if result != "errors written":
                log.log(req.text)
                self.status.set("Error writting error log to server.")
                self.update()
        except:
            open_req(req)
        if len(errors) > 0:
            tkMessageBox.showwarning("ALERT", errors)
        self.status.set("Upload finished. Press Quit to exit.")
        
        

################################################################################
    
    def debugger(self):
        self.paused = True
        return
    
    def exit(self):
        self.updateMetaFromForm()
        self.quit()        

if __name__ == "__main__":
    
    """Read in any metadata stored in metadata.pickle. If none exists, return
    the default meta dictionary"""
        
    try:
        meta = pickle.load(file("metadata.pickle", "rb"))
    except Exception as e:
        meta = defaultmeta
    if not meta['uploadInfo'].get('company', ""):
        if "ask" in sys.argv:
            meta['uploadInfo']['company'] = askCompany()
        else:
            meta['uploadInfo']['company'] = ""
    
    meta['uploadInfo']['chunkSize'] = chunkSize
        
    """For each EEG file add it's length, ctime and other metadata to the
    metadata dictionary refreshing any dictionary structures for files that
    already exist in the meta dictionary and adding any new ones. Delete ones
    that are missing from the filesystem.
    
    In other words, sync from filesystem to meta"""
    
    fileList = [x for x in os.listdir(cwd) if re.match(globRE, x) ]
    fileList = sorted(fileList, reverse=True)
    for fileName in fileList:
        updateMeta(fileName)

    for fileName in meta['files']:
        if fileName not in fileList:
            del meta['files'][fileName]
    
    """Open the Tk Window"""
    root = tk.Tk()
    root.geometry(meta.get("geometry", ""))
    root.geometry("")
    app = UploadWindow(root)
    app.mainloop()
    meta['geometry'] = root.geometry()
    pickle.dump(meta, file("metadata.pickle", "wb"))
        
    
    
    
    
