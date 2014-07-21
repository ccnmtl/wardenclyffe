from django.db import models
from django_extensions.db.fields import UUIDField
from django_extensions.db.models import TimeStampedModel
from django.contrib.auth.models import User
from sorl.thumbnail.fields import ImageWithThumbnailsField
from django import forms
from taggit.managers import TaggableManager
from south.modelsinspector import add_introspection_rules
from surelink import SureLink
from surelink.helpers import PROTECTION_OPTIONS
from surelink.helpers import AUTHTYPE_OPTIONS
from django.conf import settings
import os.path
from wardenclyffe.util.mail import send_failed_operation_mail
from django_statsd.clients import statsd
import uuid
from json import dumps, loads

add_introspection_rules(
    [],
    ["^django_extensions\.db\.fields\.CreationDateTimeField",
     "django_extensions.db.fields.ModificationDateTimeField",
     "sorl.thumbnail.fields.ImageWithThumbnailsField",
     "django_extensions.db.fields.UUIDField"])


class Collection(TimeStampedModel):
    title = models.CharField(max_length=256)
    creator = models.CharField(max_length=256, default="", blank=True)
    contributor = models.CharField(max_length=256, default="", blank=True)
    language = models.CharField(max_length=256, default="", blank=True)
    description = models.TextField(default="", blank=True, null=True)
    subject = models.TextField(default="", blank=True, null=True)
    license = models.CharField(max_length=256, default="", blank=True)
    active = models.BooleanField(default=True)

    uuid = UUIDField()

    tags = TaggableManager(blank=True)

    def __unicode__(self):
        """
        >>> c = Collection.objects.create(title="foo")
        >>> str(c)
        'foo'
        """
        return self.title

    def get_absolute_url(self):
        """
        >>> c = Collection.objects.create(title="foo")
        >>> c.get_absolute_url().startswith("/collection/")
        True
        """
        return "/collection/%d/" % self.id

    def add_video_form(self):
        class AddVideoForm(forms.ModelForm):
            class Meta:
                model = Video
                exclude = ('collection', )
        return AddVideoForm()


class CollectionWorkflow(models.Model):
    collection = models.ForeignKey(Collection)
    workflow = models.CharField(max_length=256, default="", blank=True)
    label = models.CharField(max_length=256, default="", blank=True)


class Video(TimeStampedModel):
    collection = models.ForeignKey(Collection)
    title = models.CharField(max_length=256)
    creator = models.CharField(max_length=256, default="", blank=True)
    description = models.TextField(default="", blank=True, null=True)
    subject = models.TextField(default="", blank=True, null=True)
    license = models.CharField(max_length=256, default="", blank=True)
    language = models.CharField(max_length=256, default="", blank=True)

    uuid = UUIDField()

    tags = TaggableManager(blank=True)

    def s3_file(self):
        r = self.file_set.filter(location_type='s3')
        if r.count():
            return r[0]
        else:
            return None

    def s3_key(self):
        t = self.s3_file()
        if t:
            return t.cap
        else:
            return None

    def source_file(self):
        r = self.file_set.filter(label='source file')
        if r.count():
            return r[0]
        else:
            return None

    def filename(self):
        r = self.file_set.filter().exclude(filename="").exclude(filename=None)
        if r.count():
            return r[0].filename
        else:
            return "none"

    def extension(self):
        """ guess at the extension of the video.
        prefer the source file
        otherwise, we'll take *anything* with a filename """
        f = self.source_file()
        if f is not None:
            return os.path.splitext(f.filename)[1]
        r = self.file_set.filter().exclude(filename="").exclude(filename=None)
        if r.count():
            return os.path.splitext(r[0].filename)[1]
        return ""

    def get_absolute_url(self):
        """
        >>> c = Collection.objects.create(title="foo")
        >>> v = Video.objects.create(collection=c, title="bar")
        >>> v.get_absolute_url().startswith("/video/")
        True
        """
        return "/video/%d/" % self.id

    def get_oembed_url(self):
        """
        >>> c = Collection.objects.create(title="foo")
        >>> v = Video.objects.create(collection=c, title="bar")
        >>> v.get_oembed_url().startswith("/video/")
        True
        >>> v.get_oembed_url().endswith("/oembed/")
        True
        """
        return "/video/%d/oembed/" % self.id

    def add_file_form(self, data=None):
        class AddFileForm(forms.ModelForm):
            class Meta:
                model = File
                exclude = ('video', )
        if data:
            return AddFileForm(data)
        else:
            return AddFileForm()

    def get_dimensions(self):
        t = self.source_file()
        if t is None:
            return (0, 0)
        return (t.get_width(), t.get_height())

    def cuit_url(self):
        r = self.file_set.filter(location_type="cuit")
        if r.count() > 0:
            f = r[0]
            return f.cuit_public_url()
        return ""

    def mediathread_url(self):
        r = self.file_set.filter(location_type="cuit")
        if r.count() > 0:
            f = r[0]
            return f.mediathread_public_url()
        return ""

    def h264_secure_stream_url(self):
        r = self.file_set.filter(location_type="cuit")
        if r.count() > 0:
            f = r[0]
            if f.is_h264_secure_streamable():
                return f.h264_secure_stream_url()
        return ""

    def h264_public_stream_url(self):
        r = self.file_set.filter(location_type="cuit")
        if r.count() > 0:
            f = r[0]
            if f.is_h264_public_streamable():
                return f.h264_public_stream_url()
        return ""

    def has_poster(self):
        return Poster.objects.filter(video=self).count()

    def poster_url(self):
        return self.poster().url()

    def poster(self):
        r = Poster.objects.filter(video=self)
        if r.count() > 0:
            return r[0]
        else:
            return DummyPoster()

    def cuit_poster_url(self):
        try:
            return File.objects.filter(video=self,
                                       location_type='cuitthumb')[0].url
        except:
            return None

    def is_mediathread_submit(self):
        return self.file_set.filter(
            location_type="mediathreadsubmit").count() > 0

    def mediathread_submit(self):
        r = self.file_set.filter(location_type="mediathreadsubmit")
        if r.count() > 0:
            f = r[0]
            return (f.get_metadata("set_course"),
                    f.get_metadata("username"),
                    f.get_metadata("audio"),
                    f.get_metadata("audio2"),
                    )
        else:
            return (None, None, None)

    def clear_mediathread_submit(self):
        self.file_set.filter(location_type="mediathreadsubmit").delete()

    def cuit_file(self):
        try:
            return self.file_set.filter(location_type="cuit")[0]
        except:
            return None

    def make_mediathread_submit_file(self, filename, user, set_course,
                                     redirect_to, audio=False,
                                     audio2=False):
        submit_file = File.objects.create(video=self,
                                          label="mediathread submit",
                                          filename=filename,
                                          location_type='mediathreadsubmit'
                                          )
        submit_file.set_metadata("username", user.username)
        submit_file.set_metadata("set_course", set_course)
        submit_file.set_metadata("redirect_to", redirect_to)
        if audio:
            submit_file.set_metadata("audio", "True")
        if audio2:
            submit_file.set_metadata("audio2", "True")

    def make_extract_metadata_operation(self, tmpfilename, source_file, user):
        params = dict(tmpfilename=tmpfilename,
                      source_file_id=source_file.id)
        o = Operation.objects.create(uuid=uuid.uuid4(),
                                     video=self,
                                     action="extract metadata",
                                     status="enqueued",
                                     params=dumps(params),
                                     owner=user)
        return (o, params)

    def make_save_file_to_s3_operation(self, tmpfilename, user):
        params = dict(tmpfilename=tmpfilename, filename=tmpfilename)
        o = Operation.objects.create(uuid=uuid.uuid4(),
                                     video=self,
                                     action="save file to S3",
                                     status="enqueued",
                                     params=dumps(params),
                                     owner=user)
        return (o, params)

    def make_make_images_operation(self, tmpfilename, user):
        params = dict(tmpfilename=tmpfilename)
        o = Operation.objects.create(uuid=uuid.uuid4(),
                                     video=self,
                                     action="make images",
                                     status="enqueued",
                                     params=dumps(params),
                                     owner=user)
        return o, params

    def make_import_from_cuit_operation(self, video_id, user):
        params = dict(video_id=video_id)
        o = Operation.objects.create(uuid=uuid.uuid4(),
                                     video=self,
                                     action="import from cuit",
                                     status="enqueued",
                                     params=dumps(params),
                                     owner=user)
        return o, params

    def make_pull_from_s3_and_submit_to_pcp_operation(self, video_id,
                                                      workflow, user):
        params = dict(video_id=video_id, workflow=workflow)
        o = Operation.objects.create(
            uuid=uuid.uuid4(),
            video=self,
            action="pull from s3 and submit to pcp",
            status="enqueued",
            params=dumps(params),
            owner=user)
        return o, params

    def make_pull_from_cuit_and_submit_to_pcp_operation(self, video_id,
                                                        workflow, user):
        params = dict(video_id=video_id, workflow=workflow)
        o = Operation.objects.create(
            uuid=uuid.uuid4(),
            video=self,
            action="pull from cuit and submit to pcp",
            status="enqueued",
            params=dumps(params),
            owner=user)
        return o, params

    def make_submit_to_podcast_producer_operation(
            self, tmpfilename, workflow, user):
        params = dict(tmpfilename=tmpfilename,
                      pcp_workflow=workflow)
        o = Operation.objects.create(
            uuid=uuid.uuid4(),
            video=self,
            action="submit to podcast producer",
            status="enqueued",
            params=dumps(params),
            owner=user)
        return o, params

    def make_upload_to_youtube_operation(self, tmpfilename, user):
        params = dict(tmpfilename=tmpfilename)
        o = Operation.objects.create(uuid=uuid.uuid4(),
                                     video=self,
                                     action="upload to youtube",
                                     status="enqueued",
                                     params=dumps(params),
                                     owner=user)
        return o, params

    def make_source_file(self, filename):
        return File.objects.create(video=self,
                                   label="source file",
                                   filename=filename,
                                   location_type='none')

    def make_default_operations(self, tmpfilename, source_file, user,
                                audio=False, audio2=False):
        operations = []
        params = []
        if not audio and not audio2:
            o, p = self.make_extract_metadata_operation(
                tmpfilename, source_file, user)
            operations.append(o)
            params.append(p)

        o, p = self.make_save_file_to_s3_operation(
            tmpfilename, user)
        operations.append(o)
        params.append(p)

        if not audio and not audio2:
            o, p = self.make_make_images_operation(
                tmpfilename, user)
            operations.append(o)
            params.append(p)
        return operations, params

    def upto_hundred_images(self):
        """ return the first 100 frames for the video

        some really long videos end up with thousands of frames
        which takes sorl a long time to thumbnail and makes
        the page really slow. There's really no good reason
        to show *all* those images. The first hundred or so
        ought to be enough to select a poster from """
        return self.image_set.all()[:100]


class WrongFileType(Exception):
    pass


class FileType(object):
    def __init__(self, file):
        self.file = file


class CUITFile(FileType):
    pass


class S3File(FileType):
    pass


class File(TimeStampedModel):
    video = models.ForeignKey(Video)
    label = models.CharField(max_length=256, blank=True, null=True, default="")
    url = models.URLField(default="", blank=True, null=True, max_length=2000)
    cap = models.CharField(max_length=256, default="", blank=True, null=True)
    filename = models.CharField(max_length=256, blank=True, null=True,
                                default="")
    location_type = models.CharField(max_length=256, default="s3",
                                     choices=(('pcp', 'pcp'),
                                              ('cuit', 'cuit'),
                                              ('youtube', 'youtube'),
                                              ('s3', 's3'),
                                              ('none', 'none')))

    def filetype(self):
        tmap = dict(
            cuit=CUITFile,
            s3=S3File,
        )
        return tmap.get(self.location_type, FileType)(self)

    def set_metadata(self, field, value):
        r = Metadata.objects.filter(file=self, field=field)
        if r.count():
            # update
            m = r[0]
            m.value = value
            m.save()
        else:
            # add
            m = Metadata.objects.create(file=self, field=field, value=value)

    def get_metadata(self, field):
        r = Metadata.objects.filter(file=self, field=field)
        if r.count():
            return r[0].value
        else:
            return None

    def get_absolute_url(self):
        return "/file/%d/" % self.id

    def get_width(self):
        r = self.metadata_set.filter(field="ID_VIDEO_WIDTH")
        if r.count() > 0:
            return int(r[0].value)
        else:
            return 0

    def get_height(self):
        r = self.metadata_set.filter(field="ID_VIDEO_HEIGHT")
        if r.count() > 0:
            return int(r[0].value)
        else:
            return 0

    # for these, if we don't know our width/height,
    # we see if the video has a source file associated
    # with it that may have the dimensions
    def guess_width(self):
        r = self.metadata_set.filter(field="ID_VIDEO_WIDTH")
        if r.count() > 0:
            return int(r[0].value)
        else:
            try:
                return self.video.get_dimensions()[0]
            except:
                return None

    def guess_height(self):
        r = self.metadata_set.filter(field="ID_VIDEO_HEIGHT")
        if r.count() > 0:
            return int(r[0].value)
        else:
            try:
                return self.video.get_dimensions()[1]
            except:
                return None

    def surelinkable(self):
        return self.location_type == 'cuit'

    def has_cuit_poster(self):
        return File.objects.filter(video=self.video,
                                   location_type='cuitthumb').count() > 0

    def cuit_poster_url(self):
        return File.objects.filter(video=self.video,
                                   location_type='cuitthumb')[0].url

    def cuit_public_url(self):
        filename = self.filename[len(settings.CUNIX_BROADCAST_DIRECTORY):]
        return "%s%s" % (settings.FLV_STREAM_BASE_URL, filename)

    def mediathread_public_url(self):
        PROTECTION_KEY = settings.SURELINK_PROTECTION_KEY
        filename = self.filename
        if filename.startswith(settings.CUNIX_BROADCAST_DIRECTORY):
            filename = filename[len(settings.CUNIX_BROADCAST_DIRECTORY):]

        s = SureLink(filename=filename, width=0, height=0,
                     captions='', poster='', protection="public",
                     authtype='', protection_key=PROTECTION_KEY)
        return s.public_url()

    def is_h264_secure_streamable(self):
        if self.filename is None:
            return False
        return self.filename.startswith(settings.H264_SECURE_STREAM_DIRECTORY)

    def h264_secure_path(self):
        return "/" + self.filename[len(settings.H264_SECURE_STREAM_DIRECTORY):]

    def h264_secure_stream_url(self):
        """ the URL handed to mediathread for h264 streams """
        filename = self.filename
        if filename.startswith(settings.H264_SECURE_STREAM_DIRECTORY):
            filename = filename[len(settings.H264_SECURE_STREAM_DIRECTORY):]
        return settings.H264_SECURE_STREAM_BASE + "SECURE/" + filename

    def is_h264_public_streamable(self):
        return self.filename.startswith(settings.H264_PUBLIC_STREAM_DIRECTORY)

    def h264_public_stream_url(self):
        filename = self.filename
        if filename.startswith(settings.H264_PUBLIC_STREAM_DIRECTORY):
            filename = filename[len(settings.H264_PUBLIC_STREAM_DIRECTORY):]
        return settings.H264_PUBLIC_STREAM_BASE + filename

    def h264_public_path(self):
        return "/" + self.filename[len(settings.H264_PUBLIC_STREAM_DIRECTORY):]

    def is_cuit(self):
        return self.location_type == "cuit"

    def audio_format(self):
        return self.get_metadata("ID_AUDIO_FORMAT")

    def video_format(self):
        return self.get_metadata("ID_VIDEO_FORMAT")

    def poster_options(self, cuit_poster_base):
        options = [
            dict(value=cuit_poster_base + "_320x240.jpg",
                 label="CCNMTL 320x240"),
            dict(value=cuit_poster_base + "_480x360.jpg",
                 label="CCNMTL 480x360"),
            dict(value=cuit_poster_base + "_480x272.jpg",
                 label="CCNMTL 480x272"),
        ]

        if self.video.has_poster():
            options.insert(
                0,
                dict(value=(self.video.poster_url()),
                     label="Wardenclyffe generated")
            )
        return options

    def protection_options(self):
        if self.is_h264_secure_streamable():
            return [
                dict(value="mp4_secure_stream",
                     label="mp4 secure stream"),
            ]
        return PROTECTION_OPTIONS

    def authtype_options(self):
        if self.is_h264_secure_streamable():
            return [
                dict(value="wind",
                     label="WIND [authtype=wind]"),
                dict(value="wikispaces",
                     label=("Wikispaces (Pamacea auth-domain) "
                            "[authtype=wikispaces]")),
                dict(value="auth",
                     label=("Standard UNI (Pamacea domain incompatible"
                            " with wikispaces)"
                            " [authtype=auth]")),
            ]
        return AUTHTYPE_OPTIONS


class Metadata(models.Model):
    """ metadata that we've extracted. more about
    encoding/file format kinds of stuff than dublin-core"""
    file = models.ForeignKey(File)
    field = models.CharField(max_length=256, default="")
    value = models.TextField(default="", blank=True, null=True)

    class Meta:
        ordering = ('field', )


class Operation(TimeStampedModel):
    video = models.ForeignKey(Video)
    action = models.CharField(max_length=256, default="")
    owner = models.ForeignKey(User)
    status = models.CharField(max_length=256, default="in progress")
    params = models.TextField(default="")
    uuid = UUIDField()

    def as_dict(self):
        d = dict(action=self.action,
                 status=self.status,
                 params=self.params,
                 uuid=self.uuid,
                 id=self.id,
                 video_id=self.video.id,
                 video_url=self.video.get_absolute_url(),
                 video_title=self.video.title,
                 video_creator=self.video.creator,
                 collection_id=self.video.collection.id,
                 collection_title=self.video.collection.title,
                 collection_url=self.video.collection.get_absolute_url(),
                 modified=str(self.modified)[:19],
                 )
        return d

    def get_absolute_url(self):
        return "/operation/%s/" % self.uuid

    def formatted_params(self):
        try:
            return dumps(loads(self.params), indent=4)
        except:
            return self.params

    def get_task(self):
        import wardenclyffe.main.tasks
        import wardenclyffe.youtube.tasks
        import wardenclyffe.mediathread.tasks
        import wardenclyffe.cuit.tasks

        mapper = {
            'extract metadata': wardenclyffe.main.tasks.extract_metadata,
            'save file to S3': wardenclyffe.main.tasks.save_file_to_s3,
            'make images': wardenclyffe.main.tasks.make_images,
            'import from cuit': wardenclyffe.cuit.tasks.import_from_cuit,
            'submit to podcast producer':
            wardenclyffe.main.tasks.submit_to_pcp,
            'upload to youtube': wardenclyffe.youtube.tasks.upload_to_youtube,
            'submit to mediathread':
            wardenclyffe.mediathread.tasks.submit_to_mediathread,
            'pull from s3 and submit to pcp':
            wardenclyffe.main.tasks.pull_from_s3_and_submit_to_pcp,
            'pull from cuit and submit to pcp':
            wardenclyffe.main.tasks.pull_from_cuit_and_submit_to_pcp,
        }
        return mapper[self.action]

    def process(self, args):
        statsd.incr("main.process_task")
        self.status = "in progress"
        self.save()
        f = self.get_task()
        error_message = ""
        try:
            (success, message) = f(self, args)
            self.status = success
            if self.status == "failed" or message != "":
                self.log(info=message)
                error_message = message
        except Exception, e:
            self.status = "failed"
            self.log(info=str(e))
            error_message = str(e)

        self.save()
        if self.status == "failed":
            statsd.incr("main.process_task.failure")
            send_failed_operation_mail(self, error_message)

    def post_process(self):
        """ the operation has completed, now we have a chance
        to do additional work. Generally, this is for
        a submit to PCP operation and we want to create
        a derived File to track where the result ended up"""
        if self.action == "submit to podcast producer":
            # see if the workflow has a post_process hook
            p = loads(self.params)
            if 'pcp_workflow' not in p:
                # what? how could that happen?
                return
            workflow = p['pcp_workflow']
            if not hasattr(settings, 'WORKFLOW_POSTPROCESS_HOOKS'):
                # no hooks configured
                return
            if workflow not in settings.WORKFLOW_POSTPROCESS_HOOKS:
                # no hooks registered for this workflow
                return
            for hook in settings.WORKFLOW_POSTPROCESS_HOOKS[workflow]:
                if not hasattr(self, hook):
                    continue
                f = getattr(self, hook)
                f()

    def log(self, info=""):
        OperationLog.objects.create(operation=self,
                                    info=info)


class OperationFile(models.Model):
    operation = models.ForeignKey(Operation)
    file = models.ForeignKey(File)


class OperationLog(TimeStampedModel):
    operation = models.ForeignKey(Operation)
    info = models.TextField(default="")


class Image(TimeStampedModel):
    video = models.ForeignKey(Video)
    image = ImageWithThumbnailsField(upload_to="images",
                                     thumbnail={'size': (100, 100)})

    class Meta:
        order_with_respect_to = "video"


class Poster(models.Model):
    video = models.ForeignKey(Video)
    image = models.ForeignKey(Image)

    def url(self):
        return (settings.POSTER_BASE_URL
                + str(self.image.image))


class DummyPoster:
    dummy = True

    def url(self):
        return settings.DEFAULT_POSTER_URL


class Server(models.Model):
    name = models.CharField(max_length=256)
    hostname = models.CharField(max_length=256)
    credentials = models.CharField(max_length=256)
    description = models.TextField(default="", blank=True)
    base_dir = models.CharField(max_length=256, default="/")
    base_url = models.CharField(max_length=256, default="")
    server_type = models.CharField(max_length=256, default="sftp")

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "/server/%d/" % self.id


class ServerFile(TimeStampedModel):
    server = models.ForeignKey(Server)
    file = models.ForeignKey(File)
