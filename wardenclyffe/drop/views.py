import os.path

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.generic.base import View

from .models import DropBucket
from .snsparser import SNSMessage, SNSMessageError
from .tasks import move_from_dropbucket_to_upload_bucket


def is_encodable_file(fname):
    return os.path.splitext(fname)[1].lower() in settings.ALLOWED_EXTENSIONS


def process_record(r):
    s3key = r.s3_bucket_key()
    if r.is_directory():
        # someone made a directory. not a file upload. ignore.
        return
    if not is_encodable_file(s3key):
        # only try to process audio/video files
        return
    b = get_object_or_404(
        DropBucket, bucket_id=r.s3_bucket_name())
    move_from_dropbucket_to_upload_bucket.delay(
        b.id, s3key, r.title())


class SNSView(View):
    def post(self, request):
        request_body = request.read()

        try:
            s = SNSMessage(request_body)
            if (s.message_type() != "Notification"
                    and s.topic() != settings.DROPBOX_TOPIC_ARN):
                return HttpResponseBadRequest()
            for r in s.records():
                process_record(r)
        except SNSMessageError:
            return HttpResponseBadRequest()
        return HttpResponse("OK")
