import urllib2
import wardenclyffe.main.models
import os.path
import uuid 
from django.conf import settings
from restclient import POST
import httplib
from wardenclyffe.util.mail import *
from django_statsd.clients import statsd

def submit_to_mediathread(operation,params):
    statsd.incr("mediathread.tasks.submit_to_mediathread")
    video = operation.video
    user = operation.owner
    course_id = params['set_course']
    mediathread_secret = settings.MEDIATHREAD_SECRET
    mediathread_base = settings.MEDIATHREAD_BASE

    (width,height) = video.get_dimensions()
    if not width or not height:
        statsd.incr("mediathread.tasks.submit_to_mediathread.failure.dimensions")
        return ("failed","could not figure out dimensions")
    if not video.mediathread_url() and not video.tahoe_download_url():
        statsd.incr("mediathread.tasks.submit_to_mediathread.failure.video_url")
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
        "metadata-tag" : "upload",
        }
    if video.mediathread_url():
        params['flv_pseudo'] = video.mediathread_url()
        params['flv_pseudo-metadata'] = "w%dh%d" % (width,height)
    else:
        params['mp4'] = video.tahoe_download_url()
        params["mp4-metadata"] = "w%dh%d" % (width,height)

    resp,content = POST(mediathread_base + "/save/",
                        params=params,async=False,resp=True)
    if resp.status == 302:
        url = resp['location']
        f = wardenclyffe.main.models.File.objects.create(video=video,url=url,cap="",
                                                         location_type="mediathread",
                                                         filename="",
                                                         label="mediathread")
        of = wardenclyffe.main.models.OperationFile.objects.create(operation=operation,file=f)

        send_mediathread_uploaded_mail(video.title, user.username, url)

        return ("complete","")
    else:
        statsd.incr("mediathread.tasks.submit_to_mediathread.failure")
        return ("failed","mediathread rejected submission")
