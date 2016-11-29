import wardenclyffe.main.tasks as tasks

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from wardenclyffe.main.models import Video, Collection, File


class Command(BaseCommand):
    def add_arguments(self, parser):
        # we need to specify a user to associate with the operations
        parser.add_argument('uni', type=str)

        # id of the collection to create the video in
        # (videos have to be in a collection)
        parser.add_argument('collection', type=int)

        # and the filename of the flv to import
        parser.add_argument('flv', type=str)

    def handle(self, *args, **kwargs):
        uni = kwargs['uni']
        collection_id = kwargs['collection']
        flv = kwargs['flv']

        user = User.objects.get(username=uni)
        collection = Collection.objects.get(id=collection_id)

        # create basic video
        v = Video.objects.simple_create(collection, flv, uni)

        # create an FLV File for the video
        File.objects.create(
            video=v,
            filename=flv,
            location_type='cuit',
            label='CUIT FLV',
        )

        # now we can just pretend that it was originally uploaded
        # through WC and someone has now hit the 'FLV to MP4' button

        o = v.make_flv_to_mp4_operation(user)
        tasks.process_operation.delay(o.id)

        # print out the location of the video so it's easy to check
        # up on it in the browser:
        print(v.get_absolute_url())
