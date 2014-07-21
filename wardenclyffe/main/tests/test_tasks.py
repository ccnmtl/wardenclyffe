from django.conf import settings
from django.test import TestCase
from wardenclyffe.main.tasks import slow_operations
from wardenclyffe.main.tasks import slow_operations_other_than_submitted
from wardenclyffe.main.tasks import image_extract_command
from wardenclyffe.main.tasks import avi_image_extract_command
from wardenclyffe.main.tasks import fallback_image_extract_command
from wardenclyffe.main.tasks import image_extract_command_for_file


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
