from django.urls import path
from training.views.home_views import HomeView
from training.views.filiere_views import FiliereListView, FiliereDetailView, FiliereCreateUpdateView, FiliereDeleteView
from training.views.service_views import ServiceListView, ServiceDetailView, ServiceCreateUpdateView, ServiceDeleteView
from training.views.formation_views import FormationListView, FormationDetailView, FormationCreateUpdateView, FormationDeleteView # Import Formation views


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

    # Canonical 'formations' routes (replace /metiers)
    path("formations", FormationListView.as_view(), name="formations"),
    # Legacy name aliases for compatibility with older templates/code
    path("formations", FormationListView.as_view(), name="metiers"),

    path("formations/create", FormationCreateUpdateView.as_view(), name="formation_create"), # Utilise la vue unifiée
    path("formations/create", FormationCreateUpdateView.as_view(), name="metier_create"),

    path("formations/<int:pk>", FormationDetailView.as_view(), name="formation"),
    path("formations/<int:pk>", FormationDetailView.as_view(), name="metier"),

    path("formations/<int:pk>/update", FormationCreateUpdateView.as_view(), name="formation_update"), # Utilise la vue unifiée
    path("formations/<int:pk>/update", FormationCreateUpdateView.as_view(), name="metier_update"),

    path("formations/<int:pk>/delete", FormationDeleteView.as_view(), name="formation_delete"),
    path("formations/<int:pk>/delete", FormationDeleteView.as_view(), name="metier_delete"),

]