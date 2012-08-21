# Create your views here.
from annoying.decorators import render_to
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from wardenclyffe.main.models import Video, Operation, Collection, File
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
            source_file = File.objects.create(video=v,
                                              label="source file",
                                              filename=filename,
                                              location_type='none')
            # we make a "mediathreadsubmit" file to store the submission
            # info and serve as a flag that it needs to be submitted
            # (when PCP comes back)
            submit_file = File.objects.create(video=v,
                                              label="mediathread submit",
                                              filename=filename,
                                              location_type='mediathreadsubmit'
                                              )
            user = User.objects.get(username=request.session['username'])
            submit_file.set_metadata("username", request.session['username'])
            submit_file.set_metadata("set_course",
                                     request.session['set_course'])
            submit_file.set_metadata("redirect_to",
                                     request.session['redirect_to'])
            params = dict(tmpfilename=tmpfilename,
                          source_file_id=source_file.id)
            o = Operation.objects.create(uuid=uuid.uuid4(),
                                         video=v,
                                         action="extract metadata",
                                         status="enqueued",
                                         params=dumps(params),
                                         owner=user)
            operations.append((o.id, params))
            params = dict(tmpfilename=tmpfilename, filename=tmpfilename,
                          tahoe_base=settings.TAHOE_BASE)
            o = Operation.objects.create(uuid=uuid.uuid4(),
                                         video=v,
                                         action="save file to tahoe",
                                         status="enqueued",
                                         params=dumps(params),
                                         owner=user)
            operations.append((o.id, params))
            params = dict(tmpfilename=tmpfilename)
            o = Operation.objects.create(uuid=uuid.uuid4(),
                                         video=v,
                                         action="make images",
                                         status="enqueued",
                                         params=dumps(params),
                                         owner=user)
            operations.append((o.id, params))

            workflow = settings.PCP_WORKFLOW
            if hasattr(settings, 'MEDIATHREAD_PCP_WORKFLOW'):
                workflow = settings.MEDIATHREAD_PCP_WORKFLOW
                params = dict(tmpfilename=tmpfilename)
                params = dict(tmpfilename=tmpfilename,
                              pcp_workflow=workflow)

                o = Operation.objects.create(
                    uuid=uuid.uuid4(),
                    video=v,
                    action="submit to podcast producer",
                    status="enqueued",
                    params=dumps(params),
                    owner=user
                    )
                operations.append((o.id, params))

        except:
            statsd.incr("mediathread.mediathread.failure")
            transaction.rollback()
            raise
        else:
            transaction.commit()
            # hand operations off to celery
            for o, kwargs in operations:
                maintasks.process_operation.delay(o, kwargs)
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
