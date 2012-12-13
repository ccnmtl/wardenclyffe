from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from wardenclyffe.main.models import Collection, Video, File
import uuid


class SimpleText(TestCase):
    def setUp(self):
        self.u = User.objects.create(username="foo")
        self.u.set_password("bar")
        self.u.save()
        self.c = Client()

    def tearDown(self):
        self.u.delete()

    def test_index(self):
        response = self.c.get('/')
        self.assertEquals(response.status_code, 302)

        self.c.login(username="foo", password="bar")
        response = self.c.get('/')
        self.assertEquals(response.status_code, 200)

    def test_dashboard(self):
        self.c.login(username="foo", password="bar")
        response = self.c.get("/dashboard/")
        self.assertEquals(response.status_code, 200)

    def test_received_invalid(self):
        response = self.c.post("/received/")
        assert response.content == "expecting a title"

    def test_received(self):
        response = self.c.post("/received/",
                               {'title': 'some title. not a uuid'})
        assert response.content == "ok"

    def test_recent_operations(self):
        self.c.login(username="foo", password="bar")
        response = self.c.get("/recent_operations/")
        self.assertEquals(response.status_code, 200)

    def test_upload_form(self):
        self.c.login(username="foo", password="bar")
        response = self.c.get("/upload/")
        self.assertEquals(response.status_code, 200)

        response = self.c.get("/scan_directory/")
        self.assertEquals(response.status_code, 200)

    def test_upload_errors(self):
        # if we try to post without logging in, should get redirected
        response = self.c.post("/upload/post/")
        self.assertEquals(response.status_code, 302)

        self.c.login(username="foo", password="bar")
        # GET should not work
        response = self.c.get("/upload/post/")
        self.assertEquals(response.status_code, 302)

        # invalid form
        response = self.c.post("/upload/post/")
        self.assertEquals(response.status_code, 302)


class TestSurelink(TestCase):
    def setUp(self):
        self.u = User.objects.create(username="foo")
        self.u.set_password("bar")
        self.u.save()
        self.c = Client()
        self.c.login(username="foo", password="bar")
        self.collection = Collection.objects.create(
            title="Mediathread Spring 2012",
            uuid=uuid.uuid4())
        self.video = Video.objects.create(collection=self.collection,
                                          title="test video",
                                          creator="anp8",
                                          uuid=uuid.uuid4())
        self.file = File.objects.create(
            video=self.video,
            label="CUIT File",
            location_type="cuit",
            filename=("/media/h264/ccnmtl/secure/"
                      "courses/56d27944-4131-11e1-8164-0017f20ea192"
                      "-Mediathread_video_uploaded_by_mlp55.mp4"),
            )

    def tearDown(self):
        self.u.delete()

    def test_surelink_form(self):
        response = self.c.get("/surelink/")
        self.assertEquals(response.status_code, 200)

    def test_file_surelink_form(self):
        response = self.c.get("/file/%d/" % self.file.id)
        self.assertEquals(response.status_code, 200)

        response = self.c.get("/file/%d/surelink/" % self.file.id)
        self.assertEquals(response.status_code, 200)
