import csv

from django.core.management.base import BaseCommand
from django.utils.encoding import smart_str

from wardenclyffe.main.models import Video


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('videos', type=str)

    def format_description(self, row):
        URL = 11
        SUMMARY = 12
        COURSE_NUMBERS = 13
        COURSE_NAMES = 14
        FIELD_OF_PRACTICE = 15
        CONCEPTS = 16
        COPYRIGHT = 17
        KEYWORDS = 18
        METHOD = 19
        YEAR_PRODUCED = 20

        d = ('Url - {}\nSummary - {}\nKeywords - {}\n'
             'Copyright Holder - {}\nMethod - {}\n'
             'Field of Practice - {}\nConcepts - {}\n'
             'Course Names - {}\nCourse Numbers - {}\n'
             'Year Produced - {}')

        return d.format(
            row[URL], row[SUMMARY], row[KEYWORDS],
            row[COPYRIGHT], row[METHOD], row[FIELD_OF_PRACTICE],
            row[CONCEPTS], row[COURSE_NAMES], row[COURSE_NUMBERS],
            row[YEAR_PRODUCED])

    def handle(self, *args, **kwargs):
        VIDEO_ID = 9
        TITLE = 3

        content = open(kwargs['videos'], 'r')
        reader = csv.reader(content)
        reader.next()  # skip header

        for row in reader:
            try:
                video = Video.objects.get(id=int(row[VIDEO_ID]))
                video.title = row[TITLE]
                video.description = smart_str(self.format_description(row))
                video.save()
            except Video.DoesNotExist:
                print('Unable to find video - {}'.format(row[0]))
