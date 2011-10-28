from django.conf.urls.defaults import *
from django.conf import settings
import os.path

urlpatterns = patterns('',
                       ('^$','cuit.views.index'),
                       ('^import_quicktime/$','cuit.views.import_quicktime'),
                       )
