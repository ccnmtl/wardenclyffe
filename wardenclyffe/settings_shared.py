# Django settings for wardenclyffe project.
import os.path
import sys

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS
WATCH_DIRECTORY = "/var/www/wardenclyffe/tmp/watch_dir/"

ALLOWED_HOSTS = [".ccnmtl.columbia.edu", "localhost"]

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

if 'test' in sys.argv or 'jenkins' in sys.argv:
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
    SURELINK_PROTECTION_KEY = "test-dummy-key"
    MEDIATHREAD_SECRET = "test-dummy-secret"
    TAHOE_DOWNLOAD_BASE = "http://tahoe.ccnmtl.columbia.edu/"
    WATCH_DIRECTORY = "/tmp/"

SOUTH_TESTS_MIGRATE = False
SOUTH_AUTO_FREEZE_APP = True
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.django_tests',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes',
)
PROJECT_APPS = [
    'wardenclyffe.main',
    'wardenclyffe.mediathread',
    'wardenclyffe.surelink',
    'wardenclyffe.util',
    'wardenclyffe.vital',
    'wardenclyffe.youtube',
    'wardenclyffe.cuit',
]

NOSE_ARGS = [
    '--with-coverage',
    "--with-doctest",
    "--noexe",
    "--exclude-dir-file=exclude_tests.txt",
    ('--cover-package=wardenclyffe.main,wardenclyffe.mediathread,'
     'wardenclyffe.vital,wardenclyffe.youtube,wardenclyffe.surelink,'
     'wardenclyffe.util'),
]


TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
MEDIA_ROOT = "/var/www/wardenclyffe/uploads/"
MEDIA_URL = '/uploads/'
STATIC_URL = '/media/'
SECRET_KEY = ')ng#)ef_u@_^zvvu@dxm7ql-yb^_!a6%v3v^j3b(mp+)l+5%@h'
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
)

MIDDLEWARE_CLASSES = (
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'waffle.middleware.WaffleMiddleware',
)

ROOT_URLCONF = 'wardenclyffe.urls'

TEMPLATE_DIRS = (
    "/var/www/wardenclyffe/templates/",
    os.path.join(os.path.dirname(__file__), "templates"),
)
import djcelery
djcelery.setup_loader()

INSTALLED_APPS = [
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
    'wardenclyffe.util',
    'oembed',
    'taggit',
    'wardenclyffe.vital',
    'wardenclyffe.surelink',
    'south',
    'django_nose',
    'munin',
    'wardenclyffe.cuit',
    'django_statsd',
    'smoketest',
    'waffle',
    'debug_toolbar',
    'django_jenkins',
]

INTERNAL_IPS = ('127.0.0.1', )
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
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

H264_SECURE_STREAM_DIRECTORY = "/media/h264/ccnmtl/secure/"
H264_PUBLIC_STREAM_DIRECTORY = "/media/h264/ccnmtl/public/"
H264_SECURE_STREAM_BASE = "http://stream.ccnmtl.columbia.edu/secvideos/"

H264_PUBLIC_STREAM_DIRECTORY = "/media/h264/ccnmtl/public/"
H264_PUBLIC_STREAM_DIRECTORY = "/media/h264/ccnmtl/public/"
H264_PUBLIC_STREAM_BASE = "http://stream.ccnmtl.columbia.edu/public/"

CUNIX_BROADCAST_DIRECTORY = "/www/data/ccnmtl/broadcast/"
CUNIX_BROADCAST_URL = "http://ccnmtl.columbia.edu/broadcast/"
CUNIX_SECURE_DIRECTORY = "/www/data/ccnmtl/broadcast/secure/"
CUNIX_H264_DIRECTORY = "/media/h264"
FLV_STREAM_BASE_URL = "http://ccnmtl.columbia.edu/stream/flv/"

POSTER_BASE_URL = "http://wardenclyffe.ccnmtl.columbia.edu/uploads/"
DEFAULT_POSTER_URL = (
    "http://ccnmtl.columbia.edu/"
    "broadcast/posters/vidthumb_480x360.jpg")
