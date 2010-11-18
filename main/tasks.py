import urllib2
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
from django.conf import settings
from angeldust import PCP
from celery.decorators import task
from models import Video
import os.path


@task
def save_file_to_tahoe(tmpfilename,video_id):
    print "saving to tahoe"
    source_file = open(tmpfilename,"rb")
    register_openers()
    datagen, headers = multipart_encode((
        ("t","upload"),
        MultipartParam(name='file',fileobj=source_file,filename=os.path.basename(tmpfilename))))
    request = urllib2.Request(settings.TAHOE_BASE, datagen, headers)
    
    cap = urllib2.urlopen(request).read()
    source_file.close()
    print "finished saving to tahoe"
    video = Video.objects.get(id=video_id)
    video.cap = cap
    video.save()

@task
def submit_to_podcast_producer(tmpfilename,video_id):
    print "submitting to PCP"
    pcp = PCP(settings.PCP_BASE_URL,
              settings.PCP_USERNAME,
              settings.PCP_PASSWORD)
    video = Video.objects.get(id=video_id)
    filename = video.pcp_filename()
    fileobj = open(tmpfilename)
    pcp.upload_file(fileobj,filename,settings.PCP_WORKFLOW,video.title,video.description)
    print "finished submitting to PCP"
