from django.conf.urls import url
from django.views.generic.list import ListView

from .models import StreamLog
from .views import LogView

urlpatterns = [
    url(r'^$', LogView.as_view(), name='streamlogs'),
    url(r'list/$', ListView.as_view(
        model=StreamLog,
    ), name='streamlogs-list'),
]
