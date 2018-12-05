from django.conf.urls import url

from wardenclyffe.youtube import views


urlpatterns = [
    url(r'^$', views.youtube, name='youtube-upload-form'),
    url(r'^post/$', views.youtube_post, name='youtube-post'),
    url(r'^collection/(?P<pk>\d+)/$',
        views.YouTubeCollectionSubmitView.as_view(),
        name='youtube-collection-submit'),
    url(r'^done/$', views.youtube_done, name='youtube-done'),
    url(r'auth/$', views.YTAuth.as_view(), name='youtube-auth'),
    url(r'oauth2callback/$', views.OauthCallback.as_view(),
        name='youtube-oauth2callback'),
]
