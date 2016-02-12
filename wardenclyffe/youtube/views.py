# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from wardenclyffe.main.models import Video, Collection
import wardenclyffe.main.tasks
import os
from django.conf import settings
from django.db import transaction
from django_statsd.clients import statsd


@login_required
def youtube(request):
    return render(request, 'main/youtube.html', dict())


@transaction.non_atomic_requests()
@login_required
def youtube_post(request):
    statsd.incr("youtube.youtube")
    tmpfilename = request.POST.get('tmpfilename', '')
    operations = []
    if tmpfilename.startswith(settings.TMP_DIR):
        # make db entry
        filename = os.path.basename(tmpfilename)
        vuuid = os.path.splitext(filename)[0]
        try:
            collection = Collection.objects.filter(title="Youtube")[0]
            v = Video.objects.create(
                collection=collection,
                title=request.POST.get(
                    "title",
                    ("youtube video uploaded by %s" %
                     request.user.username)),
                creator=request.user.username,
                description=request.POST.get("description", ""),
                uuid=vuuid)
            source_file = v.make_source_file(filename)
            operations = v.make_default_operations(
                tmpfilename, source_file, request.user)

            o = v.make_upload_to_youtube_operation(
                tmpfilename, request.user)
            operations.append(o)
        except:
            statsd.incr("youtube.youtube.failure")
            raise
        else:
            for o in operations:
                wardenclyffe.main.tasks.process_operation.delay(o.id)
            return HttpResponseRedirect("/youtube/done/")
    else:
        return HttpResponse("no tmpfilename parameter set")


def youtube_done(request):
    return render(request, 'main/youtube_done.html', dict())
