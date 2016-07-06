from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from wardenclyffe.main.feeds import CollectionFeed
import wardenclyffe.main.views as views
import wardenclyffe.mediathread.views as mediathread_views
from django.views.generic import TemplateView
admin.autodiscover()

urlpatterns = patterns(
    '',
    ('^$', views.IndexView.as_view()),
    ('^dashboard/', views.DashboardView.as_view()),
    ('^recent_operations/', views.RecentOperationsView.as_view()),
    ('^slow_operations/', views.SlowOperationsView.as_view()),
    ('^most_recent_operation/', views.MostRecentOperationView.as_view()),
    ('^accounts/', include('djangowind.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^drop/', include('wardenclyffe.drop.urls')),
    (r'^capture/file_upload', 'wardenclyffe.main.views.test_upload'),
    (r'^add_collection/$', views.AddCollectionView.as_view()),
    (r'^collection/(?P<pk>\d+)/$', views.CollectionView.as_view()),
    (r'^collection/(?P<pk>\d+)/videos/$',
     views.AllCollectionVideosView.as_view()),
    url(r'^collection/(?P<pk>\d+)/audio/$',
        views.CollectionEditAudioView.as_view(),
        name='collection-edit-audio'),
    (r'^collection/(?P<pk>\d+)/operations/$',
     views.AllCollectionOperationsView.as_view()),
    (r'^collection/(?P<pk>\d+)/edit/$',
     views.EditCollectionView.as_view()),
    (r'^collection/(?P<pk>\d+)/toggle_active/$',
     views.CollectionToggleActiveView.as_view()),
    (r'^collection/(?P<pk>\d+)/mediathread_submit/$',
     mediathread_views.CollectionMediathreadSubmit.as_view()),
    (r'^collection/(?P<pk>\d+)/delete/$',
     views.DeleteCollectionView.as_view()),
    (r'^collection/(?P<id>\d+)/remove_tag/(?P<tagname>\w+)/$',
     views.RemoveTagFromCollectionView.as_view()),
    (r'^collection/(?P<id>\d+)/rss/$', CollectionFeed()),
    (r'^video/(?P<pk>\d+)/edit/$', views.EditVideoView.as_view()),
    (r'^video/(?P<id>\d+)/delete/$', views.DeleteVideoView.as_view()),
    (r'^video/(?P<id>\d+)/remove_tag/(?P<tagname>\w+)/$',
     views.RemoveTagFromVideoView.as_view()),

    (r'^server/$', views.ServersListView.as_view()),
    (r'^server/add/$', views.AddServerView.as_view()),
    (r'^server/(?P<pk>\d+)/$', views.ServerView.as_view()),
    (r'^server/(?P<pk>\d+)/edit/$', views.EditServerView.as_view()),
    (r'^server/(?P<pk>\d+)/delete/$', views.DeleteServerView.as_view()),

    (r'^file/$', views.FileIndexView.as_view()),
    (r'^file/(?P<id>\d+)/$', views.FileView.as_view()),
    url(r'^file/(?P<pk>\d+)/audio/$', views.AudioEncodeFileView.as_view(),
        name='audio_encode_file'),

    (r'^file/filter/$', views.FileFilterView.as_view()),
    ((r'^operation/(?P<uuid>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-'
      r'[a-z0-9]{4}-[a-z0-9]{12})/info/$'),
     views.OperationInfoView.as_view()),
    ((r'^operation/(?P<uuid>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-'
      r'[a-z0-9]{4}-[a-z0-9]{12})/$'),
     views.OperationView.as_view()),

    url(r'^bulk_operation/$', views.BulkOperationView.as_view(),
        name="bulk-operation"),
    url(r'^bulk_surelink/$', views.BulkSurelinkView.as_view(),
        name="bulk-surelink"),
    (r'^user/(?P<username>\w+)/', views.UserView.as_view()),
    (r'^file/(?P<id>\d+)/delete/$', views.DeleteFileView.as_view()),
    (r'^file/(?P<id>\d+)/surelink/$', views.FileSurelinkView.as_view()),
    (r'^operation/(?P<id>\d+)/delete/$', views.DeleteOperationView.as_view()),
    (r'^operation/(?P<operation_id>\d+)/rerun/$',
     views.RerunOperationView.as_view()),
    (r'^tag/$', views.TagsListView.as_view()),
    (r'^tag/(?P<tagname>\w+)/$', views.TagView.as_view()),

    (r'^upload/post/$', 'wardenclyffe.main.views.upload'),
    (r'^upload/$', views.UploadFormView.as_view()),

    (r'^upload/batch/$', views.BatchUploadFormView.as_view()),
    (r'^upload/batch/post/$', 'wardenclyffe.main.views.batch_upload'),

    (r'^mediathread/$', 'wardenclyffe.mediathread.views.mediathread'),
    (r'^mediathread/post/$',
     'wardenclyffe.mediathread.views.mediathread_post'),
    (r'^youtube/$', 'wardenclyffe.youtube.views.youtube'),
    (r'^youtube/post/$', 'wardenclyffe.youtube.views.youtube_post'),
    (r'^youtube/done/$', 'wardenclyffe.youtube.views.youtube_done'),
    (r'^received/$', views.ReceivedView.as_view()),
    (r'^surelink/$', views.SureLinkView.as_view()),
    (r'^video/$', views.VideoIndexView.as_view()),
    (r'^video/(?P<pk>\d+)/$', views.VideoView.as_view()),
    url(r'^video/(?P<id>\d+)/youtube/$',
        views.VideoYoutubeUploadView.as_view(), name="s3-to-youtube"),
    (r'^video/(?P<id>\d+)/mediathread_submit/$',
     mediathread_views.VideoMediathreadSubmit.as_view()),
    (r'^video/(?P<id>\d+)/add_file/$', views.VideoAddFileView.as_view()),
    (r'^video/(?P<id>\d+)/select_poster/(?P<image_id>\d+)/$',
     views.VideoSelectPosterView.as_view()),
    (r'^search/$', views.SearchView.as_view()),
    (r'^uuid_search/$', views.UUIDSearchView.as_view()),
    (r'^api/tagautocomplete/$', views.TagAutocompleteView.as_view()),
    (r'^api/subjectautocomplete/$', views.SubjectAutocompleteView.as_view()),
    (r'^api/sns/$', views.SNSView.as_view()),
    (r'^celery/', include('djcelery.urls')),
    ('smoketest/', include('smoketest.urls')),
    (r'^stats/$', TemplateView.as_view(template_name="main/stats.html")),
    (r'^stats/auth/$',
     TemplateView.as_view(template_name="main/auth_stats.html")),
    url(r'^sign_s3/$', views.SignS3View.as_view(), name='sign-s3'),
    (r'^uploads/(?P<path>.*)$',
     'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),
)
