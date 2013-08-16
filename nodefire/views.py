# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404,redirect
from django.http import HttpResponse
from django.template import RequestContext
from automate.production.views import menutext
from nodefire.flyout_menu import FireMenu
from pdb import set_trace as debug


def nodefire_test(request):

    menu=FireMenu()
    #The old way
    '''
    menu.add('Dashboard','/',['menu'])
    menu.add('Databases', '/admin',['menu','parent'])
    menu.add('Manuscripts',"/admin/manuscripts", ['subitem'])
    menu.add('Authors',"/admin/authors", ['subitem'])
    menu.pop()
    menu.add('Batches','/automate/batchlist',['menu','parent'])
    menu.add('24','/automate/batchlist',['subitem', 'parent'])
    menu.add('24.1', '/automate/batchlist?view=24.1',['subitem'])
    menu.add('24.2', '/automate/batchlist?view=24.2',['subitem'])
    menu.pop()
    menu.add('25','/automate/batchlist',['subitem', 'parent'])
    menu.add('25.1', '/automate/batchlist?view=25.1',['subitem'])
    menu.add('25.2', '/automate/batchlist?view=25.2',['subitem'])
    menu.top()
    menu.add('Final Lineups',"/automate/final2",['menu'])

    #menu.top()
    print menu.html()
    '''
    
    menu.add("All","/nodefire",['menu'])
    print menu.html()
    debug()
    menu.add('One',"/nodefire",['subitem'])
    print menu.html()
    debug()
    menu.add('Dashboard',"/nodefire",['menu'])
    print menu.html()
    debug()
    return render_to_response('nodefire_test.html', {'menu':menu},
        context_instance=RequestContext(request))
