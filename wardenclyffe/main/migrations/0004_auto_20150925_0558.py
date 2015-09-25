# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_collection_audio'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collectionworkflow',
            name='collection',
        ),
        migrations.DeleteModel(
            name='CollectionWorkflow',
        ),
    ]
