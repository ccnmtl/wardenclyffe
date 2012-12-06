from django.test import TestCase
from wardenclyffe.util.mail import *


class BodyTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_slow_operations_body(self):
        num_operations = 1
        body = slow_operations_email_body(num_operations)
        assert "1 operation " in body

        num_operations = 2
        body = slow_operations_email_body(num_operations)
        assert "2 operations " in body
