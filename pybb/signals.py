from datetime import datetime

from django.db.models.signals import post_save
from django.contrib.auth.models import User

from pybb.subscription import notify_topic_subscribers
from pybb.models import Post, Topic, Profile, ReadTracking


def post_saved(instance, created, **kwargs):

    if created:
        notify_topic_subscribers(instance)

        now = datetime.now()

        instance.topic.updated = now
        instance.topic.last_post = instance
        instance.topic.post_count += 1
        instance.topic.save()

        forum = instance.topic.forum
        forum.updated = now
        forum.last_post = instance
        forum.post_count += 1
        forum.save()

        profile = instance.user.pybb_profile
        profile.post_count += 1
        profile.save()


#def topic_saved(instance, **kwargs):
    #pass


def user_saved(instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        ReadTracking.objects.create(user=instance)


post_save.connect(post_saved, sender=Post)
#post_save.connect(topic_saved, sender=Topic)
post_save.connect(user_saved, sender=User)
