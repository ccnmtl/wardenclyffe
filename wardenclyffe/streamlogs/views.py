from django.http import HttpResponse
from django.views.generic.base import View

from .models import StreamLog


class LogView(View):
    def post(self, request):
        StreamLog.objects.create(
            filename=request.POST.get('filename', ''),
            remote_addr=request.POST.get('remote_addr', ''),
            offset=request.POST.get('offset', ''),
            referer=request.POST.get('referer', ''),
            user_agent=request.POST.get('user_agent', ''),
            access=request.POST.get('access', ''),
        )
        return HttpResponse("ok")
