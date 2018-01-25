# Django settings for wardenclyffe project.
import os.path
import sys
from ccnmtlsettings.shared import common
import djcelery

project = 'wardenclyffe'
base = os.path.dirname(__file__)

locals().update(
    common(
        project=project,
        base=base,
    ))

WATCH_DIRECTORY = "/var/www/wardenclyffe/tmp/watch_dir/"
TMP_DIR = "/tmp"  # nosec

if 'test' in sys.argv or 'jenkins' in sys.argv:
    SURELINK_PROTECTION_KEY = "test-dummy-key"
    MEDIATHREAD_SECRET = "test-dummy-secret"
    WATCH_DIRECTORY = "/tmp/"  # nosec
    TMP_DIR = "/tmp"  # nosec
    PCP_BASE_URL = ""
    CELERY_ALWAYS_EAGER = True

PROJECT_APPS = [
    'wardenclyffe.main',
    'wardenclyffe.mediathread',
    'wardenclyffe.panopto',
    'wardenclyffe.util',
    'wardenclyffe.youtube',
    'wardenclyffe.graphite',
]

djcelery.setup_loader()

INSTALLED_APPS += [  # noqa
    'djcelery',
    'wardenclyffe.main',
    'wardenclyffe.mediathread',
    'wardenclyffe.panopto',
    'wardenclyffe.youtube',
    'wardenclyffe.util',
    'oembed',
    'taggit',
    'wardenclyffe.graphite',
    'django_extensions',
    's3sign',
    'wardenclyffe.drop',
    'wardenclyffe.streamlogs',
    'bootstrap4'
]

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

POSTER_BASE_URL = "https://wardenclyffe.ccnmtl.columbia.edu/uploads/"
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

DROPBOX_TOPIC_ARN = (
    "arn:aws:sns:us-east-1:051882422638:ctl-wardenclyffe-dropbox")

VIDEO_EXTENSIONS = [".mov", ".avi", ".mp4", ".flv", ".mpg", ".wmv", ".m4v"]
AUDIO_EXTENSIONS = [".mp3"]
ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS + AUDIO_EXTENSIONS

SOUTH_MIGRATION_MODULES = {
    'taggit': 'taggit.south_migrations',
}

# dummy these out for now
GOOGLE_OAUTH2_CLIENT_ID = ""
GOOGLE_OAUTH2_CLIENT_SECRET = ""

PRIMARY_YOUTUBE_ACCOUNT = "ccnmtl@gmail.com"
