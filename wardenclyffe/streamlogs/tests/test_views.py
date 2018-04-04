from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

from wardenclyffe.main.tests.factories import UserFactory
from wardenclyffe.streamlogs.models import StreamLog
from wardenclyffe.streamlogs.tests.factories import StreamLogFactory
from wardenclyffe.streamlogs.views import LogView, ReportView


class LogViewTest(TestCase):
    def test_post(self):
        params = dict(
            filename='foo.flv',
            remote_addr='test remote addr',
            offset='test offset',
            referer='test referer',
            user_agent='test user agent',
            access='test access',
        )
        request = RequestFactory().post(reverse('streamlogs'), params)
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


class ReportViewTest(TestCase):
    def test_get(self):
        request = RequestFactory().get(reverse('streamlogs-report'))
        response = ReportView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('total_count' in response.context_data)
        self.assertTrue('daily_counts' in response.context_data)


class StreamLogListViewTest(TestCase):

    def setUp(self):
        StreamLogFactory()
        StreamLogFactory(filename="bar.mp4")
        self.log = StreamLogFactory(filename="foo.mp4")

    def test_anonymous(self):
        response = self.client.get(reverse('streamlogs-list'))
        self.assertEqual(response.status_code, 302)

    def test_get(self):
        user = UserFactory()
        url = reverse('streamlogs-list')
        self.client.login(username=user, password='test')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.context_data['object_list'].count(), 3)

        response = self.client.get(url + '?q=foo')
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.context_data['object_list'].count(), 1)
        self.assertEquals(response.context_data['object_list'].first(),
                          self.log)
