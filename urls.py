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
                       (r'^series/(?P<id>\d+)/edit/$','main.views.edit_series'),
                       (r'^series/(?P<id>\d+)/delete/$','main.views.delete_series'),
                       (r'^series/(?P<id>\d+)/remove_tag/(?P<tagname>\w+)/$','main.views.remove_tag_from_series'),
                       (r'^video/(?P<id>\d+)/edit/$','main.views.edit_video'),
                       (r'^video/(?P<id>\d+)/delete/$','main.views.delete_video'),
                       (r'^video/(?P<id>\d+)/remove_tag/(?P<tagname>\w+)/$','main.views.remove_tag_from_video'),
                       (r'^file/$','main.views.file_index'),
                       (r'^file/(?P<id>\d+)/$','main.views.file'),
                       (r'^user/(?P<username>\w+)/','main.views.user'),
                       (r'^file/(?P<id>\d+)/delete/$','main.views.delete_file'),
                       (r'^operation/(?P<id>\d+)/delete/$','main.views.delete_operation'),
                       (r'^tag/$','main.views.tags'),
                       (r'^tag/(?P<tagname>\w+)/$','main.views.tag'),
                       (r'^upload/$', 'main.views.upload'),
                       (r'^scan_directory/$', 'main.views.scan_directory'),
                       (r'^vitaldrop/$', 'main.views.vitaldrop'),
                       (r'^vitaldrop/done/$', 'main.views.vitaldrop_done'),
                       (r'^mediathread/$', 'main.views.mediathread'),
                       (r'^done/$','main.views.done'),
                       (r'^video/$','main.views.video_index'),
                       (r'^video/(?P<id>\d+)/$','main.views.video'),
                       (r'^video/(?P<id>\d+)/pcp_submit/$','main.views.video_pcp_submit'),
                       (r'^video/(?P<id>\d+)/mediathread_submit/$','main.views.video_mediathread_submit'),
                       (r'^video/(?P<id>\d+)/zencoder_submit/$','main.views.video_zencoder_submit'),
                       (r'^video/(?P<id>\d+)/add_file/$','main.views.video_add_file'),
                       (r'^list_workflows/$','main.views.list_workflows'),
                       (r'^celery/', include('djcelery.urls')),
                       (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': site_media_root}),
                       (r'^uploads/(?P<path>.*)$','django.views.static.serve',{'document_root' : settings.MEDIA_ROOT}),
) 

