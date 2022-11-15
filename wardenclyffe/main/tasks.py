from datetime import datetime, timedelta
from json import loads, dumps
import os
import os.path
import random
import re
import subprocess  # nosec
import tempfile
import uuid

import boto3
from django.conf import settings
from django.utils.encoding import smart_text
from django_statsd.clients import statsd
import paramiko
from paramiko.sftp import SFTPError
import waffle

from celery.schedules import crontab
from wardenclyffe.celery import app
from wardenclyffe.main.models import File, Operation, OperationFile
from wardenclyffe.main.models import Image, Poster
from wardenclyffe.util.mail import send_slow_operations_email
from wardenclyffe.util.mail import send_slow_operations_to_videoteam_email


def exp_backoff(tries):
    """ exponential backoff with jitter

    back off 2^1, then 2^2, 2^3 (seconds), etc.

    add a 10% jitter to prevent thundering herd.

    """
    backoff = 2 ** tries
    jitter = random.uniform(0, backoff * .1)  # nosec
    return int(backoff + jitter)


@app.task(ignore_result=True, bind=True, max_retries=None)
def process_operation(self, operation_id, **kwargs):
    print("process_operation(%s)" % (operation_id))
    try:
        operation = Operation.objects.get(id=operation_id)
    except Operation.DoesNotExist as exc:
        handle_operation_does_not_exist(self, exc)
        return

    try:
        operation.process()
    except Exception as exc:
        handle_processing_error(self, operation, exc)


def handle_operation_does_not_exist(self, exc):
    if self.request.retries > settings.OPERATION_MAX_RETRIES:
        # max out at (default) 10 retry attempts
        print("operation not found after %d attempts (probably deleted)" %
              settings.OPERATION_MAX_RETRIES)
        statsd.incr("max_retries")
    else:
        statsd.incr("retry_operation")
        statsd.incr("retry_%02d" % self.request.retries)
        self.retry(exc=exc, countdown=exp_backoff(self.request.retries))


def handle_processing_error(self, operation, exc):
    print("Exception:")
    print(str(exc))
    if self.request.retries > settings.OPERATION_MAX_RETRIES:
        # max out at (default) 10 retry attempts
        operation.fail(str(exc))
        statsd.incr("max_retries")
    else:
        statsd.incr("retry_operation")
        statsd.incr("retry_%02d" % self.request.retries)
        self.retry(exc=exc, countdown=exp_backoff(self.request.retries))


def save_file_to_s3(operation):
    if not waffle.switch_is_active('enable_s3'):
        print("S3 uploads are disabled")
        return ("complete", "S3 uploads temporarily disabled")
    statsd.incr("save_file_to_s3")
    params = loads(operation.params)

    s3 = boto3.resource(
        's3', aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY)

    # make a YYYY/MM/DD directory to put the file in
    source_file = open(params['tmpfilename'], "rb")

    n = datetime.now()
    key = "%04d/%02d/%02d/%s" % (
        n.year, n.month, n.day,
        os.path.basename(params['tmpfilename']))
    s3.Object(settings.AWS_S3_UPLOAD_BUCKET, key).put(Body=source_file)
    source_file.close()
    label = "uploaded source file (S3)"
    if params['audio']:
        label = "uploaded source audio (S3)"
    f = File.objects.create(video=operation.video, url="", cap=key,
                            location_type="s3",
                            filename=params['filename'],
                            label=label)
    OperationFile.objects.create(operation=operation, file=f)
    # stash the s3 key back in params
    params['s3_key'] = key
    operation.params = dumps(params)
    operation.save()
    return ("complete", "")


def create_elastic_transcoder_job(operation):
    statsd.incr('create_transcoder_job')
    params = loads(operation.params)
    boto3.setup_default_session(region_name=settings.AWS_ET_REGION)
    et = boto3.client('elastictranscoder',
                      aws_access_key_id=settings.AWS_ACCESS_KEY,
                      aws_secret_access_key=settings.AWS_SECRET_KEY)

    n = datetime.now()
    output_base = "%04d/%02d/%02d/%s" % (
        n.year, n.month, n.day, str(uuid.uuid4()))

    input_object = {
        'Key': params['key'],
        'FrameRate': 'auto',
        'Resolution': 'auto',
        'Interlaced': 'auto'
    }
    output_objects = [
        {
            'Key': output_base + "_480.mp4",
            'Rotate': 'auto',
            'PresetId': settings.AWS_ET_MP4_PRESET,
        }
    ]
    if waffle.switch_is_active('enable_et_thumbs'):
        output_objects[0]['ThumbnailPattern'] = (
            "thumbs/" + output_base + "-{count}")
    if waffle.switch_is_active('enable_720p'):
        output_objects.append(
            {
                'Key': output_base + "_720.mp4",
                'Rotate': 'auto',
                'PresetId': settings.AWS_ET_720_PRESET,
            }
        )
    job = et.create_job(
        PipelineId=settings.AWS_ET_PIPELINE_ID,
        Input=input_object,
        Outputs=output_objects)
    job_id = str(job['Job']['Id'])
    print(job_id)
    f = File.objects.create(
        video=operation.video,
        cap=job_id,
        location_type="transcode",
        filename="",
        label="transcode")
    OperationFile.objects.create(operation=operation, file=f)
    return ("submitted", "")


MPLAYER = settings.MPLAYER_PATH
FFMPEG = settings.FFMPEG_PATH


def audio_encode_command(image, tmpfilename, outputfilename):
    image = os.path.normpath(image)
    return ("%s -loop 1 -i %s -i %s -c:v libx264 -c:a aac "
            "-strict experimental -b:a 192k -shortest %s" % (
                FFMPEG, image, tmpfilename, outputfilename))


def honey_badger(f, *args, **kwargs):
    """ basically apply() wrapped in an exception handler.
    honey badger don't care if there's an exception"""
    try:
        return f(*args, **kwargs)
    except:  # nosec # noqa
        pass


def pull_thumbs_from_s3(operation):
    """ given the thumbnail pattern that we get back from
    elastic transcoder, we look through the images
    bucket for images that match the pattern,
    and create Image objects to correspond to them """
    params = loads(operation.params)
    s3 = boto3.resource(
        's3', aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY)
    bucket = s3.Bucket(settings.IMAGES_BUCKET)

    # will be something like:
    #  "thumbs/2015/05/29/e573cfeb-e32c-45c0-8caa-326c394b04b9-{count}"
    # where {count} is zero-padded to 5 digits, starts at 1
    pattern = params['pattern']
    extension = ".jpg"

    cnt = 0
    for i in range(1, settings.MAX_FRAMES + 1):
        path = pattern.replace("{count}", "%05d" % i) + extension
        r = bucket.get_key(path)
        if r is None:
            break
        cnt += 1
        Image.objects.create(
            video=operation.video,
            image=path)

    if cnt > 0:
        set_poster(operation.video, cnt)
    return ("complete", "pulled %d thumbs" % cnt)


def set_poster(video, imgs):
    if imgs == 0:
        return
    if Poster.objects.filter(video=video).count() > 0:
        return
    # pick a random image out of the set and assign
    # it as the poster on the video
    r = random.randint(0, min(imgs, settings.MAX_FRAMES) - 1)  # nosec
    image = Image.objects.filter(video=video)[r]
    Poster.objects.create(video=video, image=image)


def midentify_path():
    pwd = os.path.dirname(__file__)
    script_dir = os.path.join(pwd, "../../scripts/")
    return os.path.join(script_dir, "midentify.sh")


def pull_from_s3_and_extract_metadata(operation):
    statsd.incr("pull_from_s3_and_extract_metadata")
    print("pulling from S3")
    params = loads(operation.params)
    video = operation.video
    suffix = video.extension()
    t = pull_from_s3(suffix, settings.AWS_S3_UPLOAD_BUCKET,
                     params['key'])
    do_extract_metadata(video.source_file(), t.name)
    # clean up
    t.close()
    return ("complete", "")


def extract_metadata(operation):
    params = loads(operation.params)
    source_file = File.objects.get(id=params['source_file_id'])
    do_extract_metadata(source_file, params['tmpfilename'])
    return ("complete", "")


def do_extract_metadata(source_file, filename):
    statsd.incr("extract_metadata")
    output = smart_text(
        subprocess.Popen(  # nosec
            [midentify_path(), filename],
            stdout=subprocess.PIPE).communicate()[0],
        errors='replace')
    for f, v in parse_metadata(output):
        source_file.set_metadata(f, v)


def parse_metadata(output):
    for line in output.split("\n"):
        try:
            line = line.strip()
            if "=" not in line:
                continue
            (f, v) = line.split("=")
            yield f, v
        except Exception as e:
            # just ignore any parsing issues
            print("exception in extract_metadata: " + str(e))
            print(line)


def pull_from_s3(suffix, bucket_name, key):
    s3 = boto3.resource(
        's3', aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY)
    bucket = s3.Bucket(bucket_name)
    k = bucket.Object(key)

    t = tempfile.NamedTemporaryFile(suffix=suffix)
    k.download_fileobj(t)
    t.seek(0)
    return t


def do_audio_encode(input_filename, tout):
    image_path = settings.AUDIO_POSTER_IMAGE
    command = audio_encode_command(image_path, input_filename, tout)
    os.system(command)  # nosec


def audio_encode(operation):
    statsd.incr("audio_encode")
    params = loads(operation.params)
    file_id = params['file_id']
    f = File.objects.get(id=file_id)
    assert f.is_s3()
    assert f.is_audio()
    video = f.video
    filename = os.path.basename(f.cap)
    suffix = video.extension()

    print("pulling from s3")
    t = pull_from_s3(suffix, settings.AWS_S3_UPLOAD_BUCKET,
                     video.s3_key())
    operation.log(info="downloaded from S3")

    print("encoding mp3 to mp4")
    tout = os.path.join(settings.TMP_DIR, str(operation.uuid) + ".mp4")
    do_audio_encode(t.name, tout)

    print("uploading to CUIT")
    sftp_put(filename, suffix, open(tout, "rb"), video)
    return ("complete", "")


def local_audio_encode(operation):
    """ pull the mp3 down from S3, run it through the mp3 -> mp4
    conversion process """
    statsd.incr("audio_encode")
    params = loads(operation.params)

    s3_key = params['s3_key']
    t = pull_from_s3(".mp3", settings.AWS_S3_UPLOAD_BUCKET, s3_key)
    operation.log(info="downloaded mp3 from S3")

    print("encoding mp3 to mp4")
    tout = os.path.join(settings.TMP_DIR, str(operation.uuid) + ".mp4")
    do_audio_encode(t.name, tout)

    if not os.path.exists(tout):
        # the encode failed and didn't produce the expected .mp4 file
        # this could be an issue with ffmpeg, or just a source file
        # that eg, isn't actually a valid mp3. either way, fail quickly
        # here.
        operation.log(info="expected mp4 output does not exist")
        return ("failed", "no output file produced")
    # stash the s3 key back in params
    params['mp4_tmpfilename'] = tout
    operation.params = dumps(params)
    operation.save()
    return ("complete", "")


def sftp_client():
    sftp_hostname = settings.SFTP_HOSTNAME
    sftp_user = settings.SFTP_USER
    sftp_private_key_path = settings.SSH_PRIVATE_KEY_PATH
    mykey = paramiko.RSAKey.from_private_key_file(sftp_private_key_path)
    transport = paramiko.Transport((sftp_hostname, 22))
    transport.connect(username=sftp_user, pkey=mykey)
    return (paramiko.SFTPClient.from_transport(transport), transport)


def sftp_stat(filename):
    sftp, transport = sftp_client()

    try:
        stat = sftp.stat(filename)
        return stat
    except SFTPError:
        return None
    except IOError:
        return None
    finally:
        sftp.close()
        transport.close()
    return stat


def sftp_put(filename, suffix, fileobj, video, file_label="CUIT H264",
             remote_base=None):
    sftp, transport = sftp_client()
    remote_filename = filename.replace(suffix, "_et" + suffix)
    if remote_base is None:
        # default to secure directory if not otherwise specified
        remote_base = os.path.join(
            settings.CUNIX_H264_DIRECTORY, "ccnmtl", "secure")
    remote_path = os.path.join(remote_base, remote_filename)

    try:
        sftp.putfo(fileobj, remote_path)
        sftp.chmod(remote_path, 644)
        File.objects.create(video=video,
                            label=file_label,
                            filename=remote_path,
                            location_type='cuit',
                            )
    except Exception as e:
        print("sftp put failed")
        print(str(e))
    else:
        print("sftp_put succeeded")
    finally:
        sftp.close()
        transport.close()


def sftp_delete(remote_path):
    sftp, transport = sftp_client()
    success = False
    try:
        sftp.remove(remote_path)
        success = True
    except Exception as e:
        print("sftp delete failed")
        print(str(e))
    else:
        print("sftp_put succeeded")
    finally:
        sftp.close()
        transport.close()
    return success


def delete_from_cunix(operation):
    print("delete file from cunix")
    params = loads(operation.params)
    file_id = params['file_id']
    f = File.objects.get(id=file_id)

    remote_filename = f.filename
    success = sftp_delete(remote_filename)
    if success:
        f.delete()
        operation.log(info="deleted file %s from cunix" % remote_filename)
        return ("complete", "")
    else:
        return ("failed", "failed to delete %s from cunix" % remote_filename)


def delete_from_s3(operation):
    print("delete file from s3")
    params = loads(operation.params)
    file_id = params['file_id']
    f = File.objects.get(id=file_id)

    bucket_name = settings.AWS_S3_UPLOAD_BUCKET
    if 'transcode' in f.label:
        bucket_name = settings.AWS_S3_OUTPUT_BUCKET

    s3 = boto3.resource(
        's3', aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY)
    bucket = s3.Bucket(bucket_name)

    key = f.cap
    bucket.delete_object(Key=key)

    f.delete()
    operation.log(info="deleted file %s from s3" % key)
    return ("complete", "")


def copy_from_s3_to_cunix(operation):
    statsd.incr("copy_from_s3_to_cunix")
    print("pulling from S3")
    params = loads(operation.params)

    file_id = params['file_id']
    f = File.objects.get(id=file_id)
    assert f.is_s3()

    resolution = 480
    if "720" in f.label:
        resolution = 720

    video = f.video
    (base, ext) = os.path.splitext(os.path.basename(f.cap))
    filename = (
        base + "-" + strip_special_characters(operation.video.title) + ext)
    suffix = video.extension()
    t = pull_from_s3(suffix, settings.AWS_S3_OUTPUT_BUCKET, f.cap)
    operation.log(info="downloaded from S3")

    remote_base = os.path.join(
        settings.CUNIX_H264_DIRECTORY, "ccnmtl", "secure")
    if video.collection.is_public():
        remote_base = os.path.join(
            settings.CUNIX_H264_DIRECTORY, "ccnmtl", "public")

    sftp_put(filename, suffix, t, video, "CUIT H264 %d" % resolution,
             remote_base)
    return ("complete", "")


def copy_from_cunix_to_s3(operation):
    print("copy file from cunix to S3")
    video = operation.video
    params = loads(operation.params)
    suffix = params['suffix']
    filename = params['filename']

    # pull the flv down from cunix
    t = tempfile.NamedTemporaryFile(suffix=suffix)
    sftp_get(filename, t.name)

    # upload it to S3
    s3 = boto3.resource(
        's3', aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY)

    # make a YYYY/MM/DD directory to put the file in
    n = datetime.now()
    key = "%04d/%02d/%02d/%s" % (
        n.year, n.month, n.day,
        os.path.basename(t.name))

    source_file = open(t.name, "rb")
    s3.Object(settings.AWS_S3_UPLOAD_BUCKET, key).put(
        Body=source_file)

    source_file.close()
    label = "uploaded source file (S3)"
    f = File.objects.create(video=video, url="", cap=key,
                            location_type="s3",
                            filename=t.name,
                            label=label)
    OperationFile.objects.create(operation=operation, file=f)
    # stash the s3 key back in params
    params['s3_key'] = key
    operation.params = dumps(params)
    operation.save()
    return ("complete", "")


def sftp_get(remote_filename, local_filename):
    statsd.incr("sftp_get")
    print("sftp_get(%s,%s)" % (remote_filename, local_filename))
    sftp, transport = sftp_client()

    try:
        sftp.get(remote_filename, local_filename)
    except Exception as e:
        print("sftp fetch failed")
        print(str(e))
        raise
    else:
        print("sftp_get succeeded")
    finally:
        sftp.close()
        transport.close()


def strip_special_characters(title):
    return re.sub(r'[\W_]+', '_', title)


def slow_operations():
    status_filters = ["enqueued", "in progress", "submitted"]
    return Operation.objects.filter(
        status__in=status_filters,
        modified__lt=datetime.now() - timedelta(hours=1)
    ).order_by("-modified")


def slow_operations_other_than_submitted():
    return Operation.objects.filter(
        status__in=["enqueued", "in progress"],
        modified__lt=datetime.now() - timedelta(hours=1)
    )


@app.task
def check_for_slow_operations():
    operations = slow_operations()
    if operations.count() > 0:
        other_than_submitted = slow_operations_other_than_submitted()
        if other_than_submitted.count() > 0:
            # there are operations that are enqueued or in progress
            # so sysadmins need to know too
            send_slow_operations_email(operations)
        else:
            # it's just 'submitted' operations that are slow
            # so it's just the video team's problem
            send_slow_operations_to_videoteam_email(operations)

    # else, no slow operations to warn about. excellent.


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(
            hour='7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23',
            minute='3',
            day_of_week='*'),
        check_for_slow_operations.s())
