#!/usr/bin/env python

"""Return a list of email addresses that should be sent notifications of
uploads. The django view will import 'notification_emails' from this file."""

import os
#Comma separated list of names to send an email to when a file is uploaded, e.g.
#philip@neurovigil, dan@neurovigil.com


hostname = os.uname()[1]
if "upload" in hostname:
    notifcation_emails = ["lee@snl.salk.edu", "dhowe@neurovigil.com"]
else:
    #Development server
    notification_emails = ['lee@snl.salk.edu']