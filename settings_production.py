# flake8: noqa
from settings_shared import *

TEMPLATE_DIRS = (
    "/var/www/wardenclyffe/wardenclyffe/templates",
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

try:
    from local_settings import *
except ImportError:
    pass
