from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from ..models import StreamLog
from ..views import LogView, ReportView


class ViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()


class LogViewTest(ViewTest):
    def test_post(self):
        params = dict(
            filename='foo.flv',
            remote_addr='test remote addr',
            offset='test offset',
            referer='test referer',
            user_agent='test user agent',
            access='test access',
        )
        request = self.factory.post(reverse('streamlogs'), params)
        response = LogView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StreamLog.objects.count(), 1)
        log = StreamLog.objects.all().first()
        self.assertEqual(log.filename, params['filename'])
        self.assertEqual(log.remote_addr, params['remote_addr'])
        self.assertEqual(log.offset, params['offset'])
        self.assertEqual(log.referer, params['referer'])
        self.assertEqual(log.user_agent, params['user_agent'])
        self.assertEqual(log.access, params['access'])


class ReportViewTest(ViewTest):
    def test_get(self):
        request = self.factory.get(reverse('streamlogs-report'))
        response = ReportView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('total_count' in response.context_data)
        self.assertTrue('daily_counts' in response.context_data)
