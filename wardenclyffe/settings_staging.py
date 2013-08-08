# flake8: noqa
from settings_shared import *
import sys

TEMPLATE_DIRS = (
    "/var/www/wardenclyffe/wardenclyffe/wardenclyffe/templates",
)

MEDIA_ROOT = '/var/www/wardenclyffe/uploads/'
# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', '/var/www/wardenclyffe/wardenclyffe/sitemedia'),
)


DEBUG = False
TEMPLATE_DEBUG = DEBUG

TMP_DIR = "/var/www/wardenclyffe/tmp/"
WATCH_DIRECTORY = "/var/www/wardenclyffe/tmp/watch_dir/"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'wardenclyffe',
        'HOST': '',
        'PORT': 6432,  # 6432 = pgbouncer
        'USER': '',
        'PASSWORD': '',
        }
}

STATSD_PREFIX = 'wardenclyffe-staging'
SENTRY_SITE = 'wardenclyffe-staging'
SENTRY_SERVERS = ['http://sentry.ccnmtl.columbia.edu/sentry/store/']

if 'migrate' not in sys.argv:
    import logging
    from raven.contrib.django.handlers import SentryHandler
    logger = logging.getLogger()
    # ensure we havent already registered the handler
    if SentryHandler not in map(type, logger.handlers):
        logger.addHandler(SentryHandler())

        # Add StreamHandler to sentry's default so you can catch missed exceptions
        logger = logging.getLogger('sentry.errors')
        logger.propagate = False
        logger.addHandler(logging.StreamHandler())

    INSTALLED_APPS.append('raven.contrib.django')



try:
    from local_settings import *
except ImportError:
    pass
