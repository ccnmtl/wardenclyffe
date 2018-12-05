from django.core.management.base import BaseCommand
from wardenclyffe.main.models import File
import boto
from boto.s3.key import Key
import tempfile


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self,
               OLD_AWS_ACCESS_KEY,
               OLD_AWS_SECRET_KEY,
               OLD_AWS_S3_UPLOAD_BUCKET,

               NEW_AWS_ACCESS_KEY,
               NEW_AWS_SECRET_KEY,
               NEW_AWS_S3_UPLOAD_BUCKET,

               **kwargs):

        old_conn = boto.connect_s3(
            OLD_AWS_ACCESS_KEY,
            OLD_AWS_SECRET_KEY)
        old_bucket = old_conn.get_bucket(OLD_AWS_S3_UPLOAD_BUCKET)

        new_conn = boto.connect_s3(
            NEW_AWS_ACCESS_KEY,
            NEW_AWS_SECRET_KEY)
        new_bucket = new_conn.get_bucket(NEW_AWS_S3_UPLOAD_BUCKET)

        for f in File.objects.filter(location_type='s3'):
            video = f.video
            print("Video: " + video.title)
            try:
                print("  pulling down from old bucket")
                k = Key(old_bucket)
                k.key = video.s3_key()
                suffix = video.extension()
                t = tempfile.NamedTemporaryFile(suffix=suffix)
                k.get_contents_to_file(t)
                t.seek(0)
                print("  done")

                print("  uploading to new bucket")
                k = Key(new_bucket)
                k.key = video.s3_key()
                k.set_contents_from_file(t)
                t.close()
                print("  done")
            except Exception as e:
                print("Failed: " + str(e))
