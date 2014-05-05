from django.conf.urls import patterns

urlpatterns = patterns(
    '',
    ('^$', 'wardenclyffe.cuit.views.index'),
    ('^import_quicktime/$', 'wardenclyffe.cuit.views.import_quicktime'),
    ('^import_retry/$', 'wardenclyffe.cuit.views.import_retry'),
    ('^broken_quicktime/$', 'wardenclyffe.cuit.views.broken_quicktime'),
)
