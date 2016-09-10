from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from ..models import StreamLog
from ..views import LogView


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
        l = StreamLog.objects.all().first()
        self.assertEqual(l.filename, params['filename'])
        self.assertEqual(l.remote_addr, params['remote_addr'])
        self.assertEqual(l.offset, params['offset'])
        self.assertEqual(l.referer, params['referer'])
        self.assertEqual(l.user_agent, params['user_agent'])
        self.assertEqual(l.access, params['access'])
