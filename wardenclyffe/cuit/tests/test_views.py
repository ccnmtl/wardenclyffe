from django.test import TestCase
from django.test.client import Client
from wardenclyffe.main.tests.factories import UserFactory
from wardenclyffe.main.tests.factories import CollectionFactory


class ViewTest(TestCase):
    def setUp(self):
        u = UserFactory()
        u.set_password("foo")
        u.save()
        self.c = Client()
        self.c.login(username=u.username, password="foo")

    def test_broken_quicktime(self):
        c = CollectionFactory()
        with self.settings(QUICKTIME_IMPORT_COLLECTION_ID=c.id):
            r = self.c.get("/cuit/broken_quicktime/")
            self.assertEqual(r.status_code, 200)
