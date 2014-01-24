from django.conf.urls import patterns, include, url
import project.views
import upload.views
from pdb import set_trace as debug
import django.contrib.auth.views
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'project.views.home', name='home'),
    # url(r'^project/', include('project.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'register/login', django.contrib.auth.views.login),
    url(r'^login_user/$', 'project.views.login_user', name='login_user'),
    url(r'^/$', upload.views.Upload, name='upload'),
    url(r'^$', upload.views.Upload, name='upload'),
    url(r'bupload', upload.views.bUpload, name='bupload'),
    url(r'verifychunk', upload.views.verifychunk, name='verifychunk'),
    url(r'^freespace$', upload.views.freespace, name='freespace'),
    url(r'^logout_user/$', 'project.views.logout_user', name="logout_user"),
    url(r'^logged_out/$', TemplateView.as_view(template_name="logout_user.html") ),
)
