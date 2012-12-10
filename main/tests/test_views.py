from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User


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
