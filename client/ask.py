#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
ZetCode Tkinter tutorial

In this script, we use the grid manager
to create a skeleton of a calculator.

author: Jan Bodnar
last modified: December 2010
website: www.zetcode.com
"""

from Tkinter import Tk, W, E
from ttk import Frame, Button, Label, Style
from ttk import Entry
from pdb import set_trace as debug


class Example(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent)   
         
        self.parent = parent
        
        self.initUI()
        
    def initUI(self):
      
        self.parent.title("Please enter company name")
        
        Style().configure("TButton", padding=(0, 20, 0, 20), width=60)
        Style().configure("TLabel", padding=(3, 3, 3, 3))
        Style().configure("TEntry", padding=(0, 5, 0, 5))
        self.columnconfigure(0, pad=3)
        self.columnconfigure(1, pad=3)
        self.columnconfigure(2, pad=3)
        self.columnconfigure(3, pad=3)
        
        self.rowconfigure(0, pad=3)
        self.rowconfigure(1, pad=3)
        self.rowconfigure(2, pad=3)
        self.rowconfigure(3, pad=3)
        self.rowconfigure(4, pad=3)
        self.label = Label(self, text="Company Name")
        self.entry = Entry(self)
        self.entry.grid(row=0, columnspan=4, sticky=W+E)
        cls = Button(self, text="OK", command=self.quit)
        cls.grid(row=1, column=0)
        self.pack()


def ask_company(): 
    root = Tk()
    app = Example(root)
    wt = root.winfo_screenwidth()
    ht = root.winfo_screenheight()
    rootsize = (516, 102)
    x = wt/2 - rootsize[0]/2
    y = ht/2 - rootsize[1]/2
    root.geometry("%dx%d+%d+%d" % (rootsize + (x, y)))
    root.lift()
    root.mainloop()
    company = app.entry.get()
    app.quit()
    return(company)


if __name__ == '__main__':
    ask_company()  