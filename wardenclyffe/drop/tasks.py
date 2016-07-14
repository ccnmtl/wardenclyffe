import boto

from celery.decorators import task
from django.conf import settings

from wardenclyffe.main.models import Video
from wardenclyffe.main.tasks import exp_backoff
from wardenclyffe.main.views import enqueue_operations
from .models import DropBucket


@task(ignore_results=True, bind=True, max_retries=None)
def move_from_dropbucket_to_upload_bucket(self, bucket_id, s3key, **kwargs):
    print("move_from_dropbucket_to_upload_bucket({}, {})".format(
        bucket_id, s3key))
    try:
        b = DropBucket.objects.get(pk=bucket_id)
        conn = boto.connect_s3(
            settings.AWS_ACCESS_KEY,
            settings.AWS_SECRET_KEY)
        drop_bucket = conn.get_bucket(b.bucket_id)
        upload_bucket = conn.get_bucket(settings.AWS_S3_UPLOAD_BUCKET)
        # TODO: filename santization
        upload_bucket.copy_key(s3key, drop_bucket, s3key)

        # now that it's moved, we need to kick off a regular upload pipeline
        # using the info from the DropBucket
        v = Video.objects.simple_create(
            collection=b.collection,
            title=s3key,
            username=b.user.username,
        )
        v.make_source_file(s3key)
        v.make_uploaded_source_file(s3key)

        operations = v.initial_operations(s3key, b.user, b.collection.audio)
        enqueue_operations(operations)
        print("move completed")
    except Exception as exc:
        print "Exception:"
        print str(exc)
        if self.request.retries > settings.OPERATION_MAX_RETRIES:
            # max out at (default) 10 retry attempts
            print("max retries")
        else:
            print("retry: {}".format(self.request.retries))
            self.retry(exc=exc, countdown=exp_backoff(self.request.retries))
