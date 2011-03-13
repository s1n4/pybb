# coding: utf-8
import math
import re
from datetime import datetime
from markdown import Markdown
try:
    import pytils
    pytils_enabled = True
except ImportError:
    pytils_enabled = False

from django.shortcuts import get_object_or_404, get_list_or_404
from django.http import HttpResponseRedirect, HttpResponse,\
                        HttpResponseNotFound, Http404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connection
from django.utils.translation import ugettext_lazy as _

from common.decorators import render_to, ajax
from common.orm import load_related

from pybb.markups import mypostmarkup
from pybb.util import quote_text, paginate,\
                        set_language, urlize
from pybb.models import Category, Forum, Topic, Post, Profile, \
                        Attachment, MARKUP_CHOICES
from pybb.forms import  AddPostForm, EditPostForm, EditHeadPostForm, \
                        EditProfileForm, UserSearchForm
from pybb.read_tracking import update_read_tracking


def load_last_post(objects):
    """
    Get list of topics/forums and find the recent post in
    each topic/forum. Also extract author of the post.
    """

    pk_list = [x.last_post_id for x in objects]
    qs = Post.objects.filter(pk__in=pk_list).select_related('user')
    posts = dict((x.pk, x) for x in qs)
    for obj in objects:
        obj.last_post = posts.get(obj.last_post_id)


def index_ctx(request):
    """
    Display list of categories and forums in each category.
    """

    cats = list(Category.objects.all())
    cat_map = dict((x.pk, x) for x in cats)
    for cat in cats:
        cat.cached_forums = []
    forums = list(Forum.objects.all())
    load_last_post(forums)
    for forum in forums:
        cat_map[forum.category_id].cached_forums.append(forum)
    return {'cats': cats,
            }


def show_category_ctx(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    forums = category.forums.all()
    load_last_post(forums)
    category.cached_forums = forums

    return {'category': category,
            }


def show_forum_ctx(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    topics = forum.topics.order_by('-sticky', '-updated').select_related()
    page, paginator = paginate(topics, request, settings.PYBB_FORUM_PAGE_SIZE)
    load_last_post(page.object_list)

    return {'forum': forum,
            'page': page,
            }

def show_topic_ctx(request, topic_id):
    try:
        topic = Topic.objects.select_related().get(pk=topic_id)
    except Topic.DoesNotExist:
        raise Http404()

    topic.views += 1
    topic.save()

    if request.user.is_authenticated():
        update_read_tracking(topic, request.user)
	
    if settings.PYBB_FREEZE_FIRST_POST:
        first_post = topic.head
    else:
        first_post = None

    form = AddPostForm(topic=topic)

    moderator = (request.user.is_superuser or
                 request.user in topic.forum.moderators.all())
    subscribed = (request.user.is_authenticated() and
                  request.user in topic.subscribers.all())

    posts = topic.posts.all()

    # TODO: Here could be gotcha
    # If topic.post_count is broken then strange effect could be possible!
    page, paginator = paginate(posts, request, settings.PYBB_TOPIC_PAGE_SIZE,
                               total_count=topic.post_count)

    users = User.objects.filter(pk__in=
        set(x.user_id for x in page.object_list)).select_related("pybb_profile")
    users = dict((user.pk, user) for user in users)

    for post in page.object_list:
        post.user = users.get(post.user_id)

    load_related(page.object_list, Attachment.objects.all(), 'post')

    return {'topic': topic,
            'last_post': topic.last_post,
            'first_post': first_post,
            'form': form,
            'moderator': moderator,
            'subscribed': subscribed,
            'posts': page.object_list,
            'page': page,
            }


@login_required
def add_post_ctx(request, forum_id, topic_id):
    forum = None
    topic = None

    if forum_id:
        forum = get_object_or_404(Forum, pk=forum_id)
    elif topic_id:
        topic = get_object_or_404(Topic, pk=topic_id)

    if (topic and topic.closed) or request.user.pybb_profile.is_banned():
        return HttpResponseRedirect(topic.get_absolute_url())

    try:
        quote_id = int(request.GET.get('quote_id'))
    except TypeError:
        quote = ''
    else:
        post = get_object_or_404(Post, pk=quote_id)
        quote = quote_text(post.body_text,
                           request.user.pybb_profile.markup,
                           post.user.username)

    ip = request.META.get('REMOTE_ADDR', '')
    form_kwargs = dict(topic=topic, forum=forum, user=request.user,
                       ip=ip, initial={'body': quote})
    if request.method == 'POST':
        form = AddPostForm(request.POST, request.FILES, **form_kwargs)
    else:
        form = AddPostForm(**form_kwargs)

    if form.is_valid():
        post = form.save();
        return HttpResponseRedirect(post.get_absolute_url())

    return {'form': form,
            'topic': topic,
            'forum': forum,
            }


def user_ctx(request, username):
    user = get_object_or_404(User, username=username)
    topic_count = Topic.objects.filter(user=user).count()

    return {'profile': user,
            'topic_count': topic_count,
            }


def user_topics_ctx(request, username):
    user = get_object_or_404(User, username=username)
    topics = Topic.objects.filter(user=user).order_by('-created')
    page, paginator = paginate(topics, request, settings.PYBB_TOPIC_PAGE_SIZE)

    return {'profile': user,
            'page': page,
            }


def show_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count = post.topic.posts.filter(created__lt=post.created).count() + 1
    page = math.ceil(count / float(settings.PYBB_TOPIC_PAGE_SIZE))
    url = '%s?page=%d#post-%d' % (reverse('pybb_topic', args=[post.topic.id]), page, post.id)
    return HttpResponseRedirect(url)


@login_required
def edit_profile_ctx(request):

    form_kwargs = dict(instance=request.user.pybb_profile)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, **form_kwargs)
    else:
        form = EditProfileForm(**form_kwargs)

    if form.is_valid():
        profile = form.save()
        set_language(request, profile.language)
        return HttpResponseRedirect(reverse('pybb_edit_profile'))

    return {'form': form,
            'profile': request.user.pybb_profile,
            }


@login_required
def edit_post_ctx(request, post_id):
    from pybb.templatetags.pybb_tags import pybb_editable_by

    post = get_object_or_404(Post, pk=post_id)

    if not pybb_editable_by(post, request.user) \
    or request.user.pybb_profile.is_banned():
        return HttpResponseRedirect(post.get_absolute_url())

    head_post_id = post.topic.posts.order_by('created')[0].id
    form_kwargs = dict(instance=post, initial={'title': post.topic.name})

    if post.id == head_post_id:
        form_class = EditHeadPostForm
    else:
        form_class = EditPostForm

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, **form_kwargs)
    else:
        form = form_class(**form_kwargs)

    if form.is_valid():
        post = form.save()
        return HttpResponseRedirect(post.get_absolute_url())

    return {'form': form,
            'post': post,
            }


@login_required
def stick_topic(request, topic_id):
    from pybb.templatetags.pybb_tags import pybb_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_moderated_by(topic, request.user):
        if not topic.sticky:
            topic.sticky = True
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def unstick_topic(request, topic_id):
    from pybb.templatetags.pybb_tags import pybb_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_moderated_by(topic, request.user):
        if topic.sticky:
            topic.sticky = False
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())


@login_required
def delete_post_ctx(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    last_post = post.topic.posts.order_by('-created')[0]

    allowed = False
    if request.user.is_superuser or\
        request.user in post.topic.forum.moderators.all() or \
        (post.user == request.user and post == last_post):
        allowed = True

    if not allowed:
        return HttpResponseRedirect(post.get_absolute_url())

    if 'POST' == request.method:
        topic = post.topic
        forum = post.topic.forum
        post.delete()

        try:
            Topic.objects.get(pk=topic.id)
        except Topic.DoesNotExist:
            return HttpResponseRedirect(forum.get_absolute_url())
        else:
            return HttpResponseRedirect(topic.get_absolute_url())
    else:
        return {'post': post,
                }


@login_required
def close_topic(request, topic_id):
    from pybb.templatetags.pybb_tags import pybb_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_moderated_by(topic, request.user):
        if not topic.closed:
            topic.closed = True
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())



@login_required
def open_topic(request, topic_id):
    from pybb.templatetags.pybb_tags import pybb_moderated_by

    topic = get_object_or_404(Topic, pk=topic_id)
    if pybb_moderated_by(topic, request.user):
        if topic.closed:
            topic.closed = False
            topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())



@login_required
def merge_topics_ctx(request):
    from pybb.templatetags.pybb_tags import pybb_moderated_by

    topics_ids = request.GET.getlist('topic')
    topics = get_list_or_404(Topic, pk__in=topics_ids)

    for topic in topics:
        if not pybb_moderated_by(topic, request.user):
            # TODO: show error message: no permitions for edit this topic
            return HttpResponseRedirect(topic.get_absolute_url())

    if len(topics) < 2:
        return {'topics': topics}

    posts = get_list_or_404(Post, topic__in=topics_ids)
    main = int(request.POST.get("main", 0))

    if main and main in (topic.id for topic in topics):
        for topic in topics:
            if topic.id == main:
                main_topic = topic

        for post in posts:
            if post.topic_id != main_topic.id:
                post.topic = main_topic
                post.save()

        main_topic.update_post_count()
        main_topic.forum.update_post_count()

        for topic in topics:
            if topic.id != main:
                forum = topic.forum
                topic.delete()
                forum.update_post_count()

        return HttpResponseRedirect(main_topic.get_absolute_url())

    return {'posts': posts,
            'topics': topics,
            'topic': topics[0],
            }


def users_ctx(request):
    users = User.objects.order_by('username')
    form = UserSearchForm(request.GET)
    users = form.filter(users)

    page, paginator = paginate(users, request, settings.PYBB_USERS_PAGE_SIZE)

    return {'page': page,
            'form': form,
            }


@login_required
def delete_subscription(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    topic.subscribers.remove(request.user)
    if 'from_topic' in request.GET:
        return HttpResponseRedirect(reverse('pybb_topic', args=[topic.id]))
    else:
        return HttpResponseRedirect(reverse('pybb_edit_profile'))


@login_required
def add_subscription(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    topic.subscribers.add(request.user)
    return HttpResponseRedirect(reverse('pybb_topic', args=[topic.id]))


@login_required
def show_attachment(request, hash):
    attachment = get_object_or_404(Attachment, hash=hash)
    file_obj = file(attachment.get_absolute_path())
    # without it mod_python chokes with error that content_type must be string
    return HttpResponse(file_obj, content_type=str(attachment.content_type))


@login_required
@ajax
def post_ajax_preview(request):
    content = request.POST.get('content')
    markup = request.user.pybb_profile.markup

    if not markup in dict(MARKUP_CHOICES).keys():
        return {'error': 'Invalid markup'}

    if not content:
        return {'content': ''}

    if markup == 'bbcode':
        html = mypostmarkup.markup(content, auto_urls=False)
    elif markup == 'markdown':
        instance = Markdown(safe_mode='escape')
        html = unicode(instance.convert(content))

    html = urlize(html)

    return {'content': html,
            }


users = render_to('pybb/users.html')(users_ctx)
merge_topics = render_to('pybb/merge_topics.html')(merge_topics_ctx)
delete_post = render_to('pybb/delete_post.html')(delete_post_ctx)
edit_post = render_to('pybb/edit_post.html')(edit_post_ctx)
edit_profile = render_to('pybb/edit_profile.html')(edit_profile_ctx)
user_topics = render_to('pybb/user_topics.html')(user_topics_ctx)
user = render_to('pybb/user.html')(user_ctx)
add_post = render_to('pybb/add_post.html')(add_post_ctx)
show_topic = render_to('pybb/topic.html')(show_topic_ctx)
show_forum = render_to('pybb/forum.html')(show_forum_ctx)
index = render_to('pybb/index.html')(index_ctx)
show_category = render_to('pybb/category.html')(show_category_ctx)
