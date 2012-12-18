from smoketest import SmokeTest
from wardenclyffe.cuit.views import list_all_cuit_files


class CUITSFTPTest(SmokeTest):
    def test_connectivity(self):
        """ this will be a good candidate for the @slow decorator
        once that is implemented """
        self.assertTrue(len(list_all_cuit_files()) > 0)
