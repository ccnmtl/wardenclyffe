from __future__ import unicode_literals

from django.test import TestCase
from wardenclyffe.drop.tests.factories import DropBucketFactory


class DropBucketTest(TestCase):
    def test_unicode(self):
        b = DropBucketFactory(name="the name")
        self.assertEqual(str(b), "the name")
