# Create your views here.

from django.template.context import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from pdb import set_trace as debug
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
import json
import sys
from nodefire.flyout_menu import FireMenu

#For the example menus
from polls.models import *




#@login_required(login_url='/login_user')
def pollm(request):
    return render_to_response('poll.html',{'request':request},\
    context_instance=RequestContext(request))
    
def menutext(menu=None):
    """return the menutext html that populates the flyout menus"""
    if not menu:
        menu = FireMenu()
    menu.add("", 'javascript:void(0);',['menu','parent'],img="/static/admin/img/settingsGear.png", imgSize=(30,20))
    menu.add('Dashboard','/',['subitem'])
    menu.add('Get Production','/production/getproduction',['subitem'])
    menu.add('Reorder Authors','/production/namereorder',['subitem'])
    menu.add('Complete Batch','/automate/completebatch',['subitem'])
    menu.add('Page # from Batch Proofs','/automate/batchproofs',['subitem'])
    menu.add('Freeze and Unfreeze','/automate/freeze',['subitem'])
    menu.add('Address Lists','/production/authoraddresslist',['subitem'])
    menu.add('Database','/admin',['subitem','parent'])
    menu.add('Manuscripts','/automate/admin/production/manuscript/',['subitem'])
    menu.add('Authors','/automate/admin/production/author/',['subitem'])
    menu.add('Add Batch Deadlines','/automate/createbatchreminders/',['subitem'])
    menu.add('Existing Batch Deadlines','/automate/admin/production/reminder/',['subitem'])
    menu.add('Author Name Cleanup','/automate/admin/production/authornamecleanup/',['subitem'])
    menu.add('Database Users','/automate/admin/auth/user/',['subitem']),
    menu.add('Transactions','/automate/admin/production/transaction/',['subitem']),
    menu.add('Logout','/logout_user/',['subitem']),
    menu.pop() #outdent
    return(menu)


    

    


def poll(request):
    
    #This forces this context to include a CSRF cookie. Without this
    #you'll get an CSRF error when using AJAX.  See also the javascript code snippet 
    #in the list.html template that must be present to put the CSRF
    #token back into json posts. 
    request.META['CSRF_COOKIE_USED'] = True
    
    if request.is_ajax():
        newrank = request.POST.getlist('rank[]')
        #jquery seems to add the [] characters onto the the name
        #beause i'm sending it as 'rank' and it comes in as 'rank[]'

        try:
            
            if  len(newrank) > 0:
                #Here we modify the database to reflect the new rank
                #assiming there is a newrank response in the post data
                data = Listdata.objects.all().order_by('rank')
                        
                #Convert the newrank array that came in by ajax from strings
                #to numbers. Originally it is an array of strings.
                newrank = map(int, newrank)
            
                #Re-order the database objects
                for dd in data:
                    index = newrank.index(dd.rank)
                    if index != dd.rank:
                        print(str(dd.rank) + " -mm-> " + str(index) )
                        dd.rank = index
                        dd.save()
            else:
                print("when updating ranks in jquery sortable, wrong number of ranks found")
                raise IndexError

        except:
            errorTxt = sys.exc_info()
            errors = {'status':False, 'textStatus':str(errorTxt)}
            print("Error.  Changes for " + str(request.user) + " may be lost." + str(errors))
            return(HttpResponse(json.dumps(errors), mimetype="application/json"))
        
    
    data = Listdata.objects.all().order_by('rank')
    #Make the ranks a sequence of numbers. Just in case there are multiple 
    #objects with the same rank.
    count = 0
    for d in data:
        if d.rank != count:
            d.rank = count
            d.save()
        count +=1
    

    return render_to_response('poll.html', {'data':data, 'menutext':menutext()}, \
        context_instance=RequestContext(request))