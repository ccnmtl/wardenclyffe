# flake8: noqa
import sys
from settings_shared import *

if 'test' not in sys.argv:
    try:
        from local_settings import *
    except ImportError:
        pass
