from django.conf.urls import url
from wardenclyffe.drop.views import SNSView


urlpatterns = [
    url(r'^sns/$', SNSView.as_view(), name='drop-sns-endpoint'),
]
