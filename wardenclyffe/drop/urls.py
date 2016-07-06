from django.conf.urls import patterns, url

from .views import SNSView


urlpatterns = patterns(
    '',
    url(r'^sns/$', SNSView.as_view(), name='drop-sns-endpoint'),
)
