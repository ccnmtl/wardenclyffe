from django.urls import re_path

from wardenclyffe.panopto.views import (
    CollectionSubmitView, CollectionSubmitSuccessView, VideoSubmitView)


urlpatterns = [
    re_path(r'^collection/(?P<pk>\d+)/$', CollectionSubmitView.as_view(),
            name='panopto-collection-submit'),
    re_path(r'^collection/(?P<pk>\d+)/success/$',
            CollectionSubmitSuccessView.as_view(),
            name='panopto-collection-success-submit'),
    re_path(r'^video/(?P<pk>\d+)/$', VideoSubmitView.as_view(),
            name='panopto-video-submit'),
]
