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
    print "sftp_recursive_listdir(%s)" % basedir
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

@render_to('cuit/index.html')
def index(request):
    sftp_hostname = settings.SFTP_HOSTNAME 
    sftp_path = settings.SFTP_PATH 
    sftp_user = settings.SFTP_USER 
    sftp_private_key_path = settings.SSH_PRIVATE_KEY_PATH
    mykey = paramiko.RSAKey.from_private_key_file(sftp_private_key_path)
    transport = paramiko.Transport((sftp_hostname, 22))
    transport.connect(username=sftp_user, pkey = mykey)
    sftp = paramiko.SFTPClient.from_transport(transport)
    all_files = sftp_recursive_listdir(sftp,sftp_path)

    return dict(dirs=all_files)
