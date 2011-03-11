from django.contrib.syndication.views import Feed
from wardenclyffe.main.models import Series
from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import Atom1Feed

class SeriesFeed(Feed):
    description_template = 'feeds/series_description.html'
    feed_type = Atom1Feed

    def get_object(self, request, id):
        return get_object_or_404(Series, pk=id)

    def title(self, obj):
        return "Wardenclyffe: videos for series %s" % obj.title

    def link(self, obj):
        return obj.get_absolute_url()

    def feed_guid(self,obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return obj.description

    def author_name(self, obj):
        return obj.creator

    def feed_copyright(self,obj):
        return obj.license

    def items(self, obj):
        return obj.video_set.all().order_by('-created')[:30]

    def item_enclosure_url(self, item):
        return item.enclosure_url()

    def item_link(self,item):
        return item.get_absolute_url()

    def item_author_name(self,item):
        return item.creator

    def item_copyright(self,item):
        return item.license

    def item_title(self,item):
        return item.title
