import unittest
from wardenclyffe.graphite.models import operation_count_by_status
from wardenclyffe.main.tests.factories import OperationFactory


class TestCount(unittest.TestCase):
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
