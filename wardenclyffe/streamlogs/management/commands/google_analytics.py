import csv
from datetime import datetime

from django.core.management.base import BaseCommand

from wardenclyffe.streamlogs.models import StreamLog


class Command(BaseCommand):

    def process_file(self, row):
        dt = datetime.strptime(row[0], '%Y%m%d')
        referer = row[1]
        filename = row[2]

        sl = StreamLog.objects.create(filename=filename,
                                      referer=referer)

        # override the request_at, auto_now_add attribute
        sl.request_at = dt
        sl.save()

    def add_arguments(self, parser):
        # where the inventory directories live
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        local_path = kwargs['path']
        f = open(local_path, 'r')
        reader = csv.reader(f)
        for row in reader:
            self.process_file(row)
