from django.conf import settings
from wardenclyffe.settings_shared import *  # noqa: F403
from ctlsettings.production import common, init_sentry

locals().update(
    common(
        project=project,  # noqa: F405
        base=base,  # noqa: F405
        INSTALLED_APPS=INSTALLED_APPS,  # noqa: F405
        STATIC_ROOT=STATIC_ROOT,  # noqa: F405
        cloudfront="d32f8np9uyk4f2",
        s3prefix="ccnmtl",
    ))

TMP_DIR = "/var/www/wardenclyffe/tmp/"
WATCH_DIRECTORY = "/var/www/wardenclyffe/tmp/watch_dir/"

FFMPEG_PATH = "/usr/bin/ffmpeg"

IMAGES_BUCKET = "ccnmtl-wardenclyffe-images-prod"
IMAGES_URL_BASE = "https://d369ay3g98xik5.cloudfront.net/"

# id of the default collection to put imported FLVs into
FLV_IMPORT_COLLECTION_ID = 30
FLV_PUBLIC_IMPORT_COLLECTION_ID = 31


try:
    from wardenclyffe.local_settings import *  # noqa: F403
except ImportError:
    pass

if hasattr(settings, 'SENTRY_DSN'):
    init_sentry(SENTRY_DSN)  # noqa F405
