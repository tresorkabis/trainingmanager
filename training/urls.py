
from django.urls import path

from training.views.home_views import HomeView


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]