from .factories import DropBucketFactory
from django.test import TestCase


class DropBucketTest(TestCase):
    def test_unicode(self):
        b = DropBucketFactory(name="the name")
        self.assertEqual(str(b), "the name")
