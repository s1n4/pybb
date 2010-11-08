from django.db.models.signals import post_save
from django.contrib.auth.models import User

from pybb.subscription import notify_topic_subscribers
from pybb.models import Post, Topic, Profile, ReadTracking


def post_saved(instance, **kwargs):
    notify_topic_subscribers(instance)

    profile = instance.user.pybb_profile
    profile.post_count = instance.user.pybb_posts.count()
    profile.save()


def topic_saved(instance, **kwargs):
    forum = instance.forum
    forum.topic_count = forum.topics.count()
    forum.save()


def user_saved(instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        ReadTracking.objects.create(user=instance)


def setup_signals():
    post_save.connect(post_saved, sender=Post)
    post_save.connect(topic_saved, sender=Topic)
    post_save.connect(user_saved, sender=User)
