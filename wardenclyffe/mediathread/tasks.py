import requests
import waffle
import wardenclyffe.main.models
from django.conf import settings
from django_statsd.clients import statsd
from json import loads
from wardenclyffe.util.mail import send_mediathread_uploaded_mail


def guess_dimensions(video, audio):
    if audio:
        return 160, 120
    return video.get_dimensions()


def mp3_url(video):
    return video.h264_public_stream_url()


def mediathread_submit_params(video, course_id, username, mediathread_secret,
                              audio, width, height):
    params = {
        'set_course': course_id,
        'as': username,
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
    params['thumb'] = video.cuit_poster_url() or video.poster_url()
    if video.has_panopto_source():
        params['mp4_panopto'] = video.mediathread_url()
    elif video.h264_secure_stream_url():
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
    return params


def mediathread_update_params(video, mediathread_secret):
    params = {
        'secret': mediathread_secret,
        "metadata-uuid": video.uuid,
        "metadata-wardenclyffe-id": str(video.id),
        "metadata-tag": "update",
    }
    # asset-url for reference
    params['asset-url'] = video.mediathread_asset_url()
    # the thumbnail may also have changed
    params['thumb'] = video.cuit_poster_url() or video.poster_url()

    if video.has_panopto_source():
        params['mp4_panopto'] = video.panopto_file().filename
    else:
        # only handle the non-audio parameter. afaik, we didn't do audio
        # conversions with the flv, so they shouldn't ever be converted
        params['mp4_pseudo'] = video.h264_secure_stream_url()
    return params


def submit_to_mediathread(operation):
    statsd.incr("mediathread.tasks.submit_to_mediathread")
    params = loads(operation.params)
    video = operation.video
    user = operation.owner
    course_id = params['set_course']
    audio = params['audio']
    mediathread_secret = settings.MEDIATHREAD_SECRET
    mediathread_base = settings.MEDIATHREAD_BASE

    (width, height) = guess_dimensions(video, audio)
    if not video.mediathread_url():
        statsd.incr(
            "mediathread.tasks.submit_to_mediathread.failure.video_url")
        return ("failed", "no video URL")

    params = mediathread_submit_params(
        video, course_id, user.username, mediathread_secret,
        audio, width, height
    )

    r = requests.post(mediathread_base + "save/", params, timeout=30)
    if r.status_code == 200:
        # requests follows redirects, so we need to get the location
        # out of the history
        url = r.history[0].headers['Location']
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


def update_mediathread(operation):
    if not waffle.switch_is_active('mediathread_update'):
        print("mediathread updates are disabled")
        return ("complete", "mediathread updates are temporarily disabled")
    statsd.incr("mediathread.tasks.update_mediathread")
    video = operation.video
    mediathread_secret = settings.MEDIATHREAD_SECRET
    mediathread_base = settings.MEDIATHREAD_BASE

    # assume that width/height stay the same
    # so we just need the new URL and the asset ID
    if not video.mediathread_url():
        statsd.incr(
            "mediathread.tasks.update_mediathread.failure.video_url")
        return ("failed", "no video URL")

    params = mediathread_update_params(video, mediathread_secret)

    r = requests.post(mediathread_base + 'update/', params, timeout=5)
    if r.status_code == 200:
        return ("complete", "")
    elif r.status_code == 404:
        print("Mediathread responded with a 404")
        # mediathread doesn't have this asset anymore. that's fine.
        # we should delete the asset on our end while we're at it
        # since it is outdated.
        video.remove_mediathread_asset()
        # from an operation perspective, we consider this successful
        return ("complete", "")
    else:
        statsd.incr("mediathread.tasks.update_mediathread.failure")
        print(r.status_code)
        print(r.content)
        return ("failed", "mediathread rejected update")
