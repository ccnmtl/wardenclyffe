from django.conf.urls import url

from wardenclyffe.panopto.views import (
    CollectionSubmitView, CollectionSubmitSuccessView, VideoSubmitView)


urlpatterns = [
    url(r'^collection/(?P<pk>\d+)/$', CollectionSubmitView.as_view(),
        name='panopto-collection-submit'),
    url(r'^collection/(?P<pk>\d+)/success/$',
        CollectionSubmitSuccessView.as_view(),
        name='panopto-collection-success-submit'),
    url(r'^video/(?P<pk>\d+)/$', VideoSubmitView.as_view(),
        name='panopto-video-submit'),
]
