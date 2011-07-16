from datetime import datetime
import os.path
import random
import traceback
try:
	from hashlib import md5
except ImportError:
	from md5 import md5
import urllib

from django.utils.translation import check_for_language
from django import forms
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.conf import settings
from django.contrib.sites.models import Site


def quote_text(text, markup, username=""):
    """
    Quote message using selected markup.
    """

    if markup == 'markdown':
        return '>'+text.replace('\n','\n>').replace('\r','\n>') + '\n'

    elif markup == 'bbcode':
        if username is not "":
            username = '="%s"' % username
        return '[quote%s]%s[/quote]\n' % (username, text)

    else:
        return text


def set_language(request, language):
    """
    Change the language of session of authenticated user.
    """

    if language and check_for_language(language):
        if hasattr(request, 'session'):
            request.session['django_language'] = language
        else:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)


def unescape(text):
    """
    Do reverse escaping.
    """

    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', '\'')
    return text


def gravatar_url(email):
    """
    Return gravatar URL for given email.

    Details: http://gravatar.com/site/implement/url
    """

    hash = md5(email).hexdigest()
    size = max(settings.PYBB_AVATAR_WIDTH, settings.PYBB_AVATAR_HEIGHT)
    url = settings.PYBB_DEFAULT_AVATAR_URL
    hostname = Site.objects.get_current().domain
    if not url.startswith('http://'):
        url = 'http://%s%s%s' % (hostname,
                                 settings.STATIC_URL,
                                 settings.PYBB_DEFAULT_AVATAR_URL)
    default = urllib.quote(url)
    url = 'http://www.gravatar.com/avatar/%s?s=%d&d=%s' % (hash, size, default)
    return url
