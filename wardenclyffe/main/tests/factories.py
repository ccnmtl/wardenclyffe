from django.contrib.auth.models import User
from wardenclyffe.main.models import Collection, Video, File, Operation
import factory
import uuid


class CollectionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Collection
    title = "Mediathread Spring 2012"
    subject = "test subject"
    uuid = factory.LazyAttribute(lambda t: uuid.uuid4())


class VideoFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Video
    title = "test video"
    creator = "anp8"
    subject = "test subject"
    uuid = factory.LazyAttribute(lambda t: uuid.uuid4())
    collection = factory.SubFactory(CollectionFactory)


class FileFactory(factory.DjangoModelFactory):
    FACTORY_FOR = File
    label = "CUIT File"
    location_type = "cuit"
    filename = ("/media/h264/ccnmtl/secure/"
                "courses/56d27944-4131-11e1-8164-0017f20ea192"
                "-Mediathread_video_uploaded_by_mlp55.mp4")
    video = factory.SubFactory(VideoFactory)


class PublicFileFactory(FileFactory):
    filename = ("/media/h264/ccnmtl/public/"
                "courses/56d27944-4131-11e1-8164-0017f20ea192"
                "-Mediathread_video_uploaded_by_mlp55.mp4")


class CUITFLVFileFactory(FileFactory):
    filename = ("/www/data/ccnmtl/broadcast/secure/"
                "courses/56d27944-4131-11e1-8164-0017f20ea192"
                "-Mediathread_video_uploaded_by_mlp55.flv")


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    username = "foo"
    is_staff = True


METADATA = """ID_AUDIO_BITRATE,128000
ID_AUDIO_CODEC,faad
ID_AUDIO_FORMAT,255
ID_AUDIO_ID,0
ID_AUDIO_NCH,2
ID_AUDIO_RATE,48000
ID_CHAPTERS,0
ID_DEMUXER,lavfpref
ID_EXIT,EOF
ID_FILENAME,/var/www/wardenclyffe/tmp//6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov
ID_LENGTH,31.26
ID_SEEKABLE,1
ID_VIDEO_ASPECT,1.3333
ID_VIDEO_BITRATE,0
ID_VIDEO_CODEC,ffh264
ID_VIDEO_FORMAT,avc1
ID_VIDEO_FPS,29.970
ID_VIDEO_HEIGHT,480
ID_VIDEO_ID,1
ID_VIDEO_WIDTH,704"""

METADATA_WITHOUT_DIMENSIONS = """ID_AUDIO_BITRATE,128000
ID_AUDIO_CODEC,faad
ID_AUDIO_FORMAT,255
ID_AUDIO_ID,0
ID_AUDIO_NCH,2
ID_AUDIO_RATE,48000
ID_CHAPTERS,0
ID_DEMUXER,lavfpref
ID_EXIT,EOF
ID_FILENAME,/var/www/wardenclyffe/tmp//6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov
ID_LENGTH,31.26
ID_SEEKABLE,1
ID_VIDEO_ASPECT,1.3333
ID_VIDEO_BITRATE,0
ID_VIDEO_CODEC,ffh264
ID_VIDEO_FORMAT,avc1
ID_VIDEO_FPS,29.970
ID_VIDEO_ID,1"""


class SourceFileFactory(FileFactory):
    FACTORY_FOR = File
    label = "source file"
    location_type = "none"
    filename = "6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov"

    @factory.post_generation
    def init_metadata(self, *args):
        for line in METADATA.split("\n"):
            line = line.strip()
            (k, v) = line.split(",")
            self.set_metadata(k, v)


class DimensionlessSourceFileFactory(FileFactory):
    FACTORY_FOR = File
    label = "source file"
    location_type = "none"
    filename = "6a0dac24-7982-4df3-a1cb-86d52bf4df94.mov"

    @factory.post_generation
    def init_metadata(self, *args):
        for line in METADATA_WITHOUT_DIMENSIONS.split("\n"):
            line = line.strip()
            (k, v) = line.split(",")
            self.set_metadata(k, v)


class TahoeFileFactory(FileFactory):
    label = "uploaded source file"
    location_type = "tahoe"
    cap = ("URI:CHK:dzunkd4hgk6zn4eclrxihmpwcq:"
           "wowscjwczcrih2cjsdgps5igj4ommb43vxsh5m4ludnxrucrbdsa:"
           "3:10:4783186")
    filename = ("/var/www/wardenclyffe/tmp//6a0dac24-7982-"
                "4df3-a1cb-86d52bf4df94.mov")


class MediathreadFileFactory(FileFactory):
    label = "mediathread"
    location_type = "mediathread"
    url = "http://mediathread.ccnmtl.columbia.edu/asset/5684/"


class VitalThumbnailFileFactory(FileFactory):
    label = "vital thumbnail image"
    location_type = "vitalthumb"
    url = ("http://ccnmtl.columbia.edu/broadcast/projects/vital/"
           "thumbs/vital/25b0e81e-42b2-11e1-a13d-0017f20ea192-"
           "Vital_video_uploaded_by_anp8_thumb.png")


class OperationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Operation
    video = factory.SubFactory(VideoFactory)
    action = "tahoe"
    owner = factory.SubFactory(UserFactory)
    status = "in progress"
    params = ""
