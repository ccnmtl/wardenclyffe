# Django settings for wardenclyffe project.
import os.path
import sys

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ( )

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2' # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'wardenclyffe' # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

if 'test' in sys.argv:
    DATABASE_ENGINE = 'sqlite3'
SOUTH_TESTS_MIGRATE = False

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
MEDIA_ROOT = "/var/www/wardenclyffe/uploads/"
MEDIA_URL = '/uploads/'
ADMIN_MEDIA_PREFIX = '/media/'
SECRET_KEY = ')ng#)ef_u@_^zvvu@dxm7ql-yb^_!a6%v3v^j3b(mp+)l+5%@h'
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = 'wardenclyffe.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # Put application templates before these fallback ones:
    "/var/www/wardenclyffe/templates/",
    os.path.join(os.path.dirname(__file__),"templates"),
)
import djcelery
djcelery.setup_loader()

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.markup',
    'sorl.thumbnail',
    'django.contrib.admin',
    'tagging',
    'smartif',
    'template_utils',
    'typogrify',
    'djcelery',
    'main',
    'mediathread',
    'youtube',
    'sentry.client',
    'oembed',
    'taggit',
    'vital',
    'surelink',
    'south',
    'paging',
    'indexer',
)

#CELERY_RESULT_BACKEND = "database"
BROKER_HOST = "localhost"
BROKER_PORT = 5672
#BROKER_USER = "guest"
#BROKER_PASSWORD = "guest"
BROKER_VHOST = "/"
CELERYD_CONCURRENCY = 4

import logging
from sentry.client.handlers import SentryHandler
logger = logging.getLogger()
if SentryHandler not in map(lambda x: x.__class__, logger.handlers):
    logger.addHandler(SentryHandler())
    logger = logging.getLogger('sentry.errors')
    logger.propagate = False
    logger.addHandler(logging.StreamHandler())
    SENTRY_REMOTE_URL = 'http://sentry.ccnmtl.columbia.edu/sentry/store/'
SENTRY_SITE = 'wardenclyffe'

THUMBNAIL_SUBDIR = "thumbs"
EMAIL_SUBJECT_PREFIX = "[wardenclyffe] "
EMAIL_HOST = 'localhost'
SERVER_EMAIL = "wardenclyffe@ccnmtl.columbia.edu"
# email addresses of video team members how want to be annoyed by lots of status email
ANNOY_EMAILS = ["agraddy@columbia.edu","anders@columbia.edu"]

# WIND settings

AUTHENTICATION_BACKENDS = ('djangowind.auth.WindAuthBackend','django.contrib.auth.backends.ModelBackend',)
WIND_BASE = "https://wind.columbia.edu/"
WIND_SERVICE = "cnmtl_full_np"
WIND_PROFILE_HANDLERS = ['djangowind.auth.CDAPProfileHandler']
WIND_AFFIL_HANDLERS = ['djangowind.auth.AffilGroupMapper','djangowind.auth.StaffMapper','djangowind.auth.SuperuserMapper']
WIND_STAFF_MAPPER_GROUPS = ['tlc.cunix.local:columbia.edu']
WIND_SUPERUSER_MAPPER_GROUPS = ['anp8','jb2410','zm4','sbd12','egr2107','kmh2124','sld2131','amm8','mar227','ed2198', 'ej2223']

WATCH_DIRECTORY = "/tmp/wardenclyffe/watch_dir/"
