import wardenclyffe.main.tasks as tasks

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from wardenclyffe.main.models import Video


class Command(BaseCommand):
    def add_arguments(self, parser):
        # we need to specify a user to associate with the operations
        parser.add_argument('uni', type=str)

        # how many to convert in this run
        parser.add_argument('n', type=int)

    def handle(self, *args, **kwargs):
        uni = kwargs['uni']
        n = kwargs['n']

        user = User.objects.get(username=uni)

        operations = []
        cnt = 0
        for video in Video.objects.all():
            if (not video.flv_convertable()
                    or not video.has_mediathread_asset()):
                continue
            video.create_mediathread_update()
            if video.has_s3_source():
                # we don't need to pull down the flv, there's
                # already a copy in S3. instead, just
                # kick off the elastic transcode job
                operations.append(
                    video.make_create_elastic_transcoder_job_operation(
                        video.s3_key(),
                        user,
                    ))
            else:
                # have to pull it down
                operations.append(video.make_flv_to_mp4_operation(user))
            cnt += 1
            if cnt > n:
                break

        print("converting %d videos" % cnt)
        self.enqueue_operations(operations)

    def enqueue_operations(self, operations):
        for o in operations:
            tasks.process_operation.delay(o.id)
