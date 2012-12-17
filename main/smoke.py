from smoketest import SmokeTest
from models import Collection
from django.conf import settings


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

    def test_vital_settings(self):
        self.assertIsNotNone(settings.VITAL_PCP_WORKFLOW)
        self.assertIsNotNone(settings.VITAL_COLLECTION_ID)

    def test_mediathread_settings(self):
        self.assertIsNotNone(settings.MEDIATHREAD_BASE)
        self.assertIsNotNone(settings.MEDIATHREAD_SECRET)
        self.assertIsNotNone(settings.MEDIATHREAD_POST_URL)
        self.assertIsNotNone(settings.MEDIATHREAD_PCP_WORKFLOW)
        self.assertIsNotNone(settings.MEDIATHREAD_CREDENTIALS)
        self.assertIsNotNone(settings.MEDIATHREAD_COLLECTION_ID)

    def test_youtube_settings(self):
        self.assertIsNotNone(settings.YOUTUBE_EMAIL)
        self.assertIsNotNone(settings.YOUTUBE_PASSWORD)
        self.assertIsNotNone(settings.YOUTUBE_SOURCE)
        self.assertIsNotNone(settings.YOUTUBE_DEVELOPER_KEY)
        self.assertIsNotNone(settings.YOUTUBE_CLIENT_ID)

    def test_sshsftp_settings(self):
        pass

    def test_rabbitmq_settings(self):
        pass


class RabbitMQTest(SmokeTest):
    """ make sure we can connect to the RabbitMQ server """
    def test_rabbitmq_connection(self):
        pass


class KinoTest(SmokeTest):
    """ make sure the Kino server is up and we can connect
    with the username/password we have """
    def test_kino_connection(self):
        pass


class YoutubeTest(SmokeTest):
    """ make sure our youtube account works """
    def test_youtube_connection(self):
        pass


class CUITSSHTest(SmokeTest):
    """ make sure we have key-based ssh access to the CUIT servers """
    def test_cuit_ssh(self):
        pass


class WatchDirTest(SmokeTest):
    """ make sure the watch directory exists and has the right
    permissions"""
    def test_watchdir(self):
        pass


class TahoeTest(SmokeTest):
    """ make sure we can connect to Tahoe and that the
    base CAP looks legit"""
    def test_tahoe(self):
        pass
