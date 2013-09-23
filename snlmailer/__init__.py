#/usr/bin/env python

#coding: UTF8
from __future__ import with_statement
import os
import smtplib
import threading
import Queue
import uuid
import re
import html2text
from socket import timeout
import time

from pdb import set_trace as debug


#Check to see if the user indends to redirect all outbound mail.
#look for a file called snlmailerRedirect.py on the system path,
#probably at the base path of the django project if using django
snlmailerRedirect = None
try:
    from snlmailerRedirect import *
except ImportError:
    pass


# this is to support name changes
# from version 2.4 to version 2.5
try:
    from email import encoders
    from email.header import make_header
    from email.message import Message
    from email.mime.audio import MIMEAudio
    from email.mime.base import MIMEBase
    from email.mime.image import MIMEImage
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
except ImportError:
    from email import Encoders as encoders
    from email.Header import make_header
    from email.MIMEMessage import Message
    from email.MIMEAudio import MIMEAudio
    from email.MIMEBase import MIMEBase
    from email.MIMEImage import MIMEImage
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText

# For guessing MIME type based on file name extension
import mimetypes
import time

from os import path

__version__ = "0.6"
__author__ = "Ryan Ginstrom"
__license__ = "MIT"
__description__ = "A module to send email simply in Python"

def validateEmail(email_address):
    if type(email_address) == type([]):
        valid_emails = []
        for addr in email_address:
            if re.match(r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', addr, re.IGNORECASE):
                valid_emails.append(addr)
            else:
                pass
        return valid_emails
            
    if re.match(r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', email_address, re.IGNORECASE):
        return [email_address]
    else:
        return []



class Mailer(object):
    """
    Represents an SMTP connection.

    Use login() to log in with a username and password.
    """

    def __init__(self, host="localhost", port=0, use_tls=False, usr=None, pwd=None):
        self.host = host
        self.port = port
        self.use_tls = use_tls
        self._usr = usr
        self._pwd = pwd

    def login(self, usr, pwd):
        self._usr = usr
        self._pwd = pwd
        
    def starttls(self):
        self._starttls = True
        self.use_tls = True
        self.port = 587

    def send(self, msg):
        """
        Send one message or a sequence of messages.

        Every time you call send, the mailer creates a new
        connection, so if you have several emails to send, pass
        them as a list:
        mailer.send([msg1, msg2, msg3])
        """
        server = smtplib.SMTP(self.host, self.port)
        
        if self._usr and self._pwd:
            if self.use_tls is True:
                server.ehlo()
                server.starttls()
                server.ehlo()
            
            server.login(self._usr, self._pwd)

        try:
            num_msgs = len(msg)
            for m in msg:
                self._send(server, m)
        except TypeError:
            self._send(server, msg)

        server.quit()
        
    def _send(self, server, msg):
        """
        Sends a single message using the server
        we created in send()
        """
        me = msg.From
        if isinstance(msg.To, basestring):
            to = [msg.To]
        else:
            to = list(msg.To)
            
        cc = []
        try:
            if msg.CC:
                if isinstance(msg.CC, basestring):
                    cc = [msg.CC]
                else:
                    cc = list(msg.CC)
        except AttributeError:
            pass

        bcc = []
        try:
            if msg.BCC:
                if isinstance(msg.BCC, basestring):
                    bcc = [msg.BCC]
                else:
                    bcc = list(msg.BCC)
        except AttributeError:
            pass        
            
        you = to + cc + bcc
        #I've wrapped the server.sendmail in a try to trap a 
        #greylisting problem I've seen.  smtp.snl.salk.edu
        #shouldn't greylist a local recipient.
        try:
            server.sendmail(me, you, msg.as_string())
        except smtplib.SMTPRecipientsRefused as e:
            #The email may have been graylisted.
            if 'Greylisted' in e:
                time.sleep(400)
                try:
                    server.sendmail(me, you, msg.as_string())
                except:
                    print("Could not deliver email to "+str(msg.To))
            else:
                print(e)

class MessageOrig(object):
    """
    Represents an email message.

    Set the To, From, Subject, and Body attributes as plain-text strings.
    Optionally, set the Html attribute to send an HTML email, or use the
    attach() method to attach files.

    Use the charset property to send messages using other than us-ascii

    If you specify an attachments argument, it should be a list of
    attachment filenames: ["file1.txt", "file2.txt"]

    `To` should be a string for a single address, and a sequence
    of strings for multiple recipients (castable to list)

    Send using the Mailer class.
    """

    def __init__(self, To=None, From=None, CC=None, BCC=None, Subject=None, Body=None, Html=None,
                 Date=None, attachments=None, charset=None):
        self.attachments = []
        if attachments:
            for attachment in attachments:
                if isinstance(attachment, basestring):
                    self.attachments.append((attachment, None))
                else:
                    try:
                        filename, cid = attachment
                    except (TypeError, IndexError):
                        self.attachments.append((attachment, None))
                    else:
                        self.attachments.append((filename, cid))
        self.To = To
        self.CC = CC
        self.BCC = BCC        
        """string or iterable"""
        self.From = From
        """string"""
        self.Subject = Subject
        self.Body = Body
        self.Html = Html
        self.Date = Date or time.strftime("%a, %d %b %Y %H:%M:%S %z (PDT)")
        
        self.charset = charset or 'us-ascii'

        self.message_id = self.make_key()
    def __str__(self):
        return "Email Message==> TO: "+str(self.To)+"; FROM: "+self.From+"; SUBJECT: "+self.Subject
        
    def make_key(self):
        return str(uuid.uuid4())
    
    def as_string(self):
        """Get the email as a string to send in the mailer"""
        if not self.attachments:
            return self._plaintext()
        else:
            return self._multipart()

    def _plaintext(self):
        """Plain text email with no attachments"""
        if not self.Html:
            msg = MIMEText(self.Body, 'plain', self.charset)
        else:
            msg  = self._with_html()

        self._set_info(msg)
        return msg.as_string()

    def _with_html(self):
        """There's an html part"""

        outer = MIMEMultipart('alternative')

        part1 = MIMEText(self.Body, 'plain', self.charset)
        part2 = MIMEText(self.Html, 'html', self.charset)

        outer.attach(part1)
        outer.attach(part2)

        return outer

    def _set_info(self, msg):
        if self.charset == 'us-ascii':
            msg['Subject'] = self.Subject
        else:
            subject = unicode(self.Subject, self.charset)
            msg['Subject'] = str(make_header([(subject, self.charset)]))
            
        msg['From'] = self.From
        
        if isinstance(self.To, basestring):
            msg['To'] = self.To
        else:
            self.To = list(self.To)
            msg['To'] = ", ".join(self.To)
            
        if self.CC:
            if isinstance(self.CC, basestring):
                msg['CC'] = self.CC
            else:
                self.CC = list(self.CC)
                msg['CC'] = ", ".join(self.CC)
                
        msg['Date'] = self.Date

    def _multipart(self):
        """The email has attachments"""

        #msg = MIMEMultipart('related')
        msg = MIMEMultipart('mixed')

        if self.Html:
            outer = MIMEMultipart('alternative')

            part1 = MIMEText(self.Body, 'plain', self.charset)
            part1.add_header('Content-Disposition', 'inline')

            part2 = MIMEText(self.Html, 'html', self.charset)
            part2.add_header('Content-Disposition', 'inline')

            outer.attach(part1)
            outer.attach(part2)
            msg.attach(outer)
        else:
            msg.attach(MIMEText(self.Body, 'plain', self.charset))

        self._set_info(msg)
        msg.preamble = self.Subject

        for filename, cid in self.attachments:
            self._add_attachment(msg, filename, cid)

        return msg.as_string()

    def _add_attachment(self, outer, filename, cid):
        ctype, encoding = mimetypes.guess_type(filename)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        fp = open(filename, 'rb')
        if maintype == 'text':
            # Note: we should handle calculating the charset
            msg = MIMEText(fp.read(), _subtype=subtype)
        elif maintype == 'image':
            msg = MIMEImage(fp.read(), _subtype=subtype)
        elif maintype == 'audio':
            msg = MIMEAudio(fp.read(), _subtype=subtype)
        else:
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(fp.read())
            # Encode the payload using Base64
            encoders.encode_base64(msg)
        fp.close()

        # Set the content-ID header
        if cid:
            msg.add_header('Content-ID', '<%s>' % cid)
            msg.add_header('Content-Disposition', 'inline')
        else:
            # Set the filename parameter
            msg.add_header('Content-Disposition', 'attachment', filename=path.basename(filename))
        outer.attach(msg)

    def attach(self, filename, cid=None):
        """
        Attach a file to the email. Specify the name of the file;
        Message will figure out the MIME type and load the file.
        """

        self.attachments.append((filename, cid))
        

class Manager(threading.Thread):
    """
    Manages the sending of email in the background
    
    you can supply it with an instance of class Mailler or pass in the same 
    parameters that you would have used to create an instance of Mailler
    
    if a message was succesfully sent, self.results[msg.message_id] returns a 3 
    element tuple (True/False, err_code, err_message)
    """
    
    def __init__(self, mailer=None, callback=None, **kwargs):
        threading.Thread.__init__(self)
        
        self.queue = Queue.Queue()
        self.mailer = mailer
        self.abort = False
        self.callback = callback
        self._results = {}
        self._result_lock = threading.RLock()
        
        if self.mailer is None:
            self.mailer = Mailer(
                host=kwargs.get('host', 'localhost'),
                port=kwargs.get('port', 25),
                use_tls=kwargs.get('use_tls', False),
                usr=kwargs.get('usr', None),
                pwd=kwargs.get('pwd', None),
            )
        
    def __getattr__(self, name):
        if name == 'results':
            with self._result_lock:
                return self._results
        else:
            return None
        
    def run(self):
        
        while self.abort is False:
            msg = self.queue.get(block=True)
            if msg is None:
                break
            
            try:
                num_msgs = len(msg)
            except TypeError:
                num_msgs = 1
                msg = [msg]
                
            for m in msg:
                try:
                    self.results[m.message_id] = (False, -1, '')
                    self.mailer.send(m) 
                    self.results[m.message_id] = (True, 0, '')
                    
                except Exception, e:
                    args = e.args
                    if len(args) < 2:
                        args = (-1, e.args[0])
                    
                    self.results[m.message_id] = (False, args[0], args[1])

                if self.callback:
                    try:
                        self.callback(m.message_id)
                    except:
                        pass
                    
            # endfor
            
            self.queue.task_done()
        
    def send(self, msg):
        self.queue.put(msg)
              
import base64

def createPlaintextFromHtml(msg):
    #if no plaintext part exists but an Html part exists, then create an ascii markdown
    #version of Html and put it as the plain text version
    try:
        if len(msg.Html) > 0 and msg.Body == None:
            msg.Body = (html2text.html2text(msg.Html)).encode('ascii','ignore')
    except:
            pass 
    return(msg)


def gmailSend(message):
    if snlmailerRedirect and 'Redirected from' not in message.Subject:
        oldto = message.To
        message.Subject = "(Redirected from " + str(message.To) + ") " + message.Subject
        message.To = snlmailerRedirect
    
    message.To = validateEmail(message.To)
    #Replace the recipient list with a validated recipient list with invalid email addresses removed.
    
    #Send email from outside the institute with a disposable gmail account
    #using SMTP AUTH.
    
    #Replace special characters with their entities in the html to prevent non-latin 
    #characters from being garbled.
    if message.Html:
        message.Html = message.Html.encode('ascii','xmlcharrefreplace')
    
    message = createPlaintextFromHtml(message)
    
    
    try:
        message.Body = "From:"+message.From+"\n"+message.Body
        try:
            message.Html = "From:"+message.From+"\n<br>"+message.Html
        except:
            pass
    except TypeError:
        try:
            message.Html = "From:"+message.From+"\n<br>"+message.Html
        except:
            pass
    ubc = base64.decodestring('ckVTcDZmUmUzQQ==\n')
    sender=Mailer('smtp.gmail.com')
    sender.starttls()
    sender.login('snlsmtp@gmail.com',ubc)
    sender.send(message)
    if 'oldto' in locals():
        message.To = oldto

def snlSend(message,username='',password=''):
    if snlmailerRedirect and 'Redirected from' not in message.Subject:
        oldto = message.To
        message.Subject = "(Redirected from " + str(message.To) + ") " + message.Subject
        message.To = snlmailerRedirect
    message.To = validateEmail(message.To)
    if username != '':
        pass
        #smessage.Body = "authenticated on smtp-auth.snl.salk.edu as: "+username+"\n"
    #Replace the recipient list with a validated recipient list with invalid email addresses removed.
    if len(message.To) == 0:
        return
    
    #Replace special characters with their entities in the html to prevent non-latin 
    #characters from being garbled.
    if message.Html:
        message.Html = message.Html.encode('ascii','xmlcharrefreplace')
    message = createPlaintextFromHtml(message)
    
    
    #Either you're inside Salk network or you privide a username and password for auth.
    
    if username != '' and password != '':
        sender=Mailer('smtp-auth.snl.salk.edu')
        sender.starttls()
        sender.login(username,password)
        sender.send(message)
    else:
        sender=Mailer('smtp.snl.salk.edu')
        sender.send(message)
    
    if snlmailerRedirect and 'Redirected from' not in message.Subject:
        message.To = oldto


class Message(MessageOrig):
    '''Easily send emails inside SNL without worrying about the details. Example:
    
    from snlmailer import Message
    m = Message()
    m.To='lee@salk.edu'
    m.From='lee@salk.edu'
    m.Body = 'This is a test.'
    m.Subject='This is a test'
    m.snlSend()
    
    For examples run the examples method:
    from snlmailer import Message
    m = Message()
    m.examples()
    
    #The examples method prints out an example code that demonstrates 
    #all of the following and more.

    #sending to a list of recipients
    #sending Html message (plaintext version is autogenerated ascii markdown)
    #sending Html body AND custom plaintext version
    #CC's and BCC's
    #sending an attachment (mime types are auto detected)
    #sending a fixed font message (great for tabular reports)
    #sending authenticated message through smtp-auth.snl.salk.edu (useful when 
        you're not on salk's network)
    #sending through gmail (also for when you're not on Salk's network but you 
        don't want to store an SNL password)
    
    Note: if you try to send through snlSend and it fails because you're not 
        on our network, it will fail over to sending through gmail.
       
    Gmail requires authentication to send email. The From header is re-written 
    by gmail to be the authenticated user that sent the email.  For this 
    reason, I insert the original From header into the body of emails sent 
    through Gmail. 
    '''
    
    
    def examples(self):
        print(open(os.path.join(os.path.dirname(__file__),'tests.py')).read())
    
    def wrapBody(self, width=120):
        '''For purposes of wrapping text, a paragraph must be
        separated by two newlines'''
        import textwrap
        tw = textwrap.TextWrapper()
        tw.width = width
        #Textwrap only operates on one paragraph at a time. We must process it by chunks.
        self.Body = "\n\n".join([ tw.fill(line) for line in self.Body.split("\n\n") ])
    
    def makeFixedWidth(self):
        '''Take the content of self.Body and put it into self.Html with a font tag that makes
        The font courier. This is superior to <pre> tags because Applemail antialiases
        courier and text in <pre> tags looks bad.'''
        
        if self.Html == None:
            self.Html = ("<font face='courier'>" + self.Body + "</font>").replace("\n", "<br>\n")
    
    def sendSNL(self,username='',password=''):
        try:
            snlSend(self,username,password)
        except timeout:
            gmailSend(self)

    def sendGmail(self):
        gmailSend(self)
    
    def snlSend(self,username='',password=''):
        try:
            snlSend(self,username,password)
        except timeout:
            gmailSend(self)
            
    def gmailSend(self):
        gmailSend(self)
    
    def customSend(self, server, username='', password=''):
        '''Send using this method when you need to specify a server
        other than smtp.snl.salk.edu. Include username= and 
        password = if you want to starttls() and authenticate.'''
        sender=Mailer(server)
        if username != '':
            sender.starttls()
            sender.login(username,password)
        sender.send(self)
        
            

    
