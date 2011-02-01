from settings_shared import *

TEMPLATE_DIRS = (
    "/var/www/wardenclyffe/wardenclyffe/templates",
)

MEDIA_ROOT = '/var/www/wardenclyffe/uploads/'
# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', '/var/www/wardenclyffe/wardenclyffe/sitemedia'),	
)


DEBUG = False
TEMPLATE_DEBUG = DEBUG

try:
    from local_settings import *
except ImportError:
    pass
