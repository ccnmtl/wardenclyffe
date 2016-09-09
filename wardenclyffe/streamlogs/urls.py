from django.conf.urls import url

from .views import LogView

urlpatterns = [
    url(r'^$', LogView.as_view(), name='streamlogs'),
]
