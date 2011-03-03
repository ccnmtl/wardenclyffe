# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from models import Video, Operation, Series, File, Metadata, OperationLog, OperationFile
from django.contrib.auth.models import User
from forms import UploadVideoForm,AddSeriesForm
import uuid 
from tasks import save_file_to_tahoe, submit_to_podcast_producer, pull_from_tahoe_and_submit_to_pcp, make_images, extract_metadata
import os
from angeldust import PCP
from django.conf import settings
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from taggit.models import Tag
from restclient import GET,POST
from simplejson import loads

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
    return dict(
        series=Series.objects.all().order_by("title"),
        videos=Video.objects.all().order_by("-modified")[:20],
                operations=Operation.objects.all().order_by("-modified")[:20])

@login_required
@rendered_with('main/series.html')
def series(request,id):
    series = get_object_or_404(Series,id=id)
    videos = Video.objects.filter(series=series).order_by("-modified")
    return dict(series=series,videos=videos[:20],
                operations=Operation.objects.filter(video__series__id=id).order_by("-modified")[:20])

@login_required
@rendered_with('main/user.html')
def user(request,username):
    user = get_object_or_404(User,username=username)
    return dict(user=user,
                operations=Operation.objects.filter(owner__id=user.id).order_by("-modified")[:20])


@login_required
@rendered_with('main/edit_series.html')
def edit_series(request,id):
    series = get_object_or_404(Series,id=id)
    if request.method == "POST":
        form = series.edit_form(request.POST)
        if form.is_valid():
            series = form.save()
            return HttpResponseRedirect(series.get_absolute_url())
    form = series.edit_form()
    return dict(series=series,form=form)

@login_required
@rendered_with('main/edit_video.html')
def edit_video(request,id):
    video = get_object_or_404(Video,id=id)
    if request.method == "POST":
        form = video.edit_form(request.POST)
        if form.is_valid():
            video = form.save()
            return HttpResponseRedirect(video.get_absolute_url())
    form = video.edit_form()
    return dict(video=video,form=form)

@login_required
def remove_tag_from_video(request,id,tagname):
    video = get_object_or_404(Video,id=id)
    if 'ajax' in request.GET:
        # we're not being strict about requiring POST,
        # but let's at least require ajax
        video.tags.remove(tagname)
    return HttpResponse("ok")

@login_required
def remove_tag_from_series(request,id,tagname):
    series = get_object_or_404(Series,id=id)
    if 'ajax' in request.GET:
        # we're not being strict about requiring POST,
        # but let's at least require ajax
        series.tags.remove(tagname)
    return HttpResponse("ok")


@login_required
@rendered_with('main/tag.html')
def tag(request,tagname):
    return dict(tag=tagname,
                series=Series.objects.filter(tags__name__in=[tagname]).order_by("-modified"),
                videos = Video.objects.filter(tags__name__in=[tagname]).order_by("-modified"))

@login_required
@rendered_with('main/tags.html')
def tags(request):
    return dict(tags=Tag.objects.all().order_by("name"))

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
            form.save_m2m()
            return HttpResponseRedirect(s.get_absolute_url())
    return dict(form=AddSeriesForm())


@transaction.commit_manually
@login_required
@rendered_with('main/upload.html')
def upload(request):
    series_id = None
    if request.method == "POST":
        form = UploadVideoForm(request.POST,request.FILES)
        if form.is_valid():
            # save it locally
            vuuid = uuid.uuid4()
            if request.FILES.get('source_file',None):
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
                if request.FILES.get('source_file',None):
                    filename = request.FILES['source_file'].name
                v = form.save(commit=False)
                v.uuid = vuuid
                series_id = request.GET.get('series',None)
                if series_id:
                    v.series_id = series_id
                v.save()
                form.save_m2m()
                if request.FILES.get('source_file',None):
                    source_file = File.objects.create(video=v,
                                                      label="source file",
                                                      filename=request.FILES['source_file'].name,
                                                      location_type='none')

            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
                if request.FILES.get('source_file',None):
                    # only run these steps if there's actually a file uploaded
                    if request.POST.get('upload_to_tahoe',False):
                        save_file_to_tahoe.delay(tmpfilename,v.id,filename,request.user,settings.TAHOE_BASE)
                    if request.POST.get('extract_metadata',False):
                        extract_metadata.delay(tmpfilename,v.id,request.user,source_file.id)
                    if request.POST.get('extract_images',False):
                        make_images.delay(tmpfilename,v.id,request.user)
                    if request.POST.get('submit_to_pcp',False):
                        submit_to_podcast_producer.delay(tmpfilename,v.id,request.user,settings.PCP_WORKFLOW,
                                                         settings.PCP_BASE_URL,settings.PCP_USERNAME,settings.PCP_PASSWORD)
                return HttpResponseRedirect("/")
    else:
        form = UploadVideoForm()
        series_id = request.GET.get('series',None)
        if series_id:
            series = get_object_or_404(Series,id=series_id)
            form = series.add_video_form()
            
    return dict(form=form,series_id=series_id)


@transaction.commit_manually
@login_required
@rendered_with('main/scan_directory.html')
def scan_directory(request):
    series_id = None
    file_listing = []
    if request.method == "POST":
        form = UploadVideoForm(request.POST)
        if form.is_valid():
            # save it locally
            vuuid = uuid.uuid4()
            try: 
                os.makedirs(settings.TMP_DIR)
            except:
                pass
            if not request.POST['source_file']:
                return HttpResponse("no video uploaded")

            extension = request.POST.get('source_file').split(".")[-1]
            tmpfilename = settings.TMP_DIR + "/" + str(vuuid) + "." + extension.lower()

            os.rename(settings.WATCH_DIRECTORY + request.POST.get('source_file'),tmpfilename)


            # make db entry
            try:
                filename = request.POST['source_file']
                v = form.save(commit=False)
                v.uuid = vuuid
                series_id = request.GET.get('series',None)
                if series_id:
                    v.series_id = series_id
                v.save()
                form.save_m2m()
                source_file = File.objects.create(video=v,
                                                  label="source file",
                                                  filename=request.POST.get('source_file'),
                                                  location_type='none')

            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
                if request.POST.get('upload_to_tahoe',False):
                    save_file_to_tahoe.delay(tmpfilename,v.id,filename,request.user,settings.TAHOE_BASE)
                if request.POST.get('extract_metadata',False):
                    extract_metadata.delay(tmpfilename,v.id,request.user,source_file.id)
                if request.POST.get('extract_images',False):
                    make_images.delay(tmpfilename,v.id,request.user)
                if request.POST.get('submit_to_pcp',False):
                    submit_to_podcast_producer.delay(tmpfilename,v.id,request.user,settings.PCP_WORKFLOW,
                                                     settings.PCP_BASE_URL,settings.PCP_USERNAME,settings.PCP_PASSWORD)
                return HttpResponseRedirect("/")
    else:
        form = UploadVideoForm()
        series_id = request.GET.get('series',None)
        if series_id:
            series = get_object_or_404(Series,id=series_id)
            form = series.add_video_form()
        file_listing = os.listdir(settings.WATCH_DIRECTORY)
            
    return dict(form=form,series_id=series_id,file_listing=file_listing)


@transaction.commit_manually
@login_required
@rendered_with('main/vitaldrop.html')
def vitaldrop(request):
    if request.method == "POST":
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
                save_file_to_tahoe.delay(tmpfilename,v.id,filename,request.user,settings.TAHOE_BASE)
                extract_metadata.delay(tmpfilename,v.id,request.user,source_file.id)
                make_images.delay(tmpfilename,v.id,request.user)
                submit_to_podcast_producer.delay(tmpfilename,v.id,request.user,settings.VITAL_PCP_WORKFLOW,
                                                 settings.PCP_BASE_URL,settings.PCP_USERNAME,settings.PCP_PASSWORD)
                return HttpResponseRedirect("/vitaldrop/done/")
    else:
        pass
    return dict()

@rendered_with('main/vitaldrop_done.html')
def vitaldrop_done(request):
    return dict()

def test_upload(request):
    return HttpResponse("a response")

def done(request):
    title = request.POST.get('title','no title')
    if title.startswith("[") and "]" in title:
        (uuid,oldtitle) = title.split("]")
        uuid = uuid[1:]
    r = Operation.objects.filter(uuid=uuid)
    if r.count() == 1:
        operation = r[0]
        operation.status = "complete"
        operation.save()
        ol = OperationLog.objects.create(operation=operation,
                                         info="PCP completed")
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
@rendered_with('main/delete_confirm.html')
def delete_file(request,id):
    f = get_object_or_404(File,id=id)
    if request.method == "POST":
        video = f.video
        f.delete()
        return HttpResponseRedirect(video.get_absolute_url())
    else:
        return dict()

@login_required
@rendered_with('main/delete_confirm.html')
def delete_video(request,id):
    v = get_object_or_404(Video,id=id)
    if request.method == "POST":
        series = v.series
        v.delete()
        return HttpResponseRedirect(series.get_absolute_url())
    else:
        return dict()

@login_required
@rendered_with('main/delete_confirm.html')
def delete_series(request,id):
    s = get_object_or_404(Series,id=id)
    if request.method == "POST":
        s.delete()
        return HttpResponseRedirect("/")
    else:
        return dict()

@login_required
@rendered_with('main/delete_confirm.html')
def delete_operation(request,id):
    o = get_object_or_404(Operation,id=id)
    if request.method == "POST":
        video = o.video
        o.delete()
        return HttpResponseRedirect(video.get_absolute_url())
    else:
        return dict()


@login_required
@rendered_with('main/pcp_submit.html')
def video_pcp_submit(request,id):
    video = get_object_or_404(Video,id=id)
    if request.method == "POST":
        filename = video.filename()
        # send to podcast producer
        pull_from_tahoe_and_submit_to_pcp.delay(video.id,
                                                request.user,
                                                request.POST.get('workflow',''),
                                                settings.PCP_BASE_URL,settings.PCP_USERNAME,settings.PCP_PASSWORD)
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
@rendered_with('main/mediathread_submit.html')
def video_mediathread_submit(request,id):
    video = get_object_or_404(Video,id=id)
    if request.method == "POST":
        # TODO: convert this to a celery task so it can
        # run asynchronously
        operation = Operation.objects.create(video=video,
                                             owner=request.user,
                                             action="submit to mediathread",
                                             status="in progress")
        (width,height) = video.get_dimensions()
        if not width or not height:
            return HttpResponse("can not determine dimensions of video, which mediathread requires")
        params = {
            'set_course' : request.POST.get('course',''),
            'as' : request.user.username,
            'secret' : settings.MEDIATHREAD_SECRET,
            'title' : video.title,
            'mp4' : video.tahoe_download_url(),
            # TODO: until we let users designate poster images
            'thumb' : video.poster_url(),
            "mp4-metadata" : "w%dh%d" % (width,height),
            "metadata-creator" : video.creator,
            "metadata-description" : video.description,
            "metadata-subject" : video.subject,
            "metadata-license" : video.license,
            "metadata-language" : video.language,
            "metadata-uuid" : video.uuid,
            "metadata-wardenclyffe-id" : str(video.id),
            }
        resp,content = POST(settings.MEDIATHREAD_POST_URL,params=params,async=False,resp=True)
        if resp.status == 302:
            url = resp['location']
            f = File.objects.create(video=video,url=url,cap="",location_type="mediathread",
                                    filename="",
                                    label="mediathread")
            of = OperationFile.objects.create(operation=operation,file=f)
            operation.status = "complete"
            operation.save()
        else:
            log = OperationLog.objects.create(operation=operation,
                                              info="mediathread rejected submission")
            operation.status = "failed"
            operation.save()

        return HttpResponseRedirect(video.get_absolute_url())        
    try:
        courses = loads(GET(settings.MEDIATHREAD_BASE + "/api/user/courses?secret=" 
                            + settings.MEDIATHREAD_SECRET + "&user=" + request.user.username))['courses']
        courses = [dict(id=k,title=v['title']) for (k,v) in courses.items()]
        courses.sort(key=lambda x: x['title'].lower())
    except:
        courses = []
    return dict(video=video,courses=courses,
                mediathread_base=settings.MEDIATHREAD_BASE)


@login_required
@rendered_with('main/add_file.html')
def video_add_file(request,id):
    video = get_object_or_404(Video,id=id)
    if request.method == "POST":
        form = video.add_file_form(request.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.video = video
            f.save()
        else:
            pass
        return HttpResponseRedirect(video.get_absolute_url())
    return dict(video=video)

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

