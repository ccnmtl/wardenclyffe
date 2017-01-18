from django.contrib import admin
from .models import Credentials


class CredentialsAdmin(admin.ModelAdmin):
    pass


admin.site.register(Credentials, CredentialsAdmin)
