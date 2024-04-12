from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
import django.views.static
from django_cas_ng import views as cas_views

from wardenclyffe.main.feeds import CollectionFeed
import wardenclyffe.main.views as views
import wardenclyffe.mediathread.views as mediathread_views
import wardenclyffe.panopto.views as panopto_views


admin.autodiscover()

urlpatterns = [
    path('', views.IndexView.as_view()),
    path('dashboard/', views.DashboardView.as_view()),
    path('recent_operations/', views.RecentOperationsView.as_view()),
    path('slow_operations/', views.SlowOperationsView.as_view()),
    path('most_recent_operation/', views.MostRecentOperationView.as_view()),
    path('accounts/', include('django.contrib.auth.urls')),
    path('cas/login', cas_views.LoginView.as_view(),
         name='cas_ng_login'),
    path('cas/logout', cas_views.LogoutView.as_view(),
         name='cas_ng_logout'),
    path('admin/', admin.site.urls),
    path('streamlogs/', include('wardenclyffe.streamlogs.urls')),
    path('capture/file_upload', views.test_upload),
    path('add_collection/', views.AddCollectionView.as_view(),
         name='add-collection'),
    re_path(r'^collection/(?P<pk>\d+)/$', views.CollectionView.as_view(),
            name="collection-view"),
    re_path(r'^collection/(?P<pk>\d+)/videos/$',
            views.AllCollectionVideosView.as_view()),
    re_path(r'^collection/(?P<pk>\d+)/audio/$',
            views.CollectionEditAudioView.as_view(),
            name='collection-edit-audio'),
    re_path(r'^collection/(?P<pk>\d+)/public/$',
            views.CollectionEditPublicView.as_view(),
            name='collection-edit-public'),
    re_path(r'^collection/(?P<pk>\d+)/operations/$',
            views.AllCollectionOperationsView.as_view()),
    re_path(r'^collection/(?P<pk>\d+)/edit/$',
            views.EditCollectionView.as_view()),
    re_path(r'^collection/(?P<pk>\d+)/toggle_active/$',
            views.CollectionToggleActiveView.as_view()),
    re_path(r'^collection/(?P<pk>\d+)/mediathread_submit/$',
            mediathread_views.CollectionMediathreadSubmit.as_view()),
    re_path(r'^collection/(?P<pk>\d+)/delete/$',
            views.DeleteCollectionView.as_view()),
    re_path(r'^collection/(?P<id>\d+)/remove_tag/(?P<tagname>\w+)/$',
            views.RemoveTagFromCollectionView.as_view()),
    re_path(r'^collection/(?P<pk>\d+)/elastictranscode/$',
            views.ElasticTranscoderCollectionSubmitView.as_view(),
            name='elastictranscoder-collection-submit'),
    re_path(r'^collection/(?P<pk>\d+)/report/$',
            views.CollectionReportView.as_view(),
            name='collection-panopto-report'),
    re_path(r'^collection/(?P<id>\d+)/rss/$', CollectionFeed()),
    re_path(r'^video/(?P<pk>\d+)/edit/$', views.EditVideoView.as_view()),
    re_path(r'^video/(?P<pk>\d+)/s3serve/$', views.VideoS3Serve.as_view()),
    re_path(r'^video/(?P<id>\d+)/delete/$', views.DeleteVideoView.as_view()),
    re_path(r'^video/(?P<id>\d+)/remove_tag/(?P<tagname>\w+)/$',
            views.RemoveTagFromVideoView.as_view()),

    path('server/', views.ServersListView.as_view()),
    path('server/add/', views.AddServerView.as_view()),
    re_path(r'^server/(?P<pk>\d+)/$', views.ServerView.as_view()),
    re_path(r'^server/(?P<pk>\d+)/edit/$', views.EditServerView.as_view()),
    re_path(r'^server/(?P<pk>\d+)/delete/$', views.DeleteServerView.as_view()),

    path('file/', views.FileIndexView.as_view()),
    re_path(r'^file/(?P<id>\d+)/$', views.FileView.as_view()),
    re_path(r'^file/(?P<pk>\d+)/audio/$', views.AudioEncodeFileView.as_view(),
            name='audio_encode_file'),
    re_path(r'^file/(?P<pk>\d+)/delete_from_cunix/$',
            views.DeleteFromCunix.as_view(),
            name='delete-file-from-cunix'),
    re_path(r'^file/(?P<pk>\d+)/delete_from_s3/$',
            views.DeleteFromS3.as_view(),
            name='delete-file-from-s3'),

    re_path(r'^file/filter/$', views.FileFilterView.as_view()),
    re_path((r'^operation/(?P<uuid>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-'
             r'[a-z0-9]{4}-[a-z0-9]{12})/info/$'),
            views.OperationInfoView.as_view()),
    re_path((r'^operation/(?P<uuid>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-'
             r'[a-z0-9]{4}-[a-z0-9]{12})/$'),
            views.OperationView.as_view()),

    re_path(r'^bulk_operation/$', views.BulkOperationView.as_view(),
            name="bulk-operation"),
    re_path(r'^bulk_surelink/$', views.BulkSurelinkView.as_view(),
            name="bulk-surelink"),
    re_path(r'^user/(?P<username>\w+)/', views.UserView.as_view()),
    re_path(r'^file/(?P<id>\d+)/delete/$', views.DeleteFileView.as_view()),
    re_path(r'^file/(?P<id>\d+)/surelink/$', views.FileSurelinkView.as_view()),
    re_path(r'^operation/(?P<id>\d+)/delete/$',
            views.DeleteOperationView.as_view()),
    re_path(r'^operation/(?P<operation_id>\d+)/rerun/$',
            views.RerunOperationView.as_view()),
    re_path(r'^tag/$', views.TagsListView.as_view()),
    re_path(r'^tag/(?P<tagname>\w+)/$', views.TagView.as_view()),

    re_path(r'^upload/post/$', views.upload),
    re_path(r'^upload/$', views.UploadFormView.as_view()),

    re_path(r'^upload/batch/$', views.BatchUploadFormView.as_view()),
    re_path(r'^upload/batch/post/$', views.batch_upload),

    re_path(r'^mediathread/$', mediathread_views.mediathread),
    re_path(r'^mediathread/post/$', mediathread_views.mediathread_post),
    re_path(r'^panopto/', include('wardenclyffe.panopto.urls')),
    re_path(r'^received/$', views.ReceivedView.as_view()),

    re_path(r'^surelink/video/$', views.SureLinkVideoView.as_view()),
    re_path(r'^surelink/$', views.SureLinkView.as_view()),

    re_path(r'^video/$', views.VideoIndexView.as_view()),
    re_path(r'^video/(?P<pk>\d+)/$', views.VideoView.as_view(),
            name='video-details'),
    re_path(r'^video/(?P<id>\d+)/youtube/$',
            views.VideoYoutubeUploadView.as_view(), name="s3-to-youtube"),
    re_path(r'^video/(?P<id>\d+)/flv2mp4/$',
            views.FlvToMp4View.as_view(), name="video-flv-to-mp4"),
    re_path(r'^video/(?P<id>\d+)/mov2mp4/$',
            views.MovToMp4View.as_view(), name="video-mov-to-mp4"),
    re_path(r'^video/(?P<id>\d+)/mediathread_submit/$',
            mediathread_views.VideoMediathreadSubmit.as_view()),
    re_path(r'^video/(?P<id>\d+)/add_file/$',
            views.VideoAddFileView.as_view()),
    re_path(r'^video/(?P<id>\d+)/select_poster/(?P<image_id>\d+)/$',
            views.VideoSelectPosterView.as_view()),
    re_path(r'importflv/$', views.ImportFlv.as_view(), name='import-flv'),
    re_path(r'^search/$', views.SearchView.as_view(), name='search'),
    re_path(r'^uuid_search/$', views.UUIDSearchView.as_view()),
    re_path(r'^api/tagautocomplete/$', views.TagAutocompleteView.as_view()),
    re_path(r'^api/subjectautocomplete/$',
            views.SubjectAutocompleteView.as_view()),
    re_path(r'^api/sns/$', views.SNSView.as_view()),
    re_path(r'^api/cunixdelete/$', views.APICunixDelete.as_view(),
            name='api-cunix-delete'),
    re_path(r'^api/panopto/convert/$',
            panopto_views.APIPanoptoConversion.as_view(),
            name='api-panopto-conversion'),
    re_path('smoketest/', include('smoketest.urls')),
    re_path(r'^stats/$',
            TemplateView.as_view(template_name="main/stats.html")),
    re_path(r'^sign_s3/$', views.SignS3View.as_view(), name='sign-s3'),
    re_path(r'^uploads/(?P<path>.*)$', django.views.static.serve,
            {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls))
    ]
