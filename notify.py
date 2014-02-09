#!/usr/bin/env python

"""Return a list of email addresses that should be sent notifications of
uploads. The django view will import 'notification_emails' from this file."""

import os

hostname = os.uname()[1]
if "upload" in hostname:
    notification_emails = ["lee@snl.salk.edu", "dhowe@neurovigil.com"]
else:
    #Development server
    notification_emails = ['lee@snl.salk.edu'] 
