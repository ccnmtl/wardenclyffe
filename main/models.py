from django.db import models
from django_extensions.db.fields import UUIDField
from django_extensions.db.models import TimeStampedModel
from django.contrib.auth.models import User
from sorl.thumbnail.fields import ImageWithThumbnailsField
from django import forms
from taggit.managers import TaggableManager
from south.modelsinspector import add_introspection_rules
from surelink.helpers import SureLink
from django.conf import settings
import os.path
from django.core.mail import send_mail
from django_statsd.clients import statsd

add_introspection_rules([],
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

    uuid = UUIDField()

    tags = TaggableManager(blank=True)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return "/collection/%d/" % self.id

    def add_video_form(self):
        class AddVideoForm(forms.ModelForm):
            class Meta:
                model = Video
                exclude = ('collection')
        return AddVideoForm()

    def edit_form(self, data=None):
        class EditForm(forms.ModelForm):
            class Meta:
                model = Collection
        if data:
            return EditForm(data, instance=self)
        else:
            return EditForm(instance=self)


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

    def tahoe_file(self):
        r = self.file_set.filter(location_type='tahoe')
        if r.count():
            return r[0]
        else:
            return None

    def source_file(self):
        r = self.file_set.filter(label='source file')
        if r.count():
            return r[0]
        else:
            return None

    def cap(self):
        t = self.tahoe_file()
        if t:
            return t.cap
        else:
            return None

    def tahoe_download_url(self):
        t = self.tahoe_file()
        if t:
            return t.tahoe_download_url()
        else:
            return ""

    def enclosure_url(self):
        return self.tahoe_download_url()

    def filename(self):
        r = self.file_set.filter().exclude(filename="").exclude(filename=None)
        if r.count():
            return r[0].filename
        else:
            return "none"

    def extension(self):
        """ guess at the extension of the video.
        prefer the source file, but fallback to the tahoe copy if we have one
        otherwise, we'll take *anything* with a filename """
        f = self.source_file()
        if f is not None:
            return os.path.splitext(f.filename)[1]
        f = self.tahoe_file()
        if f is not None:
            return os.path.splitext(f.filename)[1]
        r = self.file_set.filter().exclude(filename="").exclude(filename=None)
        if r.count():
            return os.path.splitext(r[0].filename)[1]
        return ""

    def get_absolute_url(self):
        return "/video/%d/" % self.id

    def get_oembed_url(self):
        return "/video/%d/oembed/" % self.id

    def add_file_form(self, data=None):
        class AddFileForm(forms.ModelForm):
            class Meta:
                model = File
                exclude = ('video')
        if data:
            return AddFileForm(data)
        else:
            return AddFileForm()

    def edit_form(self, data=None):
        class EditForm(forms.ModelForm):
            class Meta:
                model = Video
        if data:
            return EditForm(data, instance=self)
        else:
            return EditForm(instance=self)

    def get_dimensions(self):
        t = self.source_file()
        if t is None:
            return (0, 0)
        return (t.get_width(), t.get_height())

    def vital_thumb_url(self):
        r = self.file_set.filter(location_type="vitalthumb")
        if r.count() > 0:
            f = r[0]
            return f.url
        return ""

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

    def poster_url(self):
        if self.image_set.all().count() > 0:
            # TODO: get absolute url of first image
            # and use that
            # return self.image_set.all()[0].image
            pass
        return "http://ccnmtl.columbia.edu/broadcast/posters/vidthumb_480x360.jpg"

    def cuit_poster_url(self):
        try:
            return File.objects.filter(video=self,
                                       location_type='cuitthumb')[0].url
        except:
            return None

    def is_mediathread_submit(self):
        return self.file_set.filter(location_type="mediathreadsubmit").count() > 0

    def mediathread_submit(self):
        r = self.file_set.filter(location_type="mediathreadsubmit")
        if r.count() > 0:
            f = r[0]
            return (f.get_metadata("set_course"), f.get_metadata("username"), )
        else:
            return (None, None)

    def clear_mediathread_submit(self):
        self.file_set.filter(location_type="mediathreadsubmit").delete()

    def is_vital_submit(self):
        return self.file_set.filter(location_type="vitalsubmit").count() > 0

    def vital_submit(self):
        r = self.file_set.filter(location_type="vitalsubmit")
        if r.count() > 0:
            f = r[0]
            return (f.get_metadata("set_course"), f.get_metadata("username"),
                    f.get_metadata("notify_url"))
        else:
            return (None, None, None)

    def clear_vital_submit(self):
        self.file_set.filter(location_type="vitalsubmit").delete()

    def poster(self):
        class DummyPoster:
            dummy = True
        r = Poster.objects.filter(video=self)
        if r.count() > 0:
            return r[0].image
        else:
            return DummyPoster()

    def cuit_file(self):
        try:
            return self.file_set.filter(location_type="cuit")[0]
        except:
            return None


class File(TimeStampedModel):
    video = models.ForeignKey(Video)
    label = models.CharField(max_length=256, blank=True, null=True, default="")
    url = models.URLField(default="", blank=True, null=True, max_length=2000)
    cap = models.CharField(max_length=256, default="", blank=True, null=True)
    filename = models.CharField(max_length=256, blank=True, null=True)
    location_type = models.CharField(max_length=256, default="tahoe",
                                     choices=(('tahoe', 'tahoe'),
                                              ('pcp', 'pcp'),
                                              ('cuit', 'cuit'),
                                              ('youtube', 'youtube'),
                                              ('none', 'none')))

    def tahoe_download_url(self):
        if self.location_type == "tahoe":
            return settings.TAHOE_DOWNLOAD_BASE + "file/" + self.cap\
                + "/@@named=" + self.filename
        else:
            return None

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
        try:
            return self.get_width()
        except:
            try:
                return self.video.get_dimensions()[0]
            except:
                return None

    def guess_height(self):
        try:
            return self.get_height()
        except:
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
        filename = self.filename[len("/www/data/ccnmtl/broadcast/"):]
        return "http://ccnmtl.columbia.edu/stream/flv/%s" % filename

    def mediathread_public_url(self):
        PROTECTION_KEY = settings.SURELINK_PROTECTION_KEY
        filename = self.filename
        if filename.startswith("/www/data/ccnmtl/broadcast/"):
            filename = filename[len("/www/data/ccnmtl/broadcast/"):]

        s = SureLink(filename=filename, width=0, height=0,
                     captions='', poster='', protection="public",
                     authtype='', player='v4', protection_key=PROTECTION_KEY)
        return s.public_url()

    def is_cuit(self):
        return self.location_type == "cuit"

    def audio_format(self):
        return self.get_metadata("ID_AUDIO_FORMAT")

    def video_format(self):
        return self.get_metadata("ID_VIDEO_FORMAT")


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
                 video_title=self.video.title,
                 video_creator=self.video.creator,
                 collection_id=self.video.collection.id,
                 collection_title=self.video.collection.title,
                 modified=str(self.modified)[:19],
                 )
        return d

    def get_absolute_url(self):
        return "/operation/%s/" % self.uuid

    def get_task(self):
        import wardenclyffe.main.tasks
        import wardenclyffe.youtube.tasks
        import wardenclyffe.mediathread.tasks

        mapper = {'extract metadata': wardenclyffe.main.tasks.extract_metadata,
                  'save file to tahoe': wardenclyffe.main.tasks.save_file_to_tahoe,
                  'make images': wardenclyffe.main.tasks.make_images,
                  'submit to podcast producer': wardenclyffe.main.tasks.submit_to_pcp,
                  'upload to youtube': wardenclyffe.youtube.tasks.upload_to_youtube,
                  'submit to mediathread': wardenclyffe.mediathread.tasks.submit_to_mediathread,
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
                log = OperationLog.objects.create(operation=self,
                                                  info=message)
                error_message = message
        except Exception, e:
            self.status = "failed"
            log = OperationLog.objects.create(operation=self,
                                              info=str(e))
            error_message = str(e)

        if self.status == "failed":
            statsd.incr("main.process_task.failure")
            for vuser in settings.ANNOY_EMAILS:
                send_mail('Video upload failed',
                          """An error has occurred while processing the video:
   "%s"

at:

   http://wardenclyffe.ccnmtl.columbia.edu%s

During the %s step. The error encountered was:

%s
""" % (self.video.title, self.video.get_absolute_url(), error_message),
                          'ccnmtl-vital@columbia.edu',
                          [vuser], fail_silently=False)
                statsd.incr("event.mail_sent")

        self.save()


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
