#!/usr/bin/env python
# encoding: utf-8
import pexpect.pexpect as pexpect
import os
import sys
from pdb import set_trace as debug

pexpect.run('rm /var/lib/sqlite3/portalDB/upload.neurovigil.db')
child=pexpect.spawn('./manage.py syncdb')
child.expect('yes/no')
child.sendline("yes")
child.expect(": ")
child.sendline("lee")
child.expect("address:")
child.sendline('snl@snl.salk.edu')
child.expect("Password:")
child.sendline("staticmouseveganlight")
child.expect("again\):")
child.sendline("staticmouseveganlight")
print child.read()


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.dirname(PROJECT_DIR))
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
os.environ['PYTHONPATH'] = PROJECT_DIR

from django.contrib.auth.models import User
#from upload.models import *



def main():
    pass


if __name__ == '__main__':
    main()

