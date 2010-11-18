# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from models import Video
from forms import UploadVideoForm
import uuid 
from tasks import save_file_to_tahoe, submit_to_podcast_producer
import os

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
    return dict(videos=Video.objects.all())

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
                print "exception"
            tmpfilename = "/tmp/tna/" + str(vuuid) + ".mp4"
            print tmpfilename
            tmpfile = open(tmpfilename, 'wb')
            for chunk in request.FILES['source_file'].chunks():
                tmpfile.write(chunk)
            tmpfile.close()
            # make db entry
            v = Video.objects.create(
                title = form.cleaned_data['title'],
                description = form.cleaned_data['description'],
                owner = request.user,
                cap = "None",
                filename = request.FILES['source_file'].name,
                uuid=uuid)
            # upload to tahoe
            save_file_to_tahoe.delay(tmpfilename,v.id)
            # send to podcast producer
            submit_to_podcast_producer.delay(tmpfilename,v.id)
            return HttpResponseRedirect("/")
    else:
        form = UploadVideoForm()
    return dict(form=form)

def test_upload(request):
    print request.raw_post_data
    return HttpResponse("a response")

