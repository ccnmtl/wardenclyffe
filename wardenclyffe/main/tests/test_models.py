"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from wardenclyffe.main.tasks import strip_special_characters
from factories import CollectionFactory, VideoFactory, CUITFLVFileFactory
from factories import SourceFileFactory
from factories import MediathreadFileFactory, FileFactory
from factories import PublicFileFactory, OperationFactory
from factories import DimensionlessSourceFileFactory
from factories import ServerFactory, UserFactory


class CUITFileTest(TestCase):
    def setUp(self):
        self.file = CUITFLVFileFactory()

    def test_extension(self):
        assert self.file.video.extension() == ".flv"

    def test_is_cuit(self):
        assert self.file.is_cuit()

    def test_surelinkable(self):
        assert self.file.surelinkable()

    def test_mediathread_url(self):
        self.assertEqual(
            self.file.video.mediathread_url(),
            ("http://ccnmtl.columbia.edu/stream/flv/"
             "99bd1007cd733e65d12d0f843e1a9f5c1f28dec2"
             "/OPTIONS/secure/courses/"
             "56d27944-4131-11e1-8164-0017f20ea192-"
             "Mediathread_video_uploaded_by_mlp55.flv"))

    def test_poster_url(self):
        assert not self.file.has_cuit_poster()
        assert self.file.video.cuit_poster_url() is None

    def test_filename(self):
        assert self.file.video.filename() == self.file.filename

    def test_cuit_url(self):
        assert self.file.cuit_public_url() == (
            "http://ccnmtl.columbia.edu/stream/flv/secure/courses/"
            "56d27944-4131-11e1-8164-0017f20ea192-"
            "Mediathread_video_uploaded_by_mlp55.flv")
        assert self.file.video.cuit_url() == self.file.cuit_public_url()


class CollectionTest(TestCase):
    def test_forms(self):
        self.collection = CollectionFactory()
        add_form = self.collection.add_video_form()
        assert "id_title" in str(add_form)
        assert 'title' in add_form.fields


class EmptyVideoTest(TestCase):
    """ test the behavior for a video that doesn't have any files associated
    with it """
    def setUp(self):
        self.video = VideoFactory()

    def test_extension(self):
        assert self.video.extension() == ""

    def test_source_file(self):
        assert self.video.source_file() is None

    def test_filename(self):
        assert self.video.filename() == "none"

    def test_add_file_form(self):
        self.video.add_file_form()

    def test_get_dimensions(self):
        assert self.video.get_dimensions() == (0, 0)

    def test_cuit_url(self):
        assert self.video.cuit_url() == ""

    def test_mediathread_url(self):
        assert self.video.mediathread_url() == ""

    def test_poster_url(self):
        self.assertEquals(
            self.video.poster_url(),
            ("http://ccnmtl.columbia.edu/broadcast/posters/"
             "vidthumb_480x360.jpg"))

    def test_cuit_poster_url(self):
        assert self.video.cuit_poster_url() is None

    def test_is_mediathread_submit(self):
        assert not self.video.is_mediathread_submit()

    def test_mediathread_submit(self):
        assert self.video.mediathread_submit() == (None, None, None)

    def test_poster(self):
        assert self.video.poster().dummy

    def test_cuit_file(self):
        assert self.video.cuit_file() is None

    def test_make_source_file(self):
        f = self.video.make_source_file("somefile.mpg")
        self.assertEqual(f.filename, "somefile.mpg")

    def test_upto_hundred_images(self):
        r = self.video.upto_hundred_images()
        self.assertEqual(len(r), 0)

    def test_is_audio_file(self):
        self.assertFalse(self.video.is_audio_file())


class FileTest(TestCase):
    def test_set_metadata(self):
        f = FileFactory()
        f.set_metadata("foo", "bar")
        self.assertEqual(f.get_metadata("foo"), "bar")

    def test_update_metadata(self):
        f = FileFactory()
        f.set_metadata("foo", "bar")
        f.set_metadata("foo", "baz")
        self.assertEqual(f.get_metadata("foo"), "baz")

    def test_get_absolute_url(self):
        f = FileFactory()
        self.assertEqual(f.get_absolute_url(), "/file/%d/" % f.id)


class MediathreadVideoTest(TestCase):
    """ test the behavior for a video that was uploaded to Mediathread """
    def test_extension(self):
        f = CUITFLVFileFactory()
        self.assertEquals(f.video.extension(), ".flv")

    def test_source_file(self):
        source_file = SourceFileFactory()
        assert source_file.video.source_file() == source_file

    def test_filename(self):
        source_file = SourceFileFactory()
        assert source_file.video.filename() == source_file.filename

    def test_add_file_form(self):
        f = CUITFLVFileFactory()
        f.video.add_file_form()

    def test_get_dimensions(self):
        source_file = SourceFileFactory()
        assert source_file.video.get_dimensions() == (704, 480)

    def test_cuit_url(self):
        f = CUITFLVFileFactory(
            filename=("/www/data/ccnmtl/broadcast/secure/courses/"
                      "40e67868-41f1-11e1-aaa7-0017f20ea192-"
                      "Mediathread_video_uploaded_by_anp8.flv"))
        assert f.video.cuit_url() == (
            "http://ccnmtl.columbia.edu/stream/flv/secure/courses/"
            "40e67868-41f1-11e1-aaa7-0017f20ea192-"
            "Mediathread_video_uploaded_by_anp8.flv")

    def test_mediathread_url(self):
        f = CUITFLVFileFactory(
            filename=("/www/data/ccnmtl/broadcast/secure/courses/"
                      "40e67868-41f1-11e1-aaa7-0017f20ea192-"
                      "Mediathread_video_uploaded_by_anp8.flv"))
        self.assertEquals(
            f.video.mediathread_url(),
            (
                "http://ccnmtl.columbia.edu/stream/flv/"
                "4d9a45a17dbcf0c50241d0f5ec2f237d08f38398"
                "/OPTIONS/secure/courses/"
                "40e67868-41f1-11e1-aaa7-0017f20ea192"
                "-Mediathread_video_uploaded_by_anp8.flv"))

    def test_poster_url(self):
        f = CUITFLVFileFactory()
        assert f.video.poster_url() == (
            "http://ccnmtl.columbia.edu/broadcast/posters/"
            "vidthumb_480x360.jpg")

    def test_cuit_poster_url(self):
        f = CUITFLVFileFactory()
        assert f.video.cuit_poster_url() is None

    def test_is_mediathread_submit(self):
        f = CUITFLVFileFactory()
        assert not f.video.is_mediathread_submit()

    def test_mediathread_submit(self):
        f = MediathreadFileFactory()
        assert f.video.mediathread_submit() == (None, None, None)

    def test_poster(self):
        f = CUITFLVFileFactory()
        assert f.video.poster().dummy

    def test_cuit_file(self):
        f = CUITFLVFileFactory()
        assert f.video.cuit_file() == f


class MissingDimensionsTest(TestCase):
    """ test the behavior for a video that has a source file, but
    that we couldn't parse the dimensions out of for some reason
    """
    def test_get_dimensions(self):
        m = MediathreadFileFactory()
        CUITFLVFileFactory(video=m.video)
        DimensionlessSourceFileFactory(video=m.video)

        assert m.video.get_dimensions() == (0, 0)


class SpecialCharacterTests(TestCase):
    def test_strip_characters(self):
        self.assertEquals(strip_special_characters("video file"), "video_file")
        self.assertEquals(strip_special_characters("video \"foo\" file"),
                          "video_foo_file")
        self.assertEquals(strip_special_characters("a.b.c"), "a_b_c")
        self.assertEquals(strip_special_characters("(foo)"), "_foo_")


class H264SecureStreamFileTest(TestCase):
    def test_h264_secure_stream_url(self):
        f = FileFactory()
        assert f.video.h264_secure_stream_url() == (
            "http://stream.ccnmtl.columbia.edu/secvideos/"
            "SECURE/courses/56d27944-4131-11e1-8164-0017f20ea192"
            "-Mediathread_video_uploaded_by_mlp55.mp4")


class H264PublicStreamFileTest(TestCase):
    def test_h264_public_stream_url(self):
        f = PublicFileFactory()
        self.assertEquals(f.video.h264_public_stream_url(),
                          ("http://stream.ccnmtl.columbia.edu/public/"
                           "courses/56d27944-4131-11e1-8164-0017f20ea192-"
                           "Mediathread_video_uploaded_by_mlp55.mp4"))

    def test_h264_public_path(self):
        f = PublicFileFactory()
        self.assertEquals(f.h264_public_path(),
                          ("/courses/56d27944-4131-11e1-8164-0017f20ea192-"
                           "Mediathread_video_uploaded_by_mlp55.mp4"))


class SubmitFilesTest(TestCase):
    def test_mediathread_submit(self):
        v = VideoFactory()
        u = UserFactory()
        v.make_mediathread_submit_file(
            "file.mp4", u, "course-id",
            "http://example.com/", audio=False,
            audio2=False)
        self.assertEquals(
            v.mediathread_submit(),
            ("course-id", u.username, None, None))
        v.clear_mediathread_submit()
        self.assertEquals(
            v.mediathread_submit(),
            (None, None, None))

    def test_mediathread_submit_audio(self):
        v = VideoFactory()
        u = UserFactory()
        v.make_mediathread_submit_file(
            "file.mp4", u, "course-id",
            "http://example.com/", audio=True,
            audio2=True)
        self.assertEquals(
            v.mediathread_submit(),
            ("course-id", u.username, u'True', u'True'))
        self.assertTrue(v.is_audio_file())
        v.clear_mediathread_submit()
        self.assertEquals(
            v.mediathread_submit(),
            (None, None, None))


class OperationTest(TestCase):
    def test_basics(self):
        o = OperationFactory()
        self.assertEquals(o.get_absolute_url().startswith("/operation/"),
                          True)
        d = o.as_dict()
        self.assertEquals(d['status'], o.status)
        self.assertEquals(o.formatted_params(), '{}')

    def test_default_operations_creation(self):
        f = SourceFileFactory()
        u = UserFactory()
        (ops, params) = f.video.make_default_operations(
            "/tmp/file.mov",
            f, u)
        self.assertEquals(len(ops), 3)
        # just run these to get the coverage up. don't worry if they fail
        for (o, p) in zip(ops, params):
            o.process(params)
            o.post_process()

    def test_audio_default_operations_creation(self):
        f = SourceFileFactory()
        u = UserFactory()
        (ops, params) = f.video.make_default_operations(
            "/tmp/file.mov",
            f, u, True, True)
        self.assertEquals(len(ops), 1)
        # just run these to get the coverage up. don't worry if they fail
        for (o, p) in zip(ops, params):
            o.process(params)

    def test_submit_to_pcp_operation(self):
        f = SourceFileFactory()
        u = UserFactory()
        o, p = f.video.make_submit_to_podcast_producer_operation(
            "/tmp/file.mov", "SOMEWORKFLOW", u)
        o.process(p)
        o.post_process()

    def test_make_upload_to_youtube_operation(self):
        f = SourceFileFactory()
        u = UserFactory()
        o, p = f.video.make_upload_to_youtube_operation("/tmp/file.mov", u)
        o.process(p)
        o.post_process()


class ServerTest(TestCase):
    def test_unicode(self):
        s = ServerFactory()
        self.assertEquals(str(s), s.name)

    def test_url(self):
        s = ServerFactory()
        self.assertEquals(s.get_absolute_url(), "/server/%d/" % s.id)
