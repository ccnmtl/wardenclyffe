from celery.task.schedules import crontab
from django_statsd.clients import statsd
from wardenclyffe.celery import app
from wardenclyffe.graphite.models import operation_count_by_status, \
    minutes_video_stats


@app.task
def operations_report():
    print("operations_report()")
    r = operation_count_by_status()
    statsd.gauge("operations.failed", r['failed'])
    statsd.gauge("operations.complete", r['complete'])
    statsd.gauge("operations.submitted", r['submitted'])
    statsd.gauge("operations.inprogress", r['in progress'])
    statsd.gauge("operations.enqueued", r['enqueued'])
    statsd.gauge("operations.total", sum(r.values()))


@app.task
def minutes_video():
    print("minutes_video()")
    statsd.gauge("minutes_video", int(minutes_video_stats()))


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour='*', minute='*', day_of_week='*'),
        operations_report.s())

    sender.add_periodic_task(
        crontab(hour='*', minute='*', day_of_week='*'),
        minutes_video.s())
