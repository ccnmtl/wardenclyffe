from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from wardenclyffe.main.models import Video, File
import wardenclyffe.main.tasks as tasks


class Command(BaseCommand):
    args = ''
    help = ''

    def add_arguments(self, parser):
        # we need to specify a user to associate with the operations
        parser.add_argument('uni', type=str)
        parser.add_argument('dryrun', type=int, default=1)

    def redundant_files(self):
        # Videos that have both an "uploaded source file (S3)" and a
        # "transcoded file (S3)" can have the "uploaded" file removed
        qs = Video.objects.filter(
            file__label__startswith='transcoded').filter(
                file__label='uploaded source file (S3)').distinct()
        vids = qs.values_list('id', flat=True)
        return File.objects.filter(
            label='uploaded source file (S3)', video__id__in=vids)

    def orphaned_files(self):
        # Files that are attached to videos with no public endpoint
        # Likely the public endpoint was deleted at some point, and left
        # the S3 file orphaned
        valid_types = ['cuit', 'panopto', 'youtube', 'mediathread', 'rtsp_url']

        qs = Video.objects.exclude(file__location_type__in=valid_types)
        qs = qs.filter(file__location_type__in=['s3']).distinct()
        vids = qs.values_list('id', flat=True)
        return File.objects.filter(location_type='s3', video__id__in=vids)

    def handle(self, *args, **kwargs):
        user = User.objects.get(username=kwargs['uni'])
        print('{} executing job'.format(user.get_full_name()))

        dryrun = kwargs['dryrun']
        if dryrun:
            print('This is a dryrun')
        else:
            print('This is not a dryrun')

        qs = self.orphaned_files()
        print('Found {} files to delete'.format(qs.count()))
        for f in qs:
            if not dryrun:
                print('Video {}'.format(f.video.id))
                print('  {}: {}: {}'.format(f.label, f.location_type, f.id))

                o = f.video.make_delete_from_s3_operation(file_id=f.id,
                                                          user=user)
                tasks.process_operation.delay(o.id)
                print('  deleted')

        qs = self.redundant_files()
        print('Found {} redundant files to delete'.format(qs.count()))
        for f in qs:
            if not dryrun:
                print('Video {}'.format(f.video.id))
                print('  {}: {}: {}'.format(f.label, f.location_type, f.id))

                o = f.video.make_delete_from_s3_operation(file_id=f.id,
                                                          user=user)
                tasks.process_operation.delay(o.id)
                print('  deleted')
