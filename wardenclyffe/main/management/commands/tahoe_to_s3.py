from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from wardenclyffe.main.models import File
import boto
from boto.s3.key import Key
import tempfile
import urllib2
import os


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, **kwargs):
        self.conn = boto.connect_s3(
            settings.AWS_ACCESS_KEY,
            settings.AWS_SECRET_KEY)
        self.bucket = self.conn.get_bucket(settings.AWS_S3_UPLOAD_BUCKET)

        cnt = File.objects.filter(location_type='tahoe').count()
        i = 1
        for f in File.objects.filter(location_type='tahoe').order_by("id"):
            print "[%03d/%03d] moving video %d" % (
                i, cnt, f.video.id)
            i += 1
            try:
                self.move_file(f)
            except Exception, e:
                print "exception: %s" % str(e)

    @transaction.atomic
    def move_file(self, f):
        video = f.video
        url = video.tahoe_download_url()
        if url == "":
            print "does not have a tahoe stored file"
            return
        print "pulling from %s" % url
        suffix = video.extension()
        t = tempfile.NamedTemporaryFile(suffix=suffix)
        r = urllib2.urlopen(url)
        t.write(r.read())
        t.seek(0)
        print "pulled from tahoe and wrote to temp file"
        print t.name

        k = Key(self.bucket)
        # make a YYYY/MM/DD directory to put the file in
        n = video.created
        key = "%04d/%02d/%02d/%s" % (
            n.year, n.month, n.day,
            os.path.basename(video.filename()))
        k.key = key
        print "uploading to S3 with key %s" % key
        k.set_contents_from_file(t)
        t.close()
        print "uploaded"
        f = File.objects.create(video=video, url="", cap=key,
                                location_type="s3",
                                filename=video.filename(),
                                label="uploaded source file (S3)")

        print "remove tahoe file entry"
        f.delete()
