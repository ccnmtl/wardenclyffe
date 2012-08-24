# stdlib imports
import os
import uuid
import wardenclyffe.main.tasks as tasks

from angeldust import PCP
from annoying.decorators import render_to
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django_statsd.clients import statsd
from munin.helpers import muninview
from simplejson import dumps
from taggit.models import Tag
from wardenclyffe.main.forms import AddServerForm
from wardenclyffe.main.forms import UploadVideoForm, AddCollectionForm
from wardenclyffe.main.models import Video, Operation, Collection, File
from wardenclyffe.main.models import Metadata, OperationLog, Image, Poster
from wardenclyffe.main.models import Server, CollectionWorkflow
from wardenclyffe.surelink.helpers import SureLink
import wardenclyffe.vital.tasks as vitaltasks
from wardenclyffe.util import uuidparse
from wardenclyffe.util.mail import send_mediathread_received_mail
from wardenclyffe.util.mail import send_vital_received_mail
from zencoder import Zencoder


@login_required
@render_to('main/index.html')
def index(request):
    return dict(
        collection=Collection.objects.all().order_by("title"),
        videos=Video.objects.all().order_by("-modified")[:20],
                operations=Operation.objects.all().order_by("-modified")[:20])


@login_required
@render_to('main/dashboard.html')
def dashboard(request):
    submitted = request.GET.get('submitted', '') == '1'
    status_filters = dict()
    status_filters["failed"] = request.GET.get('status_filter_failed',
                                               not submitted)
    status_filters["complete"] = request.GET.get('status_filter_complete',
                                                 not submitted)
    status_filters["submitted"] = request.GET.get('status_filter_submitted',
                                                  not submitted)
    status_filters["inprogress"] = request.GET.get('status_filter_inprogress',
                                                   not submitted)
    status_filters["enqueued"] = request.GET.get('status_filter_enqueued',
                                                 not submitted)
    user_filter = request.GET.get('user', '')
    collection_filter = int(request.GET.get('collection', False) or '0')
    d = dict(
        all_collection=Collection.objects.all().order_by("title"),
        all_users=User.objects.all(),
        user_filter=user_filter,
        collection_filter=collection_filter,
        submitted=submitted,
        )
    d.update(status_filters)
    return d


def received(request):
    if 'title' not in request.POST:
        return HttpResponse("expecting a title")
    statsd.incr('main.received')
    title = request.POST.get('title', 'no title')
    ruuid = uuidparse(title)
    r = Operation.objects.filter(uuid=ruuid)
    if r.count() == 1:
        operation = r[0]

        if operation.video.is_mediathread_submit():
            send_mediathread_received_mail(operation.video.title,
                                           operation.owner.username)

        if operation.video.is_vital_submit():
            send_vital_received_mail(operation.video.title,
                                     operation.owner.username)
    else:
        statsd.incr('main.received_failure')

    return HttpResponse("ok")


def uploadify(request, *args, **kwargs):
    if request.method == 'POST':
        statsd.incr('main.uploadify_post')
        if request.FILES:
            # save it locally
            vuuid = uuid.uuid4()
            safe_makedirs(settings.TMP_DIR)
            extension = request.FILES['Filedata'].name.split(".")[-1]
            tmpfilename = settings.TMP_DIR + "/" + str(vuuid) + "."\
                + extension.lower()
            tmpfile = open(tmpfilename, 'wb')
            for chunk in request.FILES['Filedata'].chunks():
                tmpfile.write(chunk)
            tmpfile.close()
            return HttpResponse(tmpfilename)
        else:
            statsd.incr('main.uploadify_post_no_file')
    return HttpResponse('True')


@login_required
def recent_operations(request):
    submitted = request.GET.get('submitted', '') == '1'
    status_filters = []
    if request.GET.get('status_filter_failed', not submitted):
        status_filters.append("failed")
    if request.GET.get('status_filter_enqueued', not submitted):
        status_filters.append("enqueued")
    if request.GET.get('status_filter_complete', not submitted):
        status_filters.append("complete")
    if request.GET.get('status_filter_inprogress', not submitted):
        status_filters.append("in progress")
    if request.GET.get('status_filter_submitted', not submitted):
        status_filters.append("submitted")
    user_filter = request.GET.get('user', '')
    collection_filter = int(request.GET.get('collection', False) or '0')

    q = Operation.objects.filter(status__in=status_filters)
    if collection_filter:
        q = q.filter(video__collection__id=collection_filter)
    if user_filter:
        q = q.filter(video__creator=user_filter)

    return HttpResponse(
        dumps(dict(operations=[o.as_dict() for o
                               in q.order_by("-modified")[:200]])),
        mimetype="application/json")


@login_required
def most_recent_operation(request):
    return HttpResponse(
        dumps(dict(modified=str(Operation.objects.all().order_by(
                        "-modified")[0].modified)[:19])),
        mimetype="application/json")


@login_required
@render_to('main/servers.html')
def servers(request):
    servers = Server.objects.all()
    return dict(servers=servers)


@login_required
@render_to('main/server.html')
def server(request, id):
    server = get_object_or_404(Server, id=id)
    return dict(server=server)


@login_required
@render_to('main/delete_confirm.html')
def delete_server(request, id):
    s = get_object_or_404(Server, id=id)
    if request.method == "POST":
        s.delete()
        return HttpResponseRedirect("/server/")
    else:
        return dict()


@login_required
@render_to('main/edit_server.html')
def edit_server(request, id):
    server = get_object_or_404(Server, id=id)
    if request.method == "POST":
        form = server.edit_form(request.POST)
        if form.is_valid():
            server = form.save()
            return HttpResponseRedirect(server.get_absolute_url())
    form = server.edit_form()
    return dict(server=server, form=form)


@login_required
@render_to('main/add_server.html')
def add_server(request):
    if request.method == "POST":
        form = AddServerForm(request.POST)
        if form.is_valid():
            suuid = uuid.uuid4()
            s = form.save(commit=False)
            s.uuid = suuid
            s.save()
            form.save_m2m()
            return HttpResponseRedirect(s.get_absolute_url())
    return dict(form=AddServerForm())


@login_required
@render_to('main/collection.html')
def collection(request, id):
    collection = get_object_or_404(Collection, id=id)
    videos = Video.objects.filter(collection=collection).order_by("-modified")
    return dict(collection=collection, videos=videos[:20],
                operations=Operation.objects.filter(
            video__collection__id=id).order_by("-modified")[:20])


@login_required
@render_to('main/all_collection_videos.html')
def all_collection_videos(request, id):
    collection = get_object_or_404(Collection, id=id)
    videos = collection.video_set.all().order_by("title")
    params = dict(collection=collection)
    paginator = Paginator(videos, 100)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        videos = paginator.page(page)
    except (EmptyPage, InvalidPage):
        videos = paginator.page(paginator.num_pages)

    for k, v in request.GET.items():
        params[k] = v
    params.update(dict(videos=videos))
    return params


@login_required
@render_to('main/all_collection_operations.html')
def all_collection_operations(request, id):
    collection = get_object_or_404(Collection, id=id)
    operations = Operation.objects.filter(
        video__collection__id=id).order_by("-modified")
    params = dict(collection=collection)
    paginator = Paginator(operations, 100)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        operations = paginator.page(page)
    except (EmptyPage, InvalidPage):
        operations = paginator.page(paginator.num_pages)

    for k, v in request.GET.items():
        params[k] = v
    params.update(dict(operations=operations))
    return params


@login_required
@render_to('main/user.html')
def user(request, username):
    user = get_object_or_404(User, username=username)
    return dict(viewuser=user,
                operations=Operation.objects.filter(
            owner__id=user.id).order_by("-modified")[:20])


@login_required
@render_to('main/edit_collection.html')
def edit_collection(request, id):
    collection = get_object_or_404(Collection, id=id)
    if request.method == "POST":
        form = collection.edit_form(request.POST)
        if form.is_valid():
            collection = form.save()
            return HttpResponseRedirect(collection.get_absolute_url())
    form = collection.edit_form()
    return dict(collection=collection, form=form)


@login_required
@render_to('main/edit_collection_workflows.html')
def edit_collection_workflows(request, id):
    collection = get_object_or_404(Collection, id=id)

    workflows = []
    try:
        p = PCP(settings.PCP_BASE_URL,
                settings.PCP_USERNAME,
                settings.PCP_PASSWORD)
        workflows = p.workflows()
    except:
        workflows = []

    if request.method == 'POST':
        # clear existing ones
        collection.collectionworkflow_set.all().delete()
        # re-add
        for k in request.POST.keys():
            if k.startswith('workflow_'):
                uuid = k.split('_')[1]
                label = 'default workflow'
                for w in workflows:
                    if w.uuid == uuid:
                        label = w.title
                        break
                cw = CollectionWorkflow.objects.create(
                    collection=collection,
                    workflow=uuid,
                    label=label,
                    )
        return HttpResponseRedirect(collection.get_absolute_url())

    existing_uuids = [str(cw.workflow) for cw in
                      collection.collectionworkflow_set.all()]
    for w in workflows:
        if str(w.uuid) in existing_uuids:
            w.selected = True

    return dict(collection=collection, workflows=workflows)


@login_required
@render_to('main/edit_video.html')
def edit_video(request, id):
    video = get_object_or_404(Video, id=id)
    if request.method == "POST":
        form = video.edit_form(request.POST)
        if form.is_valid():
            video = form.save()
            return HttpResponseRedirect(video.get_absolute_url())
    form = video.edit_form()
    return dict(video=video, form=form)


@login_required
def remove_tag_from_video(request, id, tagname):
    video = get_object_or_404(Video, id=id)
    if 'ajax' in request.GET:
        # we're not being strict about requiring POST,
        # but let's at least require ajax
        video.tags.remove(tagname)
    return HttpResponse("ok")


@login_required
def remove_tag_from_collection(request, id, tagname):
    collection = get_object_or_404(Collection, id=id)
    if 'ajax' in request.GET:
        # we're not being strict about requiring POST,
        # but let's at least require ajax
        collection.tags.remove(tagname)
    return HttpResponse("ok")


@login_required
@render_to('main/tag.html')
def tag(request, tagname):
    return dict(tag=tagname,
                collection=Collection.objects.filter(
            tags__name__in=[tagname]).order_by("-modified"),
                videos=Video.objects.filter(
            tags__name__in=[tagname]).order_by("-modified"))


@login_required
@render_to('main/tags.html')
def tags(request):
    return dict(tags=Tag.objects.all().order_by("name"))


@login_required
@render_to('main/video_index.html')
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
    paginator = Paginator(videos.order_by('title'), 100)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        videos = paginator.page(page)
    except (EmptyPage, InvalidPage):
        videos = paginator.page(paginator.num_pages)
    params = dict()
    for k, v in request.GET.items():
        params[k] = v
    params.update(dict(videos=videos))
    return params


@login_required
@render_to('main/file_index.html')
def file_index(request):
    files = File.objects.all()
    params = dict()
    facets = []
    for k, v in request.GET.items():
        params[k] = v
        metadatas = Metadata.objects.filter(field=k, value=v)
        files = files.filter(id__in=[m.file_id for m in metadatas])
        facets.append(dict(field=k, value=v))
    paginator = Paginator(files.order_by('video__title'), 100)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        files = paginator.page(page)
    except (EmptyPage, InvalidPage):
        files = paginator.page(paginator.num_pages)
    params.update(dict(files=files, facets=facets))
    return params


@login_required
@render_to('main/add_collection.html')
def add_collection(request):
    if request.method == "POST":
        form = AddCollectionForm(request.POST)
        if form.is_valid():
            suuid = uuid.uuid4()
            s = form.save(commit=False)
            s.uuid = suuid
            s.save()
            form.save_m2m()
            return HttpResponseRedirect(s.get_absolute_url())
    return dict(form=AddCollectionForm())


def operation_info(request, uuid):
    operation = get_object_or_404(Operation, uuid=uuid)
    return HttpResponse(dumps(operation.as_dict()),
                        mimetype="application/json")


@login_required
@render_to('main/operation.html')
def operation(request, uuid):
    operation = get_object_or_404(Operation, uuid=uuid)
    return dict(operation=operation)


def safe_makedirs(d):
    try:
        os.makedirs(d)
    except:
        pass


def save_file_locally(request):
    vuuid = uuid.uuid4()
    source_filename = None
    tmp_filename = ''
    tmpfilename = ''
    if request.POST.get('scan_directory', False):
        source_filename = request.POST.get('source_file', '')
        statsd.incr('main.upload.scan_directory')
    if request.POST.get('tmpfilename', False):
        tmp_filename = request.POST.get('tmpfilename', '')
    if source_filename:
        safe_makedirs(settings.TMP_DIR)
        extension = source_filename.split(".")[-1]
        tmpfilename = settings.TMP_DIR + "/" + str(vuuid) + "."\
            + extension.lower()
        if request.POST.get('scan_directory', False):
            os.rename(settings.WATCH_DIRECTORY\
                          + request.POST.get('source_file'),
                      tmpfilename)
        else:
            tmpfile = open(tmpfilename, 'wb')
            for chunk in request.FILES['source_file'].chunks():
                tmpfile.write(chunk)
            tmpfile.close()
    if tmp_filename.startswith(settings.TMP_DIR):
        tmpfilename = tmp_filename
        filename = os.path.basename(tmpfilename)
        vuuid = os.path.splitext(filename)[0]
        source_filename = tmp_filename

    return (source_filename, tmpfilename, vuuid)


def create_operations(request, v, tmpfilename, source_file, filename):
    operations, params = v.make_default_operations(
        tmpfilename, source_file, request.user)

    if request.POST.get("submit_to_vital", False):
        o, p = v.make_submit_to_podcast_producer_operation(
            tmpfilename, settings.VITAL_PCP_WORKFLOW, request.user)
        operations.append(o)
        params.append(p)
    if request.POST.get("submit_to_youtube", False):
        o, p = v.make_upload_to_youtube_operation(
            tmpfilename, request.user)
        operations.append(o)
        params.append(p)
    # run collection's default workflow(s)
    for cw in v.collection.collectionworkflow_set.all():
        o, p = v.make_submit_to_podcast_producer_operation(
            tmpfilename, cw.workflow, request.user)
        operations.append(o)
        params.append(p)
    return operations, params


def prep_vital_submit(request, v, source_filename):
    if request.POST.get('submit_to_vital', False) \
            and request.POST.get('course_id', False):
        v.make_vital_submit_file(
            source_filename, request.user,
            request.POST['course_id'],
            "",
            settings.VITAL_NOTIFY_URL)


@transaction.commit_manually
@login_required
def upload(request):
    if request.method != "POST":
        transaction.rollback()
        return HttpResponseRedirect("/upload/")

    form = UploadVideoForm(request.POST, request.FILES)
    if not form.is_valid():
        # TODO: give the user proper feedback here
        transaction.rollback()
        return HttpResponseRedirect("/upload/")

    collection_id = None
    operations = []
    params = []
    statsd.incr('main.upload')

    # save it locally
    (source_filename, tmpfilename, vuuid) = save_file_locally(request)
    # important to note here that we allow an "upload" with no file
    # so the user can create a placeholder for a later upload,
    # or to associate existing files/urls with

    # make db entry
    try:
        v = form.save(commit=False)
        v.uuid = vuuid
        v.creator = request.user.username
        collection_id = request.GET.get('collection', None)
        if collection_id:
            v.collection_id = collection_id
        v.save()
        form.save_m2m()
        source_file = v.make_source_file(source_filename)

        if source_filename:
            prep_vital_submit(request, v, source_filename)
            operations, params = create_operations(
                request, v, tmpfilename, source_file, source_filename)
    except:
        statsd.incr('main.upload.failure')
        transaction.rollback()
        raise
    else:
        transaction.commit()
        for o, p in zip(operations, params):
            tasks.process_operation.delay(o.id, p)
    return HttpResponseRedirect("/")


@render_to('main/upload.html')
@login_required
def upload_form(request):
    form = UploadVideoForm()
    collection_id = request.GET.get('collection', None)
    if collection_id:
        collection = get_object_or_404(Collection, id=collection_id)
        form = collection.add_video_form()
    return dict(form=form, collection_id=collection_id)


@login_required
@render_to('main/upload.html')
def scan_directory(request):
    collection_id = None
    file_listing = []
    form = UploadVideoForm()
    collection_id = request.GET.get('collection', None)
    if collection_id:
        collection = get_object_or_404(Collection, id=collection_id)
        form = collection.add_video_form()
    file_listing = os.listdir(settings.WATCH_DIRECTORY)
    return dict(form=form, collection_id=collection_id,
                file_listing=file_listing, scan_directory=True)


def test_upload(request):
    return HttpResponse("a response")


def handle_vital_submit(operation, cunix_path):
    if operation.video.is_vital_submit():
        statsd.incr("vital.done")
        rtsp_url = cunix_path.replace(
            "/media/qtstreams/projects/",
            "rtsp://qtss.cc.columbia.edu/projects/")
        (set_course, username, notify_url) = operation.video.vital_submit()
        if set_course is not None:
            user = User.objects.get(username=username)
            File.objects.create(video=operation.video,
                                label="Quicktime Streaming Video",
                                url=rtsp_url,
                                location_type='rtsp_url')
            vitaltasks.submit_to_vital.delay(
                operation.video.id, user,
                set_course,
                rtsp_url,
                settings.VITAL_SECRET,
                notify_url)
            operation.video.clear_vital_submit()


@transaction.commit_manually
def done(request):
    if 'title' not in request.POST:
        transaction.commit()
        return HttpResponse("expecting a title")
    title = request.POST.get('title', 'no title')
    ouuid = uuidparse(title)
    r = Operation.objects.filter(uuid=ouuid)
    if r.count() != 1:
        transaction.commit()
        return HttpResponse("could not find an operation with that UUID")

    statsd.incr('main.done')
    operations = []
    params = dict()
    try:
        operation = r[0]
        operation.status = "complete"
        operation.save()
        OperationLog.objects.create(operation=operation,
                                    info="PCP completed")

        cunix_path = request.POST.get('movie_destination_path', '')
        if cunix_path.startswith("/www/data/ccnmtl/broadcast/secure/"):
            File.objects.create(video=operation.video,
                                label="CUIT File",
                                filename=cunix_path,
                                location_type='cuit',
                                )
        if cunix_path.startswith("/media/h264"):
            File.objects.create(video=operation.video,
                                label="CUIT H264",
                                filename=cunix_path,
                                location_type='cuit',
                                )

        handle_vital_submit(operation, cunix_path)

        if operation.video.is_mediathread_submit():
            statsd.incr('main.upload.mediathread')
            (set_course, username) = operation.video.mediathread_submit()
            if set_course is not None:
                user = User.objects.get(username=username)
                params['set_course'] = set_course
                o = Operation.objects.create(
                    uuid=uuid.uuid4(),
                    video=operation.video,
                    action="submit to mediathread",
                    status="enqueued",
                    params=dumps(params),
                    owner=user
                    )
                operations.append(o.id)
                o.video.clear_mediathread_submit()
    except:
        statsd.incr('main.upload.failure')
        transaction.rollback()
        raise
    finally:
        transaction.commit()
        for o in operations:
            tasks.process_operation.delay(o, params)

    return HttpResponse("ok")


def posterdone(request):
    if 'title' not in request.POST:
        return HttpResponse("expecting a title")
    title = request.POST.get('title', 'no title')
    uuid = uuidparse(title)
    r = Operation.objects.filter(uuid=uuid)
    if r.count() == 1:
        statsd.incr('main.posterdone')
        operation = r[0]
        cunix_path = request.POST.get('image_destination_path', '')
        poster_url = cunix_path.replace(
            "/www/data/ccnmtl/broadcast/posters/",
            "http://ccnmtl.columbia.edu/broadcast/posters/")

        File.objects.create(video=operation.video,
                            label="CUIT thumbnail image",
                            url=poster_url,
                            location_type='cuitthumb')
        if operation.video.is_vital_submit():
            # vital wants a special one
            File.objects.create(video=operation.video,
                                label="vital thumbnail image",
                                url=poster_url,
                                location_type='vitalthumb')

    return HttpResponse("ok")


@login_required
@render_to('main/video.html')
def video(request, id):
    v = get_object_or_404(Video, id=id)
    return dict(video=v)


@login_required
@render_to('main/file.html')
def file(request, id):
    f = get_object_or_404(File, id=id)
    return dict(file=f)


@login_required
@render_to("main/file_surelink.html")
def file_surelink(request, id):
    f = get_object_or_404(File, id=id)
    PROTECTION_KEY = settings.SURELINK_PROTECTION_KEY
    filename = f.filename
    if filename.startswith("/www/data/ccnmtl/broadcast/"):
        filename = filename[len("/www/data/ccnmtl/broadcast/"):]

    s = SureLink(filename,
                 int(request.GET.get('width', '0')),
                 int(request.GET.get('height', '0')),
                 request.GET.get('captions', ''),
                 request.GET.get('poster', ''),
                 request.GET.get('protection', ''),
                 request.GET.get('authtype', ''),
                 PROTECTION_KEY)

    return dict(
        surelink=s,
        protection=request.GET.get('protection', ''),
        public=request.GET.get('protection', '').startswith('public'),
        public_mp4_download=request.GET.get(
            'protection',
            '') == "public-mp4-download",
        width=request.GET.get('width', ''),
        height=request.GET.get('height', ''),
        captions=request.GET.get('captions', ''),
        filename=filename,
        file=f)


@login_required
@render_to('main/delete_confirm.html')
def delete_file(request, id):
    f = get_object_or_404(File, id=id)
    if request.method == "POST":
        video = f.video
        f.delete()
        return HttpResponseRedirect(video.get_absolute_url())
    else:
        return dict()


@login_required
@render_to('main/delete_confirm.html')
def delete_video(request, id):
    v = get_object_or_404(Video, id=id)
    if request.method == "POST":
        collection = v.collection
        v.delete()
        return HttpResponseRedirect(collection.get_absolute_url())
    else:
        return dict()


@login_required
@render_to('main/delete_confirm.html')
def delete_collection(request, id):
    s = get_object_or_404(Collection, id=id)
    if request.method == "POST":
        s.delete()
        return HttpResponseRedirect("/")
    else:
        return dict()


@login_required
@render_to('main/delete_confirm.html')
def delete_operation(request, id):
    o = get_object_or_404(Operation, id=id)
    if request.method == "POST":
        video = o.video
        o.delete()
        return HttpResponseRedirect(video.get_absolute_url())
    else:
        return dict()


@login_required
@render_to('main/pcp_submit.html')
def video_pcp_submit(request, id):
    video = get_object_or_404(Video, id=id)
    if request.method == "POST":
        statsd.incr('main.video_pcp_submit')
        # send to podcast producer
        tasks.pull_from_tahoe_and_submit_to_pcp.delay(
            video.id,
            request.user,
            request.POST.get('workflow',
                             ''),
            settings.PCP_BASE_URL,
            settings.PCP_USERNAME,
            settings.PCP_PASSWORD)
        return HttpResponseRedirect(video.get_absolute_url())
    try:
        p = PCP(settings.PCP_BASE_URL,
                settings.PCP_USERNAME,
                settings.PCP_PASSWORD)
        workflows = p.workflows()
    except:
        workflows = []
    return dict(video=video, workflows=workflows,
                kino_base=settings.PCP_BASE_URL)


@login_required
@render_to('main/file_pcp_submit.html')
def file_pcp_submit(request, id):
    file = get_object_or_404(File, id=id)
    if request.method == "POST":
        statsd.incr('main.file_pcp_submit')
        video = file.video
        # send to podcast producer
        tasks.pull_from_cuit_and_submit_to_pcp.delay(
            video.id,
            request.user,
            request.POST.get('workflow',
                             ''),
            settings.PCP_BASE_URL,
            settings.PCP_USERNAME,
            settings.PCP_PASSWORD)
        return HttpResponseRedirect(video.get_absolute_url())
    try:
        p = PCP(settings.PCP_BASE_URL,
                settings.PCP_USERNAME,
                settings.PCP_PASSWORD)
        workflows = p.workflows()
    except:
        workflows = []
    return dict(file=file, workflows=workflows,
                kino_base=settings.PCP_BASE_URL)


@login_required
@render_to('main/file_filter.html')
def file_filter(request):

    include_collection = request.GET.getlist('include_collection')
    include_file_types = request.GET.getlist('include_file_types')
    include_video_formats = request.GET.getlist('include_video_formats')
    include_audio_formats = request.GET.getlist('include_audio_formats')

    results = File.objects.filter(
        video__collection__id__in=include_collection
        ).filter(location_type__in=include_file_types)

    all_collection = [(s, str(s.id) in include_collection)
                      for s in Collection.objects.all()]

    all_file_types = [(l, l in include_file_types)
                      for l in list(set([f.location_type
                                         for f in File.objects.all()]))]

    all_video_formats = []
    excluded_video_formats = []
    for vf in [""] + list(set([m.value for m
                               in Metadata.objects.filter(
                    field="ID_VIDEO_FORMAT")])):
        all_video_formats.append((vf, vf in include_video_formats))
        if vf not in include_video_formats:
            excluded_video_formats.append(vf)
            if vf == "":
                excluded_video_formats.append(None)
    all_audio_formats = []
    excluded_audio_formats = []
    for af in [""] + list(set([m.value for m
                               in Metadata.objects.filter(
                    field="ID_AUDIO_FORMAT")])):
        all_audio_formats.append((af, af in include_audio_formats))
        if af not in include_audio_formats:
            excluded_audio_formats.append(af)
            if af == "":
                excluded_audio_formats.append(None)

    files = [f for f in results
             if f.video_format() not in excluded_video_formats
             and f.audio_format() not in excluded_audio_formats]

    return dict(all_collection=all_collection,
                all_video_formats=all_video_formats,
                all_audio_formats=all_audio_formats,
                all_file_types=all_file_types,
                files=files,
                )


@login_required
@render_to('main/bulk_file_operation.html')
def bulk_file_operation(request):
    if request.method == "POST":
        files = [File.objects.get(id=int(f.split("_")[1]))\
                     for f in request.POST.keys() if f.startswith("file_")]
        for file in files:
            video = file.video
            # send to podcast producer
            tasks.pull_from_cuit_and_submit_to_pcp.delay(
                video.id,
                request.user,
                request.POST.get('workflow',
                                 ''),
                settings.PCP_BASE_URL,
                settings.PCP_USERNAME,
                settings.PCP_PASSWORD)
            statsd.incr('main.bulk_file_operation')
        return HttpResponseRedirect("/")
    files = [File.objects.get(id=int(f.split("_")[1]))\
                 for f in request.GET.keys() if f.startswith("file_")]
    try:
        p = PCP(settings.PCP_BASE_URL,
                settings.PCP_USERNAME,
                settings.PCP_PASSWORD)
        workflows = p.workflows()
    except:
        workflows = []
    return dict(files=files, workflows=workflows,
                kino_base=settings.PCP_BASE_URL)


@login_required
def video_zencoder_submit(request, id):
    video = get_object_or_404(Video, id=id)
    if request.method == "POST":
        statsd.incr('main.zencoder_submit')
        tahoe_url = video.tahoe_download_url()
        if not tahoe_url:
            return HttpResponse("not stored in tahoe")
        zen = Zencoder(settings.ZENCODER_API_KEY)
        job = zen.job.create(tahoe_url)
        File.objects.create(video=video,
                            label="zencoder file",
                            url=job.body['outputs'][0]['url'],
                            location_type='zencoder')
        return HttpResponseRedirect(video.get_absolute_url())
    return HttpResponse("POST only")


@login_required
@render_to('main/add_file.html')
def video_add_file(request, id):
    video = get_object_or_404(Video, id=id)
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
def video_select_poster(request, id, image_id):
    video = get_object_or_404(Video, id=id)
    image = get_object_or_404(Image, id=image_id)
    # clear any existing ones for the video
    Poster.objects.filter(video=video).delete()
    Poster.objects.create(video=video, image=image)
    return HttpResponseRedirect(video.get_absolute_url())


@login_required
@render_to('main/workflows.html')
def list_workflows(request):
    error_message = ""
    try:
        p = PCP(settings.PCP_BASE_URL,
                settings.PCP_USERNAME,
                settings.PCP_PASSWORD)
        workflows = p.workflows()
    except Exception, e:
        error_message = str(e)
        workflows = []
    return dict(workflows=workflows,
                error_message=error_message,
                kino_base=settings.PCP_BASE_URL)


@login_required
@render_to("main/search.html")
def search(request):
    q = request.GET.get('q', '')
    results = dict(count=0)
    if q:
        r = Collection.objects.filter(
            Q(title__icontains=q) |
            Q(creator__icontains=q) |
            Q(contributor__icontains=q) |
            Q(language__icontains=q) |
            Q(description__icontains=q) |
            Q(subject__icontains=q) |
            Q(license__icontains=q)
            )
        results['count'] += r.count()
        results['collection'] = r

        r = Video.objects.filter(
            Q(title__icontains=q) |
            Q(creator__icontains=q) |
            Q(language__icontains=q) |
            Q(description__icontains=q) |
            Q(subject__icontains=q) |
            Q(license__icontains=q)
            )
        results['count'] += r.count()
        results['videos'] = r

    return dict(q=q, results=results)


@login_required
@render_to("main/uuid_search.html")
def uuid_search(request):
    uuid = request.GET.get('uuid', '')
    results = dict()
    if uuid:
        for k, label in [(Collection, "collection"), (Video, "video"),
                        (Operation, "operation")]:
            r = k.objects.filter(uuid=uuid)
            if r.count() > 0:
                results[label] = r[0]
                break
    return dict(uuid=uuid, results=results)


def tag_autocomplete(request):
    q = request.GET.get('q', '')
    r = Tag.objects.filter(name__icontains=q)
    return HttpResponse("\n".join([t.name for t in list(r)]))


def subject_autocomplete(request):
    q = request.GET.get('q', '')
    q = q.lower()
    r = Video.objects.filter(subject__icontains=q)
    all_subjects = dict()
    for v in r:
        s = v.subject.lower()
        for p in s.split(","):
            p = p.strip()
            all_subjects[p] = 1
    r = Collection.objects.filter(subject__icontains=q)
    for v in r:
        s = v.subject.lower()
        for p in s.split(","):
            p = p.strip()
            all_subjects[p] = 1

    return HttpResponse("\n".join(all_subjects.keys()))

POSTER_BASE = "http://ccnmtl.columbia.edu/broadcast/posters/vidthumb"
POSTER_OPTIONS = [
    dict(value="default_custom_poster",
         label="broadcast/posters/[media path]/[filename].jpg"),
    dict(value=POSTER_BASE + "_480x360.jpg",
         label="CCNMTL 480x360"),
    dict(value=POSTER_BASE + "_480x272.jpg",
         label="CCNMTL 480x272"),
    dict(value=POSTER_BASE + "_320x240.jpg",
         label="CCNMTL 320x240"),
    ]
PROTECTION_OPTIONS = [
    dict(value="public-mp4-download",
         label="public mp4/mp3 non-streaming"),
    dict(value="public",
         label="public streaming flv"),
    dict(value="protected",
         label="protected streaming flv/protected mp3 (valid-user)"),
]
AUTHTYPE_OPTIONS = [
    dict(value="", label="None (Public)"),
    dict(value="wikispaces",
         label="Wikispaces (Pamacea auth-domain) [authtype=wikispaces]"),
    dict(value="auth",
         label=("Standard UNI (Pamacea domain incompatible with wikispaces)"
                " [authtype=auth]")),
    dict(value="wind",
         label="WIND [authtype=wind]"),
]


@render_to("main/surelink.html")
def surelink(request):
    PROTECTION_KEY = settings.SURELINK_PROTECTION_KEY
    results = []
    if request.GET.get('files', ''):
        for filename in request.GET.get('files', '').split('\n'):
            filename = filename.strip()
            s = SureLink(filename,
                         int(request.GET.get('width', '0')),
                         int(request.GET.get('height', '0')),
                         request.GET.get('captions', ''),
                         request.GET.get('poster', ''),
                         request.GET.get('protection', ''),
                         request.GET.get('authtype', ''),
                         PROTECTION_KEY)
            results.append(s)
    return dict(
        protection=request.GET.get('protection', ''),
        public=request.GET.get('protection', '').startswith('public'),
        public_mp4_download=request.GET.get('protection',
                                            '') == "public-mp4-download",
        width=request.GET.get('width', ''),
        height=request.GET.get('height', ''),
        captions=request.GET.get('captions', ''),
        results=results,
        rows=len(results) * 3,
        files=request.GET.get('files', ''),
        poster=request.GET.get('poster', ''),
        poster_options=POSTER_OPTIONS,
        protection_options=PROTECTION_OPTIONS,
        authtype_options=AUTHTYPE_OPTIONS,
        authtype=request.GET.get('authtype', ''),
        )


@muninview(config="""graph_title Total Videos
graph_vlabel videos""")
def total_videos(request):
    return [("videos", Video.objects.all().count())]


@muninview(config="""graph_title Total Files
graph_vlabel files""")
def total_files(request):
    return [("files", File.objects.all().count())]


@muninview(config="""graph_title Total Operations
graph_vlabel operations""")
def total_operations(request):
    return [("operations", Operation.objects.all().count())]


@muninview(config="""graph_title Total Minutes of video Uploaded
graph_vlabel minutes""")
def total_minutes(request):
    return [("minutes",
             sum([float(str(m.value)) for m in Metadata.objects.filter(
                        field='ID_LENGTH',
                        file__location_type='none')]) / 60.0)]
