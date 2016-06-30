# flake8: noqa
# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-30 08:49
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0005_auto_20160616_1000'),
    ]

    operations = [
        migrations.CreateModel(
            name='DropBucket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('description', models.TextField(blank=True, default='')),
                ('bucket_id', models.TextField()),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Collection')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
