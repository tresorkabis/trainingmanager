
from django.urls import path

from training.views.formation_views import FormationView
from training.views.home_views import HomeView


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("formations", FormationView.as_view(), name="formations"),
]