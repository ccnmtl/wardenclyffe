import urllib2
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
from django.conf import settings
from angeldust import PCP
from celery.decorators import task
from models import Video, File, Operation, OperationFile, OperationLog, Image
import os.path
import uuid 
import tempfile
import subprocess

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
def make_images(tmpfilename,video_id,user,**kwargs):
    print "making images"
    video = Video.objects.get(id=video_id)
    ouuid = uuid.uuid4()
    operation = Operation.objects.create(video=video,
                                         action="make images",
                                         status="in progress",
                                         params="",
                                         owner=user,
                                         uuid=ouuid)
    try:
        size = os.stat(tmpfilename)[6] / (1024 * 1024)
        frames = size * 2 # 2 frames per MB at the most
        if tmpfilename.lower().endswith("avi"):
            command = "/usr/bin/ionice -c 3 /usr/bin/mplayer -nosound -vo jpeg:outdir=/tmp/tna/imgs/ -endpos 03:00:00 -frames %d -sstep 10 -correct-pts '%s'" % (frames,tmpfilename)
        else:
            command = "/usr/bin/ionice -c 3 /usr/bin/mplayer -nosound -vo jpeg:outdir=/tmp/tna/imgs/ -endpos 03:00:00 -frames %d -sstep 10 '%s'" % (frames,tmpfilename)
        print command
        os.system(command)
        imgs = os.listdir("/tmp/tna/imgs/")
        if len(imgs) == 0:
            print "failed to create images. falling back to framerate hack"
            command = "/usr/bin/ionice -c 3 /usr/bin/mplayer -nosound -vo jpeg:outdir=/tmp/tna/imgs/ -endpos 03:00:00 -frames %d -vf framerate=250 '%s'" % (frames,tmpfilename)
            os.system(command)
        imgdir = "/var/www/tna/uploads/images/%05d/" % video.id
        try:
            os.makedirs(imgdir)
        except:
            pass
        imgs = os.listdir("/tmp/tna/imgs/")
        imgs.sort()
        for img in imgs:
            os.system("mv /tmp/tna/imgs/%s %s" % (img,imgdir))
            i = Image.objects.create(video=video,image="images/%05d/%s" % (video.id,img))

        operation.status = "complete"
        operation.save()
        log = OperationLog.objects.create(operation=operation,
                                          info="created %d images" % len(imgs))
    except Exception, e:
        operation.status = "failed"
        operation.save()
        log = OperationLog.objects.create(operation=operation,
                                          info=str(e))

            
@task(ignore_results=True)
def extract_metadata(tmpfilename,video_id,user,source_file_id,**kwargs):
    print "extracting metadata"
    video = Video.objects.get(id=video_id)
    source_file = File.objects.get(id=source_file_id)
    ouuid = uuid.uuid4()
    operation = Operation.objects.create(video=video,
                                         action="extract metadata",
                                         status="in progress",
                                         params="",
                                         owner=user,
                                         uuid=ouuid)
    try:
        # warning: for now we're expecting the midentify script
        # to be relatively located to this file. this ought to 
        # be a bit more configurable
        pwd = os.path.dirname(__file__)
        script_dir = os.path.join(pwd,"../scripts/")
        output = subprocess.Popen([os.path.join(script_dir,"midentify.sh"), tmpfilename], stdout=subprocess.PIPE).communicate()[0]
        pairs = [l.strip().split("=") for l in output.split("\n")]
        for line in output.split("\n"):
            try:
                line = line.strip()
                (f,v) = line.split("=")
                source_file.set_metadata(f,v)
            except Exception, e:
                # just ignore any parsing issues
                print str(e)
        operation.status = "complete"
        operation.save()
        print "finished extracting metadata"
    except Exception, e:
        operation.status = "failed"
        operation.save()
        log = OperationLog.objects.create(operation=operation,
                                          info=str(e))
        print "failed to extract metadata"

    

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

    if workflow == "":
        operation.status = "failed"
        log = OperationLog.objects.create(operation=operation,
                                          info="no workflow specified")
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
        print "submitted with filename %s" % filename
        title = "[" + str(ouuid) + "]" + video.title
        print "submitted with title %s" % title
        pcp.upload_file(t,filename,workflow, title, video.description)
        operation.status = "submitted"
        log = OperationLog.objects.create(operation=operation,
                                          info="submitted to PCP")

    except Exception, e:
        operation.status = "failed"
        log = OperationLog.objects.create(operation=operation,
                                          info=str(e))
    operation.save()
    print "finished submitting to PCP"
    
