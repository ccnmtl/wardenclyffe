from django.contrib import admin

from wardenclyffe.main.models import File, Video, VideoReference


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'video', 'location_type')
    search_fields = ('filename', 'video__title')


class VideoReferenceInline(admin.TabularInline):
    model = VideoReference


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'collection', 'creator', 'created', 'modified')
    search_fields = ('title', 'collection__title')
    inlines = [
        VideoReferenceInline,
    ]
