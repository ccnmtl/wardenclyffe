import os.path

from django.conf import settings
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from smoketest import SmokeTest

from .models import Credentials


class YoutubeTest(SmokeTest):
    def check_settings(self):
        """ there are variables that need to be set """
        self.assertIsNotNone(settings.YOUTUBE_CLIENT_SECRETS_FILE)
        self.assertIsNotNone(settings.OAUTH_STORAGE_PATH)

    def check_settings_files(self):
        """ and make sure those files actually exist """
        self.assertTrue(os.path.exists(settings.YOUTUBE_CLIENT_SECRETS_FILE))
        self.assertTrue(os.path.exists(settings.OAUTH_STORAGE_PATH))

    """ make sure our youtube account works """
    def test_youtube_connection(self):
        storage = DjangoORMStorage(
            Credentials, 'email', settings.PRIMARY_YOUTUBE_ACCOUNT,
            'credential')
        credential = storage.get()
        self.assertIsNotNone(credential)
        self.assertFalse(credential.invalid)
