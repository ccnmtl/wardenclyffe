from django.conf.urls import url

from wardenclyffe.panopto.views import (
    CollectionSubmitView, CollectionSubmitSuccessView)


urlpatterns = [
    url(r'^collection/(?P<pk>\d+)/$', CollectionSubmitView.as_view(),
        name='panopto-collection-submit'),
    url(r'^collection/(?P<pk>\d+)/success/$',
        CollectionSubmitSuccessView.as_view(),
        name='panopto-collection-success-submit'),
]
