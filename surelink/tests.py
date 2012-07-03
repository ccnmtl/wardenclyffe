from helpers import SureLink
from django.conf import settings
import unittest
THUMB_URL = "http://ccnmtl.columbia.edu/broadcast/posters/vidthumb_480x360.jpg"


class PublicFLVTestCase(unittest.TestCase):
    def setUp(self):
        self.surelink = SureLink("test/test_stream.flv",
                                 480, 360, "",
                                 THUMB_URL,
                                 "public", "", "v4",
                                 settings.SURELINK_PROTECTION_KEY)

    def testProtection(self):
        self.assertEquals(self.surelink.get_protection(),
                          "74464d1a6c82afe0f73ab5c59a2c5e25ab470857")

    def testBasicEmbed(self):
        self.assertEquals(
            self.surelink.basic_embed(),
            ("""<script type="text/javascript" """
             """src="http://ccnmtl.columbia.edu/stream/"""
             """jsembed?player=v4&file=test/test_stream.flv"""
             """&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/posters/"""
             """vidthumb_480x360.jpg&protection=74464d1a6c82afe0f"""
             """73ab5c59a2c5e25ab470857"></script>"""))

    def testIFrameEmbed(self):
        self.assertEquals(
            self.surelink.iframe_embed(),
            ("""<iframe width="480" height="384" src="https://surelink"""
             """.ccnmtl.columbia.edu/video/?player=v4&file=test/"""
             """test_stream.flv&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/posters/"""
             """vidthumb_480x360.jpg&protection=74464d1a6c82afe"""
             """0f73ab5c59a2c5e25ab470857" />"""))

    def testEdblogsEmbed(self):
        self.assertEquals(
            self.surelink.edblogs_embed(),
            ("""[ccnmtl_video src="http://ccnmtl.columbia.edu/stream/"""
             """jsembed?player=v4&file=test/test_stream.flv&width=480"""
             """&height=360&poster=http://ccnmtl.columbia.edu/broadcast/"""
             """posters/vidthumb_480x360.jpg&protection="""
             """74464d1a6c82afe0f73ab5c59a2c5e25ab470857"]"""))

    def testDrupalEmbed(self):
        self.assertEquals(
            self.surelink.drupal_embed(),
            ("""http://ccnmtl.columbia.edu/stream/flv/xdrupalx/OPTIONS/"""
             """test/test_stream.flv"""))

    def testMDPEmbed(self):
        self.assertEquals(
            self.surelink.mdp_embed(),
            ("""[flv]http://ccnmtl.columbia.edu/stream/flv/"""
             """74464d1a6c82afe0f73ab5c59a2c5e25ab470857/OPTIONS/"""
             """test/test_stream.flv[w]480[h]360[flv]"""))


class PublicFLVDefaultPosterTestCase(unittest.TestCase):
    def setUp(self):
        self.surelink = SureLink("test/test_stream.flv",
                                 480, 360, "",
                                 "default_custom_poster",
                                 "public", "", "v4",
                                 settings.SURELINK_PROTECTION_KEY)

    def testProtection(self):
        self.assertEquals(self.surelink.get_protection(),
                          "74464d1a6c82afe0f73ab5c59a2c5e25ab470857")

    def testBasicEmbed(self):
        self.assertEquals(
            self.surelink.basic_embed(),
            ("""<script type="text/javascript" src="http://ccnmtl."""
             """columbia.edu/stream/jsembed?player=v4&file=test/"""
             """test_stream.flv&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/test/"""
             """test_stream.jpg&protection=74464d1a6c82afe0f73"""
             """ab5c59a2c5e25ab470857"></script>"""))

    def testIFrameEmbed(self):
        self.assertEquals(
            self.surelink.iframe_embed(),
            ("""<iframe width="480" height="384" src="https://surelink."""
             """ccnmtl.columbia.edu/video/?player=v4&file=test/"""
             """test_stream.flv&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/test/"""
             """test_stream.jpg&protection=74464d1a6c82afe0f73ab5c59a2c"""
             """5e25ab470857" />"""))

    def testEdblogsEmbed(self):
        self.assertEquals(
            self.surelink.edblogs_embed(),
            ("""[ccnmtl_video src="http://ccnmtl.columbia.edu/stream/"""
             """jsembed?player=v4&file=test/test_stream.flv&width=480"""
             """&height=360&poster=http://ccnmtl.columbia.edu/"""
             """broadcast/test/test_stream.jpg&protection="""
             """74464d1a6c82afe0f73ab5c59a2c5e25ab470857"]"""))

    def testDrupalEmbed(self):
        self.assertEquals(
            self.surelink.drupal_embed(),
            ("""http://ccnmtl.columbia.edu/stream/flv/xdrupalx/"""
             """OPTIONS/test/test_stream.flv"""))

    def testMDPEmbed(self):
        self.assertEquals(
            self.surelink.mdp_embed(),
            ("""[flv]http://ccnmtl.columbia.edu/stream/flv/"""
             """74464d1a6c82afe0f73ab5c59a2c5e25ab470857"""
             """/OPTIONS/test/test_stream.flv[w]480[h]360[flv]"""))


class PublicMP4TestCase(unittest.TestCase):
    def setUp(self):
        self.surelink = SureLink("test/test_clip.mp4",
                                 480, 360, "",
                                 THUMB_URL,
                                 "public-mp4-download", "", "v4",
                                 settings.SURELINK_PROTECTION_KEY)

    def testProtection(self):
        self.assertEquals(self.surelink.get_protection(),
                          "d81e0d43fbccf40dbcb6d695268069dd14c21536")

    def testBasicEmbed(self):
        self.assertEquals(
            self.surelink.basic_embed(),
            ("""<script type="text/javascript" src="http://ccnmtl."""
             """columbia.edu/stream/jsembed?player=download_mp4_v3&"""
             """file=test/test_clip.mp4&width=480&height=360&"""
             """poster=http://ccnmtl.columbia.edu/broadcast/posters/"""
             """vidthumb_480x360.jpg&protection=5916f0fe8ab583c47adf39f"""
             """be3a80086b7122994"></script>"""))

    def testIFrameEmbed(self):
        self.assertEquals(
            self.surelink.iframe_embed(),
            ("""<iframe width="480" height="384" src="https://surelink."""
             """ccnmtl.columbia.edu/video/?player=download_mp4_v3&"""
             """file=test/test_clip.mp4&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/posters/"""
             """vidthumb_480x360.jpg&protection=5916f0fe8ab583c47adf3"""
             """9fbe3a80086b7122994" />"""))

    def testEdblogsEmbed(self):
        self.assertEquals(
            self.surelink.edblogs_embed(),
            ("""[ccnmtl_video src="http://ccnmtl.columbia.edu/stream/"""
             """jsembed?player=download_mp4_v3&file=test/test_clip.mp4"""
             """&width=480&height=360&poster=http://ccnmtl.columbia.edu/"""
             """broadcast/posters/vidthumb_480x360.jpg&protection="""
             """5916f0fe8ab583c47adf39fbe3a80086b7122994"]"""))

    def testDrupalEmbed(self):
        self.assertEquals(
            self.surelink.drupal_embed(),
            ("""http://ccnmtl.columbia.edu/stream/flv/xdrupalx/"""
             """OPTIONS/test/test_clip.mp4"""))

    def testMDPEmbed(self):
        self.assertEquals(
            self.surelink.mdp_embed(),
            ("""[mp4]http://ccnmtl.columbia.edu/broadcast/test/"""
             """test_clip.mp4[w]480[h]360[mp4]"""))


class WindMP4TestCase(unittest.TestCase):
    def setUp(self):
        self.surelink = SureLink("test/test_clip.mp4",
                                 480, 360, "",
                                 THUMB_URL,
                                 "protected", "wind", "v4",
                                 settings.SURELINK_PROTECTION_KEY)

    def testProtection(self):
        self.assertEquals(self.surelink.get_protection(),
                          "18e74f6f8998963c72154f969f11d8f3ad91345d")

    def testBasicEmbed(self):
        self.assertEquals(
            self.surelink.basic_embed(),
            ("""<script type="text/javascript" src="http://ccnmtl."""
             """columbia.edu/stream/jsembed?player=v4&file=test/test"""
             "_clip.mp4&width=480&height=360&poster=http://"""
             """ccnmtl.columbia.edu/broadcast/posters/vidthumb_"""
             """480x360.jpg&authtype=wind"></script>"""))

    def testIFrameEmbed(self):
        self.assertEquals(
            self.surelink.iframe_embed(),
            ("""<iframe width="480" height="384" src="https://surelink."""
             """ccnmtl.columbia.edu/video/?player=v4&file="""
             """test/test_clip.mp4&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/posters/"""
             """vidthumb_480x360.jpg&authtype=wind" />"""))

    def testEdblogsEmbed(self):
        self.assertEquals(
            self.surelink.edblogs_embed(),
            ("""[ccnmtl_video src="http://ccnmtl.columbia.edu/stream/"""
             """jsembed?player=v4&file=test/test_clip.mp4&width=480&"""
             """height=360&poster=http://ccnmtl.columbia.edu/broadcast/"""
             """posters/vidthumb_480x360.jpg&authtype=wind"]"""))

    def testDrupalEmbed(self):
        self.assertEquals(
            self.surelink.drupal_embed(),
            ("""http://ccnmtl.columbia.edu/stream/flv/xdrupalx/OPTIONS/"""
             """test/test_clip.mp4"""))

    def testMDPEmbed(self):
        self.assertEquals(
            self.surelink.mdp_embed(),
            ("""[flv]http://ccnmtl.columbia.edu/stream/flv/"""
             """5916f0fe8ab583c47adf39fbe3a80086b7122994/OPTIONS/"""
             """test/test_clip.mp4[w]480[h]360[flv]"""))
