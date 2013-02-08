from smoketest import SmokeTest
from django.conf import settings
import paramiko


class CUITSFTPTest(SmokeTest):
    def test_connectivity(self):
        """ this will be a good candidate for the @slow decorator
        once that is implemented """
        sftp_hostname = settings.SFTP_HOSTNAME
        sftp_path = settings.SFTP_PATH
        sftp_user = settings.SFTP_USER
        sftp_private_key_path = settings.SSH_PRIVATE_KEY_PATH
        mykey = paramiko.RSAKey.from_private_key_file(sftp_private_key_path)
        transport = paramiko.Transport((sftp_hostname, 22))
        transport.connect(username=sftp_user, pkey=mykey)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.chdir(sftp_path)
        self.assertTrue(len(sftp.listdir_attr()))
