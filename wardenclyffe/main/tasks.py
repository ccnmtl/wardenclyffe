import urllib2
from restclient import GET, POST
import requests
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
import tempfile
import subprocess
from django.conf import settings
from json import loads
import paramiko
import random
import re
import shutil
from django_statsd.clients import statsd
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
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


def split_cap(tahoe_url):
    parts = tahoe_url.split('URI:DIR2')
    return (parts[0], "URI:DIR2" + parts[1])


def get_or_create_tahoe_dir(tahoe_base, dirname):
    base, cap = split_cap(tahoe_base)
    info = loads(GET(tahoe_base + "?t=json"))
    dirnode = info[1]
    children = dirnode['children']
    if dirname not in children:
        # need to make it
        new_cap = POST(
            tahoe_base,
            params=dict(
                t="mkdir",
                name=dirname), async=False)
        return base + new_cap + "/"
    else:
        new_cap = children[dirname][1]['rw_uri']
        return base + new_cap + "/"


def get_date_dir(tahoe_base):
    n = datetime.now()
    year = "%04d" % n.year
    month = "%02d" % n.month
    day = "%02d" % n.day
    year_dir = get_or_create_tahoe_dir(tahoe_base, year)
    month_dir = get_or_create_tahoe_dir(year_dir, month)
    day_dir = get_or_create_tahoe_dir(month_dir, day)
    return day_dir


def save_file_to_tahoe(operation, params):
    statsd.incr("save_file_to_tahoe")
    # make a YYYY/MM/DD directory to put the file in
    # instead of dumping everything in one big directory
    # which is getting slow to update
    tahoe_base = get_date_dir(settings.TAHOE_BASE)
    source_file = open(params['tmpfilename'], "rb")
    register_openers()
    datagen, headers = multipart_encode(
        (
            ("t", "upload"),
            MultipartParam(name='file', fileobj=source_file,
                           filename=os.path.basename(params['tmpfilename']))))
    request = urllib2.Request(tahoe_base, datagen, headers)
    try:
        cap = urllib2.urlopen(request).read()
    except Exception, e:
        return ("failed", "tahoe gave an error: " + str(e))

    source_file.close()
    if not cap.startswith('URI'):
        # looks like we didn't get a response we were expecting from tahoe
        return ("failed", "upload failed (invalid cap): " + cap)

    f = File.objects.create(video=operation.video, url="", cap=cap,
                            location_type="tahoe",
                            filename=params['filename'],
                            label="uploaded source file")
    OperationFile.objects.create(operation=operation, file=f)
    return ("complete", "")


IONICE = "/usr/bin/ionice"
MPLAYER = "/usr/bin/mplayer"
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
    imgdir = "/var/www/wardenclyffe/uploads/images/%05d/" % operation.video.id
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


def pull_from_tahoe_and_submit_to_pcp(operation, params):
    statsd.incr("pull_from_tahoe_and_submit_to_pcp")
    print "pulling from tahoe"
    params = loads(operation.params)
    video_id = params['video_id']
    workflow = params['workflow']
    video = Video.objects.get(id=video_id)
    ouuid = operation.uuid
    url = video.tahoe_download_url()
    if url == "":
        return ("failed", "does not have a tahoe stored file")
    if workflow == "":
        return ("failed", "no workflow specified")
    filename = video.filename()
    suffix = video.extension()
    t = tempfile.NamedTemporaryFile(suffix=suffix)
    r = urllib2.urlopen(url)
    t.write(r.read())
    t.seek(0)
    operation.log(info="downloaded from tahoe")
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
    print "pulling from tahoe"
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


@task(ignore_results=True)
def move_file(file_id):
    f = File.objects.get(id=file_id)
    conn = boto.connect_s3(
        settings.AWS_ACCESS_KEY,
        settings.AWS_SECRET_KEY)
    bucket = conn.get_bucket(settings.AWS_S3_UPLOAD_BUCKET)
    video = f.video
    url = video.tahoe_download_url()
    if url == "":
        print "does not have a tahoe stored file"
        return
    print "pulling from %s" % url
    suffix = video.extension()
    t = tempfile.NamedTemporaryFile(suffix=suffix)
    r = requests.get(url, stream=True)
    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            t.write(chunk)
            t.flush()
    t.seek(0)
    print "pulled from tahoe and wrote to temp file"

    k = Key(bucket)
    # make a YYYY/MM/DD directory to put the file in
    n = video.created
    key = "%04d/%02d/%02d/%s" % (
        n.year, n.month, n.day,
        os.path.basename(video.filename()))
    k.key = key
    print "uploading to S3 with key %s" % key
    k.set_contents_from_file(t)
    t.close()
    print "uploaded"
    File.objects.create(video=video, url="", cap=key,
                        location_type="s3",
                        filename=video.filename(),
                        label="uploaded source file (S3)")

    print "remove tahoe file entry"
    f.delete()
