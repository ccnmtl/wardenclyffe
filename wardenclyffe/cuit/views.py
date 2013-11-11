from annoying.decorators import render_to
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from wardenclyffe.main.models import Video, Operation, File, Server
from wardenclyffe.main.models import ServerFile, Collection
from wardenclyffe.main.tasks import process_operation
import uuid
import os
from django.conf import settings
from django.db import transaction
import paramiko
import stat


def sftp_recursive_listdir(sftp, basedir):
    sftp.chdir(basedir)
    try:
        contents = sftp.listdir_attr()
    except:
        return []
    child_files = []
    child_dirs = []
    for f in contents:
        kind = stat.S_IFMT(f.st_mode)
        if kind == stat.S_IFDIR:
            child_dirs.append(f.filename)
        else:
            child_files.append(basedir + "/" + f.filename)
    for d in child_dirs:
        children = sftp_recursive_listdir(sftp, basedir + "/" + d)
        child_files = child_files + children
    return child_files


def list_all_cuit_files():
    sftp_hostname = settings.SFTP_HOSTNAME
    sftp_path = settings.SFTP_PATH
    sftp_user = settings.SFTP_USER
    sftp_private_key_path = settings.SSH_PRIVATE_KEY_PATH
    mykey = paramiko.RSAKey.from_private_key_file(sftp_private_key_path)
    transport = paramiko.Transport((sftp_hostname, 22))
    transport.connect(username=sftp_user, pkey=mykey)
    sftp = paramiko.SFTPClient.from_transport(transport)
    results = sftp_recursive_listdir(sftp, sftp_path)
    sftp.close()
    return results


@login_required
@render_to('cuit/index.html')
def index(request):
    all_files = list_all_cuit_files()
    return dict(dirs=[f for f in all_files if f.endswith(".mov")])


@transaction.commit_manually
@login_required
def import_quicktime(request):
    if request.method != "POST":
        return HttpResponseRedirect("/cuit/")
    operations = []
    params = []
    try:
        s = Collection.objects.get(id=settings.QUICKTIME_IMPORT_COLLECTION_ID)
        server = Server.objects.get(id=settings.QUICKTIME_IMPORT_SERVER_ID)

        for filename in list_all_cuit_files():
            if not filename.endswith(".mov"):
                continue
            vuuid = uuid.uuid4()
            # make db entry
            v = Video.objects.create(collection=s,
                                     title=os.path.basename(filename),
                                     creator=request.user.username,
                                     uuid=vuuid)
            cuit_file = File.objects.create(video=v,
                                            label="cuit file",
                                            filename=filename,
                                            location_type='cuit')
            ServerFile.objects.create(server=server, file=cuit_file)
            v.make_source_file("")
            o, p = v.make_import_from_cuit_operation(v.id, request.user)
            operations.append(o)
            params.append(p)
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()
        for o, p in zip(operations, params):
            process_operation.delay(o.id, p)
        return HttpResponse("database entries created. import has begun.")


@render_to("cuit/retry.html")
def import_retry(request):
    failed = Operation.objects.filter(action="import from CUIT",
                                      status="failed")
    if request.method != "POST":
        return dict(failed=failed)
    for operation in failed:
        # try again
        process_operation.delay(operation.id, operation.params)
    return HttpResponse("retry has begun.")


@render_to("cuit/broken_quicktime.html")
def broken_quicktime(request):
    broken_files = []
    s = Collection.objects.get(id=settings.QUICKTIME_IMPORT_COLLECTION_ID)
    for v in s.video_set.all():
        f = v.cuit_file()
        if not f:
            continue
        if f.get_metadata("ID_AUDIO_FORMAT") != "255":
            broken_files.append(f)

    return dict(broken_files=broken_files)
