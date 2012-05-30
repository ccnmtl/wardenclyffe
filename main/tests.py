"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from wardenclyffe.main.models import Collection, Video, File
import uuid
from wardenclyffe.main.tasks import strip_special_characters


class CUITFileTest(TestCase):
    def setUp(self):
        self.collection = Collection.objects.create(title="test collection",
                                            uuid=uuid.uuid4())
        self.video = Video.objects.create(collection=self.collection,
                                          title="test video",
                                          uuid=uuid.uuid4())
        self.file = File.objects.create(video=self.video,
                                        label="CUIT File",
                                        location_type="cuit",
                                        filename="/www/data/ccnmtl/broadcast/secure/courses/56d27944-4131-11e1-8164-0017f20ea192-Mediathread_video_uploaded_by_mlp55.flv",
                                        )

    def test_extension(self):
        assert self.video.extension() == ".flv"

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


class CollectionTest(TestCase):
    def setUp(self):
        self.collection = Collection.objects.create(title="test collection",
                                            uuid=uuid.uuid4())

    def test_forms(self):
        add_form = self.collection.add_video_form()
        assert "id_title" in str(add_form)
        assert 'title' in add_form.fields
        edit_form = self.collection.edit_form()
        assert 'title' in edit_form.fields
        assert self.collection.title in str(edit_form)


class EmptyVideoTest(TestCase):
    """ test the behavior for a video that doesn't have any files associated
    with it """
    def setUp(self):
        self.collection = Collection.objects.create(title="test collection",
                                            uuid=uuid.uuid4())
        self.video = Video.objects.create(collection=self.collection,
                                          title="test video",
                                          uuid=uuid.uuid4())

    def test_extension(self):
        assert self.video.extension() == ""

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
        assert self.video.get_dimensions() == (0, 0)

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
        assert self.video.mediathread_submit() == (None, None)

    def test_is_vital_submit(self):
        assert not self.video.is_vital_submit()

    def test_vital_submit(self):
        assert self.video.vital_submit() == (None, None, None)

    def test_poster(self):
        assert self.video.poster().dummy

    def test_cuit_file(self):
        assert self.video.cuit_file() == None


class MediathreadVideoTest(TestCase):
    """ test the behavior for a video that was uploaded to Mediathread """
    def setUp(self):
        self.collection = Collection.objects.create(title="Mediathread Spring 2012",
                                                    uuid=uuid.uuid4())
        self.video = Video.objects.create(collection=self.collection,
                                          title="test video",
                                          creator="anp8",
                                          uuid=uuid.uuid4())

        self.source_file = File.objects.create(
            video=self.video,
            label="source file",
            location_type="none",
            filename="6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov",
            )
        metadata = """ID_AUDIO_BITRATE,128000
ID_AUDIO_CODEC,faad
ID_AUDIO_FORMAT,255
ID_AUDIO_ID,0
ID_AUDIO_NCH,2
ID_AUDIO_RATE,48000
ID_CHAPTERS,0
ID_DEMUXER,lavfpref
ID_EXIT,EOF
ID_FILENAME,/var/www/wardenclyffe/tmp//6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov
ID_LENGTH,31.26
ID_SEEKABLE,1
ID_VIDEO_ASPECT,1.3333
ID_VIDEO_BITRATE,0
ID_VIDEO_CODEC,ffh264
ID_VIDEO_FORMAT,avc1
ID_VIDEO_FPS,29.970
ID_VIDEO_HEIGHT,480
ID_VIDEO_ID,1
ID_VIDEO_WIDTH,704"""
        for line in metadata.split("\n"):
            line = line.strip()
            (k, v) = line.split(",")
            self.source_file.set_metadata(k, v)
        self.cuit_file = File.objects.create(
            video=self.video,
            label="CUIT File",
            location_type="cuit",
            filename="/www/data/ccnmtl/broadcast/secure/courses/40e67868-41f1-11e1-aaa7-0017f20ea192-Mediathread_video_uploaded_by_anp8.flv",
            )
        self.tahoe_file = File.objects.create(
            video=self.video,
            label="uploaded source file",
            location_type="tahoe",
            cap="URI:CHK:dzunkd4hgk6zn4eclrxihmpwcq:wowscjwczcrih2cjsdgps5igj4ommb43vxsh5m4ludnxrucrbdsa:3:10:4783186",
            filename="/var/www/wardenclyffe/tmp//6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov"
            )
        self.mediathread_file = File.objects.create(
            video=self.video,
            label="mediathread",
            location_type="mediathread",
            url="http://mediathread.ccnmtl.columbia.edu/asset/5684/",
            )

    def test_extension(self):
        assert self.video.extension() == ".mov"

    def test_tahoe_file(self):
        assert self.video.tahoe_file() == self.tahoe_file

    def test_source_file(self):
        assert self.video.source_file() == self.source_file

    def test_cap(self):
        assert self.video.cap() == self.tahoe_file.cap

    def test_tahoe_download_url(self):
        assert self.video.tahoe_download_url() == "http://tahoe.ccnmtl.columbia.edu/file/URI:CHK:dzunkd4hgk6zn4eclrxihmpwcq:wowscjwczcrih2cjsdgps5igj4ommb43vxsh5m4ludnxrucrbdsa:3:10:4783186/@@named=/var/www/wardenclyffe/tmp//6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov"

    def test_enclosure_url(self):
        assert self.video.enclosure_url() == "http://tahoe.ccnmtl.columbia.edu/file/URI:CHK:dzunkd4hgk6zn4eclrxihmpwcq:wowscjwczcrih2cjsdgps5igj4ommb43vxsh5m4ludnxrucrbdsa:3:10:4783186/@@named=/var/www/wardenclyffe/tmp//6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov"

    def test_filename(self):
        assert self.video.filename() == self.source_file.filename

    def test_add_file_form(self):
        add_form = self.video.add_file_form()

    def test_edit_form(self):
        edit_form = self.video.edit_form()

    def test_get_dimensions(self):
        assert self.video.get_dimensions() == (704, 480)

    def test_vital_thumb_url(self):
        assert self.video.vital_thumb_url() == ""

    def test_cuit_url(self):
        assert self.video.cuit_url() == "http://ccnmtl.columbia.edu/stream/flv/secure/courses/40e67868-41f1-11e1-aaa7-0017f20ea192-Mediathread_video_uploaded_by_anp8.flv"

    def test_mediathread_url(self):
        assert self.video.mediathread_url() == "http://ccnmtl.columbia.edu/stream/flv/e0c41066bd2c496c76fd178083d159386518be11/OPTIONS/secure/courses/40e67868-41f1-11e1-aaa7-0017f20ea192-Mediathread_video_uploaded_by_anp8.flv"

    def test_poster_url(self):
        assert self.video.poster_url() == "http://ccnmtl.columbia.edu/broadcast/posters/vidthumb_480x360.jpg"

    def test_cuit_poster_url(self):
        assert self.video.cuit_poster_url() == None

    def test_is_mediathread_submit(self):
        assert not self.video.is_mediathread_submit()

    def test_mediathread_submit(self):
        assert self.video.mediathread_submit() == (None, None)

    def test_is_vital_submit(self):
        assert not self.video.is_vital_submit()

    def test_vital_submit(self):
        assert self.video.vital_submit() == (None, None, None)

    def test_poster(self):
        assert self.video.poster().dummy

    def test_cuit_file(self):
        assert self.video.cuit_file() == self.cuit_file


class VitalVideoTest(TestCase):
    """ test the behavior for a video that was uploaded to Vital """
    def setUp(self):
        self.collection = Collection.objects.create(title="Vital Spring 2012",
                                                    uuid=uuid.uuid4())
        self.video = Video.objects.create(collection=self.collection,
                                          title="Vital video uploaded by anp8",
                                          creator="anp8",
                                          uuid=uuid.uuid4())

        self.source_file = File.objects.create(
            video=self.video,
            label="source file",
            location_type="none",
            filename="wctest.mov",
            )
        metadata = """ID_AUDIO_BITRATE,128000
ID_AUDIO_CODEC,faad
ID_AUDIO_FORMAT,255
ID_AUDIO_ID,0
ID_AUDIO_NCH,2
ID_AUDIO_RATE,48000
ID_CHAPTERS,0
ID_DEMUXER,lavfpref
ID_EXIT,EOF
ID_FILENAME,/var/www/wardenclyffe/tmp//5c4aa9a5-0110-4e47-b314-1a89321dbcd9.mov
ID_LENGTH,31.26
ID_SEEKABLE,1
ID_VIDEO_ASPECT,1.3333
ID_VIDEO_BITRATE,0
ID_VIDEO_CODEC,ffh264
ID_VIDEO_FORMAT,avc1
ID_VIDEO_FPS,29.970
ID_VIDEO_HEIGHT,480
ID_VIDEO_ID,1
ID_VIDEO_WIDTH,704"""
        for line in metadata.split("\n"):
            line = line.strip()
            (k, v) = line.split(",")
            self.source_file.set_metadata(k, v)
        self.cuit_file = File.objects.create(
            video=self.video,
            label="CUIT File",
            location_type="cuit",
            filename="/www/data/ccnmtl/broadcast/secure/courses/40e67868-41f1-11e1-aaa7-0017f20ea192-Mediathread_video_uploaded_by_anp8.flv",
            )
        self.tahoe_file = File.objects.create(
            video=self.video,
            label="uploaded source file",
            location_type="tahoe",
            cap="URI:CHK:dzunkd4hgk6zn4eclrxihmpwcq:wowscjwczcrih2cjsdgps5igj4ommb43vxsh5m4ludnxrucrbdsa:3:10:4783186",
            filename="/var/www/wardenclyffe/tmp//5c4aa9a5-0110-4e47-b314-1a89321dbcd9.mov",
            )
        self.vital_thumbnail = File.objects.create(
            video=self.video,
            label="vital thumbnail image",
            location_type="vitalthumb",
            url="http://ccnmtl.columbia.edu/broadcast/projects/vital/thumbs/vital/25b0e81e-42b2-11e1-a13d-0017f20ea192-Vital_video_uploaded_by_anp8_thumb.png",
            )
        self.qtsp_file = File.objects.create(
            video=self.video,
            label="Quicktime Streaming Video",
            location_type="rtsp_url",
            url="rtsp://qtss.cc.columbia.edu/projects/vital/25b0e81e-42b2-11e1-a13d-0017f20ea192-Vital_video_uploaded_by_anp8.mov",
            )

    def test_extension(self):
        assert self.video.extension() == ".mov"

    def test_tahoe_file(self):
        assert self.video.tahoe_file() == self.tahoe_file

    def test_source_file(self):
        assert self.video.source_file() == self.source_file

    def test_cap(self):
        assert self.video.cap() == self.tahoe_file.cap

    def test_tahoe_download_url(self):
        assert self.video.tahoe_download_url() == "http://tahoe.ccnmtl.columbia.edu/file/URI:CHK:dzunkd4hgk6zn4eclrxihmpwcq:wowscjwczcrih2cjsdgps5igj4ommb43vxsh5m4ludnxrucrbdsa:3:10:4783186/@@named=/var/www/wardenclyffe/tmp//5c4aa9a5-0110-4e47-b314-1a89321dbcd9.mov"

    def test_enclosure_url(self):
        assert self.video.enclosure_url() == "http://tahoe.ccnmtl.columbia.edu/file/URI:CHK:dzunkd4hgk6zn4eclrxihmpwcq:wowscjwczcrih2cjsdgps5igj4ommb43vxsh5m4ludnxrucrbdsa:3:10:4783186/@@named=/var/www/wardenclyffe/tmp//5c4aa9a5-0110-4e47-b314-1a89321dbcd9.mov"

    def test_filename(self):
        assert self.video.filename() == self.source_file.filename

    def test_add_file_form(self):
        add_form = self.video.add_file_form()

    def test_edit_form(self):
        edit_form = self.video.edit_form()

    def test_get_dimensions(self):
        assert self.video.get_dimensions() == (704, 480)

    def test_vital_thumb_url(self):
        assert self.video.vital_thumb_url() == self.vital_thumbnail.url

    def test_cuit_url(self):
        assert self.video.cuit_url() == "http://ccnmtl.columbia.edu/stream/flv/secure/courses/40e67868-41f1-11e1-aaa7-0017f20ea192-Mediathread_video_uploaded_by_anp8.flv"

    def test_mediathread_url(self):
        assert self.video.mediathread_url() == "http://ccnmtl.columbia.edu/stream/flv/e0c41066bd2c496c76fd178083d159386518be11/OPTIONS/secure/courses/40e67868-41f1-11e1-aaa7-0017f20ea192-Mediathread_video_uploaded_by_anp8.flv"

    def test_poster_url(self):
        assert self.video.poster_url() == "http://ccnmtl.columbia.edu/broadcast/posters/vidthumb_480x360.jpg"

    def test_cuit_poster_url(self):
        assert self.video.cuit_poster_url() == None

    def test_is_mediathread_submit(self):
        assert not self.video.is_mediathread_submit()

    def test_mediathread_submit(self):
        assert self.video.mediathread_submit() == (None, None)

    def test_is_vital_submit(self):
        assert not self.video.is_vital_submit()

    def test_vital_submit(self):
        assert self.video.vital_submit() == (None, None, None)

    def test_poster(self):
        assert self.video.poster().dummy

    def test_cuit_file(self):
        assert self.video.cuit_file() == self.cuit_file


class MissingDimensionsTest(TestCase):
    """ test the behavior for a video that has a source file, but
    that we couldn't parse the dimensions out of for some reason
    """
    def setUp(self):
        self.collection = Collection.objects.create(title="Mediathread Spring 2012",
                                                    uuid=uuid.uuid4())
        self.video = Video.objects.create(collection=self.collection,
                                          title="test video",
                                          creator="anp8",
                                          uuid=uuid.uuid4())

        self.source_file = File.objects.create(
            video=self.video,
            label="source file",
            location_type="none",
            filename="6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov",
            )
        metadata = """ID_AUDIO_BITRATE,128000
ID_AUDIO_CODEC,faad
ID_AUDIO_FORMAT,255
ID_AUDIO_ID,0
ID_AUDIO_NCH,2
ID_AUDIO_RATE,48000
ID_CHAPTERS,0
ID_DEMUXER,lavfpref
ID_EXIT,EOF
ID_FILENAME,/var/www/wardenclyffe/tmp//6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov
ID_LENGTH,31.26
ID_SEEKABLE,1
ID_VIDEO_ASPECT,1.3333
ID_VIDEO_BITRATE,0
ID_VIDEO_CODEC,ffh264
ID_VIDEO_FORMAT,avc1
ID_VIDEO_FPS,29.970
ID_VIDEO_ID,1"""
        for line in metadata.split("\n"):
            line = line.strip()
            (k, v) = line.split(",")
            self.source_file.set_metadata(k, v)
        self.cuit_file = File.objects.create(
            video=self.video,
            label="CUIT File",
            location_type="cuit",
            filename="/www/data/ccnmtl/broadcast/secure/courses/40e67868-41f1-11e1-aaa7-0017f20ea192-Mediathread_video_uploaded_by_anp8.flv",
            )
        self.tahoe_file = File.objects.create(
            video=self.video,
            label="uploaded source file",
            location_type="tahoe",
            cap="URI:CHK:dzunkd4hgk6zn4eclrxihmpwcq:wowscjwczcrih2cjsdgps5igj4ommb43vxsh5m4ludnxrucrbdsa:3:10:4783186",
            filename="/var/www/wardenclyffe/tmp//6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov"
            )
        self.mediathread_file = File.objects.create(
            video=self.video,
            label="mediathread",
            location_type="mediathread",
            url="http://mediathread.ccnmtl.columbia.edu/asset/5684/",
            )

    def test_get_dimensions(self):
        assert self.video.get_dimensions() == (0, 0)


class SpecialCharacterTests(TestCase):

    def test_strip_characters(self):
        self.assertEquals(strip_special_characters("video file"), "video_file")
        self.assertEquals(strip_special_characters("video \"foo\" file"),
                          "video_foo_file")
        self.assertEquals(strip_special_characters("a.b.c"), "a_b_c")
        self.assertEquals(strip_special_characters("(foo)"), "_foo_")
