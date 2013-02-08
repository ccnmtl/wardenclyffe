from celery.decorators import task
import wardenclyffe.petiole.models


@task
def run_jobset(jobset_id):
    js = wardenclyffe.petiole.models.JobSet.objects.get(id=jobset_id)
    js.run()


@task
def run_job(job_id):
    j = wardenclyffe.petiole.models.Job.objects.get(id=job_id)
    j.run()
