import urllib2
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
from angeldust import PCP
from celery.decorators import task
from main.models import Video, File, Operation, OperationFile, OperationLog, Image
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
        send_mail("\"%s\" was submitted to Columbia on YouTube EDU" % video.title, 
                  """This email confirms that "%s" has been successfully submitted to Columbia's YouTube channel by %s.  

Your video will now be reviewed by our staff, and published. When completed, it will be available at the following destination:

YouTube URL: %s

If you have any questions, please contact Columbia's YouTube administrators at ccmtl-youtube@columbia.edu.
""" % (video.title,user.username,youtube_url), 
                  'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu',
                  ["%s@columbia.edu" % user.username], fail_silently=False)
        for vuser in settings.ANNOY_EMAILS:
            send_mail('Youtube video uploaded', 
                      """Your video has been uploaded to the Columbia Youtube account. 
It is available here: %s""" % youtube_url, 
                      'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu',
                      [vuser], fail_silently=False)

        return ("complete","")
    with_operation(_do_upload_to_youtube,
                   video,"upload to youtube","",user,
                   args,kwargs)
        

