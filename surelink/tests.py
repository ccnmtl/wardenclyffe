from helpers import SureLink
from django.conf import settings
import unittest

class SurelinkTestCase(unittest.TestCase):
    def setUp(self):
        self.surelink = SureLink("test/test_stream.flv",
                                 480,360,"",
                                 "http://ccnmtl.columbia.edu/broadcast/posters/vidthumb_480x360.jpg",
                                 "public","","v4",
                                 settings.SURELINK_PROTECTION_KEY)

    def testProtection(self):
        self.assertEquals(self.surelink.get_protection(),"74464d1a6c82afe0f73ab5c59a2c5e25ab470857")

    def testBasicEmbed(self):
        self.assertEquals(self.surelink.basic_embed(),
                          """<script type="text/javascript" src="http://ccnmtl.columbia.edu/stream/jsembed?player=v4&file=test/test_stream.flv&width=480&height=360&poster=http://ccnmtl.columbia.edu/broadcast/posters/vidthumb_480x360.jpg&protection=74464d1a6c82afe0f73ab5c59a2c5e25ab470857"></script>""")

    def testIFrameEmbed(self):
        self.assertEquals(self.surelink.iframe_embed(),
                          """<iframe width="480" height="384" src="https://surelink.ccnmtl.columbia.edu/video/?player=v4&file=test/test_stream.flv&width=480&height=360&poster=http://ccnmtl.columbia.edu/broadcast/posters/vidthumb_480x360.jpg&protection=74464d1a6c82afe0f73ab5c59a2c5e25ab470857" />""")

    def testEdblogsEmbed(self):
        self.assertEquals(self.surelink.edblogs_embed(),
                          """[ccnmtl_video src="http://ccnmtl.columbia.edu/stream/jsembed?player=v4&file=test/test_stream.flv&width=480&height=360&poster=http://ccnmtl.columbia.edu/broadcast/posters/vidthumb_480x360.jpg&protection=74464d1a6c82afe0f73ab5c59a2c5e25ab470857"]""")
        
    def testDrupalEmbed(self):
        self.assertEquals(self.surelink.drupal_embed(),
                          """http://ccnmtl.columbia.edu/stream/flv/xdrupalx/OPTIONS/test/test_stream.flv""")

    def testMDPEmbed(self):
        self.assertEquals(self.surelink.mdp_embed(),
                          """[flv]http://ccnmtl.columbia.edu/stream/flv/74464d1a6c82afe0f73ab5c59a2c5e25ab470857/OPTIONS/test/test_stream.flv[w]480[h]360[flv]""")
