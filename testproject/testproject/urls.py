from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http.response import HttpResponse
from django.views.static import serve as static_serve
from django_nyt.urls import get_pattern as get_notify_pattern
from wiki.compat import include, url
from wiki.urls import get_pattern as get_wiki_pattern

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^robots.txt', lambda _: HttpResponse('User-agent: *\nDisallow: /')),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
    ]


urlpatterns += [
    url(r'^notify/', get_notify_pattern()),
    url(r'', get_wiki_pattern())
]

handler500 = 'testproject.views.server_error'
handler404 = 'testproject.views.page_not_found'
