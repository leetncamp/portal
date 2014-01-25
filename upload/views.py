# imports

# import the django settings
from django.conf import settings
import json
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

import subprocess
from snlmailer import Message

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
    print("Starting upload")
    """
    
    ## View for browser-based file uploads ##

    It does the following actions:
        - displays a template if no action have been specified
        - upload a file into unique temporary directory
                unique directory for an upload session
                    meaning when user opens up an upload page, all upload actions
                    while being on that page will be uploaded to unique directory.
                    as soon as user reloads their browser, files will be uploaded 
                    to a different unique directory
        - delete an uploaded file

    ## How Single View Multi-functions ##

    If the user just goes to a the upload url (e.g. '/upload/'), the request.method will be "GET"
        Or you can think of it as request.method will NOT be "POST"
    Therefore the view will always return the upload template

    If on the other hand the method is POST, that means some sort of upload action
    has to be done. That could be either uploading a file or deleting a file

    For deleting files, there is the same url (e.g. '/upload/'), except it has an
    extra query parameter. Meaning the url will have '?' in it.
    In this implementation the query will simply be '?f=filename_of_the_file_to_be_removed'

    If the request has no query parameters, file is being uploaded.

    """

    if "MSIE" in request.META.get("HTTP_USER_AGENT"):
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
            "application/octet-stream", #This allows any binary file to be uploaded.  Be careful.
            "application/msword",
            "application/vnd.ms-excel",
            "application/vnd.ms-powerpoint",            
            )
    }


    # POST request
    #   meaning user has triggered an upload action

    if request.method == 'POST':

        print("Starting POST")
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

            print("Response data")
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
            print("Writing metadata")
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
                To = open(os.path.join(project_dir, 'email.txt')).read().replace(",","").split("\n")
            except Exception as e:
                print(e)
                To = []
            print("Sending Email")
            try:
                #Remove comment lines
                To = [line for line in To if not line.startswith("#")]
                #Parse the names
                To = " ".join(To).split()
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
def verifyfile(request):
    
    """The client sends information about a file and the
    server responds with a chunks manifest if there is
    an eeg file avaiable on this end."""
    
    request._load_post_and_files()
    filename = safe_filename(request._files['file'].read())
    filepath = os.path.join(upload_dir, filename)
    try:
        fullMD5 = request._files['fullMD5'].read()
        #If fullMD5 exists, assume you just want the 
        #md5sum of the entire eeg file.
        FULLMD5 = hashlib.md5(open(filepath, 'rb').read()).hexdigest()
        data = {"verified": FULLMD5 == fullMD5}
        return HttpResponse(json.dumps(data), mimetype='application/json')
    except KeyError:
        pass
    chunkSize = int(request._files['chunkSize'].read())
    conf = {}
    length = 0
    count = 0
    try:
        eegFile = open(filepath, "rb")
        eegFile.seek(0, 2)
        length = eegFile.tell()
        eegFile.seek(0)
        fullMD5 = hashlib.md5(eegFile.read()).hexdigest()
        eegFile.seek(0)
        eegFile.seek(0)
        try:
            for chunk in chunks(eegFile):
                conf[count] = hashlib.md5(chunk).hexdigest()
                count += 1
        except Exception as e:
            debug()
    except IOError:
        pass

    data = {"conf":conf, "length":length}
    return HttpResponse(json.dumps(data), mimetype='application/json')


@csrf_exempt
def bUpload(request):
    request._load_post_and_files()
    filename = safe_filename(request._files['filename'].read())
    filepath = os.path.join(upload_dir, filename)
    count = request._files['count'].read()
    if count == "0":
        try:
            os.remove(filepath)
        except OSError:
            pass
    metapath = filepath + ".meta.txt"
    chunk = request._files['file'].read()
    md5SUM = request._files['md5sum'].read()
    md5sum = hashlib.md5(chunk).hexdigest()
    success = md5SUM == md5sum
    if success:
        destFile = file(filepath, 'ab').write(zlib.decompress(chunk))
    data = {"status": success}
    return HttpResponse(json.dumps(data), mimetype='application/json')