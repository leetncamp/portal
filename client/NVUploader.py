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



class Example(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent)   
        self.parent = parent
        self.parent.title("Neurovigil Uploader")
        self.style = Style()
        self.patientName = StringVar()
        self.patientLabel = Label(self, text="Patient Notes")
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
        
    def go(self):
        num = len(self.fileGlob)
        count = 1
        for file in self.fileGlob:
            self.currentFile.set(file)
            time.sleep(.2)
            self.pb['value'] = (count / num) * 100
            count += 1
            self.parent.update()
            
        
if __name__ == '__main__':
    cwd = os.path.dirname(sys.argv[0])
    if cwd.endswith("MacOS"):
        cwd = os.path.dirname(os.path.dirname(os.path.dirname(cwd)))
    file("/tmp/cwd.txt", 'w').write(cwd)
    os.chdir(cwd)
    root = Tk()
    ex = Example(root)
    root.geometry("300x450+900+100")
    ex.fileGlob = glob.glob("*.txt")
    ex.fileNames.set("Files to upload\n=========\n\n" + "\n".join(ex.fileGlob))
    root.mainloop()  
    print ex.patientName.get()