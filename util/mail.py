from django.core.mail import send_mail
from django_statsd.clients import statsd
from django.conf import settings

def send_to_everyone(subject,body,toaddress,fromaddress):
    """ send email to the user as well as everyone in settings.ANNOY_EMAILS """
    send_mail(subject, body, fromaddress, [toaddress], fail_silently)
    statsd.incr('event.mail_sent')
    for vuser in settings.ANNOY_EMAILS:
        send_mail(subject, body, fromaddress, [vuser], fail_silently)
        statsd.incr('event.mail_sent')

def send_mediathread_received_mail(video_title,uni):
    subject = "Video submitted to Mediathread"
    body = """
This email confirms that '%s' has been successfully submitted to Mediathread by %s.  

The video is now being processed.  When it is available in your Mediathread course you will receive another email confirmation.  This confirmation should arrive within 24 hours.

If you have any questions, please visit 

    http://support.ccnmtl.columbia.edu/knowledgebase/articles/44003-uploading-video-into-mediathread

""" % (video_title, uni)
    fromaddress = 'ccnmtl-mediathread@columbia.edu'
    toaddress = "%s@columbia.edu" % uni
    send_to_everyone(subject, body, toaddress, fromaddress)


def send_vital_received_mail(video_title,uni):
    subject = 'Video submitted to VITAL', 
    body = """This email confirms that %s has been successfully submitted to VITAL by %s.  

The video is now being processed.  When it appears in your VITAL course library you will receive another email confirmation.  This confirmation should arrive within 24 hours.

If you have any questions, please contact VITAL administrators at ccnmtl-vital@columbia.edu.
""" % (video_title, uni)
    fromaddress = 'ccnmtl-vital@columbia.edu'
    toaddress = "%s@columbia.edu" % uni
    send_to_everyone(subject, body, toaddress, fromaddress)
