from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from wardenclyffe.main.models import Collection


@python_2_unicode_compatible
class DropBucket(models.Model):
    name = models.TextField()
    description = models.TextField(blank=True, default="")
    bucket_id = models.TextField()
    user = models.ForeignKey(User)
    collection = models.ForeignKey(Collection)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
