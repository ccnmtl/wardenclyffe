from django.test import TestCase, RequestFactory
from django.test.client import Client
from wardenclyffe.main.tests.factories import UserFactory
import hmac
import hashlib
from django.conf import settings
from wardenclyffe.mediathread.views import mediathread_post


class SimpleTest(TestCase):
    def setUp(self):
        self.u = UserFactory(username="foo")
        self.u.set_password("bar")
        self.u.save()
        self.c = Client()

    def tearDown(self):
        self.u.delete()

    def test_invalid_auth(self):
        response = self.c.get("/mediathread/")
        self.assertEquals(
            response.content,
            "invalid authentication token")

    def test_upload_form(self):
        # make a correct one
        nonce = 'foobar'
        set_course = 'course_foo'
        username = 'foo'
        redirect_to = "http://www.example.com/"
        hmc = hmac.new(settings.MEDIATHREAD_SECRET,
                       '%s:%s:%s' % (username, redirect_to, nonce),
                       hashlib.sha1
                       ).hexdigest()

        response = self.c.get(
            "/mediathread/",
            {
                'nonce': nonce,
                'as': username,
                'redirect_url': redirect_to,
                'set_course': set_course,
                'hmac': hmc
            }
        )
        self.assertNotEquals(
            response.content,
            "invalid authentication token")


class TestInvalidUpload(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_bad_upload(self):
        request = self.factory.post(
            "/mediathread/post",
            dict(tmpfilename=''))
        request.session = dict(username='foo', set_course='bar')
        response = mediathread_post(request)
        self.assertEqual(response.content,
                         "Bad file upload. Please try again.")


class TestInvalidSessions(TestCase):
    def setUp(self):
        self.c = Client()

    def test_get(self):
        r = self.c.get("/mediathread/post/")
        self.assertEqual(r.content, "post only")

    def test_no_session(self):
        r = self.c.post("/mediathread/post/", {})
        self.assertEqual(r.content, "invalid session")
