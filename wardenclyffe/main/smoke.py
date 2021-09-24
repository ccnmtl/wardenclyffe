import os.path
import subprocess  # nosec

from django.conf import settings
from smoketest import SmokeTest

from wardenclyffe.main.models import Collection


class DBConnectivityTest(SmokeTest):
    """ damn well better be able to connect to the database
    and there better be stuff in it """
    def test_retrieve(self):
        cnt = Collection.objects.all().count()
        self.assertTrue(cnt > 0)


class ExpectedSettings(SmokeTest):
    """ just make sure that the settings that we expect
    are even set to non-null values."""
    def test_dir_settings(self):
        self.assertIsNotNone(settings.TMP_DIR)
        self.assertIsNotNone(settings.WATCH_DIRECTORY)

    def test_aws_settings(self):
        self.assertIsNotNone(settings.AWS_ACCESS_KEY)
        self.assertIsNotNone(settings.AWS_SECRET_KEY)
        self.assertIsNotNone(settings.AWS_S3_UPLOAD_BUCKET)

    def test_mediathread_settings(self):
        self.assertIsNotNone(settings.MEDIATHREAD_BASE)
        self.assertIsNotNone(settings.MEDIATHREAD_SECRET)
        self.assertIsNotNone(settings.MEDIATHREAD_POST_URL)
        self.assertIsNotNone(settings.MEDIATHREAD_COLLECTION_ID)

    def test_sshsftp_settings(self):
        self.assertIsNotNone(settings.SFTP_HOSTNAME)
        self.assertIsNotNone(settings.SFTP_USER)
        self.assertIsNotNone(settings.SSH_PRIVATE_KEY_PATH)
        self.assertIsNotNone(settings.CREDENTIALS)

    def test_rabbitmq_settings(self):
        self.assertIsNotNone(settings.CELERY_BROKER_URL)

    def test_sentry_settings(self):
        if not settings.DEBUG:
            self.assertIsNotNone(settings.RAVEN_CONFIG)

    def test_executables(self):
        self.assertIsNotNone(settings.IONICE_PATH)
        self.assertIsNotNone(settings.MPLAYER_PATH)
        self.assertTrue(os.path.exists(settings.IONICE_PATH))
        self.assertTrue(os.path.exists(settings.MPLAYER_PATH))
        self.assertTrue(os.path.isfile(settings.IONICE_PATH))
        self.assertTrue(os.path.isfile(settings.MPLAYER_PATH))


class RabbitMQTest(SmokeTest):
    """ make sure we can connect to the RabbitMQ server """
    def test_rabbitmq_connection(self):
        pass


class WatchDirTest(SmokeTest):
    """ make sure the watch directory exists"""
    def test_watchdir(self):
        self.assertTrue(os.path.exists(settings.WATCH_DIRECTORY))
        self.assertTrue(os.path.isdir(settings.WATCH_DIRECTORY))


class FFMPEGTest(SmokeTest):
    def test_existence(self):
        self.assertTrue(os.path.exists(settings.FFMPEG_PATH))
        self.assertTrue(os.path.isfile(settings.FFMPEG_PATH))

    def test_notavconv(self):
        """ the audio conversion step relies on the ffmpeg
        binary being the *real* ffmpeg, not avconv's
        "compatible" version.

        We test by running 'ffmpeg -version' and looking at the output.

        avconv's output will contain the string:

            Copyright (c) 2000-2014 the Libav developers

        while ffmpeg's has either:

            Copyright (c) 2000-2015 the FFmpeg developers

        (on 2.6+) or no copyright string on older versions.
        """
        output = subprocess.Popen(  # nosec
            [settings.FFMPEG_PATH, "-version"],
            stdout=subprocess.PIPE).communicate()[0]
        self.assertFalse(b"the Libav developers" in output)
