from django.core.management.base import BaseCommand
from wardenclyffe.youtube.util import (
    get_credentials)


class Command(BaseCommand):
    help = 'upload a video to youtube to test out code'

    def add_arguments(self, parser):
        parser.add_argument('video', type=str)

    def handle(self, *args, **kwargs):
        credentials = get_credentials()
        print(str(credentials))
        print("new credentials file written to youtube_oauth.json")
