import os
import re
from datetime import timedelta
from django.db import connection
from django.db import models
from django.conf import settings

from wardenclyffe.main.models import File


class StreamLog(models.Model):
    filename = models.TextField(blank=True)
    remote_addr = models.TextField(blank=True)
    offset = models.TextField(blank=True)
    referer = models.TextField(blank=True)
    user_agent = models.TextField(blank=True)
    # how they were authenticated: cookie, url hash, or public
    access = models.TextField(blank=True)
    request_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-request_at']

    def video(self):
        """ try to find a Video that matches this entry.
        not all files will have a match, so it can also return None
        """
        f = File.objects.filter(
            location_type='cuit', filename=self.full_filename()).first()
        if f is not None:
            return f.video

        sf = self.secure_filename()
        f = File.objects.filter(
            location_type='cuit', filename=sf).first()
        if f is not None:
            return f.video

        return None

    def full_filename(self):
        # unfortunately, streamlogs filenames start with a 'broadcast/'
        # and the broadcast directory also includes it. So we need to
        # to strip it first.
        pattern = re.compile(r'^broadcast/')
        filename = pattern.sub("", self.filename)
        return os.path.join(settings.CUNIX_BROADCAST_DIRECTORY, filename)

    def secure_filename(self):
        return os.path.join(settings.H264_SECURE_STREAM_DIRECTORY,
                            self.filename.strip('/'))


def counts_by_date():
    by_date = dict()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT date(request_at), count(*)
            FROM streamlogs_streamlog GROUP BY date(request_at)""")
        for row in cursor.fetchall():
            by_date[row[0].isoformat()] = row[1]
    return by_date


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def daily_counts(start, end):
    by_date = counts_by_date()
    results = []
    for d in daterange(start, end):
        results.append(
            dict(date=d.date(), count=by_date.get(d.date().isoformat(), 0)))
    return results
