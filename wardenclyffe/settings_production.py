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
        'ATOMIC_REQUESTS': True,
        }
}

FFMPEG_PATH = "/usr/local/bin/ffmpeg"

IMAGES_BUCKET = "ccnmtl-wardenclyffe-images-prod"
IMAGES_URL_BASE = "https://d369ay3g98xik5.cloudfront.net/"


if 'migrate' not in sys.argv:
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')

try:
    from local_settings import *
except ImportError:
    pass
