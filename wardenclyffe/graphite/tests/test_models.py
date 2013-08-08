import unittest
from wardenclyffe.graphite.models import operation_count_by_status


class TestCount(unittest.TestCase):
    def test_base(self):
        self.assertEqual(operation_count_by_status(), dict())
