from json import loads

from django.conf import settings
from django_statsd.clients import statsd
from panopto.upload import PanoptoUpload, PanoptoUploadStatus

from wardenclyffe.main.models import Video, File
from wardenclyffe.main.tasks import pull_from_s3
import wardenclyffe.main.tasks as tasks


def panopto_upload(operation, video, folder, input_file):
    uploader = PanoptoUpload()
    uploader.server = settings.PANOPTO_SERVER
    uploader.folder = folder
    uploader.username = settings.PANOPTO_API_USER
    uploader.instance_name = settings.PANOPTO_INSTANCE_NAME
    uploader.application_key = settings.PANOPTO_APPLICATION_KEY
    uploader.input_file = input_file
    uploader.title = video.title
    uploader.description = video.description
    uploader.dest_filename = '{}.{}'.format(video.uuid, video.extension())

    if not uploader.create_session():
        operation.fail('Failed to create a Panopto upload session')
        return None
    operation.log(info="Panopto upload initialized")

    uploader.create_bucket()
    operation.log(info="Upload bucket created")

    uploader.upload_manifest()
    operation.log(info="Manifest uploaded")

    uploader.upload_media()
    operation.log(info="Media file uploaded")

    if not uploader.complete_session():
        operation.fail('Panopto complete session failed')
        return None

    operation.log(info="Panopto upload completed")
    return uploader


def pull_from_s3_and_upload_to_panopto(operation):
    statsd.incr('pull_from_s3_and_upload_to_panopto')

    params = loads(operation.params)
    video_id = params['video_id']
    video = Video.objects.get(id=video_id)

    suffix = video.extension()
    tmp = pull_from_s3(
        suffix, settings.AWS_S3_UPLOAD_BUCKET, video.s3_key())
    operation.log(info='downloaded from S3')

    # the pull_from_s3 returns an open file pointer. Wait to close it
    # until the pypanopto library reads it
    uploader = panopto_upload(operation, video, params['folder'], tmp.name)
    tmp.close()

    if uploader:
        # queue another operation
        op = video.make_verify_upload_to_panopto_operation(
            operation.owner, video.id, uploader.get_upload_id())
        tasks.process_operation.delay(op.id)

    return ('complete', '')


def verify_upload_to_panopto(operation):
    statsd.incr('verify upload to panopto')

    params = loads(operation.params)
    video_id = params['video_id']
    video = Video.objects.get(id=video_id)
    user = operation.owner

    upload_status = PanoptoUploadStatus()
    upload_status.server = settings.PANOPTO_SERVER
    upload_status.username = settings.PANOPTO_API_USER
    upload_status.instance_name = settings.PANOPTO_INSTANCE_NAME
    upload_status.application_key = settings.PANOPTO_APPLICATION_KEY
    upload_status.upload_id = params['upload_id']

    (state, panopto_id) = upload_status.check()
    if panopto_id is None:
        raise Exception('Panopto is not yet finished.')

    url = 'https://{}/Panopto/Pages/Viewer.aspx?id={}'.format(
        settings.PANOPTO_SERVER, panopto_id)

    File.objects.create(
        video=video, location_type="panopto", url=url,
        filename=panopto_id, label="uploaded to panopto")

    upload_status.set_viewer(panopto_id, [user.username])

    return ('complete', '')
