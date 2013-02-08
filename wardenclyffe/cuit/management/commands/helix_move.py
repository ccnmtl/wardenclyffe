from django.core.management.base import BaseCommand
from wardenclyffe.main.models import Operation
from wardenclyffe.util import uuidparse
import os.path

HELIX_DIR = "/media/qtstreams/helix_reencode"
TMP_DIR = "/media/qtstreams/helix_backup"


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **options):
        file_list = args[0]
        for line in open(file_list, "r"):
            filename = line.strip()
            try:
                uuid = uuidparse(filename)
                operation = Operation.objects.get(uuid=uuid)
                destination = operation.video.cuit_file().filename
                print "mv %s %s" % (destination, os.path.join(TMP_DIR,
                                                              filename))
                print "mv %s %s" % (os.path.join(HELIX_DIR, filename),
                                    destination)
            except Exception, e:
                print str(e)
