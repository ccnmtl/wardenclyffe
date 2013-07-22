from django.test import TestCase
from django.test.client import Client
from wardenclyffe.main.tests.factories import UserFactory


class ViewTest(TestCase):
    def setUp(self):
        u = UserFactory()
        u.set_password("foo")
        u.save()
        self.c = Client()
        self.c.login(username=u.username, password="foo")

    def test_form(self):
        r = self.c.get("/youtube/")
        self.assertEqual(r.status_code, 200)

    def test_done(self):
        r = self.c.get("/youtube/done/")
        self.assertEqual(r.status_code, 200)

    def test_post(self):
        r = self.c.post("/youtube/post/", {"tmpfilename": "foo.mp4"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, "no tmpfilename parameter set")
