from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib import admin
from django.urls import path, include, re_path

from training.views.home_views import HomeView
from users.views.auth_views import LoginPageView, LogoutPageView
#from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('select2/', include('django_select2.urls')), # Ajout des URLs de django-select2
    path("", HomeView.as_view(), name="home"),

    path("intern/", include('intern.urls')),
    path("progress/", include('progress.urls')),
    path("training/", include('training.urls')),
    path("users/", include('users.urls')),

    path("login/", LoginPageView.as_view(), name="login"),
    path("logout/", LogoutPageView.as_view(), name="logout"),

    
]

#urlpatterns += i18n_patterns(path("admin/", admin.site.urls))
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# User-uploaded photos and documents are stored on the persistent Docker media
# volume. Django's static() helper only adds media routes when DEBUG=True, while
# the production container runs with DEBUG=False.
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
