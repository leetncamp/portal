# imports

# import the django settings
from django.conf import settings
# for generating json
from django.utils import simplejson
# for loading template
from django.template import Context, loader
# for csrf
from django.core.context_processors import csrf
# for HTTP response
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
# for os manipulations
import os
from pdb import set_trace as debug
import datetime
import urllib
# used to generate random unique id
import uuid
from django.contrib.auth.decorators import login_required

import subprocess
from snlmailer import Message

import string
import re
escapeRE = re.compile("^\.\./|^\/|^\.\/")
valid_chars = "/-_.() %s%s" % (string.ascii_letters, string.digits)

def safe_filename(filename):
    #make sure it's safe. Pass it through a whitelist.
    ''.join(c for c in filename if c in valid_chars)
    count =1
    while count > 0:
        filename, count = re.subn(escapeRE, '', filename)
    return (''.join(c for c in filename if c in valid_chars) )


#@login_required(login_url='/login_user')
def Upload(request):

    """
    
    ## View for file uploads ##

    It does the following actions:
        - displays a template if no action have been specified
        - upload a file into unique temporary directory
                unique directory for an upload session
                    meaning when user opens up an upload page, all upload actions
                    while being on that page will be uploaded to unique directory.
                    as soon as user will reload, files will be uploaded to a different
                    unique directory
        - delete an uploaded file

    ## How Single View Multi-functions ##

    If the user just goes to a the upload url (e.g. '/upload/'), the request.method will be "GET"
        Or you can think of it as request.method will NOT be "POST"
    Therefore the view will always return the upload template

    If on the other side the method is POST, that means some sort of upload action
    has to be done. That could be either uploading a file or deleting a file

    For deleting files, there is the same url (e.g. '/upload/'), except it has an
    extra query parameter. Meaning the url will have '?' in it.
    In this implementation the query will simply be '?f=filename_of_the_file_to_be_removed'

    If the request has no query parameters, file is being uploaded.

    """

    

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

        # figure out the path where files will be uploaded to
        # PROJECT_DIR is from the settings file
        temp_path = os.path.join(settings.PROJECT_DIR, "uploads", request.session._get_or_create_session_key())
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
            if ufile.content_type not in options["acceptedformats"]:
                error = "acceptFileTypes"


            # the response data which will be returned to the uploader as json
            response_data = {
                "name": ufile.name,
                "size": ufile.size,
                "type": ufile.content_type
            }

            # if there was an error, add error message to response_data and return
            if error:
                # append error message
                response_data["error"] = error
                # generate json
                response_data = simplejson.dumps([response_data])
                # return response to uploader with error
                # so it can display error message
                return HttpResponse(response_data, mimetype='application/json')

            # make temporary dir if not exists already
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)            
            
            safename = safe_filename(ufile.name)
            filename = os.path.join(temp_path, safename)

            #Before writing the files out, create the group folder based on the date of the group.


            if not os.path.exists(temp_path):
                os.makedirs(temp_path)
                
            destination = open(filename, "wb+")
            # save file data into the disk
            # use the chunk method in case the file is too big
            # in order not to clutter the system memory
            for chunk in ufile.chunks():
                destination.write(chunk)
                # close the file
            destination.close()
            
            file(os.path.join(temp_path, "username.txt"), "w").write(request.user.username)
            gigsFree = subprocess.Popen(['df',"-h" , "."], stdout=subprocess.PIPE).communicate()[0].split("\n")[1].split()[3]
            tmpdir = os.path.join(settings.PROJECT_DIR, "uploads")
            filelisting = subprocess.Popen(["find", tmpdir, "-type", "f"], stdout=subprocess.PIPE).communicate()[0].split("\n")
            for banned in ['.DS_Store', "username.txt"]:
                filelisting = [fl for fl in filelisting if not banned in fl]
            commands = ''
            filelisting = "\n".join(filelisting)
            To = open('email.txt').read().replace(",","")
            To = [line for line in To.split("\n") if not line.startswith("#")]
            To = [line for line in To if line]
            debug()
            
            msg = Message(To=To, From='lee@salk.edu', Subject='{0} Uploaded Files'.format(request.user.username))
            msg.Body = "\nGigabytes free: {0}\n\nFile Listing: {1}".format(gigsFree, filelisting)
            for recipient in To:
                msg.To = recipient
                msg.gmailSend()
 
            # url for deleting the file in case user decides to delete it
            response_data["delete_url"] = request.path + "?" + urllib.urlencode(
                    {"f": os.path.join(temp_path.split(settings.PROJECT_DIR+"/")[1], ufile.name)})

            # specify the delete type - must be POST for csrf
            response_data["delete_type"] = "POST"

            # generate the json data
            response_data = simplejson.dumps([response_data])

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


            return HttpResponse(response_data, mimetype=response_type)

        else: # file has to be deleted
            
            #remove any attempts to escape the file name
            
            # get the file path by getting it from the query (e.g. '?f=filename.here')
            filename = safe_filename(request.GET["f"])
            filepath = os.path.join(settings.PROJECT_DIR, filename)

            
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
            response_data = simplejson.dumps(True)

            # return the result data
            # here it always has to be json
            return HttpResponse(response_data, mimetype="application/json")

    else: #GET

        # load the template

        t = loader.get_template("upload.html")
        c = Context({
            #The manuscript
            'manuscript':"manu",
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

