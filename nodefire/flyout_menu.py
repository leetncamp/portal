#!/usr/bin/env python
# encoding: utf-8
"""
flyout-menu.py

Created by leetncamp on 2012-07-12.
Copyright (c) 2012 __MyCompanyName__. All rights reserved.
"""

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse_lazy

from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.etree import ElementTree
from xml.dom import minidom
from pdb import set_trace as debug



class FireMenu():
    #Anchor classes
    classes = {
    'outerUL':"qmmc qm-horizontal-c",
    'menu':"qmitem-m",
    'parent':"qmparent",
    'ul':'qmsub',
    'subitem':'qmitem-s',
    }  #Remember to add id='qm0' to the top ul.
    

    
    
    
    def __init__(self):
        self.pos =[ Element('ul', attrib = {'id':"qm0", 'class':self.classes['outerUL']}) ]
        #self.pos is a stack holding the position of the thing you're inserting into.  
        self.elist = []

    def html(self):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(self.pos[0], 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="    ").replace('<?xml version="1.0" ?>',"")
        
    def add(self, name, href, types, img=None, imgSize=None):
        '''
        Types is a list containing one or more of these
        'menu', 'subitem', 'parent'
        Top level links should be ['menu'].
        Top level menus with subitems below them should be ['menu', 'parent']
        Those subitems should be ['subitem']
        Subitems that themselves have subitems should be ['subitem', 'parent']
        
        'Name' is the name of the menu and 'href' is what it should point to.
        When you are finished inserting submenus, call self.outdent() to outdent.
        img is an optional href to an image to include next to the link text
        imgSize is an optional tuple containing the width and height in px
        '''

        if 'parent' in types:
            myclasses = self.classes['parent']
        else:
            myclasses = ''
        if 'menu' in types:
            myclasses += " "+self.classes['menu']
        if 'subitem' in types:
            myclasses += " "+self.classes['subitem']

        li = SubElement(self.pos[-1], 'li')
        #Append these to a list, elist,so they don't get garbage collected. 
        self.elist.append(li)
        a =  SubElement(li, 'a', attrib={'class':myclasses.strip(),'href':href})
        
        if img:
            if imgSize:
                image = SubElement(a, 'img', attrib={'src':img, 'width':str(imgSize[0]), 'height':str(imgSize[1])})
            else:
                image = SubElement(a, 'img', attrib={'src':img})
        
        self.elist.append(a)
        a.text = name
        #If this is a parent, then start a new <ul> and push it onto the 
        #position stack.
        if 'parent' in types:
            ul = SubElement(li, 'ul', attrib={'class':self.classes['ul']})
            self.pos.append(ul)

        
    def outdent(self):
        self.pos.pop()
        
    def pop(self):
        self.pos.pop()
    
    def top(self):
        while len(self.pos) > 1:
            self.pop()
        
        
        
def main():
    menu=FireMenu()
    menu.add('Dashboard','/',['menu'])
    menu.add('Databaes', '/admin',['menu','parent'])
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

    #menu.top()
    print menu.html()


##This code is old and not used any longer.
class FlyoutMenu():
    '''A class to hold a navigation menu structure. One flyout instance
    will hold one menu plus all of it's flyouts. To create several
    menus, as on the NIPS.cc site, you'll need to pass several instances.

    The structure attribute should hold a list of dictionaries.  The dictionary
    should contain menu titles for keys and URLS for those menu titles as values.
    The value of a key can also be another list of dictionaries, which creates
    a submenu.

    Use the .as_list() method in your template to render the structure to 
    an HTML nested list. This is useful for the Filament Group type of 
    jquery flyout menus. This method terminates lines with the 
    continuation character so the line can be quoted in javascript as a 
    multiline string. 
    
    See the file fg.menu.js to customize what happens when you actually click a
    link in a menu structure. Remember not to edit files in /admin/js. The
    get replaced by collectstatic.
    '''
    def pprint(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def pp(self):
        self.pp(self.top)
        
    def insert_menu(self, parent, menuDict):
        """Insert a menu item that has no flyouts. It's just an <li> element."""
        newmenu = SubElement(parent, 'li')
        link = SubElement(newmenu,'a',{'href':menuDict.values()[0],'class':'qmitem-s','title':menuDict.keys()[0]})
        link.text=menuDict.keys()[0]
        return(newmenu)
    
    def insert_submenu(self, parent, menuList):
        """place a submenu below parent"""
        #First create the menu item <li> that will have menu name and it's flyouts
        newli = self.insert_menu(parent, menuList[0])
        subui = SubElement(newli,'ul',attrib = {'class':'gmsub'})
        for subitem in menuList[1]:
            if type(subitem) == type([]):
                self.insert_submenu(subui, subitem)
            elif type(subitem) == type({}):
                self.insert_menu(subui, subitem)


    def from_list(self, menuList):
        """Return an html blob suitable for passing to the FilamentGroup.com
        flyout menu widget. Build the blob from a python list as detailed above."""

        self.top = Element('ul', attrib = {'id':"qm0", 'class':"qmmc qm-horizontal-c"})
        for item in menuList:
            if type(item) == type({}):
                self.insert_menu(self.top,item)
            elif type(item) == type([]):
                self.insert_submenu(self.top, item)
            else:
                print("Broken menuList passed to FlyoutMenu.from_list(menuList)")
        
        #Get the string version
        html = self.pprint(self.top)
        #Get rid of the XML header that minidom inserts
        html=html.replace("<?xml version=\"1.0\" ?>\n","")
        print html
        #Javascript needs line continuation marks before return characters
        html = html.replace("\n","\\\n")
        #Mark it safe so Django won't escape it.
        return(mark_safe(html))
        
    

def mmain():
    '''This example flyout menu list has three flat menus, Freeze, Complete Batch and Set Batch 
    followed by the Admin menu which has 4 flyouts.  Followed by the Batches menu which has 
    multilevel flyouts, followed by the Final Lineups menu, which also has multilevel 
    flyouts. Finally we return to just have a flat Complete Batch 2 menu'''

    fmList = \
        [
            {'Complete Batch': '/automate/completebatch'}, 
            {'Set Batch Pages': '/automate/batchproofs'}, 
            {'Freeze and Unfreeze': '/automate/freeze'}, 
            [{'Admin': '/admin'}, [
                    {'Manuscripts': '/automate/admin/production/manuscript/'}, 
                    {'Authors': '/automate/admin/production/author/'}, 
                    {'Author Name Cleanup': '/automate/admin/production/authornamecleanup/'}, 
                    {'Batch Deadlines': '/automate/admin/production/reminder/'}
                    ]
            ], 

            [{'Batches': '/automate/batchlist'}, 
                [   {'24': '/automate/batchlist'}, 
                        [
                            {'2': '/automate/batchlist?view=24.2'}, 
                            {'3': '/automate/batchlist?view=24.3'}, 
                        ],
                    {'25':'/automate/batchlist'}, [
                        {'2': '/automate/batchlist?view=25.2'},
                        {'3': '/automate/batchlist?view=25.3'},
                    ]        
                ]    
            ], 

            [{'Final Lineups': '/automate/final2'}, 
                [   {'24': '/automate/final2'}, [
                        {'2': '/automate/final2?issue=24.2'}, 
                        {'3': '/automate/final2?issue=24.3'}, 
                        ],
                    {'25':'/automate/final2'}, [
                        {'2': '/automate/final2?issue=25.2'},
                        {'3': '/automate/final2?issue=25.3'},
                    ]
                        
                ]
            ],
            {"Complete Batch 2":"/automate/completebatch"},
        ]

    

    
    
    fm = FlyoutMenu()
    fm.from_list(fmList)



if __name__ == '__main__':
    main()

