from django.core.management.base import BaseCommand
from django.conf import settings
from wardenclyffe.main.models import Image
from wardenclyffe.main.tasks import copy_image_to_s3


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **kwargs):
        for i in Image.objects.all():
            # sorl image.path gives the fullpath like:
            # /var/www/wardenclyffe/uploads/images/00011/00000003.jpg
            # so we need to get it relative to the MEDIA_ROOT
            relpath = i.image.path[len(settings.MEDIA_ROOT):]
            copy_image_to_s3.delay(relpath)
