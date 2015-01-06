# flake8: noqa
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sorl.thumbnail.fields
import django.utils.timezone
from django.conf import settings
import taggit.managers
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=256)),
                ('creator', models.CharField(default=b'', max_length=256, blank=True)),
                ('contributor', models.CharField(default=b'', max_length=256, blank=True)),
                ('language', models.CharField(default=b'', max_length=256, blank=True)),
                ('description', models.TextField(default=b'', null=True, blank=True)),
                ('subject', models.TextField(default=b'', null=True, blank=True)),
                ('license', models.CharField(default=b'', max_length=256, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('uuid', django_extensions.db.fields.UUIDField(max_length=36, editable=False, blank=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CollectionWorkflow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('workflow', models.CharField(default=b'', max_length=256, blank=True)),
                ('label', models.CharField(default=b'', max_length=256, blank=True)),
                ('collection', models.ForeignKey(to='main.Collection')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('label', models.CharField(default=b'', max_length=256, null=True, blank=True)),
                ('url', models.URLField(default=b'', max_length=2000, null=True, blank=True)),
                ('cap', models.CharField(default=b'', max_length=256, null=True, blank=True)),
                ('filename', models.CharField(default=b'', max_length=256, null=True, blank=True)),
                ('location_type', models.CharField(default=b's3', max_length=256, choices=[(b'pcp', b'pcp'), (b'cuit', b'cuit'), (b'youtube', b'youtube'), (b's3', b's3'), (b'none', b'none')])),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('image', sorl.thumbnail.fields.ImageWithThumbnailsField(upload_to=b'images')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Metadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field', models.CharField(default=b'', max_length=256)),
                ('value', models.TextField(default=b'', null=True, blank=True)),
                ('file', models.ForeignKey(to='main.File')),
            ],
            options={
                'ordering': ('field',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('action', models.CharField(default=b'', max_length=256)),
                ('status', models.CharField(default=b'in progress', max_length=256)),
                ('params', models.TextField(default=b'')),
                ('uuid', django_extensions.db.fields.UUIDField(max_length=36, editable=False, blank=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OperationFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.ForeignKey(to='main.File')),
                ('operation', models.ForeignKey(to='main.Operation')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OperationLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('info', models.TextField(default=b'')),
                ('operation', models.ForeignKey(to='main.Operation')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Poster',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ForeignKey(to='main.Image')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('hostname', models.CharField(max_length=256)),
                ('credentials', models.CharField(max_length=256)),
                ('description', models.TextField(default=b'', blank=True)),
                ('base_dir', models.CharField(default=b'/', max_length=256)),
                ('base_url', models.CharField(default=b'', max_length=256)),
                ('server_type', models.CharField(default=b'sftp', max_length=256)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServerFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('file', models.ForeignKey(to='main.File')),
                ('server', models.ForeignKey(to='main.Server')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=256)),
                ('creator', models.CharField(default=b'', max_length=256, blank=True)),
                ('description', models.TextField(default=b'', null=True, blank=True)),
                ('subject', models.TextField(default=b'', null=True, blank=True)),
                ('license', models.CharField(default=b'', max_length=256, blank=True)),
                ('language', models.CharField(default=b'', max_length=256, blank=True)),
                ('uuid', django_extensions.db.fields.UUIDField(max_length=36, editable=False, blank=True)),
                ('collection', models.ForeignKey(to='main.Collection')),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='poster',
            name='video',
            field=models.ForeignKey(to='main.Video'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='operation',
            name='video',
            field=models.ForeignKey(to='main.Video'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='video',
            field=models.ForeignKey(to='main.Video'),
            preserve_default=True,
        ),
        migrations.AlterOrderWithRespectTo(
            name='image',
            order_with_respect_to='video',
        ),
        migrations.AddField(
            model_name='file',
            name='video',
            field=models.ForeignKey(to='main.Video'),
            preserve_default=True,
        ),
    ]
