# Create your views here.
from annoying.decorators import render_to
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from wardenclyffe.main.models import Video, Collection, File
from django.contrib.auth.models import User
import wardenclyffe.vital.tasks as tasks
import wardenclyffe.main.tasks as maintasks
from django.conf import settings
from django.db import transaction
import uuid
import hmac
import hashlib
from django_statsd.clients import statsd
import os
import waffle


@transaction.commit_manually
@render_to('vital/submit.html')
def submit(request, id):
    v = get_object_or_404(Video, id=id)
    if request.method == "POST":
        statsd.incr("vital.submit")
        # make db entry
        try:
            # we make a "vitalsubmit" file to store the submission
            # info and serve as a flag that it needs to be submitted
            # (when PCP comes back)
            if not request.POST.get('bypass', False):
                submit_file = File.objects.create(video=v,
                                                  label="vital submit",
                                                  location_type='vitalsubmit')
                submit_file.set_metadata("username",
                                         request.user.username)
                submit_file.set_metadata("set_course",
                                         request.POST['course_id'])
                submit_file.set_metadata("notify_url",
                                         settings.VITAL_NOTIFY_URL)
        except:
            statsd.incr("vital.submit.failure")
            transaction.rollback()
            raise
        else:
            transaction.commit()
            if request.POST.get('bypass', False):
                vt = File.objects.filter(video=v, location_type='vitalthumb')
                qt = File.objects.filter(video=v, location_type='rtsp_url')

                tasks.submit_to_vital.delay(v.id, request.user,
                                            request.POST['course_id'],
                                            qt[0].url,
                                            settings.VITAL_SECRET,
                                            settings.VITAL_NOTIFY_URL)
            else:
                workflow = settings.PCP_WORKFLOW
                if hasattr(settings, 'VITAL_PCP_WORKFLOW'):
                    workflow = settings.VITAL_PCP_WORKFLOW
                maintasks.pull_from_tahoe_and_submit_to_pcp.delay(
                    v.id, request.user, workflow, settings.PCP_BASE_URL,
                    settings.PCP_USERNAME, settings.PCP_PASSWORD)
            return HttpResponseRedirect(v.get_absolute_url())
    vt = File.objects.filter(video=v, location_type='vitalthumb')
    qt = File.objects.filter(video=v, location_type='rtsp_url')
    return dict(video=v,
                bypassable=vt.count() > 0 and qt.count() > 0)


@transaction.commit_manually
@render_to('vital/drop.html')
def drop(request):
    if request.method != "POST":
        transaction.commit()
        return HttpResponse("POST only")
    operations = []
    params = []
    if request.FILES['source_file']:
        statsd.incr("vital.drop")
        # save it locally
        vuuid = uuid.uuid4()
        try:
            os.makedirs(settings.TMP_DIR)
        except:
            pass
        extension = request.FILES['source_file'].name.split(".")[-1]
        tmpfilename = (settings.TMP_DIR + "/" + str(vuuid) + "." +
                       extension.lower())
        tmpfile = open(tmpfilename, 'wb')
        for chunk in request.FILES['source_file'].chunks():
            tmpfile.write(chunk)
        tmpfile.close()
        # make db entry
        try:
            collection = Collection.objects.get(
                id=settings.VITAL_COLLECTION_ID)
            filename = request.FILES['source_file'].name
            user = User.objects.get(username=request.session['username'])
            v = Video.objects.create(collection=collection,
                                     title=request.POST.get('title', ''),
                                     creator=request.session['username'],
                                     uuid=vuuid)
            source_file = v.make_source_file(filename=filename)
            # we make a "vitalsubmit" file to store the submission
            # info and serve as a flag that it needs to be submitted
            # (when PCP comes back)
            v.make_vital_submit_file(
                filename, user, request.session['set_course'],
                request.session['redirect_to'],
                request.session['notify_url'])
            operations, params = v.make_default_operations(
                tmpfilename, source_file, user)

            workflow = settings.PCP_WORKFLOW
            if hasattr(settings, 'VITAL_PCP_WORKFLOW'):
                workflow = settings.VITAL_PCP_WORKFLOW
                o, p = v.make_submit_to_podcast_producer_operation(
                    tmpfilename, workflow, user)
                operations.append(o)
                params.append(p)
        except:
            statsd.incr("vital.drop.failure")
            transaction.rollback()
            raise
        else:
            transaction.commit()

            for o, p in zip(operations, params):
                maintasks.process_operation.delay(o.id, p)
            return HttpResponseRedirect(request.session['redirect_to'])


@render_to('vital/drop.html')
def drop_form(request):
    if not waffle.flag_is_active(request, 'vital_uploads'):
        return dict()
    # check their credentials
    nonce = request.GET.get('nonce', '')
    hmc = request.GET.get('hmac', '')
    set_course = request.GET.get('set_course', '')
    username = request.GET.get('as')
    redirect_to = request.GET.get('redirect_url', '')
    notify_url = request.GET.get('notify_url', '')
    verify = hmac.new(settings.VITAL_SECRET,
                      '%s:%s:%s:%s' % (username, redirect_to, notify_url,
                                       nonce),
                      hashlib.sha1
                      ).hexdigest()
    if verify != hmc:
        statsd.incr("vital.auth_failure")
        return HttpResponse("invalid authentication token")
    try:
        r = User.objects.filter(username=username)
        if r.count():
            user = User.objects.get(username=username)
        else:
            statsd.incr("vital.create_user")
            user = User.objects.create(username=username)
        request.session['username'] = username
        request.session['set_course'] = set_course
        request.session['nonce'] = nonce
        request.session['redirect_to'] = redirect_to
        request.session['hmac'] = hmc
        request.session['notify_url'] = notify_url
    except:
        statsd.incr("vital.drop.failure_on_get")
        raise

    return dict(user=user)
