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

    def test_filename(self):
        assert self.video.filename() == self.file.filename

    def test_cuit_url(self):
        assert self.file.cuit_public_url() == "http://ccnmtl.columbia.edu/stream/flv/secure/courses/56d27944-4131-11e1-8164-0017f20ea192-Mediathread_video_uploaded_by_mlp55.flv"
        assert self.video.cuit_url() == self.file.cuit_public_url()


class SeriesTest(TestCase):
    def setUp(self):
        self.series = Series.objects.create(title = "test series",
                                            uuid = uuid.uuid4())

    def test_forms(self):
        add_form = self.series.add_video_form()
        assert "id_title" in str(add_form)
        assert 'title' in add_form.fields
        edit_form = self.series.edit_form()
        assert 'title' in edit_form.fields
        assert self.series.title in str(edit_form)

class EmptyVideoTest(TestCase):
    """ test the behavior for a video that doesn't have any files associated
    with it """
    def setUp(self):
        self.series = Series.objects.create(title = "test series",
                                            uuid = uuid.uuid4())
        self.video = Video.objects.create(series = self.series,
                                          title = "test video",
                                          uuid = uuid.uuid4())
    def test_tahoe_file(self):
        assert self.video.tahoe_file() is None

    def test_source_file(self):
        assert self.video.source_file() is None

    def test_cap(self):
        assert self.video.cap() is None

    def test_tahoe_download_url(self):
        assert self.video.tahoe_download_url() == ""

    def test_enclosure_url(self): 
        assert self.video.enclosure_url() == ""       

    def test_filename(self):
        assert self.video.filename() == "none"

    def test_add_file_form(self):
        add_form = self.video.add_file_form()

    def test_edit_form(self):
        edit_form = self.video.edit_form()

    def test_get_dimensions(self):
        assert self.video.get_dimensions() == (0,0)

    def test_vital_thumb_url(self):
        assert self.video.vital_thumb_url() == ""

    def test_cuit_url(self):
        assert self.video.cuit_url() == ""

    def test_mediathread_url(self):
        assert self.video.mediathread_url() == ""

    def test_poster_url(self):
        assert self.video.poster_url() == "http://ccnmtl.columbia.edu/broadcast/posters/vidthumb_480x360.jpg"

    def test_cuit_poster_url(self):
        assert self.video.cuit_poster_url() == None

    def test_is_mediathread_submit(self):
        assert not self.video.is_mediathread_submit()

    def test_mediathread_submit(self):
        assert self.video.mediathread_submit() == (None,None)

    def test_is_vital_submit(self):
        assert not self.video.is_vital_submit()

    def test_vital_submit(self):
        assert self.video.vital_submit() == (None,None,None)

    def test_poster(self):
        assert self.video.poster().dummy

    def test_cuit_file(self):
        assert self.video.cuit_file() == None
