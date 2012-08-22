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
from simplejson import loads
import hmac
import hashlib
from django_statsd.clients import statsd
from simplejson import dumps


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
    except:
        user = User.objects.create(username=username)
        statsd.incr("mediathread.user_created")

    request.session['username'] = username
    request.session['set_course'] = set_course
    request.session['nonce'] = nonce
    request.session['redirect_to'] = redirect_to
    request.session['hmac'] = hmc
    return dict(username=username, user=user)


@transaction.commit_manually
def mediathread_post(request):
    if request.method != "POST":
        transaction.commit()
        return HttpResponse("post only")

    tmpfilename = request.POST.get('tmpfilename', '')
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
                request.session['redirect_to'])

            operations, params = v.make_default_operations(
                tmpfilename, source_file, user)

            workflow = settings.PCP_WORKFLOW
            if hasattr(settings, 'MEDIATHREAD_PCP_WORKFLOW'):
                workflow = settings.MEDIATHREAD_PCP_WORKFLOW
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
