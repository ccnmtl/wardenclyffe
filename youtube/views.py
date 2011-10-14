# Create your views here.
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

from main.views import rendered_with


@transaction.commit_manually
@login_required
@rendered_with('main/youtube.html')
def youtube(request):
    if request.method == "POST":
        tmpfilename = request.POST.get('tmpfilename','')
        if tmpfilename.startswith(settings.TMP_DIR):
            # make db entry
            filename = os.path.basename(tmpfilename)
            vuuid = os.path.splitext(filename)[0]
            try:
                series = Series.objects.filter(title="Youtube")[0]
                v = Video.objects.create(series=series,
                                         title=request.POST.get("title","youtube video uploaded by %s" % request.user.username),
                                         creator=request.user.username,
                                         description=request.POST.get("description",""),
                                         uuid = vuuid)
                source_file = File.objects.create(video=v,
                                                  label="source file",
                                                  filename=filename,
                                                  location_type='none')

            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
                save_file_to_tahoe.delay(tmpfilename,v.id,filename,request.user,settings.TAHOE_BASE)
                extract_metadata.delay(tmpfilename,v.id,request.user,source_file.id)
                make_images.delay(tmpfilename,v.id,request.user)
                tasks.upload_to_youtube.delay(tmpfilename,v.id,request.user,
                                              settings.YOUTUBE_EMAIL,
                                              settings.YOUTUBE_PASSWORD,
                                              settings.YOUTUBE_SOURCE,
                                              settings.YOUTUBE_DEVELOPER_KEY,
                                              settings.YOUTUBE_CLIENT_ID
                                              )
                return HttpResponseRedirect("/youtube/done/")
        else:
            return HttpResponse("no tmpfilename parameter set")
    else:
        pass
    return dict()

@rendered_with('main/youtube_done.html')
def youtube_done(request):
    return dict()




