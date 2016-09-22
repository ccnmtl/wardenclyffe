from datetime import timedelta
from django.db import connection
from django.db import models


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
