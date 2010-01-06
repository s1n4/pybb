from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils import translation
from django.contrib.sites.models import Site


TOPIC_SUBSCRIPTION_TEXT_TEMPLATE = lambda: _(u"""New reply from %(username)s to topic that you have subscribed on.
---
%(message)s
---
See topic: %(post_url)s
Unsubscribe %(unsubscribe_url)s""")


def send_mail(recipients, subject, text, html=None):
    """
    Shortcut for sending email.
    """

    msg = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL,
                                 recipients)
    if html:
        msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=True)


def notify_topic_subscribers(post):
    from pybb.models import Post

    if settings.PYBB_DISABLE_NOTIFICATION:
        return

    topic = post.topic
    if post != topic.head:
        for user in topic.subscribers.all():
            if user != post.user:
                old_lang = translation.get_language()
                lang = user.pybb_profile.language or 'en'
                translation.activate(lang)

                subject = u'RE: %s' % topic.name
                to_email = user.email
                hostname = Sites.objects.get_current().domain
                delete_url = reverse('pybb_delete_subscription', args=[post.topic.id])
                text_content = TOPIC_SUBSCRIPTION_TEXT_TEMPLATE() % {
                    'username': post.user.username,
                    'message': post.body_text,
                    'post_url': 'http://%s%s' % (hostname, post.get_absolute_url()),
                    'unsubscribe_url': 'http://%s%s' % (hostname, delete_url),
                }
                #html_content = html_version(post)
                send_mail([to_email], subject, text_content)

                translation.activate(old_lang)
