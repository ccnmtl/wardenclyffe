from django.conf.urls import url
import views


urlpatterns = [
    url(r'^$', views.youtube, name='youtube-upload-form'),
    url(r'^post/$', views.youtube_post, name='youtube-post'),
    url(r'^done/$', views.youtube_done, name='youtube-done'),
]
