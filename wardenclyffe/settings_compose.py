# flake8: noqa
from wardenclyffe.settings_shared import *

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

# if you want to actually do AWS stuff, you need the following
# variables set in a `local_settings.py`
#
# AWS_ACCESS_KEY = 'your id'
# AWS_SECRET_KEY = 'your secret'
#
# you may also want to set the `AWS_ET_PIPELINE_ID`,
# `AWS_ET_MP4_PRESET` and `AWS_ET_720_PRESET`

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
broker_url = "amqp://guest:guest@rabbitmq:5672/"

# don't bother with separate queues and routing when running
# dev environment
class MyDummyRouter(object):
    def route_for_task(self, task, args=None, kwargs=None):
        return None

task_routes = (MyDummyRouter(),)

try:
    from wardenclyffe.local_settings import *
except ImportError:
    pass
AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = AWS_SECRET_KEY
