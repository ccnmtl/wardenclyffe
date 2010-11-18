from django.db import models
from django_extensions.db.fields import UUIDField
from django_extensions.db.models import TimeStampedModel
from django.contrib.auth.models import User
from angeldust import PCP
from django.conf import settings

class Video(TimeStampedModel):
    title = models.CharField(max_length=256)
    description = models.TextField(default="",blank=True,null=True)
    filename = models.CharField(max_length=256)
    cap = models.CharField(max_length=256)
    uuid = UUIDField()
    owner = models.ForeignKey(User)

    def pcp_filename(self):
        return self.uuid + ".mp4"

    def submit_to_podcast_producer(self,fileobj):
        pcp = PCP(settings.PCP_BASE_URL,
                  settings.PCP_USERNAME,
                  settings.PCP_PASSWORD)
        filename = self.pcp_filename()
        pcp.upload_file(fileobj,filename,settings.PCP_WORKFLOW,self.title,self.description)
