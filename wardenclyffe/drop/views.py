from django.core.mail import send_mail
from django.http import HttpResponse
from django.views.generic.base import View


class SNSView(View):
    def post(self, request):
        request_body = request.read()
        request_meta = str(request.META)

        body = "{}\n\n\n{}".format(request_meta, request_body)

        send_mail(
            "SNS Debug",
            body,
            "snsdebug@wardenclyffe.ccnmtl.columbia.edu",
            ["anders@columbia.edu"],
            fail_silently=False)
        return HttpResponse("OK")
