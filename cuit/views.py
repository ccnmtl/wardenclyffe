from annoying.decorators import render_to
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from main.models import Video, Operation, Series, File, Metadata, OperationLog, OperationFile, Image, Poster
from django.contrib.auth.models import User
import uuid 
import tasks
import os
from django.conf import settings
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from simplejson import loads, dumps
from django.db.models import Q
from django.core.mail import send_mail
import re
import paramiko
import stat

def sftp_recursive_listdir(sftp,basedir):
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
        children = sftp_recursive_listdir(sftp,basedir + "/" + d)
        child_files = child_files + children
    return child_files

def list_all_cuit_files():
    sftp_hostname = settings.SFTP_HOSTNAME 
    sftp_path = settings.SFTP_PATH 
    sftp_user = settings.SFTP_USER 
    sftp_private_key_path = settings.SSH_PRIVATE_KEY_PATH
    mykey = paramiko.RSAKey.from_private_key_file(sftp_private_key_path)
    transport = paramiko.Transport((sftp_hostname, 22))
    transport.connect(username=sftp_user, pkey = mykey)
    sftp = paramiko.SFTPClient.from_transport(transport)
    return sftp_recursive_listdir(sftp,sftp_path)

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

    try:
        s = Series.objects.get(id=settings.QUICKTIME_IMPORT_SERIES_ID)

        video_ids = []
        for filename in list_all_cuit_files():
            if not filename.endswith(".mov"):
                continue
            vuuid = uuid.uuid4()
            # make db entry
            v = Video.objects.create(series=s,
                                     title=os.path.basename(filename),
                                     creator=request.user.username,
                                     uuid = vuuid)
            cuit_file = File.objects.create(video=v,
                                            label="cuit file",
                                            filename=filename,
                                            location_type='cuit')
            source_file = File.objects.create(video=v,
                                              label="source file",
                                              filename="",
                                              location_type='none')

            video_ids.append(v.id)
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()
        for video_id in video_ids:
            tasks.import_from_cuit.delay(video_id,request.user)
        return HttpResponse("database entries created. import has begun.")
