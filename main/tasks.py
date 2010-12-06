import urllib2
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
from django.conf import settings
from angeldust import PCP
from celery.decorators import task
from models import Video, File, Operation, OperationFile
import os.path
import uuid 

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
    except:
        operation.status = "failed"
    operation.save()


    

@task(ignore_result=True)
def submit_to_podcast_producer(tmpfilename,video_id,user,**kwargs):
    print "submitting to PCP"
    video = Video.objects.get(id=video_id)
    ouuid = uuid.uuid4()
    operation = Operation.objects.create(video=video,
                                         owner=user,
                                         action="submit to podcast producer",
                                         status="in progress",
                                         params="",
                                         uuid=ouuid,
                                         )
    pcp = PCP(settings.PCP_BASE_URL,
              settings.PCP_USERNAME,
              settings.PCP_PASSWORD)
    filename = str(ouuid) + ".mp4"
    fileobj = open(tmpfilename)
    try:
        pcp.upload_file(fileobj,filename,settings.PCP_WORKFLOW,video.title,video.description)
        operation.status = "submitted"
    except:
        operation.status = "failed"
    operation.save()
    print "finished submitting to PCP"
