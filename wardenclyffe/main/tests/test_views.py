from __future__ import unicode_literals

import json
import os.path

from django.urls.base import reverse
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.test.utils import override_settings
from httpretty import HTTPretty, httprettified
import httpretty

from wardenclyffe.main.models import Collection, Operation, File
from wardenclyffe.main.tests.factories import (
    FileFactory, OperationFactory, ServerFactory,
    UserFactory, VideoFactory, CollectionFactory,
    ImageFactory, OperationFileFactory)
from wardenclyffe.main.views import (
    CollectionReportView, VideoYoutubeUploadView, key_from_s3url,
    SureLinkVideoView)
from wardenclyffe.streamlogs.models import StreamLog


class SimpleTest(TestCase):
    """ most of these tests are just about getting
    the absolute bare minimum of test coverage in place,
    hitting pages and just making sure they return the
    appropriate 200/302 status instead of generating a
    server error. *Real* tests can come later.
    """
    def setUp(self):
        self.u = UserFactory()
        self.u.set_password("bar")
        self.u.save()
        self.c = Client()

    def tearDown(self):
        self.u.delete()

    def test_index(self):
        response = self.c.get('/')
        self.assertEqual(response.status_code, 302)

        self.c.login(username=self.u.username, password="bar")
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)

    def test_smoke(self):
        self.c.get('/smoketest/')

    def test_dashboard(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_received_invalid(self):
        response = self.c.post("/received/")
        assert response.content == b"expecting a title"

    def test_received(self):
        response = self.c.post("/received/",
                               {'title': 'some title. not a uuid'})
        assert response.content == b"ok"

    def test_received_with_operation(self):
        o = OperationFactory()
        response = self.c.post("/received/",
                               {'title': str(o.uuid)})
        assert response.content == b"ok"

    def test_recent_operations(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/recent_operations/")
        self.assertEqual(response.status_code, 200)

    def test_upload_form(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/upload/")
        self.assertEqual(response.status_code, 200)

    def test_batch_upload_form(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/upload/batch/")
        self.assertEqual(response.status_code, 200)

    def test_upload_form_for_collection(self):
        c = CollectionFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/upload/")
        self.assertEqual(response.status_code, 200)
        response = self.c.get("/upload/?collection=%d" % c.id)
        self.assertEqual(response.status_code, 200)

    def test_upload_errors(self):
        # if we try to post without logging in, should get redirected
        response = self.c.post("/upload/post/")
        self.assertEqual(response.status_code, 302)

        self.c.login(username=self.u.username, password="bar")
        # GET should not work
        response = self.c.get("/upload/post/")
        self.assertEqual(response.status_code, 302)

        # invalid form
        response = self.c.post("/upload/post/")
        self.assertEqual(response.status_code, 302)

    def test_batch_upload_errors(self):
        # if we try to post without logging in, should get redirected
        response = self.c.post("/upload/batch/post/")
        self.assertEqual(response.status_code, 302)

        self.c.login(username=self.u.username, password="bar")
        # GET should not work
        response = self.c.get("/upload/batch/post/")
        self.assertEqual(response.status_code, 302)

        # invalid form
        response = self.c.post("/upload/batch/post/", dict(collection=1))
        self.assertEqual(response.status_code, 302)

    def test_subject_autocomplete(self):
        response = self.c.get("/api/subjectautocomplete/", dict(q="test"))
        self.assertEqual(response.status_code, 200)

    def test_uuid_search(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/uuid_search/", dict(uuid=f.video.uuid))
        self.assertEqual(response.status_code, 200)

    def test_uuid_search_empty(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/uuid_search/", dict(uuid=""))
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/search/", dict(q="test"))
        self.assertEqual(response.status_code, 200)

    def test_search_empty(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/search/", dict(q=""))
        self.assertEqual(response.status_code, 200)

    def test_file_filter(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get(
            "/file/filter/",
            dict(
                include_collection=f.video.collection.id,
            ))
        self.assertEqual(response.status_code, 200)

    def test_video_index(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/video/")
        self.assertEqual(response.status_code, 200)

    def test_video_index_nan(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/video/?page=foo")
        self.assertEqual(response.status_code, 200)

    def test_video_index_offtheend(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/video/?page=200")
        self.assertEqual(response.status_code, 200)

    def test_video_index_with_params(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/video/?creator=c&description=d&"
                              "language=l&subject=s&licence=l")
        self.assertEqual(response.status_code, 200)

    def test_file_index(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/file/")
        self.assertEqual(response.status_code, 200)

    def test_file_index_nan(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/file/?page=foo")
        self.assertEqual(response.status_code, 200)

    def test_file_index_offtheend(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/file/?page=200")
        self.assertEqual(response.status_code, 200)

    def test_file_index_with_params(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/file/?foo=bar")
        self.assertEqual(response.status_code, 200)

    def test_user_page(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/user/%s/" % self.u.username)
        self.assertEqual(response.status_code, 200)

    def test_collection_videos(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get(
            "/collection/%d/videos/" % f.video.collection.id)
        self.assertEqual(response.status_code, 200)

    def test_collection_videos_pagination_nan(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get(
            "/collection/%d/videos/?page=foo" % f.video.collection.id)
        self.assertEqual(response.status_code, 200)

    def test_collection_videos_pagination_offtheend(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get(
            "/collection/%d/videos/?page=200" % f.video.collection.id)
        self.assertEqual(response.status_code, 200)

    def test_collection_operations(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/collection/%d/operations/"
                              % f.video.collection.id)
        self.assertEqual(response.status_code, 200)

    def test_collection_page(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get(
            "/collection/%d/" % f.video.collection.id)
        self.assertEqual(response.status_code, 200)

    def test_slow_operations(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/slow_operations/")
        self.assertEqual(response.status_code, 200)

    def test_tagautocomplete(self):
        response = self.c.get("/api/tagautocomplete/?q=foo")
        self.assertEqual(response.status_code, 200)

    def test_subjectautocomplete(self):
        VideoFactory(title="thread")
        response = self.c.get("/api/subjectautocomplete/?q=thread")
        self.assertEqual(response.status_code, 200)

    def test_operation_info(self):
        o = OperationFactory()
        response = self.c.get("/operation/%s/info/" % o.uuid)
        self.assertEqual(response.status_code, 200)

    def test_flv_to_mp4_convert(self):
        v = VideoFactory()
        FileFactory(video=v, location_type="mediathread", label="mediathread")
        FileFactory(
            video=v, location_type="cuit", label="flv",
            filename=("/media/h264/ccnmtl/public/"
                      "courses/56d27944-4131-11e1-8164-0017f20ea192"
                      "-Mediathread_video_uploaded_by_mlp55.flv"))
        self.c.login(username=self.u.username, password="bar")
        response = self.c.post(reverse('video-flv-to-mp4', args=[v.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(v.has_mediathread_update())


class TestSurelink(TestCase):
    def setUp(self):
        self.u = UserFactory()
        self.u.set_password("bar")
        self.u.save()
        self.c = Client()
        self.c.login(username=self.u.username, password="bar")

    def test_surelink_form(self):
        response = self.c.get("/surelink/")
        self.assertEqual(response.status_code, 200)

    def test_surelink_with_files(self):
        response = self.c.get("/surelink/", dict(files="foo.mp4"))
        self.assertEqual(response.status_code, 200)

    def test_file_surelink_form(self):
        f = FileFactory()
        response = self.c.get("/file/%d/" % f.id)
        self.assertEqual(response.status_code, 200)

        response = self.c.get("/file/%d/surelink/" % f.id)
        self.assertEqual(response.status_code, 200)

    def test_file_surelink_public_stream(self):
        """ regression test for PMT #87084 """
        public_file = FileFactory(
            filename=("/media/h264/ccnmtl/public/"
                      "courses/56d27944-4131-11e1-8164-0017f20ea192"
                      "-Mediathread_video_uploaded_by_mlp55.mp4"))
        response = self.c.get("/file/%d/" % public_file.id)
        self.assertEqual(response.status_code, 200)

        response = self.c.get(
            "/file/%d/surelink/" % public_file.id,
            {'file': public_file.filename,
             'captions': '',
             'poster': ('https://wardenclyffe.ctl.columbia.edu/'
                        'uploads/images/11213/00000238.jpg'),
             'width': public_file.guess_width(),
             'height': public_file.guess_height(),
             'protection': 'mp4_public_stream',
             'authtype': '',
             'player': 'v4',
             })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "&lt;iframe")
        self.assertNotContains(response, "file=/media/h264/ccnmtl/")
        self.assertContains(response, "file=/course")

    def test_file_surelink_extra_chars_in_dimensions(self):
        """ regression test for PMT #87084 """
        public_file = FileFactory(
            filename=("/media/h264/ccnmtl/public/"
                      "courses/56d27944-4131-11e1-8164-0017f20ea192"
                      "-Mediathread_video_uploaded_by_mlp55.mp4"))
        response = self.c.get("/file/%d/" % public_file.id)
        self.assertEqual(response.status_code, 200)

        response = self.c.get(
            "/file/%d/surelink/" % public_file.id,
            {'file': public_file.filename,
             'captions': '',
             'poster': ('https://wardenclyffe.ctl.columbia.edu/'
                        'uploads/images/11213/00000238.jpg'),
             'width': "480-",
             'height': " 720 ",
             'protection': 'mp4_public_stream',
             'authtype': '',
             'player': 'v4',
             })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "&lt;iframe")
        self.assertNotContains(response, "file=/media/h264/ccnmtl/")
        self.assertContains(response, "file=/course")


class TestFeed(TestCase):
    def test_rss_feed(self):
        self.c = Client()
        f = FileFactory()
        response = self.c.get("/collection/%d/rss/" % f.video.collection.id)
        self.assertEqual(response.status_code, 200)


class TestStats(TestCase):
    def test_stats_page(self):
        self.c = Client()
        response = self.c.get("/stats/")
        self.assertEqual(response.status_code, 200)


class TestSignS3View(TestCase):
    def test_sign_s3(self):
        self.c = Client()
        with self.settings(
                AWS_ACCESS_KEY='',
                AWS_SECRET_KEY='',
                AWS_S3_UPLOAD_BUCKET=''):
            r = self.c.get(
                "/sign_s3/?s3_object_name=default_name&s3_object_type=foo")
            self.assertEqual(r.status_code, 200)
            j = json.loads(r.content)
            self.assertTrue('presigned_post_url' in j)


class TestStaff(TestCase):
    def setUp(self):
        self.u = UserFactory()
        self.u.set_password("bar")
        self.u.save()
        self.c = Client()
        self.c.login(username=self.u.username, password="bar")

    def test_most_recent_operation(self):
        o = OperationFactory()
        r = self.c.get("/most_recent_operation/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, str(o.modified.year))

    def test_most_recent_operation_empty(self):
        r = self.c.get("/most_recent_operation/")
        self.assertEqual(r.status_code, 200)

    def test_servers_empty(self):
        r = self.c.get("/server/")
        self.assertEqual(r.status_code, 200)

    def test_servers(self):
        s = ServerFactory()
        r = self.c.get("/server/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, s.name)
        self.assertContains(r, s.hostname)

    def test_server(self):
        s = ServerFactory()
        r = self.c.get(s.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, s.name)
        self.assertContains(r, s.hostname)

    def test_edit_server(self):
        s = ServerFactory()
        r = self.c.get(s.get_absolute_url() + "edit/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, s.name)
        self.assertContains(r, s.hostname)
        self.assertContains(r, '<form ')

    def test_delete_server(self):
        s = ServerFactory()
        # make sure it appears in the list
        r = self.c.get("/server/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, s.name)
        self.assertContains(r, s.hostname)
        # delete it
        r = self.c.post("/server/%d/delete/" % s.id, {})
        self.assertEqual(r.status_code, 302)
        # now it should be gone
        r = self.c.get("/server/")
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, s.name)
        self.assertNotContains(r, s.hostname)

    def test_delete_server_get(self):
        """ GET request should just be confirm form, not actually delete """
        s = ServerFactory()
        # make sure it appears in the list
        r = self.c.get("/server/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, s.name)
        self.assertContains(r, s.hostname)

        r = self.c.get("/server/%d/delete/" % s.id)
        self.assertEqual(r.status_code, 200)
        # it should not be gone
        r = self.c.get("/server/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, s.name)
        self.assertContains(r, s.hostname)

    def test_tags(self):
        r = self.c.get("/tag/")
        self.assertEqual(r.status_code, 200)

    def test_video(self):
        v = VideoFactory()
        r = self.c.get(v.get_absolute_url())
        self.assertEqual(r.status_code, 200)

    def test_delete_collection(self):
        c = CollectionFactory()
        r = self.c.get(c.get_absolute_url() + "delete/")
        self.assertEqual(r.status_code, 200)
        r = self.c.post(c.get_absolute_url() + "delete/")
        self.assertEqual(r.status_code, 302)

    def test_video_select_poster(self):
        i = ImageFactory()
        v = i.video
        r = self.c.get("/video/%d/select_poster/%d/" % (v.id, i.id))
        self.assertEqual(r.status_code, 302)

    def test_edit_collection(self):
        c = CollectionFactory()
        r = self.c.get(c.get_absolute_url() + "edit/")
        self.assertEqual(r.status_code, 200)
        r = self.c.post(c.get_absolute_url() + "edit/",
                        data=dict(title="updated title"))
        self.assertEqual(r.status_code, 302)

    def test_collection_toggle_active(self):
        c = CollectionFactory(active=True)
        r = self.c.post(c.get_absolute_url() + "toggle_active/")
        c = Collection.objects.get(id=c.id)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(c.active)
        r = self.c.post(c.get_absolute_url() + "toggle_active/")
        self.assertEqual(r.status_code, 302)
        c = Collection.objects.get(id=c.id)
        self.assertTrue(c.active)

    def test_edit_collection_audio(self):
        c = CollectionFactory(audio=False)
        r = self.c.post(reverse('collection-edit-audio', args=[c.id]),
                        dict(audio="1"))
        self.assertEqual(r.status_code, 302)
        c = Collection.objects.get(id=c.id)
        self.assertTrue(c.audio)
        r = self.c.post(reverse('collection-edit-audio', args=[c.id]),
                        dict(audio="0"))
        self.assertEqual(r.status_code, 302)
        c = Collection.objects.get(id=c.id)
        self.assertFalse(c.audio)

    def test_edit_collection_public(self):
        c = CollectionFactory(public=False)
        r = self.c.post(reverse('collection-edit-public', args=[c.id]),
                        dict(public="1"))
        self.assertEqual(r.status_code, 302)
        c = Collection.objects.get(id=c.id)
        self.assertTrue(c.public)
        r = self.c.post(reverse('collection-edit-public', args=[c.id]),
                        dict(public="0"))
        self.assertEqual(r.status_code, 302)
        c = Collection.objects.get(id=c.id)
        self.assertFalse(c.public)

    def test_add_server_form(self):
        r = self.c.get("/server/add/")
        self.assertEqual(r.status_code, 200)

    def test_add_server(self):
        r = self.c.post(
            "/server/add/",
            dict(name="foo", hostname="foo", credentials="foo",
                 description="foo", base_dir="/",
                 base_url="something", server_type="sftp"))
        self.assertEqual(r.status_code, 302)

    def test_add_server_invalid(self):
        r = self.c.post("/server/add/")
        self.assertEqual(r.status_code, 200)

    def test_edit_video_form(self):
        v = VideoFactory()
        r = self.c.get(v.get_absolute_url() + "edit/")
        self.assertEqual(r.status_code, 200)

    def test_remove_tag_from_collection(self):
        c = CollectionFactory()
        r = self.c.get(c.get_absolute_url() + "remove_tag/foo/")
        self.assertEqual(r.status_code, 200)
        r = self.c.get(c.get_absolute_url() + "remove_tag/foo/?ajax=1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, b"ok")

    def test_remove_tag_from_video(self):
        c = VideoFactory()
        r = self.c.get(c.get_absolute_url() + "remove_tag/foo/")
        self.assertEqual(r.status_code, 200)
        r = self.c.get(c.get_absolute_url() + "remove_tag/foo/?ajax=1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, b"ok")

    def test_tag(self):
        r = self.c.get("/tag/foo/")
        self.assertEqual(r.status_code, 200)

    def test_add_collection_form(self):
        r = self.c.get("/add_collection/")
        self.assertEqual(r.status_code, 200)

    def test_add_collection(self):
        r = self.c.post("/add_collection/", dict(title="new collection",
                                                 active="on"))
        self.assertEqual(r.status_code, 302)

    def test_add_collection_and_initialize(self):
        v = VideoFactory(title='alpha')
        r = self.c.post(
            "/add_collection/",
            dict(title="new collection", active="on", q="alpha"))
        self.assertEqual(r.status_code, 302)

        c = Collection.objects.get(title='new collection')
        self.assertEqual(c.video_set.first(), v)

    def test_operation(self):
        o = OperationFactory()
        response = self.c.get("/operation/%s/" % o.uuid)
        self.assertEqual(response.status_code, 200)

    def test_delete_file_form(self):
        f = FileFactory()
        response = self.c.get("/file/%d/delete/" % f.id)
        self.assertEqual(response.status_code, 200)

    def test_delete_file(self):
        f = FileFactory()
        response = self.c.post("/file/%d/delete/" % f.id)
        self.assertEqual(response.status_code, 302)

    def test_delete_video_form(self):
        f = VideoFactory()
        response = self.c.get("/video/%d/delete/" % f.id)
        self.assertEqual(response.status_code, 200)

    def test_delete_video(self):
        f = VideoFactory()
        response = self.c.post("/video/%d/delete/" % f.id)
        self.assertEqual(response.status_code, 302)

    def test_delete_operation_form(self):
        f = OperationFactory()
        response = self.c.get("/operation/%d/delete/" % f.id)
        self.assertEqual(response.status_code, 200)

    def test_delete_operation(self):
        f = OperationFactory()
        response = self.c.post("/operation/%d/delete/" % f.id)
        self.assertEqual(response.status_code, 302)

    def test_video_youtube_upload(self):
        factory = RequestFactory()
        v = VideoFactory()
        request = factory.post(
            "/video/%d/youtube/" % v.id,
            {})
        request.user = self.u
        view = VideoYoutubeUploadView.as_view()
        response = view(request, v.id)
        self.assertEqual(response.status_code, 302)

    def test_bulk_file_operation_form_empty(self):
        response = self.c.get(reverse('bulk-operation'))
        self.assertEqual(response.status_code, 200)

    def test_bulk_file_operation_form(self):
        v = VideoFactory()
        response = self.c.get(
            reverse('bulk-operation') + "?video_%d=on" % v.id)
        self.assertEqual(response.status_code, 200)

    def test_bulk_file_operation_surelink_empty(self):
        response = self.c.post(
            reverse('bulk-operation'),
            {'surelink': 'yes'})
        self.assertRedirects(response, reverse('bulk-surelink'))

    def test_bulk_file_operation_invalid(self):
        response = self.c.post(
            reverse('bulk-operation'))
        self.assertEqual(response.status_code, 400)

    def test_bulk_surelink_empty(self):
        r = self.c.get(reverse('bulk-surelink'))
        self.assertEqual(r.status_code, 200)

    def test_bulk_surelink_video_not_surelinkable(self):
        v = VideoFactory()
        r = self.c.get(reverse('bulk-surelink') + "?video_%d=on" % v.id)
        self.assertEqual(r.status_code, 200)

    def test_bulk_surelink_video_surelinkable(self):
        f = FileFactory()
        v = f.video
        r = self.c.get(reverse('bulk-surelink') + "?video_%d=on" % v.id)
        self.assertEqual(r.status_code, 200)

    def test_video_add_file_form(self):
        v = VideoFactory()
        response = self.c.get("/video/%d/add_file/" % v.id)
        self.assertEqual(response.status_code, 200)


confirmation_headers = {
    'HTTP_X_AMZ_SNS_MESSAGE_TYPE': 'SubscriptionConfirmation',
    'x-amz-sns-message-id': '165545c9-2a5c-472c-8df2-7ff2be2b3b1b',
    'x-amz-sns-topic-arn': 'arn:aws:sns:us-east-1:123456789012:MyTopic',
    'content_type': 'text/plain; charset=UTF-8',
    'User-Agent': 'Amazon Simple Notification Service Agent',
}

confirmation_body = """
{
  "Type" : "SubscriptionConfirmation",
  "MessageId" : "165545c9-2a5c-472c-8df2-7ff2be2b3b1b",
  "Token" : "2336412f37fb687f5d51e6e241d09",
  "TopicArn" : "arn:aws:sns:us-east-1:123456789012:MyTopic",
  "Message" : "You have chosen to subscribe to the topic arn:aws:sns:",
  "SubscribeURL" : "http://example.com/?Action=ConfirmSubscription",
  "Timestamp" : "2012-04-26T20:45:04.751Z",
  "SignatureVersion" : "1",
  "Signature" : "EXAMPLEpH+DcEwjAPg8O9mY8dReBSwksfg2S7WKQcikcNK+gLPoBc1Q=",
  "SigningCertURL" : "https://example.com/SimpleNotificationService.pem"
  }"""

notification_headers = {
    'HTTP_X_AMZ_SNS_MESSAGE_TYPE': 'Notification',
    'x-amz-sns-message-id': '165545c9-2a5c-472c-8df2-7ff2be2b3b1b',
    'x-amz-sns-topic-arn': 'arn:aws:sns:us-east-1:123456789012:MyTopic',
    'content_type': 'text/plain; charset=UTF-8',
    'User-Agent': 'Amazon Simple Notification Service Agent',
}


class SNSTest(TestCase):
    def setUp(self):
        self.c = Client()

    @httprettified
    def test_subscription_confirmation(self):
        HTTPretty.register_uri(
            HTTPretty.GET,
            "http://example.com/?Action=ConfirmSubscription",
            body="yes"
        )
        r = self.c.post(
            "/api/sns/",
            confirmation_body,
            **confirmation_headers
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, b"OK")
        self.assertEqual(httpretty.last_request().method, "GET")
        self.assertEqual(httpretty.last_request().path,
                         "/?Action=ConfirmSubscription")

    def test_subscription_confirmation_invalid_json(self):
        r = self.c.post(
            "/api/sns/",
            "{}",
            **confirmation_headers
        )
        self.assertEqual(r.status_code, 400)

    def test_sns_no_message_type(self):
        r = self.c.post(
            "/api/sns/",
            dict(),
        )
        self.assertEqual(r.status_code, 400)

    @override_settings(AWS_ET_720_PRESET="foo")
    def test_sns_success_notification(self):
        tf = FileFactory(
            location_type='transcode',
            cap="1411757335963-fyxugb",
        )
        o = OperationFactory(
            action="elastic transcode job",
            status="submitted")
        OperationFileFactory(operation=o, file=tf)

        r = self.c.post(
            "/api/sns/",
            open(os.path.join(os.path.dirname(__file__),
                              "notification_body.json")).read(),
            **notification_headers
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, b"OK")

        no = Operation.objects.get(id=o.id)
        self.assertEqual(no.status, 'complete')

        nf = File.objects.get(
            location_type='s3',
            label='transcoded 480p file (S3)')
        self.assertEqual(
            nf.cap,
            "2014/09/26/f3d2831b-11dd-409f-ad94-97a77e98922f_480.mp4")

    @override_settings(AWS_ET_720_PRESET="foo")
    def test_sns_success_notification_thumbnails(self):
        tf = FileFactory(
            location_type='transcode',
            cap="1432910411000-tfe2a2",
        )
        o = OperationFactory(
            action="elastic transcode job",
            status="submitted")
        OperationFileFactory(operation=o, file=tf)

        r = self.c.post(
            "/api/sns/",
            open(os.path.join(os.path.dirname(__file__),
                              "thumbnail_pattern.json")).read(),
            **notification_headers
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, b"OK")

        no = Operation.objects.get(id=o.id)
        self.assertEqual(no.status, 'complete')

        nf = File.objects.get(
            location_type='s3',
            label='transcoded 480p file (S3)')
        self.assertEqual(
            nf.cap,
            "2015/05/29/e573cfeb-e32c-45c0-8caa-326c394b04b9_480.mp4")


class TestKeyFromS3Url(TestCase):
    def test_simple(self):
        s3url = "https://s3.amazonaws.com/<bucket>/2016/02/29/f.mp4"
        self.assertEqual(
            key_from_s3url(s3url),
            "2016/02/29/f.mp4",
        )

    def test_known_failure(self):
        s3url = ("https://wardenclyffe-input-prod.s3.amazonaws.com/"
                 "2016/04/18/46d54344-d228-4315-83ed-c0361dcac47c.mp3")
        self.assertEqual(
            key_from_s3url(s3url),
            "2016/04/18/46d54344-d228-4315-83ed-c0361dcac47c.mp3",
        )


class FLVImportTest(TestCase):
    def setUp(self):
        self.u = UserFactory()
        self.u.set_password("bar")
        self.u.save()
        self.c = Client()
        self.c.login(username=self.u.username, password="bar")
        self.secure_collection = CollectionFactory()
        self.public_collection = CollectionFactory(public=True)

    def test_post(self):
        with self.settings(
                FLV_IMPORT_COLLECTION_ID=self.secure_collection.id,
                FLV_PUBLIC_IMPORT_COLLECTION_ID=self.public_collection.id):
            r = self.c.post(
                reverse("import-flv"),
                dict(flv="broadcast/secure/file.flv"))
            self.assertEqual(r.status_code, 302)
            # secure one should go to the right collection
            self.assertEqual(self.secure_collection.video_set.count(), 1)
            self.assertEqual(self.public_collection.video_set.count(), 0)
            # and a public one should also be routed properly
            r = self.c.post(
                reverse("import-flv"),
                dict(flv="broadcast/file.flv"))
            self.assertEqual(r.status_code, 302)
            self.assertEqual(self.secure_collection.video_set.count(), 1)
            self.assertEqual(self.public_collection.video_set.count(), 1)


class CollectionReportViewTest(TestCase):

    def test_cuit_filename(self):
        f = FileFactory()
        view = CollectionReportView()
        self.assertEqual(
            view.cuit_filename(f.video),
            ("56d27944-4131-11e1-8164-0017f20ea192"
             "-Mediathread_video_uploaded_by_mlp55.mp4"))

    def test_rows(self):
        f = FileFactory()
        FileFactory(location_type='panopto', video=f.video, filename='alpha')
        FileFactory(location_type='youtube', video=f.video,
                    url='http://www.youtube.com/watch?v=fS4qBPdhr8A')

        with self.settings(
            PANOPTO_LINK_URL='http://testserver/link/{}/',
                PANOPTO_EMBED_URL='http://testserver/embed/{}/'):
            view = CollectionReportView()
            rows = view.rows(f.video.collection)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], f.video.id)
            self.assertEqual(rows[0][1], 'test video')
            self.assertEqual(rows[0][2], 0)
            self.assertEqual(
                rows[0][3],
                'https://wardenclyffe.ctl.columbia.edu/video/{}/'.format(
                    f.video.id))
            self.assertEqual(
                rows[0][4],
                ("56d27944-4131-11e1-8164-0017f20ea192"
                 "-Mediathread_video_uploaded_by_mlp55.mp4"))
            self.assertEqual(rows[0][5], 'alpha')
            self.assertEqual(rows[0][6], 'http://testserver/link/alpha/')
            self.assertEqual(rows[0][7], 'http://testserver/embed/alpha/')
            self.assertEqual(
                rows[0][8], 'http://www.youtube.com/watch?v=fS4qBPdhr8A')
            self.assertEqual(
                rows[0][9], 'http://www.youtube.com/watch?v=fS4qBPdhr8A')


class MockSftpStatAttrs(object):

    def __init__(self, sz=700000):
        self.st_size = sz


class SureLinkVideoViewTest(TestCase):

    def test_get_context_data_bad_params(self):
        view = SureLinkVideoView()
        view.request = RequestFactory().get('/')

        ctx = view.get_context_data()
        self.assertEquals(len(ctx), 0)
        self.assertEquals(StreamLog.objects.count(), 0)

    def test_get_context_data_youtube(self):
        cuit = FileFactory()
        FileFactory(
            location_type='youtube', video=cuit.video,
            url='http://www.youtube.com/watch?v=fS4qBPdhr8A')

        view = SureLinkVideoView()
        view.request = RequestFactory().get('/', {'file': cuit.filename})
        ctx = view.get_context_data()
        self.assertEquals(
            ctx['youtube'], 'https://www.youtube.com/embed/fS4qBPdhr8A')
        self.assertEquals(
            StreamLog.objects.filter(filename=cuit.filename).count(), 1)

    def test_get_context_data_panopto(self):
        cuit = FileFactory()
        FileFactory(
            location_type='panopto', filename='alpha', video=cuit.video)

        view = SureLinkVideoView()
        view.request = RequestFactory().get('/', {'file': cuit.filename})
        ctx = view.get_context_data()
        self.assertEquals(ctx['panopto'], 'alpha')
        self.assertEquals(
            StreamLog.objects.filter(filename=cuit.filename).count(), 1)
