# flake8: noqa
from settings_shared import *
from ccnmtlsettings.production import common

locals().update(
    common(
        project=project,
        base=base,
        INSTALLED_APPS=INSTALLED_APPS,
        STATIC_ROOT=STATIC_ROOT,
        cloudfront="d32f8np9uyk4f2",
    ))

TMP_DIR = "/var/www/wardenclyffe/tmp/"
WATCH_DIRECTORY = "/var/www/wardenclyffe/tmp/watch_dir/"

FFMPEG_PATH = "/usr/local/bin/ffmpeg"

IMAGES_BUCKET = "ccnmtl-wardenclyffe-images-prod"
IMAGES_URL_BASE = "https://d369ay3g98xik5.cloudfront.net/"

# id of the default collection to put imported FLVs into
FLV_IMPORT_COLLECTION_ID = 30
FLV_PUBLIC_IMPORT_COLLECTION_ID = 31

INSTALLED_APPS += [
    'opbeat.contrib.django',
]
MIDDLEWARE_CLASSES.insert(0, 'opbeat.contrib.django.middleware.OpbeatAPMMiddleware')


try:
    from local_settings import *
except ImportError:
    pass
