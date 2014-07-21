from datetime import datetime, timedelta
from angeldust import PCP
from celery.decorators import task
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from wardenclyffe.main.models import Video, File, Operation, OperationFile
from wardenclyffe.main.models import Image, Poster
from wardenclyffe.util.mail import send_slow_operations_email
from wardenclyffe.util.mail import send_slow_operations_to_videoteam_email
import os.path
import os
import tempfile
import subprocess
from django.conf import settings
from json import loads
import paramiko
import random
import re
import shutil
from django_statsd.clients import statsd
import boto
from boto.s3.key import Key
import waffle


def save_file_to_s3(operation, params):
    if not waffle.switch_is_active('enable_s3'):
        print "S3 uploads are disabled"
        return ("complete", "S3 uploads temporarily disabled")
    statsd.incr("save_file_to_s3")
    conn = boto.connect_s3(
        settings.AWS_ACCESS_KEY,
        settings.AWS_SECRET_KEY)
    bucket = conn.get_bucket(settings.AWS_S3_UPLOAD_BUCKET)
    k = Key(bucket)
    # make a YYYY/MM/DD directory to put the file in
    source_file = open(params['tmpfilename'], "rb")

    n = datetime.now()
    key = "%04d/%02d/%02d/%s" % (
        n.year, n.month, n.day,
        os.path.basename(params['tmpfilename']))
    k.key = key
    k.set_contents_from_file(source_file)
    source_file.close()
    f = File.objects.create(video=operation.video, url="", cap=key,
                            location_type="s3",
                            filename=params['filename'],
                            label="uploaded source file (S3)")
    OperationFile.objects.create(operation=operation, file=f)
    return ("complete", "")


IONICE = settings.IONICE_PATH
MPLAYER = settings.MPLAYER_PATH
MAX_SEEK_POS = "03:00:00"


def avi_image_extract_command(tmpdir, frames, tmpfilename):
    return ("%s -c 3 %s -nosound"
            " -vo jpeg:outdir=%s -endpos %s -frames %d"
            " -sstep 10 -correct-pts '%s' 2>/dev/null"
            % (IONICE, MPLAYER, tmpdir, MAX_SEEK_POS, frames, tmpfilename))


def image_extract_command(tmpdir, frames, tmpfilename):
    return ("%s -c 3 %s "
            "-nosound -vo jpeg:outdir=%s "
            "-endpos %s -frames %d "
            "-sstep 10 '%s' 2>/dev/null"
            % (IONICE, MPLAYER, tmpdir, MAX_SEEK_POS, frames, tmpfilename))


def fallback_image_extract_command(tmpdir, frames, tmpfilename):
    return ("%s -c 3 %s "
            "-nosound -vo jpeg:outdir=%s "
            "-endpos %s -frames %d "
            "-vf framerate=250 '%s' 2>/dev/null"
            % (IONICE, MPLAYER, tmpdir, MAX_SEEK_POS, frames, tmpfilename))


def honey_badger(f, *args, **kwargs):
    """ basically apply() wrapped in an exception handler.
    honey badger don't care if there's an exception"""
    try:
        return f(*args, **kwargs)
    except:
        pass


def image_extract_command_for_file(tmpdir, frames, tmpfilename):
    if tmpfilename.lower().endswith("avi"):
        return avi_image_extract_command(tmpdir, frames, tmpfilename)
    else:
        return image_extract_command(tmpdir, frames, tmpfilename)


def make_images(operation, params):
    statsd.incr("make_images")
    ouuid = operation.uuid
    tmpfilename = params['tmpfilename']
    tmpdir = settings.TMP_DIR + "/imgs/" + str(ouuid) + "/"
    honey_badger(os.makedirs, tmpdir)
    size = os.stat(tmpfilename)[6] / (1024 * 1024)
    frames = size * 2  # 2 frames per MB at the most
    command = image_extract_command_for_file(tmpdir, frames, tmpfilename)
    os.system(command)
    imgs = os.listdir(tmpdir)
    if len(imgs) == 0:
        command = fallback_image_extract_command(tmpdir, frames, tmpfilename)
        os.system(command)
    # TODO: parameterize
    imgdir = "%simages/%05d/" % (settings.MEDIA_ROOT, operation.video.id)
    honey_badger(os.makedirs, imgdir)
    imgs = os.listdir(tmpdir)
    imgs.sort()
    for img in imgs[:settings.MAX_FRAMES]:
        os.system("mv %s%s %s" % (tmpdir, img, imgdir))
        Image.objects.create(
            video=operation.video,
            image="images/%05d/%s" % (operation.video.id, img))
        statsd.incr("image_created")
    shutil.rmtree(tmpdir)
    if Poster.objects.filter(video=operation.video).count() == 0\
            and len(imgs) > 0:
        # pick a random image out of the set and assign
        # it as the poster on the video
        r = random.randint(0, min(len(imgs), 50) - 1)
        image = Image.objects.filter(video=operation.video)[r]
        Poster.objects.create(video=operation.video, image=image)

    return ("complete", "created %d images" % len(imgs))


def extract_metadata(operation, params):
    statsd.incr("extract_metadata")
    source_file = File.objects.get(id=params['source_file_id'])
    # warning: for now we're expecting the midentify script
    # to be relatively located to this file. this ought to
    # be a bit more configurable
    pwd = os.path.dirname(__file__)
    script_dir = os.path.join(pwd, "../../scripts/")
    output = unicode(subprocess.Popen([os.path.join(script_dir,
                                                    "midentify.sh"),
                                       params['tmpfilename']],
                                      stdout=subprocess.PIPE).communicate()[0],
                     errors='replace')
    for line in output.split("\n"):
        try:
            line = line.strip()
            if "=" not in line:
                continue
            (f, v) = line.split("=")
            source_file.set_metadata(f, v)
        except Exception, e:
            # just ignore any parsing issues
            print "exception in extract_metadata: " + str(e)
            print line
    return ("complete", "")


@task(ignore_results=True)
def process_operation(operation_id, params, **kwargs):
    print "process_operation(%s,%s)" % (operation_id, str(params))
    try:
        operation = Operation.objects.get(id=operation_id)
        operation.process(params)
    except Operation.DoesNotExist:
        print "operation not found (probably deleted)"


def submit_to_pcp(operation, params):
    statsd.incr("submit_to_pcp")
    ouuid = operation.uuid

    # ignore the passed in params and use the ones from the operation object
    params = loads(operation.params)
    pcp = PCP(settings.PCP_BASE_URL, settings.PCP_USERNAME,
              settings.PCP_PASSWORD)
    # TODO: probably don't always want it to be .mp4
    filename = str(ouuid) + (operation.video.filename() or ".mp4")
    fileobj = open(params['tmpfilename'])
    title = "%s-%s" % (str(ouuid),
                       strip_special_characters(operation.video.title))
    pcp.upload_file(fileobj, filename, params['pcp_workflow'], title,
                    operation.video.description)
    return ("submitted", "")


def pull_from_s3_and_submit_to_pcp(operation, params):
    statsd.incr("pull_from_s3_and_submit_to_pcp")
    print "pulling from S3"
    params = loads(operation.params)
    video_id = params['video_id']
    workflow = params['workflow']
    video = Video.objects.get(id=video_id)
    ouuid = operation.uuid
    filename = video.filename()
    suffix = video.extension()

    conn = boto.connect_s3(
        settings.AWS_ACCESS_KEY,
        settings.AWS_SECRET_KEY)
    bucket = conn.get_bucket(settings.AWS_S3_UPLOAD_BUCKET)
    k = Key(bucket)
    k.key = video.s3_key()

    t = tempfile.NamedTemporaryFile(suffix=suffix)
    k.get_contents_to_file(t)
    t.seek(0)

    operation.log(info="downloaded from S3")
    # TODO: figure out how to re-use submit_to_pcp()
    print "submitting to PCP"
    pcp = PCP(settings.PCP_BASE_URL, settings.PCP_USERNAME,
              settings.PCP_PASSWORD)
    filename = str(ouuid) + suffix
    print "submitted with filename %s" % filename

    title = "%s-%s" % (str(ouuid), strip_special_characters(video.title))
    print "submitted with title %s" % title
    pcp.upload_file(t, filename, workflow, title, video.description)
    return ("submitted", "submitted to PCP")


def sftp_get(remote_filename, local_filename):
    statsd.incr("sftp_get")
    print "sftp_get(%s,%s)" % (remote_filename, local_filename)
    sftp_hostname = settings.SFTP_HOSTNAME
    sftp_user = settings.SFTP_USER
    sftp_private_key_path = settings.SSH_PRIVATE_KEY_PATH
    mykey = paramiko.RSAKey.from_private_key_file(sftp_private_key_path)
    transport = paramiko.Transport((sftp_hostname, 22))
    transport.connect(username=sftp_user, pkey=mykey)
    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        sftp.get(remote_filename, local_filename)
    except Exception, e:
        print "sftp fetch failed"
        print str(e)
        raise
    else:
        print "sftp_get succeeded"
    finally:
        sftp.close()
        transport.close()


def pull_from_cuit_and_submit_to_pcp(operation, params):
    statsd.incr("pull_from_cuit_and_submit_to_pcp")
    print "pulling from cuit"
    params = loads(operation.params)
    video_id = params['video_id']
    workflow = params['workflow']
    video = Video.objects.get(id=video_id)
    if workflow == "":
        return ("failed", "no workflow specified")

    ouuid = operation.uuid
    cuit_file = video.file_set.filter(video=video, location_type="cuit")[0]

    filename = cuit_file.filename
    extension = os.path.splitext(filename)[1]
    tmpfilename = os.path.join(settings.TMP_DIR, str(ouuid) + extension)
    sftp_get(filename, tmpfilename)
    operation.log(info="downloaded from cuit")

    print "submitting to PCP"
    pcp = PCP(settings.PCP_BASE_URL, settings.PCP_USERNAME,
              settings.PCP_PASSWORD)
    filename = str(ouuid) + extension
    print "submitted with filename %s" % filename

    title = "%s-%s" % (str(ouuid), strip_special_characters(video.title))
    print "submitted with title %s" % title
    pcp.upload_file(open(tmpfilename, "r"), filename, workflow, title,
                    video.description)
    return ("submitted", "submitted to PCP")


def strip_special_characters(title):
    return re.sub('[\W_]+', '_', title)


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


@periodic_task(
    run_every=crontab(
        hour="7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23",
        minute="3", day_of_week="*"))
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
