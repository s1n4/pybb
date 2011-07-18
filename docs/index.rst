.. PyBB documentation master file, created by
   sphinx-quickstart on Thu Dec 31 19:09:51 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

PyBB - Django Forum Application
===============================

Oficial repository: http://bitbucket.org/lorien/pybb
Author's email: lorien@lorien.name

Installation
============

* Install all dependencies and configure it.
* Edit settings.py

  * Add ``pybb`` to ``INSTALLED_APPS``
  * Add ``from pybb.settings import *`` line
  * Add ``pybb.middleware.PybbMiddleware`` to ``MIDDLEWARE_CLASSES``
* Add ``url('^forum/', include('pybb.urls'))`` to ``urls.py`` file
* Run command ``manage.py migrate`` if you installed `south <http://south.aeracode.org>`_ (recommended) or ``./manage.py syncdb`` (if south is not installed)
* Symlink or copy pybb static files to "%MEDIA_ROOT%/pybb"


Dependencies
============

* django-common
* markdown
* pytils (optional)
* south (optional)
* django-haystack (required for search, optional)


Feature list
============

* Each category, forum, topic and post has its own permanent url
* BBcode and markdown support
* Simple moderator system
* Email subscription on topic replies
* Topic could be sticked or closed
* Plain text urls are converted to active links
* Each user has profile with individual forum related settings
* Unread topics are marked
* i18n
* File attachments to the post
* AJAX preview of new post content
* Search

.. toctree::
    :maxdepth: 1
