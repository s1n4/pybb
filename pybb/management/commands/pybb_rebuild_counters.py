# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from datetime import datetime, timedelta
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Sum
from django.contrib.auth.models import User
from django.conf import settings

from pybb.models import Profile, Topic, Forum

def track_queries(action, cache=[0]):
    from django.db import connection

    if action == 'start':
        cache[0] = len(connection.queries)

    if action == 'stop':
        print '--'
        for item in connection.queries[cache[0]:]:
            print item['time'], item['sql']
        print 'Query count: %d' % (len(connection.queries) - cache[0])


class Command(BaseCommand):
    help = 'Rebuild various pybb counters'

    def handle(self, *args, **kwargs):
    
        self.stdout.write('Calculating profile post count\n')
        for profile in Profile.objects.annotate(_count=Count('user__pybb_posts')):
            if profile.post_count != profile._count:
                profile.post_count = profile._count
                profile.save()

        self.stdout.write('Calculating topic post count\n')
        for topic in Topic.objects.annotate(_count=Count('posts')):
            if topic.post_count != topic._count:
                topic.post_count = topic._count
                self.save()

        self.stdout.write('Calculating forum post count\n')
        for forum in Forum.objects.all():
            post_count = forum.topics.aggregate(value=Sum('post_count'))['value']
            if forum.post_count != post_count:
                forum.post_count = post_count
