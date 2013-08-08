from wardenclyffe.main.models import Operation


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
