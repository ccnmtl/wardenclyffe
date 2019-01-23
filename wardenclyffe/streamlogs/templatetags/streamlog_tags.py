from django import template

from wardenclyffe.streamlogs.models import StreamLog


register = template.Library()


@register.simple_tag
def find_video(filename):
    sl = StreamLog(filename=filename)
    return sl.video()
