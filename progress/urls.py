from django.urls import path
from progress.views.actions_views import ActionListViews, ActionDetailViews, ActionCreateView, ActionUpdateView, ActionDeleteView
from progress.views.detailAction_views import DetailActionListViews
from progress.views.formateur_views import FormateurListView, FormateurCreateUpdateView, FormateurDeleteView, FormateurDetailView # Importation de FormateurDetailView
from progress.views.typeaction_views import TypeActionListView
from progress.views.detailAction_views import DetailActionDetailView
from progress.views.typeaction_views import TypeActionDetailView


urlpatterns = [
    path("actions", ActionListViews.as_view(), name="actions"),
    path("actions/create", ActionCreateView.as_view(), name="action_create"),
    path("actions/<int:pk>", ActionDetailViews.as_view(), name="action"),
    path("actions/<int:pk>/update", ActionUpdateView.as_view(), name="action_update"),
    path("actions/<int:pk>/delete", ActionDeleteView.as_view(), name="action_delete"),

    path("detailactions",DetailActionListViews.as_view(),name="detailactions"),
    path("detailactions/<int:pk>", DetailActionDetailView.as_view(), name="detailaction"),
    
    path("formateurs",FormateurListView.as_view(),name="formateurs"),
    path("formateurs/create", FormateurCreateUpdateView.as_view(), name="formateur_create"), # URL pour la création
    path("formateurs/<int:pk>", FormateurDetailView.as_view(), name="formateur"), # URL pour la vue de détail
    path("formateurs/<int:pk>/update", FormateurCreateUpdateView.as_view(), name="formateur_update"), # URL pour la modification
    path("formateurs/<int:pk>/delete", FormateurDeleteView.as_view(), name="formateur_delete"), # URL pour la suppression

    path("typeactions",TypeActionListView.as_view(),name="typeactions"),
    path("typeactions/<int:pk>", TypeActionDetailView.as_view(), name="typeaction"), 
  
]