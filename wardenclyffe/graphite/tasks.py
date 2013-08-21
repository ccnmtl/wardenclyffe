from celery.decorators import periodic_task
from celery.task.schedules import crontab
from django_statsd.clients import statsd
from .models import operation_count_by_status
from .models import tahoe_stats
from .models import minutes_video_stats


@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def operations_report():
    r = operation_count_by_status()
    statsd.gauge("operations.failed", r['failed'])
    statsd.gauge("operations.complete", r['complete'])
    statsd.gauge("operations.submitted", r['submitted'])
    statsd.gauge("operations.inprogress", r['in progress'])
    statsd.gauge("operations.enqueued", r['enqueued'])
    statsd.gauge("operations.total", sum(r.values()))


@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def minutes_video():
    statsd.gauge("minutes_video", int(minutes_video_stats()))


@periodic_task(run_every=crontab(hour="22", minute="13", day_of_week="*"))
def nightly_tahoe_report():
    (cnt, total) = tahoe_stats()
    statsd.gauge("tahoe.total", total)
    statsd.gauge("tahoe.cnt", cnt)
