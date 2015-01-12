import wardenclyffe.main.models
from django.conf import settings
from restclient import POST
from wardenclyffe.util.mail import send_mediathread_uploaded_mail
from django_statsd.clients import statsd


def guess_dimensions(video, audio):
    if audio:
        return 160, 120
    return video.get_dimensions()


def mp3_url(video):
    return video.h264_public_stream_url()


def submit_to_mediathread(operation, params):
    statsd.incr("mediathread.tasks.submit_to_mediathread")
    video = operation.video
    user = operation.owner
    course_id = params['set_course']
    audio = params['audio']
    mediathread_secret = settings.MEDIATHREAD_SECRET
    mediathread_base = settings.MEDIATHREAD_BASE
    params = {
        'set_course': course_id,
        'as': user.username,
        'secret': mediathread_secret,
        'title': video.title,
        "metadata-creator": video.creator,
        "metadata-description": video.description,
        "metadata-subject": video.subject,
        "metadata-license": video.license,
        "metadata-language": video.language,
        "metadata-uuid": video.uuid,
        "metadata-wardenclyffe-id": str(video.id),
        "metadata-tag": "upload",
    }

    (width, height) = guess_dimensions(video, audio)
    if not width or not height:
        statsd.incr(
            "mediathread.tasks.submit_to_mediathread.failure.dimensions")
        return ("failed", "could not figure out dimensions")
    if not video.mediathread_url():
        statsd.incr(
            "mediathread.tasks.submit_to_mediathread.failure.video_url")
        return ("failed", "no video URL")
    params['thumb'] = video.cuit_poster_url() or video.poster_url()
    if video.h264_secure_stream_url():
        # prefer h264 secure pseudo stream
        if audio:
            params['mp4_audio'] = video.h264_secure_stream_url()
        else:
            params['mp4_pseudo'] = video.h264_secure_stream_url()
        params["mp4-metadata"] = "w%dh%d" % (width, height)
    elif video.mediathread_url():
        # try flv pseudo stream as a fallback
        params['flv_pseudo'] = video.mediathread_url()
        params['flv_pseudo-metadata'] = "w%dh%d" % (width, height)
    else:
        # eventually we probably also want to try
        # h264 public streams
        pass

    resp, content = POST(mediathread_base + "/save/",
                         params=params, async=False, resp=True)
    if resp.status == 302:
        url = resp['location']
        f = wardenclyffe.main.models.File.objects.create(
            video=video,
            url=url, cap="",
            location_type="mediathread",
            filename="",
            label="mediathread")
        wardenclyffe.main.models.OperationFile.objects.create(
            operation=operation, file=f)

        send_mediathread_uploaded_mail(video.title, user.username, url)

        return ("complete", "")
    else:
        statsd.incr("mediathread.tasks.submit_to_mediathread.failure")
        return ("failed", "mediathread rejected submission")
