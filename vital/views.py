# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from main.models import Video, Operation, Series, File, Metadata, OperationLog, OperationFile, Image, Poster
from django.contrib.auth.models import User
import uuid 
from tasks import submit_to_vital
import tasks
import os
from angeldust import PCP
from django.conf import settings
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from taggit.models import Tag
from restclient import GET,POST
from simplejson import loads
import hmac, hashlib, datetime
from zencoder import Zencoder
from django.db.models import Q
from django.core.mail import send_mail
import re

def uuidparse(s):
    pattern = re.compile(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})")
    m = pattern.match(s)
    if m:
        return m.group()
    else:
        return ""

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
                submit_to_vital.delay(operation.video.id,user,set_course,
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
            send_mail('VITAL video processing', 
                      """Your video, "%s", has been submitted for processing.""" % operation.video.title, 
                      'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu',
                      ["%s@columbia.edu" % operation.owner.username], fail_silently=False)

    return HttpResponse("ok")
