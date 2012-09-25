# Create your views here.
from annoying.decorators import render_to
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from wardenclyffe.main.models import Video, Collection
import wardenclyffe.main.tasks
import os
from django.conf import settings
from django.db import transaction
from django_statsd.clients import statsd


@login_required
@render_to('main/youtube.html')
def youtube(request):
    return dict()


@transaction.commit_manually
@login_required
def youtube_post(request):
    statsd.incr("youtube.youtube")
    tmpfilename = request.POST.get('tmpfilename', '')
    operations = []
    params = []
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
            operations, params = v.make_default_operations(
                tmpfilename, source_file, request.user)

            o, p = v.make_upload_to_youtube_operation(
                tmpfilename, request.user)
            operations.append(o)
            params.append(p)
        except:
            statsd.incr("youtube.youtube.failure")
            transaction.rollback()
            raise
        else:
            transaction.commit()
            for o, p in zip(operations, params):
                wardenclyffe.main.tasks.process_operation.delay(o.id, p)
            return HttpResponseRedirect("/youtube/done/")
    else:
        transaction.commit()
        return HttpResponse("no tmpfilename parameter set")


@render_to('main/youtube_done.html')
def youtube_done(request):
    return dict()
