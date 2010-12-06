import urllib2
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
from django.conf import settings
from angeldust import PCP
from celery.decorators import task
from models import Video, File, Operation, OperationFile, OperationLog
import os.path
import uuid 
import tempfile


@task(ignore_result=True)
def save_file_to_tahoe(tmpfilename,video_id,filename,user,**kwargs):
    print "saving to tahoe"
    video = Video.objects.get(id=video_id)
    ouuid = uuid.uuid4()
    operation = Operation.objects.create(video=video,
                                         action="save to tahoe",
                                         status="in progress",
                                         params="",
                                         owner=user,
                                         uuid=ouuid)
    try:
        source_file = open(tmpfilename,"rb")
        register_openers()
        datagen, headers = multipart_encode((
            ("t","upload"),
            MultipartParam(name='file',fileobj=source_file,filename=os.path.basename(tmpfilename))))
        request = urllib2.Request(settings.TAHOE_BASE, datagen, headers)
        cap = urllib2.urlopen(request).read()
        source_file.close()
        print "finished saving to tahoe"
        operation.status = "complete"
        f = File.objects.create(video=video,url="",cap=cap,location_type="tahoe",
                                filename=filename,
                                label="uploaded source file")

        of = OperationFile.objects.create(operation=operation,file=f)
    except Exception, e:
        operation.status = "failed"
        log = OperationLog.objects.create(operation=operation,
                                          info=str(e))
        
    operation.save()


    

@task(ignore_result=True)
def submit_to_podcast_producer(tmpfilename,video_id,user,workflow,**kwargs):
    print "submitting to PCP"
    video = Video.objects.get(id=video_id)
    ouuid = uuid.uuid4()
    operation = Operation.objects.create(video=video,
                                         owner=user,
                                         action="submit to podcast producer",
                                         status="in progress",
                                         params="workflow: %s" % workflow,
                                         uuid=ouuid,
                                         )
    pcp = PCP(settings.PCP_BASE_URL,
              settings.PCP_USERNAME,
              settings.PCP_PASSWORD)
    filename = str(ouuid) + ".mp4"
    fileobj = open(tmpfilename)
    try:
        pcp.upload_file(fileobj,filename,workflow,video.title,video.description)
        operation.status = "submitted"
    except Exception, e:
        operation.status = "failed"
        log = OperationLog.objects.create(operation=operation,
                                          info=str(e))
    operation.save()
    print "finished submitting to PCP"


@task(ignore_result=True)
def pull_from_tahoe_and_submit_to_pcp(video_id,user,workflow,**kwargs):
    print "pulling from tahoe"
    video = Video.objects.get(id=video_id)
    ouuid = uuid.uuid4()
    operation = Operation.objects.create(video=video,
                                         owner=user,
                                         action="pull from tahoe and submit to pcp",
                                         status="in progress",
                                         params="workflow: %s" % workflow,
                                         uuid=ouuid,
                                         )
    url = video.tahoe_download_url()
    if url == "":
        operation.status = "failed"
        log = OperationLog.objects.create(operation=operation,
                                          info="does not have a tahoe stored file")

        operation.save()
        return

    filename = video.filename()
    suffix = os.path.splitext(filename)[1]
    t = tempfile.NamedTemporaryFile(suffix=suffix)
    try:
        r = urllib2.urlopen(url)
        t.write(r.read())
        t.seek(0)
        log = OperationLog.objects.create(operation=operation,
                                          info="downloaded from tahoe")
    except Exception, e:
        log = OperationLog.ojbects.create(operation=operation,
                                          info=str(e))
        operation.status = "failed"
        operation.save()
        return

    print "submitting to PCP"
    pcp = PCP(settings.PCP_BASE_URL,
              settings.PCP_USERNAME,
              settings.PCP_PASSWORD)
    filename = str(ouuid) + ".mp4"
    try:
        pcp.upload_file(t,filename,workflow,video.title,video.description)
        operation.status = "submitted"
    except Exception, e:
        operation.status = "failed"
        log = OperationLog.objects.create(operation=operation,
                                          info=str(e))
    operation.save()
    print "finished submitting to PCP"
