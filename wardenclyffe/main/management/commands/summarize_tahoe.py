from django.core.management.base import BaseCommand
from wardenclyffe.main.models import File
import requests


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **kwargs):
        total = 0
        cnt = 0
        for f in File.objects.filter(location_type='tahoe'):
            try:
                r = requests.get(f.tahoe_info_url())
                size = r.json[1]['size']
                total += size
                cnt += 1
            except:
                pass
        print "%d files, %dGB" % (
            cnt, total / (1024 * 1024 * 1024))
