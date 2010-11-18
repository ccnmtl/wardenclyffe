# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from models import Video
from forms import UploadVideoForm
import uuid 
import urllib2
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from django.conf import settings

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

def save_file_to_tahoe(source_file):
    filename = source_file.name
    register_openers()
    datagen, headers = multipart_encode({"file": source_file,
                                         "t" : "upload"})
    request = urllib2.Request(settings.TAHOE_BASE, datagen, headers)
    
    cap = urllib2.urlopen(request).read()
    return cap

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
            cap = save_file_to_tahoe(request.FILES['source_file'])
#            cap = "None"
            v = Video.objects.create(
                title = form.cleaned_data['title'],
                description = form.cleaned_data['description'],
                owner = request.user,
                cap = cap,
                filename = request.FILES['source_file'].name,
                uuid=uuid.uuid5(uuid.NAMESPACE_DNS,'tna.ccnmtl.columbia.edu'))
            v.submit_to_podcast_producer(request.FILES['source_file'])
            return HttpResponseRedirect("/")
    else:
        form = UploadVideoForm()
    return dict(form=form)

def test_upload(request):
    print request.raw_post_data
    return HttpResponse("a response")
