# stdlib imports
import os
import uuid
import requests
import urlparse

import wardenclyffe.main.tasks as tasks

from django.shortcuts import render
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django_statsd.clients import statsd
from json import dumps, loads
from taggit.models import Tag
from wardenclyffe.main.forms import ServerForm, EditCollectionForm
from wardenclyffe.main.forms import VideoForm, AddCollectionForm
from wardenclyffe.main.models import Video, Operation, Collection, File
from wardenclyffe.main.models import Metadata, Image, Poster
from wardenclyffe.main.models import Server
from wardenclyffe.main.models import OperationFile
from surelink.helpers import PROTECTION_OPTIONS
from surelink.helpers import AUTHTYPE_OPTIONS
from surelink import SureLink
from wardenclyffe.util import uuidparse, safe_basename
from wardenclyffe.util.mail import send_mediathread_received_mail

from s3sign.views import SignS3View as BaseSignS3View


def is_staff(user):
    return user and not user.is_anonymous() and user.is_staff


class StaffMixin(object):
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_staff))
    def dispatch(self, *args, **kwargs):
        return super(StaffMixin, self).dispatch(*args, **kwargs)


class IndexView(StaffMixin, TemplateView):
    template_name = 'main/index.html'

    def get_context_data(self, *args, **kwargs):
        return dict(
            collections=Collection.objects.filter(
                active=True).order_by("title"),
            videos=Video.objects.all().order_by("-modified")[:20],
            operations=Operation.objects.all().order_by("-modified")[:20])


class DashboardView(StaffMixin, TemplateView):
    template_name = 'main/dashboard.html'

    def get_context_data(self, *args, **kwargs):
        submitted = self.request.GET.get('submitted', '') == '1'
        status_filters = dict()
        for (status, get_param) in [
            ("failed", 'status_filter_failed'),
            ("complete", 'status_filter_complete'),
            ("submitted", 'status_filter_submitted'),
            ("inprogress", 'status_filter_inprogress'),
            ("enqueued", 'status_filter_enqueued'),
        ]:
            status_filters[status] = self.request.GET.get(
                get_param, not submitted)

        user_filter = self.request.GET.get('user', '')
        collection_filter = int(self.request.GET.get('collection',
                                                     False) or '0')
        d = dict(
            all_collection=Collection.objects.all().order_by("title"),
            all_users=User.objects.all(),
            user_filter=user_filter,
            collection_filter=collection_filter,
            submitted=submitted,
        )
        d.update(status_filters)
        return d


class ReceivedView(View):
    def post(self, request):
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

        else:
            statsd.incr('main.received_failure')

        return HttpResponse("ok")


class RecentOperationsView(StaffMixin, View):
    def get(self, request):
        submitted = request.GET.get('submitted', '') == '1'
        status_filters = []
        for (status, get_param) in [
            ("failed", "status_filter_failed"),
            ("enqueued", "status_filter_enqueued"),
            ("complete", 'status_filter_complete'),
            ("in progress", 'status_filter_inprogress'),
            ("submitted", 'status_filter_submitted'),
        ]:
            if request.GET.get(get_param, not submitted):
                status_filters.append(status)

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
            content_type="application/json")


class MostRecentOperationView(StaffMixin, View):
    def get(self, request):
        qs = Operation.objects.all().order_by("-modified")
        if qs.count():
            return HttpResponse(
                dumps(
                    dict(
                        modified=str(qs[0].modified)[:19])),
                content_type="application/json")
        else:
            return HttpResponse(
                dumps(dict()),
                content_type="application/json")


class SlowOperationsView(StaffMixin, TemplateView):
    template_name = 'main/slow_operations.html'

    def get_context_data(self, *args, **kwargs):
        status_filters = ["enqueued", "in progress", "submitted"]
        operations = Operation.objects.filter(
            status__in=status_filters,
            modified__lt=datetime.now() - timedelta(hours=1)
        ).order_by("-modified")
        return dict(operations=operations)


class ServersListView(StaffMixin, ListView):
    template_name = 'main/servers.html'
    model = Server
    context_object_name = "servers"


class ServerView(StaffMixin, DetailView):
    template_name = 'main/server.html'
    model = Server
    context_object_name = "server"


class DeleteServerView(StaffMixin, DeleteView):
    template_name = 'main/delete_confirm.html'
    model = Server
    success_url = "/server/"


class EditServerView(StaffMixin, UpdateView):
    template_name = 'main/edit_server.html'
    model = Server
    form_class = ServerForm
    context_object_name = "server"


class AddServerView(StaffMixin, View):
    template_name = 'main/add_server.html'

    def post(self, request):
        form = ServerForm(request.POST)
        if form.is_valid():
            suuid = uuid.uuid4()
            s = form.save(commit=False)
            s.uuid = suuid
            s.save()
            form.save_m2m()
            return HttpResponseRedirect(s.get_absolute_url())
        return render(request, self.template_name,
                      dict(form=form))

    def get(self, request):
        return render(request, self.template_name,
                      dict(form=ServerForm()))


class CollectionView(StaffMixin, TemplateView):
    template_name = 'main/collection.html'

    def get_context_data(self, pk):
        collection = get_object_or_404(Collection, pk=pk)
        videos = Video.objects.filter(
            collection=collection).order_by("-modified")
        return dict(
            collection=collection, videos=videos[:20],
            operations=Operation.objects.filter(
                video__collection__id=pk).order_by("-modified")[:20])


class CollectionEditAudioView(StaffMixin, View):
    def post(self, request, pk):
        collection = get_object_or_404(Collection, pk=pk)
        collection.audio = request.POST.get('audio', '') == '1'
        collection.save()
        return HttpResponseRedirect(collection.get_absolute_url())


class ChildrenView(TemplateView):
    """ abstract view for fetching the "children" of an object
    and paginating. don't instantiate this one directly,
    subclass it and set the appropriate fields."""

    def get_context_data(self, pk):
        obj = get_object_or_404(self.model, pk=pk)
        children = self.get_children_qs(obj)
        params = {self.context_object_name: obj}
        paginator = Paginator(children, 100)

        try:
            page = int(self.request.GET.get('page', '1'))
        except ValueError:
            page = 1
        try:
            children = paginator.page(page)
        except (EmptyPage, InvalidPage):
            children = paginator.page(paginator.num_pages)

        for k, v in self.request.GET.items():
            params[k] = v
        params.update({self.context_children_name: children})
        return params


class AllCollectionVideosView(StaffMixin, ChildrenView):
    template_name = 'main/all_collection_videos.html'
    model = Collection
    context_object_name = "collection"
    context_children_name = "videos"

    def get_children_qs(self, obj):
        return obj.video_set.all().order_by("title")


class AllCollectionOperationsView(StaffMixin, ChildrenView):
    template_name = 'main/all_collection_operations.html'
    model = Collection
    context_object_name = "collection"
    context_children_name = "operations"

    def get_children_qs(self, obj):
        return Operation.objects.filter(
            video__collection__id=obj.id).order_by("-modified")


class UserView(StaffMixin, TemplateView):
    template_name = 'main/user.html'

    def get_context_data(self, username):
        user = get_object_or_404(User, username=username)
        return dict(
            viewuser=user,
            operations=Operation.objects.filter(
                owner__id=user.id).order_by("-modified")[:20])


class EditCollectionView(StaffMixin, UpdateView):
    template_name = 'main/edit_collection.html'
    model = Collection
    form_class = EditCollectionForm
    context_object_name = "collection"


class CollectionToggleActiveView(StaffMixin, View):
    def post(self, request, pk):
        collection = get_object_or_404(Collection, id=pk)
        collection.active = not collection.active
        collection.save()
        return HttpResponseRedirect(collection.get_absolute_url())


class EditVideoView(StaffMixin, UpdateView):
    template_name = 'main/edit_video.html'
    model = Video
    form_class = VideoForm
    context_object_name = "video"


class RemoveTagView(View):
    def get(self, request, id, tagname):
        m = get_object_or_404(self.model, id=id)
        if 'ajax' in request.GET:
            # we're not being strict about requiring POST,
            # but let's at least require ajax
            m.tags.remove(tagname)
        return HttpResponse("ok")


class RemoveTagFromVideoView(StaffMixin, RemoveTagView):
    model = Video


class RemoveTagFromCollectionView(StaffMixin, RemoveTagView):
    model = Collection


class TagView(StaffMixin, TemplateView):
    template_name = 'main/tag.html'

    def get_context_data(self, tagname):
        return dict(
            tag=tagname,
            collection=Collection.objects.filter(
                tags__name__in=[tagname]).order_by("-modified"),
            videos=Video.objects.filter(
                tags__name__in=[tagname]).order_by("-modified"))


class TagsListView(StaffMixin, ListView):
    template_name = 'main/tags.html'
    queryset = Tag.objects.all().order_by("name")
    context_object_name = "tags"


class VideoIndexView(StaffMixin, TemplateView):
    template_name = 'main/video_index.html'

    def get_params(self):
        params = dict()
        for k, v in self.request.GET.items():
            params[k] = v
        return params

    def get_videos(self):
        videos = Video.objects.all()
        creators = self.request.GET.getlist('creator')
        if len(creators) > 0:
            videos = videos.filter(creator__in=creators)
        descriptions = self.request.GET.getlist('description')
        if len(descriptions) > 0:
            videos = videos.filter(description__in=descriptions)
        languages = self.request.GET.getlist('language')
        if len(languages) > 0:
            videos = videos.filter(language__in=languages)
        subjects = self.request.GET.getlist('subject')
        if len(subjects) > 0:
            videos = videos.filter(subject__in=subjects)
        licenses = self.request.GET.getlist('license')
        if len(licenses) > 0:
            videos = videos.filter(license__in=licenses)
        return videos

    def get_context_data(self):
        videos = self.get_videos()
        paginator = Paginator(videos.order_by('title'), 100)

        try:
            page = int(self.request.GET.get('page', '1'))
        except ValueError:
            page = 1

        try:
            videos = paginator.page(page)
        except (EmptyPage, InvalidPage):
            videos = paginator.page(paginator.num_pages)
        params = self.get_params()
        params.update(dict(videos=videos))
        return params


class FileIndexView(StaffMixin, TemplateView):
    template_name = 'main/file_index.html'

    def get_context_data(self):
        files = File.objects.all()
        params = dict()
        facets = []
        for k, v in self.request.GET.items():
            params[k] = v
            metadatas = Metadata.objects.filter(field=k, value=v)
            files = files.filter(id__in=[m.file_id for m in metadatas])
            facets.append(dict(field=k, value=v))
        paginator = Paginator(files.order_by('video__title'), 100)

        try:
            page = int(self.request.GET.get('page', '1'))
        except ValueError:
            page = 1

        try:
            files = paginator.page(page)
        except (EmptyPage, InvalidPage):
            files = paginator.page(paginator.num_pages)
        params.update(dict(files=files, facets=facets))
        return params


class AddCollectionView(StaffMixin, CreateView):
    model = Collection
    form_class = AddCollectionForm
    template_name = 'main/add_collection.html'

    def form_valid(self, form):
        suuid = uuid.uuid4()
        s = form.save(commit=False)
        s.uuid = suuid
        s.save()
        form.save_m2m()
        return super(AddCollectionView, self).form_valid(form)


class OperationInfoView(View):
    def get(self, request, uuid):
        operation = get_object_or_404(Operation, uuid=uuid)
        return HttpResponse(dumps(operation.as_dict()),
                            content_type="application/json")


class OperationView(StaffMixin, TemplateView):
    template_name = 'main/operation.html'

    def get_context_data(self, uuid):
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
            os.rename(settings.WATCH_DIRECTORY +
                      request.POST.get('source_file'),
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


def create_operations(request, v, tmpfilename, source_file, filename, idx=''):
    operations = v.make_default_operations(
        tmpfilename, source_file, request.user)

    if request.POST.get("submit_to_youtube" + idx, False):
        o = v.make_upload_to_youtube_operation(
            tmpfilename, request.user)
        operations.append(o)
    if v.collection.audio:
        o = v.make_audio_encode_operation(source_file.id, request.user)
    return operations


@transaction.non_atomic_requests
@login_required
@user_passes_test(is_staff)
def upload(request):
    if request.method != "POST":
        return HttpResponseRedirect("/upload/")

    form = VideoForm(request.POST, request.FILES)
    if not form.is_valid():
        # TODO: give the user proper feedback here
        return HttpResponseRedirect("/upload/")

    collection_id = None
    statsd.incr('main.s3upload')

    vuuid = uuid.uuid4()

    v = form.save(commit=False)
    v.uuid = vuuid
    v.creator = request.user.username
    collection_id = request.GET.get('collection', None)
    if collection_id:
        v.collection_id = collection_id
    v.save()
    form.save_m2m()
    s3url = request.POST['s3_url']

    key = key_from_s3url(s3url)

    # we need a source file object in there
    # to attach basic metadata to
    v.make_source_file(key)

    label = "uploaded source file (S3)"
    if v.collection.audio:
        label = "uploaded source audio (S3)"

    File.objects.create(video=v, url="", cap=key, location_type="s3",
                        filename=key, label=label)
    # trigger operations
    if v.collection.audio:
        operations = [v.make_local_audio_encode_operation(
            key, user=request.user)]
    else:
        operations = [
            v.make_pull_from_s3_and_extract_metadata_operation(
                key=key, user=request.user),
            v.make_create_elastic_transcoder_job_operation(
                key=key, user=request.user)]

    if request.POST.get("submit_to_youtube", False):
        o = v.make_pull_from_s3_and_upload_to_youtube_operation(
            v.id, request.user)
        operations.append(o)

    enqueue_operations(operations)
    return HttpResponseRedirect("/")


def key_from_s3url(s3url):
    # expects something like
    #   https://s3.amazonaws.com/<bucket>/2016/02/29/filename.mp4
    # and returns
    #   2016/02/29/filename.mp4
    r = urlparse.urlparse(s3url)
    if r.netloc == 's3.amazonaws.com':
        return '/'.join(s3url.split('/')[4:])
    else:
        # it's a https://<bucket>.s3.amazonaws.com/ URL
        return '/'.join(s3url.split('/')[3:])


def create_operations_if_source_filename(request, v, tmpfilename,
                                         source_file, source_filename):
    if source_filename:
        return create_operations(
            request, v, tmpfilename, source_file, source_filename)
    return []


def s3_batch_upload(request, collection_id):
    operations = []
    for k in request.POST.keys():
        if not k.startswith('s3url_'):
            continue
        if request.POST[k] == "":
            continue
        (_base, idx) = k.split('_')

        s3url = request.POST[k]
        key = key_from_s3url(s3url)

        vuuid = uuid.uuid4()
        v = Video.objects.create(
            uuid=vuuid,
            collection_id=collection_id,
            creator=request.user.username,
            title=request.POST.get('title_' + idx, key),
            description=request.POST.get('description_' + idx, ""),
            subject=request.POST.get('subject_' + idx, ""),
            license=request.POST.get('license_' + idx, ""),
            language=request.POST.get('language_' + idx, ""),
        )

        source_file = v.make_source_file(key)
        label = "uploaded source file (S3)"
        source_file = File.objects.create(video=v, url="", cap=key,
                                          location_type="s3",
                                          filename=key,
                                          label=label)

        v_operations = [
            v.make_pull_from_s3_and_extract_metadata_operation(
                key=key, user=request.user),
            v.make_create_elastic_transcoder_job_operation(
                key=key, user=request.user)]
        if v.collection.audio:
            o = v.make_audio_encode_operation(source_file.id, request.user)
            v_operations.append(o)
        operations.extend(v_operations)
    return operations


@transaction.non_atomic_requests()
@login_required
@user_passes_test(is_staff)
def batch_upload(request):
    if request.method != "POST":
        return HttpResponseRedirect("/upload/batch/")

    collection_id = None
    operations = []
    statsd.incr('main.batch_upload')
    collection_id = request.POST.get('collection', None)

    if collection_id is None:
        # javascript should prevent this from happening
        # but...
        return HttpResponse("need to pick a collection")

    try:
        operations = s3_batch_upload(request, collection_id)
    except:
        statsd.incr('main.batch_upload.failure')
        raise
    else:
        enqueue_operations(operations)
    return HttpResponseRedirect("/")


def enqueue_operations(operations):
    for o in operations:
        tasks.process_operation.delay(o.id)


class RerunOperationView(StaffMixin, View):
    def post(self, request, operation_id):
        operation = get_object_or_404(Operation, id=operation_id)
        operation.status = "enqueued"
        operation.save()
        tasks.process_operation.delay(operation_id)
        redirect_to = request.META.get(
            'HTTP_REFERER',
            operation.video.get_absolute_url())
        return HttpResponseRedirect(redirect_to)


class UploadFormView(StaffMixin, TemplateView):
    template_name = 'main/upload.html'

    def get_context_data(self):
        form = VideoForm()
        form.fields["collection"].queryset = Collection.objects.filter(
            active=True)
        collection_id = self.request.GET.get('collection', None)
        collection_title = None
        if collection_id:
            collection = get_object_or_404(Collection, id=collection_id)
            collection_title = collection.title
            form = collection.add_video_form()
        return dict(form=form, collection_id=collection_id,
                    collection_title=collection_title)


class BatchUploadFormView(StaffMixin, TemplateView):
    template_name = 'main/batch_upload.html'

    def get_context_data(self):
        form = VideoForm()
        form.fields["collection"].queryset = Collection.objects.filter(
            active=True)
        collection_id = self.request.GET.get('collection', None)
        collection_title = None
        if collection_id:
            collection = get_object_or_404(Collection, id=collection_id)
            collection_title = collection.title
            form = collection.add_video_form()
        return dict(form=form, collection_id=collection_id,
                    collection_title=collection_title)


def test_upload(request):
    return HttpResponse("a response")


def make_cunix_file(operation, cunix_path):
    if cunix_path.startswith(settings.CUNIX_SECURE_DIRECTORY):
        File.objects.create(video=operation.video,
                            label="CUIT File",
                            filename=cunix_path,
                            location_type='cuit',
                            )
    if cunix_path.startswith(settings.CUNIX_H264_DIRECTORY):
        File.objects.create(video=operation.video,
                            label="CUIT H264",
                            filename=cunix_path,
                            location_type='cuit',
                            )


class VideoView(StaffMixin, DetailView):
    template_name = 'main/video.html'
    model = Video
    context_object_name = "video"


class FileView(StaffMixin, TemplateView):
    template_name = 'main/file.html'

    def get_context_data(self, id):
        f = get_object_or_404(File, id=id)
        filename = f.filename
        if filename and filename.startswith(
                settings.CUNIX_BROADCAST_DIRECTORY):
            filename = filename[len(settings.CUNIX_BROADCAST_DIRECTORY):]
        if f.is_h264_secure_streamable():
            filename = f.h264_secure_path()

        return dict(file=f, filename=filename,
                    poster_options=f.poster_options(POSTER_BASE),
                    protection_options=f.protection_options(),
                    authtype_options=f.authtype_options(),
                    )


class FileSurelinkView(StaffMixin, TemplateView):
    template_name = "main/file_surelink.html"

    def get_context_data(self, id):
        f = get_object_or_404(File, id=id)
        PROTECTION_KEY = settings.SURELINK_PROTECTION_KEY
        filename = f.filename
        if filename.startswith(settings.CUNIX_BROADCAST_DIRECTORY):
            filename = filename[len(settings.CUNIX_BROADCAST_DIRECTORY):]
        if f.is_h264_secure_streamable():
            filename = f.h264_secure_path()
        if (self.request.GET.get('protection', '') == 'mp4_public_stream' and
                f.is_h264_public_streamable()):
            filename = f.h264_public_path()
        s = SureLink(filename,
                     int(self.request.GET.get('width', '0')),
                     int(self.request.GET.get('height', '0')),
                     self.request.GET.get('captions', ''),
                     self.request.GET.get('poster', ''),
                     self.request.GET.get('protection', ''),
                     self.request.GET.get('authtype', ''),
                     PROTECTION_KEY)

        return dict(
            surelink=s,
            protection=self.request.GET.get('protection', ''),
            public=self.request.GET.get('protection', '').startswith('public'),
            public_mp4_download=self.request.GET.get(
                'protection',
                '') == "public-mp4-download",
            width=self.request.GET.get('width', ''),
            height=self.request.GET.get('height', ''),
            captions=self.request.GET.get('captions', ''),
            filename=filename,
            file=f,
            poster=self.request.GET.get('poster', ''),
            poster_options=POSTER_OPTIONS,
            protection_options=f.protection_options(),
            authtype_options=f.authtype_options(),
            authtype=self.request.GET.get('authtype', ''),
        )


class DeleteFileView(StaffMixin, View):
    template_name = 'main/delete_confirm.html'

    def post(self, request, id):
        f = get_object_or_404(File, id=id)
        video = f.video
        f.delete()
        return HttpResponseRedirect(video.get_absolute_url())

    def get(self, request, id):
        return render(request, self.template_name, dict())


class DeleteVideoView(StaffMixin, View):
    template_name = 'main/delete_confirm.html'

    def post(self, request, id):
        v = get_object_or_404(Video, id=id)
        collection = v.collection
        v.delete()
        return HttpResponseRedirect(collection.get_absolute_url())

    def get(self, request, id):
        return render(request, self.template_name, dict())


class DeleteCollectionView(StaffMixin, DeleteView):
    template_name = 'main/delete_confirm.html'
    model = Collection
    success_url = "/"


class DeleteOperationView(StaffMixin, View):
    template_name = 'main/delete_confirm.html'

    def post(self, request, id):
        o = get_object_or_404(Operation, id=id)
        video = o.video
        o.delete()
        redirect_to = request.META.get(
            'HTTP_REFERER',
            video.get_absolute_url())
        return HttpResponseRedirect(redirect_to)

    def get(self, request, id):
        return render(request, self.template_name, dict())


class VideoYoutubeUploadView(StaffMixin, View):
    def post(self, request, id):
        video = get_object_or_404(Video, id=id)

        statsd.incr('main.video_youtube_upload')
        o = video.make_pull_from_s3_and_upload_to_youtube_operation(
            video.id, request.user)
        tasks.process_operation.delay(o.id)
        return HttpResponseRedirect(video.get_absolute_url())


class AudioEncodeFileView(StaffMixin, View):
    def post(self, request, pk):
        f = get_object_or_404(File, pk=pk)
        o = f.video.make_audio_encode_operation(f.id, request.user)
        tasks.process_operation.delay(o.id)
        return HttpResponse(f.video.get_absolute_url())


class FileFilterView(StaffMixin, TemplateView):
    template_name = 'main/file_filter.html'

    def get_context_data(self):
        include_collection = self.request.GET.getlist('include_collection')
        include_file_types = self.request.GET.getlist('include_file_types')
        include_video_formats = self.request.GET.getlist(
            'include_video_formats')
        include_audio_formats = self.request.GET.getlist(
            'include_audio_formats')

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
        for vf in [""] + list(
            set(
                [
                    m.value for m
                    in Metadata.objects.filter(
                        field="ID_VIDEO_FORMAT")])):
            all_video_formats.append((vf, vf in include_video_formats))
            if vf not in include_video_formats:
                excluded_video_formats.append(vf)
                if vf == "":
                    excluded_video_formats.append(None)
        all_audio_formats = []
        excluded_audio_formats = []
        for af in [""] + list(
            set(
                [
                    m.value for m
                    in Metadata.objects.filter(
                        field="ID_AUDIO_FORMAT")])):
            all_audio_formats.append((af, af in include_audio_formats))
            if af not in include_audio_formats:
                excluded_audio_formats.append(af)
                if af == "":
                    excluded_audio_formats.append(None)

        files = [f for f in results
                 if f.video_format() not in excluded_video_formats and
                 f.audio_format() not in excluded_audio_formats]

        return dict(all_collection=all_collection,
                    all_video_formats=all_video_formats,
                    all_audio_formats=all_audio_formats,
                    all_file_types=all_file_types,
                    files=files,
                    )


class BulkSurelinkView(StaffMixin, TemplateView):
    template_name = "main/bulk_surelink.html"

    def _videos(self, request):
        r = request.POST if request.method == "POST" else request.GET
        return [get_object_or_404(Video, id=int(f.split("_")[1]))
                for f in r.keys() if f.startswith("video_")]

    def get_context_data(self):
        surelinks = []
        for v in self._videos(self.request):
            f = v.h264_secure_stream_file()
            if f is None:
                continue
            PROTECTION_KEY = settings.SURELINK_PROTECTION_KEY
            filename = f.filename
            if filename.startswith(settings.CUNIX_BROADCAST_DIRECTORY):
                filename = filename[len(settings.CUNIX_BROADCAST_DIRECTORY):]
            if f.is_h264_secure_streamable():
                filename = f.h264_secure_path()
            if (self.request.GET.get(
                    'protection', '') == 'mp4_public_stream' and
                    f.is_h264_public_streamable()):
                filename = f.h264_public_path()
            s = SureLink(filename,
                         int(self.request.GET.get('width', f.get_width())),
                         int(self.request.GET.get('height', f.get_height())),
                         '',
                         v.poster_url(),
                         'mp4_secure_stream',
                         self.request.GET.get('authtype', 'wind'),
                         PROTECTION_KEY)
            surelinks.append(s)
        return dict(
            videos=self._videos(self.request),
            surelinks=surelinks,
            rows=len(surelinks),
        )


class BulkOperationView(StaffMixin, View):
    template_name = 'main/bulk_operation.html'

    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, *args, **kwargs):
        return super(BulkOperationView, self).dispatch(*args, **kwargs)

    def _videos(self, request):
        r = request.POST if request.method == "POST" else request.GET
        return [get_object_or_404(Video, id=int(f.split("_")[1]))
                for f in r.keys() if f.startswith("video_")]

    def post(self, request):
        if request.POST.get('surelink', False):
            query_string = "&".join(
                "video_%d=on" % v.id for v in self._videos(request))
            if query_string != "":
                query_string = "?" + query_string
            return HttpResponseRedirect(
                reverse("bulk-surelink") + query_string)
        return HttpResponse("Unknown action", status=400)

    def get(self, request):
        return render(request, self.template_name, dict(
            videos=self._videos(request)))


class VideoAddFileView(StaffMixin, View):
    template_name = 'main/add_file.html'

    def post(self, request, id):
        video = get_object_or_404(Video, id=id)
        form = video.add_file_form(request.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.video = video
            f.save()
        return HttpResponseRedirect(video.get_absolute_url())

    def get(self, request, id):
        video = get_object_or_404(Video, id=id)
        return render(request, self.template_name, dict(video=video))


class VideoSelectPosterView(StaffMixin, View):
    def get(self, request, id, image_id):
        video = get_object_or_404(Video, id=id)
        image = get_object_or_404(Image, id=image_id)
        # clear any existing ones for the video
        Poster.objects.filter(video=video).delete()
        Poster.objects.create(video=video, image=image)
        return HttpResponseRedirect(video.get_absolute_url())


class SearchView(StaffMixin, TemplateView):
    template_name = "main/search.html"

    def get_context_data(self):
        q = self.request.GET.get('q', '')
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


class UUIDSearchView(StaffMixin, TemplateView):
    template_name = "main/uuid_search.html"

    def get_context_data(self):
        uuid = self.request.GET.get('uuid', '')
        results = dict()
        if uuid:
            for k, label in [
                    (Collection, "collection"),
                    (Video, "video"),
                    (Operation, "operation")]:
                r = k.objects.filter(uuid=uuid)
                if r.count() > 0:
                    results[label] = r[0]
                    break
        return dict(uuid=uuid, results=results)


class TagAutocompleteView(View):
    def get(self, request):
        q = request.GET.get('q', '')
        r = Tag.objects.filter(name__icontains=q)
        return HttpResponse("\n".join([t.name for t in list(r)]))


class SubjectAutocompleteView(View):
    def get(self, request):
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

POSTER_BASE = settings.CUNIX_BROADCAST_URL + "posters/vidthumb"
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


class SureLinkView(TemplateView):
    template_name = "main/surelink.html"

    def get_context_data(self):
        PROTECTION_KEY = settings.SURELINK_PROTECTION_KEY
        results = []
        if self.request.GET.get('files', ''):
            for filename in self.request.GET.get('files', '').split('\n'):
                filename = filename.strip()
                s = SureLink(filename,
                             int(self.request.GET.get('width', '0')),
                             int(self.request.GET.get('height', '0')),
                             self.request.GET.get('captions', ''),
                             self.request.GET.get('poster', ''),
                             self.request.GET.get('protection', ''),
                             self.request.GET.get('authtype', ''),
                             PROTECTION_KEY)
                results.append(s)
        return dict(
            protection=self.request.GET.get('protection', ''),
            public=self.request.GET.get(
                'protection', '').startswith('public'),
            public_mp4_download=self.request.GET.get(
                'protection', '') == "public-mp4-download",
            width=self.request.GET.get('width', ''),
            height=self.request.GET.get('height', ''),
            captions=self.request.GET.get('captions', ''),
            results=results,
            rows=len(results) * 3,
            files=self.request.GET.get('files', ''),
            poster=self.request.GET.get('poster', ''),
            poster_options=POSTER_OPTIONS,
            protection_options=PROTECTION_OPTIONS,
            authtype_options=AUTHTYPE_OPTIONS,
            authtype=self.request.GET.get('authtype', ''),
        )


class SNSView(View):
    def _subscription_confirmation(self, request):
        message = loads(self.body)
        if "SubscribeURL" not in message:
            return HttpResponse("no subscribe url", status=400)
        url = message["SubscribeURL"]
        r = requests.get(url)
        if r.status_code == 200:
            return HttpResponse("OK")
        return HttpResponse("Failed to confirm")

    def _notification(self, request):
        full_message = loads(self.body)
        ets_message = loads(full_message['Message'])
        state = ets_message['state']
        job_id = ets_message['jobId']

        # retrieve matching operation by jobId
        tf = File.objects.filter(
            location_type='transcode',
            cap=job_id,
        )
        if not tf.exists():
            # success report for a non-existent transcoding
            # job. assume it's a duplicate
            return HttpResponse("OK")
        fo = tf.first()
        operation = fo.operationfile_set.first().operation
        fo.delete()

        operations = []
        if state == 'COMPLETED':
            # set it to completed
            operation.status = "complete"
            operation.save()

            # add S3 output file record
            for output in ets_message['outputs']:
                label = "transcoded 480p file (S3)"
                if output['presetId'] == settings.AWS_ET_720_PRESET:
                    label = "transcoded 720p file (S3)"
                f = File.objects.create(
                    video=operation.video,
                    cap=output['key'],
                    location_type="s3",
                    filename=output['key'],
                    label=label)
                OperationFile.objects.create(operation=operation, file=f)
                v = operation.video
                if 'thumbnailPattern' in output:
                    o = v.make_pull_thumbs_from_s3_operation(
                        output['thumbnailPattern'], operation.owner)
                    operations.append(o)
                o = v.make_copy_from_s3_to_cunix_operation(
                    f.id, operation.owner)
                operations.append(o)
        else:
            # set it to failed
            operation.status = "failed"
            operation.save()
            operation.log(info=self.body)
        for o in operations:
            tasks.process_operation.delay(o.id)
        return HttpResponse("OK")

    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, *args, **kwargs):
        return super(SNSView, self).dispatch(*args, **kwargs)

    def post(self, request):
        self.body = request.read()
        if 'HTTP_X_AMZ_SNS_MESSAGE_TYPE' not in self.request.META:
            return HttpResponse("unknown message type", status=400)
        if (self.request.META['HTTP_X_AMZ_SNS_MESSAGE_TYPE'] ==
                'SubscriptionConfirmation'):
            return self._subscription_confirmation(request)
        if (self.request.META['HTTP_X_AMZ_SNS_MESSAGE_TYPE'] ==
                'Notification'):
            return self._notification(request)
        return HttpResponse("unknown message type", status=400)


class SignS3View(BaseSignS3View):
    def get_bucket(self):
        return settings.AWS_S3_UPLOAD_BUCKET

    def extension(self, request):
        object_name = safe_basename(
            request.GET.get(self.get_name_field(), 'unknown.obj'))
        (_, extension) = os.path.splitext(object_name)
        return extension
