"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from wardenclyffe.main.models import Series, Video, File
import uuid

class CUITFileTest(TestCase):
    def setUp(self):
        self.series = Series.objects.create(title = "test series",
                                            uuid = uuid.uuid4())
        self.video = Video.objects.create(series = self.series,
                                          title = "test video",
                                          uuid = uuid.uuid4())
        self.file = File.objects.create(video=self.video,
                                        label = "CUIT File",
                                        location_type = "cuit",
                                        filename = "/www/data/ccnmtl/broadcast/secure/courses/56d27944-4131-11e1-8164-0017f20ea192-Mediathread_video_uploaded_by_mlp55.flv",
                                        )

    def test_is_cuit(self):
        assert self.file.is_cuit()

    def test_surelinkable(self):
        assert self.file.surelinkable()

    def test_tahoe_download_url(self):
        assert self.video.tahoe_file() is None
        assert self.video.cap() is None
        assert self.file.tahoe_download_url() is None

    def test_mediathread_url(self):
        assert self.video.mediathread_url() == "http://ccnmtl.columbia.edu/stream/flv/b16c80a7e6b21e3671f8f7fa4ec468777f7e1e8b/OPTIONS/secure/courses/56d27944-4131-11e1-8164-0017f20ea192-Mediathread_video_uploaded_by_mlp55.flv"

    def test_poster_url(self):
        assert self.file.has_cuit_poster() == False
        assert self.video.cuit_poster_url() is None


