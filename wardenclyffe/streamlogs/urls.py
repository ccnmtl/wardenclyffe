from django.conf.urls import url
from django.contrib.auth.decorators import user_passes_test
from django.views.generic.detail import DetailView

from wardenclyffe.main.views import is_staff
from wardenclyffe.streamlogs.models import StreamLog
from wardenclyffe.streamlogs.views import (
    LogView, ReportView, StreamLogListView)


staff_only = user_passes_test(lambda u: is_staff(u))

urlpatterns = [
    url(r'^$', LogView.as_view(), name='streamlogs'),
    url(r'report/$', staff_only(
        ReportView.as_view(days=200)),
        name='streamlogs-report'),
    url(r'list/$', staff_only(
        StreamLogListView.as_view()), name='streamlogs-list'),
    url(r'(?P<pk>\d+)/$', staff_only(
        DetailView.as_view(
            model=StreamLog,
        )), name='streamlogs-detail'),
]
