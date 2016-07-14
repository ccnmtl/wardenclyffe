from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.generic.base import View

from .models import DropBucket
from .snsparser import SNSMessage, SNSMessageError
from .tasks import move_from_dropbucket_to_upload_bucket


class SNSView(View):
    def post(self, request):
        request_body = request.read()

        try:
            s = SNSMessage(request_body)
            if (s.message_type() != "Notification"
                    and s.topic() != settings.DROPBOX_TOPIC_ARN):
                return HttpResponseBadRequest()
            for r in s.records():
                s3key = r.s3_bucket_key()
                if s3key.endswith("/"):
                    # someone made a directory. not a file upload. ignore.
                    continue
                b = get_object_or_404(
                    DropBucket, bucket_id=r.s3_bucket_name())
                move_from_dropbucket_to_upload_bucket.delay(b.id, s3key)
        except SNSMessageError:
            return HttpResponseBadRequest()
        return HttpResponse("OK")
