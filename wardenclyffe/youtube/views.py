import uuid

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from wardenclyffe.main.models import Video, Collection, File
import wardenclyffe.main.tasks
from django.db import transaction
from django_statsd.clients import statsd
from wardenclyffe.main.views import key_from_s3url


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
    return HttpResponseRedirect("/youtube/done/")


def youtube_done(request):
    return render(request, 'main/youtube_done.html', dict())
