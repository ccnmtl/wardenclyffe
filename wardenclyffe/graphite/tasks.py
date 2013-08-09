from celery.decorators import periodic_task
from celery.task.schedules import crontab
from django.conf import settings
from socket import socket
import time
import sys
from .models import operation_count_by_status


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
    results = operation_count_by_status()
    total = sum(results.values())
    now = int(time.time())
    lines = [
        "%s.operations.total %d %d" % (settings.GRAPHITE_PREFIX,
                                       total, now),
        "%s.operations.failed %d %d" % (settings.GRAPHITE_PREFIX,
                                        results['failed'], now),
        "%s.operations.enqueued %d %d" % (settings.GRAPHITE_PREFIX,
                                          results['enqueued'], now),
        "%s.operations.submitted %d %d" % (settings.GRAPHITE_PREFIX,
                                           results['submitted'], now),
        "%s.operations.complete %d %d" % (settings.GRAPHITE_PREFIX,
                                          results['complete'], now),
        "%s.operations.inprogress %d %d" % (settings.GRAPHITE_PREFIX,
                                            results['in progress'], now),
    ]
    message = "\n".join(lines) + "\n"
    send_to_graphite(message)
