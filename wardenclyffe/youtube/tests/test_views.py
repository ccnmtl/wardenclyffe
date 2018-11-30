from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from wardenclyffe.main.tests.factories import (
    UserFactory, CollectionFactory
)


class ViewTest(TestCase):
    def setUp(self):
        u = UserFactory()
        u.set_password("foo")
        u.save()
        self.c = Client()
        self.c.login(username=u.username, password="foo")

    def test_form(self):
        r = self.c.get(reverse('youtube-upload-form'))
        self.assertEqual(r.status_code, 200)

    def test_done(self):
        r = self.c.get(reverse('youtube-done'))
        self.assertEqual(r.status_code, 200)

    def test_post(self):
        CollectionFactory(title='Youtube')
        s3url = "https://s3.amazonaws.com/<bucket>/2016/02/29/f.mp4"
        r = self.c.post(reverse('youtube-post'), {"s3_url": s3url})
        self.assertEqual(r.status_code, 302)
