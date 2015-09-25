# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20150604_0617'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='audio',
            field=models.BooleanField(default=False),
        ),
    ]
