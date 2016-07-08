import os.path
import unittest

from ..snsparser import SNSMessage, SNSMessageError


def sample_message():
    f = open(os.path.join(os.path.dirname(__file__), "sample_message.txt"))
    return f.read()


class TestSNSMessage(unittest.TestCase):
    def setUp(self):
        self.m = sample_message()
        self.s = SNSMessage(self.m)

    def test_init(self):
        self.assertTrue(self.s is not None)

    def test_message_type(self):
        self.assertEqual(self.s.message_type(), "Notification")

    def test_subject(self):
        self.assertEqual(self.s.subject(), "Amazon S3 Notification")

    def test_topic(self):
        self.assertEqual(
            self.s.topic(),
            "arn:aws:sns:us-east-1:051882422638:ctl-wardenclyffe-dropbox")

    def test_records(self):
        self.assertEqual(len(self.s.records()), 1)


class TestInvalidMessage(unittest.TestCase):
    def test_invalid_json(self):
        """ it should raise an error if it's not given valid json """
        with self.assertRaises(SNSMessageError):
            SNSMessage("not valid json")

    def test_not_notification(self):
        """ valid JSON, but not an SNS notification """
        with self.assertRaises(SNSMessageError):
            SNSMessage("{\"key\": \"value\"}")


class TestMessage(unittest.TestCase):
    def setUp(self):
        m = sample_message()
        self.s = SNSMessage(m)
        self.r = self.s.records()[0]

    def test_event_source(self):
        self.assertEqual(self.r.event_source(), 'aws:s3')

    def test_event_name(self):
        self.assertEqual(self.r.event_name(), 'ObjectCreated:Put')

    def test_s3_bucket_name(self):
        self.assertEqual(self.r.s3_bucket_name(),
                         'ctl-wardenclyffe-dropbox-test')

    def test_s3_bucket_arn(self):
        self.assertEqual(self.r.s3_bucket_arn(),
                         'arn:aws:s3:::ctl-wardenclyffe-dropbox-test')

    def test_s3_bucket_key(self):
        self.assertEqual(self.r.s3_bucket_key(), '929.jpg')
