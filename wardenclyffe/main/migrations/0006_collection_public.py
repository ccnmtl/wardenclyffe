# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2016-12-08 10:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_auto_20160616_1000'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='public',
            field=models.BooleanField(default=False),
        ),
    ]
