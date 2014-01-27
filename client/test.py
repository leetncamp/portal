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

import psutil

existing = [ p for p in psutil.process_iter() if "NVUploader" in p.name ]
debug()
