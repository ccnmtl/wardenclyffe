# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-30 05:01
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_auto_20170630_0458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4),
        ),
        migrations.AlterField(
            model_name='operation',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4),
        ),
        migrations.AlterField(
            model_name='video',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4),
        ),
    ]
