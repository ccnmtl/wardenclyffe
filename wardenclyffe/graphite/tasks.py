from celery.decorators import periodic_task
from celery.task.schedules import crontab
from django.conf import settings
from socket import socket
import sys
from .models import operation_count_report
from .models import tahoe_report


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


@periodic_task(run_every=crontab(hour="22", minute="13", day_of_week="*"))
def nightly_tahoe_report():
    send_to_graphite(tahoe_report())
