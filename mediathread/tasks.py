import urllib2
from celery.decorators import task
from main.models import Video, File, Operation, OperationFile, OperationLog, Image
import os.path
import uuid 
from django.conf import settings
from restclient import POST
import httplib
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
            'thumb' : video.cuit_poster_url() or video.poster_url(),
            "metadata-creator" : video.creator,
            "metadata-description" : video.description,
            "metadata-subject" : video.subject,
            "metadata-license" : video.license,
            "metadata-language" : video.language,
            "metadata-uuid" : video.uuid,
            "metadata-wardenclyffe-id" : str(video.id),
            }
        if video.cuit_url():
            params['flv_pseudo'] = video.cuit_url()
            params['flv_pseudo-metadata'] = "w%dh%d" % (width,height)
        else:
            params['mp4'] = video.tahoe_download_url()
            params["mp4-metadata"] = "w%dh%d" % (width,height)

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
