from django.conf import settings
from wardenclyffe.settings_shared import *  # noqa: F403
from ctlsettings.staging import common, init_sentry

locals().update(
    common(
        project=project,  # noqa: F405
        base=base,  # noqa: F405
        INSTALLED_APPS=INSTALLED_APPS,  # noqa: F405
        STATIC_ROOT=STATIC_ROOT,  # noqa: F405
        cloudfront="d1ta430vcju3u4",
        s3prefix="ccnmtl",
    ))

TMP_DIR = "/var/www/wardenclyffe/tmp/"
WATCH_DIRECTORY = "/var/www/wardenclyffe/tmp/watch_dir/"

FFMPEG_PATH = "/usr/bin/ffmpeg"

try:
    from wardenclyffe.local_settings import *  # noqa: F403
except ImportError:
    pass

if hasattr(settings, 'SENTRY_DSN'):
    init_sentry(SENTRY_DSN)  # noqa F405
