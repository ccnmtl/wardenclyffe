# Generated by Django 4.2.18 on 2025-02-05 16:45

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_file_st_size'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='collection',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AlterModelOptions(
            name='file',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AlterModelOptions(
            name='operation',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AlterModelOptions(
            name='operationlog',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AlterModelOptions(
            name='serverfile',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AlterModelOptions(
            name='video',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AddField(
            model_name='operation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='operation',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='contributor',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='collection',
            name='creator',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='collection',
            name='description',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='language',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='collection',
            name='license',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='collection',
            name='subject',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='cap',
            field=models.CharField(blank=True, default='', max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='filename',
            field=models.CharField(blank=True, default='', max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='label',
            field=models.CharField(blank=True, default='', max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='location_type',
            field=models.CharField(choices=[('pcp', 'pcp'), ('cuit', 'cuit'), ('youtube', 'youtube'), ('s3', 's3'), ('panopto', 'panopto'), ('none', 'none')], default='s3', max_length=256),
        ),
        migrations.AlterField(
            model_name='file',
            name='url',
            field=models.URLField(blank=True, default='', max_length=2000, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='field',
            field=models.CharField(default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='value',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='operation',
            name='action',
            field=models.CharField(default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='operation',
            name='params',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='operation',
            name='status',
            field=models.CharField(default='in progress', max_length=256),
        ),
        migrations.AlterField(
            model_name='operationlog',
            name='info',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='server',
            name='base_dir',
            field=models.CharField(default='/', max_length=256),
        ),
        migrations.AlterField(
            model_name='server',
            name='base_url',
            field=models.CharField(default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='server',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='server',
            name='server_type',
            field=models.CharField(default='sftp', max_length=256),
        ),
        migrations.AlterField(
            model_name='video',
            name='creator',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='video',
            name='description',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='language',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='video',
            name='license',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='video',
            name='subject',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
