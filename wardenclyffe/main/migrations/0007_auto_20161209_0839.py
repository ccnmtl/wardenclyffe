# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2016-12-09 08:39
from __future__ import unicode_literals

from django.db import migrations


def update_public(apps, schema_editor):
    Collection = apps.get_model('main', 'Collection')
    for c in Collection.objects.filter(title='h264 Public'):
        c.public = True
        c.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_collection_public'),
    ]

    operations = [
        migrations.RunPython(update_public),
    ]
