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
