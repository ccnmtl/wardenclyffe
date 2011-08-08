import urllib2
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
from angeldust import PCP
from celery.decorators import task
from models import Video, File, Operation, OperationFile, OperationLog, Image
import os.path
import uuid 
import tempfile
import subprocess
from django.conf import settings
from restclient import POST
import httplib
import gdata.youtube
import gdata.youtube.service
from django.core.mail import send_mail

# TODO: convert to decorator
def with_operation(f,video,action,params,user,args,kwargs):
    ouuid = uuid.uuid4()
    operation = Operation.objects.create(video=video,
                                         action=action,
                                         status="in progress",
                                         params=params,
                                         owner=user,
                                         uuid=ouuid)
    try:
        (success,message) = f(video,user,operation,*args,**kwargs)
        operation.status = success
        if operation.status == "failed" or message != "":
            log = OperationLog.objects.create(operation=operation,
                                              info=message)
    except Exception, e:
        operation.status = "failed"
        log = OperationLog.objects.create(operation=operation,
                                          info=str(e))
    operation.save()

@task(ignore_result=True)
def save_file_to_tahoe(tmpfilename,video_id,filename,user,tahoe_base,**kwargs):
    print "saving to tahoe"
    video = Video.objects.get(id=video_id)

    def _do_save_file_to_tahoe(video,user,operation,tmpfilename,
                               filename,tahoe_base,**kwargs):
        source_file = open(tmpfilename,"rb")
        register_openers()
        datagen, headers = multipart_encode((
                ("t","upload"),
                MultipartParam(name='file',fileobj=source_file,
                               filename=os.path.basename(tmpfilename))))
        request = urllib2.Request(tahoe_base, datagen, headers)
        cap = urllib2.urlopen(request).read()
        source_file.close()
        f = File.objects.create(video=video,url="",cap=cap,
                                location_type="tahoe",
                                filename=filename,
                                label="uploaded source file")
        of = OperationFile.objects.create(operation=operation,file=f)
        return ("complete","")

    args = [tmpfilename,filename,tahoe_base]
    with_operation(
        _do_save_file_to_tahoe,video,"save file to tahoe","",
        user,args,kwargs)

@task(ignore_result=True)
def submit_to_mediathread(video_id,user,course_id,mediathread_secret,mediathread_base,**kwargs):
    print "submitting to mediathread"
    video = Video.objects.get(id=video_id)

    action = "submit to mediathread"
    def _do_submit_to_mediathread(video,user,operation,course_id,mediathread_secret,mediathread_base,**kwargs):
        (width,height) = video.get_dimensions()
        if not width or not height:
            return ("failed","could not figure out dimensions")
        if not video.tahoe_download_url():
            return ("failed","no video URL")
        params = {
            'set_course' : course_id,
            'as' : user.username,
            'secret' : mediathread_secret,
            'title' : video.title,
            'mp4' : video.tahoe_download_url(),
            'thumb' : video.poster_url(),
            "mp4-metadata" : "w%dh%d" % (width,height),
            "metadata-creator" : video.creator,
            "metadata-description" : video.description,
            "metadata-subject" : video.subject,
            "metadata-license" : video.license,
            "metadata-language" : video.language,
            "metadata-uuid" : video.uuid,
            "metadata-wardenclyffe-id" : str(video.id),
            }
        resp,content = POST(mediathread_base + "/save/",
                            params=params,async=False,resp=True)
        if resp.status == 302:
            url = resp['location']
            f = File.objects.create(video=video,url=url,cap="",
                                    location_type="mediathread",
                                    filename="",
                                    label="mediathread")
            of = OperationFile.objects.create(operation=operation,file=f)
            return ("complete","")
        else:
            return ("failed","mediathread rejected submission")
    args = [course_id,mediathread_secret,mediathread_base]
    with_operation(_do_submit_to_mediathread,video,
                   "submit to mediathread","",
                   user,args,kwargs)
    print "done submitting to mediathread"

@task(ignore_result=True)
def submit_to_vital(video_id,user,course_id,rtsp_url,vital_secret,vital_base,**kwargs):
    print "submitting to vital"
    video = Video.objects.get(id=video_id)

    action = "submit to vital"
    def _do_submit_to_vital(video,user,operation,course_id,rtsp_url,vital_secret,vital_base,**kwargs):
        (width,height) = video.get_dimensions()
        if not width or not height:
            return ("failed","could not figure out dimensions")
        if not rtsp_url:
            return ("failed","no video URL")
        params = {
            'set_course' : course_id,
            'as' : user.username,
            'secret' : vital_secret,
            'title' : video.title,
            'url' : rtsp_url,
            'thumb' : video.vital_thumb_url(),
            }
        resp,content = POST(vital_base,params=params,async=False,resp=True)
        if resp.status == 302 or resp.status == 200:
            send_mail('VITAL video uploaded', 
                  """Your video, "%s", has been uploaded to VITAL.""" % video.title, 
                  'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu',
                  ["%s@columbia.edu" % user.username], fail_silently=False)
            return ("complete","")
        else:
            return ("failed","vital rejected submission: %s" % content)
    args = [course_id,rtsp_url,vital_secret,vital_base]
    with_operation(_do_submit_to_vital,video,
                   "submit to vital","",
                   user,args,kwargs)
    print "done submitting to vital"

@task(ignore_result=True)
def make_images(tmpfilename,video_id,user,**kwargs):
    video = Video.objects.get(id=video_id)
    def _do_make_images(video,user,operation,**kwargs):
        ouuid = operation.uuid
        tmpdir = settings.TMP_DIR + "/imgs/" + str(ouuid) + "/"
        try:
            os.makedirs(tmpdir)
        except:
            pass
        size = os.stat(tmpfilename)[6] / (1024 * 1024)
        frames = size * 2 # 2 frames per MB at the most
        if tmpfilename.lower().endswith("avi"):
            command = "/usr/bin/ionice -c 3 /usr/bin/mplayer -nosound -vo jpeg:outdir=%s -endpos 03:00:00 -frames %d -sstep 10 -correct-pts '%s' 2>/dev/null" % (tmpdir,frames,tmpfilename)
        else:
            command = "/usr/bin/ionice -c 3 /usr/bin/mplayer -nosound -vo jpeg:outdir=%s -endpos 03:00:00 -frames %d -sstep 10 '%s' 2>/dev/null" % (tmpdir,frames,tmpfilename)
        os.system(command)
        imgs = os.listdir(tmpdir)
        if len(imgs) == 0:
            command = "/usr/bin/ionice -c 3 /usr/bin/mplayer -nosound -vo jpeg:outdir=%s -endpos 03:00:00 -frames %d -vf framerate=250 '%s' 2>/dev/null" % (tmpdir,frames,tmpfilename)
            os.system(command)
        # TODO: parameterize
        imgdir = "/var/www/wardenclyffe/uploads/images/%05d/" % video.id
        try:
            os.makedirs(imgdir)
        except:
            pass
        imgs = os.listdir(tmpdir)
        imgs.sort()
        for img in imgs:
            os.system("mv %s%s %s" % (tmpdir,img,imgdir))
            i = Image.objects.create(video=video,image="images/%05d/%s" % (video.id,img))

        return ("complete","created %d images" % len(imgs))
    with_operation(_do_make_images,video,"make images","",
                   user,[],kwargs)
            
@task(ignore_results=True)
def extract_metadata(tmpfilename,video_id,user,source_file_id,**kwargs):
    video = Video.objects.get(id=video_id)
    def _do_extract_metadata(video,user,operation,tmpfilename,source_file_id,**kwargs):
        source_file = File.objects.get(id=source_file_id)
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
        return ("complete","")
    args = [tmpfilename,source_file_id]
    with_operation(_do_extract_metadata,video,"extract metadata","",
                   user,args,kwargs)

@task(ignore_result=True)
def submit_to_podcast_producer(tmpfilename,video_id,user,workflow,pcp_base_url,pcp_username,pcp_password,**kwargs):
    print "submitting to PCP"
    video = Video.objects.get(id=video_id)
    def _do_submit_to_podcast_producer(video,user,operation,tmpfilename,workflow,pcp_base_url,pcp_username,pcp_password,**kwargs):
        ouuid = operation.uuid
        pcp = PCP(pcp_base_url,pcp_username,pcp_password)
        # TODO: probably don't always want it to be .mp4
        filename = str(ouuid) + ".mp4"
        fileobj = open(tmpfilename)
        title = "%s-%s" % (str(ouuid),video.title)
        title = title.replace(" ","_") # podcast producer not so good with spaces
        print "submitted with title %s" % title
        pcp.upload_file(fileobj,filename,workflow,title,video.description)
        return ("submitted","")
    with_operation(_do_submit_to_podcast_producer,video,"submit to podcast producer",
                   "workflow: %s" % workflow,user,
                   [tmpfilename,workflow,pcp_base_url,pcp_username,pcp_password],
                   kwargs)
    

@task(ignore_result=True)
def pull_from_tahoe_and_submit_to_pcp(video_id,user,workflow,pcp_base_url,pcp_username,pcp_password,**kwargs):
    print "pulling from tahoe"
    video = Video.objects.get(id=video_id)
    args = [workflow,pcp_base_url,pcp_username,pcp_password]
    def _do_pull_from_tahoe_and_submit_to_pcp(video,user,operation,workflow,pcp_base_url,pcp_username,pcp_password,**kwargs):
        ouuid = operation.uuid
        url = video.tahoe_download_url()
        if url == "":
            return ("failed","does not have a tahoe stored file")
        if workflow == "":
            return ("failed","no workflow specified")
        filename = video.filename()
        suffix = os.path.splitext(filename)[1]
        t = tempfile.NamedTemporaryFile(suffix=suffix)
        r = urllib2.urlopen(url)
        t.write(r.read())
        t.seek(0)
        log = OperationLog.objects.create(operation=operation,
                                          info="downloaded from tahoe")
        # TODO: figure out how to re-use submit_to_podcast_producer()
        print "submitting to PCP"
        pcp = PCP(pcp_base_url,pcp_username,pcp_password)
        filename = str(ouuid) + ".mp4"
        print "submitted with filename %s" % filename
        title = "%s-%s" % (str(ouuid),video.title)
        title = title.replace(" ","_") # podcast producer not so good with spaces
        print "submitted with title %s" % title
        pcp.upload_file(t,filename,workflow, title, video.description)
        return ("submitted","submitted to PCP")
    with_operation(_do_pull_from_tahoe_and_submit_to_pcp,video,
                   "pull from tahoe and submit to pcp",
                   "workflow: %s" % workflow,
                   user,args,kwargs)
    
@task(ignore_results=True)
def upload_to_youtube(tmpfilename,video_id,user,
                      youtube_email,youtube_password,
                      youtube_source,youtube_developer_key,
                      youtube_client_id,**kwargs):
    print "uploading to youtube"
    video = Video.objects.get(id=video_id)
    args = [tmpfilename,youtube_email,youtube_password,
            youtube_source,youtube_developer_key,
            youtube_client_id]
    def _do_upload_to_youtube(video,user,operation,tmpfilename,youtube_email,youtube_password,
                              youtube_source,youtube_developer_key,
                              youtube_client_id,**kwargs):
        httplib.MAXAMOUNT = 104857600
        yt_service = gdata.youtube.service.YouTubeService()
        
        yt_service.email = youtube_email
        yt_service.password = youtube_password
        yt_service.source = youtube_source
        yt_service.developer_key = youtube_developer_key
        yt_service.client_id = youtube_client_id
        
        yt_service.ProgrammaticLogin()
 
        title = video.title
        description = video.description

        my_media_group = gdata.media.Group(
            title=gdata.media.Title(text=title),
            description=gdata.media.Description(description_type='plain', text=description),
            keywords=gdata.media.Keywords(text='education, columbia'),
            category=gdata.media.Category(text='Education',
                                          scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
                                          label='Education'),

            player=None,
            private=gdata.media.Private()
            )
        video_entry = gdata.youtube.YouTubeVideoEntry(media=my_media_group)
        video_file_location = tmpfilename

        new_entry = yt_service.InsertVideoEntry(video_entry, video_file_location, content_type="video/quicktime")

        feed_url = new_entry.id.text
        youtube_key = feed_url[feed_url.rfind('/')+1:]
        youtube_url = "http://www.youtube.com/watch?v=%s" % youtube_key

        f = File.objects.create(video=video,url=youtube_url,
                                location_type="youtube",
                                label="youtube")
        send_mail('Youtube video uploaded', 
                  """Your video has been uploaded to the Columbia Youtube account. 
It is available here: %s""" % youtube_url, 
                  'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu',
                  ["%s@columbia.edu" % user.username], fail_silently=False)
        return ("complete","")
    with_operation(_do_upload_to_youtube,
                   video,"upload to youtube","",user,
                   args,kwargs)
        

