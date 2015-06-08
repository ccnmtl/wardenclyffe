# flake8: noqa
from settings_shared import *
import sys
import os

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), "templates"),
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

AWS_S3_CUSTOM_DOMAIN = "d32f8np9uyk4f2.cloudfront.net"
AWS_STORAGE_BUCKET_NAME = "ccnmtl-wardenclyffe-static-prod"
AWS_PRELOAD_METADATA = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
S3_URL = 'https://%s/' % AWS_S3_CUSTOM_DOMAIN
# static data, e.g. css, js, etc.
STATICFILES_STORAGE = 'cacheds3storage.CompressorS3BotoStorage'
STATIC_URL = 'https://%s/media/' % AWS_S3_CUSTOM_DOMAIN
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_URL = STATIC_URL
COMPRESS_STORAGE = 'cacheds3storage.CompressorS3BotoStorage'

if 'migrate' not in sys.argv:
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')

try:
    from local_settings import *
except ImportError:
    pass
