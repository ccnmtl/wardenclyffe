from celery.decorators import periodic_task
from celery.task.schedules import crontab
from django_statsd.clients import statsd
from .models import operation_count_by_status
from .models import s3_stats
from .models import minutes_video_stats


@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def operations_report():
    print "operations_report()"
    r = operation_count_by_status()
    statsd.gauge("operations.failed", r['failed'])
    statsd.gauge("operations.complete", r['complete'])
    statsd.gauge("operations.submitted", r['submitted'])
    statsd.gauge("operations.inprogress", r['in progress'])
    statsd.gauge("operations.enqueued", r['enqueued'])
    statsd.gauge("operations.total", sum(r.values()))


@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def minutes_video():
    print "minutes_video()"
    statsd.gauge("minutes_video", int(minutes_video_stats()))


@periodic_task(run_every=crontab(hour="*", minute="10", day_of_week="*"))
def hourly_s3_usage_report():
    print "hourly_s3_report()"
    (cnt, total) = s3_stats()
    statsd.gauge("s3.total", total)
    statsd.gauge("s3.cnt", cnt)
