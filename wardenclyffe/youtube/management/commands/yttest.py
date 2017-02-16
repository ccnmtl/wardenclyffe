from django.core.management.base import BaseCommand
from wardenclyffe.youtube.util import (
    get_authenticated_service, initialize_upload)


class Args(object):
    pass


class Command(BaseCommand):
    help = 'upload a video to youtube to test out code'

    def add_arguments(self, parser):
        parser.add_argument('video', type=str)

    def handle(self, *args, **kwargs):
        a = Args()
        a.logging_level = 'DEBUG'
        youtube = get_authenticated_service()
        a.file = kwargs['video']
        a.title = "test video"
        a.description = "delete me"
        a.privacyStatus = "public"
        a.keywords = []
        # 27 = "Education". see wardenclyffe/youtube/categories.json
        a.category = "27"
        initialize_upload(youtube, a)
