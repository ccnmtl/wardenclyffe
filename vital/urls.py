from django.conf.urls.defaults import patterns

urlpatterns = patterns('vital.views',
                       (r'^done/$','done',{},'vital-done'),
                       (r'^received/$','received',{},'vital-received'),
                       (r'^posterdone/$','posterdone',{},'vital-posterdone'),
)
