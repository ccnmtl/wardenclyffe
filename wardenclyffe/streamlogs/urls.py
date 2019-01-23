from django.conf.urls import url
from django.contrib.auth.decorators import user_passes_test

from wardenclyffe.main.views import is_staff
from wardenclyffe.streamlogs.views import (
    LogView, ReportView, StreamLogListView, StreamLogDetailView)


staff_only = user_passes_test(lambda u: is_staff(u))

urlpatterns = [
    url(r'^$', LogView.as_view(), name='streamlogs'),
    url(r'report/$', staff_only(
        ReportView.as_view(days=200)),
        name='streamlogs-report'),
    url(r'list/$', staff_only(
        StreamLogListView.as_view()), name='streamlogs-list'),
    url(r'detail/$', staff_only(
        StreamLogDetailView.as_view()), name='streamlogs-detail')
]
