from django.contrib.auth.models import User
from django.db import models

from wardenclyffe.main.models import Collection


class DropBucket(models.Model):
    name = models.TextField()
    description = models.TextField(blank=True, default=u"")
    bucket_id = models.TextField()
    user = models.ForeignKey(User)
    collection = models.ForeignKey(Collection)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name
