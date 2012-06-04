from celery.decorators import task
import petiole.models


@task
def run_jobset(jobset_id):
    js = petiole.models.JobSet.objects.get(id=jobset_id)
    js.run()


@task
def run_job(job_id):
    j = petiole.models.Job.objects.get(id=job_id)
    j.run()
