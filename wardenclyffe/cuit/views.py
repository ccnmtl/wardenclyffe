from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
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
def index(request):
    all_files = list_all_cuit_files()
    return render(request, 'cuit/index.html',
                  dict(dirs=[f for f in all_files if f.endswith(".mov")]))


@transaction.non_atomic_requests()
@login_required
def import_quicktime(request):
    if request.method != "POST":
        return HttpResponseRedirect("/cuit/")
    operations = []

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
        o = v.make_import_from_cuit_operation(v.id, request.user)
        operations.append(o)

    for o in operations:
        process_operation.delay(o.id)
    return HttpResponse("database entries created. import has begun.")


def import_retry(request):
    failed = Operation.objects.filter(action="import from CUIT",
                                      status="failed")
    if request.method != "POST":
        return render(request, "cuit/retry.html", dict(failed=failed))
    for operation in failed:
        # try again
        process_operation.delay(operation.id)
    return HttpResponse("retry has begun.")
