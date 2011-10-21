# Create your views here.
from annoying.decorators import render_to
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from main.models import Video, Operation, Series, File, Metadata, OperationLog, OperationFile, Image, Poster
from django.contrib.auth.models import User
import uuid 
from main.tasks import save_file_to_tahoe, submit_to_podcast_producer, make_images, extract_metadata
import tasks
import os
from django.conf import settings
from django.db import transaction
from restclient import GET
from simplejson import loads, dumps
import hmac, hashlib, datetime
from django.core.mail import send_mail
import re

@transaction.commit_manually
@render_to('main/mediathread.html')
def mediathread(request):
    if request.method == "POST":
        tmpfilename = request.POST.get('tmpfilename','')
        if tmpfilename.startswith(settings.TMP_DIR):
            filename = os.path.basename(tmpfilename)
            vuuid = os.path.splitext(filename)[0]
            # make db entry
            try:
                series = Series.objects.get(id=settings.MEDIATHREAD_SERIES_ID)
                v = Video.objects.create(series=series,
                                         title=request.POST.get('title',''),
                                         creator=request.session['username'],
                                         uuid = vuuid)
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
                                                  location_type='mediathreadsubmit')
                user = User.objects.get(username=request.session['username'])
                submit_file.set_metadata("username",request.session['username'])
                submit_file.set_metadata("set_course",request.session['set_course'])
                submit_file.set_metadata("redirect_to",request.session['redirect_to'])
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
                
                save_file_to_tahoe.delay(tmpfilename,v.id,filename,user,settings.TAHOE_BASE)
                extract_metadata.delay(tmpfilename,v.id,request.user,source_file.id)
                make_images.delay(tmpfilename,v.id,request.user)
                workflow = settings.PCP_WORKFLOW
                if hasattr(settings,'MEDIATHREAD_PCP_WORKFLOW'):
                    workflow = settings.MEDIATHREAD_PCP_WORKFLOW
                submit_to_podcast_producer.delay(tmpfilename,v.id,request.user,workflow,
                                                 settings.PCP_BASE_URL,settings.PCP_USERNAME,settings.PCP_PASSWORD)
                return HttpResponseRedirect(request.session['redirect_to'])
    else:
        # check their credentials
        nonce = request.GET.get('nonce','')
        hmc = request.GET.get('hmac','')
        set_course = request.GET.get('set_course','')
        username = request.GET.get('as')
        redirect_to = request.GET.get('redirect_url','')
        verify = hmac.new(settings.MEDIATHREAD_SECRET,
                          '%s:%s:%s' % (username,redirect_to,nonce),
                          hashlib.sha1
                          ).hexdigest()
        if verify != hmc:
            return HttpResponse("invalid authentication token")

        try:
            user = User.objects.get(username=username)
        except:
            user = User.objects.create(username=username)
        request.session['username'] = username
        request.session['set_course'] = set_course
        request.session['nonce'] = nonce
        request.session['redirect_to'] = redirect_to
        request.session['hmac'] = hmc
        return dict(username=username)

@login_required
@render_to('main/mediathread_submit.html')
def video_mediathread_submit(request,id):
    video = get_object_or_404(Video,id=id)
    if request.method == "POST":
        tasks.submit_to_mediathread.delay(video.id,request.user,
                                          request.POST.get('course',''),
                                          settings.MEDIATHREAD_SECRET,
                                          settings.MEDIATHREAD_BASE)
        return HttpResponseRedirect(video.get_absolute_url())        
    try:
        url = settings.MEDIATHREAD_BASE + "/api/user/courses?secret=" + settings.MEDIATHREAD_SECRET + "&user=" + request.user.username
        credentials = None
        if hasattr(settings,"MEDIATHREAD_CREDENTIALS"):
            credentials = settings.MEDIATHREAD_CREDENTIALS
        response = GET(url,credentials=credentials)
        courses = loads(response)['courses']
        courses = [dict(id=k,title=v['title']) for (k,v) in courses.items()]
        courses.sort(key=lambda x: x['title'].lower())
    except Exception, e:
        print str(e)
        courses = []
    return dict(video=video,courses=courses,
                mediathread_base=settings.MEDIATHREAD_BASE)

