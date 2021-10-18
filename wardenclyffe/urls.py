from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
import django.views.static
from django_cas_ng import views as cas_views

from wardenclyffe.main.feeds import CollectionFeed
import wardenclyffe.main.views as views
import wardenclyffe.mediathread.views as mediathread_views
import wardenclyffe.panopto.views as panopto_views


admin.autodiscover()

urlpatterns = [
    url('^$', views.IndexView.as_view()),
    url('^dashboard/', views.DashboardView.as_view()),
    url('^recent_operations/', views.RecentOperationsView.as_view()),
    url('^slow_operations/', views.SlowOperationsView.as_view()),
    url('^most_recent_operation/', views.MostRecentOperationView.as_view()),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    path('cas/login', cas_views.LoginView.as_view(),
         name='cas_ng_login'),
    path('cas/logout', cas_views.LogoutView.as_view(),
         name='cas_ng_logout'),
    url(r'^admin/', admin.site.urls),
    url(r'^streamlogs/', include('wardenclyffe.streamlogs.urls')),
    url(r'^capture/file_upload', views.test_upload),
    url(r'^add_collection/$', views.AddCollectionView.as_view(),
        name='add-collection'),
    url(r'^collection/(?P<pk>\d+)/$', views.CollectionView.as_view(),
        name="collection-view"),
    url(r'^collection/(?P<pk>\d+)/videos/$',
        views.AllCollectionVideosView.as_view()),
    url(r'^collection/(?P<pk>\d+)/audio/$',
        views.CollectionEditAudioView.as_view(),
        name='collection-edit-audio'),
    url(r'^collection/(?P<pk>\d+)/public/$',
        views.CollectionEditPublicView.as_view(),
        name='collection-edit-public'),
    url(r'^collection/(?P<pk>\d+)/operations/$',
        views.AllCollectionOperationsView.as_view()),
    url(r'^collection/(?P<pk>\d+)/edit/$',
        views.EditCollectionView.as_view()),
    url(r'^collection/(?P<pk>\d+)/toggle_active/$',
        views.CollectionToggleActiveView.as_view()),
    url(r'^collection/(?P<pk>\d+)/mediathread_submit/$',
        mediathread_views.CollectionMediathreadSubmit.as_view()),
    url(r'^collection/(?P<pk>\d+)/delete/$',
        views.DeleteCollectionView.as_view()),
    url(r'^collection/(?P<id>\d+)/remove_tag/(?P<tagname>\w+)/$',
        views.RemoveTagFromCollectionView.as_view()),
    url(r'^collection/(?P<pk>\d+)/elastictranscode/$',
        views.ElasticTranscoderCollectionSubmitView.as_view(),
        name='elastictranscoder-collection-submit'),
    url(r'^collection/(?P<pk>\d+)/report/$',
        views.CollectionReportView.as_view(),
        name='collection-panopto-report'),
    url(r'^collection/(?P<id>\d+)/rss/$', CollectionFeed()),
    url(r'^video/(?P<pk>\d+)/edit/$', views.EditVideoView.as_view()),
    url(r'^video/(?P<pk>\d+)/s3serve/$', views.VideoS3Serve.as_view()),
    url(r'^video/(?P<id>\d+)/delete/$', views.DeleteVideoView.as_view()),
    url(r'^video/(?P<id>\d+)/remove_tag/(?P<tagname>\w+)/$',
        views.RemoveTagFromVideoView.as_view()),

    url(r'^server/$', views.ServersListView.as_view()),
    url(r'^server/add/$', views.AddServerView.as_view()),
    url(r'^server/(?P<pk>\d+)/$', views.ServerView.as_view()),
    url(r'^server/(?P<pk>\d+)/edit/$', views.EditServerView.as_view()),
    url(r'^server/(?P<pk>\d+)/delete/$', views.DeleteServerView.as_view()),

    url(r'^file/$', views.FileIndexView.as_view()),
    url(r'^file/(?P<id>\d+)/$', views.FileView.as_view()),
    url(r'^file/(?P<pk>\d+)/audio/$', views.AudioEncodeFileView.as_view(),
        name='audio_encode_file'),
    url(r'^file/(?P<pk>\d+)/delete_from_cunix/$',
        views.DeleteFromCunix.as_view(),
        name='delete-file-from-cunix'),
    url(r'^file/(?P<pk>\d+)/delete_from_s3/$',
        views.DeleteFromS3.as_view(),
        name='delete-file-from-s3'),

    url(r'^file/filter/$', views.FileFilterView.as_view()),
    url((r'^operation/(?P<uuid>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-'
         r'[a-z0-9]{4}-[a-z0-9]{12})/info/$'),
        views.OperationInfoView.as_view()),
    url((r'^operation/(?P<uuid>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-'
         r'[a-z0-9]{4}-[a-z0-9]{12})/$'),
        views.OperationView.as_view()),

    url(r'^bulk_operation/$', views.BulkOperationView.as_view(),
        name="bulk-operation"),
    url(r'^bulk_surelink/$', views.BulkSurelinkView.as_view(),
        name="bulk-surelink"),
    url(r'^user/(?P<username>\w+)/', views.UserView.as_view()),
    url(r'^file/(?P<id>\d+)/delete/$', views.DeleteFileView.as_view()),
    url(r'^file/(?P<id>\d+)/surelink/$', views.FileSurelinkView.as_view()),
    url(r'^operation/(?P<id>\d+)/delete/$',
        views.DeleteOperationView.as_view()),
    url(r'^operation/(?P<operation_id>\d+)/rerun/$',
        views.RerunOperationView.as_view()),
    url(r'^tag/$', views.TagsListView.as_view()),
    url(r'^tag/(?P<tagname>\w+)/$', views.TagView.as_view()),

    url(r'^upload/post/$', views.upload),
    url(r'^upload/$', views.UploadFormView.as_view()),

    url(r'^upload/batch/$', views.BatchUploadFormView.as_view()),
    url(r'^upload/batch/post/$', views.batch_upload),

    url(r'^mediathread/$', mediathread_views.mediathread),
    url(r'^mediathread/post/$', mediathread_views.mediathread_post),
    url(r'^panopto/', include('wardenclyffe.panopto.urls')),
    url(r'^received/$', views.ReceivedView.as_view()),

    url(r'^surelink/video/$', views.SureLinkVideoView.as_view()),
    url(r'^surelink/$', views.SureLinkView.as_view()),

    url(r'^video/$', views.VideoIndexView.as_view()),
    url(r'^video/(?P<pk>\d+)/$', views.VideoView.as_view(),
        name='video-details'),
    url(r'^video/(?P<id>\d+)/youtube/$',
        views.VideoYoutubeUploadView.as_view(), name="s3-to-youtube"),
    url(r'^video/(?P<id>\d+)/flv2mp4/$',
        views.FlvToMp4View.as_view(), name="video-flv-to-mp4"),
    url(r'^video/(?P<id>\d+)/mov2mp4/$',
        views.MovToMp4View.as_view(), name="video-mov-to-mp4"),
    url(r'^video/(?P<id>\d+)/mediathread_submit/$',
        mediathread_views.VideoMediathreadSubmit.as_view()),
    url(r'^video/(?P<id>\d+)/add_file/$', views.VideoAddFileView.as_view()),
    url(r'^video/(?P<id>\d+)/select_poster/(?P<image_id>\d+)/$',
        views.VideoSelectPosterView.as_view()),
    url(r'importflv/$', views.ImportFlv.as_view(), name='import-flv'),
    url(r'^search/$', views.SearchView.as_view(), name='search'),
    url(r'^uuid_search/$', views.UUIDSearchView.as_view()),
    url(r'^api/tagautocomplete/$', views.TagAutocompleteView.as_view()),
    url(r'^api/subjectautocomplete/$',
        views.SubjectAutocompleteView.as_view()),
    url(r'^api/sns/$', views.SNSView.as_view()),
    url(r'^api/cunixdelete/$', views.APICunixDelete.as_view(),
        name='api-cunix-delete'),
    url(r'^api/panopto/convert/$',
        panopto_views.APIPanoptoConversion.as_view(),
        name='api-panopto-conversion'),
    url('smoketest/', include('smoketest.urls')),
    url(r'^stats/$', TemplateView.as_view(template_name="main/stats.html")),
    url(r'^sign_s3/$', views.SignS3View.as_view(), name='sign-s3'),
    url(r'^uploads/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls))
    ]
