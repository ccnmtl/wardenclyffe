# Django settings for wardenclyffe project.
import os.path
import sys

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'wardenclyffe',
        'HOST': '',
        'PORT': 5432,
        'USER': '',
        'PASSWORD': '',
        }
}

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'HOST': '',
            'PORT': '',
            'USER': '',
            'PASSWORD': '',
            }
        }

SOUTH_TESTS_MIGRATE = False
SOUTH_AUTO_FREEZE_APP = True
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

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
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = 'wardenclyffe.urls'

TEMPLATE_DIRS = (
    "/var/www/wardenclyffe/templates/",
    os.path.join(os.path.dirname(__file__), "templates"),
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
    'djcelery',
    'wardenclyffe.main',
    'wardenclyffe.mediathread',
    'wardenclyffe.youtube',
    'oembed',
    'taggit',
    'wardenclyffe.vital',
    'surelink',
    'south',
    'django_nose',
    'munin',
    'wardenclyffe.cuit',
    'raven.contrib.django',
    'django_statsd',
)

STATSD_CLIENT = 'statsd.client'
STATSD_PREFIX = 'wardenclyffe'
STATSD_HOST = 'localhost'
STATSD_PORT = 8125
STATSD_PATCHES = ['django_statsd.patches.db', ]

#CELERY_RESULT_BACKEND = "database"
BROKER_HOST = "localhost"
BROKER_PORT = 5672
#BROKER_USER = "guest"
#BROKER_PASSWORD = "guest"
BROKER_VHOST = "/"
CELERYD_CONCURRENCY = 4

THUMBNAIL_SUBDIR = "thumbs"
EMAIL_SUBJECT_PREFIX = "[wardenclyffe] "
EMAIL_HOST = 'localhost'
SERVER_EMAIL = "wardenclyffe@ccnmtl.columbia.edu"
# email addresses of video team members how want to
# be annoyed by lots of status email
ANNOY_EMAILS = ["jhanford@columbia.edu", "anders@columbia.edu"]

# WIND settings

AUTHENTICATION_BACKENDS = ('djangowind.auth.WindAuthBackend',
                           'django.contrib.auth.backends.ModelBackend', )
WIND_BASE = "https://wind.columbia.edu/"
WIND_SERVICE = "cnmtl_full_np"
WIND_PROFILE_HANDLERS = ['djangowind.auth.CDAPProfileHandler']
WIND_AFFIL_HANDLERS = ['djangowind.auth.AffilGroupMapper',
                       'djangowind.auth.StaffMapper',
                       'djangowind.auth.SuperuserMapper']
WIND_STAFF_MAPPER_GROUPS = ['tlc.cunix.local:columbia.edu']
WIND_SUPERUSER_MAPPER_GROUPS = ['anp8', 'jb2410', 'zm4', 'egr2107',
                                'amm8', 'mar227']

WATCH_DIRECTORY = "/var/www/wardenclyffe/tmp/watch_dir/"
H264_SECURE_STREAM_DIRECTORY = "/media/h264/ccnmtl/secure/"
H264_PUBLIC_STREAM_DIRECTORY = "/media/h264/ccnmtl/public/"
H264_SECURE_STREAM_BASE = "http://stream.ccnmtl.columbia.edu/secvideos/"

H264_PUBLIC_STREAM_DIRECTORY = "/media/h264/ccnmtl/public/"
H264_PUBLIC_STREAM_DIRECTORY = "/media/h264/ccnmtl/public/"
H264_PUBLIC_STREAM_BASE = "http://stream.ccnmtl.columbia.edu/public/"
