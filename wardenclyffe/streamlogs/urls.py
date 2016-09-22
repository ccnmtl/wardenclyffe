from django.conf.urls import url
from django.contrib.auth.decorators import user_passes_test
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from wardenclyffe.main.views import is_staff

from .models import StreamLog
from .views import LogView, ReportView

staff_only = user_passes_test(lambda u: is_staff(u))

urlpatterns = [
    url(r'^$', LogView.as_view(), name='streamlogs'),
    url(r'report/$', staff_only(
        ReportView.as_view()),
        name='streamlogs-report'),
    url(r'list/$', staff_only(
        ListView.as_view(
            model=StreamLog,
            paginate_by=50,
        )), name='streamlogs-list'),
    url(r'(?P<pk>\d+)/$', staff_only(
        DetailView.as_view(
            model=StreamLog,
        )), name='streamlogs-detail'),
]
