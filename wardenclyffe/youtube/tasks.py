import wardenclyffe.main.models
from wardenclyffe.util.mail import send_youtube_submitted_mail
from wardenclyffe.youtube.util import (
    get_authenticated_service, initialize_upload, Args)
from json import loads


def upload_to_youtube(operation):
    params = loads(operation.params)
    video = operation.video
    user = operation.owner
    tmpfilename = params['tmpfilename']

    description = video.description
    if len(description) > 4500:
        description = description[:4500] + "..."

    a = Args()
    a.logging_level = 'DEBUG'
    a.noauth_local_webserver = 'http://localhost:8000/'
    youtube = get_authenticated_service(a)
    a.file = tmpfilename
    a.title = video.title
    a.description = description
    a.privacyStatus = "private"
    a.keywords = ["education", "columbia"]

    # actually don't know what the right value is for this yet
    # it should map to this (from v2):
#        category=gdata.media.Category(
#            text='Education',
#            scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
#            label='Education'),
    a.category = "22"
    youtube_key = initialize_upload(youtube, a)

    youtube_url = "http://www.youtube.com/watch?v=%s" % youtube_key

    wardenclyffe.main.models.File.objects.create(video=video, url=youtube_url,
                                                 location_type="youtube",
                                                 label="youtube")
    send_youtube_submitted_mail(video.title, user.username, youtube_url)

    return ("complete", "")
