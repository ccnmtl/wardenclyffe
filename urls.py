from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
import os.path
admin.autodiscover()

site_media_root = os.path.join(os.path.dirname(__file__),"media")

urlpatterns = patterns('',
                       ('^$','main.views.index'),
                       ('^accounts/',include('djangowind.urls')),
                       (r'^admin/(.*)', admin.site.root),
                       (r'^capture/file_upload','main.views.test_upload'),
                       (r'^add_series/$','main.views.add_series'),
                       (r'^series/(?P<id>\d+)/$','main.views.series'),
                       (r'^file/(?P<id>\d+)/$','main.views.file'),
                       (r'^upload/$', 'main.views.upload'),
                       (r'^done/$','main.views.done'),
                       (r'^video/$','main.views.video_index'),
                       (r'^video/(?P<id>\d*)/$','main.views.video'),
                       (r'^video/(?P<id>\d*)/pcp_submit/$','main.views.video_pcp_submit'),
                       (r'^list_workflows/$','main.views.list_workflows'),
                       (r'^celery/', include('djcelery.urls')),
                       (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': site_media_root}),
                       (r'^uploads/(?P<path>.*)$','django.views.static.serve',{'document_root' : settings.MEDIA_ROOT}),
) 

