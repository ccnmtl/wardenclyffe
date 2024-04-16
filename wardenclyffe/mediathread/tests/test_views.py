from __future__ import unicode_literals

from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.test.utils import override_settings
import hmac
import hashlib
from django.conf import settings
from django.utils.encoding import smart_bytes
from wardenclyffe.mediathread.views import (
    MediathreadUploadFormView, s3_upload, VideoMediathreadSubmit,
    CollectionMediathreadSubmit)
from wardenclyffe.main.tests.factories import (
    UserFactory, CollectionFactory, VideoFactory)


class DummyCourseGetter(object):
    def run(self, *args, **kwargs):
        return []


class SubmitViewsTest(TestCase):
    def setUp(self):
        self.u = UserFactory()

    @override_settings(MEDIATHREAD_BASE="foo")
    def test_video_mediathread_submit_form(self):
        factory = RequestFactory()
        v = VideoFactory()
        request = factory.get("/video/%d/mediathread/" % v.id, {})
        request.user = self.u
        view = VideoMediathreadSubmit.as_view(
            course_getter=DummyCourseGetter,
        )
        response = view(request, v.id)
        self.assertEqual(response.status_code, 200)

    def test_video_mediathread_submit(self):
        factory = RequestFactory()
        v = VideoFactory()
        request = factory.post("/video/%d/mediathread/" % v.id, {})
        request.user = self.u
        view = VideoMediathreadSubmit.as_view(
            course_getter=DummyCourseGetter,
        )
        response = view(request, v.id)
        self.assertEqual(response.status_code, 302)

    @override_settings(MEDIATHREAD_BASE="foo")
    def test_collection_mediathread_submit_form(self):
        factory = RequestFactory()
        c = CollectionFactory()
        request = factory.get("/collection/%d/mediathread/" % c.id, {})
        request.user = self.u
        view = CollectionMediathreadSubmit.as_view(
            course_getter=DummyCourseGetter,
        )
        response = view(request, c.id)
        self.assertEqual(response.status_code, 200)

    def test_collection_mediathread_submit(self):
        factory = RequestFactory()
        c = CollectionFactory()
        request = factory.post("/collection/%d/mediathread/" % c.id, {})
        request.user = self.u
        view = CollectionMediathreadSubmit.as_view(
            course_getter=DummyCourseGetter,
        )
        response = view(request, c.id)
        self.assertEqual(response.status_code, 302)


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
        self.assertContains(response, "invalid authentication token")

    def test_upload_form(self):
        # make a correct one
        nonce = 'foobar'
        set_course = 'course_foo'
        username = 'foo'
        redirect_to = "http://www.example.com/"
        hmc = hmac.new(smart_bytes(settings.MEDIATHREAD_SECRET),
                       smart_bytes(
                           '%s:%s:%s' % (username, redirect_to, nonce)),
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
        self.assertNotContains(
            response,
            "invalid authentication token")


class TestS3Upload(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_video(self):
        u = UserFactory()
        c = CollectionFactory()
        s3url = "https://s3.amazonaws.com/f/2016/02/29/filename.mp4"
        r = self.factory.post(
            "/mediathread/",
            dict(s3_url=s3url, title="test video")
        )
        r.session = dict(username=u.username,
                         set_course="",
                         redirect_to="")
        with self.settings(MEDIATHREAD_COLLECTION_ID=c.id):
            response = s3_upload(r)
            self.assertEqual(response.status_code, 302)

    def test_audio(self):
        u = UserFactory()
        c = CollectionFactory()
        s3url = "https://s3.amazonaws.com/f/2016/02/29/filename.mp3"
        r = self.factory.post(
            "/mediathread/",
            dict(s3_url=s3url, title="test audio", audio=True)
        )
        r.session = dict(username=u.username,
                         set_course="",
                         redirect_to="")
        with self.settings(MEDIATHREAD_COLLECTION_ID=c.id):
            response = s3_upload(r)
            self.assertEqual(response.status_code, 302)


class TestInvalidUpload(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_bad_upload(self):
        request = self.factory.post(
            "/mediathread/",
            dict(tmpfilename=''))
        request.session = dict(username='foo', set_course='bar')
        response = MediathreadUploadFormView.as_view()(request)
        self.assertContains(response, "Bad file upload. Please try again.")


class TestInvalidSessions(TestCase):
    def setUp(self):
        self.c = Client()

    def test_no_session(self):
        r = self.c.post("/mediathread/", {})
        self.assertContains(r, "invalid session")
