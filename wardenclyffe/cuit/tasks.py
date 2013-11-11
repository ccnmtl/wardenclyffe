from celery.decorators import task
from wardenclyffe.main.models import Video, File
import wardenclyffe.main.tasks
import os.path
import os
from django.conf import settings
from json import loads


@task(ignore_result=True)
def clear_out_tmpfile(tmpfilename):
    print "clearing out %s" % tmpfilename
    os.unlink(tmpfilename)


def import_from_cuit(operation, params):
    params = loads(operation.params)
    video_id = params['video_id']
    print "importing from cuit (%d)" % video_id
    video = Video.objects.get(id=video_id)

    ouuid = operation.uuid
    f = File.objects.filter(video=video, location_type="cuit")[0]
    filename = f.filename
    extension = os.path.splitext(filename)[1]
    tmpfilename = os.path.join(settings.TMP_DIR, str(ouuid) + extension)
    wardenclyffe.main.tasks.sftp_get(filename, tmpfilename)
    operation.log(info="downloaded from CUIT")

    wardenclyffe.main.tasks.extract_metadata(
        operation,
        dict(source_file_id=f.id,
             tmpfilename=tmpfilename))
    wardenclyffe.main.tasks.make_images(
        operation,
        dict(tmpfilename=tmpfilename))
    print "calling clear out"
    clear_out_tmpfile.apply(args=(tmpfilename,))
    print "done clearing out"
    return ("complete", "pulled from CUIT")
