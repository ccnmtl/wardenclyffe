from django.core import mail
from django.test import TestCase
from wardenclyffe.util.mail import slow_operations_email_body
from wardenclyffe.util.mail import failed_operation_body
from wardenclyffe.util.mail import mediathread_received_body
from wardenclyffe.util.mail import mediathread_uploaded_body
from wardenclyffe.util.mail import vital_received_body
from wardenclyffe.util.mail import vital_uploaded_body
from wardenclyffe.util.mail import vital_failed_body
from wardenclyffe.util.mail import youtube_submitted_body
from wardenclyffe.util.mail import send_slow_operations_email


class DummyVideo(object):
    def __init__(self, title):
        self.title = title

    def get_absolute_url(self):
        return "/video/1/"


class DummyOperation(object):
    def __init__(self, action, video):
        self.action = action
        self.video = video


class DummyOperationsSet(object):
    def __init__(self, cnt=0):
        self.cnt = cnt

    def count(self):
        return self.cnt


class BodyTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_slow_operations_body(self):
        num_operations = 1
        body = slow_operations_email_body(num_operations)
        assert "1 operation " in body
        num_operations = 2
        body = slow_operations_email_body(num_operations)
        assert "2 operations " in body

    def test_send_slow_operations_email(self):
        operations = DummyOperationsSet(1)
        send_slow_operations_email(operations)
        assert len(mail.outbox) > 0
        self.assertEqual(mail.outbox[0].subject, 'Slow operations detected')

    def test_failed_operation_body(self):
        dummy_op = DummyOperation(action="dummy",
                                  video=DummyVideo("dummy video"))
        body = failed_operation_body(dummy_op, "fake error message")
        assert "fake error message" in body
        assert "http://wardenclyffe.ccnmtl.columbia.edu/video/1/" in body

    def test_mediathread_received_body(self):
        body = mediathread_received_body("test video", "testuni")
        assert "confirms that 'test video'" in body
        assert "for testuni" in body

    def test_mediathread_uploaded_body(self):
        body = mediathread_uploaded_body("test video", "testuni",
                                         "http://example.com/")
        assert "confirms that test video" in body
        assert "for testuni" in body
        assert "http://example.com/" in body

    def test_vital_received_body(self):
        body = vital_received_body("test video", "testuni")
        assert "test video has been successfully" in body
        assert "by testuni" in body

    def test_vital_uploaded_body(self):
        body = vital_uploaded_body("test video", "testuni",
                                         "http://example.com/")
        assert "confirms that test video" in body
        assert "by testuni" in body
        assert "http://example.com/" in body

    def test_vital_failed_body(self):
        body = vital_failed_body("fake video title", "fake error message")
        assert "fake error message" in body
        assert "fake video title" in body

    def test_youtube_submitted_body(self):
        body = youtube_submitted_body("fake video title", "fakeuni",
                                      "http://example.com/")
        assert 'confirms that "fake video title"' in body
        assert "by fakeuni" in body
        assert "YouTube URL: http://example.com/" in body
