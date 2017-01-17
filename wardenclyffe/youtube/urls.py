from django.conf.urls import url
import views


urlpatterns = [
    url(r'^$', views.youtube),
    url(r'^post/$', views.youtube_post),
    url(r'^done/$', views.youtube_done),
]
