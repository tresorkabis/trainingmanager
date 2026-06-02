from django.urls import path
from training.views.home_views import HomeView
from training.views.filiere_views import FiliereListView, FiliereDetailView, FiliereCreateUpdateView, FiliereDeleteView
from training.views.service_views import ServiceListView, ServiceDetailView, ServiceCreateUpdateView, ServiceDeleteView
from training.views.formation_views import MetierListView, MetierDetailView, MetierCreateUpdateView, MetierDeleteView # Import MetierCreateUpdateView


urlpatterns = [
    path("", HomeView.as_view(), name="home"),

    path("filieres", FiliereListView.as_view(), name="filieres"),
    path("filieres/create", FiliereCreateUpdateView.as_view(), name="filiere_create"),
    path("filieres/<int:pk>", FiliereDetailView.as_view(), name="filiere"),
    path("filieres/<int:pk>/update", FiliereCreateUpdateView.as_view(), name="filiere_update"),
    path("filieres/<int:pk>/delete", FiliereDeleteView.as_view(), name="filiere_delete"),

    path("services", ServiceListView.as_view(), name="services"),
    path("services/create", ServiceCreateUpdateView.as_view(), name="service_create"),
    path("services/<int:pk>", ServiceDetailView.as_view(), name="service"),
    path("services/<int:pk>/update", ServiceCreateUpdateView.as_view(), name="service_update"),
    path("services/<int:pk>/delete", ServiceDeleteView.as_view(), name="service_delete"),

    path("metiers", MetierListView.as_view(), name="metiers"),
    path("metiers/create", MetierCreateUpdateView.as_view(), name="metier_create"), # Utilise la vue unifiée
    path("metiers/<int:pk>", MetierDetailView.as_view(), name="metier"),
    path("metiers/<int:pk>/update", MetierCreateUpdateView.as_view(), name="metier_update"), # Utilise la vue unifiée
    path("metiers/<int:pk>/delete", MetierDeleteView.as_view(), name="metier_delete"),

    # Aliases using 'formation' names for templates and external links (backwards compatible)
    path("metiers", MetierListView.as_view(), name="formations"),
    path("metiers/create", MetierCreateUpdateView.as_view(), name="formation_create"),
    path("metiers/<int:pk>", MetierDetailView.as_view(), name="formation"),
    path("metiers/<int:pk>/update", MetierCreateUpdateView.as_view(), name="formation_update"),
    path("metiers/<int:pk>/delete", MetierDeleteView.as_view(), name="formation_delete"),
]