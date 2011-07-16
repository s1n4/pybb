#!.env/bin/python
# -*- coding: utf-8 -*-
"""
Generate sample data for pybb demo
"""

import sys
from datetime import date, datetime, time, timedelta
from random import randint, choice
from common.system import setup_django
from common.sample import random_string, random_text
setup_django(__file__)

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import connection

from pybb.models import Category, Topic, Post, Forum, Topic, Post

def track_queries(action, cache=[0]):
    from django.db import connection

    if action == 'start':
        cache[0] = len(connection.queries)

    if action == 'stop':
        print '--'
        for item in connection.queries[cache[0]:]:
            print item['time'], item['sql']
        print 'Query count: %d' % (len(connection.queries) - cache[0])


def main():
    Site.objects.filter(pk=1).update(domain='localhost:8000', name='localhost:8000')
    return 

    # Delete old data
    User.objects.all().delete()
    Category.objects.all().delete()

    print 'Creating superuser'
    admin = User.objects.create_user('foob', 'foob@foob.com', 'foob') 
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()

    print 'Creating users'
    users = []
    for x in xrange(2):
        users.append(User.objects.create_user('noob%d' % x, 'noob%d@noob.com' %x, 'noob'))

    for x in xrange(2):
        cat = Category.objects.create(name=random_text(3))
        print 'Category %s' % cat
        for x in xrange(2):
            forum = Forum.objects.create(category=cat, name=random_text(3))
            print 'Forum %s' % forum
            for x in xrange(2):
                topic = Topic.objects.create(forum=forum, name=random_text(3),
                                             user=choice(users))
                print 'Topic %s' % topic
                for x in xrange(20):
                    post = Post.objects.create(
                        topic=topic, user=topic.user if not x else choice(users),
                        markup='markdown', body=random_text(30))


if __name__ == '__main__':
    main()
