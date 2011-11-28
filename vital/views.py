# Create your views here.
from annoying.decorators import render_to
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from wardenclyffe.main.models import Video, Operation, Series, File, Metadata, OperationLog, OperationFile, Image, Poster
from django.contrib.auth.models import User
import wardenclyffe.vital.tasks as tasks
import wardenclyffe.main.tasks as maintasks
from django.conf import settings
from django.core.mail import send_mail
import re
from django.db import transaction
import uuid
import hmac, hashlib, datetime
from django.template import RequestContext

def uuidparse(s):
    pattern = re.compile(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})")
    m = pattern.match(s)
    if m:
        return m.group()
    else:
        return ""

@transaction.commit_manually
@render_to('vital/submit.html')
def submit(request,id):
    v = get_object_or_404(Video,id=id)
    if request.method == "POST":
        # make db entry
        try:
            # we make a "vitalsubmit" file to store the submission
            # info and serve as a flag that it needs to be submitted
            # (when PCP comes back)
            if not request.POST.get('bypass',False):
                submit_file = File.objects.create(video=v,
                                                  label="vital submit",
                                                  filename=request.FILES['source_file'].name,
                                                  location_type='vitalsubmit')
                submit_file.set_metadata("username",request.user.username)
                submit_file.set_metadata("set_course",request.POST['course_id'])
                submit_file.set_metadata("notify_url",settings.VITAL_NOTIFY_URL)
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()
            if request.POST.get('bypass',False):
                vt = File.objects.filter(video=v,location_type='vitalthumb')
                qt = File.objects.filter(video=v,location_type='rtsp_url')
                
                tasks.submit_to_vital.delay(v.id,request.user,
                                            request.POST['course_id'],
                                            qt[0].url,
                                            settings.VITAL_SECRET,
                                            settings.VITAL_NOTIFY_URL)
            else:
                workflow = settings.PCP_WORKFLOW
                if hasattr(settings,'VITAL_PCP_WORKFLOW'):
                    workflow = settings.VITAL_PCP_WORKFLOW
                maintasks.pull_from_tahoe_and_submit_to_pcp.delay(v.id,user,workflow,settings.PCP_BASE_URL,settings.PCP_USERNAME,settings.PCP_PASSWORD)
            return HttpResponseRedirect(v.get_absolute_url())
    vt = File.objects.filter(video=v,location_type='vitalthumb')
    qt = File.objects.filter(video=v,location_type='rtsp_url')
    return dict(video=v,
                bypassable=vt.count() > 0 and qt.count() > 0)


@transaction.commit_manually
@render_to('vital/drop.html')
def drop(request):
    if request.method == "POST":
        operations = []
        if request.FILES['source_file']:
            # save it locally
            vuuid = uuid.uuid4()
            try: 
                os.makedirs(settings.TMP_DIR)
            except:
                pass
            extension = request.FILES['source_file'].name.split(".")[-1]
            tmpfilename = settings.TMP_DIR + "/" + str(vuuid) + "." + extension.lower()
            tmpfile = open(tmpfilename, 'wb')
            for chunk in request.FILES['source_file'].chunks():
                tmpfile.write(chunk)
            tmpfile.close()
            # make db entry
            try:
                series = Series.objects.get(id=settings.VITAL_SERIES_ID)
                filename = request.FILES['source_file'].name
                user = User.objects.get(username=request.session['username'])                
                v = Video.objects.create(series=series,
                                         title=request.POST.get('title',''),
                                         creator=request.session['username'],
                                         uuid = vuuid)
                source_file = File.objects.create(video=v,
                                                  label="source file",
                                                  filename=request.FILES['source_file'].name,
                                                  location_type='none')
                # we make a "vitalsubmit" file to store the submission
                # info and serve as a flag that it needs to be submitted
                # (when PCP comes back)
                submit_file = File.objects.create(video=v,
                                                  label="vital submit",
                                                  filename=request.FILES['source_file'].name,
                                                  location_type='vitalsubmit')
                submit_file.set_metadata("username",request.session['username'])
                submit_file.set_metadata("set_course",request.session['set_course'])
                submit_file.set_metadata("redirect_to",request.session['redirect_to'])
                submit_file.set_metadata("notify_url",request.session['notify_url'])

                params = dict(tmpfilename=tmpfilename,source_file_id=source_file.id)
                o = Operation.objects.create(uuid = uuid.uuid4(),
                                             video=v,
                                             action="extract metadata",
                                             status="enqueued",
                                             params=params,
                                             owner=request.user)
                operations.append((o.id,params))
                params = dict(tmpfilename=tmpfilename,filename=tmpfilename,
                              tahoe_base=settings.TAHOE_BASE)
                o = Operation.objects.create(uuid = uuid.uuid4(),
                                             video=v,
                                             action="save file to tahoe",
                                             status="enqueued",
                                             params=params,
                                             owner=request.user
                                             )
                operations.append((o.id,params))
                params = dict(tmpfilename=tmpfilename)
                o = Operation.objects.create(uuid = uuid.uuid4(),
                                             video=v,
                                             action="make images",
                                             status="enqueued",
                                             params=params,
                                             owner=request.user
                                             )
                operations.append((o.id,params))
                
                workflow = settings.PCP_WORKFLOW
                if hasattr(settings,'VITAL_PCP_WORKFLOW'):
                    workflow = settings.VITAL_PCP_WORKFLOW
                    params = dict(tmpfilename=tmpfilename)
                    params = dict(tmpfilename=tmpfilename,
                                  pcp_workflow=workflow,
                                  pcp_base_url=settings.PCP_BASE_URL,
                                  pcp_username=settings.PCP_USERNAME,
                                  pcp_password=settings.PCP_PASSWORD)

                    o = Operation.objects.create(uuid = uuid.uuid4(),
                                                 video=v,
                                                 action="submit to podcast producer",
                                                 status="enqueued",
                                                 params=params,
                                                 owner=request.user
                                                 )
                    operations.append((o.id,params))
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()

                for o,kwargs in operations:
                    maintasks.process_operation.delay(o,kwargs)
                return HttpResponseRedirect(request.session['redirect_to'])
    else:
        # check their credentials
        nonce = request.GET.get('nonce','')
        hmc = request.GET.get('hmac','')
        set_course = request.GET.get('set_course','')
        username = request.GET.get('as')
        redirect_to = request.GET.get('redirect_url','')
        notify_url = request.GET.get('notify_url','')
        verify = hmac.new(settings.VITAL_SECRET,
                          '%s:%s:%s:%s' % (username,redirect_to,notify_url,nonce),
                          hashlib.sha1
                          ).hexdigest()
        if verify != hmc:
            return HttpResponse("invalid authentication token")
        try:
            r = User.objects.filter(username=username)
            if r.count():
                user = User.objects.get(username=username)
            else:
                user = User.objects.create(username=username)
            request.session['username'] = username
            request.session['set_course'] = set_course
            request.session['nonce'] = nonce
            request.session['redirect_to'] = redirect_to
            request.session['hmac'] = hmc
            request.session['notify_url'] = notify_url
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return dict(user=user)

def done(request):
    if 'title' not in request.POST:
        return HttpResponse("expecting a title")
    title = request.POST.get('title','no title')
    uuid = uuidparse(title)
    r = Operation.objects.filter(uuid=uuid)
    if r.count() == 1:
        operation = r[0]
        operation.status = "complete"
        operation.save()
        ol = OperationLog.objects.create(operation=operation,
                                         info="PCP completed")
        if operation.video.is_vital_submit():
            cunix_path = request.POST.get('movie_destination_path','')
            rtsp_url = cunix_path.replace("/media/qtstreams/projects/","rtsp://qtss.cc.columbia.edu/projects/")
            (set_course,username,notify_url) = operation.video.vital_submit()
            if set_course is not None:
                user = User.objects.get(username=username)
                qtf = File.objects.create(video=operation.video,
                                          label="Quicktime Streaming Video",
                                          url=rtsp_url,
                                          location_type='rtsp_url')
                tasks.submit_to_vital.delay(operation.video.id,user,set_course,
                                            rtsp_url,
                                            settings.VITAL_SECRET,
                                            notify_url)
                operation.video.clear_vital_submit()
    return HttpResponse("ok")


def posterdone(request):
    if 'title' not in request.POST:
        return HttpResponse("expecting a title")
    title = request.POST.get('title','no title')
    uuid = uuidparse(title)
    r = Operation.objects.filter(uuid=uuid)
    if r.count() == 1:
        operation = r[0]
        if operation.video.is_vital_submit():
            cunix_path = request.POST.get('image_destination_path','')
            poster_url = cunix_path.replace("/www/data/ccnmtl/broadcast/projects/vital/thumbs/",
                                            "http://ccnmtl.columbia.edu/broadcast/projects/vital/thumbs/")

            vitalthumb_file = File.objects.create(video=operation.video,
                                                  label="vital thumbnail image",
                                                  url=poster_url,
                                                  location_type='vitalthumb')
    return HttpResponse("ok")



def received(request):
    if 'title' not in request.POST:
        return HttpResponse("expecting a title")
    title = request.POST.get('title','no title')
    uuid = uuidparse(title)
    r = Operation.objects.filter(uuid=uuid)
    if r.count() == 1:
        operation = r[0]
        if operation.video.is_vital_submit():
            send_mail('Video submitted to VITAL', 
"""This email confirms that %s has been successfully submitted to VITAL by %s.  

The video is now being processed.  When it appears in your VITAL course library you will receive another email confirmation.  This confirmation should arrive within 24 hours.

If you have any questions, please contact VITAL administrators at ccmtl-vital@columbia.edu.
""" % (operation.video.title,operation.owner.username),
                      'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu',
                      ["%s@columbia.edu" % operation.owner.username], fail_silently=False)
            for vuser in settings.ANNOY_EMAILS:
                send_mail('Video submitted to VITAL', 
                          """This email confirms that %s has been successfully submitted to VITAL by %s.  

The video is now being processed.  When it appears in your VITAL course library you will receive another email confirmation.  This confirmation should arrive within 24 hours.

If you have any questions, please contact VITAL administrators at ccmtl-vital@columbia.edu.
""" % (operation.video.title,operation.owner.username),
                          'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu',
                          [vuser], fail_silently=False)

    return HttpResponse("ok")
