from django.conf.urls import url

from wardenclyffe.panopto.views import CollectionSubmitView


urlpatterns = [
    url(r'^collection/(?P<pk>\d+)/$', CollectionSubmitView.as_view(),
        name='panopto-collection-submit'),
]
