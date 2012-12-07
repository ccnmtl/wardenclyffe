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
