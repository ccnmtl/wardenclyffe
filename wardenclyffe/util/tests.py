from __future__ import unicode_literals

import unittest

from django.core import mail
from django.test import TestCase
from wardenclyffe.util.mail import slow_operations_email_body
from wardenclyffe.util.mail import failed_operation_body
from wardenclyffe.util.mail import mediathread_received_body
from wardenclyffe.util.mail import mediathread_uploaded_body
from wardenclyffe.util.mail import youtube_submitted_body
from wardenclyffe.util.mail import send_slow_operations_email
from wardenclyffe.util.mail import send_failed_operation_mail
from wardenclyffe.util.mail import send_mediathread_received_mail
from wardenclyffe.util.mail import send_mediathread_uploaded_mail
from wardenclyffe.util.mail import send_youtube_submitted_mail
from wardenclyffe.util import uuidparse, safe_basename


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
        with self.settings(
                MEDIATHREAD_BASE='https://mediathread.ccnmtl.columbia.edu/'):

            body = mediathread_uploaded_body("test video", "testuni",
                                             "/asset/1")
            assert "confirms that test video" in body
            assert "for testuni" in body
            assert (
                "https://mediathread.ccnmtl.columbia.edu/asset/1" in body)

    def test_youtube_submitted_body(self):
        body = youtube_submitted_body("fake video title", "fakeuni",
                                      "http://example.com/")
        assert 'confirms that "fake video title"' in body
        assert "by fakeuni" in body
        assert "YouTube URL: http://example.com/" in body


class MailTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_send_slow_operations_email(self):
        operations = DummyOperationsSet(1)
        send_slow_operations_email(operations)
        assert len(mail.outbox) > 0
        self.assertEqual(mail.outbox[0].subject, 'Slow operations detected')

    def test_send_slow_operations_to_videoteam_email(self):
        operations = DummyOperationsSet(1)
        send_slow_operations_email(operations)
        assert len(mail.outbox) > 0
        self.assertEqual(mail.outbox[0].subject, 'Slow operations detected')

    def test_send_failed_operation_mail(self):
        dummy_op = DummyOperation(action="dummy",
                                  video=DummyVideo("dummy video"))
        send_failed_operation_mail(dummy_op, "fake error message")
        assert len(mail.outbox) > 0
        self.assertEqual(mail.outbox[0].subject, 'Video upload failed')

    def test_send_mediathread_received_mail(self):
        send_mediathread_received_mail("fake video", "fakeuni")
        assert len(mail.outbox) > 1
        self.assertEqual(mail.outbox[0].subject,
                         "Mediathread submission received")

    def test_send_mediathread_uploaded_mail(self):
        with self.settings(
                MEDIATHREAD_BASE='https://mediathread.ccnmtl.columbia.edu/'):
            send_mediathread_uploaded_mail("fake video", "fakeuni",
                                           "/asset/1/")
            assert len(mail.outbox) > 1
            self.assertEqual(mail.outbox[0].subject,
                             "Mediathread submission now available")
            self.assertTrue(
                mail.outbox[0].body.find(
                    "https://mediathread.ccnmtl.columbia.edu/asset/1") > 0)

    def test_send_youtube_submitted_mail(self):
        send_youtube_submitted_mail("fake video title", "fakeuni",
                                    "http://example.com/")
        assert len(mail.outbox) > 1
        self.assertEqual(
            mail.outbox[0].subject,
            "\"fake video title\" was submitted to Columbia on YouTube EDU")


class UUIDParseTest(TestCase):
    def test_uuidparse(self):
        self.assertEqual(
            uuidparse('4a6e4a20-fd8f-4e2a-9808-4ed612b1f0d0.mov'),
            '4a6e4a20-fd8f-4e2a-9808-4ed612b1f0d0')
        self.assertEqual(
            uuidparse('not a uuid'),
            '')


class SafeBasenameTests(unittest.TestCase):
    def test_safe_basename(self):
        self.assertEqual(safe_basename('Foo bar.png'), 'foobar.png')
