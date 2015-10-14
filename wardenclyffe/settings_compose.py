# flake8: noqa
from settings_shared import *

DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'db',
        'PORT': 5432,
        'ATOMIC_REQUESTS': True,
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
BROKER_URL = "amqp://guest:guest@rabbitmq:5672/"

# don't bother with separate queues and routing when running
# dev environment
class MyDummyRouter(object):
    def route_for_task(self, task, args=None, kwargs=None):
        return None

CELERY_ROUTES = (MyDummyRouter(),)

try:
    from local_settings import *
except ImportError:
    pass
