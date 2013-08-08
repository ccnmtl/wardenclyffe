import os, sys, site

# enable the virtualenv
site.addsitedir('/var/www/wardenclyffe/wardenclyffe/ve/lib/python2.7/site-packages')

# paths we might need to pick up the project's settings
sys.path.append('/var/www/wardenclyffe/wardenclyffe/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'wardenclyffe.settings_staging'
os.environ["CELERY_LOADER"] = "django"

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
