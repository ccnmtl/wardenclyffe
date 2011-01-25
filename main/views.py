# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from models import Video, Operation, Series, File, Metadata
from forms import UploadVideoForm,AddSeriesForm
import uuid 
from tasks import save_file_to_tahoe, submit_to_podcast_producer, pull_from_tahoe_and_submit_to_pcp, make_images, extract_metadata
import os
from angeldust import PCP
from django.conf import settings
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, InvalidPage

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
    return dict(videos=Video.objects.all().order_by("-modified")[:20],
                operations=Operation.objects.all().order_by("-modified")[:20])

@login_required
@rendered_with('main/series.html')
def series(request,id):
    series = get_object_or_404(Series,id=id)
    videos = Video.objects.filter(series=series).order_by("-modified")
    return dict(series=series,videos=videos[:20],
                operations=Operation.objects.filter(video__series__id=id).order_by("-modified")[:20])


@login_required
@rendered_with('main/video_index.html')
def video_index(request):
    videos = Video.objects.all()
    creators = request.GET.getlist('creator')
    if len(creators) > 0:
        videos = videos.filter(creator__in=creators)
    descriptions = request.GET.getlist('description')
    if len(descriptions) > 0:
        videos = videos.filter(description__in=descriptions)
    languages = request.GET.getlist('language')
    if len(languages) > 0:
        videos = videos.filter(language__in=languages)
    subjects = request.GET.getlist('subject')
    if len(subjects) > 0:
        videos = videos.filter(subject__in=subjects)
    licenses = request.GET.getlist('license')
    if len(licenses) > 0:
        videos = videos.filter(license__in=licenses)
    paginator = Paginator(videos.order_by('title'),100)
    
    try:
        page = int(request.GET.get('page','1'))
    except ValueError:
        page = 1

    try:
        videos = paginator.page(page)
    except (EmptyPage, InvalidPage):
        videos = paginator.page(paginator.num_pages)
    params = dict()
    for k,v in request.GET.items():
        params[k] = v
    params.update(dict(videos=videos))
    return params

@login_required
@rendered_with('main/file_index.html')
def file_index(request):
    files = File.objects.all()
    params = dict()
    facets = []
    for k,v in request.GET.items():
        params[k] = v
        metadatas = Metadata.objects.filter(field=k,value=v)
        files = files.filter(id__in=[m.file_id for m in metadatas])
        facets.append(dict(field=k,value=v))
    paginator = Paginator(files.order_by('video__title'),100)
    
    try:
        page = int(request.GET.get('page','1'))
    except ValueError:
        page = 1

    try:
        files = paginator.page(page)
    except (EmptyPage, InvalidPage):
        files = paginator.page(paginator.num_pages)
    params.update(dict(files=files,facets=facets))
    return params

@login_required
@rendered_with('main/add_series.html')
def add_series(request):
    if request.method == "POST":
        form = AddSeriesForm(request.POST)
        if form.is_valid():
            suuid = uuid.uuid4()
            s = form.save(commit=False)
            s.uuid = suuid
            s.save()
            return HttpResponseRedirect(s.get_absolute_url())
    return dict(form=AddSeriesForm())


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
            extension = request.FILES['source_file'].name.split(".")[-1]
            tmpfilename = "/tmp/tna/" + str(vuuid) + "." + extension.lower()
            print tmpfilename
            tmpfile = open(tmpfilename, 'wb')
            for chunk in request.FILES['source_file'].chunks():
                tmpfile.write(chunk)
            tmpfile.close()
            # make db entry
            try:
                filename = request.FILES['source_file'].name
                v = form.save(commit=False)
                v.uuid = vuuid
                v.save()
                source_file = File.objects.create(video=v,
                                                  label="source file",
                                                  filename=request.FILES['source_file'].name,
                                                  location_type='none')

            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
                if request.POST.get('upload_to_tahoe',False):
                    save_file_to_tahoe.delay(tmpfilename,v.id,filename,request.user)
                if request.POST.get('extract_metadata',False):
                    extract_metadata.delay(tmpfilename,v.id,request.user,source_file.id)
                if request.POST.get('extract_images',False):
                    make_images.delay(tmpfilename,v.id,request.user)
                if request.POST.get('submit_to_pcp',False):
                    submit_to_podcast_producer.delay(tmpfilename,v.id,request.user,settings.PCP_WORKFLOW)
                return HttpResponseRedirect("/")
    else:
        form = UploadVideoForm()
    return dict(form=form)


@transaction.commit_manually
@login_required
@rendered_with('main/vitaldrop.html')
def vitaldrop(request):
    if request.method == "POST":
        if request.FILES['source_file']:
            # save it locally
            vuuid = uuid.uuid4()
            try: 
                os.makedirs("/tmp/tna/")
                print "made dir"
            except:
                pass
            extension = request.FILES['source_file'].name.split(".")[-1]
            tmpfilename = "/tmp/tna/" + str(vuuid) + "." + extension.lower()
            tmpfile = open(tmpfilename, 'wb')
            for chunk in request.FILES['source_file'].chunks():
                tmpfile.write(chunk)
            tmpfile.close()
            # make db entry
            try:
                series = Series.objects.filter(title="Vital")[0]
                filename = request.FILES['source_file'].name
                v = Video.objects.create(series=series,
                                         title="vital video uploaded by %s" % request.user.username,
                                         creator=request.user.username,
                                         uuid = vuuid)
                source_file = File.objects.create(video=v,
                                                  label="source file",
                                                  filename=request.FILES['source_file'].name,
                                                  location_type='none')

            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
                save_file_to_tahoe.delay(tmpfilename,v.id,filename,request.user)
                extract_metadata.delay(tmpfilename,v.id,request.user,source_file.id)
                make_images.delay(tmpfilename,v.id,request.user)
                submit_to_podcast_producer.delay(tmpfilename,v.id,request.user,settings.VITAL_PCP_WORKFLOW)
                return HttpResponseRedirect("/vitaldrop/done/")
    else:
        pass
    return dict()

@rendered_with('main/vitaldrop_done.html')
def vitaldrop_done(request):
    return dict()

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
@rendered_with('main/file.html')
def file(request,id):
    f = get_object_or_404(File,id=id)
    return dict(file=f)

@login_required
@rendered_with('main/pcp_submit.html')
def video_pcp_submit(request,id):
    video = get_object_or_404(Video,id=id)
    if request.method == "POST":
        filename = video.filename()
        # send to podcast producer
        pull_from_tahoe_and_submit_to_pcp.delay(video.id,
                                                request.user,
                                                request.POST.get('workflow',''))
        return HttpResponseRedirect(video.get_absolute_url())        
    try:
        p = PCP(settings.PCP_BASE_URL,
                settings.PCP_USERNAME,
                settings.PCP_PASSWORD)
        workflows = p.workflows()
    except:
        workflows = []
    return dict(video=video,workflows=workflows,
                kino_base=settings.PCP_BASE_URL)

@login_required
@rendered_with('main/workflows.html')
def list_workflows(request):
    try:
        p = PCP(settings.PCP_BASE_URL,
                settings.PCP_USERNAME,
                settings.PCP_PASSWORD)
        workflows = p.workflows()
    except:
        workflows = []
    return dict(workflows=workflows,
                kino_base=settings.PCP_BASE_URL)

