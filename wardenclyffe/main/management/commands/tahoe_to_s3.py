from django.core.management.base import BaseCommand
from wardenclyffe.main.models import File
from wardenclyffe.main.tasks import move_file


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, **kwargs):
        cnt = File.objects.filter(location_type='tahoe').count()
        i = 1
        for f in File.objects.filter(location_type='tahoe').order_by("-id"):
            print "[%03d/%03d] moving video %d" % (
                i, cnt, f.video.id)
            i += 1
            if File.objects.filter(
                    location_type='s3', video=f.video).exists():
                # if there's already an S3 file, skip this one
                continue
            move_file.delay(f.id)
