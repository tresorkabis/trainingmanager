from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from training.views.home_views import HomeView
from users.views.auth_views import LoginPageView, LogoutPageView
#from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
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
