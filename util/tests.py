from django.test import TestCase
from wardenclyffe.util.mail import slow_operations_email_body
from wardenclyffe.util.mail import failed_operation_body
from wardenclyffe.util.mail import mediathread_received_body


class DummyVideo(object):
    def __init__(self, title):
        self.title = title

    def get_absolute_url(self):
        return "/video/1/"


class DummyOperation(object):
    def __init__(self, action, video):
        self.action = action
        self.video = video


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
