from django.core.management.base import BaseCommand
import gdata.youtube
import gdata.youtube.service


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, **kwargs):
        yt_service = gdata.youtube.service.YouTubeService()
        print("hi")
