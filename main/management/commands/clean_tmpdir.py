from django.core.management.base import BaseCommand
from django.conf import settings
import random
import os
import os.path
import sys
import shutil
from datetime import datetime, timedelta

class Command(BaseCommand):
    args = ''
    help = ''
    
    def handle(self,*args,**kwargs):
        # don't remove anything less than a week old
        ARCHIVE_CUTOFF = datetime.now() - timedelta(days=7)
        BASE = settings.TMP_DIR
        for f in os.listdir(BASE):
            if f in ["imgs","watch_dir"]:
                continue
            mtime = datetime.fromtimestamp(int(os.path.getmtime(os.path.join(BASE,f))))
            if mtime > ARCHIVE_CUTOFF: 
                continue
            else:
                print "deleting %s" % (f,)
                os.unlink(os.path.join(BASE,f))

