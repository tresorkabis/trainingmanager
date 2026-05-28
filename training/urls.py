from django.urls import path

from training.views.metier_views import MetierCreateView, MetierListView, MetierDetailView, MetierUpdateView, MetierDeleteView # Importation des vues Metier
from training.views.filiere_views import FiliereListView, FiliereDetailView, FiliereCreateUpdateView, FiliereDeleteView
from training.views.service_views import ServiceListView, ServiceDetailView, ServiceCreateUpdateView, ServiceDeleteView


urlpatterns = [
    path("metiers/", MetierListView.as_view(), name="metiers"),
    path("metiers/create", MetierCreateView.as_view(), name="metier_create"),
    path("metiers/<int:pk>", MetierDetailView.as_view(), name="metier"),
    path("metiers/<int:pk>/update", MetierUpdateView.as_view(), name="metier_update"),
    path("metiers/<int:pk>/delete", MetierDeleteView.as_view(), name="metier_delete"),

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
]