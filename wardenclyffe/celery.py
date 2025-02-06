import os

from celery import Celery, signals
from django.conf import settings
import sentry_sdk

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wardenclyffe.settings')

app = Celery('wardenclyffe')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

if hasattr(settings, 'ENVIRONMENT') and hasattr(settings, 'SENTRY_DSN'):
    # Initialize Sentry SDK on Celery startup
    @signals.worker_init.connect
    def init_sentry(**_kwargs):
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
        )

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
