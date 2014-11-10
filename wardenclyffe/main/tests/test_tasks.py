from django.conf import settings
from django.test import TestCase
from wardenclyffe.main.tasks import (
    slow_operations, slow_operations_other_than_submitted,
    image_extract_command, avi_image_extract_command,
    fallback_image_extract_command, image_extract_command_for_file,
    audio_encode_command, parse_metadata)


class SlowOperationsTest(TestCase):
    def test_slow_operations_base(self):
        r = slow_operations()
        self.assertEqual(r.count(), 0)

    def test_slow_operations_other_than_submitted_base(self):
        r = slow_operations_other_than_submitted()
        self.assertEqual(r.count(), 0)


class ImageExtractCommandTest(TestCase):
    def test_image_extract_command(self):
        r = image_extract_command("foo", 5, "baz")
        self.assertEqual(r, ("%s -c 3 %s "
                             "-nosound -vo jpeg:outdir=foo -endpos "
                             "03:00:00 -frames 5 -sstep 10 'baz' "
                             "2>/dev/null" % (settings.IONICE_PATH,
                                              settings.MPLAYER_PATH)))

    def test_avi_image_extract_command(self):
        r = avi_image_extract_command("foo", 5, "baz")
        self.assertEqual(
            r, ("%s -c 3 %s "
                "-nosound -vo jpeg:outdir=foo -endpos "
                "03:00:00 -frames 5 -sstep 10 -correct-pts "
                "'baz' 2>/dev/null" % (
                    settings.IONICE_PATH,
                    settings.MPLAYER_PATH)))

    def test_fallback_image_extract_command(self):
        r = fallback_image_extract_command("foo", 5, "baz")
        self.assertEqual(
            r, ("%s -c 3 %s "
                "-nosound -vo jpeg:outdir=foo -endpos "
                "03:00:00 -frames 5 -vf framerate=250 "
                "'baz' 2>/dev/null" % (
                    settings.IONICE_PATH,
                    settings.MPLAYER_PATH)))

    def test_image_extract_command_for_file(self):
        r = image_extract_command_for_file("foo", 5, "baz")
        self.assertEqual(
            r, ("%s -c 3 %s "
                "-nosound -vo jpeg:outdir=foo -endpos "
                "03:00:00 -frames 5 -sstep 10 'baz' "
                "2>/dev/null" % (
                    settings.IONICE_PATH,
                    settings.MPLAYER_PATH)))
        r = image_extract_command_for_file("foo", 5, "baz.avi")
        self.assertEqual(
            r, ("%s -c 3 %s "
                "-nosound -vo jpeg:outdir=foo -endpos "
                "03:00:00 -frames 5 -sstep 10 -correct-pts "
                "'baz.avi' 2>/dev/null" % (
                    settings.IONICE_PATH, settings.MPLAYER_PATH)))


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
