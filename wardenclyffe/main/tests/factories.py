from django.contrib.auth.models import User
from wardenclyffe.main.models import (
    Collection, Video, File, Operation,
    Server, Image, Poster, OperationFile)
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


class SecureFileFactory(FileFactory):
    filename = ("/media/h264/ccnmtl/secure/"
                "courses/56d27944-4131-11e1-8164-0017f20ea192"
                "-Mediathread_video_uploaded_by_mlp55.mp4")


class CUITFLVFileFactory(FileFactory):
    filename = ("/www/data/ccnmtl/broadcast/secure/"
                "courses/56d27944-4131-11e1-8164-0017f20ea192"
                "-Mediathread_video_uploaded_by_mlp55.flv")


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    username = factory.Sequence(lambda n: "user%03d" % n)
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


class MediathreadSubmitFileFactory(FileFactory):
    FACTORY_FOR = File
    label = "mediathread submit"
    location_type = "mediathreadsubmit"

    @factory.post_generation
    def init_metadata(self, *args):
        self.set_metadata("set_course", "a course")
        self.set_metadata("username", "anp8")
        self.set_metadata("audio", None)


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


class MediathreadFileFactory(FileFactory):
    label = "mediathread"
    location_type = "mediathread"
    url = "http://mediathread.ccnmtl.columbia.edu/asset/5684/"


class S3FileFactory(FileFactory):
    label = "uploaded source file (S3)"
    location_type = "s3"
    cap = "2011/09/28/t6009_005_2011_3_oppenheim_shear_kim1_edit.mov"


class OperationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Operation
    video = factory.SubFactory(VideoFactory)
    action = "s3"
    owner = factory.SubFactory(UserFactory)
    status = "in progress"
    params = "{}"


class OperationFileFactory(factory.DjangoModelFactory):
    FACTORY_FOR = OperationFile
    operation = factory.SubFactory(OperationFactory)
    file = factory.SubFactory(FileFactory)


class ServerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Server
    name = "test server"
    hostname = "testserver.ccnmtl.columbia.edu"
    credentials = ""


class ImageFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Image
    video = factory.SubFactory(VideoFactory)
    image = "images/1234.jpg"


class PosterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Poster
    video = factory.SubFactory(VideoFactory)
    image = factory.SubFactory(ImageFactory)
