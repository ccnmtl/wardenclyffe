from celery.task.schedules import crontab
from django_statsd.clients import statsd
from wardenclyffe.main.celery import app
from wardenclyffe.graphite.models import operation_count_by_status, \
    minutes_video_stats, s3_stats


def operations_report(*args, **kwargs):
    print("operations_report()")
    r = operation_count_by_status()
    statsd.gauge("operations.failed", r['failed'])
    statsd.gauge("operations.complete", r['complete'])
    statsd.gauge("operations.submitted", r['submitted'])
    statsd.gauge("operations.inprogress", r['in progress'])
    statsd.gauge("operations.enqueued", r['enqueued'])
    statsd.gauge("operations.total", sum(r.values()))


def minutes_video(*args, **kwargs):
    print("minutes_video()")
    statsd.gauge("minutes_video", int(minutes_video_stats()))


def weekly_s3_usage_report(*args, **kwargs):
    print("weekly_s3_report()")
    (cnt, total) = s3_stats()
    statsd.gauge("s3.total", total)
    statsd.gauge("s3.cnt", cnt)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour='*', minute='*', day_of_week='*'),
        operations_report)

    sender.add_periodic_task(
        crontab(hour='*', minute='*', day_of_week='*'),
        minutes_video)

    sender.add_periodic_task(
        crontab(hour=5, minute=0, day_of_week=0),
        weekly_s3_usage_report)
