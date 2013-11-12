from django.test import TestCase
from django.test.client import Client
from factories import FileFactory
from factories import OperationFactory
from factories import ServerFactory
from factories import UserFactory
from factories import VideoFactory
from factories import CollectionFactory


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

    def test_subject_autocomplete(self):
        response = self.c.get("/api/subjectautocomplete/", dict(q="test"))
        self.assertEquals(response.status_code, 200)

    def test_uuid_search(self):
        f = FileFactory()
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/uuid_search/", dict(uuid=f.video.uuid))
        self.assertEquals(response.status_code, 200)

    def test_search(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/search/", dict(q="test"))
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

    def test_file_index(self):
        self.c.login(username=self.u.username, password="bar")
        response = self.c.get("/file/")
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
