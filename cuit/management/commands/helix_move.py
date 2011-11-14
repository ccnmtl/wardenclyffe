from django.core.management.base import BaseCommand
from main.models import Video,File,Operation,Server
import re
import os.path

def uuidparse(s):
    pattern = re.compile(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})")
    m = pattern.match(s)
    if m:
        return m.group()
    else:
        return ""

HELIX_DIR = "/media/qtstreams/helix_reencode"
TMP_DIR = "/media/qtstreams/helix_backup"

class Command(BaseCommand):
    args = ''
    help = ''
    def handle(self,*args,**options):
        file_list = args[0]
        for line in open(file_list,"r"):
            filename = line.strip()
            try:
                uuid = uuidparse(filename)
                operation = Operation.objects.get(uuid=uuid)
                destination = operation.video.cuit_file().filename
                print "mv %s %s" % (destination,os.path.join(TMP_DIR,filename))
                print "mv %s %s" % (os.path.join(HELIX_DIR,filename),destination)
            except Exception, e:
                print str(e)
