from django.test import TestCase
from wardenclyffe.graphite.models import operation_count_by_status
from wardenclyffe.graphite.models import tahoe_stats
from wardenclyffe.graphite.models import minutes_video_stats
from wardenclyffe.main.tests.factories import OperationFactory, FileFactory


class TestCount(TestCase):
    def test_empty(self):
        self.assertEqual(
            operation_count_by_status(),
            {'failed': 0, 'complete': 0, 'submitted': 0, 'in progress': 0,
             'enqueued': 0})

    def test_populated(self):
        OperationFactory(status="failed")
        self.assertEqual(operation_count_by_status()["failed"], 1)
        self.assertEqual(operation_count_by_status()["enqueued"], 0)
        self.assertEqual(operation_count_by_status()["submitted"], 0)
        self.assertEqual(operation_count_by_status()["complete"], 0)


class TestTahoeStats(TestCase):
    def test_empty(self):
        result = tahoe_stats()
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], 0)
        # unfortunately, we'll need to mock out tahoe
        # to test this any better


class TestMinutesVideoStats(TestCase):
    def test_empty(self):
        result = minutes_video_stats()
        self.assertEqual(result, 0.0)

    def test_populated(self):
        f = FileFactory(location_type="none")
        f.set_metadata('ID_LENGTH', "300")
        result = minutes_video_stats()
        self.assertEqual(result, 5.0)
