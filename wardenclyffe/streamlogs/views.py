from datetime import datetime, timedelta

from django.db.models.aggregates import Count, Max
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.urls.base import reverse
from django.views.generic.base import View, TemplateView
from django.views.generic.list import ListView

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
    days = 30

    def get_context_data(self, **kwargs):
        context = super(ReportView, self).get_context_data(**kwargs)
        context['total_count'] = StreamLog.objects.all().count()
        context['days'] = self.days
        today = datetime.now()
        start = today - timedelta(days=self.days)
        context['daily_counts'] = daily_counts(start, today)
        return context


class StreamLogListView(ListView):
    model = StreamLog
    paginate_by = 50

    def get_queryset(self):
        qs = StreamLog.objects.all()

        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(filename__icontains=q) |
                Q(referer__icontains=q)
            )

        # aggregate
        qs = qs.values('filename').annotate(
            views=Count('id'), last_view=Max('request_at'))

        sort_by = 'last_view'
        direction = self.request.GET.get('direction', 'desc')
        if direction == 'desc':
            qs = qs.order_by('-' + sort_by)
        else:
            qs = qs.order_by(sort_by)

        return qs

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)

        base = reverse('streamlogs-list')
        context['base_url'] = u'{}?page='.format(base)
        context['q'] = self.request.GET.get('q', '')
        context['sort_by'] = self.request.GET.get('sort_by', 'request_at')
        context['direction'] = self.request.GET.get('direction', 'desc')
        context['page'] = self.request.GET.get('page', '1')

        return context


class StreamLogDetailView(ListView):
    model = StreamLog
    paginate_by = 50
    template_name = 'streamlogs/streamlog_detail.html'

    def get_queryset(self):
        qs = StreamLog.objects.all()

        f = self.request.GET.get('f', '')
        if f:
            qs = qs.filter(filename=f)

        qs.order_by('-request_at')
        return qs

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)

        base = reverse('streamlogs-detail')
        context['base_url'] = u'{}?page='.format(base)
        context['page'] = self.request.GET.get('page', '1')

        return context
