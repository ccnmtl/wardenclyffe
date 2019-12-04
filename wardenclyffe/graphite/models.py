from django.conf import settings
from wardenclyffe.main.models import Operation, File, Metadata
import boto3


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


def s3_stats():
    """ return info on S3 storage usage
    -> (int, int) for (# files, bytes)
    """
    total = 0
    cnt = 0
    s3 = boto3.resource(
        's3', aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY)
    bucket = s3.Bucket(settings.AWS_S3_UPLOAD_BUCKET)
    for f in File.objects.filter(location_type="s3"):
        k = bucket.get_key(f.video.s3_key())
        if k is not None:
            total += k.size
            cnt += 1
    return (cnt, total)


def minutes_video_stats():
    "return the total number of minutes of video uploaded"
    return sum(
        [
            float(str(m.value))
            for m in Metadata.objects.filter(
                field='ID_LENGTH',
                file__location_type='none')]) / 60.0
