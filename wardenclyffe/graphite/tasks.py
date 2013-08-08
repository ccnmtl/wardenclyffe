from celery.decorators import periodic_task
from celery.task.schedules import crontab
from django_statsd.clients import statsd
from .models import operation_count_by_status


@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def operations_report():
    results = operation_count_by_status()
    total = sum(results.values())
    statsd.gauge("operations.total", total)
    statsd.gauge("operations.failed", results["failed"])
    statsd.gauge("operations.enqueued", results["enqueued"])
    statsd.gauge("operations.submitted", results["submitted"])
    statsd.gauge("operations.complete", results["complete"])
    statsd.gauge("operations.inprogress", results["in progress"])
