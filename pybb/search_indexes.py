import haystack
from haystack import indexes

from pybb.models import Post

class PostIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True)
    user = indexes.CharField(model_attr='user__username')
    subject = indexes.CharField(model_attr='topic__name')

    def get_updated_field(self):
        return 'updated'

    def prepare_text(self, obj):
        return obj.body_text


haystack.site.register(Post, PostIndex)
