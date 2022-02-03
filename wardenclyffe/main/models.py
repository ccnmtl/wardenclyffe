from __future__ import unicode_literals

import base64
import hmac
from json import dumps, loads
import os.path
import hashlib
import time

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.deletion import SET
from django.db.models.query_utils import Q
from django.utils.encoding import python_2_unicode_compatible, smart_bytes
from django_extensions.db.models import TimeStampedModel
from django_statsd.clients import statsd
from surelink.helpers import SureLink, AUTHTYPE_OPTIONS, PROTECTION_OPTIONS
from taggit.managers import TaggableManager
import uuid

from wardenclyffe.util.mail import send_failed_operation_mail


@python_2_unicode_compatible
class Collection(TimeStampedModel):
    title = models.CharField(max_length=256)
    creator = models.CharField(max_length=256, default="", blank=True)
    contributor = models.CharField(max_length=256, default="", blank=True)
    language = models.CharField(max_length=256, default="", blank=True)
    description = models.TextField(default="", blank=True, null=True)
    subject = models.TextField(default="", blank=True, null=True)
    license = models.CharField(max_length=256, default="", blank=True)
    active = models.BooleanField(default=True)
    audio = models.BooleanField(default=False)
    public = models.BooleanField(default=False)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    tags = TaggableManager(blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return "/collection/%d/" % self.id

    def add_video_form(self):
        from wardenclyffe.main.forms import AddVideoForm
        return AddVideoForm()

    def is_public(self):
        """ is this a Public collection? """
        return self.public


class VideoManager(models.Manager):

    def video_from_form(self, form, username, collection_id):
        v = form.save(commit=False)
        vuuid = uuid.uuid4()
        v.uuid = vuuid
        v.creator = username
        if collection_id:
            v.collection_id = collection_id
        v.save()
        form.save_m2m()
        return v

    def simple_create(self, collection, title, username):
        vuuid = uuid.uuid4()
        return Video.objects.create(
            collection=collection,
            title=title[:256],
            creator=username,
            uuid=vuuid,
        )

    def search(self, q):
        qs = Video.objects.all()

        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(creator__icontains=q) |
                Q(description__icontains=q) |
                Q(subject__icontains=q) |
                Q(license__icontains=q) |
                Q(file__filename__icontains=q)
            ).distinct()
        return qs


def unclassified():
    return Collection.objects.get_or_create(title='Unclassified')[0]


@python_2_unicode_compatible
class Video(TimeStampedModel):
    collection = models.ForeignKey(Collection, on_delete=SET(unclassified))
    title = models.CharField(max_length=256)
    creator = models.CharField(max_length=256, default="", blank=True)
    description = models.TextField(default="", blank=True, null=True)
    subject = models.TextField(default="", blank=True, null=True)
    license = models.CharField(max_length=256, default="", blank=True)
    language = models.CharField(max_length=256, default="", blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    objects = VideoManager()
    tags = TaggableManager(blank=True)

    def __str__(self):
        return self.title

    def s3_file(self):
        labels = ["uploaded source file (S3)", "uploaded source audio (S3)"]
        r = self.file_set.filter(
            location_type='s3', label__in=labels)
        return r.first()

    def has_s3_source(self):
        return self.s3_file() is not None

    def s3_transcoded(self):
        r = self.file_set.filter(
            location_type='s3', label="transcoded 480p file (S3)")
        return r.first()

    def has_s3_transcoded(self):
        return self.s3_transcoded() is not None

    def s3_key(self):
        t = self.s3_file()
        if t:
            return t.cap
        else:
            return None

    def has_panopto_source(self):
        return self.file_set.filter(location_type='panopto').exists()

    def panopto_file(self):
        return self.file_set.filter(
            location_type='panopto').order_by('-created').first()

    def youtube_file(self):
        return self.file_set.filter(location_type='youtube').first()

    def source_file(self):
        return self.file_set.filter(label='source file').first()

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
        return "/video/%d/" % self.id

    def get_oembed_url(self):
        return "/video/%d/oembed/" % self.id

    def add_file_form(self, data=None):
        from wardenclyffe.main.forms import AddFileForm
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
        for f in self.file_set.filter(location_type="cuit"):
            return f.cuit_public_url()
        return ""

    def mediathread_url(self):
        for f in self.file_set.filter(location_type="cuit"):
            return f.mediathread_public_url()

        for f in self.file_set.filter(location_type="panopto"):
            return f.filename

        return ""

    def h264_secure_stream_file(self):
        for f in self.file_set.filter(location_type="cuit"):
            if f.is_h264_secure_streamable():
                return f
        return None

    def h264_secure_stream_url(self):
        for f in self.file_set.filter(location_type="cuit"):
            if f.is_h264_secure_streamable():
                return f.h264_secure_stream_url()
        return ""

    def h264_public_stream_file(self):
        for f in self.file_set.filter(location_type="cuit"):
            if f.is_h264_public_streamable():
                return f
        return None

    def h264_public_stream_url(self):
        for f in self.file_set.filter(location_type="cuit"):
            if f.is_h264_public_streamable():
                return f.h264_public_stream_url()
        return ""

    def has_poster(self):
        return self.poster_set.count()

    def poster_url(self):
        return self.poster().url()

    def poster(self):
        if self.poster_set.count() > 0:
            return self.poster_set.first()
        else:
            return DummyPoster()

    def cuit_poster_url(self):
        try:
            return File.objects.filter(video=self,
                                       location_type='cuitthumb')[0].url
        except IndexError:
            return None

    def is_mediathread_submit(self):
        return self.file_set.filter(
            location_type="mediathreadsubmit").count() > 0

    def has_mediathread_asset(self):
        return self.file_set.filter(
            location_type="mediathread").count() > 0

    def mediathread_asset_url(self):
        return self.file_set.filter(
            location_type="mediathread").first().url

    def remove_mediathread_asset(self):
        return self.file_set.filter(location_type="mediathread").delete()

    def mediathread_submit(self):
        for f in self.file_set.filter(location_type="mediathreadsubmit"):
            return (f.get_metadata("set_course"),
                    f.get_metadata("username"),
                    f.get_metadata("audio"),
                    )
        return (None, None, None)

    def clear_mediathread_submit(self):
        self.file_set.filter(location_type="mediathreadsubmit").delete()

    def handle_mediathread_submit(self):
        if self.is_mediathread_submit():
            statsd.incr('main.upload.mediathread')
            (set_course, username,
             audio) = self.mediathread_submit()
            if set_course is not None:
                user = User.objects.get(username=username)
                params = dict()
                params['set_course'] = set_course
                params['audio'] = audio
                o = self.make_op(
                    user, params, action="submit to mediathread")
                self.clear_mediathread_submit()
                return [o]
        return []

    def handle_mediathread_update(self):
        if not self.has_mediathread_update():
            return []
        o = self.make_op(
            User.objects.get(username=self.creator),
            dict(),
            action="update mediathread")
        self.clear_mediathread_update()
        return [o]

    def handle_mediathread_delete(self):
        if (self.has_mediathread_asset() and
            not self.has_panopto_source() and
                not self.has_cuit_source()):
            self.remove_mediathread_asset()
        return []

    def create_mediathread_update(self):
        """ add a temporary File that indicates that an update to Meth
        is expected """
        return File.objects.create(
            video=self,
            label="mediathread update",
            filename="",
            location_type='mediathreadupdate'
        )

    def has_mediathread_update(self):
        return self.file_set.filter(
            location_type="mediathreadupdate").count() > 0

    def clear_mediathread_update(self):
        self.file_set.filter(location_type="mediathreadupdate").delete()

    def has_cuit_source(self):
        return self.file_set.filter(location_type="cuit").exists()

    def cuit_file(self):
        return self.file_set.filter(location_type="cuit").first()

    def cuit_file_extension(self):
        try:
            f = self.file_set.filter(location_type="cuit").first()
            return os.path.splitext(f.filename)[1]
        except AttributeError:
            return None

    def has_flv(self):
        return self.file_set.filter(
            location_type="cuit", filename__endswith='.flv').count() > 0

    def flv_filename(self):
        # only valid if video has an flv attached.
        # expect an exception otherwise
        return self.file_set.filter(
            location_type="cuit", filename__endswith='.flv').first().filename

    def has_mov(self):
        return self.file_set.filter(
            location_type="cuit", filename__endswith='.mov').count() > 0

    def mov_filename(self):
        # only valid if video has an mov attached.
        # expect an exception otherwise
        return self.file_set.filter(
            location_type="cuit", filename__endswith='.mov').first().filename

    def has_mp4(self):
        return self.file_set.filter(
            location_type="cuit", filename__endswith='.mp4').count() > 0

    def mp4_filename(self):
        # only valid if video has an mp4 attached.
        # expect an exception otherwise
        return self.file_set.filter(
            location_type="cuit", filename__endswith='.mp4').first().filename

    def flv_convertable(self):
        # there's an associated flv, but no mp4 yet
        return self.has_flv() and not self.has_mp4()

    def mov_convertable(self):
        # there's an associated flv, but no mp4 yet
        return self.has_mov() and not self.has_mp4()

    def is_audio_file(self):
        """ is this one of the weird mp3s that are
        uploaded to be converted to mp4s so clipping works?"""
        try:
            return self.file_set.filter(
                location_type='mediathreadsubmit')[0].get_metadata('audio')
        except IndexError:
            return False

    def streamlogs(self):
        StreamLog = apps.get_model('streamlogs', 'StreamLog')

        if self.has_flv():
            filename = self.flv_filename()
            # convert to the partial filename that streamlogs have
            base = settings.CUNIX_BROADCAST_DIRECTORY
            # strip off up to the 'broadcast/'
            filename = filename.replace(base, "broadcast/")
            return StreamLog.objects.filter(filename=filename)
        elif self.has_mp4():
            f = self.file_set.filter(
                location_type="cuit", filename__endswith='.mp4').first()

            filename = f.filename
            if f.is_h264_secure_streamable():
                filename = f.h264_secure_path()
            return StreamLog.objects.filter(filename__contains=filename)

        return StreamLog.objects.none()

    def make_mediathread_submit_file(self, filename, user, set_course,
                                     redirect_to, audio=False):
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

    def make_op(self, user, params, **oparams):
        oparams['video'] = self
        oparams['uuid'] = uuid.uuid4()
        oparams['params'] = dumps(params)
        oparams['owner'] = user
        oparams['status'] = "enqueued"
        return Operation.objects.create(**oparams)

    def make_extract_metadata_operation(self, tmpfilename, source_file, user):
        params = dict(tmpfilename=tmpfilename,
                      source_file_id=source_file.id)
        return self.make_op(user, params, action="extract metadata")

    def make_pull_from_s3_and_extract_metadata_operation(self, key, user):
        return self.make_op(user, dict(key=key),
                            action="pull from s3 and extract metadata")

    def make_save_file_to_s3_operation(self, tmpfilename, user, audio=None):
        params = dict(tmpfilename=tmpfilename, filename=tmpfilename,
                      audio=audio)
        return self.make_op(user, params, action="save file to S3")

    def make_delete_from_s3_operation(self, file_id, user):
        params = dict(file_id=file_id)
        return self.make_op(user, params, action="delete from s3")

    def make_copy_from_s3_to_cunix_operation(self, file_id, user):
        params = dict(file_id=file_id)
        return self.make_op(user, params, action="copy from s3 to cunix")

    def make_delete_from_cunix_operation(self, file_id, user):
        params = dict(file_id=file_id)
        return self.make_op(user, params, action="delete from cunix")

    def make_pull_thumbs_from_s3_operation(self, pattern, user):
        params = dict(pattern=pattern)
        return self.make_op(user, params, action="pull thumbs from s3")

    def make_audio_encode_operation(self, file_id, user):
        """ pull the file down from S3
        run it through the audio encode job
        then upload it to cunix. """
        params = dict(file_id=file_id)
        return self.make_op(user, params, action="audio encode")

    def make_local_audio_encode_operation(self, s3_key, user):
        """ run it through the audio encode job
        then upload it to s3. """
        params = dict(s3_key=s3_key)
        return self.make_op(user, params, action="local audio encode")

    def make_create_elastic_transcoder_job_operation(
            self, key, user):
        params = dict(key=key)
        return self.make_op(user, params,
                            action="create elastic transcoder job")

    def make_upload_to_youtube_operation(self, tmpfilename, user):
        params = dict(tmpfilename=tmpfilename)
        return self.make_op(user, params, action="upload to youtube")

    def make_pull_from_s3_and_upload_to_youtube_operation(self, video_id,
                                                          user):
        params = dict(video_id=video_id)
        return self.make_op(user, params,
                            action="pull from s3 and upload to youtube")

    def make_pull_from_cunix_and_upload_to_youtube_operation(self, video_id,
                                                             user):
        params = dict(video_id=video_id)
        return self.make_op(user, params,
                            action="pull from cunix and upload to youtube")

    def make_pull_from_s3_and_upload_to_panopto_operation(
            self, video_id, folder, user):
        params = dict(video_id=video_id, folder=folder)
        return self.make_op(user, params,
                            action="pull from s3 and upload to panopto")

    def make_pull_from_cunix_and_upload_to_panopto_operation(
            self, video_id, folder, user):
        params = dict(video_id=video_id, folder=folder)
        return self.make_op(user, params,
                            action="pull from cunix and upload to panopto")

    def make_verify_upload_to_panopto_operation(
            self, user, video_id, upload_id):
        params = dict(video_id=video_id, upload_id=upload_id)
        return self.make_op(user, params,
                            action="verify upload to panopto")

    def make_pull_thumb_from_panopto_operation(
            self, user, video_id, panopto_id):
        params = dict(video_id=video_id, panopto_id=panopto_id)
        return self.make_op(user, params, action="pull thumb from panopto")

    def make_flv_to_mp4_operation(self, user, suffix, filename):
        params = dict(suffix=suffix, filename=filename)
        return self.make_op(user, params, action="copy from cunix to s3")

    def make_mov_to_mp4_operation(self, user, suffix, filename):
        params = dict(suffix=suffix, filename=filename)
        return self.make_op(user, params, action="copy from cunix to s3")

    def make_source_file(self, filename):
        return File.objects.create(video=self,
                                   label="source file",
                                   filename=filename,
                                   location_type='none')

    def make_uploaded_source_file(self, key, audio=False):
        return File.objects.create_uploaded_source_file(self, key, audio)

    def upto_hundred_images(self):
        """ return the first 100 frames for the video

        some really long videos end up with thousands of frames
        which takes sorl a long time to thumbnail and makes
        the page really slow. There's really no good reason
        to show *all* those images. The first hundred or so
        ought to be enough to select a poster from """
        return self.image_set.all()[:100]

    def initial_operations(self, key, user, audio, folder=None):
        if folder:
            return [
                self.make_pull_from_s3_and_upload_to_panopto_operation(
                    self.id, folder, user)
            ]
        elif audio:
            return [self.make_local_audio_encode_operation(
                key, user=user)]
        else:
            return [
                self.make_pull_from_s3_and_extract_metadata_operation(
                    key=key, user=user),
                self.make_create_elastic_transcoder_job_operation(
                    key=key, user=user)]


class WrongFileType(Exception):
    pass


class FileType(object):
    def __init__(self, file):
        self.file = file

    def is_s3(self):
        return False

    def is_audio(self):
        return False

    def s3_download_url(self):
        return None


class VideoReference(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    url = models.URLField()
    name = models.CharField(max_length=1024, blank=True, null=True)


class CUITFile(FileType):
    pass


class S3File(FileType):
    def is_s3(self):
        return True

    def s3_download_url(self):
        bucket = settings.AWS_S3_UPLOAD_BUCKET
        if 'transcode' in self.file.label:
            bucket = settings.AWS_S3_OUTPUT_BUCKET
        filename = "/" + bucket + "/" + self.file.cap
        expiry = str(int(time.time()) + 3600)
        h = hmac.new(
            smart_bytes(settings.AWS_SECRET_KEY),
            smart_bytes("".join(["GET\n\n\n", expiry, "\n", filename])),
            hashlib.sha1)
        signature = quote_plus(base64.encodebytes(h.digest()).strip())
        return "".join([
            "https://s3.amazonaws.com",
            filename,
            "?AWSAccessKeyId=",
            settings.AWS_ACCESS_KEY,
            "&Expires=",
            expiry,
            "&Signature=",
            signature
        ])

    def is_audio(self):
        return self.file.cap.lower().endswith("mp3")


class FileManager(models.Manager):
    def create_uploaded_source_file(self, v, key, audio=False):
        label = "uploaded source file (S3)"
        if audio or v.collection.audio:
            label = "uploaded source audio (S3)"

        f = File.objects.create(video=v, url="", cap=key, location_type="s3",
                                filename=key, label=label)
        return f


class File(TimeStampedModel):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    label = models.CharField(max_length=256, blank=True, null=True, default="")
    url = models.URLField(default="", blank=True, null=True, max_length=2000)
    cap = models.CharField(max_length=256, default="", blank=True, null=True)
    filename = models.CharField(max_length=256, blank=True, null=True,
                                default="")
    st_size = models.IntegerField(default=0)
    location_type = models.CharField(max_length=256, default="s3",
                                     choices=(('pcp', 'pcp'),
                                              ('cuit', 'cuit'),
                                              ('youtube', 'youtube'),
                                              ('s3', 's3'),
                                              ('panopto', 'panopto'),
                                              ('none', 'none')))
    objects = FileManager()

    def __str__(self):
        return self.filename

    def filetype(self):
        tmap = dict(
            cuit=CUITFile,
            s3=S3File,
        )
        return tmap.get(self.location_type, FileType)(self)

    def is_s3(self):
        return self.filetype().is_s3()

    def is_audio(self):
        return self.filetype().is_audio()

    def s3_download_url(self):
        return self.filetype().s3_download_url()

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
            except IndexError:
                return None

    def guess_height(self):
        r = self.metadata_set.filter(field="ID_VIDEO_HEIGHT")
        if r.count() > 0:
            return int(r[0].value)
        else:
            try:
                return self.video.get_dimensions()[1]
            except IndexError:
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

    def h264_secure_internal_url(self):
        url = self.h264_secure_stream_url()
        url_slashed = url.split("?")[0].split("/")
        filename = "/%s" % url_slashed[5]
        t_hex = "%08x" % int(time.time())

        enc = (settings.SURELINK_ACCESS + filename + t_hex).encode('utf-8')
        m = hashlib.md5(enc).hexdigest()  # nosec
        return "%s%s/%s/%s" % (
            settings.H264_SECURE_STREAM_BASE, m, t_hex, filename)

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

    def file_base(self):
        return self.filename.split('/')[-1]


class Metadata(models.Model):
    """ metadata that we've extracted. more about
    encoding/file format kinds of stuff than dublin-core"""
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    field = models.CharField(max_length=256, default="")
    value = models.TextField(default="", blank=True, null=True)

    class Meta:
        ordering = ('field', )


class Operation(TimeStampedModel):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    action = models.CharField(max_length=256, default="")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=256, default="in progress")
    params = models.TextField(default="")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    def __json__(self):
        return self.as_dict()

    def as_dict(self):
        d = dict(action=self.action,
                 status=self.status,
                 params=self.params,
                 uuid=str(self.uuid),
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
        except ValueError:
            return self.params

    def operation_type(self):
        """ factory for the correct OperationType class"""
        return OPERATION_TYPE_MAPPER[self.action](self)

    def get_task(self):
        return self.operation_type().get_task()

    def process(self):
        statsd.incr("main.process_task")
        self.status = "in progress"
        self.save()
        f = self.get_task()
        try:
            (success, message) = f(self)
            self.status = success
            self.save()
            if message != "":
                self.log(message)
            if self.status == "failed":
                self.fail(message)
            else:
                self.post_process()
        except Exception as e:
            self.log(info=str(e))
            # re-raise so Celery's retry logic can deal with it
            raise

    def fail(self, error_message):
        self.status = "failed"
        self.save()
        statsd.incr("main.process_task.failure")
        send_failed_operation_mail(self, error_message)

    def post_process(self):
        import wardenclyffe.main.tasks as tasks
        operations = self.operation_type().post_process()
        for o in operations:
            tasks.process_operation.delay(o.id)

    def log(self, info=""):
        OperationLog.objects.create(operation=self,
                                    info=info)


class OperationType(object):
    """ abstract base class for operation types """
    def __init__(self, operation):
        self.operation = operation

    def get_task(self):
        """ must override this """
        raise NotImplementedError

    def post_process(self):
        """ steps to run after operation has completed.

        optional. Expectation is that it will do what it
        needs to do and possibly return a list of
        operations for further processing """
        return []


class ExtractMetadataOperation(OperationType):
    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.extract_metadata


class PullFromS3AndExtractMetadataOperation(OperationType):
    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.pull_from_s3_and_extract_metadata


class SaveFileToS3Operation(OperationType):
    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.save_file_to_s3

    def post_process(self):
        operation = self.operation
        params = loads(operation.params)
        if 's3_key' not in params:
            return []
        key = params['s3_key']

        if params['audio']:
            return [operation.video.make_local_audio_encode_operation(
                params['s3_key'], user=operation.owner)]

        return [
            operation.video.make_pull_from_s3_and_extract_metadata_operation(
                key=key, user=operation.owner),
            operation.video.make_create_elastic_transcoder_job_operation(
                key=key, user=operation.owner)]


class UploadToYoutubeOperation(OperationType):
    def get_task(self):
        import wardenclyffe.youtube.tasks
        return wardenclyffe.youtube.tasks.upload_to_youtube


class SubmitToMediathreadOperation(OperationType):
    def get_task(self):
        import wardenclyffe.mediathread.tasks
        return wardenclyffe.mediathread.tasks.submit_to_mediathread


class UpdateMediathreadOperation(OperationType):
    def get_task(self):
        import wardenclyffe.mediathread.tasks
        return wardenclyffe.mediathread.tasks.update_mediathread


class PullFromS3AndUploadToYoutubeOperation(OperationType):
    def get_task(self):
        import wardenclyffe.youtube.tasks
        return wardenclyffe.youtube.tasks.pull_from_s3_and_upload_to_youtube


class PullFromCunixAndUploadToYoutubeOperation(OperationType):
    def get_task(self):
        import wardenclyffe.youtube.tasks
        return \
            wardenclyffe.youtube.tasks.pull_from_cunix_and_upload_to_youtube


class PullFromS3AndUploadToPanoptoOperation(OperationType):
    def get_task(self):
        import wardenclyffe.panopto.tasks
        return wardenclyffe.panopto.tasks.pull_from_s3_and_upload_to_panopto

    def post_process(self):
        operation = self.operation
        params = loads(operation.params)
        if 'upload_id' not in params:
            return []

        return [operation.video.make_verify_upload_to_panopto_operation(
            operation.owner, operation.video.id, params['upload_id'])]


class PullFromCunixAndUploadToPanoptoOperation(OperationType):
    def get_task(self):
        import wardenclyffe.panopto.tasks
        return \
            wardenclyffe.panopto.tasks.pull_from_cunix_and_upload_to_panopto

    def post_process(self):
        operation = self.operation
        params = loads(operation.params)
        if 'upload_id' not in params:
            return []

        return [operation.video.make_verify_upload_to_panopto_operation(
            operation.owner, operation.video.id, params['upload_id'])]


class VerifyUploadToPanoptoOperation(OperationType):

    def get_task(self):
        import wardenclyffe.panopto.tasks
        return wardenclyffe.panopto.tasks.verify_upload_to_panopto

    def post_process(self):
        operation = self.operation
        params = loads(operation.params)

        return [operation.video.make_pull_thumb_from_panopto_operation(
            operation.owner, operation.video.id, params['panopto_id'])]


class PullThumbFromPanoptoOperation(OperationType):

    def get_task(self):
        import wardenclyffe.panopto.tasks
        return wardenclyffe.panopto.tasks.pull_thumb_from_panopto

    def post_process(self):
        ops = self.operation.video.handle_mediathread_submit()
        ops.extend(self.operation.video.handle_mediathread_update())
        return ops


class CreateElasticTranscoderJobOperation(OperationType):
    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.create_elastic_transcoder_job


class CopyFromS3ToCunixOperation(OperationType):
    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.copy_from_s3_to_cunix

    def post_process(self):
        ops = self.operation.video.handle_mediathread_submit()
        ops.extend(self.operation.video.handle_mediathread_update())
        return ops


class DeleteFromCunixOperation(OperationType):
    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.delete_from_cunix

    def post_process(self):
        ops = self.operation.video.handle_mediathread_delete()
        return ops


class DeleteFromS3Operation(OperationType):

    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.delete_from_s3


class CopyFromCunixToS3Operation(OperationType):
    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.copy_from_cunix_to_s3

    def post_process(self):
        o = self.operation
        params = loads(o.params)
        if 's3_key' not in params:
            return []
        key = params['s3_key']
        ops = [
            o.video.make_create_elastic_transcoder_job_operation(
                key=key, user=o.owner)]
        if o.video.source_file() is None:
            # no source file implies that the metadata has not been extracted
            o.video.make_source_file(key)
            ops.extend([
                o.video.make_pull_from_s3_and_extract_metadata_operation(
                    key=key,
                    user=o.owner,
                )])
        return ops


class AudioEncodeOperation(OperationType):
    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.audio_encode


class LocalAudioEncodeOperation(OperationType):
    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.local_audio_encode

    def post_process(self):
        operation = self.operation
        params = loads(operation.params)
        if 'mp4_tmpfilename' not in params:
            return []
        tmpfilename = params['mp4_tmpfilename']

        # now we can send it off on the AWS pipeline
        return [operation.video.make_save_file_to_s3_operation(
            tmpfilename, operation.owner)]


class PullThumbsFromS3Operation(OperationType):
    def get_task(self):
        import wardenclyffe.main.tasks
        return wardenclyffe.main.tasks.pull_thumbs_from_s3


# map actions to OperationTypes
OPERATION_TYPE_MAPPER = {
    'extract metadata': ExtractMetadataOperation,
    'pull from s3 and extract metadata': PullFromS3AndExtractMetadataOperation,
    'save file to S3': SaveFileToS3Operation,
    'delete from s3': DeleteFromS3Operation,
    'upload to youtube': UploadToYoutubeOperation,
    'submit to mediathread': SubmitToMediathreadOperation,
    'update mediathread': UpdateMediathreadOperation,
    'pull from s3 and upload to youtube':
    PullFromS3AndUploadToYoutubeOperation,
    'pull from cunix and upload to youtube':
    PullFromCunixAndUploadToYoutubeOperation,
    'pull from s3 and upload to panopto':
    PullFromS3AndUploadToPanoptoOperation,
    'pull from cunix and upload to panopto':
    PullFromCunixAndUploadToPanoptoOperation,
    'verify upload to panopto': VerifyUploadToPanoptoOperation,
    'pull thumb from panopto': PullThumbFromPanoptoOperation,
    'create elastic transcoder job': CreateElasticTranscoderJobOperation,
    'copy from s3 to cunix': CopyFromS3ToCunixOperation,
    'delete from cunix': DeleteFromCunixOperation,
    'copy from cunix to s3': CopyFromCunixToS3Operation,
    'audio encode': AudioEncodeOperation,
    'local audio encode': LocalAudioEncodeOperation,
    'pull thumbs from s3': PullThumbsFromS3Operation
}


class OperationFile(models.Model):
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE)


class OperationLog(TimeStampedModel):
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE)
    info = models.TextField(default="")


class Image(TimeStampedModel):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    image = models.CharField(max_length=1024)

    class Meta:
        order_with_respect_to = "video"

    def src(self):
        if self.image.startswith('http'):
            return self.image
        else:
            return settings.IMAGES_URL_BASE + str(self.image)


class Poster(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)

    def url(self):
        return self.image.src()


class DummyPoster:
    dummy = True

    def url(self):
        return settings.DEFAULT_POSTER_URL


@python_2_unicode_compatible
class Server(models.Model):
    name = models.CharField(max_length=256)
    hostname = models.CharField(max_length=256)
    credentials = models.CharField(max_length=256)
    description = models.TextField(default="", blank=True)
    base_dir = models.CharField(max_length=256, default="/")
    base_url = models.CharField(max_length=256, default="")
    server_type = models.CharField(max_length=256, default="sftp")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "/server/%d/" % self.id


class ServerFile(TimeStampedModel):
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE)
