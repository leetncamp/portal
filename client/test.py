#!/usr/bin/env python
from __future__ import division

from Tkinter import *
from ttk import *
from pdb import set_trace as debug
import sys

class Main(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent)   
        self.e1 = Entry(self)
        self.e1.grid(row=1, column=1)


master = Tk()
Label(master, text="First").grid(row=0, sticky=W)
Label(master, text="Second").grid(row=1, sticky=W)

e1 = Entry(master)
e2 = Entry(master)

e1.grid(row=0, column=1)
e2.grid(row=1, column=1)

Button(master, text="Quit", command=sys.exit).grid(row=3)
debug()
#root.mainloop()
