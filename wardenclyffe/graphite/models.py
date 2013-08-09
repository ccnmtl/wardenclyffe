from django.conf import settings
from wardenclyffe.main.models import Operation
import time


def operation_count_by_status():
    """ get a count of all operations grouped by status
    -> dict() of {status -> int}

    failed  complete  submitted  in progress  enqueued
    """
    return {
        'failed': Operation.objects.filter(status="failed").count(),
        'complete': Operation.objects.filter(status="complete").count(),
        'submitted': Operation.objects.filter(status="submitted").count(),
        'in progress': Operation.objects.filter(status="in progress").count(),
        'enqueued': Operation.objects.filter(status="enqueued").count()}


def generate_operation_count_report(results):
    """ return report on operations by status suitable to send to graphite

    dict() -> string
    """
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
    return message


def operation_count_report():
    """get count of all operations grouped by status as graphite ready message

    -> string
    """
    results = operation_count_by_status()
    print str(results)
    return generate_operation_count_report(results)
