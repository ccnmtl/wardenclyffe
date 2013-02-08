import wardenclyffe.main.models
from django.conf import settings
import httplib
import gdata.youtube
import gdata.youtube.service
from wardenclyffe.util.mail import send_youtube_submitted_mail


def upload_to_youtube(operation, params):
    video = operation.video
    user = operation.owner
    tmpfilename = params['tmpfilename']
    youtube_email = settings.YOUTUBE_EMAIL
    youtube_password = settings.YOUTUBE_PASSWORD
    youtube_source = settings.YOUTUBE_SOURCE
    youtube_developer_key = settings.YOUTUBE_DEVELOPER_KEY
    youtube_client_id = settings.YOUTUBE_CLIENT_ID

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
    if len(description) > 4500:
        description = description[:4500] + "..."

    my_media_group = gdata.media.Group(
        title=gdata.media.Title(text=title),
        description=gdata.media.Description(description_type='plain',
                                            text=description),
        keywords=gdata.media.Keywords(text='education, columbia'),
        category=gdata.media.Category(
            text='Education',
            scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
            label='Education'),
        player=None,
        private=gdata.media.Private()
    )
    video_entry = gdata.youtube.YouTubeVideoEntry(media=my_media_group)
    video_file_location = tmpfilename

    new_entry = yt_service.InsertVideoEntry(video_entry,
                                            video_file_location,
                                            content_type="video/quicktime")

    feed_url = new_entry.id.text
    youtube_key = feed_url[feed_url.rfind('/') + 1:]
    youtube_url = "http://www.youtube.com/watch?v=%s" % youtube_key

    wardenclyffe.main.models.File.objects.create(video=video, url=youtube_url,
                                                 location_type="youtube",
                                                 label="youtube")
    send_youtube_submitted_mail(video.title, user.username, youtube_url)

    return ("complete", "")
