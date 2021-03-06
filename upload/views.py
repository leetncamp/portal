# imports

# import the django settings
from django.conf import settings
import json
import pickle
from django.template import Context, loader
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
import os
from pdb import set_trace as debug
import datetime
import urllib
import zlib
import uuid
from django.contrib.auth.decorators import login_required
import hashlib
import traceback
import subprocess
from snlmailer import Message
from notify import notification_emails
import copy

import time
import glob
import string
import re

escapeRE = re.compile("^\.\./|^\/|^\.\/")
valid_chars = "/-_.() %s%s" % (string.ascii_letters, string.digits)

project_dir = settings.PROJECT_DIR
upload_dir = os.path.join(project_dir, "uploads")

uname = os.uname()

import pprint

ppr = pprint.PrettyPrinter(indent=4)


def safe_filename(filename):
    #make sure it's safe. Pass it through a whitelist.
    ''.join(c for c in filename if c in valid_chars)
    count =1
    while count > 0:
        filename, count = re.subn(escapeRE, '', filename)
    return (''.join(c for c in filename if c in valid_chars) )


sizeRE = re.compile("([\d\.]*)")
def getFreeSpace():
    
    if uname[0] == "Linux":
        units = "-BM"
    elif uname[0] == "Darwin":
        units = "-bm"
    else:
        units = ""
    tmpFree = subprocess.Popen(['df', units, "/tmp"], stdout=subprocess.PIPE).communicate()[0].split("\n")[1].split()[3]
    tmpFree = float(re.search(sizeRE, tmpFree).group(1)) / 1000
    rootFree = subprocess.Popen(['df', units, "/"], stdout=subprocess.PIPE).communicate()[0].split("\n")[1].split()[3]
    rootFree = float(re.search(sizeRE, rootFree).group(1)) / 1000
    uploadFree = min(tmpFree, rootFree)
    result = {"tmpFree":tmpFree, "uploadFree":uploadFree, "rootFree":rootFree}
    print result
    return result

def freespace(request):
    response_data = json.dumps(getFreeSpace())
    return HttpResponse(response_data, mimetype='application/json')

osRE = re.compile("\((.*?)\)")
clientNameRE = re.compile("domain\ name\ pointer\s(.*)\.")    

@login_required(login_url='/login_user')
def Upload(request):

    browser = request.META.get("HTTP_USER_AGENT", "").lower()
    if re.search("trident|msie", browser):
        incompatibleBrowser = "<h2>INCOMPATIBLE BROWSER, Try MS Edge, Firefox, Chrome or Opera</h2>"
    else:
        incompatibleBrowser = ""

    print("Starting upload")
    """
    
    ## View for browser-based file uploads using jquery-fileuploader ##

    It does the following actions:
        - displays a template if no action have been specified
        - upload a file into unique temporary directory
                unique directory for an upload session
                    meaning when user opens up an upload page, all upload actions
                    from that page will be uploaded to unique directory.
                    as soon as user reloads their browser, files will be uploaded 
                    to a different unique directory
        - delete an uploaded file
    """
    
    """This doesn't work in IE"""
    if "MSIE" in request.META.get("HTTP_USER_AGENT", u""):
        return(render_to_response("internetexplorer.html", context_instance=RequestContext(request)))
    
    freeSpace = getFreeSpace()
    # settings for the file upload
    #   you can define other parameters here
    #   and check validity late in the code
    options = {
        # the maximum file size (must be in bytes)
        "maxfilesize": 4000000000, # 4 Gb
        # the minimum file size (must be in bytes)
        "minfilesize": 0 * 2 ** 10, # 0 Kb
        # the file types which are going to be allowed for upload
        #   must be a mimetype
        "acceptedformats": (
            "application/txt",
            "image/jpeg",
            "image/tiff",
            "image/png",
            "application/pdf",
            'application/x-compressed',
            'application/x-zip-compressed',
            'application/zip',
            'multipart/x-zip',
            'image/x-eps',
            "video/x-msvideo",
            "image/bmp",
            "image/jp2",
            "video/x-m4v",
            "video/quicktime",
            "video/x-sgi-movie",
            "video/mp4",
            "video/mpeg",
            "application/x-tar",
            "application/octet-stream", 
            #This allows any binary file to be uploaded.  Be careful.
            "application/msword",
            "application/vnd.ms-excel",
            "application/vnd.ms-powerpoint",            
            )
    }


    # POST request
    #  user has triggered an upload action

    if request.method == 'POST':
        # figure out the path where files will be uploaded to
        # PROJECT_DIR is from the settings file
        temp_path = os.path.join(project_dir, "uploads", request.session._get_or_create_session_key())
        # if 'f' query parameter is not specified
        # file is being uploaded
        if not ("f" in request.GET.keys()): # upload file

            # make sure some files have been uploaded
            if not request.FILES:
                print("User tried to upload something that wasn't a file.")
                return HttpResponseBadRequest('Must upload a file')

            

            # update the temporary path by creating a sub-folder within
            # the upload folder with the uid name
            #temp_path = os.path.join(temp_path, uid)

            # get the uploaded file
            ufile = request.FILES[u'files[]']
            
            error = False

            # check against options for errors

            # file size
            if ufile.size > options["maxfilesize"]:
                error = "maxFileSize"
            if ufile.size < options["minfilesize"]:
                error = "minFileSize"
            # allowed file type
            #if ufile.content_type not in options["acceptedformats"]:
            #    error = "acceptFileTypes"

            # the response data which will be returned to the uploader as json
            response_data = {
                "name": ufile.name,
                "size": ufile.size,
                "type": ufile.content_type
            }
            print('Receiving file: {0}'.format(ufile.name))

            # if there was an error, add error message to response_data and return
            if error:
                # append error message
                response_data["error"] = error
                # generate json
                response_data = json.dumps([response_data])
                # return response to uploader with error
                # so it can display error message
                return HttpResponse(response_data, mimetype='application/json')
            
            print("Making Temp Directory")
            # make temporary dir if not exists already
            if not os.path.exists(temp_path):
                try:
                    os.makedirs(temp_path)
                except Exception as e:
                    print("Trying to create {0}".format(temp_path))
                    print(e)
            safename = safe_filename(ufile.name)
            filename = os.path.join(temp_path, safename)
            #Before writing the files out, create the group folder based on the date of the group.
            print("Create Group Folder")

            if not os.path.exists(temp_path):
                try:
                    os.makedirs(temp_path)
                except Exception as e:
                    print("Error tring to makedirs {0}".format(temp_path))
                    os.makedirs(temp_path)
            
            print("Opening Destination") 
            try:   
                destination = open(filename, "wb+")
            except Exception as e:
                print(e)
            # save file data into the disk
            # use the chunk method in case the file is too big
            # in order not to clutter the system memory
            print("Saving file")
            for chunk in ufile.chunks():
                try:
                    destination.write(chunk)
                except Exception as e:
                    print(e)
                # close the file
            print("Closing file")
            destination.close()
            ufile.close()
            meta = {"username":str(request.user.username)}
            browser = request.META.get("HTTP_USER_AGENT")
            meta['browser'] = browser.split()[-1]
            try:
                meta['os'] = re.search(osRE, browser).group(1)
            except exception as e:
                print (e)
                meta['os'] = 'Error {0}\n\n{1}'.format(browser, e)
            meta['client_address'] = request.META.get("REMOTE_ADDR")

            try:
                reverseLookup = os.popen("host {0}".format(meta['client_address'])).read()
                client_name = re.search(clientNameRE, reverseLookup).group(1)
            except Exception as e:
                client_name = reverseLookup
            meta['client_name'] = client_name
            metaStr = ppr.pformat(meta)

            try:
                file(os.path.join(temp_path, "metadata.txt"), "w").write(json.dumps(meta))
            except Exception as e:
                print(e)
            print("Metadata written")
            
            print('tmpdir')
            try:
                tmpdir = os.path.join(project_dir, "uploads")
            except Exception as e:
                print(e)
            print("Getting file listing")
            os.chdir(temp_path)
            filelisting = glob.glob("*")
            print("Removing banned files")
            for banned in ['.DS_Store', "username.txt"]:
                filelisting = [fl for fl in filelisting if not banned in fl]
            commands = ''
            filelisting = "\n".join(filelisting)
            try:
                To = notification_emails
                msg = Message(To=To, From='snlsmtp@gmail.com', Subject='User "{0}" uploaded Files'.format(request.user.username))
                msg.Body = "\nGigabytes free /uploads: {0}\nGigabytes free /tmp: {2}\n\nFile Listing for {4}:\n{1}\n\n{3}".format(freeSpace['rootFree'], filelisting, freeSpace['tmpFree'], metaStr, temp_path)
                msg.makeFixedWidth()
                for recipient in To:
                    try:
                        msg.To = recipient
                        msg.gmailSend()
                    except Exception as e:
                        print(e)
            except Exception as e:
                print(e)
            
            print("Getting delete handle")
            # url for deleting the file in case user decides to delete it
            response_data["delete_url"] = request.path + "?" + urllib.urlencode(
                    {"f": os.path.join(temp_path.split(project_dir+"/")[1], ufile.name)})

            # specify the delete type - must be POST for csrf
            response_data["delete_type"] = "POST"

            # generate the json data
            response_data = json.dumps([response_data])

            # response type
            response_type = "application/json"

            # QUIRK HERE
            # in jQuey uploader, when it falls back to uploading using iFrames
            # the response content type has to be text/html
            # if json will be send, error will occur
            # if iframe is sending the request, it's headers are a little different compared
            # to the jQuery ajax request
            # they have different set of HTTP_ACCEPT values
            # so if the text/html is present, file was uploaded using jFrame because
            # that value is not in the set when uploaded by XHR
            if "text/html" in request.META["HTTP_ACCEPT"]:
                response_type = "text/html"

            # return the data to the uploading plugin

            print("Returning Response")
            return HttpResponse(response_data, mimetype=response_type)

        else: # file has to be deleted
            
            #remove any attempts to escape the file name
            
            # get the file path by getting it from the query (e.g. '?f=filename.here')
            filename = safe_filename(request.GET["f"])
            filepath = os.path.join(project_dir, filename)

            
            # make sure file exists
            # if not return error
            if not os.path.isfile(filepath):
                return HttpResponseBadRequest("File does not exist")

            # delete the file
            # this step might not be a secure method so extra
            # security precautions might have to be taken
            os.remove(filepath)

            # generate true json result
            # in this case is it a json True value
            # if true is not returned, the file will not be removed from the upload queue
            response_data = json.dumps(True)

            # return the result data
            # here it always has to be json
            return HttpResponse(response_data, mimetype="application/json")

    else: #GET

        # load the template
        t = loader.get_template("upload.html")
        c = Context({
            #The manuscript
            'freeSpace':freeSpace,
            # the unique id which will be used to get the folder path
            "uid": "uid",
            # these two are necessary to generate the jQuery templates
            # they have to be included here since they conflict with django template system
            "open_tv": u'{{',
            "close_tv": u'}}',
            # some of the parameters to be checked by javascript
            "maxfilesize": options["maxfilesize"],
            "minfilesize": options["minfilesize"],
            "incompatibleBrowser": incompatibleBrowser,
            })
        # add csrf token value to the dictionary
        c.update(csrf(request))
        # return
        return HttpResponse(t.render(c))


chunkSize = 1000000

def chunks(fileObj):
    cont = True
    while cont:
        chunk = "".join(fileObj.readlines(chunkSize))
        cont = chunk != ''
        yield(zlib.compress(chunk))

@csrf_exempt
def bUpload(request):

    "binary Upload and full md5sum verification"
    
    request._load_post_and_files()
    data = pickle.loads(request._files['data'].read())
    meta = data['meta']
    filename = safe_filename(data['file'])
    folder = meta['uploadInfo'].get("company", "")
    working_folder = os.path.join(upload_dir, folder)
    filepath = os.path.join(working_folder, filename)
    
    #if there is an error blog to be written
    errors = data.get('errors', None)
    if errors:
        errorpath = os.path.join(working_folder, "errors.txt")
        try:
            file(errorpath, "wb").write(errors)
            status = pickle.dumps("errors written")
        except Exception as e:
            status = pickle.dumps("failed to write errors")
        return HttpResponse(status, mimetype="application/binary")
    
    
    """if there is a fullMD5 key, we are doing a verify. send back verification
    notice and write out this file's metadata. """
    
    fullMD5 = data.get("fullMD5", None)
    if fullMD5:
        
        """Write out the metadata pickle and verify md5"""
        
        """The data dict contains info about all files. Remove unneeded
        information and flatten the structure"""

        metapath = filepath + ".metadata.pickle"
        #Make a copy of the original to prevent self reference as I flatten.
        thisFilesMeta = copy.deepcopy(meta['files'][data['file']])
        del meta['files']
        meta.update(thisFilesMeta)
        print meta
        pickle.dump(meta, file(metapath, 'wb'))
        #Remove from memory.
        del thisFilesMeta
        
        
        
        """This is a request to verify the fullmd5 on an existing upload."""
        
        myMD5 = hashlib.md5(open(filepath, "rb").read()).hexdigest()
        if myMD5 == fullMD5:
            status = pickle.dumps("verified")
        else:
            status = pickle.dumps("not verified")
        return HttpResponse(status, mimetype="application/binary")
    
    #Store data in folders based on company name 
    
    if folder:
        
        try:
            os.makedirs(working_folder)
        except OSError:
            pass
        
        count = data['count']
        if count == 0:
            try:
                os.remove(filepath)
            except OSError:
                pass

        chunk = data['chunk']
        chunkMD5 = data['chunkMD5']
        md5sum = hashlib.md5(chunk).hexdigest()
        success = chunkMD5 == md5sum

        if success:
            try:
                destFile = file(filepath, 'ab').write(zlib.decompress(chunk))
                filewritten = True
            except Exception as e:
                filewritten = False
            result = {"status": success and filewritten}
    else:
        result = {"status": "failed due to lack of Company name"}
    return HttpResponse(pickle.dumps(result), mimetype='application/binary')






@csrf_exempt    
def checkstatus(request, version=None):
    request._load_post_and_files()
    meta = pickle.loads(request._files['meta'].read())
    version = float(version)
    if version >.85 and version < 2.0:

        """We recieve a dictionary that contains metadata about each file and then
        add more metadata about each file. The dictionary looks like this. Our
        job here is to check to see if the file needs to be uploaded based on
        file size. If the file can be resumed, send a manifest of md5
        signatures on the chunks.
    
    
        META = { 
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
                    "uploaded": datetimeobj, # (or none)
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

        files = meta['files']
        data_dir = os.path.join(upload_dir, meta['uploadInfo']['company'])
        for fn in files:
            thisFile = files[fn]
            try:
                f = open(os.path.join(data_dir, fn), "rb")
                f.seek(0,2)
                serverLength = f.tell()
                clientLength = thisFile['length']
                thisFile['serverstatus'] = "uploaded" if clientLength == serverLength else "resume needed"
                if thisFile['serverstatus'] == "resume needed":
                    #This file can be resumed. Send a chunksmanifest.
                    chunkSize = meta['uploadInfo']['chunkSize']
                    chunkManifest = {}
                    length = 0
                    count = 0
                    try:
                        f.seek(0)
                        fullMD5 = hashlib.md5(f.read()).hexdigest()
                        f.seek(0)

                        for chunk in chunks(f):
                            chunkManifest[count] = hashlib.md5(chunk).hexdigest()
                            count += 1
                        thisFile['chunkManifest'] = chunkManifest

                    except IOError:
                        pass
                
            except IOError:
                thisFile['serverstatus'] = "upload needed"

        return HttpResponse(pickle.dumps(meta), mimetype='application/binary')    
        
    else:
        data={"status":"version not supported", "message":"This version of the uploader, {0}, is not supported by the upload server.".format(version)}
        return HttpResponse(pickle.dumps(data), mimetype='application/binary')