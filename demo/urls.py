from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic.simple import redirect_to
import django.views.static

admin.autodiscover()

urlpatterns = patterns('',
    url('^forum/', include('pybb.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
        django.views.static.serve, {'document_root': settings.MEDIA_ROOT}),
    url(r'^account/', include('account.urls')),
    url(r'^$', redirect_to, {'url': '/forum'}),
)
