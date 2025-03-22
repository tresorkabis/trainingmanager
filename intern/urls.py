
from django.urls import path

from intern.views.categorie_views import CategorieListView
from intern.views.stagiaire_views import StagiaireListView
from intern.views.categorie_views import CategorieDetailView, CategorieListView
from intern.views.categorie_views import CategorieCreateView, CategorieListView
from intern.views.stagiaire_views import StagiaireDetailView, StagiaireListView
from intern.views.stagiaire_views import StagiaireCreateView, StagiaireListView


urlpatterns = [
    path("categories", CategorieListView.as_view(), name="categories"),
    path("categories/create", CategorieCreateView.as_view(), name="categories_create"),
    path("stagiaires", StagiaireListView.as_view(), name="stagiaires"),
    path("stagiaires/create", StagiaireCreateView.as_view(), name="stagiaire_create"),

    path("categories/<int:pk>", CategorieDetailView.as_view(), name="categorie"),
    path("stagiaires/<int:pk>", StagiaireDetailView.as_view(), name="stagiaire"),
]