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
