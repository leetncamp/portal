#!/usr/bin/env python

import sys
import array

"""Here I write out a fake example file using two-byte integers to demonstrate
python's array.aray features http://docs.python.org/library/array.html. This is
the most efficient way to read and write chunks of integers in python."""

"""For some reason, I can't make sense of your binary example file. Take a look
at this data and then let's speak by phone."""

fn = sys.argv[1]
f = open(fn, 'wb')

header = """NeuroVigil iBrain Version 1.4
Firmware Date:  11.04.2013 09:11:28
Recording Date: 12.12.2013 22:49:45
ID: 129
Sample rate: 1040
Data encryption enabled
Offline record
*****
*****
*****
"""

dataList = range(20000000)

f.write(header)
dataArray = array.array("i", dataList )
dataArray.write(f)
