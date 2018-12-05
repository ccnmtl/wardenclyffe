from __future__ import unicode_literals

from django.conf import settings
from django.test import TestCase
from wardenclyffe.main.tests.factories import FileFactory
from .factories import StreamLogFactory


class StreamLogTest(TestCase):
    def test_create(self):
        f = StreamLogFactory()
        self.assertIsNotNone(f)

    def test_full_filename(self):
        f = StreamLogFactory(filename='broadcast/foo/bar.flv')
        self.assertEqual(
            f.full_filename(),
            settings.CUNIX_BROADCAST_DIRECTORY + "foo/bar.flv")

    def test_video_no_match(self):
        f = StreamLogFactory()
        self.assertIsNone(f.video())

    def test_video_positive_match(self):
        s = StreamLogFactory(filename="broadcast/foo/bar.flv")
        f = FileFactory(
            filename=settings.CUNIX_BROADCAST_DIRECTORY + "foo/bar.flv",
            location_type='cuit')
        self.assertEqual(s.video(), f.video)
