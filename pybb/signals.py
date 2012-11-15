from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F

from pybb.models import Forum, Topic, Post

@receiver(post_save, sender=Topic)
def topic_post_save(instance, **kwargs):
    topic = instance
    Forum.objects.filter(pk=topic.forum_id)\
         .update(topic_count=F('topic_count') + 1)


@receiver(post_save, sender=Post)
def post_post_save(instance, **kwargs):
    post = instance
    topic = post.topic
    Topic.objects.filter(pk=post.topic_id)\
         .update(post_count=F('post_count') + 1)
    Forum.objects.filter(pk=topic.forum_id)\
         .update(post_count=F('post_count') + 1)
