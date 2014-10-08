from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import Client
from wardenclyffe.main.models import (
    Collection, Operation, File)
from factories import (
    FileFactory, OperationFactory, ServerFactory,
    UserFactory, VideoFactory, CollectionFactory,
    ImageFactory, OperationFileFactory)
from httpretty import HTTPretty, httprettified
import os.path
import httpretty


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
        self.assertEquals(response.status_code, 302)

        self.c.login(username=self.u.username, password="bar")
        response = self.c.get('/')
        self.assertEquals(response.status_code, 200)

    def test_smoke(self):
        response = self.c.get('/smoketest/')
        self.assertEquals(response.status_code, 200)

    def test_dashboard(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/dashboard/")
        self.assertEquals(response.status_code, 200)

    def test_received_invalid(self):
        response = self.c.post("/received/")
        assert response.content == "expecting a title"

    def test_received(self):
        response = self.c.post("/received/",
                               {'title': 'some title. not a uuid'})
        assert response.content == "ok"

    def test_received_with_operation(self):
        o = OperationFactory()
        response = self.c.post("/received/",
                               {'title': str(o.uuid)})
        assert response.content == "ok"

    def test_recent_operations(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/recent_operations/")
        self.assertEquals(response.status_code, 200)

    def test_upload_form(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/upload/")
        self.assertEquals(response.status_code, 200)

        response = self.c.get("/scan_directory/")
        self.assertEquals(response.status_code, 200)

    def test_batch_upload_form(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/upload/batch/")
        self.assertEquals(response.status_code, 200)

    def test_upload_form_for_collection(self):
        c = CollectionFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/upload/")
        self.assertEquals(response.status_code, 200)
        response = self.c.get("/upload/?collection=%d" % c.id)
        self.assertEquals(response.status_code, 200)

        response = self.c.get("/scan_directory/")
        self.assertEquals(response.status_code, 200)
        response = self.c.get("/scan_directory/?collection=%d" % c.id)
        self.assertEquals(response.status_code, 200)

    def test_upload_errors(self):
        # if we try to post without logging in, should get redirected
        response = self.c.post("/upload/post/")
        self.assertEquals(response.status_code, 302)

        self.c.login(username=self.u.username, password="bar")
        # GET should not work
        response = self.c.get("/upload/post/")
        self.assertEquals(response.status_code, 302)

        # invalid form
        response = self.c.post("/upload/post/")
        self.assertEquals(response.status_code, 302)

    def test_batch_upload_errors(self):
        # if we try to post without logging in, should get redirected
        response = self.c.post("/upload/batch/post/")
        self.assertEquals(response.status_code, 302)

        self.c.login(username=self.u.username, password="bar")
        # GET should not work
        response = self.c.get("/upload/batch/post/")
        self.assertEquals(response.status_code, 302)

        # invalid form
        response = self.c.post("/upload/batch/post/")
        self.assertEquals(response.status_code, 302)

    def test_subject_autocomplete(self):
        response = self.c.get("/api/subjectautocomplete/", dict(q="test"))
        self.assertEquals(response.status_code, 200)

    def test_uuid_search(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/uuid_search/", dict(uuid=f.video.uuid))
        self.assertEquals(response.status_code, 200)

    def test_uuid_search_empty(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/uuid_search/", dict(uuid=""))
        self.assertEquals(response.status_code, 200)

    def test_search(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/search/", dict(q="test"))
        self.assertEquals(response.status_code, 200)

    def test_search_empty(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/search/", dict(q=""))
        self.assertEquals(response.status_code, 200)

    def test_file_filter(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get(
            "/file/filter/",
            dict(
                include_collection=f.video.collection.id,
            ))
        self.assertEquals(response.status_code, 200)

    def test_video_index(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/video/")
        self.assertEquals(response.status_code, 200)

    def test_video_index_nan(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/video/?page=foo")
        self.assertEquals(response.status_code, 200)

    def test_video_index_offtheend(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/video/?page=200")
        self.assertEquals(response.status_code, 200)

    def test_video_index_with_params(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/video/?creator=c&description=d&"
                              "language=l&subject=s&licence=l")
        self.assertEquals(response.status_code, 200)

    def test_file_index(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/file/")
        self.assertEquals(response.status_code, 200)

    def test_file_index_nan(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/file/?page=foo")
        self.assertEquals(response.status_code, 200)

    def test_file_index_offtheend(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/file/?page=200")
        self.assertEquals(response.status_code, 200)

    def test_file_index_with_params(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/file/?foo=bar")
        self.assertEquals(response.status_code, 200)

    def test_user_page(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/user/%s/" % self.u.username)
        self.assertEquals(response.status_code, 200)

    def test_collection_videos(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get(
            "/collection/%d/videos/" % f.video.collection.id)
        self.assertEquals(response.status_code, 200)

    def test_collection_videos_pagination_nan(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get(
            "/collection/%d/videos/?page=foo" % f.video.collection.id)
        self.assertEquals(response.status_code, 200)

    def test_collection_videos_pagination_offtheend(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get(
            "/collection/%d/videos/?page=200" % f.video.collection.id)
        self.assertEquals(response.status_code, 200)

    def test_collection_operations(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/collection/%d/operations/"
                              % f.video.collection.id)
        self.assertEquals(response.status_code, 200)

    def test_collection_page(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get(
            "/collection/%d/" % f.video.collection.id)
        self.assertEquals(response.status_code, 200)

    def test_slow_operations(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/slow_operations/")
        self.assertEquals(response.status_code, 200)

    def test_tagautocomplete(self):
        response = self.c.get("/api/tagautocomplete/?q=foo")
        self.assertEquals(response.status_code, 200)

    def test_subjectautocomplete(self):
        VideoFactory(title="thread")
        response = self.c.get("/api/subjectautocomplete/?q=thread")
        self.assertEquals(response.status_code, 200)

    def test_operation_info(self):
        o = OperationFactory()
        response = self.c.get("/operation/%s/info/" % o.uuid)
        self.assertEqual(response.status_code, 200)

    def test_posterdone(self):
        o = OperationFactory()
        response = self.c.post("/posterdone/", dict(title=str(o.uuid)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "ok")

    def test_posterdone_empty(self):
        response = self.c.post("/posterdone/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "expecting a title")

    def test_posterdone_nonexistant(self):
        response = self.c.post("/posterdone/", dict(title="some-bad-uuid"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "ok")

    def test_done(self):
        o = OperationFactory()
        response = self.c.post("/done/", dict(title=str(o.uuid)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "ok")

    def test_done_no_title(self):
        response = self.c.post("/done/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "expecting a title")

    def test_done_nonexistant(self):
        response = self.c.post("/done/", dict(title="some-bad-uuid"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,
                         "could not find an operation with that UUID")


class TestSurelink(TestCase):
    def setUp(self):
        self.u = UserFactory()
        self.u.set_password("bar")
        self.u.save()
        self.c = Client()
        self.c.login(username=self.u.username, password="bar")

    def test_surelink_form(self):
        response = self.c.get("/surelink/")
        self.assertEquals(response.status_code, 200)

    def test_surelink_with_files(self):
        response = self.c.get("/surelink/", dict(files="foo.mp4"))
        self.assertEquals(response.status_code, 200)

    def test_file_surelink_form(self):
        f = FileFactory()
        response = self.c.get("/file/%d/" % f.id)
        self.assertEquals(response.status_code, 200)

        response = self.c.get("/file/%d/surelink/" % f.id)
        self.assertEquals(response.status_code, 200)

    def test_file_surelink_public_stream(self):
        """ regression test for PMT #87084 """
        public_file = FileFactory(
            filename=("/media/h264/ccnmtl/public/"
                      "courses/56d27944-4131-11e1-8164-0017f20ea192"
                      "-Mediathread_video_uploaded_by_mlp55.mp4"))
        response = self.c.get("/file/%d/" % public_file.id)
        self.assertEquals(response.status_code, 200)

        response = self.c.get(
            "/file/%d/surelink/" % public_file.id,
            {'file': public_file.filename,
             'captions': '',
             'poster': ('http://wardenclyffe.ccnmtl.columbia.edu/'
                        'uploads/images/11213/00000238.jpg'),
             'width': public_file.guess_width(),
             'height': public_file.guess_height(),
             'protection': 'mp4_public_stream',
             'authtype': '',
             'player': 'v4',
             })
        self.assertEquals(response.status_code, 200)
        assert "&lt;iframe" in response.content
        assert "file=/media/h264/ccnmtl/" not in response.content
        assert "file=/course" in response.content


class TestFeed(TestCase):
    def test_rss_feed(self):
        self.c = Client()
        f = FileFactory()
        response = self.c.get("/collection/%d/rss/" % f.video.collection.id)
        self.assertEquals(response.status_code, 200)


class TestStats(TestCase):
    def test_stats_page(self):
        self.c = Client()
        response = self.c.get("/stats/")
        self.assertEquals(response.status_code, 200)


class TestUploadify(TestCase):
    def test_uploadify(self):
        self.c = Client()
        response = self.c.post("/uploadify/", {})
        self.assertEqual(response.status_code, 200)


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
        self.assertTrue(str(o.modified.year) in r.content)

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
        self.assertTrue(s.name in r.content)
        self.assertTrue(s.hostname in r.content)

    def test_server(self):
        s = ServerFactory()
        r = self.c.get(s.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(s.name in r.content)
        self.assertTrue(s.hostname in r.content)

    def test_edit_server(self):
        s = ServerFactory()
        r = self.c.get(s.get_absolute_url() + "edit/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(s.name in r.content)
        self.assertTrue(s.hostname in r.content)
        self.assertTrue("<form " in r.content)

    def test_delete_server(self):
        s = ServerFactory()
        # make sure it appears in the list
        r = self.c.get("/server/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(s.name in r.content)
        self.assertTrue(s.hostname in r.content)
        # delete it
        r = self.c.post("/server/%d/delete/" % s.id, {})
        self.assertEqual(r.status_code, 302)
        # now it should be gone
        r = self.c.get("/server/")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(s.name in r.content)
        self.assertFalse(s.hostname in r.content)

    def test_delete_server_get(self):
        """ GET request should just be confirm form, not actually delete """
        s = ServerFactory()
        # make sure it appears in the list
        r = self.c.get("/server/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(s.name in r.content)
        self.assertTrue(s.hostname in r.content)

        r = self.c.get("/server/%d/delete/" % s.id)
        self.assertEqual(r.status_code, 200)
        # it should not be gone
        r = self.c.get("/server/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(s.name in r.content)
        self.assertTrue(s.hostname in r.content)

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

    def test_edit_collection_workflows_form(self):
        c = CollectionFactory()
        r = self.c.get(c.get_absolute_url() + "workflows/")
        self.assertEqual(r.status_code, 200)

    def test_edit_collection_workflows(self):
        c = CollectionFactory()
        r = self.c.post(c.get_absolute_url() + "workflows/")
        self.assertEqual(r.status_code, 302)

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
        self.assertEqual(r.content, "ok")

    def test_remove_tag_from_video(self):
        c = VideoFactory()
        r = self.c.get(c.get_absolute_url() + "remove_tag/foo/")
        self.assertEqual(r.status_code, 200)
        r = self.c.get(c.get_absolute_url() + "remove_tag/foo/?ajax=1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, "ok")

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

    def test_video_pcp_submit_form(self):
        v = VideoFactory()
        response = self.c.get("/video/%d/pcp_submit/" % v.id)
        self.assertEqual(response.status_code, 200)

    def test_video_pcp_submit(self):
        v = VideoFactory()
        response = self.c.post("/video/%d/pcp_submit/" % v.id)
        self.assertEqual(response.status_code, 302)

    def test_file_pcp_submit_form(self):
        v = FileFactory()
        response = self.c.get("/file/%d/submit_to_workflow/" % v.id)
        self.assertEqual(response.status_code, 200)

    def test_file_pcp_submit(self):
        v = FileFactory()
        response = self.c.post("/file/%d/submit_to_workflow/" % v.id)
        self.assertEqual(response.status_code, 302)

    def test_bulk_file_operation_form(self):
        response = self.c.get("/bulk_file_operation/")
        self.assertEqual(response.status_code, 200)

    def test_bulk_file_operation(self):
        response = self.c.post("/bulk_file_operation/")
        self.assertEqual(response.status_code, 302)

    def test_video_add_file_form(self):
        v = VideoFactory()
        response = self.c.get("/video/%d/add_file/" % v.id)
        self.assertEqual(response.status_code, 200)

    def test_list_workflows(self):
        response = self.c.get("/list_workflows/")
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
        self.assertEqual(r.content, "OK")
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
        self.assertEqual(r.content, "OK")

        no = Operation.objects.get(id=o.id)
        self.assertEqual(no.status, 'complete')

        nf = File.objects.get(
            location_type='s3',
            label='transcoded 480p file (S3)')
        self.assertEqual(
            nf.cap,
            "2014/09/26/f3d2831b-11dd-409f-ad94-97a77e98922f_480.mp4")
