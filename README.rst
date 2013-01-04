============================
PyBB - Python Bulletin Board
============================

Simple discussion board for your django powered website.

Questions? lorien@lorien.name

Installation
============

1. Install recent version of pybb from bitbucket repository
2. Update settings.INSTALLED_APPS::

    'pybb',

3. Update urls.py::

    url(r'^forum/', include('pybb.urls', namespace='pybb')),

4. Put templates/pybb from pybb repository to your templates directory.
   Use these templates as starting point and change them according to
   design of your site. Default templates use `django-widget-tweaks <https://bitbucket.org/kmike/django-widget-tweaks>`_ applications.

5. Run command::

   ./manage.py migrate pybb
