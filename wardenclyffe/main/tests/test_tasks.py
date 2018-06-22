from __future__ import unicode_literals

from django.conf import settings
from django.test import TestCase
from wardenclyffe.main.tasks import (
    slow_operations, slow_operations_other_than_submitted,
    audio_encode_command, parse_metadata, exp_backoff)


class SlowOperationsTest(TestCase):
    def test_slow_operations_base(self):
        r = slow_operations()
        self.assertEqual(r.count(), 0)

    def test_slow_operations_other_than_submitted_base(self):
        r = slow_operations_other_than_submitted()
        self.assertEqual(r.count(), 0)


class AudioEncodeCommandTest(TestCase):
    def test_basics(self):
        r = audio_encode_command("foo.jpg", "bar.mp3", "baz.mp4")
        self.assertEqual(
            r,
            (
                "%s -loop 1 -i foo.jpg -i bar.mp3 -c:v "
                "libx264 -c:a aac -strict experimental "
                "-b:a 192k -shortest baz.mp4" % settings.FFMPEG_PATH))


class MetaDataParseTest(TestCase):
    def test_basics(self):
        r = list(parse_metadata("foo=bar"))
        self.assertEqual(r, [('foo', 'bar')])

    def test_line_without_equals(self):
        r = list(parse_metadata("bar"))
        self.assertEqual(r, [])

    def test_invalid_line(self):
        r = list(parse_metadata("bar=bar=bar"))
        self.assertEqual(r, [])


class TestExpBackoff(TestCase):
    def test_basics(self):
        cases = [
            (0, 1, 2),
            (1, 2, 3),
            (2, 4, 5),
            (3, 8, 9),
            (4, 16, 18),
            (5, 32, 35),
            (10, 1024, 1200),
        ]
        for retries, expected_min, expected_max in cases:
            r = exp_backoff(retries)
            self.assertTrue(r >= expected_min)
            self.assertTrue(r <= expected_max)
