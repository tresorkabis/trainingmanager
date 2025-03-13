
from django.urls import path

from training.views.formation_views import FormationListView
from training.views.filiere_views import FiliereListView
from training.views.home_views import HomeView


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("formations", FormationListView.as_view(), name="formations"),
    path("filieres", FiliereListView.as_view(), name="filieres")
]