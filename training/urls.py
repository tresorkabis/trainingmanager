
from django.urls import path

from training.views.formation_views import FormationDetailView, FormationListView
from training.views.home_views import HomeView


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("formations", FormationListView.as_view(), name="formations"),
    path("formations/<int:pk>", FormationDetailView.as_view(), name="formation"),
]