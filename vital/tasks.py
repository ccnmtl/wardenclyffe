import urllib2
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
from angeldust import PCP
from celery.decorators import task
from wardenclyffe.main.models import Video, File, Operation, OperationFile, OperationLog, Image
import os.path
import uuid 
import tempfile
import subprocess
from django.conf import settings
from restclient import POST
import httplib
from wardenclyffe.util.mail import *
from django_statsd.clients import statsd

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
def submit_to_vital(video_id,user,course_id,rtsp_url,vital_secret,vital_base,**kwargs):
    statsd.incr("vital.submit_to_vital")
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
            send_vital_uploaded_mail(video.title, user.username, course_id)
            return ("complete","")
        else:
            statsd.incr("vital.submit_to_vital.failure")
            send_vital_failed_mail(video.title, user.username, content)
            return ("failed","vital rejected submission: %s" % content)
    args = [course_id,rtsp_url,vital_secret,vital_base]
    with_operation(_do_submit_to_vital,video,
                   "submit to vital","",
                   user,args,kwargs)
    print "done submitting to vital"
