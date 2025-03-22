from django.urls import path

from progress.views.action_views import ActionListViews
from progress.views.detailAction_views import DetailActionListViews
from progress.views.formateur_views import FormateurListView
from progress.views.typeaction_views import TypeActionListView
from progress.views.action_views import ActionDetailViews, ActionListViews
from progress.views.detailAction_views import DetailActionDetailView,DetailActionListViews
from progress.views.formateur_views import FormateurDetailView,FormateurListView
from progress.views.typeaction_views import TypeActionDetailView,TypeActionListView


urlpatterns = [
    path("actions", ActionListViews.as_view(), name="actions"),
    path("actions/<int:pk>", ActionDetailViews.as_view(), name="action"),
    path("detailactions",DetailActionListViews.as_view(),name="detailactions"),
    path("detailactions/<int:pk>", DetailActionDetailView.as_view(), name="detailaction"),
    path("formateurs",FormateurListView.as_view(),name="formateurs"),
    path("formateurs/<int:pk>", FormateurDetailView.as_view(), name="formateur"),
    path("typeactions",TypeActionListView.as_view(),name="typeactions"),
    path("typeactions/<int:pk>", TypeActionDetailView.as_view(), name="typeaction"), 
  
]