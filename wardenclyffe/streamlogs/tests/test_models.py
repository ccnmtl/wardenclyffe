from __future__ import unicode_literals

from django.conf import settings
from django.test import TestCase
from wardenclyffe.main.tests.factories import FileFactory
from wardenclyffe.streamlogs.tests.factories import StreamLogFactory


class StreamLogTest(TestCase):
    def test_create(self):
        f = StreamLogFactory()
        self.assertIsNotNone(f)

    def test_full_filename(self):
        f = StreamLogFactory(filename='broadcast/foo/bar.flv')
        self.assertEqual(
            f.full_filename(),
            settings.CUNIX_BROADCAST_DIRECTORY + "foo/bar.flv")

    def test_full_secure_filename(self):
        s = StreamLogFactory(filename='broadcast/secure/foo/bar.flv')
        self.assertEqual(
            s.full_secure_filename(),
            settings.CUNIX_SECURE_DIRECTORY + "foo/bar.flv")

    def test_video_no_match(self):
        f = StreamLogFactory()
        self.assertIsNone(f.video())

    def test_video_positive_match(self):
        s = StreamLogFactory(filename="broadcast/foo/bar.flv")
        f = FileFactory(
            filename=settings.CUNIX_BROADCAST_DIRECTORY + "foo/bar.flv",
            location_type='cuit')
        self.assertEqual(s.video(), f.video)

    def test_similar_video(self):
        s = StreamLogFactory(filename="broadcast/foo/bar.flv")
        self.assertFalse(s.similar_video())

        FileFactory(filename="foo/bar.flv", location_type='cuit')
        self.assertTrue(s.similar_video())
