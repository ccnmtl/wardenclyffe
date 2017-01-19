from django.db import models

from oauth2client.contrib.django_util.models import CredentialsField


class Credentials(models.Model):
    email = models.CharField(max_length=256, primary_key=True)
    credential = CredentialsField()
