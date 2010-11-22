from django.db import models
from django_extensions.db.fields import UUIDField
from django_extensions.db.models import TimeStampedModel
from django.contrib.auth.models import User
TAHOE_BASE = "http://tahoe.ccnmtl.columbia.edu/"
class Video(TimeStampedModel):
    title = models.CharField(max_length=256)
    description = models.TextField(default="",blank=True,null=True)
    filename = models.CharField(max_length=256)
    cap = models.CharField(max_length=256)
    uuid = UUIDField()
    owner = models.ForeignKey(User)

    def pcp_filename(self):
        return self.uuid + ".mp4"

    def tahoe_download_url(self):
        return TAHOE_BASE + "file/" + self.cap + "/@@named=" + self.filename

