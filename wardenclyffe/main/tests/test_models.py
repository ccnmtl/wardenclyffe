from __future__ import unicode_literals

"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from json import loads

from django.test import TestCase
from django.test.utils import override_settings

from wardenclyffe.main.tests.factories import (
    CollectionFactory, VideoFactory, CUITFLVFileFactory,
    SourceFileFactory, MediathreadFileFactory, S3FileFactory, FileFactory,
    PublicFileFactory, OperationFactory, DimensionlessSourceFileFactory,
    ServerFactory, UserFactory, SecureFileFactory, PosterFactory,
    MediathreadSubmitFileFactory,
)
from wardenclyffe.main.models import Video
from wardenclyffe.main.tasks import strip_special_characters


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

    def test_is_public(self):
        c = CollectionFactory(title="h264 Public", public=True)
        self.assertTrue(c.is_public())

        c = CollectionFactory(title="some other title", public=True)
        self.assertTrue(c.is_public())

        c = CollectionFactory(title="not h264 public", public=False)
        self.assertFalse(c.is_public())

        c = CollectionFactory(title="make sure default is secure")
        self.assertFalse(c.is_public())

    def test_delete_collection(self):
        v = VideoFactory()
        v.collection.delete()
        v.refresh_from_db()
        self.assertEqual(v.collection.title, 'Unclassified')


class VideoTest(TestCase):

    def test_search(self):
        video = VideoFactory(title='alpha')
        VideoFactory(title='beta')

        qs = Video.objects.search('alpha')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), video)


class EmptyVideoTest(TestCase):
    """ test the behavior for a video that doesn't have any files associated
    with it """
    def setUp(self):
        self.video = VideoFactory()

    def test_extension(self):
        assert self.video.extension() == ""

    def test_extension_non_source(self):
        f = PublicFileFactory()
        self.assertEqual(f.video.extension(), ".mp4")

    def test_extension_with_source(self):
        f = SourceFileFactory()
        self.assertEqual(f.video.extension(), ".mov")

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
        self.assertEqual(
            self.video.poster_url(),
            ("http://ccnmtl.columbia.edu/broadcast/posters/"
             "vidthumb_480x360.jpg"))

    def test_poster(self):
        p = PosterFactory()
        self.assertEqual(p.video.poster(), p)

    def test_cuit_poster_url(self):
        assert self.video.cuit_poster_url() is None

    def test_is_mediathread_submit(self):
        assert not self.video.is_mediathread_submit()

    def test_mediathread_submit(self):
        assert self.video.mediathread_submit() == (None, None, None)

    def test_poster_dummy(self):
        assert self.video.poster().dummy

    def test_cuit_file(self):
        assert self.video.cuit_file() is None

    def test_panopto_file(self):
        assert self.video.panopto_file() is None

    def test_youtube_file(self):
        assert self.video.youtube_file() is None

    def test_has_flv(self):
        self.assertFalse(self.video.has_flv())

    def test_has_panopto_source(self):
        self.assertFalse(self.video.has_panopto_source())

    def test_has_mp4(self):
        self.assertFalse(self.video.has_mp4())

    def test_has_s3_source(self):
        self.assertFalse(self.video.has_s3_source())

    def test_flv_convertable(self):
        self.assertFalse(self.video.flv_convertable())

    def test_streamlogs_no_flv(self):
        self.assertEqual(self.video.streamlogs().count(), 0)

    def test_streamlogs_with_flv(self):
        CUITFLVFileFactory(video=self.video)
        r = self.video.streamlogs()
        self.assertIsNotNone(r)
        self.assertEqual(r.count(), 0)

    def test_make_source_file(self):
        f = self.video.make_source_file("somefile.mpg")
        self.assertEqual(f.filename, "somefile.mpg")

    def test_upto_hundred_images(self):
        r = self.video.upto_hundred_images()
        self.assertEqual(len(r), 0)

    def test_is_audio_file(self):
        self.assertFalse(self.video.is_audio_file())

    def test_s3_key(self):
        source = S3FileFactory()
        k = source.video.s3_key()
        self.assertTrue(k.endswith("oppenheim_shear_kim1_edit.mov"))

    def test_s3_key_non_s3(self):
        source = FileFactory()
        k = source.video.s3_key()
        self.assertEqual(k, None)

    def test_handle_mediathread_submit(self):
        f = MediathreadSubmitFileFactory()
        UserFactory(username=f.get_metadata("username"))
        ops = f.video.handle_mediathread_submit()
        self.assertEqual(len(ops), 1)
        op = ops[0]
        self.assertEqual(loads(op.params)['set_course'], "a course")

    def test_handle_mediathread_submit_no_course(self):
        f = MediathreadSubmitFileFactory()
        f.set_metadata("set_course", None)
        ops = f.video.handle_mediathread_submit()
        self.assertEqual(len(ops), 0)

    def test_s3_transcoded_none(self):
        f = MediathreadSubmitFileFactory()
        self.assertIsNone(f.video.s3_transcoded())
        self.assertFalse(f.video.has_s3_transcoded())

    def test_s3_transcoded_exists(self):
        f = S3FileFactory(label="transcoded 480p file (S3)")
        self.assertIsNotNone(f.video.s3_transcoded())
        self.assertTrue(f.video.has_s3_transcoded())


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


class S3FileTest(TestCase):
    def test_is_s3(self):
        f = S3FileFactory()
        self.assertTrue(f.is_s3())

    @override_settings(AWS_S3_UPLOAD_BUCKET="foo",
                       AWS_SECRET_KEY="bar",
                       AWS_ACCESS_KEY="baz")
    def test_s3_download_url(self):
        f = S3FileFactory()
        self.assertTrue(
            f.s3_download_url().startswith(
                ("https://s3.amazonaws.com/foo/2011/09/28/"
                 "t6009_005_2011_3_oppenheim_"
                 "shear_kim1_edit.mov")))

    @override_settings(AWS_S3_UPLOAD_BUCKET="foo",
                       AWS_S3_OUTPUT_BUCKET="out",
                       AWS_SECRET_KEY="bar",
                       AWS_ACCESS_KEY="baz")
    def test_s3_download_url_transcode(self):
        f = S3FileFactory()
        f.label = "label has transcode"
        f.save()
        self.assertTrue(
            f.s3_download_url().startswith(
                ("https://s3.amazonaws.com/out/2011/09/28/"
                 "t6009_005_2011_3_oppenheim_"
                 "shear_kim1_edit.mov")))

    def test_non_s3_file(self):
        f = MediathreadFileFactory()
        self.assertFalse(f.is_s3())
        self.assertIsNone(f.s3_download_url())

    def test_default_to_source_File(self):
        source = S3FileFactory()
        S3FileFactory(video=source.video,
                      label="transcoded 480p file (S3)")
        S3FileFactory(video=source.video,
                      label="transcoded 720p file (S3)")
        f = source.video.s3_file()
        self.assertEqual(f, source)

    def test_is_audio(self):
        f = S3FileFactory()
        self.assertFalse(f.is_audio())
        f2 = FileFactory()
        self.assertFalse(f2.is_audio())
        f3 = S3FileFactory(cap='something.mp3')
        self.assertTrue(f3.is_audio())
        # uppercase extension too
        f4 = S3FileFactory(cap='something.MP3')
        self.assertTrue(f4.is_audio())


class MediathreadVideoTest(TestCase):
    """ test the behavior for a video that was uploaded to Mediathread """
    def test_extension(self):
        f = CUITFLVFileFactory()
        self.assertEqual(f.video.extension(), ".flv")

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

    def test_guess_width(self):
        s = SourceFileFactory()
        s.set_metadata("ID_VIDEO_WIDTH", 100)
        self.assertEqual(s.guess_width(), 100)

    def test_guess_height(self):
        s = SourceFileFactory()
        s.set_metadata("ID_VIDEO_HEIGHT", 100)
        self.assertEqual(s.guess_height(), 100)

    def test_cuit_url(self):
        f = CUITFLVFileFactory(
            filename=("/www/data/ccnmtl/broadcast/secure/courses/"
                      "40e67868-41f1-11e1-aaa7-0017f20ea192-"
                      "Mediathread_video_uploaded_by_anp8.flv"))
        assert f.video.cuit_url() == (
            "http://ccnmtl.columbia.edu/stream/flv/secure/courses/"
            "40e67868-41f1-11e1-aaa7-0017f20ea192-"
            "Mediathread_video_uploaded_by_anp8.flv")

    def test_has_panopto_source(self):
        f = FileFactory(location_type='panopto')
        self.assertTrue(f.video.has_panopto_source())

    def test_mediathread_url(self):
        f = CUITFLVFileFactory(
            filename=("/www/data/ccnmtl/broadcast/secure/courses/"
                      "40e67868-41f1-11e1-aaa7-0017f20ea192-"
                      "Mediathread_video_uploaded_by_anp8.flv"))
        self.assertEqual(
            f.video.mediathread_url(),
            (
                "http://ccnmtl.columbia.edu/stream/flv/"
                "4d9a45a17dbcf0c50241d0f5ec2f237d08f38398"
                "/OPTIONS/secure/courses/"
                "40e67868-41f1-11e1-aaa7-0017f20ea192"
                "-Mediathread_video_uploaded_by_anp8.flv"))

        f = FileFactory(location_type='panopto', filename='foo')
        self.assertEqual(f.video.mediathread_url(), 'foo')

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

    def test_has_mediathread_asset_negative(self):
        f = CUITFLVFileFactory()
        self.assertFalse(f.video.has_mediathread_asset())

    def test_has_mediathread_asset_positive(self):
        f = FileFactory(location_type="mediathread")
        self.assertTrue(f.video.has_mediathread_asset())

    def test_remove_mediathread_asset(self):
        f = FileFactory(location_type="mediathread")
        self.assertTrue(f.video.has_mediathread_asset())
        f.video.remove_mediathread_asset()
        self.assertFalse(f.video.has_mediathread_asset())

    def test_handle_mediathread_delete(self):
        f = FileFactory(location_type="mediathread")
        cf = FileFactory(location_type="cuit")
        pf = FileFactory(location_type="panopto", video=f.video)
        self.assertTrue(f.video.has_mediathread_asset())
        f.video.handle_mediathread_delete()
        self.assertTrue(f.video.has_mediathread_asset())

        cf.delete()
        f.video.handle_mediathread_delete()
        self.assertTrue(f.video.has_mediathread_asset())

        pf.delete()
        f.video.handle_mediathread_delete()
        self.assertFalse(f.video.has_mediathread_asset())

    def test_mediathread_submit(self):
        f = MediathreadFileFactory()
        assert f.video.mediathread_submit() == (None, None, None)

    def test_poster(self):
        f = CUITFLVFileFactory()
        assert f.video.poster().dummy

    def test_cuit_file(self):
        f = CUITFLVFileFactory()
        assert f.video.cuit_file() == f

    def test_panopto_file(self):
        f = FileFactory(location_type='panopto')
        assert f.video.panopto_file() == f

    def test_youtube_file(self):
        f = FileFactory(location_type='youtube')
        assert f.video.youtube_file() == f

    def test_mediathread_update(self):
        v = VideoFactory()
        # none to start with
        self.assertFalse(v.has_mediathread_update())
        # create one
        v.create_mediathread_update()
        self.assertTrue(v.has_mediathread_update())
        # clear it
        v.clear_mediathread_update()
        self.assertFalse(v.has_mediathread_update())


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
        self.assertEqual(strip_special_characters("video file"), "video_file")
        self.assertEqual(strip_special_characters("video \"foo\" file"),
                         "video_foo_file")
        self.assertEqual(strip_special_characters("a.b.c"), "a_b_c")
        self.assertEqual(strip_special_characters("(foo)"), "_foo_")


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
        self.assertEqual(f.video.h264_public_stream_url(),
                         ("http://stream.ccnmtl.columbia.edu/public/"
                          "courses/56d27944-4131-11e1-8164-0017f20ea192-"
                          "Mediathread_video_uploaded_by_mlp55.mp4"))

    def test_h264_public_path(self):
        f = PublicFileFactory()
        self.assertEqual(f.h264_public_path(),
                         ("/courses/56d27944-4131-11e1-8164-0017f20ea192-"
                          "Mediathread_video_uploaded_by_mlp55.mp4"))

    def test_h264_public_stream_url_non_cuit(self):
        f = SourceFileFactory()
        self.assertEqual(f.video.h264_public_stream_url(), "")

    def test_h264_public_stream_url_secure(self):
        f = SecureFileFactory()
        self.assertEqual(f.video.h264_public_stream_url(), "")


class SubmitFilesTest(TestCase):
    def test_mediathread_submit(self):
        v = VideoFactory()
        u = UserFactory()
        v.make_mediathread_submit_file(
            "file.mp4", u, "course-id",
            "http://example.com/", audio=False)
        self.assertEqual(
            v.mediathread_submit(),
            ("course-id", u.username, None))
        v.clear_mediathread_submit()
        self.assertEqual(
            v.mediathread_submit(),
            (None, None, None))

    def test_mediathread_submit_audio(self):
        v = VideoFactory()
        u = UserFactory()
        v.make_mediathread_submit_file(
            "file.mp4", u, "course-id",
            "http://example.com/", audio=True)
        self.assertEqual(
            v.mediathread_submit(),
            ("course-id", u.username, u'True'))
        self.assertTrue(v.is_audio_file())
        v.clear_mediathread_submit()
        self.assertEqual(
            v.mediathread_submit(),
            (None, None, None))


class OperationTest(TestCase):
    def test_basics(self):
        o = OperationFactory()
        self.assertEqual(o.get_absolute_url().startswith("/operation/"),
                         True)
        d = o.as_dict()
        self.assertEqual(d['status'], o.status)
        self.assertEqual(o.formatted_params(), '{}')

    @override_settings(YOUTUBE_EMAIL="foo@bar.com", YOUTUBE_PASSWORD="foo",
                       YOUTUBE_SOURCE="foo", YOUTUBE_DEVELOPER_KEY="foo",
                       YOUTUBE_CLIENT_ID="foo")
    def test_make_upload_to_youtube_operation(self):
        f = SourceFileFactory()
        u = UserFactory()
        o = f.video.make_upload_to_youtube_operation(
            "/tmp/file.mov", u)  # nosec
        try:
            o.process()
        except:  # nosec # noqa
            # we don't expect to actually be able to log in.
            # youtube raises a BadAuthentication or something here
            pass
        o.post_process()

    def test_make_audio_encode_operation(self):
        f = SourceFileFactory()
        u = UserFactory()
        o = f.video.make_audio_encode_operation(f.id, u)
        self.assertTrue('file_id' in loads(o.params))
        self.assertEqual(o.action, "audio encode")

    def test_elastic_transcoder_job_operation(self):
        f = SourceFileFactory()
        u = UserFactory()
        o = f.video.make_create_elastic_transcoder_job_operation(
            "some key", u)
        self.assertTrue('key' in loads(o.params))
        self.assertEqual(loads(o.params)['key'], "some key")
        self.assertEqual(o.action, "create elastic transcoder job")


class ServerTest(TestCase):
    def test_unicode(self):
        s = ServerFactory()
        self.assertEqual(str(s), s.name)

    def test_url(self):
        s = ServerFactory()
        self.assertEqual(s.get_absolute_url(), "/server/%d/" % s.id)
