from django.conf.urls.defaults import patterns

urlpatterns = patterns('vital.views',
                       (r'^drop/$', 'drop_form', {}, 'vital-drop-form'),
                       (r'^drop/post/$', 'drop', {}, 'vital-drop'),
                       (r'^submit/(?P<id>\d+)/$', 'submit', {},
                        'vital-submit'),
)
