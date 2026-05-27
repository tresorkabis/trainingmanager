from django.urls import path

from intern.views.categorie_views import CategorieListView
from intern.views.stagiaire_views import StagiaireListView, StagiaireCreateUpdateView, StagiaireDetailView, StagiaireDeleteView # Importation des vues manquantes
from intern.views.categorie_views import CategorieDetailView, CategorieListView
from intern.views.categorie_views import CategorieCreateView, CategorieListView


urlpatterns = [
    path("categories", CategorieListView.as_view(), name="categories"),
    path("categories/create", CategorieCreateView.as_view(), name="categories_create"),
    path("stagiaires", StagiaireListView.as_view(), name="stagiaires"),
    path("stagiaires/create", StagiaireCreateUpdateView.as_view(), name="stagiaire_create"), # Utilise StagiaireCreateUpdateView
    path("stagiaires/<int:pk>/update", StagiaireCreateUpdateView.as_view(), name="stagiaire_update"), # Utilise StagiaireCreateUpdateView
    path("stagiaires/<int:pk>/delete", StagiaireDeleteView.as_view(), name="stagiaire_delete"), # Nouvelle URL

    path("categories/<int:pk>", CategorieDetailView.as_view(), name="categorie"),
    path("stagiaires/<int:pk>", StagiaireDetailView.as_view(), name="stagiaire"),
]