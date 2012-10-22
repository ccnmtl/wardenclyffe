import urllib2
from restclient import GET, POST
from datetime import datetime
from angeldust import PCP
from celery.decorators import task
from wardenclyffe.main.models import Video, File, Operation, OperationFile
from wardenclyffe.main.models import OperationLog, Image, Poster
import os.path
import uuid
import tempfile
import subprocess
from django.conf import settings
from simplejson import dumps, loads
import paramiko
import random
import re
import requests
import shutil
from django_statsd.clients import statsd


# TODO: convert to decorator
def with_operation(f, video, action, params, user, args, kwargs):
    ouuid = uuid.uuid4()
    operation = Operation.objects.create(video=video,
                                         action=action,
                                         status="in progress",
                                         params=dumps(params),
                                         owner=user,
                                         uuid=ouuid)
    try:
        (success, message) = f(video, user, operation, *args, **kwargs)
        operation.status = success
        if operation.status == "failed" or message != "":
            OperationLog.objects.create(operation=operation, info=message)
    except Exception, e:
        operation.status = "failed"
        OperationLog.objects.create(operation=operation, info=str(e))
    operation.save()


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
        new_cap = POST(tahoe_base, params=dict(
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

    files = {
        'file': (os.path.basename(params['tmpfilename']),
         open(params['tmpfilename'], "rb"))
        }
    try:
        r = requests.post(tahoe_base, params=dict(t="upload"), files=files)
        cap = r.text
    except Exception, e:
        return ("failed", "tahoe gave an error: " + str(e))

    if not cap.startswith('URI'):
        # looks like we didn't get a response we were expecting from tahoe
        return ("failed", "upload failed: " + cap)

    f = File.objects.create(video=operation.video, url="", cap=cap,
                            location_type="tahoe",
                            filename=params['filename'],
                            label="uploaded source file")
    OperationFile.objects.create(operation=operation, file=f)
    return ("complete", "")


def make_images(operation, params):
    statsd.incr("make_images")
    ouuid = operation.uuid
    tmpfilename = params['tmpfilename']
    tmpdir = settings.TMP_DIR + "/imgs/" + str(ouuid) + "/"
    try:
        os.makedirs(tmpdir)
    except:
        pass
    size = os.stat(tmpfilename)[6] / (1024 * 1024)
    frames = size * 2  # 2 frames per MB at the most
    if tmpfilename.lower().endswith("avi"):
        command = ("/usr/bin/ionice -c 3 /usr/bin/mplayer -nosound"
                   " -vo jpeg:outdir=%s -endpos 03:00:00 -frames %d"
                   " -sstep 10 -correct-pts '%s' 2>/dev/null"
                   % (tmpdir, frames, tmpfilename))
    else:
        command = ("/usr/bin/ionice -c 3 /usr/bin/mplayer "
                   "-nosound -vo jpeg:outdir=%s "
                   "-endpos 03:00:00 -frames %d "
                   "-sstep 10 '%s' 2>/dev/null"
                   % (tmpdir, frames, tmpfilename))
    os.system(command)
    imgs = os.listdir(tmpdir)
    if len(imgs) == 0:
        command = ("/usr/bin/ionice -c 3 /usr/bin/mplayer "
                   "-nosound -vo jpeg:outdir=%s "
                   "-endpos 03:00:00 -frames %d "
                   "-vf framerate=250 '%s' 2>/dev/null"
                   % (tmpdir, frames, tmpfilename))
        os.system(command)
    # TODO: parameterize
    imgdir = "/var/www/wardenclyffe/uploads/images/%05d/" % operation.video.id
    try:
        os.makedirs(imgdir)
    except:
        pass
    imgs = os.listdir(tmpdir)
    imgs.sort()
    for img in imgs:
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
        r = random.randint(0, len(imgs) - 1)
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
    script_dir = os.path.join(pwd, "../scripts/")
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
    operation = Operation.objects.get(id=operation_id)
    operation.process(params)


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


@task(ignore_result=True)
def pull_from_tahoe_and_submit_to_pcp(video_id, user, workflow, pcp_base_url,
                                      pcp_username, pcp_password, **kwargs):
    statsd.incr("pull_from_tahoe_and_submit_to_pcp")
    print "pulling from tahoe"
    video = Video.objects.get(id=video_id)
    args = [workflow, pcp_base_url, pcp_username, pcp_password]

    def _do_pull_from_tahoe_and_submit_to_pcp(video, user, operation,
                                              workflow, pcp_base_url,
                                              pcp_username, pcp_password,
                                              **kwargs):
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
        OperationLog.objects.create(operation=operation,
                                    info="downloaded from tahoe")
        # TODO: figure out how to re-use submit_to_pcp()
        print "submitting to PCP"
        pcp = PCP(pcp_base_url, pcp_username, pcp_password)
        filename = str(ouuid) + suffix
        print "submitted with filename %s" % filename

        title = "%s-%s" % (str(ouuid), strip_special_characters(video.title))
        print "submitted with title %s" % title
        pcp.upload_file(t, filename, workflow, title, video.description)
        return ("submitted", "submitted to PCP")
    with_operation(_do_pull_from_tahoe_and_submit_to_pcp, video,
                   "pull from tahoe and submit to pcp",
                   "workflow: %s" % workflow,
                   user, args, kwargs)


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


@task(ignore_result=True)
def pull_from_cuit_and_submit_to_pcp(video_id, user, workflow, pcp_base_url,
                                     pcp_username, pcp_password, **kwargs):
    statsd.incr("pull_from_cuit_and_submit_to_pcp")
    print "pulling from tahoe"
    video = Video.objects.get(id=video_id)
    args = [workflow, pcp_base_url, pcp_username, pcp_password]

    def _do_pull_from_cuit_and_submit_to_pcp(video, user, operation, workflow,
                                             pcp_base_url, pcp_username,
                                             pcp_password, **kwargs):
        if workflow == "":
            return ("failed", "no workflow specified")

        ouuid = operation.uuid
        cuit_file = video.file_set.filter(video=video, location_type="cuit")[0]

        filename = cuit_file.filename
        extension = os.path.splitext(filename)[1]
        tmpfilename = os.path.join(settings.TMP_DIR, str(ouuid) + extension)
        sftp_get(filename, tmpfilename)

        OperationLog.objects.create(operation=operation,
                                    info="downloaded from cuit")

        print "submitting to PCP"
        pcp = PCP(pcp_base_url, pcp_username, pcp_password)
        filename = str(ouuid) + extension
        print "submitted with filename %s" % filename

        title = "%s-%s" % (str(ouuid), strip_special_characters(video.title))
        print "submitted with title %s" % title
        pcp.upload_file(open(tmpfilename, "r"), filename, workflow, title,
                        video.description)
        return ("submitted", "submitted to PCP")
    with_operation(_do_pull_from_cuit_and_submit_to_pcp, video,
                   "pull from cuit and submit to pcp",
                   "workflow: %s" % workflow,
                   user, args, kwargs)


@task(ignore_result=True)
def flv_encode(video_id, user, basedir, infile, outfile, ffmpeg_path):
    statsd.incr("flv_encode")
    print "flv_encode"
    args = [basedir, infile, outfile, ffmpeg_path]

    def _do_flv_encode(video, user, operation, basedir, infile, outfile,
                       ffmpeg_path):
        command = ("""%s -i "%s/%s" -y -f flv -vcodec flv -qmin 1 -b """
                   """800k -s '480x360' -me_method epzs -r 29.97 -g 100 """
                   """-qcomp 0.6 -qmax 15 -qdiff 4 -i_qfactor """
                   """0.71428572 -b_qfactor 0.76923078 -subq 6 """
                   """-acodec libmp3lame -ab 128k -ar 22050 """
                   """-ac 2 -benchmark "%s/%s" """
                   % (ffmpeg_path, basedir, infile, basedir, outfile))
        os.system(command)
        return ("complete", "flv encoded")

    with_operation(_do_flv_encode, None, "flv encode",
                   "", user, args, {})


def strip_special_characters(title):
    return re.sub('[\W_]+', '_', title)
