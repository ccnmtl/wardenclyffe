import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import (
    HttpResponseBadRequest, HttpResponseRedirect, HttpResponse)
from django.shortcuts import render, get_object_or_404
from django.views.generic.base import View
from django_statsd.clients import statsd
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.contrib import xsrfutil
from oauth2client.contrib.django_util.storage import DjangoORMStorage

from wardenclyffe.main.models import Video, Collection, File
import wardenclyffe.main.tasks
from wardenclyffe.main.views import key_from_s3url, enqueue_operations
from wardenclyffe.mediathread.views import AuthenticatedNonAtomic

from .models import Credentials
from .util import YOUTUBE_UPLOAD_SCOPE


@login_required
def youtube(request):
    return render(request, 'main/youtube.html', dict())


@transaction.non_atomic_requests()
@login_required
def youtube_post(request):
    statsd.incr("youtube.youtube")
    vuuid = uuid.uuid4()

    collection = Collection.objects.filter(title="Youtube").first()
    v = Video.objects.create(
        collection=collection,
        title=request.POST.get(
            "title",
            ("youtube video uploaded by %s" %
             request.user.username)),
        creator=request.user.username,
        description=request.POST.get("description", ""),
        uuid=vuuid)
    s3url = request.POST['s3_url']
    key = key_from_s3url(s3url)
    # we need a source file object in there
    # to attach basic metadata to
    v.make_source_file(key)

    label = "uploaded source file (S3)"
    File.objects.create(video=v, url="", cap=key, location_type="s3",
                        filename=key, label=label)

    operations = [
        v.make_pull_from_s3_and_extract_metadata_operation(
            key=key, user=request.user),
        # we still need to run our own transcode job
        # because that extracts the frames
        v.make_create_elastic_transcoder_job_operation(
            key=key, user=request.user),
        v.make_pull_from_s3_and_upload_to_youtube_operation(
            video_id=v.id, user=request.user
        ),
    ]
    for o in operations:
        wardenclyffe.main.tasks.process_operation.delay(o.id)
    return HttpResponseRedirect(reverse('youtube-done'))


def youtube_done(request):
    return render(request, 'main/youtube_done.html', dict())


def get_flow(request):
    return OAuth2WebServerFlow(
        client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
        client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        scope=YOUTUBE_UPLOAD_SCOPE,
        redirect_uri='https://' + request.get_host() +
        reverse('youtube-oauth2callback'))


class YTAuth(View):
    def get(self, request):
        storage = DjangoORMStorage(
            Credentials, 'email', settings.PRIMARY_YOUTUBE_ACCOUNT,
            'credential')
        credential = storage.get()
        if credential is None or credential.invalid:
            flow = get_flow(request)
            flow.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                           request.user)
            authorize_url = flow.step1_get_authorize_url()
            return HttpResponseRedirect(authorize_url)
        else:
            return HttpResponse("credentials are currently valid")


class OauthCallback(View):
    def get(self, request):
        if not xsrfutil.validate_token(
                settings.SECRET_KEY, str(request.GET['state']),
                request.user):
            return HttpResponseBadRequest()
        flow = get_flow(request)
        credential = flow.step2_exchange(code=request.GET['code'])
        storage = DjangoORMStorage(
            Credentials, 'email', settings.PRIMARY_YOUTUBE_ACCOUNT,
            'credential')
        storage.put(credential)
        return HttpResponseRedirect("/")


class YouTubeCollectionSubmitView(AuthenticatedNonAtomic, View):

    def submit_to_youtube(self, video):
        if video.has_s3_source():
            operations = [
                video.make_pull_from_s3_and_upload_to_youtube_operation(
                    video.id, self.request.user)]
            enqueue_operations(operations)
        elif video.cuit_file():
            operations = [
                video.make_pull_from_cunix_and_upload_to_youtube_operation(
                    video.id, self.request.user)]
            enqueue_operations(operations)

    def get(self, *args, **kwargs):
        collection_id = kwargs.get('pk', None)
        collection = get_object_or_404(Collection, id=collection_id)

        for video in collection.video_set.all():
            self.submit_to_youtube(video)

        messages.add_message(
            self.request, messages.INFO,
            '{} was submitted to YouTube.'.format(collection))

        url = reverse('collection-view', kwargs={'pk': collection_id})
        return HttpResponseRedirect(url)
