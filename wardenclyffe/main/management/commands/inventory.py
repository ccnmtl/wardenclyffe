import os

from django.core.management.base import BaseCommand

import csv
from wardenclyffe.main.models import File, Collection, Video


class Command(BaseCommand):

    VALID_EXTENSIONS = [
        '.rm',
        '.wma',
        '.smil',
        '.rp',
        '.rt',
        '.rpl',
        '.mov',
        '.ra',
        '.avi',
        '.mpg',
        '.mp3',
        '.m4a',
        '.flv',
        '.m4v',
        '.mp4']

    def create_record(self, full_filename, filename):
        print('{}'.format(full_filename))
        collection = Collection.objects.get(title='Unclassified')

        # create basic video
        v = Video.objects.simple_create(collection, filename, 'sld2131')

        # create the File for the video
        File.objects.create(
           video=v,
           filename=full_filename,
           location_type='cuit',
           label='source file')

        # add tags based on the directory and filename
        EXCLUDE = ['media', 'projects', '/', '', 'ccnmtl', 'public',
                   'www', 'data', 'remote', 'all', 'raw']
        bits = full_filename.split('/')
        for idx in range(0, len(bits) - 1):
            bit = bits[idx]
            if bit and bit not in EXCLUDE:
                v.tags.add(bit)

    def process_file(self, row):
        full_filename = row[-1]
        filename = os.path.split(full_filename)[-1]

        # only consider files with a video-ish extension
        root, ext = os.path.splitext(filename)
        if ext not in self.VALID_EXTENSIONS:
            return

        try:
            File.objects.get(filename__iendswith=filename)
        except File.DoesNotExist:
            self.create_record(full_filename, filename)
        except File.MultipleObjectsReturned:
            pass

    def add_arguments(self, parser):
        # where the inventory directories live
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        # for each inventory directory listing
        # * recursively read the directory listing
        # * is there a reference to the video file in Wardenclyffe?
        # * print status
        local_path = kwargs['path']
        files = os.listdir(local_path)

        for f in files:
            content = open(os.path.join(local_path, f), 'r')
            reader = csv.reader(content)
            for row in reader:
                self.process_file(row)
