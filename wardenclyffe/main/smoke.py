from angeldust import PCP
from smoketest import SmokeTest
from models import Collection
from django.conf import settings
import os.path
import requests


class DBConnectivityTest(SmokeTest):
    """ damn well better be able to connect to the database
    and there better be stuff in it """
    def test_retrieve(self):
        cnt = Collection.objects.all().count()
        self.assertTrue(cnt > 0)


class ExpectedSettings(SmokeTest):
    """ just make sure that the settings that we expect
    are even set to non-null values."""
    def test_tahoe_settings(self):
        self.assertIsNotNone(settings.TAHOE_BASE)
        self.assertIsNotNone(settings.TAHOE_DOWNLOAD_BASE)

    def test_dir_settings(self):
        self.assertIsNotNone(settings.TMP_DIR)
        self.assertIsNotNone(settings.WATCH_DIRECTORY)

    def test_pcp_settings(self):
        self.assertIsNotNone(settings.PCP_BASE_URL)
        self.assertIsNotNone(settings.PCP_USERNAME)
        self.assertIsNotNone(settings.PCP_PASSWORD)
        self.assertIsNotNone(settings.PCP_WORKFLOW)

    def test_aws_settings(self):
        self.assertIsNotNone(settings.AWS_ACCESS_KEY)
        self.assertIsNotNone(settings.AWS_SECRET_KEY)
        self.assertIsNotNone(settings.AWS_S3_UPLOAD_BUCKET)

    def test_mediathread_settings(self):
        self.assertIsNotNone(settings.MEDIATHREAD_BASE)
        self.assertIsNotNone(settings.MEDIATHREAD_SECRET)
        self.assertIsNotNone(settings.MEDIATHREAD_POST_URL)
        self.assertIsNotNone(settings.MEDIATHREAD_PCP_WORKFLOW)
        self.assertIsNotNone(settings.MEDIATHREAD_COLLECTION_ID)
        self.assertIsNotNone(settings.MEDIATHREAD_AUDIO_PCP_WORKFLOW)
        self.assertIsNotNone(settings.MEDIATHREAD_AUDIO_PCP_WORKFLOW2)

    def test_youtube_settings(self):
        self.assertIsNotNone(settings.YOUTUBE_EMAIL)
        self.assertIsNotNone(settings.YOUTUBE_PASSWORD)
        self.assertIsNotNone(settings.YOUTUBE_SOURCE)
        self.assertIsNotNone(settings.YOUTUBE_DEVELOPER_KEY)
        self.assertIsNotNone(settings.YOUTUBE_CLIENT_ID)

    def test_sshsftp_settings(self):
        self.assertIsNotNone(settings.SFTP_HOSTNAME)
        self.assertIsNotNone(settings.SFTP_USER)
        self.assertIsNotNone(settings.SSH_PRIVATE_KEY_PATH)
        self.assertIsNotNone(settings.CREDENTIALS)

    def test_rabbitmq_settings(self):
        self.assertIsNotNone(settings.BROKER_URL)

    def test_sentry_settings(self):
        if not settings.DEBUG:
            self.assertIsNotNone(settings.RAVEN_CONFIG)

    def test_surelink_settings(self):
        self.assertIsNotNone(settings.SURELINK_PROTECTION_KEY)


class RabbitMQTest(SmokeTest):
    """ make sure we can connect to the RabbitMQ server """
    def test_rabbitmq_connection(self):
        pass


class KinoTest(SmokeTest):
    """ make sure the Kino server is up and we can connect
    with the username/password we have """
    def test_kino_connection(self):
        workflows = []
        try:
            p = PCP(settings.PCP_BASE_URL,
                    settings.PCP_USERNAME,
                    settings.PCP_PASSWORD)
            workflows = p.workflows()
        except:
            workflows = []
        self.assertTrue(len(workflows) > 0)


class WatchDirTest(SmokeTest):
    """ make sure the watch directory exists"""
    def test_watchdir(self):
        self.assertTrue(os.path.exists(settings.WATCH_DIRECTORY))
        self.assertTrue(os.path.isdir(settings.WATCH_DIRECTORY))


class TahoeTest(SmokeTest):
    """ make sure we can connect to Tahoe and that the
    base CAP looks legit"""
    def test_tahoe(self):
        if not settings.STAGING:
            response = requests.get(settings.TAHOE_BASE)
            self.assertEqual(response.status_code, 200)
