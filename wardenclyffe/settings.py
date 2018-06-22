# flake8: noqa
import sys
from wardenclyffe.settings_shared import *

if 'test' not in sys.argv and 'jenkins' not in sys.argv:
    try:
        from wardenclyffe.local_settings import *
    except ImportError:
        pass
