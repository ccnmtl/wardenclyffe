from django.contrib import admin
from wardenclyffe.youtube.models import Credentials


class CredentialsAdmin(admin.ModelAdmin):
    pass


admin.site.register(Credentials, CredentialsAdmin)
