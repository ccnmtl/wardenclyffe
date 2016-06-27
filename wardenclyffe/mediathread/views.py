# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import View
from wardenclyffe.main.models import Video, Collection
from wardenclyffe.main.views import key_from_s3url
from django.contrib.auth.models import User
import wardenclyffe.main.tasks as maintasks
import uuid
from django.conf import settings
from django.db import transaction
from restclient import GET
from json import loads
import hmac
import hashlib
from django_statsd.clients import statsd


class MediathreadAuthenticator(object):
    def __init__(self, request):
        self.nonce = request.GET.get('nonce', '')
        self.hmc = request.GET.get('hmac', '')
        self.set_course = request.GET.get('set_course', '')
        self.username = request.GET.get('as')
        self.redirect_to = request.GET.get('redirect_url', '')

    def is_valid(self):
        verify = hmac.new(
            settings.MEDIATHREAD_SECRET,
            '%s:%s:%s' % (self.username, self.redirect_to,
                          self.nonce),
            hashlib.sha1
        ).hexdigest()
        return verify == self.hmc


def mediathread(request):
    # check their credentials
    authenticator = MediathreadAuthenticator(request)
    if not authenticator.is_valid():
        statsd.incr("mediathread.auth_failure")
        return HttpResponse("invalid authentication token")

    username = authenticator.username
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create(username=username)
        statsd.incr("mediathread.user_created")

    request.session['username'] = username
    request.session['set_course'] = authenticator.set_course
    request.session['nonce'] = authenticator.nonce
    request.session['redirect_to'] = authenticator.redirect_to
    request.session['hmac'] = authenticator.hmc
    # either 'audio' or 'audio2' are accepted for now
    # for backwards-compatibility. going forward,
    # 'audio2' will be deprecated
    audio2 = request.GET.get('audio2', False)
    audio = request.GET.get('audio', False) or audio2
    template = 'mediathread/mediathread.html'
    return render(
        request, template,
        dict(username=username, user=user, audio=audio))


@transaction.non_atomic_requests
def mediathread_post(request):
    if request.method != "POST":
        return HttpResponse("post only")

    # we see this now and then, probably due to browser plugins
    # that provide "privacy" by stripping session cookies off
    # requests. we really don't have any way of handling
    # the upload if we can't maintain a session, so bail.
    if 'username' not in request.session \
            or 'set_course' not in request.session:
        return HttpResponse("invalid session")

    return s3_upload(request)


def s3_upload(request):
    s3url = request.POST.get('s3_url')
    if s3url is None:
        return HttpResponse("Bad file upload. Please try again.")

    # backwards compatibility: allow 'audio' or 'audio2'
    audio2 = request.POST.get('audio2', False)
    audio = request.POST.get('audio', False) or audio2
    operations = []
    vuuid = uuid.uuid4()
    statsd.incr("mediathread.mediathread")
    key = key_from_s3url(s3url)
    # make db entry
    try:
        collection = Collection.objects.get(
            id=settings.MEDIATHREAD_COLLECTION_ID)
        v = Video.objects.create(collection=collection,
                                 title=request.POST.get('title', ''),
                                 creator=request.session['username'],
                                 uuid=vuuid)
        v.make_source_file(key)
        # we make a "mediathreadsubmit" file to store the submission
        # info and serve as a flag that it needs to be submitted
        # (when Elastic Transcoder comes back)
        user = User.objects.get(username=request.session['username'])
        v.make_mediathread_submit_file(
            key, user, request.session['set_course'],
            request.session['redirect_to'], audio=audio,
        )

        v.make_uploaded_source_file(key, audio=audio)
        if audio:
            operations = [v.make_local_audio_encode_operation(
                key, user=user)]
        else:
            operations = [
                v.make_pull_from_s3_and_extract_metadata_operation(
                    key=key, user=user),
                v.make_create_elastic_transcoder_job_operation(
                    key=key, user=user)]
    except:
        statsd.incr("mediathread.mediathread.failure")
        raise
    else:
        # hand operations off to celery
        for o in operations:
            maintasks.process_operation.delay(o.id)
        return HttpResponseRedirect(request.session['redirect_to'])
    return HttpResponse("Bad file upload. Please try again.")


def mediathread_url(username):
    return (settings.MEDIATHREAD_BASE + "/api/user/courses?secret=" +
            settings.MEDIATHREAD_SECRET + "&user=" +
            username)


class MediathreadCourseGetter(object):
    def run(username):
        try:
            url = mediathread_url(username)
            credentials = None
            if hasattr(settings, "MEDIATHREAD_CREDENTIALS"):
                credentials = settings.MEDIATHREAD_CREDENTIALS
            response = GET(url, credentials=credentials)
            courses = loads(response)['courses']
            courses = [dict(id=k, title=v['title'])
                       for (k, v) in courses.items()]
            courses.sort(key=lambda x: x['title'].lower())
        except:
            courses = []
        return courses


def submit_video_to_mediathread(video, user, course):
    statsd.incr("mediathread.submit")
    video.make_mediathread_submit_file(
        video.filename(), user,
        course,
        redirect_to="",
        audio=video.is_audio_file())
    operations = video.handle_mediathread_submit()
    for o in operations:
        maintasks.process_operation.delay(o)
    video.clear_mediathread_submit()


class AuthenticatedNonAtomic(object):
    @method_decorator(login_required)
    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, *args, **kwargs):
        return super(AuthenticatedNonAtomic, self).dispatch(*args, **kwargs)


class VideoMediathreadSubmit(AuthenticatedNonAtomic, View):
    template_name = 'mediathread/mediathread_submit.html'
    course_getter = MediathreadCourseGetter

    def get(self, request, id):
        video = get_object_or_404(Video, id=id)
        courses = self.course_getter().run(request.user.username)
        return render(request, self.template_name,
                      dict(video=video, courses=courses,
                           mediathread_base=settings.MEDIATHREAD_BASE))

    def post(self, request, id):
        video = get_object_or_404(Video, id=id)
        submit_video_to_mediathread(video, request.user,
                                    request.POST.get('course', ''))
        return HttpResponseRedirect(video.get_absolute_url())


class CollectionMediathreadSubmit(AuthenticatedNonAtomic, View):
    template_name = 'mediathread/collection_mediathread_submit.html'
    course_getter = MediathreadCourseGetter

    def get(self, request, pk):
        collection = get_object_or_404(Collection, id=pk)
        courses = self.course_getter().run(request.user.username)
        return render(request, self.template_name,
                      dict(collection=collection, courses=courses,
                           mediathread_base=settings.MEDIATHREAD_BASE))

    def post(self, request, pk):
        collection = get_object_or_404(Collection, id=pk)
        for video in collection.video_set.all():
            submit_video_to_mediathread(video, request.user,
                                        request.POST.get('course', ''))
        return HttpResponseRedirect(collection.get_absolute_url())
