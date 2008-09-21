from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from pybb.util import render_to, build_form
from pybb.models import Category, Forum, Topic, Post
from pybb.forms import AddPostForm

@render_to('pybb/index.html')
def index(request):
    cats = Category.objects.all()
    quick = {'posts': Post.objects.count(),
             'topics': Topic.objects.count(),
             'users': User.objects.count(),
             'last_created': Topic.objects.all()[:10],
             'last_updated': Topic.objects.order_by('-updated')[:10],
             }
    return {'cats': cats,
            'quick': quick,
            }


@render_to('pybb/category.html')
def show_category(request, category_id):
    category = Category.objects.get(pk=category_id)
    quick = {'posts': category.posts.count(),
             'topics': category.topics.count(),
             'last_created': category.topics[:10],
             'last_updated': category.topics.order_by('-updated')[:10],
             }
    return {'category': category,
            'quick': quick,
            }


@render_to('pybb/forum.html')
def show_forum(request, forum_id):
    forum = Forum.objects.get(pk=forum_id)
    quick = {'posts': forum.posts.count(),
             'topics': forum.topics.count(),
             'last_created': forum.topics.all()[:10],
             'last_updated': forum.topics.order_by('-updated')[:10],
             }
    return {'forum': forum,
            'quick': quick,
            }

    
@render_to('pybb/topic.html')
def show_topic(request, topic_id):
    topic = Topic.objects.get(pk=topic_id)
    topic.views += 1
    topic.save()
    form = AddPostForm(topic=topic)
    return {'topic': topic,
            'form': form,
            }


@login_required
@render_to('pybb/add_post.html')
def add_post(request, forum_id, topic_id):
    forum = None
    topic = None

    if forum_id:
        forum = get_object_or_404(Forum, pk=forum_id)
    elif topic_id:
        topic = get_object_or_404(Topic, pk=topic_id)

    form = build_form(AddPostForm, request, topic=topic, forum=forum, user=request.user)

    if form.is_valid():
        post = form.save();
        return HttpResponseRedirect(post.topic.get_absolute_url())

    return {'form': form,
            'topic': topic,
            'forum': forum,
            }


@render_to('pybb/user.html')
def user(request, username):
    user = get_object_or_404(User, username=username)
    return {'profile': user,
            }
