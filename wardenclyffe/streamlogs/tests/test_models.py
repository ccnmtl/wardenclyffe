from django.test import TestCase
from .factories import StreamLogFactory


class StreamLogTest(TestCase):
    def test_create(self):
        f = StreamLogFactory()
        self.assertIsNotNone(f)
