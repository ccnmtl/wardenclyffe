from celery.decorators import periodic_task
from celery.task.schedules import crontab
from django.conf import settings
from django_statsd.clients import statsd
from socket import socket
import sys
from .models import operation_count_by_status
from .models import operation_count_report
from .models import tahoe_report
from .models import tahoe_stats
from .models import minutes_video_report
from .models import minutes_video_stats


def send_to_graphite(message):
    sock = socket()
    try:
        sock.connect((settings.CARBON_SERVER, settings.CARBON_PORT))
    except:
        print (
            "Couldn't connect to %(server)s on port %(port)d, "
            "is carbon-agent.py running?") % {
                'server': settings.CARBON_SERVER,
                'port': settings.CARBON_PORT,
            }
        sys.exit(1)

    sock.sendall(message)


@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def operations_report():
    send_to_graphite(operation_count_report())
    r = operation_count_by_status()
    statsd.gauge("operations.failed", r['failed'])
    statsd.gauge("operations.complete", r['complete'])
    statsd.gauge("operations.submitted", r['submitted'])
    statsd.gauge("operations.inprogress", r['in progress'])
    statsd.gauge("operations.enqueued", r['enqueued'])
    statsd.gauge("operations.total", sum(r.values()))


@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def minutes_video():
    send_to_graphite(minutes_video_report())
    statsd.gauge("minutes_video", minutes_video_stats())


@periodic_task(run_every=crontab(hour="22", minute="13", day_of_week="*"))
def nightly_tahoe_report():
    send_to_graphite(tahoe_report())
    (cnt, total) = tahoe_stats()
    statsd.gauge("tahoe.total", total)
    statsd.gauge("tahoe.cnt", cnt)
