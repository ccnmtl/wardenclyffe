from helpers import SureLink
from django.conf import settings
import unittest
THUMB_URL = "http://ccnmtl.columbia.edu/broadcast/posters/vidthumb_480x360.jpg"


class PublicFLVTestCase(unittest.TestCase):
    def setUp(self):
        self.surelink = SureLink("test/test_stream.flv",
                                 480, 360, "",
                                 THUMB_URL,
                                 "public", "",
                                 settings.SURELINK_PROTECTION_KEY)

    def testProtection(self):
        self.assertEquals(self.surelink.get_protection(),
                          "9fc95427445a4684eef0ecb64ba6bf8f9bfcfd6c")

    def testBasicEmbed(self):
        self.assertEquals(
            self.surelink.basic_embed(),
            ("""<script type="text/javascript" """
             """src="http://ccnmtl.columbia.edu/stream/"""
             """jsembed?player=v4&file=test/test_stream.flv"""
             """&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/posters/"""
             """vidthumb_480x360.jpg&protection=9fc95427445a4684eef0ecb64ba6"""
             """bf8f9bfcfd6c"></script>"""))

    def testIFrameEmbed(self):
        self.assertEquals(
            self.surelink.iframe_embed(),
            ("""<iframe width="480" height="384" src="https://surelink"""
             """.ccnmtl.columbia.edu/video/?player=v4&file=test/"""
             """test_stream.flv&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/posters/"""
             """vidthumb_480x360.jpg&protection=9fc95427445a4684eef0ecb6"""
             """4ba6bf8f9bfcfd6c" />"""))

    def testEdblogsEmbed(self):
        self.assertEquals(
            self.surelink.edblogs_embed(),
            ("""[ccnmtl_video src="http://ccnmtl.columbia.edu/stream/"""
             """jsembed?player=v4&file=test/test_stream.flv&width=480"""
             """&height=360&poster=http://ccnmtl.columbia.edu/broadcast/"""
             """posters/vidthumb_480x360.jpg&protection="""
             """9fc95427445a4684eef0ecb64ba6bf8f9bfcfd6c"]"""))

    def testDrupalEmbed(self):
        self.assertEquals(
            self.surelink.drupal_embed(),
            ("""http://ccnmtl.columbia.edu/stream/flv/xdrupalx/OPTIONS/"""
             """test/test_stream.flv"""))

    def testMDPEmbed(self):
        self.assertEquals(
            self.surelink.mdp_embed(),
            ("""[flv]http://ccnmtl.columbia.edu/stream/flv/"""
             """9fc95427445a4684eef0ecb64ba6bf8f9bfcfd6c/OPTIONS/"""
             """test/test_stream.flv[w]480[h]360[flv]"""))


class PublicFLVDefaultPosterTestCase(unittest.TestCase):
    def setUp(self):
        self.surelink = SureLink("test/test_stream.flv",
                                 480, 360, "",
                                 "default_custom_poster",
                                 "public", "",
                                 settings.SURELINK_PROTECTION_KEY)

    def testGroup(self):
        self.assertEquals(self.surelink.group(), 'public')

    def testProtection(self):
        self.assertEquals(self.surelink.get_protection(),
                          "9fc95427445a4684eef0ecb64ba6bf8f9bfcfd6c")

    def testBasicEmbed(self):
        self.assertEquals(
            self.surelink.basic_embed(),
            ("""<script type="text/javascript" src="http://ccnmtl."""
             """columbia.edu/stream/jsembed?player=v4&file=test/"""
             """test_stream.flv&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/test/"""
             """test_stream.jpg&protection=9fc95427445a4684eef0ecb6"""
             """4ba6bf8f9bfcfd6c"></script>"""))

    def testIFrameEmbed(self):
        self.assertEquals(
            self.surelink.iframe_embed(),
            ("""<iframe width="480" height="384" src="https://surelink."""
             """ccnmtl.columbia.edu/video/?player=v4&file=test/"""
             """test_stream.flv&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/test/"""
             """test_stream.jpg&protection=9fc95427445a4684eef0ecb64ba6bf8f"""
             """9bfcfd6c" />"""))

    def testEdblogsEmbed(self):
        self.assertEquals(
            self.surelink.edblogs_embed(),
            ("""[ccnmtl_video src="http://ccnmtl.columbia.edu/stream/"""
             """jsembed?player=v4&file=test/test_stream.flv&width=480"""
             """&height=360&poster=http://ccnmtl.columbia.edu/"""
             """broadcast/test/test_stream.jpg&protection="""
             """9fc95427445a4684eef0ecb64ba6bf8f9bfcfd6c"]"""))

    def testDrupalEmbed(self):
        self.assertEquals(
            self.surelink.drupal_embed(),
            ("""http://ccnmtl.columbia.edu/stream/flv/xdrupalx/"""
             """OPTIONS/test/test_stream.flv"""))

    def testMDPEmbed(self):
        self.assertEquals(
            self.surelink.mdp_embed(),
            ("""[flv]http://ccnmtl.columbia.edu/stream/flv/"""
             """9fc95427445a4684eef0ecb64ba6bf8f9bfcfd6c"""
             """/OPTIONS/test/test_stream.flv[w]480[h]360[flv]"""))


class PublicMP4TestCase(unittest.TestCase):
    def setUp(self):
        self.surelink = SureLink("test/test_clip.mp4",
                                 480, 360, "",
                                 THUMB_URL,
                                 "public-mp4-download", "",
                                 settings.SURELINK_PROTECTION_KEY)

    def testProtection(self):
        self.assertEquals(self.surelink.get_protection(),
                          "acfc85127771e4c63d9eab200520772d0e08bf7c")

    def testBasicEmbed(self):
        self.assertEquals(
            self.surelink.basic_embed(),
            ("""<script type="text/javascript" src="http://ccnmtl."""
             """columbia.edu/stream/jsembed?player=download_mp4_v3&"""
             """file=test/test_clip.mp4&width=480&height=360&"""
             """poster=http://ccnmtl.columbia.edu/broadcast/posters/"""
             """vidthumb_480x360.jpg&protection=e4e546e9398cacbe6b3e29f"""
             """1ccd9d286fd5017ff"></script>"""))

    def testIFrameEmbed(self):
        self.assertEquals(
            self.surelink.iframe_embed(),
            ("""<iframe width="480" height="384" src="https://surelink."""
             """ccnmtl.columbia.edu/video/?player=download_mp4_v3&"""
             """file=test/test_clip.mp4&width=480&height=360&poster="""
             """http://ccnmtl.columbia.edu/broadcast/posters/"""
             """vidthumb_480x360.jpg&protection=e4e546e9398cacbe"""
             """6b3e29f1ccd9d286fd5017ff" />"""))

    def testEdblogsEmbed(self):
        self.assertEquals(
            self.surelink.edblogs_embed(),
            ("""[ccnmtl_video src="http://ccnmtl.columbia.edu/stream/"""
             """jsembed?player=download_mp4_v3&file=test/test_clip.mp4"""
             """&width=480&height=360&poster=http://ccnmtl.columbia.edu/"""
             """broadcast/posters/vidthumb_480x360.jpg&protection="""
             """e4e546e9398cacbe6b3e29f1ccd9d286fd5017ff"]"""))

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
                                 "protected", "wind",
                                 settings.SURELINK_PROTECTION_KEY)

    def testGroup(self):
        self.assertEquals(self.surelink.group(), 'protected')

    def testProtection(self):
        self.assertEquals(self.surelink.get_protection(),
                          "d9ab631d356793e9d1d56db7caf4f0f13ef3928c")

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
             """e4e546e9398cacbe6b3e29f1ccd9d286fd5017ff/OPTIONS/"""
             """test/test_clip.mp4[w]480[h]360[flv]"""))
