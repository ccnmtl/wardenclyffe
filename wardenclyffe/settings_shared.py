# Django settings for wardenclyffe project.
import os.path
import sys
from ctlsettings.shared import common

project = 'wardenclyffe'
base = os.path.dirname(__file__)

locals().update(
    common(
        project=project,
        base=base,
    ))

WATCH_DIRECTORY = "/var/www/wardenclyffe/tmp/watch_dir/"
TMP_DIR = "/tmp"  # nosec


CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//wardenclyffe'
CELERY_WORKER_CONCURRENCY = 1

CELERY_TASK_ROUTES = {
    'wardenclyffe.graphite.tasks.*': {
        'queue': 'graphite'
    },
    'wardenclyffe.main.tasks.check_for_slow_operations': {
        'queue': 'short'
    },
    'wardenclyffe.main.tasks.move_file': {
        'queue': 'batch'
    },
}


if 'test' in sys.argv or 'jenkins' in sys.argv:
    SURELINK_PROTECTION_KEY = "test-dummy-key"
    MEDIATHREAD_SECRET = "test-dummy-secret"  # nosec
    WATCH_DIRECTORY = "/tmp/"  # nosec
    TMP_DIR = "/tmp"  # nosec
    PCP_BASE_URL = ""

    from celery.contrib.testing.app import DEFAULT_TEST_CONFIG

    CELERY_BROKER_URL = DEFAULT_TEST_CONFIG.get('broker_url')
    CELERY_RESULT_BACKEND = DEFAULT_TEST_CONFIG.get('result_backend')
    CELERY_BROKER_HEARTBEAT = DEFAULT_TEST_CONFIG.get('broker_heartbeat')

    # don't bother with separate queues and routing when running
    # dev environment
    class MyDummyRouter(object):
        def route_for_task(self, task, args=None, kwargs=None):
            return None

    CELERY_TASK_ROUTES = (MyDummyRouter(),)


PROJECT_APPS = [
    'wardenclyffe.main',
    'wardenclyffe.mediathread',
    'wardenclyffe.panopto',
    'wardenclyffe.util',
    'wardenclyffe.graphite',
]

INSTALLED_APPS += [  # noqa
    'wardenclyffe.main',
    'wardenclyffe.mediathread',
    'wardenclyffe.panopto',
    'wardenclyffe.util',
    'oembed',
    'taggit',
    'wardenclyffe.graphite',
    'django_extensions',
    's3sign',
    'wardenclyffe.streamlogs',
    'bootstrap4',
    'django_celery_results',
    'waffle',
]

MIDDLEWARE += [  # noqa
    'django.middleware.csrf.CsrfViewMiddleware',
]

# email addresses of video team members how want to
# be annoyed by lots of status email
ANNOY_EMAILS = ["jhanford@columbia.edu"]
VIDEO_TEAM_EMAILS = ["jhanford@columbia.edu"]

H264_SECURE_STREAM_DIRECTORY = "/media/h264/ccnmtl/secure/"
H264_PUBLIC_STREAM_DIRECTORY = "/media/h264/ccnmtl/public/"
H264_SECURE_STREAM_BASE = "http://stream.ccnmtl.columbia.edu/secvideos/"

H264_PUBLIC_STREAM_DIRECTORY = "/media/h264/ccnmtl/public/"
H264_PUBLIC_STREAM_DIRECTORY = "/media/h264/ccnmtl/public/"
H264_PUBLIC_STREAM_BASE = "http://stream.ccnmtl.columbia.edu/public/"

CUNIX_BROADCAST_BASE = "/www/data/ccnmtl/"
CUNIX_BROADCAST_DIRECTORY = "/www/data/ccnmtl/broadcast/"
CUNIX_BROADCAST_URL = "http://ccnmtl.columbia.edu/broadcast/"
CUNIX_SECURE_DIRECTORY = "/www/data/ccnmtl/broadcast/secure/"
CUNIX_H264_DIRECTORY = "/media/h264"
FLV_STREAM_BASE_URL = "http://ccnmtl.columbia.edu/stream/flv/"

MAX_FRAMES = 50

OPERATION_MAX_RETRIES = 10

POSTER_BASE_URL = "https://wardenclyffe.ctl.columbia.edu/uploads/"
DEFAULT_POSTER_URL = (
    "http://ccnmtl.columbia.edu/"
    "broadcast/posters/vidthumb_480x360.jpg")
STAGING = False

IONICE_PATH = "/usr/bin/ionice"
MPLAYER_PATH = "/usr/bin/mplayer"
FFMPEG_PATH = "/usr/bin/ffmpeg"

AUDIO_POSTER_IMAGE = os.path.join(
    os.path.dirname(__file__),
    "../media/img/audiothumb.jpg")

IMAGES_BUCKET = "ccnmtl-wardenclyffe-images-dev"
IMAGES_URL_BASE = "https://s3.amazonaws.com/" + IMAGES_BUCKET + "/"

AWS_S3_UPLOAD_BUCKET = "ccnmtl-wardenclyffe-input-devel"
AWS_S3_OUTPUT_BUCKET = "ccnmtl-wardenclyffe-output-dev"
AWS_ET_REGION = 'us-east-1'

VIDEO_EXTENSIONS = [".mov", ".avi", ".mp4", ".flv", ".mpg", ".wmv", ".m4v"]
AUDIO_EXTENSIONS = [".mp3"]
ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS + AUDIO_EXTENSIONS

SOUTH_MIGRATION_MODULES = {
    'taggit': 'taggit.south_migrations',
}

PANOPTO_LINK_URL = 'http://testserver/link/{}/'
PANOPTO_EMBED_URL = 'http://testserver/embed/{}/'
PANOPTO_MIGRATIONS_USER = 'migrations'
PANOPTO_COLLECTION = 'Automatic Panopto Migrations'
PANOPTO_MIGRATIONS_FOLDER = 'dummy'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(base, "templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'stagingcontext.staging_processor',
                'ctlsettings.context_processors.env',
                'gacontext.ga_processor',
                'django.template.context_processors.csrf'
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
