from django.urls import path
from django.contrib.auth.decorators import user_passes_test

from wardenclyffe.main.views import is_staff
from wardenclyffe.streamlogs.views import (
    LogView, ReportView, StreamLogListView, StreamLogDetailView)


staff_only = user_passes_test(lambda u: is_staff(u))

urlpatterns = [
    path('', LogView.as_view(), name='streamlogs'),
    path('report/', staff_only(
        ReportView.as_view(days=200)),
        name='streamlogs-report'),
    path('list/', staff_only(
        StreamLogListView.as_view()), name='streamlogs-list'),
    path('detail/', staff_only(
        StreamLogDetailView.as_view()), name='streamlogs-detail')
]
