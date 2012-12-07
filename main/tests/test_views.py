from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User


class SimpleText(TestCase):
    def setUp(self):
        self.u = User.objects.create(username="foo")
        self.u.set_password("bar")
        self.u.save()

    def tearDown(self):
        self.u.delete()

    def test_index(self):
        c = Client()
        response = c.get('/')
        self.assertEquals(response.status_code, 302)

        c.login(username="foo", password="bar")
        response = c.get('/')
        self.assertEquals(response.status_code, 200)
