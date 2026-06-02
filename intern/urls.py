from django.urls import path

from intern.views.categorie_views import CategorieListView, CategorieDetailView, CategorieCreateUpdateView, CategorieDeleteView # Importation des nouvelles vues
from intern.views.stagiaire_views import StagiaireListView, StagiaireCreateUpdateView, StagiaireDetailView, StagiaireDeleteView


urlpatterns = [
    path("categories", CategorieListView.as_view(), name="categories"),
    path("categories/create", CategorieCreateUpdateView.as_view(), name="categorie_create"), # Changé CategorieCreateView à CategorieCreateUpdateView
    path("categories/<int:pk>", CategorieDetailView.as_view(), name="categorie"),
    path("categories/<int:pk>/update", CategorieCreateUpdateView.as_view(), name="categorie_update"), # Nouvelle URL pour la modification
    path("categories/<int:pk>/delete", CategorieDeleteView.as_view(), name="categorie_delete"), # Nouvelle URL pour la suppression

    path("stagiaires", StagiaireListView.as_view(), name="stagiaires"),
    path("stagiaires/create", StagiaireCreateUpdateView.as_view(), name="stagiaire_create"),
    path("stagiaires/<int:pk>/update", StagiaireCreateUpdateView.as_view(), name="stagiaire_update"),
    path("stagiaires/<int:pk>/delete", StagiaireDeleteView.as_view(), name="stagiaire_delete"),
    path("stagiaires/<int:pk>", StagiaireDetailView.as_view(), name="stagiaire"),
    path("stagiaires/print", stagiaire_cards_print, name="stagiaires_print"),
]