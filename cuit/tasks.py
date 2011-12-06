from celery.decorators import task
from wardenclyffe.main.models import Video, File, Operation, OperationFile, OperationLog, Image
import wardenclyffe.main.tasks
import os.path
import os
import uuid 
import tempfile
import subprocess
from django.conf import settings
from django.core.mail import send_mail
import paramiko

# TODO: convert to decorator
def with_operation(f,video,action,params,user,args,kwargs):
    ouuid = uuid.uuid4()
    operation = Operation.objects.create(video=video,
                                         action=action,
                                         status="in progress",
                                         params=params,
                                         owner=user,
                                         uuid=ouuid)
    try:
        (success,message) = f(video,user,operation,*args,**kwargs)
        operation.status = success
        if operation.status == "failed" or message != "":
            log = OperationLog.objects.create(operation=operation,
                                              info=message)
    except Exception, e:
        operation.status = "failed"
        log = OperationLog.objects.create(operation=operation,
                                          info=str(e))
    operation.save()


def sftp_get(remote_filename,local_filename):
    print "sftp_get(%s,%s)" % (remote_filename,local_filename)
    sftp_hostname = settings.SFTP_HOSTNAME 
    sftp_path = settings.SFTP_PATH 
    sftp_user = settings.SFTP_USER 
    sftp_private_key_path = settings.SSH_PRIVATE_KEY_PATH
    mykey = paramiko.RSAKey.from_private_key_file(sftp_private_key_path)
    transport = paramiko.Transport((sftp_hostname, 22))
    transport.connect(username=sftp_user, pkey = mykey)
    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        sftp.get(remote_filename, local_filename)
    except Exception, e:
        print "sftp fetch failed"
        raise
    else:
        print "sftp_get succeeded"
    finally:
        sftp.close()
        transport.close()


@task(ignore_result=True)
def clear_out_tmpfile(tmpfilename):
    print "clearing out %s" % tmpfilename
    os.unlink(tmpfilename)

@task(ignore_result=True)
def import_from_cuit(video_id,user,**kwargs):
    print "importing from cuit (%d)" % video_id
    video = Video.objects.get(id=video_id)
    args = []
    def _import_from_cuit(video,user,operation,**kwargs):
        ouuid = operation.uuid
        f = File.objects.filter(video=video,location_type="cuit")[0]
        filename = f.filename
        extension = os.path.splitext(filename)[1]
        tmpfilename = os.path.join(settings.TMP_DIR,str(ouuid) + extension)
        sftp_get(filename,tmpfilename)
        log = OperationLog.objects.create(operation=operation,
                                          info="downloaded from CUIT")

        wardenclyffe.main.tasks.extract_metadata(operation,
                                       dict(source_file_id=f.id,
                                            tmpfilename=tmpfilename))
        wardenclyffe.main.tasks.make_images(operation,
                                  dict(tmpfilename=tmpfilename))
        print "calling clear out"
        clear_out_tmpfile.apply(args=(tmpfilename,))
        print "done clearing out"
        return ("complete","pulled from CUIT")
    with_operation(_import_from_cuit,video,
                   "import from CUIT",
                   "",user,args,kwargs)
