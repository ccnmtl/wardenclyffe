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
        'ATOMIC_REQUESTS': True,
    }
}

TMP_DIR = "/tmp"

if 'test' in sys.argv or 'jenkins' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'HOST': '',
            'PORT': '',
            'USER': '',
            'PASSWORD': '',
            'ATOMIC_REQUESTS': True,
        }
    }
    SURELINK_PROTECTION_KEY = "test-dummy-key"
    MEDIATHREAD_SECRET = "test-dummy-secret"
    WATCH_DIRECTORY = "/tmp/"
    TMP_DIR = "/tmp"
    PCP_BASE_URL = ""
    CELERY_ALWAYS_EAGER = True

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes',
)
PROJECT_APPS = [
    'wardenclyffe.main',
    'wardenclyffe.mediathread',
    'wardenclyffe.util',
    'wardenclyffe.youtube',
    'wardenclyffe.cuit',
    'wardenclyffe.graphite',
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
    'django.core.context_processors.static',
)

MIDDLEWARE_CLASSES = (
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
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
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'compressor',
    'django.contrib.admin',
    'tagging',
    'template_utils',
    'djcelery',
    'wardenclyffe.main',
    'wardenclyffe.mediathread',
    'wardenclyffe.youtube',
    'wardenclyffe.util',
    'oembed',
    'taggit',
    'wardenclyffe.cuit',
    'django_statsd',
    'smoketest',
    'waffle',
    'debug_toolbar',
    'django_jenkins',
    'wardenclyffe.graphite',
    'django_extensions',
    'django_markwhat',
]

INTERNAL_IPS = ('127.0.0.1', )
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
)

STATSD_CLIENT = 'statsd.client'
STATSD_PREFIX = 'wardenclyffe'
STATSD_HOST = 'localhost'
STATSD_PORT = 8125

BROKER_URL = "amqp://localhost:5672//"
CELERYD_CONCURRENCY = 4


class MyRouter(object):
    def route_for_task(self, task, args=None, kwargs=None):
        if task.startswith('wardenclyffe.graphite.tasks'):
            return {
                'exchange': 'graphite',
                'exchange_type': 'direct',
                'routing_key': 'graphite',
            }
        if task == 'wardenclyffe.main.tasks.check_for_slow_operations':
            return {'exchange': 'short',
                    'exchange_type': 'direct',
                    'routing_key': 'short'}
        if task == 'wardenclyffe.main.tasks.move_file':
            return {'exchange': 'batch',
                    'exchange_type': 'direct',
                    'routing_key': 'batch'}
        return None

CELERY_ROUTES = (MyRouter(),)

THUMBNAIL_SUBDIR = "thumbs"
EMAIL_SUBJECT_PREFIX = "[wardenclyffe] "
EMAIL_HOST = 'localhost'
SERVER_EMAIL = "wardenclyffe@ccnmtl.columbia.edu"
# email addresses of video team members how want to
# be annoyed by lots of status email
ANNOY_EMAILS = ["jhanford@columbia.edu", "anders@columbia.edu"]
VIDEO_TEAM_EMAILS = ["jhanford@columbia.edu"]

# WIND settings

AUTHENTICATION_BACKENDS = ('djangowind.auth.SAMLAuthBackend',
                           'django.contrib.auth.backends.ModelBackend', )
CAS_BASE = "https://cas.columbia.edu/"
WIND_PROFILE_HANDLERS = ['djangowind.auth.CDAPProfileHandler']
WIND_AFFIL_HANDLERS = ['djangowind.auth.AffilGroupMapper',
                       'djangowind.auth.StaffMapper',
                       'djangowind.auth.SuperuserMapper']
WIND_STAFF_MAPPER_GROUPS = ['tlc.cunix.local:columbia.edu']
WIND_SUPERUSER_MAPPER_GROUPS = ['anp8', 'jb2410', 'zm4', 'egr2107',
                                'amm8', 'mar227', 'njn2118', 'jed2161',
                                'sld2131']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

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

MAX_FRAMES = 50

POSTER_BASE_URL = "https://wardenclyffe.ccnmtl.columbia.edu/uploads/"
DEFAULT_POSTER_URL = (
    "http://ccnmtl.columbia.edu/"
    "broadcast/posters/vidthumb_480x360.jpg")
STAGING = False

STATIC_ROOT = '/tmp/wardenclyffe/static'
STATICFILES_DIRS = ('media/',)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

IONICE_PATH = "/usr/bin/ionice"
MPLAYER_PATH = "/usr/bin/mplayer"
FFMPEG_PATH = "/usr/bin/ffmpeg"

AUDIO_POSTER_IMAGE = os.path.join(
    os.path.dirname(__file__),
    "../media/img/audiothumb.jpg")

COMPRESS_URL = "/media/"
COMPRESS_ROOT = "media/"

IMAGES_BUCKET = "ccnmtl-wardenclyffe-images-dev"
IMAGES_URL_BASE = "https://s3.amazonaws.com/" + IMAGES_BUCKET + "/"

SOUTH_MIGRATION_MODULES = {
    'taggit': 'taggit.south_migrations',
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}
