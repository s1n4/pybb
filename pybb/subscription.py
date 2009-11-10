from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils import translation

from pybb.util import absolute_url


TOPIC_SUBSCRIPTION_TEXT_TEMPLATE = lambda: _(u"""New reply from %(username)s to topic that you have subscribed on.
---
%(message)s
---
See topic: %(post_url)s
Unsubscribe %(unsubscribe_url)s""")


def send_mail(rec_list, subject, text, html=None):
    """
    Shortcut for sending email.
    """

    from_email = settings.DEFAULT_FROM_EMAIL

    msg = EmailMultiAlternatives(subject, text, from_email, rec_list)
    if html:
        msg.attach_alternative(html, "text/html")
    if settings.PYBB_EMAIL_DEBUG:
        logging.debug('---begin---')
        logging.debug('To: %s' % rec_list)
        logging.debug('Subject: %s' % subject)
        logging.debug('Body: %s' % text)
        logging.debug('---end---')
    else:
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
                text_content = TOPIC_SUBSCRIPTION_TEXT_TEMPLATE() % {
                    'username': post.user.username,
                    'message': post.body_text,
                    'post_url': absolute_url(post.get_absolute_url()),
                    'unsubscribe_url': absolute_url(reverse('pybb_delete_subscription', args=[post.topic.id])),
                }
                #html_content = html_version(post)
                send_mail([to_email], subject, text_content)

                translation.activate(old_lang)
