# flake8: noqa
from django.conf import settings
from wardenclyffe.settings_shared import *
from ccnmtlsettings.staging import common
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

locals().update(
    common(
        project=project,
        base=base,
        INSTALLED_APPS=INSTALLED_APPS,
        STATIC_ROOT=STATIC_ROOT,
        cloudfront="d1ta430vcju3u4",
    ))

TMP_DIR = "/var/www/wardenclyffe/tmp/"
WATCH_DIRECTORY = "/var/www/wardenclyffe/tmp/watch_dir/"

FFMPEG_PATH = "/usr/local/bin/ffmpeg"

try:
    from wardenclyffe.local_settings import *
except ImportError:
    pass

if hasattr(settings, 'SENTRY_DSN'):
    sentry_sdk.init(
        dsn=SENTRY_DSN,  # noqa: F405
        integrations=[DjangoIntegration()],
        debug=True,
    )
