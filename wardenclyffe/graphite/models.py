from wardenclyffe.main.models import Operation, File, Metadata
import requests


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


def tahoe_stats():
    """ return info on Tahoe storage usage
    -> (int, int) for (# files, bytes)
    """
    total = 0
    cnt = 0
    for f in File.objects.filter(location_type='tahoe'):
        try:
            r = requests.get(f.tahoe_info_url())
            size = r.json[1]['size']
            total += size
            cnt += 1
        except:
            pass
    return (cnt, total)


def minutes_video_stats():
    "return the total number of minutes of video uploaded"
    return sum(
        [
            float(str(m.value))
            for m in Metadata.objects.filter(
                field='ID_LENGTH',
                file__location_type='none')]) / 60.0
