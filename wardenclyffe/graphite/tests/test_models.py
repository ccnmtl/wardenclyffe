from django.test import TestCase
import unittest
from wardenclyffe.graphite.models import operation_count_by_status
from wardenclyffe.graphite.models import operation_count_report
from wardenclyffe.graphite.models import generate_operation_count_report
from wardenclyffe.graphite.models import tahoe_stats
from wardenclyffe.graphite.models import minutes_video_stats
from wardenclyffe.graphite.models import minutes_video_report
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


class TestGenerateOperationCountReport(unittest.TestCase):
    def test_empty(self):
        result = generate_operation_count_report(
            {'failed': 0, 'complete': 0, 'submitted': 0, 'in progress': 0,
             'enqueued': 0})
        self.assertTrue("operations.failed 0 " in result)
        self.assertTrue("operations.total 0 " in result)
        self.assertTrue("operations.complete 0 " in result)
        self.assertTrue("operations.submitted 0 " in result)
        self.assertTrue("operations.inprogress 0 " in result)
        self.assertTrue("operations.enqueued 0 " in result)
        self.assertTrue(result.endswith("\n"))

    def test_populated(self):
        result = generate_operation_count_report(
            {'failed': 1, 'complete': 2, 'submitted': 3, 'in progress': 4,
             'enqueued': 5})
        self.assertTrue("operations.failed 1 " in result)
        self.assertTrue("operations.total 15 " in result)
        self.assertTrue("operations.complete 2 " in result)
        self.assertTrue("operations.submitted 3 " in result)
        self.assertTrue("operations.inprogress 4 " in result)
        self.assertTrue("operations.enqueued 5 " in result)
        self.assertTrue(result.endswith("\n"))


class TestOperationCountReport(TestCase):
    def test_empty(self):
        result = operation_count_report()
        self.assertTrue("operations.failed 0 " in result)
        self.assertTrue("operations.total 0 " in result)
        self.assertTrue("operations.complete 0 " in result)
        self.assertTrue("operations.submitted 0 " in result)
        self.assertTrue("operations.inprogress 0 " in result)
        self.assertTrue("operations.enqueued 0 " in result)
        self.assertTrue(result.endswith("\n"))

    def test_populated(self):
        OperationFactory(status="failed")
        result = operation_count_report()
        self.assertTrue("operations.failed 1 " in result)
        self.assertTrue("operations.total 1 " in result)
        self.assertTrue("operations.complete 0 " in result)
        self.assertTrue("operations.submitted 0 " in result)
        self.assertTrue("operations.inprogress 0 " in result)
        self.assertTrue("operations.enqueued 0 " in result)
        self.assertTrue(result.endswith("\n"))


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


class TestMinutesVideoReport(TestCase):
    def test_empty(self):
        result = minutes_video_report()
        self.assertTrue("minutes_video 0 " in result)

    def test_populated(self):
        f = FileFactory(location_type="none")
        f.set_metadata('ID_LENGTH', "300")
        result = minutes_video_report()
        self.assertTrue("minutes_video 5 " in result)
