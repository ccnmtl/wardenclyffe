# Create your views here.
from annoying.decorators import render_to
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from wardenclyffe.main.models import Video, Operation, Collection
from django.contrib.auth.models import User
import uuid
import wardenclyffe.main.tasks as maintasks
import os
from django.conf import settings
from django.db import transaction
from restclient import GET
from json import loads, dumps
import hmac
import hashlib
from django_statsd.clients import statsd


@render_to('mediathread/mediathread.html')
def mediathread(request):
    # check their credentials
    nonce = request.GET.get('nonce', '')
    hmc = request.GET.get('hmac', '')
    set_course = request.GET.get('set_course', '')
    username = request.GET.get('as')
    redirect_to = request.GET.get('redirect_url', '')
    verify = hmac.new(settings.MEDIATHREAD_SECRET,
                      '%s:%s:%s' % (username, redirect_to, nonce),
                      hashlib.sha1
                      ).hexdigest()
    if verify != hmc:
        statsd.incr("mediathread.auth_failure")
        return HttpResponse("invalid authentication token")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create(username=username)
        statsd.incr("mediathread.user_created")

    request.session['username'] = username
    request.session['set_course'] = set_course
    request.session['nonce'] = nonce
    request.session['redirect_to'] = redirect_to
    request.session['hmac'] = hmc
    audio = request.GET.get('audio', False)
    audio2 = request.GET.get('audio2', False)
    return dict(username=username, user=user,
                audio=audio or audio2,
                audio2=audio2,
                )


def select_workflow(audio, audio2):
    if audio:
        if hasattr(settings, 'MEDIATHREAD_AUDIO_PCP_WORKFLOW'):
            return settings.MEDIATHREAD_AUDIO_PCP_WORKFLOW
    if audio2:
        if hasattr(settings, 'MEDIATHREAD_AUDIO_PCP_WORKFLOW2'):
            return settings.MEDIATHREAD_AUDIO_PCP_WORKFLOW2
    return None


@transaction.commit_manually
def mediathread_post(request):
    if request.method != "POST":
        transaction.commit()
        return HttpResponse("post only")

    # we see this now and then, probably due to browser plugins
    # that provide "privacy" by stripping session cookies off
    # requests. we really don't have any way of handling
    # the upload if we can't maintain a session, so bail.
    if 'username' not in request.session \
            or 'set_course' not in request.session:
        transaction.commit()
        return HttpResponse("invalid session")

    tmpfilename = request.POST.get('tmpfilename', '')
    audio = request.POST.get('audio', False)
    audio2 = request.POST.get('audio2', False)
    operations = []
    params = []
    if tmpfilename.startswith(settings.TMP_DIR):
        statsd.incr("mediathread.mediathread")
        filename = os.path.basename(tmpfilename)
        vuuid = os.path.splitext(filename)[0]
        # make db entry
        try:
            collection = Collection.objects.get(
                id=settings.MEDIATHREAD_COLLECTION_ID)
            v = Video.objects.create(collection=collection,
                                     title=request.POST.get('title', ''),
                                     creator=request.session['username'],
                                     uuid=vuuid)
            source_file = v.make_source_file(filename)
            # we make a "mediathreadsubmit" file to store the submission
            # info and serve as a flag that it needs to be submitted
            # (when PCP comes back)
            user = User.objects.get(username=request.session['username'])
            v.make_mediathread_submit_file(
                filename, user, request.session['set_course'],
                request.session['redirect_to'], audio=audio,
                audio2=audio2
            )

            operations, params = v.make_default_operations(
                tmpfilename, source_file, user, audio=audio, audio2=audio2)

            workflow = select_workflow(audio, audio2)
            if workflow:
                o, p = v.make_submit_to_podcast_producer_operation(
                    tmpfilename, workflow, user)
                operations.append(o)
                params.append(p)

        except:
            statsd.incr("mediathread.mediathread.failure")
            transaction.rollback()
            raise
        else:
            transaction.commit()
            # hand operations off to celery
            for o, p in zip(operations, params):
                maintasks.process_operation.delay(o.id, p)
            return HttpResponseRedirect(request.session['redirect_to'])


@login_required
@render_to('mediathread/mediathread_submit.html')
def video_mediathread_submit(request, id):
    video = get_object_or_404(Video, id=id)
    if request.method == "POST":
        statsd.incr("mediathread.submit")
        params = dict(set_course=request.POST.get('course', ''))
        o = Operation.objects.create(uuid=uuid.uuid4(),
                                     video=video,
                                     action="submit to mediathread",
                                     status="enqueued",
                                     params=dumps(params),
                                     owner=request.user,
                                     )
        maintasks.process_operation.delay(o.id, params)
        o.video.clear_mediathread_submit()
        return HttpResponseRedirect(video.get_absolute_url())
    try:
        url = (settings.MEDIATHREAD_BASE + "/api/user/courses?secret="
               + settings.MEDIATHREAD_SECRET + "&user="
               + request.user.username)
        credentials = None
        if hasattr(settings, "MEDIATHREAD_CREDENTIALS"):
            credentials = settings.MEDIATHREAD_CREDENTIALS
        response = GET(url, credentials=credentials)
        courses = loads(response)['courses']
        courses = [dict(id=k, title=v['title']) for (k, v) in courses.items()]
        courses.sort(key=lambda x: x['title'].lower())
    except:
        courses = []
    return dict(video=video, courses=courses,
                mediathread_base=settings.MEDIATHREAD_BASE)


@login_required
@render_to('mediathread/collection_mediathread_submit.html')
def collection_mediathread_submit(request, pk):
    collection = get_object_or_404(Collection, id=pk)
    if request.method == "POST":
        for video in collection.video_set.all():
            statsd.incr("mediathread.submit")
            params = dict(set_course=request.POST.get('course', ''))
            o = Operation.objects.create(uuid=uuid.uuid4(),
                                         video=video,
                                         action="submit to mediathread",
                                         status="enqueued",
                                         params=dumps(params),
                                         owner=request.user,
                                         )
            maintasks.process_operation.delay(o.id, params)
            o.video.clear_mediathread_submit()
        return HttpResponseRedirect(video.get_absolute_url())
    try:
        url = (settings.MEDIATHREAD_BASE + "/api/user/courses?secret="
               + settings.MEDIATHREAD_SECRET + "&user="
               + request.user.username)
        credentials = None
        if hasattr(settings, "MEDIATHREAD_CREDENTIALS"):
            credentials = settings.MEDIATHREAD_CREDENTIALS
        response = GET(url, credentials=credentials)
        courses = loads(response)['courses']
        courses = [dict(id=k, title=v['title']) for (k, v) in courses.items()]
        courses.sort(key=lambda x: x['title'].lower())
    except:
        courses = []
    return dict(collection=collection, courses=courses,
                mediathread_base=settings.MEDIATHREAD_BASE)
