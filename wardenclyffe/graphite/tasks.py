from celery.decorators import periodic_task
from celery.task.schedules import crontab
from socket import socket
import time
import sys
from .models import operation_count_by_status


# TODO: move these to django settings
PREFIX = "ccnmtl.app.counters.wardenclyffe"
CARBON_SERVER = '128.59.222.209'
CARBON_PORT = 2003


@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def operations_report():
    results = operation_count_by_status()
    total = sum(results.values())
    now = int(time.time())
    lines = [
        "%s.operations.total %d %d" % (PREFIX, total, now),
        "%s.operations.failed %d %d" % (PREFIX, results['failed'], now),
        "%s.operations.enqueued %d %d" % (PREFIX, results['enqueued'], now),
        "%s.operations.submitted %d %d" % (PREFIX, results['submitted'], now),
        "%s.operations.complete %d %d" % (PREFIX, results['complete'], now),
        "%s.operations.inprogress %d %d" % (PREFIX, results['in progress'],
                                            now),
    ]
    message = "\n".join(lines) + "\n"
    sock = socket()
    try:
        sock.connect((CARBON_SERVER, CARBON_PORT))
    except:
        print (
            "Couldn't connect to %(server)s on port %(port)d, "
            "is carbon-agent.py running?") % {
                'server': CARBON_SERVER, 'port': CARBON_PORT
            }
        sys.exit(1)

    sock.sendall(message)
