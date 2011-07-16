"""
Forum models:

Category, Forum, Topic, Post, Profile, Attachment, ReadTracking

"""
from datetime import datetime
from markdown import Markdown
import os.path
try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1

from django.db import models
from django.db.models import F, Sum
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.template.defaultfilters import urlize

from pybb.markups import mypostmarkup
from pybb.util import unescape

from common.fields import JSONField


TZ_CHOICES = [(float(x[0]), x[1]) for x in (
    (-12, '-12'), (-11, '-11'), (-10, '-10'), (-9.5, '-09.5'), (-9, '-09'),
    (-8.5, '-08.5'), (-8, '-08 PST'), (-7, '-07 MST'), (-6, '-06 CST'),
    (-5, '-05 EST'), (-4, '-04 AST'), (-3.5, '-03.5'), (-3, '-03 ADT'),
    (-2, '-02'), (-1, '-01'), (0, '00 GMT'), (1, '+01 CET'), (2, '+02'),
    (3, '+03'), (3.5, '+03.5'), (4, '+04'), (4.5, '+04.5'), (5, '+05'),
    (5.5, '+05.5'), (6, '+06'), (6.5, '+06.5'), (7, '+07'), (8, '+08'),
    (9, '+09'), (9.5, '+09.5'), (10, '+10'), (10.5, '+10.5'), (11, '+11'),
    (11.5, '+11.5'), (12, '+12'), (13, '+13'), (14, '+14'),
)]

MARKUP_CHOICES = (
    ('bbcode', 'bbcode'),
    ('markdown', 'markdown'),
)

class Category(models.Model):
    name = models.CharField(_('Name'), max_length=80)
    position = models.IntegerField(_('Position'), blank=True, default=0)
    slug = models.CharField(max_length=30, db_index=True, blank=True)

    class Meta:
        ordering = ['position']
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __unicode__(self):
        return self.name

    def forum_count(self):
        return self.forums.all().count()

    def get_absolute_url(self):
        return reverse('pybb_category_details', args=[self.id])

    @property
    def topics(self):
        return Topic.objects.filter(forum__category=self).select_related()

    @property
    def posts(self):
        return Post.objects.filter(topic__forum__category=self).select_related()


class Forum(models.Model):
    category = models.ForeignKey(Category, related_name='forums', verbose_name=_('Category'))
    name = models.CharField(_('Name'), max_length=80)
    position = models.IntegerField(_('Position'), blank=True, default=0)
    description = models.TextField(_('Description'), blank=True)
    moderators = models.ManyToManyField(User, blank=True, null=True, verbose_name=_('Moderators'))
    updated = models.DateTimeField(_('Updated'), blank=True, null=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)
    topic_count = models.IntegerField(_('Topic count'), blank=True, default=0)
    last_post = models.ForeignKey("Post", related_name='last_post_in_forum', verbose_name=_(u"last post"), blank=True, null=True)
    slug = models.CharField(max_length=30, db_index=True, blank=True)

    class Meta:
        ordering = ['position']
        verbose_name = _('Forum')
        verbose_name_plural = _('Forums')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('pybb_forum_details', args=[self.id])

    @property
    def posts(self):
        return Post.objects.filter(topic__forum=self).select_related()

    def get_last_post(self):
        try:
            return self.posts.order_by('-created').select_related()[0]
        except IndexError:
            return None


class Topic(models.Model):
    forum = models.ForeignKey(Forum, related_name='topics', verbose_name=_('Forum'))
    name = models.CharField(_('Subject'), max_length=255)
    created = models.DateTimeField(_('Created'), null=True)
    updated = models.DateTimeField(_('Updated'), null=True)
    user = models.ForeignKey(User, verbose_name=_('User'), related_name='pybb_topics')
    views = models.IntegerField(_('Views count'), blank=True, default=0)
    sticky = models.BooleanField(_('Sticky'), blank=True, default=False)
    closed = models.BooleanField(_('Closed'), blank=True, default=False)
    subscribers = models.ManyToManyField(User, related_name='subscriptions', verbose_name=_('Subscribers'), blank=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)
    last_post = models.ForeignKey("Post", related_name="last_post_in_topic", verbose_name=_(u"last post"), blank=True, null=True)

    class Meta:
        ordering = ['-created']
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')

    def __unicode__(self):
        return self.name

    @property
    def head(self):
        if not hasattr(self, "_head"):
            self._head = self.posts.all().order_by('created')[0]
        return self._head

    def get_last_post(self):
        return self.posts.order_by('-created').select_related()[0]

    def get_absolute_url(self):
        return reverse('pybb_topic_details', args=[self.id])

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.created = datetime.now()
        super(Topic, self).save(*args, **kwargs)


class RenderableItem(models.Model):
    """
    Base class for models that has markup, body, body_text and body_html fields.
    """

    class Meta:
        abstract = True

    def render(self):
        if self.markup == 'bbcode':
            self.body_html = mypostmarkup.markup(self.body, auto_urls=False)
        elif self.markup == 'markdown':
            instance = Markdown(safe_mode='escape')
            self.body_html = unicode(instance.convert(self.body))
        else:
            raise Exception('Invalid markup property: %s' % self.markup)

        # Remove tags which was generated with the markup processor
        text = strip_tags(self.body_html)

        # Unescape entities which was generated with the markup processor
        self.body_text = unescape(text)

        self.body_html = urlize(self.body_html)


class Post(RenderableItem):
    topic = models.ForeignKey(Topic, related_name='posts', verbose_name=_('Topic'))
    user = models.ForeignKey(User, related_name='pybb_posts', verbose_name=_('User'))
    created = models.DateTimeField(_('Created'), blank=True)
    updated = models.DateTimeField(_('Updated'), blank=True, null=True)
    markup = models.CharField(_('Markup'), max_length=15, default=settings.PYBB_DEFAULT_MARKUP, choices=MARKUP_CHOICES)
    body = models.TextField(_('Message'))
    body_html = models.TextField(_('HTML version'))
    body_text = models.TextField(_('Text version'))
    user_ip = models.IPAddressField(_('User IP'), blank=True, default='0.0.0.0')

    class Meta:
        ordering = ['created']
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def summary(self):
        LIMIT = 50
        tail = len(self.body) > LIMIT and '...' or ''
        return self.body[:LIMIT] + tail

    __unicode__ = summary

    def save(self, *args, **kwargs):
        now = datetime.now()
        if self.created is None:
            self.created = now
        self.render()

        super(Post, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('pybb_post_details', args=[self.id])

    def delete(self, *args, **kwargs):
        # Change `last_post` of the forum which the deleted post belongs to
        # This needs to avoid whole forum deletion due to ForeignKey dependency
        forum = self.topic.forum
        if forum.last_post == self:
            try:
                post = Post.objects.filter(topic__forum=forum).exclude(pk=self.pk).order_by('-created')[0]
            except IndexError:
                post = None
            forum.last_post = post
            forum.save()

        # Change `last_post` of the topic which the deleted post belongs to
        # This needs to avaid whole topic deletion due to ForeignKey dependency
        if self.topic.last_post == self:
            try:
                post = Post.objects.filter(topic=self.topic).exclude(pk=self.pk).order_by('-created')[0]
            except IndexError:
                post = None
            self.topic.last_post = post
            self.topic.save()
        
            # If there is no more posts in topic then
            # delete the topic
            if self.topic.last_post is None:
                self.topic.delete()

        super(Post, self).delete(*args, **kwargs)

        #if self.topic.pk:
            ## If topic was not deleted
            #self.topic.update_post_count()
        #self.topic.forum.update_post_count()


BAN_STATUS = (
(0, _('No')),
(1, _('Caution')),
(2, _('Ban')))


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='pybb_profile', verbose_name=_('User'))
    signature = models.TextField(_('Signature'), blank=True, max_length=settings.PYBB_SIGNATURE_MAX_LENGTH)
    signature_html = models.TextField(_('Signature HTML Version'), blank=True, max_length=settings.PYBB_SIGNATURE_MAX_LENGTH + 30)
    time_zone = models.FloatField(_('Time zone'), choices=TZ_CHOICES, default=float(settings.PYBB_DEFAULT_TIME_ZONE))
    language = models.CharField(_('Language'), max_length=10, blank=True,
                                choices=settings.LANGUAGES)
    show_signatures = models.BooleanField(_('Show signatures'), blank=True, default=True)
    markup = models.CharField(_('Default markup'), max_length=15, default=settings.PYBB_DEFAULT_MARKUP, choices=MARKUP_CHOICES)
    ban_status = models.SmallIntegerField(_('Ban status'), default=0, choices=BAN_STATUS)
    ban_till = models.DateTimeField(_('Ban till'), blank=True, null=True, default=None)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    def save(self, *args, **kwargs):
        self.signature_html = mypostmarkup.markup(self.signature, auto_urls=False)
        super(Profile, self).save(*args, **kwargs)

    def is_banned(self):
        if self.ban_status == 2:
            if self.ban_till is None or self.ban_till < datetime.now():
                self.ban_status = 0
                self.ban_till = None
                self.save()
                return False
            return True
        return False

    def get_absolute_url(self):
        return reverse('pybb_user_details', args=[self.user.username])


class Attachment(models.Model):
    post = models.ForeignKey(Post, verbose_name=_('Post'), related_name='attachments')
    size = models.IntegerField(_('Size'))
    content_type = models.CharField(_('Content type'), max_length=255)
    path = models.CharField(_('Path'), max_length=255)
    name = models.TextField(_('Name'))
    hash = models.CharField(_('Hash'), max_length=40, blank=True, db_index=True)

    def save(self, *args, **kwargs):
        super(Attachment, self).save(*args, **kwargs)
        if not self.hash:
            self.hash = sha1(str(self.id) + settings.SECRET_KEY).hexdigest()
        super(Attachment, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('pybb_attachment_details', args=[self.hash])

    def size_display(self):
        size = self.size
        if size < 1024:
            return '%db' % size
        elif size < 1024 * 1024:
            return '%dKb' % int(size / 1024)
        else:
            return '%.2fMb' % (size / float(1024 * 1024))

    def get_absolute_path(self):
        return os.path.join(settings.MEDIA_ROOT, settings.PYBB_ATTACHMENT_UPLOAD_TO,
                            self.path)

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')


class ReadTracking(models.Model):
    """
    Model for tracking read/unread posts.

    `topics` field stores JSON serialized mapping of
    `topic pk` --> `topic last post pk`
    """

    user = models.OneToOneField(User)
    topics = JSONField(null=True, blank=True)
    last_read = models.DateTimeField(null=True)

    class Meta:
        verbose_name = _('Read tracking')
        verbose_name_plural = _('Read tracking')

    def __unicode__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if not self.pk:
            self.last_read = datetime.now()
        super(ReadTracking, self).save(*args, **kwargs)


import pybb.signals
