from datetime import datetime, timedelta
from django.http import HttpResponse
from django.views.generic.base import View, TemplateView

from .models import StreamLog, daily_counts


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


class ReportView(TemplateView):
    template_name = "streamlogs/report.html"

    def get_context_data(self, **kwargs):
        context = super(ReportView, self).get_context_data(**kwargs)
        context['total_count'] = StreamLog.objects.all().count()
        today = datetime.now()
        start = today - timedelta(days=30)
        context['daily_counts'] = daily_counts(start, today)
        return context
