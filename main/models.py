from django.db import models
from django_extensions.db.fields import UUIDField
from django_extensions.db.models import TimeStampedModel
from django.contrib.auth.models import User
from sorl.thumbnail.fields import ImageWithThumbnailsField
TAHOE_BASE = "http://tahoe.ccnmtl.columbia.edu/"

class Series(TimeStampedModel):
    title = models.CharField(max_length=256)
    creator = models.CharField(max_length=256,default="",blank=True)
    contributor = models.CharField(max_length=256,default="",blank=True)
    language = models.CharField(max_length=256,default="",blank=True)
    description = models.TextField(default="",blank=True,null=True)
    subject = models.TextField(default="",blank=True,null=True)    
    license = models.CharField(max_length=256,default="",blank=True)    

    uuid = UUIDField()

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return "/series/%d/" % self.id

class Video(TimeStampedModel):
    series = models.ForeignKey(Series)
    title = models.CharField(max_length=256)
    creator = models.CharField(max_length=256,default="",blank=True)
    description = models.TextField(default="",blank=True,null=True)
    subject = models.TextField(default="",blank=True,null=True)    
    license = models.CharField(max_length=256,default="",blank=True)    
    language = models.CharField(max_length=256,default="",blank=True)

    uuid = UUIDField()

    def tahoe_file(self):
        r = self.file_set.filter(location_type='tahoe')
        if r.count():
            return r[0]
        else:
            return None

    def cap(self):
        t = self.tahoe_file()
        if t:
            return t.cap
        else:
            return None

    def tahoe_download_url(self):
        t = self.tahoe_file()
        if t:
            return t.tahoe_download_url()
        else:
            return ""

    def filename(self):
        r = self.file_set.filter().exclude(filename="")
        if r.count():
            return r[0].filename
        else:
            return "none"

    def get_absolute_url(self):
        return "/video/%d/" % self.id

            

class File(TimeStampedModel):
    video = models.ForeignKey(Video)
    label = models.CharField(max_length=256,blank=True,null=True,default="")
    url = models.URLField(default="",blank=True,null=True)
    cap = models.CharField(max_length=256,default="",blank=True,null=True)
    filename = models.CharField(max_length=256)
    location_type = models.CharField(max_length=256,default="tahoe",
                                     choices=(('tahoe','tahoe'),('pcp','pcp'),('cuit','cuit'),
                                              ('none','none')))

    def tahoe_download_url(self):
        if self.location_type == "tahoe":
            return TAHOE_BASE + "file/" + self.cap + "/@@named=" + self.filename
        else:
            return None

    def pcp_filename(self):
        return self.uuid + ".mp4"

    def set_metadata(self,field,value):
        r = Metadata.objects.filter(file=self,field=field)
        if r.count():
            # update
            m = r[0]
            m.value = value
            m.save()
        else:
            # add
            m = Metadata.objects.create(file=self,field=field,value=value)

    def get_absolute_url(self):
        return "/file/%d/" % self.id

class Metadata(models.Model):
    """ metadata that we've extracted. more about 
    encoding/file format kinds of stuff than dublin-core"""
    file = models.ForeignKey(File)
    field = models.CharField(max_length=256,default="")
    value = models.TextField(default="",blank=True,null=True)

    class Meta:
        ordering = ('field',)


class Operation(TimeStampedModel):
    video = models.ForeignKey(Video)
    action = models.CharField(max_length=256,default="")
    owner = models.ForeignKey(User)
    status = models.CharField(max_length=256,default="in progress")
    params = models.TextField(default="")
    uuid = UUIDField()
    
class OperationFile(models.Model):
    operation = models.ForeignKey(Operation)
    file = models.ForeignKey(File)

class OperationLog(TimeStampedModel):
    operation = models.ForeignKey(Operation)
    info = models.TextField(default="")

class Image(TimeStampedModel):
    video = models.ForeignKey(Video)

    image = ImageWithThumbnailsField(upload_to="images",thumbnail={'size' : (100,100)})

    class Meta:
        order_with_respect_to = "video"

