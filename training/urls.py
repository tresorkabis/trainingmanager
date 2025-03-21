
from django.urls import path

from training.views.formation_views import FormationCreateView, FormationListView
from training.views.filiere_views import FiliereListView
from training.views.formation_views import FormationDetailView, FormationListView
from training.views.filiere_views import FiliereDetailView, FiliereListView
from training.views.filiere_views import FiliereCreateView, FiliereListView

urlpatterns = [
    path("formations/", FormationListView.as_view(), name="formations"),
    path("formations/create", FormationCreateView.as_view(), name="formation_create"),
    path("formations/<int:pk>", FormationDetailView.as_view(), name="formation"),

    path("filieres", FiliereListView.as_view(), name="filieres"),
    path("filieres/create", FiliereCreateView.as_view(), name="filiere_create"),
    path("filieres/<int:pk>", FiliereDetailView.as_view(), name="filiere"),
]