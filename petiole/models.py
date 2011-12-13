from django.db import models
from django_extensions.db.models import TimeStampedModel
from picklefield.fields import PickledObjectField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import get_model
import petiole.tasks
from datetime import datetime 

class JobSet(TimeStampedModel):
    label = models.CharField(max_length=256,default="",blank=True)
    status = models.CharField(max_length=256,default="waiting")

    def run(self):
        """ call this once all the Jobs are created and defined and 
        probably ready to go. this puts them on the queue and
        kicks things off """
        self.status = "running"
        for job in self.job_set.all():
            if job.ready_for_queue():
                job.enqueue()
        self.save()

    def job_completed(self,job):
        """ one of our jobs has completed """
        r = JobDependency.objects.filter(pre=job)
        if r.count() > 0:
            # other jobs were waiting on it,
            # so we can potentially enqueue them now
            for jd in r:
                if jd.post.ready_for_queue():
                    petiole.tasks.run_job.delay(jd.post.id)
        else:
            # nothing queued
            # if all the jobs are complete, we're done
            if self.job_set.all().exclude(status="complete").count() == 0:
                self.status = "complete"
                self.save()
        # open question:
        # what to do if the finished job failed
            

class Job(TimeStampedModel):
    label = models.CharField(max_length=256,default="",blank=True)
    status = models.CharField(max_length=256,default="waiting")
    params = PickledObjectField(null=True, default=None)
    jobset = models.ForeignKey(JobSet)

    started = models.DateTimeField(null=True, default=None)
    ended = models.DateTimeField(null=True, default=None)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.label

    def job(self):
        return self.content_object

    def run(self):
        self.status = "running"
        self.started = datetime.now()

        startlog = JobLog.objects.create(job=self,info="starting")
        try:
            (success,message) = self.job().run()
            self.status = success
            if message:
                log = JobLog.objects.create(job=self,info=message)
        except Exception, e:
            # todo: handle retries
            self.status = "failed"
            errorlog = JobLog.objects.create(job=self,
                                             info=str(e))
        self.ended = datetime.now()
        self.save()
        endlog = JobLog.objects.create(job=self,info="completed")
        self.jobset.job_completed(self)

    def ready_for_queue(self):
        if self.status not in ["waiting","blocked"]:
            # it's only ready to run if it's "waiting"
            return False
        # we can only run once all the dependencies are complete
        for jd in JobDependency.objects.filter(post=self):
            if jd.pre.status != "complete":
                self.status = "blocked"
                self.save()
                return False
        else:
            # all dependencies complete
            self.status = "waiting"
            self.save()
            # check job specific preconditions
            if hasattr(self.job(),'ready_for_queue'):
                return self.job().ready_for_queue()
            else:
                return True

    def enqueue(self):
        self.status = "enqueued"
        self.save()
        nqlog = JobLog.objects.create(job=self,info="enqueued")
        petiole.tasks.run_job.delay(self.id)

    def depends_on(self,job):
        """ this job depends on another one """
        jd = JobDependency.objects.create(pre=job,post=self)


class JobDependency(models.Model):
    """ basically, it means that the 'pre'
    job *must* complete before the 'post' job
    will be put on the queue"""
    pre = models.ForeignKey(Job,related_name="pre")
    post = models.ForeignKey(Job,related_name="post")

class JobLog(TimeStampedModel):
    job = models.ForeignKey(Job)
    info = models.TextField(default="",blank=True)

class JobBase(object):
    """ just provide a couple utility methods for the Jobs """
    def job(self):
        return self.jobs.all()[0]

    
