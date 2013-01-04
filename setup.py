# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
import os
from setuptools import setup, find_packages

setup(
    name = 'pybb',
    version = '0.1.10',
    description = 'Django forum application',
    long_description = open('README.rst').read(),
    author = 'Grigoriy Petukhov',
    author_email = 'lorien@lorien.name',
    url = 'http://pybb.org',

    packages = find_packages(),
    include_package_data = True,
    install_requires = ['django-common', 'markdown', 'pytils', 'south'],

    license = "BSD",
    keywords = "django application forum board",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Message Boards',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
