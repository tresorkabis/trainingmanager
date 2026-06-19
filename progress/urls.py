from django.urls import path
from progress.views.actions_views import ActionListViews, ActionDetailViews, ActionCreateView, ActionUpdateView, ActionDeleteView, ActionUpdateProgressionsView
from progress.views.detailAction_views import DetailActionListViews, DetailActionDetailView, DetailActionCreateView
from progress.views.formateur_views import FormateurListView, FormateurCreateUpdateView, FormateurDeleteView, FormateurDetailView
from progress.views.typeaction_views import TypeActionListView, TypeActionDetailView, TypeActionCreateUpdateView, TypeActionDeleteView
from progress.views.paiement_views import PaiementListView, PaiementCreateView, PaiementDetailView, PaiementUpdateView, PaiementDeleteView, PaiementReceiptPrintView
from progress.views.module_progress_views import (
    ModuleProgressListView, ModuleProgressDetailView, ModuleProgressCreateView,
    ModuleProgressUpdateView, ModuleProgressDeleteView,
    SessionProgressCreateView, SessionProgressUpdateView, SessionProgressDeleteView
)
# Removed import for Performance views


urlpatterns = [
    path("actions/", ActionListViews.as_view(), name="actions"),
    path("actions/create/", ActionCreateView.as_view(), name="action_create"),
    path("actions/<int:pk>/", ActionDetailViews.as_view(), name="action"),
    path("actions/<int:pk>/update/", ActionUpdateView.as_view(), name="action_update"),
    path("actions/<int:pk>/delete/", ActionDeleteView.as_view(), name="action_delete"),
    path("actions/<int:pk>/update-progressions/", ActionUpdateProgressionsView.as_view(), name="action_update_progressions"),

    path("detailactions/", DetailActionListViews.as_view(), name="detailactions"),
    path("detailactions/create/", DetailActionCreateView.as_view(), name="detailaction_create"),
    path("detailactions/<int:pk>/", DetailActionDetailView.as_view(), name="detailaction"),
    
    path("formateurs/", FormateurListView.as_view(), name="formateurs"),
    path("formateurs/create/", FormateurCreateUpdateView.as_view(), name="formateur_create"),
    path("formateurs/<int:pk>/", FormateurDetailView.as_view(), name="formateur"),
    path("formateurs/<int:pk>/update/", FormateurCreateUpdateView.as_view(), name="formateur_update"),
    path("formateurs/<int:pk>/delete/", FormateurDeleteView.as_view(), name="formateur_delete"),

    path("typeactions/", TypeActionListView.as_view(), name="typeactions"),
    path("typeactions/create/", TypeActionCreateUpdateView.as_view(), name="typeaction_create"),
    path("typeactions/<int:pk>/", TypeActionDetailView.as_view(), name="typeaction"),
    path("typeactions/<int:pk>/update/", TypeActionCreateUpdateView.as_view(), name="typeaction_update"),
    path("typeactions/<int:pk>/delete/", TypeActionDeleteView.as_view(), name="typeaction_delete"),

    # URLs pour les paiements
    path("paiements/", PaiementListView.as_view(), name="paiements"),
    path("paiements/create/", PaiementCreateView.as_view(), name="paiement_create"),
    path("paiements/<int:pk>/", PaiementDetailView.as_view(), name="paiement"),
    path("paiements/<int:pk>/update/", PaiementUpdateView.as_view(), name="paiement_update"),
    path("paiements/<int:pk>/delete/", PaiementDeleteView.as_view(), name="paiement_delete"),
    path("paiements/<int:pk>/print/", PaiementReceiptPrintView.as_view(), name="paiement_print"),

    # URLs pour la progression des modules et des séances
    path("module_progressions/", ModuleProgressListView.as_view(), name="module_progressions"),
    path("module_progressions/create/", ModuleProgressCreateView.as_view(), name="module_progress_create"),
    path("module_progressions/<int:pk>/", ModuleProgressDetailView.as_view(), name="module_progress_detail"),
    path("module_progressions/<int:pk>/update/", ModuleProgressUpdateView.as_view(), name="module_progress_update"),
    path("module_progressions/<int:pk>/delete/", ModuleProgressDeleteView.as_view(), name="module_progress_delete"),
    
    path("module_progressions/<int:module_progress_pk>/sessions/create/", SessionProgressCreateView.as_view(), name="session_progress_create"),
    path("sessions/<int:pk>/update/", SessionProgressUpdateView.as_view(), name="session_progress_update"),
    path("sessions/<int:pk>/delete/", SessionProgressDeleteView.as_view(), name="session_progress_delete"),

    # Removed URLs for FormateurPerformance
]