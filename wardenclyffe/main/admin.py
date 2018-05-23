from django.contrib import admin

from wardenclyffe.main.models import File, Video


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'video', 'location_type')
    search_fields = ('filename', 'video__title')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'collection', 'creator', )
    search_fields = ('title', 'collection__title')
