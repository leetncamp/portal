# Create your views here.
from datetime import datetime, timedelta
from django.template.context import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from pdb import set_trace as debug
from django.contrib.auth.models import User
import re
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
import datetime
from django.contrib.auth import authenticate, login
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout



def login_user(request):
    try:
        if "MSIE" in request.META.get("HTTP_USER_AGENT"):
            return(render_to_response("internetexplorer.html", context_instance=RequestContext(request)))
    except Exception as e:
        print traceback.format_exc()
        return(render_to_response("internetexplorer.html", context_instance=RequestContext(request)))
    state = "Please log in below..."
    username = password = ''
    if request.method == "GET":
        nextp = request.GET.get('next',"/")
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        nextp = request.POST.get('nextp', "/")

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                state = "You're successfully logged in!"
                return(redirect(nextp))
            else:
                state = "Your account is not active, please contact the site admin."
        else:
            state = "Your username and/or password were incorrect."

    return render_to_response('login_user.html',{'state':state, 'username': username,\
    'nextp':nextp},context_instance=RequestContext(request))
    
def logout_user(request):
    #state = "You have been logged out..."
    #username = password = ''
    logout(request)
    if request.GET:
        nextp = request.GET.get('next')
    else:
        nextp=None
    
    if nextp:
        return(redirect(nextp))
    else:
        return render_to_response('logout_user.html',{\
        'nextp':nextp},context_instance=RequestContext(request))
