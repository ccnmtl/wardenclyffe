from django.test import TestCase
from wardenclyffe.mediathread.tasks import mediathread_submit_params
from wardenclyffe.main.tests.factories import (
    VideoFactory, UserFactory, CUITFLVFileFactory)


class TestMediathreadSubmitParams(TestCase):
    def test_non_mediathread_video(self):
        """
        test with a video that doesn't have a proper
        h264_secure_stream_url.

        At least we can check the basic parameter construction
        """
        v = VideoFactory()
        u = UserFactory()
        p = mediathread_submit_params(
            v, "a course id", u.username,
            "a mediathread secret",
            False, 100, 200
        )
        self.assertEqual(p['set_course'], "a course id")
        self.assertTrue('thumb' in p)
        self.assertTrue('mp4_audio' not in p)
        self.assertTrue('flv_pseudo' not in p)

    def test_flv(self):
        f = CUITFLVFileFactory()
        v = f.video
        u = UserFactory()
        p = mediathread_submit_params(
            v, "a course id", u.username,
            "a mediathread secret",
            False, 100, 200
        )
        self.assertTrue('mp4_audio' not in p)
        self.assertTrue('mp4_pseudo' not in p)
        self.assertTrue('flv_pseudo' in p)
        self.assertEqual(p['flv_pseudo-metadata'], 'w100h200')
