import factory
from ..models import StreamLog


class StreamLogFactory(factory.DjangoModelFactory):
    class Meta:
        model = StreamLog
    filename = "something.flv"
    remote_addr = "127.0.0.1"
    offset = "0"
    referer = "http://example.com/"
    user_agent = "Chrome"
    access = "cookie"
