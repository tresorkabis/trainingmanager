
from django.urls import path

from intern.views.categorie_views import CategorieListView
from intern.views.stagiaire_views import StagiaireListView
from intern.views.categorie_views import CategorieDetailView, CategorieListView
from intern.views.stagiaire_views import StagiaireDetailView, StagiaireListView


urlpatterns = [
    path("categories", CategorieListView.as_view(), name="categories"),
    path("stagiaires", StagiaireListView.as_view(), name="stagiaires"),
    path("categories/<int:pk>", CategorieDetailView.as_view(), name="categorie"),
    path("stagiaires/<int:pk>", StagiaireDetailView.as_view(), name="stagiaire"),
]