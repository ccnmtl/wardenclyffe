# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from models import Video, File, Operation
from forms import UploadVideoForm
import uuid 
from tasks import save_file_to_tahoe, submit_to_podcast_producer
import os
from angeldust import PCP
from django.conf import settings
from django.db import transaction

class rendered_with(object):
    def __init__(self, template_name):
        self.template_name = template_name

    def __call__(self, func):
        def rendered_func(request, *args, **kwargs):
            items = func(request, *args, **kwargs)
            if type(items) == type({}):
                return render_to_response(self.template_name, items, context_instance=RequestContext(request))
            else:
                return items

        return rendered_func

@login_required
@rendered_with('main/index.html')
def index(request):
    return dict(videos=Video.objects.all().order_by("-modified")[:20])

@transaction.commit_manually
@login_required
@rendered_with('main/upload.html')
def upload(request):
    if request.method == "POST":
        form = UploadVideoForm(request.POST,request.FILES)
        if form.is_valid():
            # save it locally
            vuuid = uuid.uuid4()
            try: 
                os.makedirs("/tmp/tna/")
                print "made dir"
            except:
                pass
            tmpfilename = "/tmp/tna/" + str(vuuid) + ".mp4"
            print tmpfilename
            tmpfile = open(tmpfilename, 'wb')
            for chunk in request.FILES['source_file'].chunks():
                tmpfile.write(chunk)
            tmpfile.close()
            # make db entry
            try:
                filename = request.FILES['source_file'].name
                v = Video.objects.create(
                    title = form.cleaned_data['title'],
                    description = form.cleaned_data['description'],
                    notes = form.cleaned_data['notes'],
                    uuid=uuid)
                v.save()
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
                # upload to tahoe
                save_file_to_tahoe.delay(tmpfilename,v.id,filename,request.user)
                # send to podcast producer
                submit_to_podcast_producer.delay(tmpfilename,v.id,request.user)
                return HttpResponseRedirect("/")
    else:
        form = UploadVideoForm()
    return dict(form=form)

def test_upload(request):
    print request.raw_post_data
    return HttpResponse("a response")

def done(request):
    print request.raw_post_data
    return HttpResponse("ok")

@login_required
@rendered_with('main/video.html')
def video(request,id):
    v = get_object_or_404(Video,id=id)
    return dict(video=v)

@login_required
@rendered_with('main/workflows.html')
def list_workflows(request):
    p = PCP(settings.PCP_BASE_URL,
            settings.PCP_USERNAME,
            settings.PCP_PASSWORD)
    return dict(workflows=p.workflows())

