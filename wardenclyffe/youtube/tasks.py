from django_statsd.clients import statsd
from django.conf import settings

from json import loads

from wardenclyffe.main.tasks import pull_from_s3
from wardenclyffe.util.mail import send_youtube_submitted_mail
from wardenclyffe.youtube.util import (
    get_authenticated_service, initialize_upload, Args)
from wardenclyffe.main.models import Video, File


def upload_to_youtube(operation):
    params = loads(operation.params)
    video = operation.video
    user = operation.owner
    tmpfilename = params['tmpfilename']
    youtube_upload(video, user, tmpfilename)
    return ("complete", "")


def youtube_upload(video, user, tmpfilename):
    description = video.description
    if len(description) > 4500:
        description = description[:4500] + "..."

    a = Args()
    a.logging_level = 'DEBUG'
    a.file = tmpfilename
    a.title = video.title
    a.description = description
    a.privacyStatus = "private"
    a.keywords = ["education", "columbia"]

    # 27 = "Education". see wardenclyffe/youtube/categories.json
    a.category = "27"
    youtube = get_authenticated_service()
    youtube_key = initialize_upload(youtube, a)

    youtube_url = "http://www.youtube.com/watch?v=%s" % youtube_key

    File.objects.create(video=video, url=youtube_url,
                        location_type="youtube",
                        label="youtube")
    send_youtube_submitted_mail(video.title, user.username, youtube_url)


def pull_from_s3_and_upload_to_youtube(operation):
    statsd.incr("pull_from_s3_and_upload_to_youtube")
    print "pulling from S3"
    params = loads(operation.params)
    video_id = params['video_id']
    video = Video.objects.get(id=video_id)
    suffix = video.extension()
    t = pull_from_s3(suffix, settings.AWS_S3_UPLOAD_BUCKET,
                     video.s3_key())

    operation.log(info="downloaded from S3")
    print "uploading to Youtube"
    youtube_upload(video, operation.owner, t.name)
    t.close()
    return ("complete", "")
