from django.core.mail import send_mail
from django_statsd.clients import statsd
from django.conf import settings
from django.template.loader import get_template
from django.template import Context


def send_to_everyone(subject, body, toaddress, fromaddress):
    """ send email to the user as well as everyone in settings.ANNOY_EMAILS """
    if toaddress:
        send_mail(subject, body, fromaddress, [toaddress], fail_silently=False)
    statsd.incr('event.mail_sent')
    for vuser in settings.ANNOY_EMAILS:
        send_mail(subject, body, fromaddress, [vuser], fail_silently=False)
        statsd.incr('event.mail_sent')


def send_to_videoteam(subject, body, toaddress, fromaddress):
    """ send email to the user as well as settings.VIDEO_TEAM_EMAILS

    we do this because a lot of the slow operations reported are just
    Podcast Producer getting hung. Only the video team can fix those,
    so they get to be the only ones bothered.
    """
    if toaddress:
        send_mail(subject, body, fromaddress, [toaddress], fail_silently=False)
    statsd.incr('event.mail_sent')
    for vuser in settings.VIDEO_TEAM_EMAILS:
        send_mail(subject, body, fromaddress, [vuser], fail_silently=False)
        statsd.incr('event.mail_sent')


def slow_operations_email_body(cnt):
    t = get_template("util/slow_operations_email_body.txt")
    d = Context(dict(cnt=cnt, mcnt=cnt > 1))
    return t.render(d)


def send_slow_operations_email(operations):
    cnt = operations.count()
    subject = "Slow operations detected"
    body = slow_operations_email_body(cnt)
    fromaddress = 'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu'
    send_to_everyone(subject, body, None, fromaddress)


def send_slow_operations_to_videoteam_email(operations):
    cnt = operations.count()
    subject = "Slow operations detected"
    body = slow_operations_email_body(cnt)
    fromaddress = 'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu'
    send_to_videoteam(subject, body, None, fromaddress)


def failed_operation_body(operation, error_message):
    t = get_template("util/failed_operation_email_body.txt")
    d = Context(dict(operation=operation, error_message=error_message))
    return t.render(d)


def send_failed_operation_mail(operation, error_message):
    subject = 'Video upload failed'
    body = failed_operation_body(operation, error_message)
    fromaddress = 'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu'
    send_to_everyone(subject, body, None, fromaddress)


def mediathread_received_body(video_title, uni):
    t = get_template("util/mediathread_received_email_body.txt")
    d = Context(dict(video_title=video_title, uni=uni))
    return t.render(d)


def send_mediathread_received_mail(video_title, uni):
    subject = "Mediathread submission received"
    body = mediathread_received_body(video_title, uni)
    fromaddress = 'ccnmtl-mediathread@columbia.edu'
    toaddress = "%s@columbia.edu" % uni
    send_to_everyone(subject, body, toaddress, fromaddress)


def mediathread_uploaded_body(video_title, uni, url):
    t = get_template("util/mediathread_uploaded_email_body.txt")
    d = Context(dict(video_title=video_title, uni=uni, url=url))
    return t.render(d)


def send_mediathread_uploaded_mail(video_title, uni, url):
    subject = 'Mediathread submission now available'
    body = mediathread_uploaded_body(video_title, uni, url)
    fromaddress = 'ccnmtl-mediathread@columbia.edu'
    toaddress = "%s@columbia.edu" % uni
    send_to_everyone(subject, body, toaddress, fromaddress)


def youtube_submitted_body(video_title, uni, url):
    t = get_template("util/youtube_submitted_email_body.txt")
    d = Context(dict(video_title=video_title, uni=uni, url=url))
    return t.render(d)


def send_youtube_submitted_mail(video_title, uni, url):
    subject = "\"%s\" was submitted to Columbia on YouTube EDU" % video_title
    body = youtube_submitted_body(video_title, uni, url)
    fromaddress = 'wardenclyffe@wardenclyffe.ccnmtl.columbia.edu'
    toaddress = "%s@columbia.edu" % uni
    send_to_everyone(subject, body, toaddress, fromaddress)
