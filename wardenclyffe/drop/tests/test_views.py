from __future__ import unicode_literals

import unittest

from django.http import Http404
from django.test import TestCase, RequestFactory
from wardenclyffe.drop.tests.factories import DropBucketFactory
from wardenclyffe.drop.tests.test_snsparser import sample_video_message, \
    sample_message
from wardenclyffe.drop.views import SNSView, is_encodable_file


class TestSNSView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_invalid_message(self):
        request = self.factory.post(
            "/sns/endpoint/",
            {}
        )
        response = SNSView.as_view()(request)
        self.assertEqual(response.status_code, 400)

    def test_valid_message_with_no_matching_bucket(self):
        request = self.factory.post(
            "/sns/endpoint/",
            data=sample_video_message(),
            content_type='application/json',
        )
        with self.assertRaises(Http404):
            SNSView.as_view()(request)

    def test_valid_message_with_matching_bucket(self):
        DropBucketFactory(bucket_id="ctl-wardenclyffe-dropbox-test")
        request = self.factory.post(
            "/sns/endpoint/",
            data=sample_message(),
            content_type='application/json',
        )
        response = SNSView.as_view()(request)
        self.assertEqual(response.status_code, 200)


class TestIsEncodableFile(unittest.TestCase):
    def test_basics(self):
        self.assertTrue(is_encodable_file("foo.mp4"))
        self.assertTrue(is_encodable_file("foo/bar/baz.mp4"))
        self.assertTrue(is_encodable_file("foo.MP4"))
        self.assertTrue(is_encodable_file("foo.wmv"))
        self.assertTrue(is_encodable_file("foo.MP3"))

        self.assertFalse(is_encodable_file("foo.jpg"))
        self.assertFalse(is_encodable_file("foo.txt"))
